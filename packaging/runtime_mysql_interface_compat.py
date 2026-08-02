"""Sélection sûre du pilote MySQL dans le package Windows.

Noethys conserve historiquement ``mysqldb`` comme préférence par défaut. Si
``mysqlclient`` n'est pas importable mais que le connecteur officiel pur Python
est disponible, le code ne doit pas continuer à appeler ``MySQLdb``.

Ce hook ne modifie ni la configuration persistée, ni les bases, ni le schéma.
Il ajuste uniquement le pilote utilisé pendant cette exécution.
"""
from __future__ import annotations

try:
    import GestionDB
except Exception as err:  # Le démarrage principal fournira le diagnostic complet.
    print("Compatibilité MySQL non initialisée : %s" % err)
else:
    if (
        GestionDB.INTERFACE_MYSQL == "mysqldb"
        and not GestionDB.IMPORT_MYSQLDB_OK
        and GestionDB.IMPORT_MYSQLCONNECTOR_OK
    ):
        GestionDB.INTERFACE_MYSQL = "mysql.connector"
        print("mysqlclient indisponible : utilisation de mysql.connector")
