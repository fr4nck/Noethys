from pathlib import Path

p = Path('noethys/Dlg/DLG_Badgeage_saisie_procedure.py')
s = p.read_text(encoding='utf-8')
a = s.index('    def Sauvegarde(self):\n')
b = s.index('    def GetIDprocedure(self):\n', a)
new = '''    def Sauvegarde(self):
        """ Sauvegarde transactionnelle de la procédure, des actions et des messages. """
        DB = GestionDB.DB()
        ok = True
        nouvelIDprocedure = self.IDprocedure

        nom = self.ctrl_nom.GetValue()
        style = self.ctrl_interface.ctrl_style.GetID()
        theme = self.ctrl_interface.ctrl_theme.GetID()
        if theme == "personnalise" :
            image = self.ctrl_interface.ctrl_image.GetValue()
        else :
            image = None
        if self.ctrl_interface.radio_barre.GetValue() : systeme = "barre_numerique"
        if self.ctrl_interface.radio_clavier.GetValue() : systeme = "clavier_numerique"
        if self.ctrl_interface.radio_liste.GetValue() : systeme = "liste_individus"
        if self.ctrl_interface.check_activites.GetValue() == True :
            activites = self.ctrl_interface.ctrl_activites.GetTexteCoches()
        else :
            activites = None
        confirmation = int(self.check_confirmation.GetValue())
        vocal = int(self.check_vocal.GetValue())
        tutoiement = int(self.check_tutoiement.GetValue())

        listeDonnees = [
                ("nom", nom),
                ("defaut", self.defaut),
                ("style", style),
                ("theme", theme),
                ("image", image),
                ("systeme", systeme),
                ("activites", activites),
                ("confirmation", confirmation),
                ("vocal", vocal),
                ("tutoiement", tutoiement),
            ]
        if nouvelIDprocedure == None :
            nouvelIDprocedure = DB.ReqInsert("badgeage_procedures", listeDonnees, commit=False)
            if nouvelIDprocedure is None :
                ok = False
        else:
            if not DB.ReqMAJ("badgeage_procedures", listeDonnees, "IDprocedure", nouvelIDprocedure, commit=False) :
                ok = False

        listeActions = self.ctrl_actions.GetDonnees()
        listeChamps = []
        for nom, type, info in DICT_TABLES["badgeage_actions"] :
            listeChamps.append(nom)

        ordre = 1
        listeIDaction = []
        listeIDmessage = []
        if ok :
            for dictAction in listeActions :
                IDaction = dictAction["IDaction"]
                listeDonnees = [("IDprocedure", nouvelIDprocedure), ("ordre", ordre), ]
                for code in listeChamps :
                    if code not in ("IDaction", "IDprocedure", "ordre") :
                        if code in dictAction :
                            valeur = dictAction[code]
                        else :
                            valeur = None
                        listeDonnees.append((code, valeur))

                if IDaction == None :
                    IDaction = DB.ReqInsert("badgeage_actions", listeDonnees, commit=False)
                    if IDaction is None :
                        ok = False
                        break
                else:
                    if not DB.ReqMAJ("badgeage_actions", listeDonnees, "IDaction", IDaction, commit=False) :
                        ok = False
                        break

                if "action_messages" in dictAction :
                    for IDmessage, message in dictAction["action_messages"] :
                        if IDmessage == None :
                            IDmessage = DB.ReqInsert("badgeage_messages", [("IDprocedure", nouvelIDprocedure), ("IDaction", IDaction), ("message", message)], commit=False)
                            if IDmessage is None :
                                ok = False
                                break
                        else:
                            if not DB.ReqMAJ("badgeage_messages", [("message", message),], "IDmessage", IDmessage, commit=False) :
                                ok = False
                                break
                        listeIDmessage.append(IDmessage)
                    if not ok :
                        break

                listeIDaction.append(IDaction)
                ordre += 1

        # Supprimer d'abord les messages, puis les actions devenues obsolètes.
        if ok :
            for IDmessage in self.listeInitialeMessages :
                if IDmessage not in listeIDmessage :
                    if not DB.ReqDEL("badgeage_messages", "IDmessage", IDmessage, commit=False) :
                        ok = False
                        break

        if ok :
            for IDaction in self.listeInitialeActions :
                if IDaction not in listeIDaction :
                    if not DB.ReqDEL("badgeage_actions", "IDaction", IDaction, commit=False) :
                        ok = False
                        break

        if ok :
            DB.Commit()
        else:
            try:
                DB.connexion.rollback()
            except Exception:
                pass
        DB.Close()

        if not ok :
            dlg = wx.MessageDialog(self, _(u"Une erreur est survenue pendant l'enregistrement de la procédure de badgeage. Aucune modification n'a été conservée."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        self.IDprocedure = nouvelIDprocedure
        return True

'''
s = s[:a] + new + s[b:]
s = '\n'.join(line.rstrip() for line in s.splitlines()) + '\n'
p.write_text(s, encoding='utf-8')
