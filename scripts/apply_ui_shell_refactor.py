#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Applique la première migration structurelle du shell UI.

Le script est volontairement déterministe et idempotent. Il sert à modifier des
fichiers historiques volumineux sans introduire de couche runtime supplémentaire.
Une fois les substitutions appliquées, le code produit est du code Noethys
normal et ne dépend pas de ce script.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text, old, new, label):
    if new in text:
        return text, False
    if old not in text:
        raise RuntimeError("Motif introuvable pour %s" % label)
    return text.replace(old, new, 1), True


def replace_all(text, old, new, label):
    if old not in text:
        if new in text:
            return text, False
        raise RuntimeError("Motif introuvable pour %s" % label)
    return text.replace(old, new), True


def migrate_noethys():
    path = ROOT / "noethys" / "Noethys.py"
    text = path.read_text(encoding="utf-8")
    changed = False

    text, did = replace_once(
        text,
        "from Utils import UTILS_Aui\n",
        "from Utils import UTILS_Aui\nfrom Utils import UTILS_UIMetrics\n",
        "import UIMetrics",
    )
    changed |= did

    text, did = replace_once(
        text,
        "        # Création des panneaux\n        self.CreationPanneaux()\n        \n        # Création des Binds\n",
        "        # Création des panneaux\n        self.CreationPanneaux()\n\n        # Le shell AUI est dimensionné à partir du contenu réel (icônes,\n        # libellés, DPI et échelle), jamais depuis les anciennes hauteurs fixes.\n        UTILS_Aui.ConfigurerManager(self._mgr)\n        \n        # Création des Binds\n",
        "configuration AUI initiale",
    )
    changed |= did

    text, did = replace_once(
        text,
        "        self.SetMinSize((935, 740))\n",
        "        self.SetMinSize((\n            min(UTILS_UIMetrics.px(820), 1100),\n            min(UTILS_UIMetrics.px(600), 800),\n        ))\n",
        "taille minimale frame",
    )
    changed |= did

    text, did = replace_all(
        text,
        "        tb.SetToolBitmapSize(wx.Size(16, 16))\n",
        "        taille_toolbar = UTILS_UIMetrics.icon_size(\"toolbar\")\n        tb.SetToolBitmapSize(wx.Size(taille_toolbar, taille_toolbar))\n",
        "métrique bitmap toolbar",
    )
    changed |= did

    toolbar_icons = (
        "Calendrier.png",
        "Imprimante.png",
        "Badgeage.png",
        "Reglement.png",
        "Calculatrice.png",
        "Homme.png",
    )
    for icon in toolbar_icons:
        old = 'wx.Bitmap(Chemins.GetStaticPath("Images/16x16/%s"), wx.BITMAP_TYPE_PNG)' % icon
        new = 'wx.Bitmap(Chemins.GetStaticIconPath("Images/16x16/%s", taille=taille_toolbar), wx.BITMAP_TYPE_PNG)' % icon
        if old in text:
            text = text.replace(old, new, 1)
            changed = True

    old = 'image = wx.Bitmap(Chemins.GetStaticPath(item["image"]), wx.BITMAP_TYPE_PNG)'
    new = 'image = wx.Bitmap(Chemins.GetStaticIconPath(item["image"], taille=taille_toolbar), wx.BITMAP_TYPE_PNG)'
    if old in text:
        text = text.replace(old, new)
        changed = True

    substitutions = {
        "self.ctrl_numfacture = CTRL_Numfacture.CTRL(tb, size=(100, -1))":
            "self.ctrl_numfacture = CTRL_Numfacture.CTRL(tb, size=(UTILS_UIMetrics.px(120), -1))",
        "self.ctrl_identification = CTRL_Identification.CTRL(tb, listeUtilisateurs=self.listeUtilisateurs, size=(80, -1))":
            "self.ctrl_identification = CTRL_Identification.CTRL(tb, listeUtilisateurs=self.listeUtilisateurs, size=(UTILS_UIMetrics.px(96), -1))",
        "tb.AddSpacer(50)": "tb.AddSpacer(UTILS_UIMetrics.spacing(4))",
    }
    for old, new in substitutions.items():
        if old in text:
            text = text.replace(old, new)
            changed = True

    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def migrate_remplissage():
    path = ROOT / "noethys" / "Ctrl" / "CTRL_Remplissage.py"
    text = path.read_text(encoding="utf-8")
    changed = False

    text, did = replace_once(
        text,
        "from Utils import UTILS_Dates\n",
        "from Utils import UTILS_Dates\nfrom Utils import UTILS_Interface\nfrom Utils import UTILS_UIMetrics\n",
        "imports design system remplissage",
    )
    changed |= did

    old_colors = '''# Colonnes Activités\nLARGEUR_COLONNE_ACTIVITE = 18\nCOULEUR_COLONNE_ACTIVITE = (205, 144, 233)\n\nCOULEUR_COLONNE_TOTAL = "#C5DDFA"\n\n# Cases\nCOULEUR_RESERVATION = (252, 213, 0) # ancien vert : "#A6FF9F"\nCOULEUR_ATTENTE = "YELLOW"\nCOULEUR_REFUS = "RED"\nCOULEUR_DISPONIBLE = "#E3FEDB"\nCOULEUR_ALERTE = "#FEFCDB"\nCOULEUR_COMPLET = "#F7ACB2"\nCOULEUR_NORMAL = "WHITE"\nCOULEUR_FERME = (220, 220, 220)\n'''
    new_colors = '''# Colonnes Activités\nLARGEUR_COLONNE_ACTIVITE = 18\nCOULEUR_COLONNE_ACTIVITE = UTILS_Interface.GetCouleurRole("primary_container")\n\nCOULEUR_COLONNE_TOTAL = UTILS_Interface.GetCouleurRole("info")\n\n# Cases : la sémantique métier est conservée, le rendu vient du design system.\nCOULEUR_RESERVATION = UTILS_Interface.GetCouleurRole("warning")\nCOULEUR_ATTENTE = UTILS_Interface.GetCouleurRole("warning")\nCOULEUR_REFUS = UTILS_Interface.GetCouleurRole("danger")\nCOULEUR_DISPONIBLE = UTILS_Interface.GetCouleurRole("success")\nCOULEUR_ALERTE = UTILS_Interface.GetCouleurRole("warning")\nCOULEUR_COMPLET = UTILS_Interface.GetCouleurRole("danger")\nCOULEUR_NORMAL = UTILS_Interface.GetCouleurRole("surface_container_lowest")\nCOULEUR_FERME = UTILS_Interface.GetCouleurRole("disabled")\n'''
    text, did = replace_once(text, old_colors, new_colors, "couleurs sémantiques remplissage")
    changed |= did

    replacements = {
        '        couleurLigneDate = "#C0C0C0"\n        self.couleurOuverture = (0, 230, 0)\n        self.couleurFermeture = "#F7ACB2"\n        couleurVacances = "#F3FD89"\n':
            '        couleurLigneDate = UTILS_Interface.GetCouleurRole("surface_container_high")\n        self.couleurOuverture = UTILS_Interface.GetCouleurRole("success")\n        self.couleurFermeture = UTILS_Interface.GetCouleurRole("danger")\n        couleurVacances = UTILS_Interface.GetCouleurRole("warning")\n',
        '            hauteurLigne = 36\n        else :\n            hauteurLigne = 30\n':
            '            hauteurLigne = UTILS_UIMetrics.row_height("comfortable")\n        else :\n            hauteurLigne = UTILS_UIMetrics.row_height("table")\n',
        '        self.SetRowLabelSize(180)\n        self.EnableGridLines(False)\n':
            '        self.SetRowLabelSize(UTILS_UIMetrics.px(180))\n        self.EnableGridLines(True)\n        self.SetGridLineColour(UTILS_Interface.GetCouleurRole("outline_variant"))\n',
        '        self.SetColLabelSize(45)\n':
            '        self.SetColLabelSize(UTILS_UIMetrics.px(45))\n',
        '                self.SetColSize(numColonne, LARGEUR_COLONNE_ACTIVITE)\n':
            '                self.SetColSize(numColonne, UTILS_UIMetrics.px(LARGEUR_COLONNE_ACTIVITE))\n',
        '                            self.SetColSize(numColonne, largeurColonne)\n':
            '                            self.SetColSize(numColonne, UTILS_UIMetrics.px(largeurColonne))\n',
        '                            self.SetColSize(numColonne, LARGEUR_COLONNE_UNITE)\n':
            '                            self.SetColSize(numColonne, UTILS_UIMetrics.px(LARGEUR_COLONNE_UNITE))\n',
        '            text = wordwrap.wordwrap(text, LARGEUR_COLONNE_UNITE, dc)\n':
            '            text = wordwrap.wordwrap(text, UTILS_UIMetrics.px(LARGEUR_COLONNE_UNITE), dc)\n',
        '        if self.case.ouvert == True or self.case.estTotal == True :\n            self.DrawBorder(grid, dc, rect)\n':
            '        self.DrawBorder(grid, dc, rect)\n',
    }
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
            changed = True
        elif new not in text:
            raise RuntimeError("Motif remplissage introuvable: %r" % old[:70])

    old_border = '''        top = rect.top\n        bottom = rect.bottom\n        left = rect.left\n        right = rect.right        \n        dc.SetPen(wx.Pen(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DSHADOW)))\n        dc.DrawLine(right, top, right, bottom)\n        dc.DrawLine(left, top, left, bottom)\n        dc.DrawLine(left, bottom, right, bottom)\n        dc.SetPen(wx.WHITE_PEN)\n        dc.DrawLine(left+1, top, left+1, bottom)\n        dc.DrawLine(left+1, top, right, top)\n'''
    new_border = '''        top = rect.top\n        bottom = rect.bottom\n        left = rect.left\n        right = rect.right\n        dc.SetPen(wx.Pen(UTILS_Interface.GetCouleurRole("outline_variant")))\n        dc.DrawLine(left, top, right, top)\n        dc.DrawLine(right, top, right, bottom)\n        dc.DrawLine(left, bottom, right, bottom)\n        dc.DrawLine(left, top, left, bottom)\n'''
    text, did = replace_once(text, old_border, new_border, "bordures dashboard")
    changed |= did

    font_replacements = {
        'font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL)':
            'font = wx.Font(max(7, UTILS_UIMetrics.px(9)), wx.SWISS, wx.NORMAL, wx.NORMAL)',
        'font=wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL)':
            'font=wx.Font(max(7, UTILS_UIMetrics.px(8)), wx.SWISS, wx.NORMAL, wx.NORMAL)',
        'font=wx.Font(6, wx.SWISS, wx.NORMAL, wx.NORMAL)':
            'font=wx.Font(max(6, UTILS_UIMetrics.px(6)), wx.SWISS, wx.NORMAL, wx.NORMAL)',
        'font = wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL)':
            'font = wx.Font(max(7, UTILS_UIMetrics.px(7)), wx.SWISS, wx.NORMAL, wx.NORMAL)',
    }
    for old, new in font_replacements.items():
        if old in text:
            text = text.replace(old, new)
            changed = True

    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def main():
    changed = []
    if migrate_noethys():
        changed.append("noethys/Noethys.py")
    if migrate_remplissage():
        changed.append("noethys/Ctrl/CTRL_Remplissage.py")
    print("Fichiers modifiés : %s" % (", ".join(changed) if changed else "aucun"))


if __name__ == "__main__":
    main()
