from pathlib import Path

src = Path('noethys/Ctrl/CTRL_Questionnaire.py')
text = src.read_text(encoding='utf-8')

old = '''    def MAJ(self, importation=True, selection=None):
        """ Met à jour (redessine) tout le contrôle """
        self.Freeze()
        self.DeleteAllItems()
        # Création de la racine
        self.root = self.AddRoot(_(u"Racine"))
        if importation == True :
            self.Importation()
        # Création des contrôles
        self.Remplissage(selection=selection)
        # Mémorisation des valeurs initiales
        if importation == True :
            self.dictValeursInitiales = self.GetValeurs()
        self.Thaw()
'''
new = '''    def MAJ(self, importation=True, selection=None):
        """ Met à jour (redessine) tout le contrôle """
        self.Freeze()
        try:
            self.DeleteAllItems()
            # Création de la racine
            self.root = self.AddRoot(_(u"Racine"))
            if importation == True :
                self.Importation()
            # Création des contrôles
            self.Remplissage(selection=selection)
            # Mémorisation des valeurs initiales
            if importation == True :
                self.dictValeursInitiales = self.GetValeurs()
        finally:
            self.Thaw()
'''
if old not in text:
    raise SystemExit('MAJ snippet not found')
text = text.replace(old, new, 1)

old = '''    def Remplissage(self, selection=None):
        # Création des branches
        self.dictBranches = {}
'''
new = '''    def Remplissage(self, selection=None):
        controles_valides = {
            None, "ligne_texte", "bloc_texte", "entier", "decimal", "montant",
            "liste_deroulante", "liste_coches", "case_coche", "date", "slider",
            "couleur", "documents", "codebarres", "rfid",
        }
        for IDcategorie in self.listeIDcategorie:
            for track in self.dictCategories[IDcategorie]["questions"]:
                if track.controle not in controles_valides:
                    raise ValueError("Type de contrôle de questionnaire inconnu : %s" % track.controle)

        # Création des branches
        self.dictBranches = {}
'''
if old not in text:
    raise SystemExit('Remplissage header not found')
text = text.replace(old, new, 1)

old = '''                        if track.controle != None :
                            if ctrl == None :
                                raise ValueError("Type de contrôle de questionnaire inconnu : %s" % track.controle)
                            self.SetItemWindow(brancheQuestion, ctrl, 1)
                            track.ctrl = ctrl

                        # Insère la valeur
                        if IDquestion in self.dictReponses :
                            valeur = self.dictReponses[IDquestion]["reponse"]
                        else:
                            valeur = track.defaut
                        track.SetValeurStr(valeur)
'''
new = '''                        if track.controle != None :
                            self.SetItemWindow(brancheQuestion, ctrl, 1)
                            track.ctrl = ctrl

                            # Insère la valeur uniquement lorsqu'un contrôle existe
                            if IDquestion in self.dictReponses :
                                valeur = self.dictReponses[IDquestion]["reponse"]
                            else:
                                valeur = track.defaut
                            track.SetValeurStr(valeur)
'''
if old not in text:
    raise SystemExit('control/value snippet not found')
text = text.replace(old, new, 1)
src.write_text(text, encoding='utf-8')

test = Path('tests/test_branch_contracts_batch_18.py')
t = test.read_text(encoding='utf-8')
old = '''    def test_unknown_non_null_control_is_rejected_explicitly(self):
        source = (NOETHYS / "Ctrl/CTRL_Questionnaire.py").read_text(encoding="utf-8")
        self.assertIn("ctrl = None", source)
        self.assertIn("if ctrl == None :", source)
        self.assertIn("Type de contrôle de questionnaire inconnu", source)
'''
new = '''    def test_unknown_non_null_control_is_rejected_before_tree_mutation(self):
        source = (NOETHYS / "Ctrl/CTRL_Questionnaire.py").read_text(encoding="utf-8")
        self.assertIn("controles_valides = {", source)
        self.assertIn("if track.controle not in controles_valides:", source)
        self.assertIn("Type de contrôle de questionnaire inconnu", source)
        self.assertLess(source.index("if track.controle not in controles_valides:"), source.index("self.dictBranches = {}", source.index("def Remplissage")))

    def test_control_less_question_does_not_load_widget_value(self):
        source = (NOETHYS / "Ctrl/CTRL_Questionnaire.py").read_text(encoding="utf-8")
        block = source[source.index("if track.controle != None :", source.index("def Remplissage")):source.index("indexQuestion += 1", source.index("def Remplissage"))]
        self.assertIn("track.SetValeurStr(valeur)", block)
        self.assertTrue(block.index("track.SetValeurStr(valeur)") > block.index("if track.controle != None :"))

    def test_maj_always_thaws_after_failure(self):
        source = (NOETHYS / "Ctrl/CTRL_Questionnaire.py").read_text(encoding="utf-8")
        maj = source[source.index("def MAJ("):source.index("def Importation(")]
        self.assertIn("try:", maj)
        self.assertIn("finally:", maj)
        self.assertIn("self.Thaw()", maj)
'''
if old not in t:
    raise SystemExit('test snippet not found')
t = t.replace(old, new, 1)
test.write_text(t, encoding='utf-8')
