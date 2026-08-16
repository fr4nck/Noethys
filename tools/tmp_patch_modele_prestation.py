from pathlib import Path
p = Path('noethys/Dlg/DLG_Appliquer_modele_prestation.py')
s = p.read_text(encoding='utf-8')
old = '''        DB.ExecuterReq(req)\n        listeDonnees = DB.ResultatReq()\n        IDcompte_payeur = listeDonnees[0][0]\n\n        # Sauvegarde de la prestation\n'''
new = '''        DB.ExecuterReq(req)\n        listeDonnees = DB.ResultatReq()\n        if not listeDonnees:\n            DB.Close()\n            dlg = wx.MessageDialog(self, _(u"Aucun compte payeur n'est associé à cette famille."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)\n            dlg.ShowModal()\n            dlg.Destroy()\n            return\n        IDcompte_payeur = listeDonnees[0][0]\n\n        # Sauvegarde de la prestation\n'''
if old not in s:
    raise SystemExit('bloc compte payeur introuvable')
s = s.replace(old, new, 1)
old2 = '''        self.IDprestation = DB.ReqInsert("prestations", listeDonnees)\n        DB.Close()\n\n        # Fermeture de la fenêtre\n        self.EndModal(wx.ID_OK)\n'''
new2 = '''        IDprestation = DB.ReqInsert("prestations", listeDonnees, commit=False)\n        if IDprestation is None:\n            try:\n                DB.connexion.rollback()\n            except Exception:\n                pass\n            DB.Close()\n            dlg = wx.MessageDialog(self, _(u"La création de la prestation a échoué."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)\n            dlg.ShowModal()\n            dlg.Destroy()\n            return\n\n        DB.Commit()\n        DB.Close()\n        self.IDprestation = IDprestation\n\n        # Fermeture de la fenêtre\n        self.EndModal(wx.ID_OK)\n'''
if old2 not in s:
    raise SystemExit('bloc insert prestation introuvable')
s = s.replace(old2, new2, 1)
p.write_text(s, encoding='utf-8')
