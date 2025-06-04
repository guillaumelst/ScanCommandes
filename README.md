# ⚡ Traitement automatique de PDF 🚀

Ce projet fournit un script Python 🐍 permettant d’automatiser le traitement de fichiers PDF dans un dossier donné. Il réalise les opérations suivantes :

- 📄 Parcourt tous les fichiers `.pdf` d’un dossier d’entrée.
- 🔍 Extrait le texte intégral pour récupérer :
  1. **N° commande** (après « N° commande »)
  2. **Date de commande** (après « Date de commande »)
- 📐 Lit une zone définie (bbox) sur la première page pour y extraire le nom du **fournisseur**.
- ✏️ Renomme chaque PDF sous la forme `<commande>_<date>_<fournisseur>.pdf` si tous les champs sont trouvés.
- 🖍️ Annoter la même zone en traçant un rectangle rouge sur la première page.
- 📂 Enregistre la version annotée dans un dossier de sortie.

Si l’un des champs (commande, date ou fournisseur) est introuvable, le PDF garde son nom d’origine et le script signale les champs manquants.  

---

## 📚 Table des matières

1. [🚀 Prérequis](#-prérequis)  
2. [🔧 Installation](#-installation)  
3. [📂 Structure du projet](#-structure-du-projet)  
4. [▶️ Utilisation](#-utilisation)  
5. [✨ Détails du script](#-détails-du-script)  
6. [📄 Licence](#-licence)  

---

## 🚀 Prérequis

- **Python 3.7+** 🐍  
- Modules Python :  
  - `PyPDF2` (pour extraire le texte brut des PDF)  
  - `PyMuPDF` (alias `fitz`, pour manipuler le PDF—extraction de texte dans une zone et annotation)  

Installez-les via :  
```bash
pip install PyPDF2 PyMuPDF
```  

> **Note** : Le script a été testé sous Windows. Les chemins d’accès (`input_dir`, `output_dir`) pointent vers un dossier OneDrive, mais vous pouvez les adapter à votre environnement (Linux/macOS).

---

## 🔧 Installation

1. **Cloner ce dépôt**  
   ```bash
   git clone https://github.com/<votre-utilisateur>/<votre-repo>.git
   cd <votre-repo>
   ```  

2. **Installer les dépendances**  
   ```bash
   pip install -r requirements.txt
   ```  
   > *Si vous n’avez pas de `requirements.txt`, exécutez simplement :*  
   > ```bash
   > pip install PyPDF2 PyMuPDF
   > ```  

3. **Modifier les chemins**  
   - Ouvrez `process_pdfs.py` (ou le nom du script principal)  
   - Ajustez les variables :  
     ```python
     input_dir = r"<chemin_vers_votre_dossier_d_entree>"
     output_dir = r"<chemin_vers_votre_dossier_de_sortie>"
     ```  
   - Vérifiez que le dossier de sortie (`output_dir`) existe ou sera créé automatiquement par le script.

---

## 📂 Structure du projet

```text
./
├── process_pdfs.py      # Script principal pour traiter et annoter les PDF
├── requirements.txt     # Liste des dépendances Python
├── README.md            # Ce fichier
└── dessin/              # (généré automatiquement) Contiendra les PDF annotés
```

---

## ▶️ Utilisation

1. **Ajouter vos PDF**  
   Placez tous les fichiers `.pdf` à traiter dans le dossier spécifié par `input_dir`.

2. **Lancer le script**  
   ```bash
   python process_pdfs.py
   ```  

3. **Observer le résultat**  
   - La console affichera pour chaque PDF :  
     - Le nom du fichier en cours de traitement.  
     - Les champs détectés (commande, date, fournisseur) ou un message d’erreur si l’un manque.  
     - Le renommage effectué (ou conservation du nom d’origine).  
     - La confirmation de l’annotation et de l’enregistrement dans le dossier `dessin/`.  

4. **Vérifier le dossier de sortie**  
   Tous les PDF annotés (avec un rectangle rouge sur la première page) seront copiés dans `output_dir` avec leur nom final.

---

## ✨ Détails du script

Le fichier **`process_pdfs.py`** est structuré en 6 grandes étapes :

1. **Définition des répertoires**  
   ```python
   input_dir = r"C:\Path\To\Input"
   output_dir = r"C:\Path\To\Output"
   os.makedirs(output_dir, exist_ok=True)
   ```  
   - `input_dir` : dossier contenant les PDF à traiter.  
   - `output_dir` : dossier où seront enregistrés les PDF annotés.  
   - Si `output_dir` n’existe pas, il est créé automatiquement.

2. **Coordonnées de la zone (bbox) pour PyMuPDF**  
   ```python
   x0, y0 = 350, 140     # coin supérieur gauche
   w, h   = 240, 20      # largeur et hauteur
   x1, y1 = x0 + w, y0 + h
   zone = fitz.Rect(x0, y0, x1, y1)
   ```  
   - Origine `(0,0)` = coin haut-gauche de la page en points.  
   - On définit un rectangle (`zone`) où se trouve le nom du fournisseur sur la première page.

3. **Fonction `sanitize_for_filename`**  
   ```python
   def sanitize_for_filename(s: str) -> str:
       s_norm = unicodedata.normalize('NFD', s)
       s_ascii = ''.join(c for c in s_norm if unicodedata.category(c) != 'Mn')
       s_clean = re.sub(r'[^A-Za-z0-9 _\.-]', '', s_ascii)
       s_clean = re.sub(r'\s+', '_', s_clean).strip('_')
       return s_clean
   ```  
   - Nettoie une chaîne pour en faire un nom de fichier valide :  
     - Supprime les accents  
     - Élimine les caractères spéciaux (ne garde que lettres, chiffres, espaces, `_.-`)  
     - Remplace les espaces par des underscores `_`.

4. **Extraction du texte complet d’un PDF**  
   ```python
   from PyPDF2 import PdfReader

   def extract_text_from_pdf(path_pdf: str) -> str:
       reader = PdfReader(path_pdf)
       pages = []
       for page in reader.pages:
           texte = page.extract_text()
           if texte:
               pages.append(texte)
       return "\n".join(pages)
   ```  
   - Utilise PyPDF2 pour parcourir chaque page et récupérer le texte brut.  
   - Retourne la concaténation de tous les textes.

5. **Parsing des champs (commande, date)**  
   ```python
   def parse_fields_from_text(text: str):
       commande = None
       date_commande = None

       # Recherche « N° commande »
       m_cmd = re.search(
           r"N°\s*commande\s*[:]?\s*([A-Za-z0-9\.-]+)",
           text,
           flags=re.IGNORECASE
       )
       if m_cmd:
           commande = m_cmd.group(1).strip()

       # Recherche « Date de commande »
       m_date = re.search(
           r"Date\s+de\s+commande\s*[:]?\s*(\d{2}[-/]\d{2}[-/]\d{2,4})",
           text,
           flags=re.IGNORECASE
       )
       if m_date:
           date_commande = m_date.group(1).strip()

       return (commande, date_commande)
   ```  
   - Grâce à deux expressions régulières, on capture :  
     1. Le **numéro de commande** (suite de lettres/chiffres/points/tirets) après « N° commande ».  
     2. La **date de commande** au format `JJ-MM-AAAA` ou `JJ/MM/AA`.  

6. **Boucle principale sur tous les PDF**  
   ```python
   for nom_fichier in os.listdir(input_dir):
       if not nom_fichier.lower().endswith(".pdf"):
           continue

       ancien_chemin = os.path.join(input_dir, nom_fichier)
       current_path = ancien_chemin
       print(f"\n=== Traitement de : {nom_fichier} ===")

       # 6.1. Extraction du texte brut
       texte_int = extract_text_from_pdf(current_path)
       commande, date_commande = parse_fields_from_text(texte_int)

       # 6.2. Extraction du fournisseur via PyMuPDF
       doc_temp = fitz.open(current_path)
       page_temp = doc_temp[0]
       texte_zone = page_temp.get_text("text", clip=zone)
       fournisseur = texte_zone.strip() if texte_zone else None
       doc_temp.close()

       # 6.3. Renommage si tous les champs sont OK
       if not (commande and date_commande and fournisseur):
           print("❌ Impossible de récupérer tous les champs pour renommer :")
           print(f"   • commande   = {commande}")
           print(f"   • date       = {date_commande}")
           print(f"   • fournisseur= {fournisseur}")
           print("⏩ On conserve le nom d’origine.")
           nouveau_nom = nom_fichier
       else:
           cmd_clean = sanitize_for_filename(commande)
           date_clean = sanitize_for_filename(date_commande.replace("/", "-"))
           fournisseur_clean = sanitize_for_filename(fournisseur)
           nouveau_nom = f"{cmd_clean}_{date_clean}_{fournisseur_clean}.pdf"
           nouveau_chemin = os.path.join(input_dir, nouveau_nom)

           if os.path.exists(nouveau_chemin):
               print(f"⚠️ '{nouveau_nom}' existe déjà, pas de renommage.")
               nouveau_nom = nom_fichier
           else:
               os.rename(ancien_chemin, nouveau_chemin)
               print(f"✅ Renommé en : {nouveau_nom}")
               current_path = nouveau_chemin

       # 6.4. Réouverture pour annoter
       doc = fitz.open(current_path)
       page = doc[0]
       texte_zone = page.get_text("text", clip=zone)

       print("\n--- Texte extrait dans la zone (fournisseur) ---")
       if texte_zone and texte_zone.strip():
           print(texte_zone.strip())
       else:
           print("(aucun texte détecté dans la zone)")

       # 6.5. Annotation (rectangle rouge)
       page.draw_rect(zone, color=(1, 0, 0), width=1)

       # 6.6. Sauvegarde dans le dossier de sortie
       sortie_annot = os.path.join(output_dir, nouveau_nom)
       doc.save(sortie_annot)
       doc.close()

       print(f"🔖 Annoté et enregistré dans : {sortie_annot}")

   print("\nTraitement complet terminé. Les PDF annotés sont dans le dossier 'dessin'.")
   