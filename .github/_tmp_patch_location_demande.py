from pathlib import Path

# 1) Questionnaire: respecter une transaction externe et retourner True/False.
p=Path('noethys/Ctrl/CTRL_Questionnaire.py')
s=p.read_text(encoding='utf-8')
a=s.index('    def Sauvegarde(self, DB=None, IDdonnee=None):\n')
b=s.index('\n\n# -------------------------------------------------------------------------------------------------------------------------------------------', a)
x=s[a:b]
x=x.replace('''        if DB == None :\n            DBT = GestionDB.DB()\n        else :\n            DBT = DB\n''','''        DBexterne = DB is not None\n        if DB == None :\n            DBT = GestionDB.DB()\n        else :\n            DBT = DB\n        ok = True\n''',1)
x=x.replace('IDreponse = DBT.ReqInsert("questionnaire_reponses", listeDonnees)','IDreponse = DBT.ReqInsert("questionnaire_reponses", listeDonnees, commit=not DBexterne)\n                        if IDreponse is None:\n                            ok = False\n                            break')
x=x.replace('DBT.ReqMAJ("questionnaire_reponses", listeDonnees, "IDreponse", IDreponse)','if not DBT.ReqMAJ("questionnaire_reponses", listeDonnees, "IDreponse", IDreponse, commit=not DBexterne):\n                            ok = False\n                            break')
x=x.replace('DBT.ReqDEL("questionnaire_reponses", "IDreponse", IDreponse)','if not DBT.ReqDEL("questionnaire_reponses", "IDreponse", IDreponse, commit=not DBexterne):\n                            ok = False\n                            break')
x=x.replace('''        if DB == None :\n            DBT.Close()\n\n        # Sauvegarde les données si nouveautés\n''','''        if DB == None :\n            DBT.Close()\n\n        if not ok:\n            return False\n        return True\n\n        # Sauvegarde les données si nouveautés\n''',1)
s=s[:a]+x+s[b:]
s='\n'.join(line.rstrip() for line in s.splitlines())+'\n'
p.write_text(s,encoding='utf-8')

# 2) Demande de location: demande + filtres + questionnaire dans une transaction.
p=Path('noethys/Dlg/DLG_Saisie_location_demande.py')
s=p.read_text(encoding='utf-8')
a=s.index('        # Sauvegarde\n        DB = GestionDB.DB()\n')
b=s.index('        # Fermeture de la fenêtre\n',a)
old=s[a:b]
new='''        # Sauvegarde transactionnelle de la demande, des filtres et du questionnaire\n        DB = GestionDB.DB()\n        ok = True\n        nouvelIDdemande = self.IDdemande\n        listeDonnees = [\n            ("date", date_demande),\n            ("IDfamille", IDfamille),\n            ("observations", observations),\n            ("categories", categories),\n            ("produits", produits),\n            ("statut", statut),\n            ("motif_refus", motif_refus),\n            ("IDlocation", IDlocation),\n            ]\n\n        if nouvelIDdemande == None :\n            nouvelIDdemande = DB.ReqInsert("locations_demandes", listeDonnees, commit=False)\n            if nouvelIDdemande is None:\n                ok = False\n        else:\n            if not DB.ReqMAJ("locations_demandes", listeDonnees, "IDdemande", nouvelIDdemande, commit=False):\n                ok = False\n\n        listeID = []\n        if ok:\n            for dictFiltre in self.notebook.GetPage("criteres").ctrl_filtres.GetDonnees():\n                IDfiltre = dictFiltre["IDfiltre"]\n                listeDonnees = [\n                    ("IDquestion", dictFiltre["IDquestion"]),\n                    ("categorie", "location_demande"),\n                    ("choix", dictFiltre["choix"]),\n                    ("criteres", dictFiltre["criteres"]),\n                    ("IDdonnee", nouvelIDdemande),\n                    ]\n                if IDfiltre == None:\n                    IDfiltre = DB.ReqInsert("questionnaire_filtres", listeDonnees, commit=False)\n                    if IDfiltre is None:\n                        ok = False\n                        break\n                else:\n                    if not DB.ReqMAJ("questionnaire_filtres", listeDonnees, "IDfiltre", IDfiltre, commit=False):\n                        ok = False\n                        break\n                listeID.append(IDfiltre)\n\n        if ok:\n            for dictInitialFiltre in self.listeInitialeFiltres:\n                IDfiltre = dictInitialFiltre["IDfiltre"]\n                if IDfiltre not in listeID:\n                    if not DB.ReqDEL("questionnaire_filtres", "IDfiltre", IDfiltre, commit=False):\n                        ok = False\n                        break\n\n        if ok:\n            if self.notebook.GetPage("questionnaire").ctrl_questionnaire.Sauvegarde(DB=DB, IDdonnee=nouvelIDdemande) is False:\n                ok = False\n\n        if ok:\n            DB.Commit()\n        else:\n            try:\n                DB.connexion.rollback()\n            except Exception:\n                pass\n        DB.Close()\n\n        if not ok:\n            dlg = wx.MessageDialog(self, _(u"Une erreur est survenue pendant l'enregistrement de la demande de location. Aucune modification n'a été conservée."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)\n            dlg.ShowModal()\n            dlg.Destroy()\n            return False\n\n        self.IDdemande = nouvelIDdemande\n\n'''
s=s[:a]+new+s[b:]
s='\n'.join(line.rstrip() for line in s.splitlines())+'\n'
p.write_text(s,encoding='utf-8')
