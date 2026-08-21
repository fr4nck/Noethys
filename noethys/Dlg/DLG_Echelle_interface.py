#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :        GNU GPL
#------------------------------------------------------------------------

import wx

from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface


class Apercu(wx.Panel):
    """Petit aperçu sans effet sur l'interface en cours."""
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style=wx.BORDER_SIMPLE)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetMinSize((500, 205))
        self.echelle = 100
        self.taille_texte = 100
        self.apparence = "systeme"
        self.theme = "Vert"
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def SetValeurs(self, echelle=100, taille_texte=100, apparence="systeme", theme="Vert"):
        self.echelle = echelle
        self.taille_texte = taille_texte
        self.apparence = apparence
        self.theme = theme
        self.Refresh()

    def _font(self, coefficient=1.0, gras=False):
        police = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        police = wx.Font(police)
        try:
            taille = police.GetFractionalPointSize()
        except Exception:
            taille = float(police.GetPointSize())
        facteur = (self.echelle / 100.0) * (self.taille_texte / 100.0)
        taille = max(5.0, taille * facteur * coefficient)
        if hasattr(police, "SetFractionalPointSize"):
            police.SetFractionalPointSize(taille)
        else:
            police.SetPointSize(max(5, int(round(taille))))
        if gras:
            police.SetWeight(wx.FONTWEIGHT_BOLD)
        return police

    def OnPaint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        largeur, hauteur = self.GetClientSize()
        sombre = UTILS_Interface.EstSombre(self.apparence)

        fond = UTILS_Interface.GetCouleurRole("surface", sombre=sombre, theme=self.theme)
        fond_controle = UTILS_Interface.GetCouleurRole("surface_container", sombre=sombre, theme=self.theme)
        fond_ligne = UTILS_Interface.GetCouleurRole("surface_container_lowest", sombre=sombre, theme=self.theme)
        fond_ligne_alt = UTILS_Interface.GetCouleurRole("surface_container_low", sombre=sombre, theme=self.theme)
        texte = UTILS_Interface.GetCouleurRole("on_surface", sombre=sombre, theme=self.theme)
        texte_secondaire = UTILS_Interface.GetCouleurRole("on_surface_variant", sombre=sombre, theme=self.theme)
        bordure = UTILS_Interface.GetCouleurRole("outline_variant", sombre=sombre, theme=self.theme)
        accent = UTILS_Interface.GetCouleurRole("primary", sombre=sombre, theme=self.theme)
        accent_texte = UTILS_Interface.GetCouleurRole("on_primary", sombre=sombre, theme=self.theme)
        danger = UTILS_Interface.GetCouleurRole("danger", sombre=sombre, theme=self.theme)
        danger_texte = UTILS_Interface.GetCouleurRole("danger_text", sombre=sombre, theme=self.theme)

        dc.SetBackground(wx.Brush(fond))
        dc.Clear()

        marge = 12
        dc.SetPen(wx.Pen(bordure))
        dc.SetBrush(wx.Brush(fond_controle))
        dc.DrawRoundedRectangle(marge, marge, max(10, largeur - marge * 2), max(10, hauteur - marge * 2), 7)

        dc.SetTextForeground(texte)
        dc.SetFont(self._font(1.15, gras=True))
        dc.DrawText(_(u"Noethys — aperçu"), marge + 12, marge + 10)

        dc.SetFont(self._font())
        dc.SetTextForeground(texte_secondaire)
        y = marge + 42
        dc.DrawText(_(u"Mercredi 2 septembre 2026"), marge + 12, y)

        # Bouton d'action : couleur primaire du thème, avec couleur de texte
        # issue du couple sémantique du design system.
        texte_bouton = _(u"Ajouter")
        dc.SetFont(self._font(0.95, gras=True))
        tw, th = dc.GetTextExtent(texte_bouton)
        bx = largeur - marge - tw - 30
        by = marge + 34
        dc.SetPen(wx.Pen(accent))
        dc.SetBrush(wx.Brush(accent))
        dc.DrawRoundedRectangle(bx, by, tw + 20, th + 10, 10)
        dc.SetTextForeground(accent_texte)
        dc.DrawText(texte_bouton, bx + 10, by + 5)

        # L'échelle agit sur la hauteur structurelle des lignes. La taille du
        # texte ne change que la typographie : l'aperçu matérialise la différence.
        y = marge + 80
        lignes = [
            (_(u"Bais — repas enfants"), u"42", fond_ligne_alt, texte),
            (_(u"Animateurs"), u"6", fond_ligne, texte),
            (_(u"Alerte capacité"), u"60", danger, danger_texte),
        ]

        hauteur_ligne = max(24, int(round(24 * self.echelle / 100.0)))
        dc.SetFont(self._font(0.92))
        for libelle, valeur, couleur, couleur_texte in lignes:
            dc.SetPen(wx.Pen(bordure))
            dc.SetBrush(wx.Brush(couleur))
            dc.DrawRectangle(marge + 12, y, max(30, largeur - marge * 2 - 24), hauteur_ligne)
            dc.SetTextForeground(couleur_texte)
            dc.DrawText(libelle, marge + 20, y + max(2, (hauteur_ligne - dc.GetCharHeight()) // 2))
            vw, vh = dc.GetTextExtent(valeur)
            dc.DrawText(valeur, largeur - marge - 22 - vw, y + max(2, (hauteur_ligne - vh) // 2))
            y += hauteur_ligne
            if y > hauteur - marge - 8:
                break


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            title=_(u"Apparence et accessibilité"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        # Apparence
        self.liste_codes_apparence = [code for code, label in UTILS_Interface.APPARENCES]
        self.liste_labels_apparence = [label for code, label in UTILS_Interface.APPARENCES]
        self.label_apparence = wx.StaticText(self, -1, _(u"Apparence :"))
        self.ctrl_apparence = wx.Choice(self, -1, choices=self.liste_labels_apparence)

        # Couleur d'accent / thème historique Noethys
        self.liste_codes_theme = [code for code, label in UTILS_Interface.THEMES]
        self.liste_labels_theme = [label for code, label in UTILS_Interface.THEMES]
        self.label_theme = wx.StaticText(self, -1, _(u"Couleur d'accent :"))
        self.ctrl_theme = wx.Choice(self, -1, choices=self.liste_labels_theme)

        # Échelle générale
        self.label_echelle = wx.StaticText(self, -1, _(u"Échelle de l'interface :"))
        self.ctrl_echelle = wx.Choice(
            self,
            -1,
            choices=[u"%d %%" % valeur for valeur in UTILS_Interface.ECHELLES],
        )

        # Accessibilité typographique indépendante de la géométrie de l'UI.
        self.label_texte = wx.StaticText(self, -1, _(u"Taille du texte :"))
        self.ctrl_texte = wx.Choice(
            self,
            -1,
            choices=[u"%d %%" % valeur for valeur in UTILS_Interface.TAILLES_TEXTE],
        )

        self.info_systeme = wx.StaticText(self, -1, "")
        self.info_accessibilite = wx.StaticText(
            self,
            -1,
            _(u"Échelle : agrandit l'interface complète. Taille du texte : agrandit principalement la typographie."),
        )
        self.apercu = Apercu(self)

        self.info = wx.StaticText(
            self,
            -1,
            _(u"L'aperçu est immédiat. L'interface complète utilisera ces réglages au prochain démarrage."),
        )

        self.bouton_defaut = wx.Button(self, wx.ID_ANY, _(u"Valeurs par défaut"))
        self.bouton_ok = wx.Button(self, wx.ID_OK, _(u"Valider"))
        self.bouton_annuler = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))

        self._importation()
        self._layout()
        self._binds()
        self.MAJaperçu()

        self.SetMinSize((590, 440))
        self.SetSize((650, 510))
        self.CenterOnParent()

    def _importation(self):
        apparence = UTILS_Interface.GetApparence()
        self.ctrl_apparence.SetSelection(self.liste_codes_apparence.index(apparence))

        theme = UTILS_Interface.GetTheme()
        if theme not in self.liste_codes_theme:
            theme = "Vert"
        self.ctrl_theme.SetSelection(self.liste_codes_theme.index(theme))

        echelle = UTILS_Interface.GetEchelle()
        self.ctrl_echelle.SetSelection(UTILS_Interface.ECHELLES.index(echelle))

        taille_texte = UTILS_Interface.GetTailleTexte()
        self.ctrl_texte.SetSelection(UTILS_Interface.TAILLES_TEXTE.index(taille_texte))

    def _layout(self):
        grille = wx.FlexGridSizer(rows=4, cols=2, vgap=8, hgap=10)
        grille.Add(self.label_apparence, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grille.Add(self.ctrl_apparence, 1, wx.EXPAND)
        grille.Add(self.label_theme, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grille.Add(self.ctrl_theme, 1, wx.EXPAND)
        grille.Add(self.label_echelle, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grille.Add(self.ctrl_echelle, 1, wx.EXPAND)
        grille.Add(self.label_texte, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grille.Add(self.ctrl_texte, 1, wx.EXPAND)
        grille.AddGrowableCol(1)

        box_apercu = wx.StaticBoxSizer(wx.StaticBox(self, -1, _(u"Aperçu")), wx.VERTICAL)
        box_apercu.Add(self.apercu, 1, wx.ALL | wx.EXPAND, 6)

        boutons_validation = wx.StdDialogButtonSizer()
        boutons_validation.AddButton(self.bouton_ok)
        boutons_validation.AddButton(self.bouton_annuler)
        boutons_validation.Realize()

        ligne_boutons = wx.BoxSizer(wx.HORIZONTAL)
        ligne_boutons.Add(self.bouton_defaut, 0, 0, 0)
        ligne_boutons.AddStretchSpacer(1)
        ligne_boutons.Add(boutons_validation, 0, 0, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grille, 0, wx.ALL | wx.EXPAND, 12)
        sizer.Add(self.info_systeme, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        sizer.Add(self.info_accessibilite, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        sizer.Add(box_apercu, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        sizer.Add(self.info, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        sizer.Add(ligne_boutons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        self.SetSizer(sizer)

    def _binds(self):
        self.ctrl_apparence.Bind(wx.EVT_CHOICE, self.OnChoix)
        self.ctrl_theme.Bind(wx.EVT_CHOICE, self.OnChoix)
        self.ctrl_echelle.Bind(wx.EVT_CHOICE, self.OnChoix)
        self.ctrl_texte.Bind(wx.EVT_CHOICE, self.OnChoix)
        self.bouton_defaut.Bind(wx.EVT_BUTTON, self.OnValeursDefaut)

    def GetValeurs(self):
        return {
            "apparence": self.liste_codes_apparence[self.ctrl_apparence.GetSelection()],
            "theme": self.liste_codes_theme[self.ctrl_theme.GetSelection()],
            "echelle": UTILS_Interface.ECHELLES[self.ctrl_echelle.GetSelection()],
            "taille_texte": UTILS_Interface.TAILLES_TEXTE[self.ctrl_texte.GetSelection()],
        }

    def OnValeursDefaut(self, event):
        self.ctrl_apparence.SetSelection(self.liste_codes_apparence.index("systeme"))
        self.ctrl_theme.SetSelection(self.liste_codes_theme.index("Vert"))
        self.ctrl_echelle.SetSelection(UTILS_Interface.ECHELLES.index(100))
        self.ctrl_texte.SetSelection(UTILS_Interface.TAILLES_TEXTE.index(100))
        self.MAJaperçu()

    def OnChoix(self, event):
        self.MAJaperçu()
        event.Skip()

    def MAJaperçu(self):
        valeurs = self.GetValeurs()
        self.apercu.SetValeurs(**valeurs)
        if valeurs["apparence"] == "systeme":
            etat = _(u"sombre") if UTILS_Interface.SystemeEstSombre() else _(u"clair")
            self.info_systeme.SetLabel(_(u"Mode système détecté actuellement : %s.") % etat)
        else:
            self.info_systeme.SetLabel("")
        self.Layout()


def Ouvrir(parent):
    dlg = Dialog(parent)
    resultat = dlg.ShowModal()
    valeurs = None
    if resultat == wx.ID_OK:
        valeurs = dlg.GetValeurs()
        UTILS_Interface.SetApparence(valeurs["apparence"])
        UTILS_Interface.SetTheme(valeurs["theme"])
        UTILS_Interface.SetEchelle(valeurs["echelle"])
        UTILS_Interface.SetTailleTexte(valeurs["taille_texte"])
    dlg.Destroy()
    return valeurs
