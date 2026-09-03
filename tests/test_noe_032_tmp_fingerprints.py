# -*- coding: utf-8 -*-
import unittest

from scripts import qualify_branch_assignment_gaps as audit


class TemporaryFingerprintProbe(unittest.TestCase):
    def test_print_current_noe032b_fingerprints(self):
        report = audit.build_report()
        targets = []
        for item in report["findings"]:
            if (
                item["file"] == "Utils/UTILS_Sauvegarde.py"
                and item["function"] == "Sauvegarde"
                and item["name"] in {"fichierDest", "dictAdresse", "err"}
            ):
                targets.append(audit.qualification_key(item))
        self.fail("NOE032B_FINGERPRINTS=%r" % (targets,))


if __name__ == "__main__":
    unittest.main()
