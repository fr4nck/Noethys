from pathlib import Path

ctrl_path = Path('noethys/Ctrl/CTRL_Questionnaire.py')
ctrl = ctrl_path.read_text(encoding='utf-8')
old_maj = '''    def MAJ(self, importation=True, selection=None):
        """ Met à jour (redessine) tout le contrôle """
        self.Freeze()
        try:
            if importation == True :
                ancien_modele = (self.dictCategories, self.listeIDcategorie, self.dictValeursInitiales, self.dictReponses)
                try:
                    self.Importation()
                    controles_valides = {
                        None, "ligne_texte", "bloc_texte", "entier", "decimal", "montant",
                        "liste_deroulante", "liste_coches", "case_coche", "date", "slider",
                        "couleur", "documents", "codebarres", "rfid",
                    }
                    for IDcategorie in self.listeIDcategorie:
                        for track in self.dictCategories[IDcategorie]["questions"]:
                            if track.controle not in controles_valides:
                                raise ValueError("Type de contrôle de questionnaire inconnu : %s" % track.controle)
                except Exception:
                    self.dictCategories, self.listeIDcategorie, self.dictValeursInitiales, self.dictReponses = ancien_modele
                    raise
            self.DeleteAllItems()
            # Création de la racine
            self.root = self.AddRoot(_(u"Racine"))
            # Création des contrôles
            self.Remplissage(selection=selection)
            # Mémorisation des valeurs initiales
            if importation == True :
                self.dictValeursInitiales = self.GetValeurs()
        finally:
            self.Thaw()
'''
new_maj = '''    def MAJ(self, importation=True, selection=None):
        """ Met à jour (redessine) tout le contrôle """
        ancien_modele = (self.dictCategories, self.listeIDcategorie, self.dictValeursInitiales, self.dictReponses)
        self.Freeze()
        try:
            if importation == True :
                self.Importation()
                controles_valides = {
                    None, "ligne_texte", "bloc_texte", "entier", "decimal", "montant",
                    "liste_deroulante", "liste_coches", "case_coche", "date", "slider",
                    "couleur", "documents", "codebarres", "rfid",
                }
                for IDcategorie in self.listeIDcategorie:
                    for track in self.dictCategories[IDcategorie]["questions"]:
                        if track.controle not in controles_valides:
                            raise ValueError("Type de contrôle de questionnaire inconnu : %s" % track.controle)
            self.DeleteAllItems()
            # Création de la racine
            self.root = self.AddRoot(_(u"Racine"))
            # Création des contrôles
            self.Remplissage(selection=selection)
            # Mémorisation des valeurs initiales
            if importation == True :
                self.dictValeursInitiales = self.GetValeurs()
        except Exception:
            self.dictCategories, self.listeIDcategorie, self.dictValeursInitiales, self.dictReponses = ancien_modele
            self.DeleteAllItems()
            self.root = self.AddRoot(_(u"Racine"))
            self.Remplissage(selection=selection)
            raise
        finally:
            self.Thaw()
'''
if old_maj not in ctrl:
    raise SystemExit('MAJ pattern not found')
ctrl = ctrl.replace(old_maj, new_maj, 1)
ctrl_path.write_text(ctrl, encoding='utf-8')

dlg_path = Path('noethys/Dlg/DLG_Questionnaires.py')
dlg = dlg_path.read_text(encoding='utf-8')
old_choice = '''    def OnChoixType(self, event): \n        self.type = self.ctrl_type.GetID()\n        self.ctrl_questionnaire.SetType(self.type)\n'''
new_choice = '''    def OnChoixType(self, event): \n        ancien_type = self.type\n        nouveau_type = self.ctrl_type.GetID()\n        try:\n            self.ctrl_questionnaire.SetType(nouveau_type)\n        except Exception:\n            self.type = ancien_type\n            self.ctrl_type.SetID(ancien_type)\n            raise\n        self.type = nouveau_type\n'''
if old_choice not in dlg:
    raise SystemExit('OnChoixType pattern not found')
dlg = dlg.replace(old_choice, new_choice, 1)
dlg_path.write_text(dlg, encoding='utf-8')

test_path = Path('tests/test_branch_contracts_batch_18.py')
test = test_path.read_text(encoding='utf-8')
marker = '\n\nif __name__ == "__main__":\n    unittest.main()\n'
addition = '''\n    def test_maj_rolls_back_model_and_tree_on_render_failure(self):\n        source = SOURCE_PATH.read_text(encoding="utf-8")\n        maj = source[source.index("    def MAJ("):source.index("    def Importation(")]\n        self.assertLess(maj.index("ancien_modele ="), maj.index("self.Importation()"))\n        self.assertIn("except Exception:", maj)\n        rollback = maj[maj.index("except Exception:"):]\n        self.assertIn("= ancien_modele", rollback)\n        self.assertIn("self.DeleteAllItems()", rollback)\n        self.assertIn("self.Remplissage(selection=selection)", rollback)\n\n    def test_dialog_type_choice_rolls_back_when_settype_fails(self):\n        dlg_path = ROOT / "noethys" / "Dlg" / "DLG_Questionnaires.py"\n        source = dlg_path.read_text(encoding="utf-8")\n        block = source[source.index("    def OnChoixType("):source.index("    def OnBoutonAjouter(")]\n        self.assertIn("ancien_type = self.type", block)\n        self.assertIn("nouveau_type = self.ctrl_type.GetID()", block)\n        self.assertIn("self.ctrl_questionnaire.SetType(nouveau_type)", block)\n        self.assertIn("self.ctrl_type.SetID(ancien_type)", block)\n        self.assertLess(block.index("self.ctrl_questionnaire.SetType(nouveau_type)"), block.rindex("self.type = nouveau_type"))\n'''
if 'test_maj_rolls_back_model_and_tree_on_render_failure' not in test:
    if marker not in test:
        raise SystemExit('test marker not found')
    test = test.replace(marker, addition + marker, 1)
    test_path.write_text(test, encoding='utf-8')
