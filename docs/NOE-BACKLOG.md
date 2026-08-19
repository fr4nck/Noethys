# Backlog Noe-xxx

Ce document associe les tickets GitHub Noe-xxx aux grands chantiers de modernisation.

## Noe-000 — SQL / base de données

- Noe-001 — Audit SQL strict complet — **terminé**
- Noe-002 — Réécriture OL_Reglements SQL strict — **code terminé ; validation copie réelle restante**
- Noe-003 — Nettoyage DLG_Export_compta — **code terminé ; validation copie réelle restante**
- Noe-004 — Audit index base de données — **outillage terminé ; mesures copie réelle restantes**
- Noe-005 — Reliquat SQL strict détecté par l'audit complet — **dette progressive post-RC**

## Noe-010 — Runtime Python

- Noe-010 — Audit compatibilité Python 3.10+ — **terminé**
- Noe-011 — Préparation Python 3.11 — **terminé**
- Noe-012 — Étude Python 3.12 — **terminé**

## Noe-020 — wxPython / plateformes

- Noe-020 — Audit wxPython Phoenix complet — **terminé**
- Noe-021 — Compatibilité GTK3/Linux — **terminé**
- Noe-022 — Validation macOS — **terminé pour la compatibilité du code source**

## Noe-030 — Tests et exploitation

- Noe-030 — Scénario de recette base existante — **outillage terminé ; recette sur copie réelle restante**
- Noe-031 — Tests non-régression métier — **terminé**
- Noe-032 — Audit sauvegarde/restauration — **terminé**

Le préflight `scripts/rc_db_preflight.py` regroupe en une seule exécution les contrôles techniques encore nécessaires pour Noe-002, Noe-003, Noe-004 et Noe-030.

## Noe-040 — Distribution

- Noe-040 — Packaging Windows final — **terminé**
- Noe-041 — Version portable Noethys — **terminé**
- Noe-042 — Préparation RC — **sas technique terminé ; recette réelle puis déclenchement RC restants**

## Noe-050 — Documentation

- Noe-050 — Documentation développeur — **terminé**
- Noe-051 — Documentation utilisateur — **terminé**
- Noe-052 — Historique Upgrade Noethys — **terminé**

## Situation pré-RC

La modernisation technique requise pour une première RC est achevée. Les tickets encore ouverts avant RC correspondent désormais au **même verrou d'exploitation** : validation sur une copie d'une base réellement utilisée, puis parcours métier Noe-030.

Noe-005 est volontairement séparé : les 151 requêtes classées `REVIEW` par l'audit SQL représentent une dette à examiner progressivement et non 151 régressions connues. Les chemins financiers critiques ont déjà été sécurisés.

## Règle de suivi

Les issues GitHub Noe-xxx sont la source de suivi opérationnelle. La roadmap décrit la trajectoire globale et ne doit pas présenter une validation sur base synthétique comme équivalente à la recette finale sur copie réelle.
