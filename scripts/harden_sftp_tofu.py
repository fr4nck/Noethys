#!/usr/bin/env python3
from pathlib import Path

p = Path('noethys/Utils/UTILS_Portail_synchro.py')
t = p.read_text(encoding='utf-8')

if 'import hashlib\n' not in t:
    t = t.replace('import json\n', 'import json\nimport hashlib\nimport base64\n', 1)

old = '''                ssh = paramiko.SSHClient()\n                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())\n                ssh.connect(self.dict_parametres["ssh_serveur"], port=int(self.dict_parametres["ssh_port"]), username=self.dict_parametres["ssh_utilisateur"], password=self.dict_parametres["ssh_mdp"])\n                ftp = ssh.open_sftp()\n'''
new = '''                ssh = paramiko.SSHClient()\n\n                # TOFU (Trust On First Use) : mémorise l'empreinte de la première\n                # clé hôte rencontrée puis refuse toute modification ultérieure.\n                class NoethysTOFUPolicy(paramiko.MissingHostKeyPolicy):\n                    def missing_host_key(policy_self, client, hostname, key):\n                        port = int(self.dict_parametres["ssh_port"])\n                        identifiant = "%s:%d" % (hostname, port)\n                        empreinte = "SHA256:" + base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode("ascii").rstrip("=")\n\n                        brut = UTILS_Parametres.Parametres(mode="get", categorie="portail", nom="ssh_known_hosts", valeur="{}")\n                        try:\n                            connus = json.loads(brut) if brut else {}\n                        except Exception:\n                            connus = {}\n\n                        precedent = connus.get(identifiant)\n                        actuel = {"type": key.get_name(), "fingerprint": empreinte}\n                        if precedent is None:\n                            connus[identifiant] = actuel\n                            UTILS_Parametres.Parametres(mode="set", categorie="portail", nom="ssh_known_hosts", valeur=json.dumps(connus, sort_keys=True))\n                            self.log.EcritLog(_(u"Première clé SSH mémorisée pour %s (%s).") % (identifiant, empreinte))\n                        elif precedent != actuel:\n                            raise paramiko.SSHException("Clé SSH du serveur modifiée pour %s" % identifiant)\n\n                        client.get_host_keys().add(hostname, key.get_name(), key)\n\n                ssh.set_missing_host_key_policy(NoethysTOFUPolicy())\n                ssh.connect(self.dict_parametres["ssh_serveur"], port=int(self.dict_parametres["ssh_port"]), username=self.dict_parametres["ssh_utilisateur"], password=self.dict_parametres["ssh_mdp"])\n                ftp = ssh.open_sftp()\n'''
if old not in t:
    raise SystemExit('bloc SFTP attendu absent')
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
print('TOFU SFTP appliqué')
