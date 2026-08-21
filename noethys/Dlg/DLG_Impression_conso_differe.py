#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Adaptateur réactif pour l'historique ``DLG_Impression_conso``.

Le moteur métier/PDF reste dans le module historique. Seule la construction du
Dialogue est étagée afin de rendre la main à wx entre les pages et les requêtes
initiales. C'est important avec une base réseau : la fenêtre doit pouvoir se
peindre et rester fermable avant que toutes les données soient chargées.
"""

import datetime
import importlib
import sys

import wx

from Utils.UTILS_Traduction import _


# Import explicite du moteur historique. Le paquet Dlg ré-expose ensuite CE
# module pour les ``from Dlg import DLG_Impression_conso`` existants.
Legacy = importlib.import_module("Dlg.DLG_Impression_conso")


class CTRL_Parametres_Differe(wx.Notebook):
    """Notebook compatible avec CTRL_Parametres, construit une page par tick."""

    PAGES = (
        ("activites", Legacy.Page_Activites, _(u"Activités"), "Activite.png"),
        ("scolarite", Legacy.Page_Scolarite, _(u"Scolarité"), "Classe.png"),
        ("evenements", Legacy.Page_Evenements, _(u"Evènements"), "Evenement.png"),
        ("etiquettes", Legacy.Page_Etiquettes, _(u"Etiquettes"), "Etiquette.png"),
        ("unites", Legacy.Page_Unites, _(u"Unités"), "Tableau_colonne.png"),
        ("colonnes", Legacy.Page_Colonnes, _(u"Colonnes perso."), "Tableau_colonne.png"),
        ("options", Legacy.Page_Options, _(u"Options"), "Options.png"),
    )

    def __init__(self, parent, on_ready=None, on_progress=None):
        wx.Notebook.__init__(self, parent, id=-1, style=wx.BK_DEFAULT | wx.NB_MULTILINE)
        self.on_ready = on_ready
        self.on_progress = on_progress
        self.dictPages = {}
        self._index_construction = 0
        self._annule = False

        il = wx.ImageList(16, 16)
        self.dictImages = {}
        for code, classe, label, image in self.PAGES:
            bitmap = wx.Bitmap(Legacy.Chemins.GetStaticPath("Images/16x16/%s" % image), wx.BITMAP_TYPE_PNG)
            self.dictImages[code] = il.Add(bitmap)
        self.AssignImageList(il)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

        wx.CallAfter(self._ConstruirePageSuivante)

    def AnnulerConstruction(self):
        self._annule = True

    def _EstVivant(self):
        try:
            return bool(self) and not self._annule
        except Exception:
            return False

    def _ConstruirePageSuivante(self):
        if not self._EstVivant():
            return
        if self._index_construction >= len(self.PAGES):
            if callable(self.on_ready):
                wx.CallAfter(self.on_ready)
            return

        code, classe, label, image = self.PAGES[self._index_construction]
        if callable(self.on_progress):
            self.on_progress(_(u"Chargement : %s…") % label)

        page = classe(self)
        self.AddPage(page, label)
        self.SetPageImage(self.GetPageCount() - 1, self.dictImages[code])
        self.dictPages[code] = page
        self._index_construction += 1

        # Rend la main à l'event loop : la fenêtre et les contrôles déjà créés
        # peuvent se peindre avant la page suivante.
        wx.CallAfter(self._ConstruirePageSuivante)

    def GetPageAvecCode(self, codePage=""):
        return self.dictPages[codePage]

    def AffichePage(self, codePage=""):
        for index, (code, classe, label, image) in enumerate(self.PAGES):
            if code == codePage and index < self.GetPageCount():
                self.SetSelection(index)
                return

    def OnPageChanged(self, event):
        if event.GetOldSelection() == -1:
            event.Skip()
            return
        index = event.GetSelection()
        if 0 <= index < self.GetPageCount():
            page = self.GetPage(index)
            wx.CallAfter(page.Refresh)
        event.Skip()


class Dialog(Legacy.Dialog):
    """Même dialogue métier, mais initialisation non monolithique."""

    def __init__(self, parent, date=None):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            name="DLG_Impression_conso",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )
        self.parent = parent
        self.date = date
        self._fermeture_demandee = False
        self._chargement_termine = False
        self._dates_initiales = [date or datetime.date.today()]

        intro = _(u"Vous pouvez ici imprimer une liste des consommations au format PDF. Pour une liste journalière, sélectionnez 'journalière' puis une date dans le calendrier. Pour la liste d'une période de dates continues ou non, sélectionnez 'périodique' puis plusieurs dates (en appuyant sur les touches CTRL ou SHIFT) dans le calendrier.")
        titre = _(u"Impression d'une liste de consommations")
        self.ctrl_bandeau = Legacy.CTRL_Bandeau.Bandeau(
            self,
            titre=titre,
            texte=intro,
            hauteurHtml=30,
            nomImage="Images/32x32/Imprimante.png",
        )

        self.staticbox_type_staticbox = wx.StaticBox(self, -1, _(u"Type de liste"))
        self.radio_journ = wx.RadioButton(self, -1, _(u"Journalière"), style=wx.RB_GROUP)
        self.radio_period = wx.RadioButton(self, -1, _(u"Périodique"))

        self.staticbox_date_staticbox = wx.StaticBox(self, -1, _(u"Date"))
        self.ctrl_calendrier = Legacy.PANEL_Calendrier(self)
        self.ctrl_calendrier.SetMinSize((250, 80))

        self.staticbox_profil_staticbox = wx.StaticBox(self, -1, _(u"Profil de configuration"))
        self.ctrl_profil = Legacy.CTRL_profil_perso(self, categorie="impression_conso", dlg=self)

        self.staticbox_parametres_staticbox = wx.StaticBox(self, -1, _(u"Paramètres"))
        self.ctrl_parametres = CTRL_Parametres_Differe(
            self,
            on_ready=self._OnPagesPretes,
            on_progress=self._AfficherEtat,
        )

        self.bouton_aide = Legacy.CTRL_Bouton_image.CTRL(self, texte=_(u"Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_export = Legacy.CTRL_Bouton_image.CTRL(self, texte=_(u"Export sous Excel"), cheminImage="Images/32x32/Excel.png")
        self.bouton_ok = Legacy.CTRL_Bouton_image.CTRL(self, texte=_(u"Aperçu"), cheminImage="Images/32x32/Apercu.png")
        self.bouton_annuler = Legacy.CTRL_Bouton_image.CTRL(self, texte=_(u"Fermer"), cheminImage="Images/32x32/Fermer.png")
        self.label_chargement = wx.StaticText(self, -1, _(u"Chargement des paramètres…"))

        self.__set_properties_differe()
        self.__do_layout_differe()
        self.__binds_differes()
        self._ActiverActions(False)

    def _EstVivant(self):
        try:
            return bool(self) and not self._fermeture_demandee
        except Exception:
            return False

    def _AfficherEtat(self, texte):
        if not self._EstVivant():
            return
        try:
            self.label_chargement.SetLabel(texte)
            self.label_chargement.GetParent().Layout()
            self.Update()
        except Exception:
            pass

    def _ActiverActions(self, etat):
        for ctrl in (self.bouton_export, self.bouton_ok):
            try:
                ctrl.Enable(bool(etat))
            except Exception:
                pass

    def __set_properties_differe(self):
        self.SetTitle(_(u"Impression d'une liste de consommations"))
        self.radio_journ.SetToolTip(wx.ToolTip(_(u"Cochez ici pour sélectionner une liste journalière")))
        self.radio_period.SetToolTip(wx.ToolTip(_(u"Cochez ici pour sélectionner une liste périodique")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_export.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour exporter les données vers Excel")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour annuler")))
        self.SetMinSize((880, 600))

    def __binds_differes(self):
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioJourn, self.radio_journ)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioPeriod, self.radio_period)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonExport, self.bouton_export)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def __do_layout_differe(self):
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)

        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        grid_sizer_gauche = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)

        staticbox_profil = wx.StaticBoxSizer(self.staticbox_profil_staticbox, wx.VERTICAL)
        staticbox_profil.Add(self.ctrl_profil, 1, wx.EXPAND | wx.ALL, 5)
        grid_sizer_gauche.Add(staticbox_profil, 1, wx.EXPAND, 0)

        staticbox_date = wx.StaticBoxSizer(self.staticbox_date_staticbox, wx.VERTICAL)
        staticbox_date.Add(self.ctrl_calendrier, 1, wx.ALL | wx.EXPAND, 5)
        grid_sizer_gauche.Add(staticbox_date, 1, wx.EXPAND, 0)

        staticbox_type = wx.StaticBoxSizer(self.staticbox_type_staticbox, wx.HORIZONTAL)
        staticbox_type.Add(self.radio_journ, 0, wx.ALL, 5)
        staticbox_type.Add(self.radio_period, 0, wx.ALL, 5)
        grid_sizer_gauche.Add(staticbox_type, 0, wx.EXPAND, 0)
        grid_sizer_gauche.AddGrowableRow(1)

        grid_sizer_contenu.Add(grid_sizer_gauche, 0, wx.EXPAND, 0)

        staticbox_parametres = wx.StaticBoxSizer(self.staticbox_parametres_staticbox, wx.VERTICAL)
        staticbox_parametres.Add(self.ctrl_parametres, 1, wx.EXPAND | wx.ALL, 5)
        staticbox_parametres.Add(self.label_chargement, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        grid_sizer_contenu.Add(staticbox_parametres, 1, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_export, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(2)
        grid_sizer_base.Add(grid_sizer_boutons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSize(self.GetMinSize())
        self.Layout()
        self.CenterOnParent() if self.GetParent() is not None else self.CenterOnScreen()

    def _OnPagesPretes(self):
        if not self._EstVivant():
            return
        self._AfficherEtat(_(u"Chargement du calendrier…"))
        self.ctrl_calendrier.SetMultiSelection(False)
        self.staticbox_date_staticbox.SetLabel(_(u"Date"))
        self.ctrl_calendrier.SetDates(self._dates_initiales)
        wx.CallAfter(self._InitActivites)

    def _InitActivites(self):
        if not self._EstVivant():
            return
        self._AfficherEtat(_(u"Chargement des activités…"))
        self.GetPage("activites").ctrl_activites.SetDates(self._dates_initiales)
        wx.CallAfter(self._InitContexte)

    def _InitContexte(self):
        if not self._EstVivant():
            return
        self._AfficherEtat(_(u"Chargement des unités et évènements…"))
        liste_activites = self.GetPage("activites").ctrl_activites.GetListeActivites()

        # Les unités ont déjà été importées par leur page : seule la sélection
        # d'activités est recalculée ici.
        self.GetPage("unites").ctrl_unites.SetActivites(liste_activites)

        # Etiquettes : un seul rafraîchissement avec le contexte final.
        self.GetPage("etiquettes").ctrl_etiquettes.SetActivites(liste_activites)
        self.GetPage("etiquettes").ctrl_etiquettes.SetCoches(tout=True)

        # Evènements : évite le double aller-retour SetActivites() puis SetDates().
        ctrl_evenements = self.GetPage("evenements").ctrl_evenements
        ctrl_evenements.listeActivites = sorted(liste_activites)
        ctrl_evenements.SetDates(listeDates=self._dates_initiales)
        ctrl_evenements.SetCoches(tout=True)

        self.GetPage("scolarite").ctrl_ecoles.SetDates(self._dates_initiales)
        wx.CallAfter(self._InitProfil)

    def _InitProfil(self):
        if not self._EstVivant():
            return
        self._AfficherEtat(_(u"Application du profil de configuration…"))
        self.ctrl_profil.SetOnDefaut()
        wx.CallAfter(self._FinChargement)

    def _FinChargement(self):
        if not self._EstVivant():
            return
        self._chargement_termine = True
        self._ActiverActions(True)
        self.label_chargement.SetLabel(_(u"Prêt"))
        self.bouton_ok.SetFocus()
        self.Layout()
        self.Refresh()

    def SetDateDefaut(self, date=None):
        """Conserve l'API historique sans relancer le chargement en doublon."""
        if not self._chargement_termine:
            self._dates_initiales = [date or datetime.date.today()]
            return
        return Legacy.Dialog.SetDateDefaut(self, date)

    def OnClose(self, event):
        self.OnBoutonAnnuler(None)

    def OnBoutonAnnuler(self, event):
        self._fermeture_demandee = True
        try:
            self.ctrl_parametres.AnnulerConstruction()
        except Exception:
            pass
        try:
            if self.IsModal():
                self.EndModal(wx.ID_CANCEL)
            else:
                self.Destroy()
        except Exception:
            try:
                self.Destroy()
            except Exception:
                pass


# L'import du moteur historique ci-dessus renseigne automatiquement l'attribut
# Dlg.DLG_Impression_conso avec le module legacy. On rétablit l'adaptateur afin
# que le ``from Dlg import DLG_Impression_conso`` appelant reçoive bien celui-ci.
try:
    setattr(sys.modules["Dlg"], "DLG_Impression_conso", sys.modules[__name__])
except Exception:
    pass
