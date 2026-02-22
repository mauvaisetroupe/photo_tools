import os
import re
import shutil
from datetime import datetime
from exif import Image
import argparse

# Extensions supportées (MediaFactory)
EXT_PICTURES = ('.jpg', '.jpeg', '.rw2')
EXT_VIDEOS = ('.avi', '.mp4', '.mts', '.mov')

def get_date_taken(file_path):
    """ Équivalent de ExifHelper.java """
    try:
        with open(file_path, 'rb') as f:
            img = Image(f)
            if img.has_exif and hasattr(img, 'datetime_original'):
                # Format EXIF: 2024:07:12 10:06:37
                return datetime.strptime(img.datetime_original, '%Y:%m:%d %H:%M:%S')
    except:
        return None

def get_date_from_file_pattern(filename):
    """ Équivalent de NameCalculator.getDateFromFilePattern """
    patterns = {
        r'(\d{8})_(\d{6})': '%Y%m%d_%H%M%S',
        r'(\d{8})-(\d{6})': '%Y%m%d-%H%M%S'
    }
    for pat, fmt in patterns.items():
        match = re.search(pat, filename)
        if match:
            return datetime.strptime(match.group(), fmt)
    return None

def get_clean_filename(filename, date_taken, delete_prefix=True):
    name, ext = os.path.splitext(filename)

    # 1. Supprime l'ancien pattern de date YYYY-MM-DD_HH-MM-SS
    name = re.sub(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', '', name)

    # 2. Supprime les préfixes (PXL_, IMG_, etc.)
    if delete_prefix:
        name = re.sub(r'^[a-zA-Z]{2,4}[_-]', '', name)

    # 3. Supprime les occurrences de la date EXIF dans le nom original
    formats = ["%Y-%m-%d", "%H-%M-%S", "%Y%m%d", "%H%M%S"]
    for fmt in formats:
        fd = date_taken.strftime(fmt)
        name = name.replace(fd, "")

    # 4. NETTOYAGE INTELLIGENT :
    # On réduit les répétitions de chaque caractère individuellement
    name = re.sub(r'_+', '_', name)  # ___ -> _
    name = re.sub(r'-+', '-', name)  # --- -> -
    # On supprime les mélanges bizarres en début/fin
    name = name.strip('-_')

    # 5. Construction de la base
    prefix = date_taken.strftime('%Y-%m-%d_%H-%M-%S')
    
    if name:
        # On s'assure qu'il n'y a qu'un seul underscore entre le prefixe et le nom
        final_name = f"{prefix}_{name}"
    else:
        final_name = f"{prefix}"

    # 6. Assemblage final avec l'extension
    return final_name + ext

def process(source_dir, dest_dir, dry_run):
    print(f"Source: {source_dir}")
    print(f"Destination: {dest_dir}")
    print(f"Mode Dry Run: {dry_run}")
    
    print(f"--- Démarrage (Mode {'TEST' if dry_run else 'REEL'}) ---")
    
    for root, dirs, files in os.walk(source_dir):
        # Ignorer les dossiers système Synology (@eaDir) ---
        dirs[:] = [d for d in dirs if not d.startswith('@')]
        
        for filename in files:
            # Ignorer les fichiers cachés (ex: .DS_Store) ---
            if filename.startswith('.'):
                continue
                
            file_path = os.path.join(root, filename)
            is_pic = filename.lower().endswith(EXT_PICTURES)
            is_vid = filename.lower().endswith(EXT_VIDEOS)
            
            if is_pic or is_vid:
                # Recherche de la date (Priorité EXIF, puis Pattern Nom, puis FileDate)
                date_taken = get_date_taken(file_path)
                if not date_taken:
                    date_taken = get_date_from_file_pattern(filename)
                if not date_taken:
                    # Fallback ultime sur la date du fichier
                    date_taken = datetime.fromtimestamp(os.path.getmtime(file_path))

                new_name = get_clean_filename(filename, date_taken)
                
                # Gestion des dossiers (Structure yyyy/MM/dd)
                sub_path = date_taken.strftime('%Y/%m/%d')
                if is_vid:
                    # Comme dans votre Java : les vidéos vont dans un dossier VIDEOS
                    target_dir = os.path.join(dest_dir, "VIDEOS", sub_path)
                else:
                    target_dir = os.path.join(dest_dir, sub_path)

                if dry_run:
                    print(f"[DRY-RUN] {file_path} -> {target_dir}/{new_name}")
                else:
                    os.makedirs(target_dir, exist_ok=True)
                    dest_file = os.path.join(target_dir, new_name)
                    
                    # Sécurité : ne pas écraser si le fichier existe déjà
                    if os.path.exists(dest_file):
                        print(f"Saut : {new_name} existe déjà.")
                    else:
                        # sur le meme disque, shutil.move fait un "rename" qui est atomique 
                        shutil.move(file_path, dest_file)
                        print(f"Déplacé : {new_name}")

def check_source_status(source_dir):
    """
    Parcourt le dossier source pour faire un inventaire final.
    Affiche ce qui reste et pourquoi.
    """
    remaining_media = []
    ignored_files = []
    empty_dirs = 0
    
    print("\n" + "="*40)
    print("🔍 AUDIT FINAL DU DOSSIER SOURCE")
    print("="*40)

    for root, dirs, files in os.walk(source_dir):
        # Compte les dossiers (hors Synology)
        visible_dirs = [d for d in dirs if not d.startswith('@')]
        if not visible_dirs and not files:
            empty_dirs += 1

        for filename in files:
            # Ignorer les fichiers système type .DS_Store ou @eaDir
            if filename.startswith('.') or '@eaDir' in root:
                continue
                
            file_path = os.path.join(root, filename)
            
            # Vérifie si c'est un média qui aurait dû être traité
            if filename.lower().endswith(EXT_PICTURES + EXT_VIDEOS):
                remaining_media.append(file_path)
            else:
                ignored_files.append(file_path)

    # Affichage des résultats
    if not remaining_media and not ignored_files:
        print("✅ SUCCÈS : Le dossier source est totalement vide (hors fichiers cachés).")
    else:
        if remaining_media:
            print(f"⚠️  ALERTE : {len(remaining_media)} médias n'ont pas été déplacés :")
            for m in remaining_media[:5]: # Top 5 pour ne pas flood
                print(f"   - {m}")
            if len(remaining_media) > 5:
                print(f"   ... et {len(remaining_media)-5} autres.")
        
        if ignored_files:
            print(f"ℹ️  INFO : {len(ignored_files)} fichiers non-médias sont restés (ex: .txt, .json, .pdf) :")
            for i in ignored_files[:5]:
                print(f"   - {i}")
    
    print(f"\nDossiers restants : {empty_dirs} dossier(s) vide(s) à nettoyer manuellement.")
    print("="*40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script de tri et conversion de media.")
    parser.add_argument("source", help="Chemin du dossier source")
    parser.add_argument("dest", help="Chemin du dossier destination")
    parser.add_argument(
        "--execute", 
        action="store_false", 
        dest="dry_run",
        default=True,
        help="Exécute réellement les opérations"
    )

    args = parser.parse_args()

    process(args.source, args.dest, args.dry_run)

    if not args.dry_run:
            check_source_status(args.source)
    else:
        print("\n[DRY-RUN] Le check final est ignoré car aucun fichier n'a été déplacé.")