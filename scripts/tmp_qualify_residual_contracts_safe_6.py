import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import qualify_branch_assignment_gaps as qualify

TARGETS = [
    ('Dlg/DLG_Impression_attestation.py', 'MAJ_CTRL_Donnees', 'numero', "SELECT MAX(numero) est une requête agrégée sans GROUP BY : après une exécution réussie elle retourne toujours une ligne, avec NULL sur table vide ; la branche affecte donc toujours numero avant formatage"),
    ('Dlg/DLG_Saisie_cotisation.py', 'OnChoixUnite', 'nomType', "une unité ne peut être sélectionnée qu'après OnChoixType, qui alimente Choix_unite avec l'ID du type ; Choix_unite refuse de charger des unités sans IDtype_cotisation, donc une unité présente implique un type présent et nomType défini"),
    ('Dlg/DLG_Saisie_cotisation.py', 'OnChoixUnite', 'type', "une unité ne peut être sélectionnée qu'après OnChoixType, qui alimente Choix_unite avec l'ID du type ; Choix_unite refuse de charger des unités sans IDtype_cotisation, donc une unité présente implique un type présent et type défini"),
    ('Dlg/DLG_Saisie_commande.py', 'CreationPDF', 'style', "CTRL_Commande_repas construit une Case pour chaque couple liste_dates/liste_colonnes : les dates réelles sont datetime.date et la ligne Total est du texte ; les deux formes créent systématiquement la clé de case avant l'impression"),
    ('Dlg/DLG_Releve_prestations.py', 'CreationPDF', 'labelRegroupement', "GetOptions de DLG_Releve_prestations_saisie borne regroupement à date/mois/annee ou None ; CreationPDF normalise None vers date, donc les trois branches couvrent exhaustivement le domaine"),
    ('Dlg/DLG_Releve_prestations.py', 'CreationPDF', 'key', "GetOptions de DLG_Releve_prestations_saisie borne regroupement à date/mois/annee ou None ; CreationPDF normalise None vers date, donc chaque prestation valide reçoit toujours une key"),
    ('Dlg/DLG_Releve_prestations.py', 'CreationPDF', 'labelKey', "les trois modes de regroupement produisent respectivement datetime.date, tuple (annee, mois) ou int année ; les trois branches de formatage couvrent donc exhaustivement le type de key"),
]

report = qualify.build_report()
review = [item for item in report['findings'] if item['classification'] == 'review']
entries = []
for file, function, name, reason in TARGETS:
    matches = [item for item in review if (item['file'], item['function'], item['name']) == (file, function, name)]
    assert len(matches) == 1, (file, function, name, matches)
    key = qualify.qualification_key(matches[0])
    assert key[-1], key
    print('QUALIFY', key)
    entries.append((key, reason))

path = Path('scripts/qualify_branch_assignment_gaps.py')
text = path.read_text(encoding='utf-8')
existing = set(qualify.EXPLICIT_SAFE)
blocks = []
for key, reason in entries:
    assert key not in existing, key
    blocks.append(f"    {key!r}: (\n        {reason!r}\n    ),\n")
marker = "\n}\n\ndef _candidate_fingerprint"
assert marker in text
text = text.replace(marker, "\n" + "".join(blocks) + marker, 1)
path.write_text(text, encoding='utf-8')

test = Path('tests/test_residual_contracts_safe_6.py')
test.write_text(r'''from pathlib import Path
import unittest

from scripts import qualify_branch_assignment_gaps as qualify

TARGETS = {
    ("Dlg/DLG_Impression_attestation.py", "MAJ_CTRL_Donnees", "numero"),
    ("Dlg/DLG_Saisie_cotisation.py", "OnChoixUnite", "nomType"),
    ("Dlg/DLG_Saisie_cotisation.py", "OnChoixUnite", "type"),
    ("Dlg/DLG_Saisie_commande.py", "CreationPDF", "style"),
    ("Dlg/DLG_Releve_prestations.py", "CreationPDF", "labelRegroupement"),
    ("Dlg/DLG_Releve_prestations.py", "CreationPDF", "key"),
    ("Dlg/DLG_Releve_prestations.py", "CreationPDF", "labelKey"),
}


class ResidualContractsSafe6Test(unittest.TestCase):
    def test_targets_are_exactly_explicit_safe(self):
        report = qualify.build_report()
        registry = report["explicit_safe_registry"]
        self.assertEqual(registry["unmatched"], [])
        self.assertEqual(registry["ambiguous"], [])
        for target in TARGETS:
            matches = [item for item in report["findings"] if (item["file"], item["function"], item["name"]) == target]
            self.assertEqual(len(matches), 1, (target, matches))
            self.assertEqual(matches[0]["classification"], "explicit_safe")

    def test_attestation_max_query_keeps_aggregate_contract(self):
        source = Path("noethys/Dlg/DLG_Impression_attestation.py").read_text(encoding="utf-8")
        self.assertIn('SELECT MAX(numero)\n        FROM attestations', source)
        self.assertIn('if numero == None :\n                numero = 1', source)
        self.assertIn('self.SetValeur("numero", u"%06d" % numero)', source)

    def test_cotisation_unit_selection_remains_tied_to_type_selection(self):
        source = Path("noethys/Dlg/DLG_Saisie_cotisation.py").read_text(encoding="utf-8")
        self.assertIn('IDtype_cotisation = self.ctrl_type.GetID()\n        self.ctrl_unite.MAJ(IDtype_cotisation)\n        self.OnChoixUnite(None)', source)
        self.assertIn('if self.IDtype_cotisation == None :\n            return []', source)
        self.assertIn('dictDonneesType = self.ctrl_type.GetDetailDonnees()', source)
        self.assertIn('dictDonneesUnite = self.ctrl_unite.GetDetailDonnees()', source)

    def test_meal_order_grid_constructs_every_printed_case(self):
        ctrl = Path("noethys/Ctrl/CTRL_Commande_repas.py").read_text(encoding="utf-8")
        dlg = Path("noethys/Dlg/DLG_Saisie_commande.py").read_text(encoding="utf-8")
        self.assertIn('dictDonnees["liste_dates"].append(_(u"Total"))', ctrl)
        self.assertIn('if type(date) == datetime.date', ctrl)
        self.assertIn('if type(date) in (str, six.text_type):', ctrl)
        self.assertGreaterEqual(ctrl.count('self.dictCases[(numLigne, numColonne)] = case'), 2)
        self.assertIn('if (numLigne, numColonne) in dictDonnees["cases"]:', dlg)

    def test_statement_grouping_domain_remains_date_month_year(self):
        saisie = Path("noethys/Dlg/DLG_Releve_prestations_saisie.py").read_text(encoding="utf-8")
        releve = Path("noethys/Dlg/DLG_Releve_prestations.py").read_text(encoding="utf-8")
        self.assertIn('if self.ctrl_regroupement_date.GetSelection() == 0 : regroupement = "date"', saisie)
        self.assertIn('if self.ctrl_regroupement_date.GetSelection() == 1 : regroupement = "mois"', saisie)
        self.assertIn('if self.ctrl_regroupement_date.GetSelection() == 2 : regroupement = "annee"', saisie)
        self.assertIn('modeRegroupement = "date"', releve)
        self.assertIn('if modeRegroupement == "date" :\n                                key = date', releve)
        self.assertIn('if modeRegroupement == "mois" :\n                                key = (date.year, date.month)', releve)
        self.assertIn('if modeRegroupement == "annee" :\n                                key = date.year', releve)
        self.assertIn('if type(key) == datetime.date : labelKey =', releve)
        self.assertIn('if type(key) == tuple : labelKey =', releve)
        self.assertIn('if type(key) == int : labelKey =', releve)


if __name__ == "__main__":
    unittest.main()
''', encoding='utf-8')
