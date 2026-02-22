import os
import unittest
from datetime import datetime
# On importe la fonction de ton script (nommé ici rename_script.py)
from _renamer import get_clean_filename, get_date_taken

class TestRenameLogic(unittest.TestCase):

    def setUp(self):
        # Une date de référence pour les tests
        self.date_ref = datetime(2025, 4, 30, 10, 41, 43)

    def test_standard_pixel(self):
        # Test d'un fichier Google Pixel classique
        filename = "PXL_20250430_084143316.jpg"
        expected = "2025-04-30_10-41-43_084143316.jpg"
        self.assertEqual(get_clean_filename(filename, self.date_ref), expected)

    def test_motion_photo(self):
        # Test avec l'extension .MP.jpg
        filename = "PXL_20250430_080736678.MP.jpg"
        expected = "2025-04-30_10-41-43_080736678.MP.jpg"
        self.assertEqual(get_clean_filename(filename, self.date_ref), expected)

    def test_multiple_separators(self):
        # Test du nettoyage des underscores multiples
        filename = "IMG___20250430___test--file.jpg"
        # Le script doit réduire les ___ en _ et -- en -
        result = get_clean_filename(filename, self.date_ref)
        self.assertIn("2025-04-30_10-41-43_test-file.jpg", result)

    def test_already_renamed(self):
        # Test si le fichier a déjà le format de date (ne doit pas le doubler)
        filename = "2025-04-30_10-41-43_mon_voyage.jpg"
        # Ici on vérifie que la Regex de nettoyage de date fonctionne
        result = get_clean_filename(filename, self.date_ref)
        self.assertEqual(result, "2025-04-30_10-41-43_mon_voyage.jpg")

    def test_already_renamed_undersore_in_target(self):
        # Test si le fichier a déjà le format de date (ne doit pas le doubler)
        filename = "2025-04-30_10-41-43_mon-voyage.jpg"
        # Ici on vérifie que la Regex de nettoyage de date fonctionne
        result = get_clean_filename(filename, self.date_ref)
        self.assertEqual(result, "2025-04-30_10-41-43_mon-voyage.jpg")


class TestPhotoIntegration(unittest.TestCase):
    def setUp(self):
        # Chemin relatif ou absolu vers ta photo de test
        self.test_photo_path = "test/PXL_20250430_080736678.MP.jpg"
        
        if not os.path.exists(self.test_photo_path):
            self.skipTest(f"Fichier de test absent : {self.test_photo_path}")

    def test_exif_extraction_and_rename(self):
        # 1. Test lecture EXIF
        date_extracted = get_date_taken(self.test_photo_path)
        
        self.assertIsNotNone(date_extracted, "L'EXIF n'a pas pu être lu sur le fichier réel.")
        self.assertEqual(date_extracted.strftime('%Y-%m-%d %H:%M:%S'), "2025-04-30 10:07:36")

        # 2. Test renommage avec cette date
        filename = os.path.basename(self.test_photo_path)
        result = get_clean_filename(filename, date_extracted)
        
        expected = "2025-04-30_10-07-36_080736678.MP.jpg"
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()