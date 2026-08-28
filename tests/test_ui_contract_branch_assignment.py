import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as branch_audit
from scripts import qualify_branch_assignment_gaps as qualified


class UIContractBranchAssignmentTests(unittest.TestCase):
    def test_timeline_toolbar_position_is_exhaustively_validated(self):
        path = qualified.ROOT / "Ctrl" / "CTRL_Timeline.py"
        self.assertEqual(branch_audit.scan_file(path), [])

        source = Path(path).read_text(encoding="utf-8")
        self.assertIn('elif positionToolbar in ("haut", "bas")', source)
        self.assertIn('raise ValueError("positionToolbar invalide : %s" % positionToolbar)', source)

    def test_messagebox_icon_is_validated_before_art_provider_use(self):
        path = qualified.ROOT / "Dlg" / "DLG_Messagebox.py"
        self.assertEqual(branch_audit.scan_file(path), [])

        source = Path(path).read_text(encoding="utf-8")
        self.assertIn("if icone not in dict_artid", source)
        self.assertIn('raise ValueError("icone de message inconnue : %r" % (icone,))', source)
        self.assertIn("artid = dict_artid[icone]", source)


if __name__ == "__main__":
    unittest.main()
