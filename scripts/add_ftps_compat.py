#!/usr/bin/env python3
from pathlib import Path

# Configuration UI/defaults
p = Path('noethys/Dlg/DLG_Portail_config.py')
t = p.read_text(encoding='utf-8')

old = '    "ftp_repertoire" : "/www/connecthys",\n'
new = '    "ftp_repertoire" : "/www/connecthys",\n    "ftp_tls" : False,\n'
if old not in t:
    raise SystemExit('default ftp_repertoire absent')
t = t.replace(old, new, 1)

old = '            ("ftp_repertoire", lambda: p(\'hebergement_type\') == 1),\n'
new = old + '            ("ftp_tls", lambda: p(\'hebergement_type\') == 1),\n'
if old not in t:
    raise SystemExit('condition ftp_repertoire absente')
t = t.replace(old, new, 1)

old = '''        # Répertoire FTP\n        nom = "ftp_repertoire"\n        propriete = wxpg.StringProperty(label=_(u"Répertoire"), name=nom, value=VALEURS_DEFAUT[nom])\n        propriete.SetHelpString(_(u"Saisissez le répertoire FTP (ex : www/connecthys)"))\n        self.Append(propriete)\n\n        # Serveur SSH\n'''
new = '''        # Répertoire FTP\n        nom = "ftp_repertoire"\n        propriete = wxpg.StringProperty(label=_(u"Répertoire"), name=nom, value=VALEURS_DEFAUT[nom])\n        propriete.SetHelpString(_(u"Saisissez le répertoire FTP (ex : www/connecthys)"))\n        self.Append(propriete)\n\n        # Chiffrement FTP explicite (FTPS). Désactivé par défaut afin de conserver\n        # strictement le comportement des configurations historiques.\n        nom = "ftp_tls"\n        propriete = wxpg.BoolProperty(label=_(u"Sécuriser la connexion FTP avec TLS (FTPS)"), name=nom, value=VALEURS_DEFAUT[nom])\n        propriete.SetHelpString(_(u"Active FTPS explicite. Laissez décoché pour conserver une ancienne configuration FTP inchangée."))\n        propriete.SetAttribute("UseCheckbox", True)\n        self.Append(propriete)\n\n        # Serveur SSH\n'''
if old not in t:
    raise SystemExit('bloc UI FTP absent')
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')

# Connexion runtime
p = Path('noethys/Utils/UTILS_Portail_synchro.py')
t = p.read_text(encoding='utf-8')
old = '''        # Connexion FTP\n        if self.dict_parametres["hebergement_type"] == 1 :\n            self.log.EcritLog(_(u"Connexion FTP..."))\n            self.Pulse_gauge()\n\n            try :\n                ftp = ftplib.FTP(self.dict_parametres["ftp_serveur"], self.dict_parametres["ftp_utilisateur"], self.dict_parametres["ftp_mdp"])\n            except Exception as err :\n                print("Connexion FTP du serveur", str(err))\n                self.log.EcritLog(_(u"[ERREUR] Connexion FTP impossible."))\n                return False\n'''
new = '''        # Connexion FTP / FTPS explicite. Le paramètre ftp_tls vaut False par\n        # défaut afin de préserver intégralement les anciennes configurations.\n        if self.dict_parametres["hebergement_type"] == 1 :\n            utiliser_tls = bool(self.dict_parametres.get("ftp_tls", False))\n            self.log.EcritLog(_(u"Connexion FTPS...") if utiliser_tls else _(u"Connexion FTP non chiffrée..."))\n            self.Pulse_gauge()\n\n            try :\n                if utiliser_tls:\n                    ftp = ftplib.FTP_TLS()\n                    ftp.connect(self.dict_parametres["ftp_serveur"])\n                    ftp.login(self.dict_parametres["ftp_utilisateur"], self.dict_parametres["ftp_mdp"])\n                    # Chiffre aussi le canal de données, pas uniquement les commandes.\n                    ftp.prot_p()\n                else:\n                    ftp = ftplib.FTP(self.dict_parametres["ftp_serveur"], self.dict_parametres["ftp_utilisateur"], self.dict_parametres["ftp_mdp"])\n                    self.log.EcritLog(_(u"[AVERTISSEMENT] FTP transmet les identifiants et les données sans chiffrement. Préférez FTPS ou SSH/SFTP lorsque le serveur le permet."))\n            except Exception as err :\n                print("Connexion FTP/FTPS du serveur", str(err))\n                self.log.EcritLog(_(u"[ERREUR] Connexion FTP/FTPS impossible."))\n                return False\n'''
if old not in t:
    raise SystemExit('bloc Connexion FTP absent')
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
print('FTPS compatible ajouté')
