#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence : Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ol import OL_Individus
from Utils import UTILS_Aui
from Utils import UTILS_ColonnesResponsive
from Utils import UTILS_Config
from Utils import UTILS_FluentIcons
from Utils import UTILS_Interface
from Utils import UTILS_Recherche
from Utils import UTILS_Responsive
from Utils import UTILS_UIMetrics

ID_CREER_FAMILLE = wx.Window.NewControlId()
ID_MODIFIER_FAMILLE = wx.Window.NewControlId()
ID_SUPPRIMER_FAMILLE = wx.Window.NewControlId()
ID_OUVRIR_GRILLE = 60
ID_OUVRIR_FICHE_IND = 70
ID_PARAMETRES = wx.Window.NewControlId()
ID_OUTILS = wx.Window.NewControlId()

ATTRIBUTS_RECHERCHE = (
    "nom", "prenom", "rue_resid", "cp_resid", "ville_resid",
    "tel_domicile", "tel_mobile", "travail_tel", "mail", "travail_mail",
    "profession", "employeur",
)
ATTRIBUTS_TELEPHONES = ("tel_domicile", "tel_mobile", "travail_tel")
LIMITE_RESULTATS_ACCUEIL = 30


class ListeIndividusAccueil(OL_Individus.ListView):
    """Vue d'accueil dense sans la colonne d'avatars historique."""

    SPECS_COLONNES = (
        (120, 1.4), (105, 1.0), (82, 0.0), (55, 0.0), (150, 2.2),
        (58, 0.0), (110, 1.2), (105, 0.2), (105, 0.2), (170, 2.4),
        (72, 0.0),
    )

    def __init__(self, *args, **kwds):
        OL_Individus.ListView.__init__(self, *args, **kwds)
        UTILS_ColonnesResponsive.Installer(self, self.SPECS_COLONNES)

    def InitObjectListView(self):
        def FormateDate(date):
            return OL_Individus.UTILS_Dates.DateDDEnFr(date)

        def FormateAge(age):
            if age is None:
                return ""
            return _(u"%d ans") % age

        def FormateEtat(etat):
            if etat == "archive":
                return _(u"Archivé")
            if etat == "efface":
                return _(u"Effacé")
            return ""

        self.evenRowsBackColor = UTILS_Interface.GetCouleurRole("surface_container_lowest")
        self.oddRowsBackColor = UTILS_Interface.GetCouleurRole("surface_container_low")
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
        self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        self.useExpansionColumn = False

        colonnes = [
            OL_Individus.ColumnDefn(_(u"Nom"), "left", 120, "nom", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"Prénom"), "left", 105, "prenom", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"Date naiss."), "left", 82, "date_naiss", typeDonnee="date", stringConverter=FormateDate),
            OL_Individus.ColumnDefn(_(u"Age"), "left", 55, "age", typeDonnee="entier", stringConverter=FormateAge),
            OL_Individus.ColumnDefn(_(u"Rue"), "left", 150, "rue_resid", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"C.P."), "left", 58, "cp_resid", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"Ville"), "left", 110, "ville_resid", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"Tél. domicile"), "left", 105, "tel_domicile", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"Tél. mobile"), "left", 105, "tel_mobile", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"Email"), "left", 170, "mail", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"État"), "left", 72, "etat", typeDonnee="texte", stringConverter=FormateEtat),
            OL_Individus.ColumnDefn(_(u"Recherche"), "left", 0, "champ_recherche", typeDonnee="texte"),
        ]

        self.SetColumns(colonnes)
        self.SetSortColumn(self.columns[0])
        self.SetObjects(self.donnees)
        wx.CallAfter(UTILS_ColonnesResponsive.Ajuster, self)


class EtatRecherche(wx.Panel):
    """État vide/no-result de la recherche rapide, sans carte mobile."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))

        taille = UTILS_Responsive.GetTailleIcone(32)
        bitmap = UTILS_FluentIcons.GetBitmap("search", taille=taille)
        if bitmap is None:
            bitmap = wx.NullBitmap

        self.ctrl_icone = wx.StaticBitmap(self, bitmap=bitmap)
        self.ctrl_titre = wx.StaticText(self, label=_(u"Rechercher une famille ou un individu"))
        self.ctrl_detail = wx.StaticText(
            self,
            label=_(u"Nom, prénom, téléphone, email, adresse, code postal ou ville."),
        )
        self.ctrl_detail.Wrap(560)

        police = self.ctrl_titre.GetFont()
        police.SetWeight(wx.FONTWEIGHT_BOLD)
        police.SetPointSize(max(police.GetPointSize() + 2, 11))
        self.ctrl_titre.SetFont(police)

        self.ctrl_titre.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        self.ctrl_detail.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface_variant"))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddStretchSpacer(1)
        sizer.Add(self.ctrl_icone, 0, wx.ALIGN_CENTER | wx.BOTTOM, UTILS_UIMetrics.spacing(2))
        sizer.Add(self.ctrl_titre, 0, wx.ALIGN_CENTER | wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        sizer.Add(self.ctrl_detail, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, UTILS_UIMetrics.spacing(3))
        sizer.AddStretchSpacer(1)
        self.SetSizer(sizer)

    def AfficherRecherche(self):
        self.ctrl_titre.SetLabel(_(u"Rechercher une famille ou un individu"))
        self.ctrl_detail.SetLabel(_(u"Nom, prénom, téléphone, email, adresse, code postal ou ville."))
        self.Layout()

    def AfficherAucunResultat(self, texte):
        self.ctrl_titre.SetLabel(_(u"Aucun résultat"))
        if texte:
            self.ctrl_detail.SetLabel(
                _(u"Aucune fiche ne correspond à « %s ». Essayez une autre orthographe ou un autre critère.") % texte
            )
        else:
            self.ctrl_detail.SetLabel(_(u"Aucune fiche ne correspond à cette recherche."))
        self.Layout()


class BarreRechercheAccueil(OL_Individus.BarreRecherche):
    """Recherche d'accueil orientée accès rapide à une famille."""

    def __init__(self, parent):
        OL_Individus.BarreRecherche.__init__(self, parent, historique=True)
        self.SetDescriptiveText(_(u"Rechercher une famille ou un individu…"))
        self.SetMinSize((280, UTILS_UIMetrics.action_target("compact")))
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
        self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        self._index = {}
        try:
            self.listView.SetFilter(None)
        except Exception:
            pass

    def _GetIndex(self, track):
        cle = getattr(track, "IDindividu", id(track))
        index = self._index.get(cle)
        if index is None:
            index = UTILS_Recherche.ConstruireIndex(
                track,
                attributs=ATTRIBUTS_RECHERCHE,
                attributs_telephones=ATTRIBUTS_TELEPHONES,
            )
            self._index[cle] = index
        return index

    def InvaliderIndex(self):
        self._index = {}

    def _Trouver(self, texte, approximatif=False):
        resultats = []
        for track in self.listView.donnees:
            if UTILS_Recherche.Correspond(self._GetIndex(track), texte, approximatif=approximatif):
                resultats.append(track)
        return resultats

    def _MajResume(self, texte, nbre, approximatif=False, tronque=False):
        if not texte:
            label = _(u"Recherche rapide")
        elif nbre == 0:
            label = _(u"Aucun résultat")
        else:
            suffixe = _(u" · résultats proches") if approximatif else ""
            plus = "+" if tronque else ""
            label = _(u"%s%d résultat(s)%s") % (plus, nbre, suffixe)
        self.parent.ctrl_resume.SetLabel(label)
        self.parent.Layout()

    def Recherche(self, event=None):
        if self.timer.IsRunning():
            self.timer.Stop()
        texte = self.GetValue().strip()
        self.ShowCancelButton(bool(texte))

        if not texte:
            self.listView.SetObjects([])
            self._MajResume("", 0)
            self.parent.AfficherEtatVide()
            self.listView.Refresh()
            return

        resultats = self._Trouver(texte, approximatif=False)
        approximatif = False
        if not resultats:
            resultats = self._Trouver(texte, approximatif=True)
            approximatif = bool(resultats)

        total = len(resultats)
        tronque = total > LIMITE_RESULTATS_ACCUEIL
        self.listView.SetObjects(resultats[:LIMITE_RESULTATS_ACCUEIL])
        self._MajResume(texte, min(total, LIMITE_RESULTATS_ACCUEIL), approximatif, tronque)

        if total:
            self.parent.AfficherResultats()
        else:
            self.parent.AfficherAucunResultat(texte)
        self.listView.Refresh()

        if self.ouvrir_fiche:
            self.OuvrirFiche()

    def OuvrirFiche(self):
        if self.listView.GetItemCount() <= 0:
            return
        track = self.listView.GetObjectAt(0)
        if track is None:
            return
        self.listView.SelectObject(track)
        self.listView.OuvrirFicheFamille(track)
        self.ouvrir_fiche = False

    def AfficherTout(self):
        self.InvaliderIndex()
        try:
            self.ChangeValue("")
        except Exception:
            self.SetValue("")
        if self.timer.IsRunning():
            self.timer.Stop()
        self.ShowCancelButton(False)
        self.listView.SetObjects(self.listView.donnees)
        self.parent.ctrl_resume.SetLabel(_(u"%d individu(s) · liste complète") % len(self.listView.donnees))
        self.parent.AfficherResultats()
        self.listView.Refresh()


class ToolBar(wx.ToolBar):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TB_FLAT | wx.TB_TEXT | wx.TB_NODIVIDER
        wx.ToolBar.__init__(self, *args, **kwds)

        liste_boutons = [
            {"ID": ID_MODIFIER_FAMILLE, "label": _(u"Modifier"), "icone": "edit", "tooltip": _(u"Modifier la fiche famille de l'individu sélectionné")},
            {"ID": ID_SUPPRIMER_FAMILLE, "label": _(u"Supprimer"), "icone": "delete", "tooltip": _(u"Supprimer ou détacher l'individu sélectionné")},
            None,
            {"ID": ID_OUVRIR_GRILLE, "label": _(u"Calendrier"), "icone": "calendar", "tooltip": _(u"Ouvrir la grille des consommations de l'individu sélectionné\n(ou double-clic sur la ligne + touche CTRL enfoncée)")},
            {"ID": ID_OUVRIR_FICHE_IND, "label": _(u"Fiche ind."), "icone": "people", "tooltip": _(u"Ouvrir la fiche individuelle de l'individu sélectionné\n(ou double-clic sur la ligne + touche SHIFT enfoncée)")},
            None,
            {"ID": ID_PARAMETRES, "label": _(u"Paramètres"), "icone": "settings", "tooltip": _(u"Sélectionner les paramètres d'affichage")},
            {"ID": ID_OUTILS, "label": _(u"Outils"), "icone": "settings", "tooltip": _(u"Outils")},
        ]

        taille_bitmap = UTILS_Responsive.GetTailleIcone(20)
        for bouton in liste_boutons:
            if bouton is None:
                self.AddSeparator()
            else:
                bitmap = UTILS_FluentIcons.GetBitmap(bouton["icone"], taille=taille_bitmap)
                if bitmap is None:
                    bitmap = wx.NullBitmap
                try:
                    self.AddTool(bouton["ID"], bouton["label"], bitmap, wx.NullBitmap, wx.ITEM_NORMAL, bouton["tooltip"], "")
                except Exception:
                    self.AddLabelTool(bouton["ID"], bouton["label"], bitmap, wx.NullBitmap, wx.ITEM_NORMAL, bouton["tooltip"], "")

        self.Bind(wx.EVT_TOOL, self.Modifier_famille, id=ID_MODIFIER_FAMILLE)
        self.Bind(wx.EVT_TOOL, self.Supprimer_famille, id=ID_SUPPRIMER_FAMILLE)
        self.Bind(wx.EVT_TOOL, self.Ouvrir_grille, id=ID_OUVRIR_GRILLE)
        self.Bind(wx.EVT_TOOL, self.Ouvrir_fiche_ind, id=ID_OUVRIR_FICHE_IND)
        self.Bind(wx.EVT_TOOL, self.Parametres, id=ID_PARAMETRES)
        self.Bind(wx.EVT_TOOL, self.MenuOutils, id=ID_OUTILS)

        UTILS_Aui.ConfigurerToolBar(self, taille_base=20, fond_uni=True)
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))
        self.SetMinSize((-1, UTILS_UIMetrics.toolbar_height(avec_libelle=True, icon_px=taille_bitmap)))
        self.Realize()

    def Ajouter_famille(self, event):
        self.GetParent().ctrl_listview.Ajouter(None)

    def Modifier_famille(self, event):
        self.GetParent().ctrl_listview.Modifier(None)

    def Supprimer_famille(self, event):
        self.GetParent().ctrl_listview.Supprimer(None)

    def Ouvrir_grille(self, event):
        self.GetParent().ctrl_listview.Modifier(event)

    def Ouvrir_fiche_ind(self, event):
        self.GetParent().ctrl_listview.Modifier(event)

    def Parametres(self, event):
        parametres = UTILS_Config.GetParametre("liste_individus_parametres", defaut="")
        from Dlg import DLG_Selection_individus
        dlg = DLG_Selection_individus.Dialog(self)
        dlg.SetParametres(parametres)
        if dlg.ShowModal() == wx.ID_OK:
            UTILS_Config.SetParametre("liste_individus_parametres", dlg.GetParametres())
        dlg.Destroy()
        self.GetParent().ActualiseParametresAffichage()
        self.GetParent().MAJ()

    def _BitmapMenu(self, image):
        taille = UTILS_Responsive.GetTailleIcone(16)
        return wx.Bitmap(Chemins.GetStaticIconPath(image, taille=taille), wx.BITMAP_TYPE_PNG)

    def MenuOutils(self, event):
        menuPop = UTILS_Adaptations.Menu()
        ID_ACTUALISER = wx.Window.NewControlId()
        ID_IMPRIMER = wx.Window.NewControlId()
        ID_APERCU = wx.Window.NewControlId()
        ID_EXPORT_EXCEL = wx.Window.NewControlId()
        ID_EXPORT_TEXTE = wx.Window.NewControlId()
        ID_AIDE = wx.Window.NewControlId()

        item = wx.MenuItem(menuPop, ID_APERCU, _(u"Aperçu avant impression"), _(u"Imprimer la liste des effectifs affichée"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Apercu.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=ID_APERCU)

        item = wx.MenuItem(menuPop, ID_IMPRIMER, _(u"Imprimer"), _(u"Imprimer la liste des effectifs affichée"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Imprimante.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=ID_IMPRIMER)

        menuPop.AppendSeparator()
        item = wx.MenuItem(menuPop, ID_EXPORT_TEXTE, _(u"Exporter au format Texte"), _(u"Exporter au format Texte"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Texte2.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.GetParent().ctrl_listview.ExportTexte, id=ID_EXPORT_TEXTE)

        item = wx.MenuItem(menuPop, ID_EXPORT_EXCEL, _(u"Exporter au format Excel"), _(u"Exporter la liste au format Excel"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Excel.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.GetParent().ctrl_listview.ExportExcel, id=ID_EXPORT_EXCEL)

        menuPop.AppendSeparator()
        item = wx.MenuItem(menuPop, ID_ACTUALISER, _(u"Actualiser"), _(u"Actualiser l'affichage"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Actualiser2.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Actualiser, id=ID_ACTUALISER)

        menuPop.AppendSeparator()
        item = wx.MenuItem(menuPop, ID_AIDE, _(u"Aide"), _(u"Aide"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Aide.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Aide, id=ID_AIDE)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        self.GetParent().ctrl_listview.Apercu(None)

    def Imprimer(self, event):
        self.GetParent().ctrl_listview.Imprimer(None)

    def Actualiser(self, event):
        self.GetParent().MAJ()

    def Aide(self, event):
        self.GetParent().Aide()


class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, name="recherche_individus", id=-1, style=wx.TAB_TRAVERSAL)

        self.ctrl_titre = wx.StaticText(self, label=_(u"Individus / Familles"))
        self.ctrl_nouvelle_famille = wx.Button(self, label=_(u"Nouvelle famille"))
        try:
            bitmap = UTILS_FluentIcons.GetBitmap("add", taille=UTILS_Responsive.GetTailleIcone(20))
            if bitmap is not None:
                self.ctrl_nouvelle_famille.SetBitmap(bitmap)
        except Exception:
            pass
        self.ctrl_nouvelle_famille.SetMinSize((-1, UTILS_UIMetrics.action_target("compact")))

        self.ctrl_listview = ListeIndividusAccueil(
            self,
            id=-1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.NO_BORDER,
        )
        self.ctrl_recherche = BarreRechercheAccueil(self)
        self.ctrl_resume = wx.StaticText(self, label=_(u"Recherche rapide"))
        self.ctrl_voir_tout = wx.Button(self, label=_(u"Voir tout"))
        self.ctrl_voir_tout.SetMinSize((-1, UTILS_UIMetrics.action_target("compact")))

        self.toolBar = ToolBar(self)
        self.ctrl_etat = EtatRecherche(self)

        self.ctrl_nouvelle_famille.Bind(wx.EVT_BUTTON, self.toolBar.Ajouter_famille)
        self.ctrl_voir_tout.Bind(wx.EVT_BUTTON, lambda evt: self.ctrl_recherche.AfficherTout())

        self.__set_properties()
        self.__do_layout()
        self.ActualiseParametresAffichage()
        wx.CallAfter(self.AfficherEtatVide)
        wx.CallAfter(self._ConfigurerPaneAui)

    def __set_properties(self):
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        police_titre = self.ctrl_titre.GetFont()
        police_titre.SetWeight(wx.FONTWEIGHT_BOLD)
        police_titre.SetPointSize(max(police_titre.GetPointSize() + 2, 11))
        self.ctrl_titre.SetFont(police_titre)

        self.ctrl_titre.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        self.ctrl_resume.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface_variant"))

    def __do_layout(self):
        principal = wx.BoxSizer(wx.VERTICAL)
        marge = UTILS_UIMetrics.spacing(1)

        # Une seule ligne fonctionnelle : titre, état, recherche et création.
        # L'ancienne superposition titre/sous-titre/recherche/résumé consommait
        # beaucoup de surface sans apporter d'information supplémentaire.
        entete = wx.BoxSizer(wx.HORIZONTAL)
        entete.Add(self.ctrl_titre, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, UTILS_UIMetrics.spacing(2))
        entete.Add(self.ctrl_resume, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, UTILS_UIMetrics.spacing(2))
        entete.AddStretchSpacer(1)
        entete.Add(self.ctrl_recherche, 2, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, marge)
        entete.Add(self.ctrl_voir_tout, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, marge)
        entete.Add(self.ctrl_nouvelle_famille, 0, wx.ALIGN_CENTER_VERTICAL)
        principal.Add(entete, 0, wx.EXPAND | wx.ALL, marge)

        principal.Add(self.toolBar, 0, wx.EXPAND)
        principal.Add(self.ctrl_listview, 1, wx.EXPAND)
        principal.Add(self.ctrl_etat, 1, wx.EXPAND)

        self.SetSizer(principal)
        self.Layout()

    def _ConfigurerPaneAui(self):
        """Rend le pane Individus pleinement manipulable comme les autres panneaux."""
        try:
            top = self.GetTopLevelParent()
            manager = getattr(top, "_mgr", None)
            if manager is None:
                return
            pane = manager.GetPane(self)
            if pane is None or not pane.IsOk():
                pane = manager.GetPane("recherche")
            if pane is None or not pane.IsOk():
                return
            pane.Caption(_(u"Individus / Familles"))
            pane.CaptionVisible(True)
            pane.PaneBorder(True)
            pane.CloseButton(True)
            pane.MaximizeButton(True)
            pane.MinimizeButton(True)
            pane.Resizable(True)
            manager.Update()
        except Exception:
            pass

    def _AfficherContenu(self, liste=False, etat=False):
        self.toolBar.Show(liste)
        self.ctrl_listview.Show(liste)
        self.ctrl_etat.Show(etat)
        self.Layout()

    def AfficherEtatVide(self):
        self.ctrl_etat.AfficherRecherche()
        self._AfficherContenu(liste=False, etat=True)

    def AfficherAucunResultat(self, texte):
        self.ctrl_etat.AfficherAucunResultat(texte)
        self._AfficherContenu(liste=False, etat=True)

    def AfficherResultats(self):
        self._AfficherContenu(liste=True, etat=False)
        self._ConfigurerPaneAui()
        wx.CallAfter(UTILS_ColonnesResponsive.Ajuster, self.ctrl_listview)

    def MAJ(self):
        self.ctrl_listview.MAJ(forceActualisation=True)
        self.ctrl_recherche.InvaliderIndex()
        self.ctrl_recherche.Recherche()

    def Aide(self):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Lalistedesindividus")

    def ActualiseParametresAffichage(self):
        parametres = UTILS_Config.GetParametre("liste_individus_parametres", defaut="")
        self.ctrl_listview.SetParametres(parametres)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL | wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Panel(panel)
        self.ctrl.MAJ()
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(1000, 600))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
