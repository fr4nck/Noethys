#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence : Licence GNU GPL
#-----------------------------------------------------------

import wx

from Ctrl import CTRL_ActionRepens
from Ol import OL_Individus
from Utils import UTILS_Adaptations
from Utils import UTILS_ColonnesResponsive
from Utils import UTILS_Config
from Utils import UTILS_IconesRepens
from Utils import UTILS_Interface
from Utils import UTILS_Recherche
from Utils import UTILS_Responsive
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


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
    """Vue d'accueil dense, responsive et sans colonne d'avatars."""

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


class IndicationRecherche(wx.Panel):
    """Indication compacte : le tableau reste la surface principale."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))

        bitmap = UTILS_IconesRepens.GetBitmap(
            "search",
            taille=UTILS_Responsive.GetTailleIcone(18),
            role="on_surface_variant",
        )
        if bitmap is None:
            bitmap = wx.NullBitmap
        self.ctrl_icone = wx.StaticBitmap(self, bitmap=bitmap)
        self.ctrl_titre = wx.StaticText(self, label=_(u"Recherchez une famille ou un individu"))
        self.ctrl_detail = wx.StaticText(
            self,
            label=_(u"Nom, prénom, téléphone, email, adresse, code postal ou ville."),
        )
        self.ctrl_titre.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        self.ctrl_detail.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface_variant"))

        police = self.ctrl_titre.GetFont()
        police.SetWeight(wx.FONTWEIGHT_BOLD)
        self.ctrl_titre.SetFont(police)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        marge = UTILS_UIMetrics.spacing(2)
        sizer.Add(self.ctrl_icone, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, marge)
        textes = wx.BoxSizer(wx.VERTICAL)
        textes.Add(self.ctrl_titre, 0)
        textes.Add(self.ctrl_detail, 0, wx.TOP, UTILS_UIMetrics.spacing(1))
        sizer.Add(textes, 1, wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(sizer)
        self.SetMinSize((-1, UTILS_UIMetrics.px(54)))

    def AfficherRecherche(self):
        self.ctrl_titre.SetLabel(_(u"Recherchez une famille ou un individu"))
        self.ctrl_detail.SetLabel(_(u"Nom, prénom, téléphone, email, adresse, code postal ou ville."))
        self.Layout()

    def AfficherAucunResultat(self, texte):
        self.ctrl_titre.SetLabel(_(u"Aucun résultat"))
        if texte:
            self.ctrl_detail.SetLabel(_(u"Aucune fiche ne correspond à « %s ». Essayez une autre orthographe ou un autre critère.") % texte)
        else:
            self.ctrl_detail.SetLabel(_(u"Aucune fiche ne correspond à cette recherche."))
        self.Layout()


class BarreRechercheAccueil(OL_Individus.BarreRecherche):
    """Recherche d'accueil orientée accès rapide à une famille."""

    def __init__(self, parent):
        OL_Individus.BarreRecherche.__init__(self, parent, historique=True)
        self.SetDescriptiveText(_(u"Rechercher une famille ou un individu…"))
        self.SetMinSize((UTILS_UIMetrics.px(300), UTILS_UIMetrics.action_target("compact")))
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
            suffixe = _(u" · proches") if approximatif else ""
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


class BarreCommandes(wx.Panel):
    """Commandes quotidiennes de la sélection, sans grosse toolbar héritée."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))

        self.ctrl_modifier = CTRL_ActionRepens.CTRL(
            self, id=ID_MODIFIER_FAMILLE, label=_(u"Modifier"), icone="edit",
            tooltip=_(u"Modifier la fiche famille de l'individu sélectionné"),
        )
        self.ctrl_calendrier = CTRL_ActionRepens.CTRL(
            self, id=ID_OUVRIR_GRILLE, label=_(u"Calendrier"), icone="calendar",
            tooltip=_(u"Ouvrir les consommations de l'individu sélectionné"),
        )
        self.ctrl_fiche = CTRL_ActionRepens.CTRL(
            self, id=ID_OUVRIR_FICHE_IND, label=_(u"Fiche individuelle"), icone="people",
            tooltip=_(u"Ouvrir la fiche individuelle"),
        )
        self.ctrl_plus = CTRL_ActionRepens.CTRL(
            self, id=ID_OUTILS, label=_(u"Plus"), icone="more", variante="ghost",
            tooltip=_(u"Supprimer, paramètres, impression, export et aide"),
        )

        self.ctrl_modifier.Bind(wx.EVT_BUTTON, self.OnModifier)
        self.ctrl_calendrier.Bind(wx.EVT_BUTTON, self.OnCalendrier)
        self.ctrl_fiche.Bind(wx.EVT_BUTTON, self.OnFiche)
        self.ctrl_plus.Bind(wx.EVT_BUTTON, self.OnPlus)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        marge = UTILS_UIMetrics.spacing(1)
        sizer.Add(self.ctrl_modifier, 0, wx.RIGHT, marge)
        sizer.Add(self.ctrl_calendrier, 0, wx.RIGHT, marge)
        sizer.Add(self.ctrl_fiche, 0, wx.RIGHT, marge)
        sizer.AddStretchSpacer(1)
        sizer.Add(self.ctrl_plus, 0)
        self.SetSizer(sizer)
        self.ActualiserEtat()

    def ActualiserEtat(self):
        actif = self.parent._GetTrackSelectionne() is not None
        for ctrl in (self.ctrl_modifier, self.ctrl_calendrier, self.ctrl_fiche):
            ctrl.Enable(actif)
            ctrl.Refresh()

    def OnModifier(self, event=None):
        self.parent.ctrl_listview.Modifier(None)

    def OnCalendrier(self, event=None):
        evenement = wx.CommandEvent(wx.wxEVT_BUTTON, ID_OUVRIR_GRILLE)
        evenement.SetEventObject(self)
        self.parent.ctrl_listview.Modifier(evenement)

    def OnFiche(self, event=None):
        evenement = wx.CommandEvent(wx.wxEVT_BUTTON, ID_OUVRIR_FICHE_IND)
        evenement.SetEventObject(self)
        self.parent.ctrl_listview.Modifier(evenement)

    def OnPlus(self, event=None):
        menu = UTILS_Adaptations.Menu()

        def Ajouter(label, callback):
            identifiant = wx.Window.NewControlId()
            menu.Append(identifiant, label)
            self.Bind(wx.EVT_MENU, callback, id=identifiant)

        selection = self.parent._GetTrackSelectionne() is not None
        identifiant_supprimer = wx.Window.NewControlId()
        item = menu.Append(identifiant_supprimer, _(u"Supprimer ou détacher…"))
        item.Enable(selection)
        self.Bind(wx.EVT_MENU, lambda evt: self.parent.ctrl_listview.Supprimer(None), id=identifiant_supprimer)

        menu.AppendSeparator()
        Ajouter(_(u"Paramètres d'affichage…"), self.OnParametres)
        Ajouter(_(u"Actualiser"), lambda evt: self.parent.MAJ())
        menu.AppendSeparator()
        Ajouter(_(u"Aperçu avant impression"), lambda evt: self.parent.ctrl_listview.Apercu(None))
        Ajouter(_(u"Imprimer"), lambda evt: self.parent.ctrl_listview.Imprimer(None))
        Ajouter(_(u"Exporter au format Texte"), lambda evt: self.parent.ctrl_listview.ExportTexte(None))
        Ajouter(_(u"Exporter au format Excel"), lambda evt: self.parent.ctrl_listview.ExportExcel(None))
        menu.AppendSeparator()
        Ajouter(_(u"Aide"), lambda evt: self.parent.Aide())

        self.PopupMenu(menu)
        menu.Destroy()

    def OnParametres(self, event=None):
        parametres = UTILS_Config.GetParametre("liste_individus_parametres", defaut="")
        from Dlg import DLG_Selection_individus
        dlg = DLG_Selection_individus.Dialog(self)
        dlg.SetParametres(parametres)
        if dlg.ShowModal() == wx.ID_OK:
            UTILS_Config.SetParametre("liste_individus_parametres", dlg.GetParametres())
        dlg.Destroy()
        self.parent.ActualiseParametresAffichage()
        self.parent.MAJ()


class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, name="recherche_individus", id=-1, style=wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        # Le titre du module appartient au pane AUI. Ici on garde uniquement
        # l'état de la recherche et les commandes utiles au contexte courant.
        self.ctrl_resume = wx.StaticText(self, label=_(u"Recherche rapide"))
        self.ctrl_resume.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface_variant"))
        police_resume = self.ctrl_resume.GetFont()
        try:
            police_resume.SetWeight(wx.FONTWEIGHT_SEMIBOLD)
        except Exception:
            police_resume.SetWeight(wx.FONTWEIGHT_BOLD)
        self.ctrl_resume.SetFont(police_resume)

        self.ctrl_listview = ListeIndividusAccueil(
            self,
            id=-1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.NO_BORDER,
        )
        self.ctrl_recherche = BarreRechercheAccueil(self)

        self.ctrl_voir_tout = CTRL_ActionRepens.CTRL(
            self, label=_(u"Voir tout"), icone="people", variante="ghost",
            tooltip=_(u"Afficher toute la liste"),
        )
        self.ctrl_email = CTRL_ActionRepens.CTRL(
            self, label=u"", icone="mail", variante="secondaire",
            tooltip=_(u"Envoyer un email"),
        )
        self.ctrl_sms = CTRL_ActionRepens.CTRL(
            self, label=u"", icone="chat", variante="secondaire",
            tooltip=_(u"Envoyer un SMS"),
        )
        self.ctrl_nouvelle_famille = CTRL_ActionRepens.CTRL(
            self, id=ID_CREER_FAMILLE, label=_(u"Nouvelle famille"), icone="add", variante="primaire",
            tooltip=_(u"Créer une nouvelle famille"),
        )

        self.ctrl_commandes = BarreCommandes(self)
        self.ctrl_indication = IndicationRecherche(self)

        self.ctrl_voir_tout.Bind(wx.EVT_BUTTON, lambda evt: self.ctrl_recherche.AfficherTout())
        self.ctrl_email.Bind(wx.EVT_BUTTON, self.OnEmail)
        self.ctrl_sms.Bind(wx.EVT_BUTTON, self.OnSMS)
        self.ctrl_nouvelle_famille.Bind(wx.EVT_BUTTON, lambda evt: self.ctrl_listview.Ajouter(None))
        self.ctrl_listview.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectionChange)
        self.ctrl_listview.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelectionChange)

        self.__do_layout()
        self.ActualiseParametresAffichage()
        wx.CallAfter(self.AfficherEtatVide)
        wx.CallAfter(self._ConfigurerPaneAui)

    def __do_layout(self):
        principal = wx.BoxSizer(wx.VERTICAL)
        marge = UTILS_UIMetrics.spacing(2)
        petit = UTILS_UIMetrics.spacing(1)

        # Ligne contextuelle : statut > recherche > communication > création.
        entete = wx.BoxSizer(wx.HORIZONTAL)
        entete.Add(self.ctrl_resume, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, marge)
        entete.Add(self.ctrl_recherche, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, petit)
        entete.Add(self.ctrl_voir_tout, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, petit)
        entete.Add(self.ctrl_email, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, petit)
        entete.Add(self.ctrl_sms, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, petit)
        entete.Add(self.ctrl_nouvelle_famille, 0, wx.ALIGN_CENTER_VERTICAL)
        principal.Add(entete, 0, wx.EXPAND | wx.ALL, marge)

        principal.Add(self.ctrl_commandes, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, marge)
        principal.Add(self.ctrl_indication, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, marge)
        principal.Add(self.ctrl_listview, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, petit)

        self.SetSizer(principal)
        self.Layout()

    def _ConfigurerPaneAui(self):
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
            pane.Movable(True)
            manager.Update()
        except Exception:
            pass

    def _GetTrackSelectionne(self):
        try:
            index = self.ctrl_listview.GetFirstSelected()
        except Exception:
            index = -1
        if index is None or index < 0:
            return None
        try:
            return self.ctrl_listview.GetObjectAt(index)
        except Exception:
            return None

    def OnSelectionChange(self, event):
        wx.CallAfter(self.ctrl_commandes.ActualiserEtat)
        event.Skip()

    def OnEmail(self, event=None):
        adresses = []
        track = self._GetTrackSelectionne()
        if track is not None:
            for attribut in ("mail", "travail_mail"):
                adresse = getattr(track, attribut, None)
                if adresse not in (None, ""):
                    adresses.append(adresse)
                    break

        from Dlg import DLG_Mailer
        dlg = DLG_Mailer.Dialog(self, categorie="saisie_libre")
        if adresses:
            try:
                dlg.ctrl_destinataires.SetDonneesManuelles(adresses)
            except Exception:
                pass
        dlg.ShowModal()
        dlg.Destroy()

    def OnSMS(self, event=None):
        numero = None
        track = self._GetTrackSelectionne()
        if track is not None:
            for attribut in ("tel_mobile", "tel_domicile", "travail_tel"):
                valeur = getattr(track, attribut, None)
                if valeur not in (None, ""):
                    numero = valeur
                    break

        from Dlg import DLG_Envoi_sms
        dlg = DLG_Envoi_sms.Dialog(self)
        if numero:
            try:
                destinataires = dlg.GetPage("destinataires").ctrl_destinataires
                page = destinataires.GetPageByCode("saisie_manuelle")
                page.SetDonnees({"texte": numero})
                index = destinataires.GetIndexPageByCode("saisie_manuelle")
                if index is not None:
                    destinataires.SetSelection(index)
            except Exception:
                pass
        dlg.ShowModal()
        dlg.Destroy()

    def AfficherEtatVide(self):
        self.ctrl_indication.AfficherRecherche()
        self.ctrl_indication.Show(True)
        self.ctrl_commandes.Show(False)
        self.ctrl_listview.SetObjects([])
        self.Layout()

    def AfficherAucunResultat(self, texte):
        self.ctrl_indication.AfficherAucunResultat(texte)
        self.ctrl_indication.Show(True)
        self.ctrl_commandes.Show(False)
        self.Layout()

    def AfficherResultats(self):
        self.ctrl_indication.Show(False)
        self.ctrl_commandes.Show(True)
        self.ctrl_commandes.ActualiserEtat()
        self._ConfigurerPaneAui()
        self.Layout()
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
        sizer_1.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Panel(panel)
        self.ctrl.MAJ()
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.EXPAND)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(1200, 700))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
