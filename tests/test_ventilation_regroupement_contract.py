import ast
import decimal
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as branch_audit


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_Ventilation.py"


def extract_method(class_name, method_name, namespace=None):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method_name:
                    module = ast.Module(body=[item], type_ignores=[])
                    ast.fix_missing_locations(module)
                    scope = {} if namespace is None else dict(namespace)
                    exec(compile(module, str(SOURCE), "exec"), scope)
                    return scope[method_name]
    raise AssertionError("Méthode introuvable : %s.%s" % (class_name, method_name))


class VentilationRegroupementContractTests(unittest.TestCase):
    def test_set_regroupement_rejects_unknown_key_before_mutating_state(self):
        method = extract_method("CTRL_Ventilation", "SetRegroupement")

        class Dummy:
            def __init__(self):
                self.KeyRegroupement = "periode"
                self.maj_calls = 0

            def MAJ(self):
                self.maj_calls += 1

        dummy = Dummy()
        method(dummy, "facture")
        self.assertEqual("facture", dummy.KeyRegroupement)
        self.assertEqual(1, dummy.maj_calls)

        with self.assertRaises(ValueError):
            method(dummy, "inconnu")
        self.assertEqual("facture", dummy.KeyRegroupement)
        self.assertEqual(1, dummy.maj_calls)

    def test_radio_handler_does_nothing_if_no_choice_is_active(self):
        method = extract_method("CTRL", "OnRadioRegroupement")

        class Radio:
            def __init__(self, value=False):
                self.value = value

            def GetValue(self):
                return self.value

        class Ventilation:
            def __init__(self):
                self.calls = []

            def SetRegroupement(self, key):
                self.calls.append(key)

        class Dummy:
            pass

        dummy = Dummy()
        dummy.radio_periode = Radio(False)
        dummy.radio_facture = Radio(False)
        dummy.radio_individu = Radio(False)
        dummy.radio_date = Radio(False)
        dummy.ctrl_ventilation = Ventilation()

        method(dummy, None)
        self.assertEqual([], dummy.ctrl_ventilation.calls)

        dummy.radio_facture.value = True
        method(dummy, None)
        self.assertEqual(["facture"], dummy.ctrl_ventilation.calls)

    def test_non_finite_amount_is_rejected_before_status_comparisons(self):
        def float_to_decimal(value=0.0):
            if isinstance(value, decimal.Decimal):
                return value
            return decimal.Decimal(str(value))

        method = extract_method(
            "CTRL",
            "MAJinfos",
            {
                "FloatToDecimal": float_to_decimal,
                "_": lambda text: text,
                "SYMBOLE": "€",
            },
        )

        class Image:
            def __init__(self):
                self.bitmap = None

            def SetBitmap(self, bitmap):
                self.bitmap = bitmap

        class Info:
            def __init__(self):
                self.label = None

            def SetLabel(self, label):
                self.label = label

            def GetLabel(self):
                return self.label

        class Ventilation:
            def GetTotalRestePrestationsAVentiler(self):
                return decimal.Decimal("10")

        class Dummy:
            pass

        dummy = Dummy()
        dummy.montant_reglement = decimal.Decimal("NaN")
        dummy.total_ventilation = decimal.Decimal("0")
        dummy.ctrl_ventilation = Ventilation()
        dummy.ctrl_image = Image()
        dummy.ctrl_info = Info()
        dummy.imgErreur = object()

        method(dummy)

        self.assertEqual("erreur", dummy.validation)
        self.assertIs(dummy.imgErreur, dummy.ctrl_image.bitmap)
        self.assertEqual("Vous avez saisi un montant non valide !", dummy.ctrl_info.label)

    def test_ctrl_ventilation_has_no_branch_assignment_gap_left(self):
        findings = branch_audit.scan_file(SOURCE.resolve())
        self.assertEqual([], findings)


if __name__ == "__main__":
    unittest.main()
