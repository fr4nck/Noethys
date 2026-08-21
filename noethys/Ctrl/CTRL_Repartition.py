#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import datetime

import wx
import wx.lib.agw.hypertreelist as HTL

import Chemins
import GestionDB
from Ol import OL_Prestations_repartition
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


def DateEngFr(textDate):
    return str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])


def DateComplete(dateDD):
    listeJours = (_(u"Lundi"), _(u"Mardi"), _(u"Mercredi"), _(u"Jeudi"), _(u"Vendredi"), _(u"Samedi"), _(u"Dimanche"))
    listeMois = (_(u"janvier"), _(u"février"), _(u"mars"), _(u"avril"), _(u"mai"), _(u"juin"), _(u"juillet"), _(u"août"), _(u"septembre"), _(u"octobre"), _(u"novembre"), _(u"décembre"))
    return listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month - 1] + " " + str(dateDD.year)


def DateEngEnDateDD(dateEng):
    return datetime.date.fromisoformat(dateEng[:10])


def PeriodeComplete(mois, annee):
    listeMois = (_(u"Janvier"), _(u"Février"), _(u"Mars"), _(u"Avril"), _(u"Mai"), _(u"Juin"), _(u"Juillet"), _(u"Août"), _(u"Septembre"), _(u"Octobre"), _(u"Novembre"), _(u"Décembre"))
    return u"%s %d" % (listeMois[mois - 1], annee)


class Track(object):
    def __init__(self, donnees):
        self.IDreglement = donnees[0]
        self.compte_payeur = donnees[1]
        self.date = DateEngEnDateDD(donnees[2])
        self.dateComplete = DateComplete(self.date)
        self.IDmode = donnees[3]
        self.nom_mode = donnees[4]
        self.IDemetteur = donnees[5]
        self.nom_emetteur = donnees[6] or u""
        self.numero_piece = donnees[7] or u""
        self.montant = donnees[8]
        self.montant_str = u"%.2f € " % self.montant
        self.IDpayeur = donnees[9]
        self.nom_payeur = donnees[10]
        self.observations = donnees[11]
        self.numero_quittancier = donnees[12]
        self.IDprestation_frais = donnees[13]
        self.IDcompte = donnees[14]
        self.date_differe = DateEngEnDateDD(donnees[15]) if donnees[15] is not None else None
        self.encaissement_attente = donnees[16]
        self.IDdepot = donnees[17]
        self.date_depot = donnees[18]
        if self.date_depot is not None:
            self.date_depot = DateEngEnDateDD(self.date_depot)
            self.date_depot_str = DateEngFr(donnees[18])
        else:
            self.date_depot_str = u""
        self.nom_depot = donnees[19]
        self.verrouillage_depot = donnees[20]
        self.date_saisie = DateEngEnDateDD(donnees[21]) if donnees[21] is not None else None
        self.IDutilisateur = donnees[22]
        self.montant_ventilation = donnees[23] or 0.0
        self.montant_ventilation_str = u"%.2f € " % self.montant_ventilation
        self.ctrl_prestations = None

    def GetImageVentilation(self):
        resteAVentiler = self.montant - self.montant_ventilation
        if abs(resteAVentiler) < 0.005:
            return "vert"
        if resteAVentiler > 0.0:
            return "orange"
        return "rouge"

    def GetImageDepot(self):
        if self.IDdepot is None:
            return "attente" if self.encaissement_attente == 1 else "non"
        return "ok"


class CTRL(HTL.HyperTreeList):
    """Répartition des règlements, adaptée à la largeur réellement disponible."""

    SPECS_COLONNES = (
        (_(u"Date"), 180, 1.9),
        (_(u"Mode"), 120, 1.1),
        (_(u"Émetteur"), 120, 1.0),
        (_(u"Numéro"), 72, 0.3),
        (_(u"Payeur"), 100, 0.8),
        (_(u"Montant"), 82, 0.4),
        (_(u"Ventilé"), 82, 0.4),
        (_(u"Dépôt"), 100, 0.8),
    )

    def __init__(self, parent, IDfamille=None):
        HTL.HyperTreeList.__init__(self, parent, -1)
        self.parent = parent
        self.IDfamille = IDfamille
        self.listeTracks = []
        self._resize_pending = False

        DB = GestionDB.DB()
        req = """SELECT IDcompte_payeur
        FROM familles
        WHERE IDfamille=%d""" % self.IDfamille
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        self.IDcompte_payeur = listeDonnees[0][0]

        for label, largeur, _poids in self.SPECS_COLONNES:
            self.AddColumn(label)
            index = self.GetColumnCount() - 1
            self.SetColumnWidth(index, Style.px(largeur))
            self.SetColumnAlignment(index, wx.ALIGN_LEFT)

        Style.appliquer_liste(self)
        try:
            Style.appliquer_liste(self.GetMainWindow())
        except Exception:
            pass

        if 'phoenix' in wx.PlatformInfo:
            TR_COLUMN_LINES = HTL.TR_COLUMN_LINES
        else:
            TR_COLUMN_LINES = wx.TR_COLUMN_LINES
        self.SetAGWWindowStyleFlag(
            wx.TR_ROW_LINES | TR_COLUMN_LINES | wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS |
            wx.TR_HAS_VARIABLE_ROW_HEIGHT | wx.TR_FULL_ROW_HIGHLIGHT
        )
        self.EnableSelectionVista(True)
        self.SetMinSize((Style.px(640), Style.px(260)))
        self.Bind(wx.EVT_SIZE, self.OnSize)
        wx.CallAfter(self._AjusterLargeur)

    def _BitmapEtat(self, image):
        taille = Style.taille_icone("inline")
        chemin = Chemins.GetStaticIconPath(image, taille=taille)
        bitmap = wx.Bitmap(chemin, wx.BITMAP_TYPE_ANY)
        if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
            bitmap = wx.Bitmap(bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH))
        return bitmap

    def OnSize(self, event):
        event.Skip()
        if self._resize_pending:
            return
        self._resize_pending = True
        wx.CallAfter(self._AjusterLargeur)

    def _AjusterLargeur(self):
        self._resize_pending = False
        try:
            largeur_client = self.GetClientSize().GetWidth()
            if largeur_client <= 0:
                return
            bases = [Style.px(spec[1]) for spec in self.SPECS_COLONNES]
            poids = [spec[2] for spec in self.SPECS_COLONNES]
            total_base = sum(bases)
            disponible = max(0, largeur_client - Style.espace(2))
            surplus = max(0, disponible - total_base)
            total_poids = sum(poids)
            for index, base in enumerate(bases):
                largeur = base
                if surplus > 0 and total_poids > 0:
                    largeur += int(round(surplus * poids[index] / total_poids))
                self.SetColumnWidth(index, largeur)

            largeur_sous_liste = max(Style.px(520), disponible - Style.espace(3))
            for track in self.listeTracks:
                if track.ctrl_prestations is not None:
                    hauteur = self._HauteurSousListe(track.ctrl_prestations)
                    track.ctrl_prestations.SetSize((largeur_sous_liste, hauteur))
            try:
                self.GetMainWindow().CalculatePositions()
            except Exception:
                pass
        except Exception:
            pass

    def _HauteurSousListe(self, ctrl):
        try:
            nombre = len(ctrl.donnees)
        except Exception:
            nombre = 0
        return Style.px(34) + nombre * Style.hauteur_ligne("compact")

    def Importation(self):
        db = GestionDB.DB()
        req = """SELECT
        reglements.IDreglement, reglements.IDcompte_payeur, reglements.date,
        reglements.IDmode, modes_reglements.label,
        reglements.IDemetteur, emetteurs.nom,
        reglements.numero_piece, reglements.montant,
        payeurs.IDpayeur, payeurs.nom,
        reglements.observations, numero_quittancier, IDprestation_frais, reglements.IDcompte, date_differe,
        encaissement_attente,
        reglements.IDdepot, depots.date, depots.nom, depots.verrouillage,
        date_saisie, IDutilisateur,
        SUM(ventilation.montant) AS total_ventilation
        FROM reglements
        LEFT JOIN ventilation ON reglements.IDreglement = ventilation.IDreglement
        LEFT JOIN modes_reglements ON reglements.IDmode=modes_reglements.IDmode
        LEFT JOIN emetteurs ON reglements.IDemetteur=emetteurs.IDemetteur
        LEFT JOIN payeurs ON reglements.IDpayeur=payeurs.IDpayeur
        LEFT JOIN depots ON reglements.IDdepot=depots.IDdepot
        WHERE reglements.IDcompte_payeur=%d
        GROUP BY reglements.IDreglement
        ORDER BY reglements.date;""" % self.IDcompte_payeur
        db.ExecuterReq(req)
        listeDonnees = db.ResultatReq()
        db.Close()
        return [Track(item) for item in listeDonnees]

    def MAJ(self):
        self.DeleteAllItems()
        self.root = self.AddRoot(_(u"Racine"))
        self.Remplissage()
        wx.CallAfter(self._AjusterLargeur)

    def Remplissage(self):
        listeTracks = self.Importation()

        taille_icone = Style.taille_icone("inline")
        il = wx.ImageList(taille_icone, taille_icone)
        self.imgVert = il.Add(self._BitmapEtat("Images/16x16/Ventilation_vert.png"))
        self.imgRouge = il.Add(self._BitmapEtat("Images/16x16/Ventilation_rouge.png"))
        self.imgOrange = il.Add(self._BitmapEtat("Images/16x16/Ventilation_orange.png"))
        self.imgAttente = il.Add(self._BitmapEtat("Images/16x16/Attente.png"))
        self.imgOk = il.Add(self._BitmapEtat("Images/16x16/Ok.png"))
        self.imgNon = il.Add(self._BitmapEtat("Images/16x16/Interdit.png"))
        self.AssignImageList(il)

        largeur_sous_liste = max(Style.px(520), self.GetClientSize().GetWidth() - Style.espace(3))
        for track in listeTracks:
            regroupement = self.AppendItem(self.root, track.dateComplete)
            self.SetPyData(regroupement, None)
            self.SetItemText(regroupement, track.nom_mode, 1)
            self.SetItemText(regroupement, track.nom_emetteur, 2)
            self.SetItemText(regroupement, track.numero_piece, 3)
            self.SetItemText(regroupement, track.nom_payeur, 4)
            self.SetItemText(regroupement, track.montant_str, 5)
            self.SetItemText(regroupement, track.montant_ventilation_str, 6)
            self.SetItemText(regroupement, track.date_depot_str, 7)

            images_ventilation = {"vert": self.imgVert, "orange": self.imgOrange, "rouge": self.imgRouge}
            regroupement.SetImage(6, images_ventilation[track.GetImageVentilation()], which=wx.TreeItemIcon_Normal)
            images_depot = {"ok": self.imgOk, "attente": self.imgAttente, "non": self.imgNon}
            regroupement.SetImage(7, images_depot[track.GetImageDepot()], which=wx.TreeItemIcon_Normal)

            prestations = self.AppendItem(regroupement, "")
            self.SetPyData(prestations, track.IDreglement)
            ctrl_prestations = OL_Prestations_repartition.ListView(
                self.GetMainWindow(),
                -1,
                IDfamille=self.IDfamille,
                size=(-1, -1),
                style=wx.LC_REPORT | wx.BORDER_THEME,
            )
            ctrl_prestations.SetFiltre("ventilation.IDreglement", track.IDreglement)
            ctrl_prestations.SetSize((largeur_sous_liste, self._HauteurSousListe(ctrl_prestations)))
            self.SetItemWindow(prestations, ctrl_prestations, 0)
            track.ctrl_prestations = ctrl_prestations

        try:
            self.GetMainWindow().CalculatePositions()
        except Exception:
            pass
        self.listeTracks = listeTracks

    def OnCompareItems(self, item1, item2):
        data1 = self.GetPyData(item1)
        data2 = self.GetPyData(item2)
        if data1 is None or data2 is None:
            return 0
        if data1 > data2:
            return 1
        if data1 < data2:
            return -1
        return 0

    def RAZ(self):
        self.DeleteAllItems()
        try:
            self.DeleteRoot()
        except Exception:
            pass


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        Style.appliquer_fenetre(self, "surface")
        panel = wx.Panel(self, -1, name="test1")
        Style.appliquer_fenetre(panel, "surface")
        self.myOlv = CTRL(panel, IDfamille=84)
        self.myOlv.MAJ()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.myOlv, 1, wx.ALL | wx.EXPAND, Style.espace(2))
        panel.SetSizer(sizer)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.SetSize((Style.px(1100), Style.px(600)))
        self.Layout()
        self.CenterOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
