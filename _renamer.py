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
                    print(f"[DRY-RUN] {filename} -> {target_dir}/{new_name}")
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
