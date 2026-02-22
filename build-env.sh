cd /volume1/homes/admin.syno2/development

mkdir -p photo_tools && cd photo_tools

# Création de l'environnement virtuel
python3 -m venv venv_photos

# Activation de l'environnement
source venv_photos/bin/activate

# Installation de la bibliothèque nécessaire dans l'environnement isolé
pip install exif

