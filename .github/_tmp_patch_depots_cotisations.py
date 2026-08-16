from pathlib import Path

# 1) Suppression depot de reglements: ne rafraichir l'UI qu'en cas de suppression reussie.
p = Path('noethys/Ol/OL_Depots.py')
s = p.read_text(encoding='utf-8')
old = '''        if dlg.ShowModal() == wx.ID_YES :\n            DB = GestionDB.DB()\n            DB.ReqDEL("depots", "IDdepot", IDdepot)\n            DB.Close() \n            self.MAJ()\n            self.GetGrandParent().MAJreglements()\n'''
new = '''        if dlg.ShowModal() == wx.ID_YES :\n            DB = GestionDB.DB()\n            resultat = DB.ReqDEL("depots", "IDdepot", IDdepot)\n            DB.Close()\n            if resultat :\n                self.MAJ()\n                self.GetGrandParent().MAJreglements()\n            else :\n                dlgErreur = wx.MessageDialog(self, _(u"La suppression du dépôt a échoué. Aucune modification n'a été effectuée."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)\n                dlgErreur.ShowModal()\n                dlgErreur.Destroy()\n'''
if old not in s:
    raise SystemExit('OL_Depots.py: bloc attendu introuvable')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# 2) Depot de cotisations: transaction unique depot + rattachements.
p = Path('noethys/Dlg/DLG_Saisie_depot_cotisation.py')
s = p.read_text(encoding='utf-8')
old_ok = '''    def OnBoutonOk(self, event): \n        # Sauvegarde des paramètres\n        etat = self.Sauvegarde_depot() \n        if etat == False :\n            return\n        # Sauvegarde des règlements\n        self.Sauvegarde_cotisations()\n        # Fermeture\n        self.EndModal(wx.ID_OK)\n'''
new_ok = '''    def OnBoutonOk(self, event):\n        # Sauvegarde atomique du dépôt et des cotisations\n        etat = self.Sauvegarde_depot()\n        if etat == False :\n            return\n        # Fermeture\n        self.EndModal(wx.ID_OK)\n'''
if old_ok not in s:
    raise SystemExit('DLG_Saisie_depot_cotisation.py: OnBoutonOk introuvable')
s = s.replace(old_ok, new_ok, 1)
start = s.index('    def Sauvegarde_depot(self):\n')
end = s.index('    def GetIDdepotCotisation(self):\n', start)
new_block = '''    def Sauvegarde_depot(self):
        # Nom
        nom = self.ctrl_nom.GetValue()
        if nom == "" :
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement saisir un nom. Exemple : 'Cotisations de Juillet 2010'... !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_nom.SetFocus()
            return False

        # Date
        date = self.ctrl_date.GetDate()
        if date == None :
            dlg = wx.MessageDialog(self, _(u"Etes-vous sûr de ne pas vouloir saisir de date de dépôt ?"), _(u"Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return False

        verrouillage = 1 if self.ctrl_verrouillage.GetValue() else 0
        observations = self.ctrl_observations.GetValue()

        DB = GestionDB.DB()
        ok = True
        nouvelIDdepot = self.IDdepot_cotisation
        listeDonnees = [
            ("nom", nom),
            ("date", date),
            ("verrouillage", verrouillage),
            ("observations", observations),
            ]

        if nouvelIDdepot == None :
            nouvelIDdepot = DB.ReqInsert("depots_cotisations", listeDonnees, commit=False)
            if nouvelIDdepot is None :
                ok = False
        else :
            if not DB.ReqMAJ("depots_cotisations", listeDonnees, "IDdepot_cotisation", nouvelIDdepot, commit=False) :
                ok = False

        if ok :
            ok = self.Sauvegarde_cotisations(DB=DB, IDdepot_cotisation=nouvelIDdepot, commit=False)

        if ok :
            DB.Commit()
        else :
            try :
                DB.connexion.rollback()
            except Exception :
                pass
        DB.Close()

        if not ok :
            dlg = wx.MessageDialog(self, _(u"Une erreur est survenue pendant l'enregistrement du dépôt et de ses cotisations. Aucune modification n'a été conservée."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        self.IDdepot_cotisation = nouvelIDdepot
        return True

    def Sauvegarde_cotisations(self, DB=None, IDdepot_cotisation=None, commit=True):
        """Rattache/détache les cotisations dans la transaction fournie si nécessaire."""
        DBexterne = DB is not None
        if DB is None :
            DB = GestionDB.DB()
        if IDdepot_cotisation is None :
            IDdepot_cotisation = self.IDdepot_cotisation

        ok = True
        for track in self.tracks :
            nouvelleValeur = None
            modifier = False
            if track.IDdepot_cotisation == None and track.inclus == True :
                nouvelleValeur = IDdepot_cotisation
                modifier = True
            elif track.IDdepot_cotisation != None and track.inclus == False :
                nouvelleValeur = None
                modifier = True

            if modifier :
                if not DB.ReqMAJ("cotisations", [("IDdepot_cotisation", nouvelleValeur),], "IDcotisation", track.IDcotisation, commit=False) :
                    ok = False
                    break

        if not DBexterne :
            if ok and commit :
                DB.Commit()
            elif not ok :
                try :
                    DB.connexion.rollback()
                except Exception :
                    pass
            DB.Close()

        return ok

'''
s = s[:start] + new_block + s[end:]
p.write_text(s, encoding='utf-8')

# 3) Suppression depot de cotisations: même garde-fou.
p = Path('noethys/Ol/OL_Depots_cotisations.py')
s = p.read_text(encoding='utf-8')
old = '''        if dlg.ShowModal() == wx.ID_YES :\n            DB = GestionDB.DB()\n            DB.ReqDEL("depots_cotisations", "IDdepot_cotisation", IDdepot_cotisation)\n            DB.Close() \n            self.MAJ()\n            self.GetGrandParent().MAJcotisations()\n'''
new = '''        if dlg.ShowModal() == wx.ID_YES :\n            DB = GestionDB.DB()\n            resultat = DB.ReqDEL("depots_cotisations", "IDdepot_cotisation", IDdepot_cotisation)\n            DB.Close()\n            if resultat :\n                self.MAJ()\n                self.GetGrandParent().MAJcotisations()\n            else :\n                dlgErreur = wx.MessageDialog(self, _(u"La suppression du dépôt de cotisations a échoué. Aucune modification n'a été effectuée."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)\n                dlgErreur.ShowModal()\n                dlgErreur.Destroy()\n'''
if old not in s:
    raise SystemExit('OL_Depots_cotisations.py: bloc attendu introuvable')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
