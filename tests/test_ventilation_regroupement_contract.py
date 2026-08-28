import ast
import decimal
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as branch_audit


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_Ventilation.py"


def extract_function(function_name, namespace=None):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            module = ast.Module(body=[node], type_ignores=[])
            ast.fix_missing_locations(module)
            scope = {} if namespace is None else dict(namespace)
            exec(compile(module, str(SOURCE), "exec"), scope)
            return scope[function_name]
    raise AssertionError("Fonction introuvable : %s" % function_name)


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


def float_to_decimal(value=0.0):
    if value is None:
        value = 0.0
    if isinstance(value, str):
        value = float(value)
    return decimal.Decimal("%.2f" % value)


def finite_converter():
    return extract_function(
        "FloatToDecimalFini",
        {"decimal": decimal, "FloatToDecimal": float_to_decimal},
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


class Dummy:
    pass


class VentilationRegroupementContractTests(unittest.TestCase):
    def extract_majinfos(self):
        return extract_method(
            "CTRL",
            "MAJinfos",
            {
                "decimal": decimal,
                "FloatToDecimal": float_to_decimal,
                "FloatToDecimalFini": finite_converter(),
                "_": lambda text: text,
                "SYMBOLE": "€",
            },
        )

    def make_majinfos_dummy(self, montant, total, ventilation):
        dummy = Dummy()
        dummy.montant_reglement = montant
        dummy.total_ventilation = total
        dummy.ctrl_ventilation = ventilation
        dummy.ctrl_image = Image()
        dummy.ctrl_info = Info()
        dummy.imgErreur = object()
        return dummy

    def assert_invalid_amount(self, dummy):
        self.assertEqual("erreur", dummy.validation)
        self.assertIs(dummy.imgErreur, dummy.ctrl_image.bitmap)
        self.assertEqual("Vous avez saisi un montant non valide !", dummy.ctrl_info.label)

    def test_set_regroupement_rejects_unknown_key_before_mutating_state(self):
        method = extract_method("CTRL_Ventilation", "SetRegroupement")

        class Grid:
            def __init__(self):
                self.KeyRegroupement = "periode"
                self.maj_calls = 0

            def MAJ(self):
                self.maj_calls += 1

        dummy = Grid()
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

    def test_signaling_nan_is_rejected_before_historical_formatter(self):
        calls = []

        def formatter(value=0.0):
            calls.append(value)
            raise AssertionError("Le formateur historique ne doit pas recevoir un sNaN")

        converter = extract_function(
            "FloatToDecimalFini",
            {"decimal": decimal, "FloatToDecimal": formatter},
        )

        self.assertIsNone(converter(decimal.Decimal("sNaN")))
        self.assertEqual([], calls)

    def test_equal_infinities_are_rejected_before_subtraction(self):
        class Ventilation:
            def GetTotalRestePrestationsAVentiler(self):
                raise AssertionError("L'agrégation ne doit pas démarrer avec des opérandes invalides")

        dummy = self.make_majinfos_dummy(
            decimal.Decimal("Infinity"),
            decimal.Decimal("Infinity"),
            Ventilation(),
        )

        self.extract_majinfos()(dummy)
        self.assert_invalid_amount(dummy)

    def test_aggregation_decimal_error_is_converted_to_invalid_amount(self):
        class Ventilation:
            def GetTotalRestePrestationsAVentiler(self):
                raise decimal.InvalidOperation

        dummy = self.make_majinfos_dummy(
            decimal.Decimal("10"),
            decimal.Decimal("2"),
            Ventilation(),
        )

        self.extract_majinfos()(dummy)
        self.assert_invalid_amount(dummy)

    def test_non_finite_aggregated_remainder_is_rejected(self):
        class Ventilation:
            def GetTotalRestePrestationsAVentiler(self):
                return decimal.Decimal("Infinity")

        dummy = self.make_majinfos_dummy(
            decimal.Decimal("10"),
            decimal.Decimal("2"),
            Ventilation(),
        )

        self.extract_majinfos()(dummy)
        self.assert_invalid_amount(dummy)

    def test_ctrl_ventilation_has_no_branch_assignment_gap_left(self):
        findings = branch_audit.scan_file(SOURCE.resolve())
        self.assertEqual([], findings)


if __name__ == "__main__":
    unittest.main()
