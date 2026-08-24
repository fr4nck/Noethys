#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest

from scripts import audit_wx_lifecycle as audit


class AuditWxLifecycleTests(unittest.TestCase):
    def _path(self):
        return audit.NOETHYS / "Ctrl" / "sample.py"

    def test_non_wx_track_is_not_reported_as_constructor_parent_callback(self):
        source = '''
class Track:
    def __init__(self, parent):
        self.parent = parent
        self.value = parent.GetReponse()
'''
        tree = ast.parse(source)
        findings = audit._scan_constructor_order(self._path(), tree, source.splitlines())
        self.assertEqual(findings, [])

    def test_wx_parent_business_callback_before_layout_is_reported(self):
        source = '''
class CTRL(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        parent.MAJListeCtrl()
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
'''
        tree = ast.parse(source)
        findings = audit._scan_constructor_order(self._path(), tree, source.splitlines())
        kinds = {item["kind"] for item in findings}
        self.assertIn("constructor_parent_callback", kinds)

    def test_callback_reading_late_attribute_is_high_risk(self):
        source = '''
class CTRL(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.MAJ()
        self.bouton_modifier = object()
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))

    def MAJ(self):
        self.bouton_modifier.Enable(True)
'''
        tree = ast.parse(source)
        findings = audit._scan_constructor_order(self._path(), tree, source.splitlines())
        risky = [
            item for item in findings
            if item["kind"] == "constructor_callback_before_dependency"
        ]
        self.assertEqual(len(risky), 1)
        self.assertEqual(risky[0]["dependencies"], ["bouton_modifier"])

    def test_parent_parent_is_reported_as_ancestry_coupling_once(self):
        source = '''
class Page(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.parent = parent

    def Validation(self):
        return self.parent.parent.ctrl_statut.GetID()
'''
        tree = ast.parse(source)
        findings = audit._dedupe(
            audit._scan_parent_coupling(self._path(), tree, source.splitlines())
        )
        ancestry = [
            item for item in findings
            if item["kind"] == "visual_parent_ancestry_coupling"
        ]
        self.assertEqual(len(ancestry), 1)
        self.assertEqual(ancestry[0]["member"], "ctrl_statut")

    def test_get_grand_parent_business_access_is_ancestry_coupling(self):
        source = '''
class Page(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.parent = parent

    def Validation(self):
        return self.GetGrandParent().ctrl_famille.GetID()
'''
        tree = ast.parse(source)
        findings = audit._scan_parent_coupling(self._path(), tree, source.splitlines())
        ancestry = [
            item for item in findings
            if item["kind"] == "visual_parent_ancestry_coupling"
        ]
        self.assertEqual(len(ancestry), 1)
        self.assertEqual(ancestry[0]["member"], "ctrl_famille")

    def test_local_object_used_after_destroy_is_reported(self):
        source = '''
class Dialog(wx.Dialog):
    def OnChoice(self):
        dlg = wx.SingleChoiceDialog(self, "x", "y", [])
        if dlg.ShowModal() == wx.ID_OK:
            dlg.Destroy()
            selection = dlg.GetSelection()
'''
        tree = ast.parse(source)
        findings = audit._scan_use_after_destroy(self._path(), tree, source.splitlines())
        risky = [item for item in findings if item["kind"] == "use_after_destroy"]
        self.assertEqual(len(risky), 1)
        self.assertEqual(risky[0]["member"], "dlg")
        self.assertEqual(risky[0]["destroy_line"], 6)

    def test_destroy_before_following_if_propagates_into_branch(self):
        source = '''
def ouvrir(ok):
    dlg = Fabrique()
    dlg.Destroy()
    if ok:
        valeur = dlg.ctrl_grille
'''
        tree = ast.parse(source)
        findings = audit._scan_use_after_destroy(self._path(), tree, source.splitlines())
        risky = [item for item in findings if item["kind"] == "use_after_destroy"]
        self.assertEqual(len(risky), 1)
        self.assertEqual(risky[0]["member"], "dlg")
        self.assertEqual(risky[0]["destroy_line"], 4)

    def test_return_after_destroy_does_not_create_false_positive(self):
        source = '''
def ouvrir():
    dlg = Fabrique()
    dlg.Destroy()
    return
    dlg.GetSelection()
'''
        tree = ast.parse(source)
        findings = audit._scan_use_after_destroy(self._path(), tree, source.splitlines())
        self.assertEqual(findings, [])

    def test_reassignment_after_destroy_resets_tracking(self):
        source = '''
def ouvrir():
    dlg = Fabrique()
    dlg.Destroy()
    dlg = Fabrique()
    return dlg.GetSelection()
'''
        tree = ast.parse(source)
        findings = audit._scan_use_after_destroy(self._path(), tree, source.splitlines())
        self.assertEqual(findings, [])

    def test_destroy_in_one_branch_does_not_poison_parent_block(self):
        source = '''
def ouvrir(ok):
    dlg = Fabrique()
    if ok:
        dlg.Destroy()
    return dlg.GetSelection()
'''
        tree = ast.parse(source)
        findings = audit._scan_use_after_destroy(self._path(), tree, source.splitlines())
        self.assertEqual(findings, [])

    def test_reusing_same_variable_name_in_nested_branch_is_not_old_object_use(self):
        source = '''
def ouvrir(mode):
    dlg = Fabrique()
    dlg.Destroy()
    if mode == "creation":
        dlg = Fabrique()
        dlg.ShowModal()
        dlg.Destroy()
'''
        tree = ast.parse(source)
        findings = audit._scan_use_after_destroy(self._path(), tree, source.splitlines())
        self.assertEqual(findings, [])

    def test_direct_use_in_if_condition_after_destroy_is_reported(self):
        source = '''
def ouvrir():
    dlg = Fabrique()
    dlg.Destroy()
    if dlg.GetSelection() == 0:
        return
'''
        tree = ast.parse(source)
        findings = audit._scan_use_after_destroy(self._path(), tree, source.splitlines())
        risky = [item for item in findings if item["kind"] == "use_after_destroy"]
        self.assertEqual(len(risky), 1)
        self.assertEqual(risky[0]["member"], "dlg")

    def test_self_attribute_used_after_destroy_is_reported(self):
        source = '''
class Dialog(wx.Dialog):
    def fermer(self):
        self.popup.Destroy()
        self.popup.Layout()
'''
        tree = ast.parse(source)
        findings = audit._scan_use_after_destroy(self._path(), tree, source.splitlines())
        risky = [item for item in findings if item["kind"] == "use_after_destroy"]
        self.assertEqual(len(risky), 1)
        self.assertEqual(risky[0]["member"], "self.popup")


if __name__ == "__main__":
    unittest.main()
