from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Dlg" / "DLG_Export_compta.py"


def _source():
    return SOURCE.read_text(encoding="utf-8")


def test_get_keys_dict_tries_iterates_sorted_list_instead_of_calling_it():
    source = _source()
    block = source[source.index("def GetKeysDictTries"):source.index("def Export_ebp_compta")]
    assert "for keyTemp, ID in listeKeys :" in block
    assert "for keyTemp, ID in listeKeys() :" not in block


def test_reglement_mode_exports_its_own_accounting_code():
    source = _source()
    start = source.index("def GetReglements_Modes")
    end = source.index("def GetReglements_Depots", start)
    block = source[start:end]
    assert '"code_compta" : dictMode["code_compta"]' in block
    assert '"code_compta" : code_compta' not in block
