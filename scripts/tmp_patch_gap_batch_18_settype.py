from pathlib import Path

source_path = Path('noethys/Ctrl/CTRL_Questionnaire.py')
source = source_path.read_text(encoding='utf-8')
old = '''    def SetType(self, type="individu"):\n        self.type = type\n        self.Importation()\n        self.MAJ()\n'''
new = '''    def SetType(self, type="individu"):\n        ancien_type = self.type\n        self.type = type\n        try:\n            self.MAJ()\n        except Exception:\n            self.type = ancien_type\n            raise\n'''
if old not in source:
    raise SystemExit('SetType pattern not found')
source = source.replace(old, new, 1)
source_path.write_text(source, encoding='utf-8')

test_path = Path('tests/test_branch_contracts_batch_18.py')
test = test_path.read_text(encoding='utf-8')
addition = '''\n\ndef test_settype_is_transactional_when_target_model_is_invalid():\n    source = SOURCE_PATH.read_text(encoding="utf-8")\n    block = source[source.index("    def SetType("):source.index("    def RAZ(")]\n    assert "ancien_type = self.type" in block\n    assert "self.MAJ()" in block\n    assert "self.Importation()" not in block\n    assert "self.type = ancien_type" in block\n    assert "except Exception:" in block\n'''
if 'test_settype_is_transactional_when_target_model_is_invalid' not in test:
    test += addition
    test_path.write_text(test, encoding='utf-8')
