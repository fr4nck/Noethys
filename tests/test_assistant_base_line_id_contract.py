import ast
import unittest
from pathlib import Path
from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE_PATH = SOURCE_ROOT / "Ctrl" / "CTRL_Assistant_base.py"


def load_sauvegarde_tarifs():
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    methods = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "Sauvegarde_tarifs"
    ]
    if len(methods) != 1:
        raise AssertionError("Méthode Sauvegarde_tarifs introuvable ou ambiguë")
    module = ast.Module(body=[methods[0]], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, str(SOURCE_PATH), "exec"), namespace)
    return namespace["Sauvegarde_tarifs"]


class FakeTrack:
    def __init__(self, nom_table, lignes=None):
        self.nom_table = nom_table
        self.lignes = [] if lignes is None else lignes

    def MAJ(self, valeurs):
        for key, value in valeurs.items():
            setattr(self, key, value)

    def Get_variables_pour_db(self):
        return []

    def Get_champs_pour_db(self):
        return "champ"

    def Get_interrogations_pour_db(self):
        return "?"


class FakeDB:
    def __init__(self, is_network, max_line_id=None):
        self.isNetwork = is_network
        self.max_line_id = max_line_id
        self.executed = []
        self.executemany = []

    def GetProchainID(self, table):
        self.requested_table = table
        return 10

    def ExecuterReq(self, req):
        self.executed.append(req)

    def ResultatReq(self):
        return [(self.max_line_id,)]

    def Executermany(self, req, donnees, commit=False):
        self.executemany.append((req, donnees, commit))

    def ReqInsert(self, table, donnees):
        return 1


class Owner:
    dict_valeurs = {"IDactivite": 123}


class AssistantBaseLineIdContractTests(unittest.TestCase):
    def test_network_path_never_assigns_or_uses_local_line_identifier(self):
        sauvegarde = load_sauvegarde_tarifs()
        line = FakeTrack("tarifs_lignes")
        tariff = FakeTrack("tarifs", [line])
        db = FakeDB(is_network=True)

        sauvegarde(Owner(), DB=db, listeTarifs=[tariff])

        self.assertFalse(hasattr(line, "IDligne"))
        self.assertEqual(db.executed, [])
        self.assertEqual(len(db.executemany), 2)

    def test_local_path_assigns_sequential_line_identifiers_from_empty_table(self):
        sauvegarde = load_sauvegarde_tarifs()
        line1 = FakeTrack("tarifs_lignes")
        line2 = FakeTrack("tarifs_lignes")
        tariff = FakeTrack("tarifs", [line1, line2])
        db = FakeDB(is_network=False, max_line_id=None)

        sauvegarde(Owner(), DB=db, listeTarifs=[tariff])

        self.assertEqual((line1.IDligne, line2.IDligne), (1, 2))
        self.assertEqual(len(db.executed), 1)
        self.assertEqual(len(db.executemany), 2)

    def test_local_path_continues_after_existing_maximum(self):
        sauvegarde = load_sauvegarde_tarifs()
        line = FakeTrack("tarifs_lignes")
        tariff = FakeTrack("tarifs", [line])
        db = FakeDB(is_network=False, max_line_id=41)

        sauvegarde(Owner(), DB=db, listeTarifs=[tariff])

        self.assertEqual(line.IDligne, 42)

    def test_branch_assignment_gap_is_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE_PATH, SOURCE_ROOT)
        targeted = [
            item
            for item in findings
            if item.get("function") == "Sauvegarde_tarifs" and item.get("name") == "prochainIDligne"
        ]
        self.assertEqual(targeted, [], targeted)


if __name__ == "__main__":
    unittest.main()
