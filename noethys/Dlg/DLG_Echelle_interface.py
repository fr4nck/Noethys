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
        self.SetMinSize((500, 190))
        self.echelle = 100
        self.apparence = "systeme"
        self.theme = "Vert"
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def SetValeurs(self, echelle=100, apparence="systeme", theme="Vert"):
        self.echelle = echelle
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
        taille = max(5.0, taille * (self.echelle / 100.0) * coefficient)
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

        if sombre:
            fond = UTILS_Interface.GetCouleurRole("surface", sombre=True, theme=self.theme)
            fond_controle = UTILS_Interface.GetCouleurRole("surface_container", sombre=True, theme=self.theme)
            fond_ligne = UTILS_Interface.GetCouleurRole("surface_container_lowest", sombre=True, theme=self.theme)
            fond_ligne_alt = UTILS_Interface.GetCouleurRole("surface_container_low", sombre=True, theme=self.theme)
            texte = UTILS_Interface.GetCouleurRole("on_surface", sombre=True, theme=self.theme)
            texte_secondaire = UTILS_Interface.GetCouleurRole("on_surface_variant", sombre=True, theme=self.theme)
            bordure = UTILS_Interface.GetCouleurRole("outline_variant", sombre=True, theme=self.theme)
            accent = UTILS_Interface.GetCouleurRole("primary", sombre=True, theme=self.theme)
            accent_texte = UTILS_Interface.GetCouleurRole("on_primary", sombre=True, theme=self.theme)
        else:
            fond = wx.Colour(245, 245, 245)
            fond_controle = wx.Colour(255, 255, 255)
            fond_ligne = wx.Colour(255, 255, 255)
            fond_ligne_alt = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237), theme=self.theme)
            texte = wx.Colour(25, 25, 25)
            texte_secondaire = wx.Colour(90, 90, 90)
            bordure = wx.Colour(190, 190, 190)
            accent = UTILS_Interface.GetValeur("couleur_claire", wx.Colour(137, 206, 27), theme=self.theme)
            luminance = accent.Red() * 0.299 + accent.Green() * 0.587 + accent.Blue() * 0.114
            accent_texte = wx.BLACK if luminance > 150 else wx.WHITE

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
        # calculée comme un couple sémantique plutôt qu'un simple RGB isolé.
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

        # Mini tableau : les lignes structurelles suivent les surfaces M3 ; les
        # couleurs métier restent réservées aux vraies alertes/états.
        y = marge + 76
        if sombre:
            lignes = [
                (_(u"Bais — repas enfants"), u"42", fond_ligne_alt, texte),
                (_(u"Animateurs"), u"6", fond_ligne, texte),
                (_(u"Alerte capacité"), u"60", UTILS_Interface.PALETTE_SOMBRE["metier_rouge"], UTILS_Interface.PALETTE_SOMBRE["metier_rouge_texte"]),
            ]
        else:
            lignes = [
                (_(u"Bais — repas enfants"), u"42", fond_ligne_alt, wx.Colour(30, 30, 30)),
                (_(u"Animateurs"), u"6", fond_ligne, wx.Colour(30, 30, 30)),
                (_(u"Alerte capacité"), u"60", wx.Colour(250, 205, 205), wx.Colour(30, 30, 30)),
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
        wx.Dialog.__init__(self, parent, -1, title=_(u"Échelle et apparence"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        # Apparence
        self.liste_codes_apparence = [code for code, label in UTILS_Interface.APPARENCES]
        self.liste_labels_apparence = [label for code, label in UTILS_Interface.APPARENCES]
        self.label_apparence = wx.StaticText(self, -1, _(u"Apparence :"))
        self.ctrl_apparence = wx.Choice(self, -1, choices=self.liste_labels_apparence)

        # Couleur d'accent / thème historique Noethys
        self.liste_codes_theme = [code for code, label in UTILS_Interface.THEMES]
        self.liste_labels_theme = [label for code, label in UTILS_Interface.THEMES]
        self.label_theme = wx.StaticText(self, -1, _(u"Couleur du thème :"))
        self.ctrl_theme = wx.Choice(self, -1, choices=self.liste_labels_theme)

        # Échelle
        self.label_echelle = wx.StaticText(self, -1, _(u"Échelle de l'interface :"))
        self.ctrl_echelle = wx.Choice(
            self,
            -1,
            choices=[u"%d %%" % valeur for valeur in UTILS_Interface.ECHELLES],
        )

        self.info_systeme = wx.StaticText(self, -1, "")
        self.apercu = Apercu(self)

        self.info = wx.StaticText(
            self,
            -1,
            _(u"L'aperçu est immédiat. L'interface complète utilisera ces réglages au prochain démarrage."),
        )

        self.bouton_ok = wx.Button(self, wx.ID_OK, _(u"Valider"))
        self.bouton_annuler = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))

        self._importation()
        self._layout()
        self._binds()
        self.MAJaperçu()

        self.SetMinSize((570, 390))
        self.SetSize((620, 450))
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

    def _layout(self):
        grille = wx.FlexGridSizer(rows=3, cols=2, vgap=8, hgap=10)
        grille.Add(self.label_apparence, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grille.Add(self.ctrl_apparence, 1, wx.EXPAND)
        grille.Add(self.label_theme, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grille.Add(self.ctrl_theme, 1, wx.EXPAND)
        grille.Add(self.label_echelle, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grille.Add(self.ctrl_echelle, 1, wx.EXPAND)
        grille.AddGrowableCol(1)

        box_apercu = wx.StaticBoxSizer(wx.StaticBox(self, -1, _(u"Aperçu")), wx.VERTICAL)
        box_apercu.Add(self.apercu, 1, wx.ALL | wx.EXPAND, 6)

        boutons = wx.StdDialogButtonSizer()
        boutons.AddButton(self.bouton_ok)
        boutons.AddButton(self.bouton_annuler)
        boutons.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grille, 0, wx.ALL | wx.EXPAND, 12)
        sizer.Add(self.info_systeme, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        sizer.Add(box_apercu, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        sizer.Add(self.info, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        sizer.Add(boutons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 12)
        self.SetSizer(sizer)

    def _binds(self):
        self.ctrl_apparence.Bind(wx.EVT_CHOICE, self.OnChoix)
        self.ctrl_theme.Bind(wx.EVT_CHOICE, self.OnChoix)
        self.ctrl_echelle.Bind(wx.EVT_CHOICE, self.OnChoix)

    def GetValeurs(self):
        return {
            "apparence": self.liste_codes_apparence[self.ctrl_apparence.GetSelection()],
            "theme": self.liste_codes_theme[self.ctrl_theme.GetSelection()],
            "echelle": UTILS_Interface.ECHELLES[self.ctrl_echelle.GetSelection()],
        }

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
    dlg.Destroy()
    return valeurs
