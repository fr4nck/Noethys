from pathlib import Path

p = Path('noethys/Dlg/DLG_Saisie_depot.py')
s = p.read_text(encoding='utf-8')

# OnBoutonOk: la sauvegarde du dépôt inclut désormais les règlements.
s = s.replace('''        # Sauvegarde des paramètres\n        etat = self.Sauvegarde_depot() \n        if etat == False :\n            return\n        # Sauvegarde des règlements\n        self.Sauvegarde_reglements()\n''','''        # Sauvegarde atomique du dépôt et des règlements\n        etat = self.Sauvegarde_depot()\n        if etat == False :\n            return\n''',1)

start = s.index('    def Sauvegarde_depot(self):\n')
end = s.index('    def GetIDdepot(self):\n', start)
old = s[start:end]
new = '''    def Sauvegarde_depot(self):
        # Nom
        nom = self.ctrl_nom.GetValue()
        if nom == "" :
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement saisir un nom. Exemple : 'Chèques - Juillet 2010'... !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
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

        # Verrouillage
        verrouillage = 1 if self.ctrl_verrouillage.GetValue() else 0

        # Compte
        IDcompte = self.ctrl_compte.GetID()
        if IDcompte == 0 :
            IDcompte = None
            dlg = wx.MessageDialog(self, _(u"Etes-vous sûr de ne pas vouloir sélectionner de compte bancaire pour ce dépôt ?"), _(u"Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return False

        observations = self.ctrl_observations.GetValue()
        code_compta = self.ctrl_code_compta.GetValue()

        DB = GestionDB.DB()
        ok = True
        nouvelIDdepot = self.IDdepot
        listeDonnees = [
            ("nom", nom),
            ("date", date),
            ("verrouillage", verrouillage),
            ("IDcompte", IDcompte),
            ("observations", observations),
            ("code_compta", code_compta),
            ]

        if nouvelIDdepot == None :
            nouvelIDdepot = DB.ReqInsert("depots", listeDonnees, commit=False)
            if nouvelIDdepot is None :
                ok = False
        else :
            if not DB.ReqMAJ("depots", listeDonnees, "IDdepot", nouvelIDdepot, commit=False) :
                ok = False

        if ok :
            ok = self.Sauvegarde_reglements(DB=DB, IDdepot=nouvelIDdepot, commit=False)

        if ok :
            DB.Commit()
        else :
            try :
                DB.connexion.rollback()
            except Exception :
                pass
        DB.Close()

        if not ok :
            dlg = wx.MessageDialog(self, _(u"Une erreur est survenue pendant l'enregistrement du dépôt et de ses règlements. Aucune modification n'a été conservée."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        self.IDdepot = nouvelIDdepot
        return True

    def Sauvegarde_reglements(self, DB=None, IDdepot=None, commit=True):
        """Rattache/détache les règlements, dans la transaction fournie si nécessaire."""
        DBexterne = DB is not None
        if DB is None :
            DB = GestionDB.DB()
        if IDdepot is None :
            IDdepot = self.IDdepot

        ok = True
        for track in self.tracks :
            nouvelleValeur = None
            modifier = False
            if track.IDdepot == None and track.inclus == True :
                nouvelleValeur = IDdepot
                modifier = True
            elif track.IDdepot != None and track.inclus == False :
                nouvelleValeur = None
                modifier = True

            if modifier :
                if not DB.ReqMAJ("reglements", [("IDdepot", nouvelleValeur),], "IDreglement", track.IDreglement, commit=False) :
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
s = s[:start] + new + s[end:]
s = '\n'.join(line.rstrip() for line in s.splitlines()) + '\n'
p.write_text(s, encoding='utf-8')
