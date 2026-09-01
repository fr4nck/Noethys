#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostic temporaire du lot 23 branch_assignment_gap.

Ce fichier est volontairement supprimé du diff final. Pendant le rebaselining,
il exécute l'inventaire dès sa découverte par unittest puis interrompt la suite
pour rendre immédiatement le diagnostic disponible dans les logs CI.
"""

import sys

from scripts import audit_branch_assignment_gaps


audit_branch_assignment_gaps.main([])
sys.stdout.flush()
raise SystemExit("diagnostic temporaire lot 23 terminé")
