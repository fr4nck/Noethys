#!/usr/bin/env python3
from pathlib import Path
p=Path('noethys/Ctrl/CTRL_Grille.py')
t=p.read_text(encoding='utf-8')
marker='from Utils import UTILS_Texte\n'
if 'from Utils import UTILS_Expressions\n' not in t:
    if marker not in t: raise SystemExit('import marker absent')
    t=t.replace(marker, marker+'from Utils import UTILS_Expressions\n',1)
old='''    def ResolveFormule(self, formule="", dictVariables={}):\n        # Remplacement de variables prédéfinies\n        #print formule\n        for variable, valeur in dictVariables.items() :\n            formule = formule.replace(variable, valeur.__repr__())\n        # Replacement des variables utilisateurs\n        formule = re.sub(r'\\\"([0-9][0-9]):([0-9][0-9])\\\"', sub, formule)\n        # Résolution de la formule\n        try :\n            resultat = eval(formule)\n        except Exception as err :\n            resultat = None\n        #print "Formule : ", formule, " -> resultat =", resultat\n        return resultat\n'''
new='''    def ResolveFormule(self, formule="", dictVariables={}):\n        variables_sures = {}\n\n        # Remplacement des variables par des noms temporaires explicitement\n        # fournis à l'évaluateur AST, sans reconstruire de code Python.\n        for index, (variable, valeur) in enumerate(dictVariables.items()):\n            nom_variable = "noethys_var_%d" % index\n            variables_sures[nom_variable] = valeur\n            formule = formule.replace(variable, nom_variable)\n\n        # Même principe pour les horaires littéraux \"HH:MM\".\n        compteur_horaires = [0]\n        def remplace_horaire(match):\n            heures = int(match.group(1))\n            minutes = int(match.group(2))\n            nom_variable = "noethys_heure_%d" % compteur_horaires[0]\n            compteur_horaires[0] += 1\n            variables_sures[nom_variable] = datetime.timedelta(minutes=heures * 60 + minutes)\n            return nom_variable\n\n        formule = re.sub(r'\\\"([0-9][0-9]):([0-9][0-9])\\\"', remplace_horaire, formule)\n\n        try:\n            resultat = UTILS_Expressions.EvaluerExpression(formule, variables=variables_sures)\n        except Exception:\n            resultat = None\n        return resultat\n'''
if old not in t: raise SystemExit('bloc ResolveFormule absent')
t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')
print('dernier eval migré')
