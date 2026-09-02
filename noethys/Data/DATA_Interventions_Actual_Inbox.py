#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Schéma additif de réception du réalisé canonique d'une séance.

Cette table mémorise les messages effectivement appliqués au domaine
activité/usagers. Elle ne remplace ni ``interventions`` ni
``interventions_execution``.
"""
from __future__ import unicode_literals


TABLE_INBOX = "interventions_execution_inbox"

DB_INTERVENTIONS_ACTUAL_INBOX = {
    TABLE_INBOX: [
        ("IDinbox_execution", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID local de réception"),
        ("idempotence_key", "VARCHAR(255)", u"Clé stable du message reçu"),
        ("source_domain", "VARCHAR(64)", u"Domaine émetteur stable, indépendant du nom du produit"),
        ("contract_version", "VARCHAR(64)", u"Version du contrat métier reçu"),
        ("event_type", "VARCHAR(64)", u"Type d'événement métier reçu"),
        ("actual_uuid", "VARCHAR(64)", u"Identifiant du réalisé côté domaine opérations"),
        ("session_uid", "VARCHAR(128)", u"UID canonique de la séance"),
        ("actual_revision", "INTEGER", u"Révision du réalisé validé"),
        ("payload_sha256", "VARCHAR(64)", u"Empreinte du payload canonique appliqué"),
        ("date_reception", "DATETIME", u"Horodatage de réception"),
    ],
}
