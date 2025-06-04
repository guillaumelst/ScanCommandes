import os
import re
import unicodedata
import fitz  # PyMuPDF
from PyPDF2 import PdfReader

# --------------------------------------------------------------------------------
# 1. Répertoires en jeu
# --------------------------------------------------------------------------------
input_dir = r"C:\Users\GLT\eiffage.com\OneDrive - eiffageenergie.be\Documents\Guillaume\Programmation\Commandes\01_Commandes"
output_dir = r"C:\Users\GLT\eiffage.com\OneDrive - eiffageenergie.be\Documents\Guillaume\Programmation\Commandes\dessin"

# Création du dossier de sortie s’il n’existe pas
os.makedirs(output_dir, exist_ok=True)

# --------------------------------------------------------------------------------
# 2. Coordonnées de la zone (bbox) en points pour PyMuPDF
#    Origine (0,0) = coin haut-gauche de la page
#    x0, y0 = coin supérieur gauche du rectangle
#    w, h = largeur et hauteur du rectangle
# --------------------------------------------------------------------------------
x0 = 350  # abscisse du coin gauche
y0 = 140  # ordonnée du coin supérieur
w  = 240  # largeur du rectangle
h  = 20   # hauteur du rectangle

x1 = x0 + w  # abscisse du coin droit
y1 = y0 + h  # ordonnée du coin inférieur

zone = fitz.Rect(x0, y0, x1, y1)

# --------------------------------------------------------------------------------
# 3. Fonction utilitaire pour nettoyer une chaîne en nom de fichier valide
# --------------------------------------------------------------------------------
def sanitize_for_filename(s: str) -> str:
    s_norm = unicodedata.normalize('NFD', s)
    s_ascii = ''.join(c for c in s_norm if unicodedata.category(c) != 'Mn')
    s_clean = re.sub(r'[^A-Za-z0-9 _\.-]', '', s_ascii)
    s_clean = re.sub(r'\s+', '_', s_clean).strip('_')
    return s_clean

# --------------------------------------------------------------------------------
# 4. Extraction du texte intégral d’un PDF (pour parsing des champs commande/date)
# --------------------------------------------------------------------------------
def extract_text_from_pdf(path_pdf: str) -> str:
    reader = PdfReader(path_pdf)
    pages = []
    for page in reader.pages:
        texte = page.extract_text()
        if texte:
            pages.append(texte)
    return "\n".join(pages)

# --------------------------------------------------------------------------------
# 5. Recherche des champs (commande, date) dans le texte brut
# --------------------------------------------------------------------------------
def parse_fields_from_text(text: str):
    """
    Parcourt le texte pour extraire :
      1. 'commande'      : contenu capturé après « N° commande »
      2. 'date_commande' : contenu capturé après « Date de commande »
    Retourne un tuple (commande, date_commande).
    """
    commande = None
    date_commande = None

    # a) Numéro de commande
    m_cmd = re.search(
        r"N°\s*commande\s*[:]?[\s]*([A-Za-z0-9\.-]+)",
        text,
        flags=re.IGNORECASE
    )
    if m_cmd:
        commande = m_cmd.group(1).strip()

    # b) Date de commande
    m_date = re.search(
        r"Date\s+de\s+commande\s*[:]?[\s]*(\d{2}[-/]\d{2}[-/]\d{2,4})",
        text,
        flags=re.IGNORECASE
    )
    if m_date:
        date_commande = m_date.group(1).strip()

    return (commande, date_commande)

# --------------------------------------------------------------------------------
# 6. Boucle sur tous les PDF : parsing, renommage, extraction bbox & annotation
# --------------------------------------------------------------------------------
for nom_fichier in os.listdir(input_dir):
    if not nom_fichier.lower().endswith(".pdf"):
        continue

    ancien_chemin = os.path.join(input_dir, nom_fichier)
    current_path = ancien_chemin  # pointeur vers le fichier à traiter

    print(f"\n=== Traitement de : {nom_fichier} ===")

    # 6.1. Extraction du texte brut pour parsing commande + date
    texte_int = extract_text_from_pdf(current_path)
    commande, date_commande = parse_fields_from_text(texte_int)

    # 6.2. Ouvrir le PDF avec PyMuPDF pour extraire le fournisseur dans la zone
    doc_temp = fitz.open(current_path)
    page_temp = doc_temp[0]
    texte_zone = page_temp.get_text("text", clip=zone)
    fournisseur = texte_zone.strip() if texte_zone else None
    doc_temp.close()

    # 6.3. Vérification des champs et renommage
    if not (commande and date_commande and fournisseur):
        print("❌ Impossible de récupérer tous les champs pour renommer :")
        print(f"   • commande   = {commande}")
        print(f"   • date       = {date_commande}")
        print(f"   • fournisseur= {fournisseur}")
        print("⏩ On conserve le nom d'origine pour ce fichier.")
        nouveau_nom = nom_fichier  # pas de renommage
    else:
        cmd_clean = sanitize_for_filename(commande)
        date_clean = sanitize_for_filename(date_commande.replace("/", "-"))
        fournisseur_clean = sanitize_for_filename(fournisseur)
        nouveau_nom = f"{cmd_clean}_{date_clean}_{fournisseur_clean}.pdf"
        nouveau_chemin = os.path.join(input_dir, nouveau_nom)

        if os.path.exists(nouveau_chemin):
            print(f"⚠️ Le fichier '{nouveau_nom}' existe déjà, on ne renomme pas.")
            nouveau_nom = nom_fichier  # on ne change pas le nom
        else:
            os.rename(ancien_chemin, nouveau_chemin)
            print(f"✅ Renommé en : {nouveau_nom}")
            current_path = nouveau_chemin  # met à jour le chemin pour l'annotation

    # 6.4. Réouvrir le PDF pour extraire de nouveau la zone et annoter
    doc = fitz.open(current_path)
    page = doc[0]
    texte_zone = page.get_text("text", clip=zone)

    print("\n--- Texte extrait dans la zone spécifiée (fournisseur) ---")
    if texte_zone and texte_zone.strip():
        print(texte_zone.strip())
    else:
        print("(aucun texte détecté dans la zone)")

    # 6.5. Dessiner le rectangle sur la page (annotation)
    page.draw_rect(zone, color=(1, 0, 0), width=1)

    # 6.6. Enregistrer la copie annotée dans 'dessin' avec le nom final
    sortie_annot = os.path.join(output_dir, nouveau_nom)
    doc.save(sortie_annot)
    doc.close()

    print(f"🔖 Annoté et enregistré dans : {sortie_annot}")

print("\nTraitement complet terminé. Les PDF annotés sont dans le dossier 'dessin'.")
