#!/usr/bin/env python3
from pathlib import Path

p = Path('noethys/Ol/OL_Activites.py')
t = p.read_text(encoding='utf-8')

old = 'import wx, os, datetime, importlib\n'
new = 'import wx, os, datetime\n'
if t.count(old) != 1:
    raise SystemExit('import importlib attendu absent ou ambigu')
t = t.replace(old, new, 1)

old = '''        # Propose assistants de génération d'activités\n        from Dlg import DLG_Nouvelle_activite\n        dlg = DLG_Nouvelle_activite.Dialog(self)\n'''
new = '''        # Propose assistants de génération d'activités\n        from Dlg import DLG_Nouvelle_activite\n        from Ctrl import CTRL_Assistants_liste\n        dlg = DLG_Nouvelle_activite.Dialog(self)\n'''
if t.count(old) != 1:
    raise SystemExit('bloc chargement assistants attendu absent ou ambigu')
t = t.replace(old, new, 1)

old = '''        else :\n            # Création avec assistant de l'activité\n            module = importlib.import_module("Ctrl.CTRL_Assistant_%s" % code)\n            dlg = module.Dialog(self)\n'''
new = '''        else :\n            # Création avec assistant de l'activité. Les modules sont déjà\n            # importés statiquement par CTRL_Assistants_liste pour le packaging.\n            assistants = {\n                "annuelle": CTRL_Assistants_liste.CTRL_Assistant_annuelle,\n                "sejour": CTRL_Assistants_liste.CTRL_Assistant_sejour,\n                "stage": CTRL_Assistants_liste.CTRL_Assistant_stage,\n                "cantine": CTRL_Assistants_liste.CTRL_Assistant_cantine,\n                "sorties": CTRL_Assistants_liste.CTRL_Assistant_sorties,\n            }\n            module = assistants.get(code)\n            if module is None:\n                dlg = wx.MessageDialog(self, _(u"Assistant d'activité inconnu : %s") % code, _(u"Erreur"), wx.OK | wx.ICON_ERROR)\n                dlg.ShowModal()\n                dlg.Destroy()\n                return\n            dlg = module.Dialog(self)\n'''
if t.count(old) != 1:
    raise SystemExit('bloc import dynamique attendu absent ou ambigu')
t = t.replace(old, new, 1)

p.write_text(t, encoding='utf-8')
print('OL_Activites.py modifié de façon ciblée')
