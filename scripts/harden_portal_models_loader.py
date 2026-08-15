#!/usr/bin/env python3
from pathlib import Path

p = Path('noethys/Utils/UTILS_Portail_synchro.py')
t = p.read_text(encoding='utf-8')

if 'import importlib.util\n' not in t:
    t = t.replace('import importlib\n', 'import importlib.util\n', 1)

old = '''        chemin, nomFichier = resultat\n        if "models" in sys.modules:\n            del sys.modules["models"]\n\n        # Import du fichier models.py\n        sys.path.append(chemin)\n        models = importlib.import_module(nomFichier.replace(".py", ""))\n'''
new = '''        chemin, nomFichier = resultat\n\n        # Import du fichier models.py téléchargé depuis le portail, sans modifier\n        # sys.path et en vérifiant explicitement le fichier et l'API attendue.\n        chemin_models = os.path.realpath(os.path.join(chemin, nomFichier))\n        chemin_attendu = os.path.realpath(os.path.join(chemin, "models.py"))\n        if chemin_models != chemin_attendu or not os.path.isfile(chemin_models):\n            self.log.EcritLog(_(u"[ERREUR] Fichier models.py invalide ou introuvable."))\n            self.Deconnexion(ftp)\n            return False\n\n        spec = importlib.util.spec_from_file_location("noethys_connecthys_models", chemin_models)\n        if spec is None or spec.loader is None:\n            self.log.EcritLog(_(u"[ERREUR] Impossible de charger models.py."))\n            self.Deconnexion(ftp)\n            return False\n\n        models = importlib.util.module_from_spec(spec)\n        spec.loader.exec_module(models)\n\n        attributs_requis = ("create_engine", "Base", "sessionmaker")\n        if not all(hasattr(models, attribut) for attribut in attributs_requis):\n            self.log.EcritLog(_(u"[ERREUR] Le fichier models.py ne fournit pas l'API attendue."))\n            self.Deconnexion(ftp)\n            return False\n'''
if old not in t:
    raise SystemExit('bloc import models attendu absent')
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
print('UTILS_Portail_synchro.py durci')
