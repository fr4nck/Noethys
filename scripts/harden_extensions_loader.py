#!/usr/bin/env python3
from pathlib import Path

p = Path('noethys/Dlg/DLG_Extensions.py')
t = p.read_text(encoding='utf-8')

# Imports
if 'import importlib.util\n' not in t:
    t = t.replace('import importlib\n', 'import importlib.util\n', 1)
if 'import re\n' not in t:
    t = t.replace('import codecs\n', 'import codecs\nimport re\n', 1)

old = '''        # Exécution de l'extension\n        nom_fichier = self.GetStringSelection()\n        sys.path.append(UTILS_Fichiers.GetRepExtensions())\n        module = importlib.import_module(nom_fichier)\n        module.Extension()\n'''
new = '''        # Exécution de l'extension\n        nom_fichier = self.GetStringSelection()\n        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", nom_fichier):\n            dlg = wx.MessageDialog(self, _(u"Nom d'extension invalide."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)\n            dlg.ShowModal()\n            dlg.Destroy()\n            return False\n\n        chemin_extensions = os.path.realpath(UTILS_Fichiers.GetRepExtensions())\n        chemin_module = os.path.realpath(os.path.join(chemin_extensions, nom_fichier + ".py"))\n        if os.path.commonpath([chemin_extensions, chemin_module]) != chemin_extensions or not os.path.isfile(chemin_module):\n            dlg = wx.MessageDialog(self, _(u"Extension introuvable ou chemin invalide."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)\n            dlg.ShowModal()\n            dlg.Destroy()\n            return False\n\n        nom_module = "noethys_extension_%s" % nom_fichier\n        spec = importlib.util.spec_from_file_location(nom_module, chemin_module)\n        if spec is None or spec.loader is None:\n            dlg = wx.MessageDialog(self, _(u"Impossible de charger cette extension."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)\n            dlg.ShowModal()\n            dlg.Destroy()\n            return False\n\n        module = importlib.util.module_from_spec(spec)\n        spec.loader.exec_module(module)\n        fonction_extension = getattr(module, "Extension", None)\n        if not callable(fonction_extension):\n            dlg = wx.MessageDialog(self, _(u"Cette extension ne contient pas de fonction Extension() exploitable."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)\n            dlg.ShowModal()\n            dlg.Destroy()\n            return False\n        fonction_extension()\n'''
if old not in t:
    raise SystemExit('bloc Executer attendu absent')
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
print('DLG_Extensions.py durci')
