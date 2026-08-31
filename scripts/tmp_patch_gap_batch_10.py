from pathlib import Path

path = Path('noethys/Utils/UTILS_Impression_menu.py')
text = path.read_text(encoding='utf-8')

old = '''        # Dessine le mot MENUS\n        afficher_mot_menu = False\n\n        if afficher_mot_menu == True :\n'''
new = '''        # Dessine le mot MENUS\n        afficher_mot_menu = False\n        largeur_box = 0\n\n        if afficher_mot_menu == True :\n'''
assert old in text
text = text.replace(old, new, 1)

old = '''        # Préparation des images\n        if self.parent.dictDonnees["case_separateur_type"] == "image" and self.parent.dictDonnees["case_separateur_image"] != "aucune":\n            img = wx.Image(Chemins.GetStaticPath("Images/Menus/%s" % self.parent.dictDonnees["case_separateur_image"]), wx.BITMAP_TYPE_ANY)\n            ratio_image = 1.0 * img.GetWidth() / img.GetHeight()\n            largeur_image = self.largeur_case / 1.5\n            hauteur_image = largeur_image / ratio_image\n            separateur_image = Image(Chemins.GetStaticPath("Images/Menus/%s" % self.parent.dictDonnees["case_separateur_image"]), width=largeur_image, height=hauteur_image)\n'''
new = '''        # Préparation des images\n        separateur_image = None\n        if self.parent.dictDonnees["case_separateur_type"] == "image" and self.parent.dictDonnees["case_separateur_image"] != "aucune":\n            img = wx.Image(Chemins.GetStaticPath("Images/Menus/%s" % self.parent.dictDonnees["case_separateur_image"]), wx.BITMAP_TYPE_ANY)\n            ratio_image = 1.0 * img.GetWidth() / img.GetHeight()\n            largeur_image = self.largeur_case / 1.5\n            hauteur_image = largeur_image / ratio_image\n            separateur_image = Image(Chemins.GetStaticPath("Images/Menus/%s" % self.parent.dictDonnees["case_separateur_image"]), width=largeur_image, height=hauteur_image)\n'''
assert old in text
text = text.replace(old, new, 1)

old = '''                if self.parent.dictDonnees["case_separateur_type"] == "image" :\n                    separateur_image.drawOn(self.canvas, self.largeur_case / 2.0 - separateur_image._width / 2.0, y_paragraphe - espace_vertical / 2.0 - separateur_image._height / 2.0)\n                elif self.parent.dictDonnees["case_separateur_type"] == "ligne":\n'''
new = '''                if self.parent.dictDonnees["case_separateur_type"] == "image" and separateur_image is not None:\n                    separateur_image.drawOn(self.canvas, self.largeur_case / 2.0 - separateur_image._width / 2.0, y_paragraphe - espace_vertical / 2.0 - separateur_image._height / 2.0)\n                elif self.parent.dictDonnees["case_separateur_type"] == "ligne":\n'''
assert old in text
text = text.replace(old, new, 1)

old = '''        # Calcule les pages\n        if dictDonnees["type"] == "mensuel" :\n            liste_pages = [{"annee" : date.year, "mois" : date.month} for date in list(rrule.rrule(rrule.MONTHLY, dtstart=dictDonnees["date_debut"], until=dictDonnees["date_fin"]))]\n        if dictDonnees["type"] == "hebdomadaire" :\n            liste_pages = [{"date" : date} for date in list(rrule.rrule(rrule.WEEKLY, dtstart=dictDonnees["date_debut"], until=dictDonnees["date_fin"]))]\n        if dictDonnees["type"] == "quotidien" :\n            liste_pages = [{"date" : date} for date in list(rrule.rrule(rrule.DAILY, dtstart=dictDonnees["date_debut"], until=dictDonnees["date_fin"]))]\n'''
new = '''        # Calcule les pages\n        if dictDonnees["type"] == "mensuel" :\n            liste_pages = [{"annee" : date.year, "mois" : date.month} for date in list(rrule.rrule(rrule.MONTHLY, dtstart=dictDonnees["date_debut"], until=dictDonnees["date_fin"]))]\n        elif dictDonnees["type"] == "hebdomadaire" :\n            liste_pages = [{"date" : date} for date in list(rrule.rrule(rrule.WEEKLY, dtstart=dictDonnees["date_debut"], until=dictDonnees["date_fin"]))]\n        elif dictDonnees["type"] == "quotidien" :\n            liste_pages = [{"date" : date} for date in list(rrule.rrule(rrule.DAILY, dtstart=dictDonnees["date_debut"], until=dictDonnees["date_fin"]))]\n        else :\n            raise ValueError("Type d'impression de menu inconnu : %s" % dictDonnees["type"])\n'''
assert old in text
text = text.replace(old, new, 1)

old = '''            if dictDonnees["type"] == "mensuel":\n                calendrier = self.GetCalendrierMois(annee=dict_page["annee"], mois=dict_page["mois"], jours_semaine=dictDonnees["jours_semaine"])\n                nbre_lignes = len(calendrier)\n                nbre_colonnes = len(dictDonnees["jours_semaine"])\n                texte_titre = UTILS_Dates.PeriodeComplete(mois=dict_page["mois"], annee=dict_page["annee"])\n\n            if dictDonnees["type"] == "hebdomadaire":\n                calendrier = self.GetCalendrierSemaine(date=dict_page["date"], jours_semaine=dictDonnees["jours_semaine"])\n                nbre_lignes = 1\n                nbre_colonnes = len(dictDonnees["jours_semaine"])\n                texte_titre = self.GetLabelSemaine(calendrier[0], calendrier[-1])\n\n            if dictDonnees["type"] == "quotidien":\n                calendrier = None\n                nbre_lignes = 1\n                nbre_colonnes = 1\n                texte_titre = UTILS_Dates.DateComplete(dict_page["date"])\n'''
new = '''            if dictDonnees["type"] == "mensuel":\n                calendrier = self.GetCalendrierMois(annee=dict_page["annee"], mois=dict_page["mois"], jours_semaine=dictDonnees["jours_semaine"])\n                nbre_lignes = len(calendrier)\n                nbre_colonnes = len(dictDonnees["jours_semaine"])\n                texte_titre = UTILS_Dates.PeriodeComplete(mois=dict_page["mois"], annee=dict_page["annee"])\n\n            elif dictDonnees["type"] == "hebdomadaire":\n                calendrier = self.GetCalendrierSemaine(date=dict_page["date"], jours_semaine=dictDonnees["jours_semaine"])\n                nbre_lignes = 1\n                nbre_colonnes = len(dictDonnees["jours_semaine"])\n                texte_titre = self.GetLabelSemaine(calendrier[0], calendrier[-1])\n\n            else :\n                calendrier = None\n                nbre_lignes = 1\n                nbre_colonnes = 1\n                texte_titre = UTILS_Dates.DateComplete(dict_page["date"])\n'''
assert old in text
text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')

Path('tests/test_impression_menu_branch_contract.py').write_text(r'''import ast
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE = SOURCE_ROOT / "Utils" / "UTILS_Impression_menu.py"


class ImpressionMenuBranchContractTests(unittest.TestCase):
    def test_seven_targeted_gaps_are_gone(self):
        targeted_names = {
            ("Dessine_titre", "largeur_box"),
            ("Dessine_texte", "separateur_image"),
            ("__init__", "liste_pages"),
            ("__init__", "nbre_colonnes"),
            ("__init__", "texte_titre"),
            ("__init__", "nbre_lignes"),
            ("__init__", "calendrier"),
        }
        leftovers = []
        for item in audit_branch_assignment_gaps.scan_file(SOURCE, SOURCE_ROOT):
            if (item.get("function"), item.get("name")) in targeted_names:
                leftovers.append(item)
        self.assertEqual(leftovers, [], leftovers)

    def test_print_type_contract_is_exhaustive(self):
        source = SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        impression = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Impression"
        )
        init = next(
            node for node in impression.body
            if isinstance(node, ast.FunctionDef) and node.name == "__init__"
        )
        segment = ast.get_source_segment(source, init)
        self.assertIn('elif dictDonnees["type"] == "hebdomadaire"', segment)
        self.assertIn('elif dictDonnees["type"] == "quotidien"', segment)
        self.assertIn("raise ValueError", segment)
        self.assertIn("Type d'impression de menu inconnu", segment)

    def test_missing_separator_image_is_explicitly_neutral(self):
        source = SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        case = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Case"
        )
        draw = next(
            node for node in case.body
            if isinstance(node, ast.FunctionDef) and node.name == "Dessine_texte"
        )
        segment = ast.get_source_segment(source, draw)
        self.assertIn("separateur_image = None", segment)
        self.assertIn("separateur_image is not None", segment)


if __name__ == "__main__":
    unittest.main()
''', encoding='utf-8')
