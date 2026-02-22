import os
import re
import shutil
from datetime import datetime
from exif import Image

# --- CONFIGURATION ---
SOURCE_DIR = "/volume1/photo/IMPORT"
DEST_DIR = "/volume1/photo/CONVERTED"
DRY_RUN = True  # Passez à False pour exécuter réellement

# Extensions supportées (MediaFactory)
EXT_PICTURES = ('.jpg', '.jpeg', '.rw2')
EXT_VIDEOS = ('.avi', '.mp4', '.mts', '.mov')

def get_exif_date(file_path):
    """ Équivalent de ExifHelper.java """
    try:
        with open(file_path, 'rb') as f:
            img = Image(f)
            if img.has_exif and hasattr(img, 'datetime_original'):
                # Format EXIF: 2024:07:12 10:06:37
                return datetime.strptime(img.datetime_original, '%Y:%m:%d %H:%M:%S')
    except:
        return None
    return None

def get_clean_filename(filename, date_taken):
    """ Équivalent de NameCalculator.java """
    name, ext = os.path.splitext(filename)
    
    # 1. deletePrefix : Enlève PXL_, IMG_, etc.
    name = re.sub(r'^[a-zA-Z_-]+', '', name)
    
    # 2. deleteDateAndTime : Enlève les dates existantes (20250501_090637)
    name = re.sub(r'\d{8}[_-]?\d{6}', '', name)
    
    # 3. Nettoyage des caractères résiduels (cleanName)
    name = re.sub(r'^[_-]+|[_-]+$', '', name)
    name = re.sub(r'[_-]{2,}', '_', name)
    
    # 4. Construction du nom final
    date_prefix = date_taken.strftime('%Y-%m-%d_%H-%M-%S')
    return f"{date_prefix}_{name}{ext}" if name else f"{date_prefix}{ext}"

def process():
    print(f"--- Démarrage (Mode {'TEST' if DRY_RUN else 'REEL'}) ---")
    
    for root, _, files in os.walk(SOURCE_DIR):
        for filename in files:
            file_path = os.path.join(root, filename)
            is_pic = filename.lower().endswith(EXT_PICTURES)
            is_vid = filename.lower().endswith(EXT_VIDEOS)
            
            if is_pic or is_vid:
                # Extraction de la date (Priorité EXIF, sinon date fichier)
                date_taken = get_exif_date(file_path)
                if not date_taken:
                    date_taken = datetime.fromtimestamp(os.path.getmtime(file_path))

                new_name = get_clean_filename(filename, date_taken)
                
                # Gestion des dossiers (Structure yyyy/MM/dd)
                sub_path = date_taken.strftime('%Y/%m/%d')
                if is_vid:
                    # Comme dans votre Java : les vidéos vont dans un dossier VIDEOS
                    target_dir = os.path.join(DEST_DIR, "VIDEOS", sub_path)
                else:
                    target_dir = os.path.join(DEST_DIR, sub_path)

                if DRY_RUN:
                    print(f"[DRY-RUN] {filename} -> {target_dir}/{new_name}")
                else:
                    os.makedirs(target_dir, exist_ok=True)
                    # Déplacement (doMove)
                    shutil.move(file_path, os.path.join(target_dir, new_name))
                    print(f"Déplacé : {new_name}")

if __name__ == "__main__":
    process()
