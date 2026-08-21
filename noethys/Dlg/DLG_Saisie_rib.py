#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-12 Ivan LUCAS
# Licence:          Licence GNU GPL
#------------------------------------------------------------------------

import string

import wx

import GestionDB
from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_BadgeRepens
from Ctrl import CTRL_FenetreRepens
from Ctrl import CTRL_Saisie_adresse
from Ctrl import CTRL_Ultrachoice
from Utils import UTILS_Prelevements
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


if 'phoenix' in wx.PlatformInfo:
    validator = wx.Validator
    IsSilent = wx.Validator.IsSilent
else:
    validator = wx.PyValidator
    IsSilent = wx.Validator_IsSilent


class MyValidator(validator):
    def __init__(self):
        validator.__init__(self)
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return MyValidator()

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        for x in val:
            if x not in string.digits:
                return False
        return True

    def OnChar(self, event):
        key = event.GetKeyCode()
        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return
        if chr(key) in string.digits or chr(key) in string.ascii_letters:
            event.Skip()
            return
        if not IsSilent():
            wx.Bell()

    def TransferToWindow(self):
        return True

    def TransferFromWindow(self):
        return True


class CTRL_Banque(CTRL_Ultrachoice.CTRL):
    def __init__(self, parent, donnees=None):
        if donnees is None:
            donnees = []
        CTRL_Ultrachoice.CTRL.__init__(self, parent, donnees)
        self.parent = parent
        Style.appliquer_saisie(self)
        self.MAJ()

    def MAJ(self):
        listeDonnees = self.GetListeDonnees()
        self.Enable(bool(listeDonnees))
        self.SetDonnees(listeDonnees)

    def GetListeDonnees(self):
        db = GestionDB.DB()
        req = """SELECT IDbanque, nom, rue_resid, cp_resid, ville_resid
        FROM banques
        ORDER BY nom;"""
        db.ExecuterReq(req)
        listeDonnees = db.ResultatReq()
        db.Close()
        listeItems = []
        self.dictDonnees = {}
        for index, (IDbanque, nom, rue_resid, cp_resid, ville_resid) in enumerate(listeDonnees):
            rue_resid = rue_resid or ""
            cp_resid = cp_resid or ""
            ville_resid = ville_resid or ""
            self.dictDonnees[index] = {"ID": IDbanque, "nom": nom}
            listeItems.append({
                "label": nom,
                "description": u"%s %s %s" % (rue_resid, cp_resid, ville_resid),
            })
        return listeItems

    def SetID(self, ID=0):
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID:
                self.SetSelection2(index)

    def GetID(self):
        index = self.GetSelection2()
        if index == -1 or index not in self.dictDonnees:
            return None
        return self.dictDonnees[index]["ID"]


class CTRL_Titulaire(wx.Choice):
    def __init__(self, parent, IDfamille=None):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.IDfamille = IDfamille
        Style.appliquer_saisie(self)
        self.MAJ()
        if self.GetCount() > 0:
            self.Select(0)

    def MAJ(self):
        listeItems = self.GetListeDonnees()
        self.Enable(bool(listeItems))
        self.SetItems(listeItems)

    def GetListeDonnees(self):
        if self.IDfamille is None:
            return []
        DB = GestionDB.DB()
        req = """SELECT individus.IDindividu, nom, prenom
        FROM rattachements
        LEFT JOIN individus ON individus.IDindividu = rattachements.IDindividu
        WHERE IDfamille=%d AND IDcategorie=1
        GROUP BY individus.IDindividu
        ORDER BY nom, prenom;""" % self.IDfamille
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()

        listeItems = [u""]
        self.dictDonnees = {0: {"ID": 0, "nom": _(u"Inconnue")}}
        for index, (IDindividu, nom, prenom) in enumerate(listeDonnees, start=1):
            label = u"%s %s" % (prenom or u"", nom or u"")
            self.dictDonnees[index] = {"ID": IDindividu, "nom": label.strip()}
            listeItems.append(label.strip())
        return listeItems

    def SetID(self, ID=0):
        if ID is None:
            self.SetSelection(0)
            return
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID:
                self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index in (-1, 0):
            return None
        return self.dictDonnees[index]["ID"]


class Dialog(CTRL_FenetreRepens.Dialog):
    """Saisie bancaire sur le shell commun Repens Design."""

    def __init__(self, parent, IDfamille=None):
        self.parent = parent
        self.IDfamille = IDfamille
        titre = _(u"Saisie du RIB")
        intro = _(u"Renseignez les coordonnées bancaires et le titulaire du compte utilisé pour le prélèvement.")
        CTRL_FenetreRepens.Dialog.__init__(
            self,
            parent,
            titre=titre,
            intro=intro,
            nomImage="Images/32x32/Prelevement.png",
            taille=(820, 680),
            taille_min=(680, 540),
        )

        self._ConstruireCoordonnees()
        self._ConstruireTitulaire()
        self._ConstruireObservations()
        self._ConstruireActions()
        self._ConfigurerTooltips()
        self._LierEvenements()

        self.Importation()
        self.OnSaisieRIB(None)
        self.OnRadioTitulaire(None)
        self.Finaliser()

    def _Label(self, parent, texte, emphase=False, role_fond="surface_container_low"):
        ctrl = wx.StaticText(parent, -1, texte)
        Style.appliquer_texte(
            ctrl,
            role="body_emphasis" if emphase else "body",
            role_texte="on_surface" if emphase else "on_surface_variant",
            role_fond=role_fond,
        )
        return ctrl

    def _Champ(self, parent, valeur=u"", style=0, validator=None, largeur=80):
        kwds = {"style": style}
        if validator is not None:
            kwds["validator"] = validator
        ctrl = wx.TextCtrl(parent, -1, valeur, **kwds)
        Style.appliquer_saisie(ctrl)
        ctrl.SetMinSize((Style.px(largeur), Style.cible_action("compact")))
        return ctrl

    def _ConstruireCoordonnees(self):
        self.section_rib = self.AjouterSection(
            _(u"Coordonnées bancaires"),
            _(u"Le statut est contrôlé automatiquement pendant la saisie."),
            proportion=0,
        )
        parent = self.section_rib.GetContenu()

        self.label_cle_iban = self._Label(parent, _(u"Clé IBAN"))
        self.label_etab = self._Label(parent, _(u"Établissement"))
        self.label_guichet = self._Label(parent, _(u"Guichet"))
        self.label_numero = self._Label(parent, _(u"Compte"))
        self.label_cle_rib = self._Label(parent, _(u"Clé RIB"))

        self.ctrl_cle_iban = self._Champ(parent, _(u"FR76"), wx.TE_CENTRE, largeur=68)
        self.ctrl_code_etab = self._Champ(parent, u"", wx.TE_CENTRE, MyValidator(), 78)
        self.ctrl_code_guichet = self._Champ(parent, u"", wx.TE_CENTRE, MyValidator(), 78)
        self.ctrl_numero = self._Champ(parent, u"", wx.TE_CENTRE, MyValidator(), 132)
        self.ctrl_cle_rib = self._Champ(parent, u"", wx.TE_CENTRE, MyValidator(), 64)
        self.ctrl_controle = CTRL_BadgeRepens.CTRL(parent, _(u"À vérifier"), role="attention")

        ligne_champs = wx.BoxSizer(wx.HORIZONTAL)
        for label, ctrl in (
            (self.label_cle_iban, self.ctrl_cle_iban),
            (self.label_etab, self.ctrl_code_etab),
            (self.label_guichet, self.ctrl_code_guichet),
            (self.label_numero, self.ctrl_numero),
            (self.label_cle_rib, self.ctrl_cle_rib),
        ):
            colonne = wx.BoxSizer(wx.VERTICAL)
            colonne.Add(label, 0, wx.BOTTOM, Style.espace(1))
            colonne.Add(ctrl, 0, wx.EXPAND)
            ligne_champs.Add(colonne, 0, wx.RIGHT, Style.espace(2))
        ligne_champs.AddStretchSpacer(1)
        ligne_champs.Add(self.ctrl_controle, 0, wx.ALIGN_CENTER_VERTICAL)
        self.section_rib.GetSizerContenu().Add(ligne_champs, 0, wx.EXPAND | wx.BOTTOM, Style.espace(3))

        self.label_banque = self._Label(parent, _(u"Établissement bancaire"), emphase=True)
        self.ctrl_banque = CTRL_Banque(parent)
        self.bouton_banques = CTRL_ActionRepens.CTRL(
            parent,
            label=_(u"Gérer"),
            icone="settings",
            tooltip=_(u"Accéder à la gestion des établissements bancaires"),
        )
        ligne_banque = wx.BoxSizer(wx.HORIZONTAL)
        ligne_banque.Add(self.label_banque, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, Style.espace(2))
        ligne_banque.Add(self.ctrl_banque, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, Style.espace(1))
        ligne_banque.Add(self.bouton_banques, 0, wx.ALIGN_CENTER_VERTICAL)
        self.section_rib.GetSizerContenu().Add(ligne_banque, 0, wx.EXPAND)

    def _ConstruireTitulaire(self):
        self.section_titulaire = self.AjouterSection(
            _(u"Titulaire du compte bancaire"),
            _(u"Choisissez un représentant de la famille ou saisissez un titulaire différent."),
            proportion=0,
        )
        parent = self.section_titulaire.GetContenu()

        self.radio_membre = wx.RadioButton(parent, -1, _(u"Membre de la famille"), style=wx.RB_GROUP)
        self.ctrl_membre = CTRL_Titulaire(parent, IDfamille=self.IDfamille)
        self.radio_individu = wx.RadioButton(parent, -1, _(u"Autre titulaire"))
        for ctrl in (self.radio_membre, self.radio_individu):
            Style.appliquer_texte(
                ctrl,
                role="body_emphasis",
                role_texte="on_surface",
                role_fond="surface_container_low",
            )

        ligne_membre = wx.BoxSizer(wx.HORIZONTAL)
        ligne_membre.Add(self.radio_membre, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, Style.espace(2))
        ligne_membre.Add(self.ctrl_membre, 1, wx.ALIGN_CENTER_VERTICAL)
        self.section_titulaire.GetSizerContenu().Add(ligne_membre, 0, wx.EXPAND | wx.BOTTOM, Style.espace(2))
        self.section_titulaire.GetSizerContenu().Add(self.radio_individu, 0, wx.BOTTOM, Style.espace(2))

        self.label_individu_nom = self._Label(parent, _(u"Nom"))
        self.ctrl_individu_nom = self._Champ(parent, largeur=240)
        self.label_individu_rue = self._Label(parent, _(u"Rue"))
        self.ctrl_individu_rue = self._Champ(parent, largeur=300)
        self.label_individu_ville = self._Label(parent, _(u"Code postal / Ville"))
        self.ctrl_individu_ville = CTRL_Saisie_adresse.Adresse(parent)
        try:
            Style.appliquer_fenetre(self.ctrl_individu_ville, "surface_container_low")
        except Exception:
            pass

        for label, ctrl in (
            (self.label_individu_nom, self.ctrl_individu_nom),
            (self.label_individu_rue, self.ctrl_individu_rue),
            (self.label_individu_ville, self.ctrl_individu_ville),
        ):
            ligne = wx.BoxSizer(wx.HORIZONTAL)
            ligne.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, Style.espace(2))
            ligne.Add(ctrl, 1, wx.ALIGN_CENTER_VERTICAL)
            self.section_titulaire.GetSizerContenu().Add(ligne, 0, wx.EXPAND | wx.BOTTOM, Style.espace(1))

    def _ConstruireObservations(self):
        self.section_memo = self.AjouterSection(
            _(u"Observations"),
            _(u"Informations internes facultatives liées à ces coordonnées bancaires."),
            proportion=1,
        )
        parent = self.section_memo.GetContenu()
        self.ctrl_memo = wx.TextCtrl(parent, -1, u"", style=wx.TE_MULTILINE)
        Style.appliquer_saisie(self.ctrl_memo)
        self.ctrl_memo.SetMinSize((-1, Style.px(90)))
        self.section_memo.GetSizerContenu().Add(self.ctrl_memo, 1, wx.EXPAND)

    def _ConstruireActions(self):
        self.bouton_aide = self.AjouterAction(
            _(u"Aide"),
            callback=self.OnBoutonAide,
            icone="help",
            alignement="gauche",
        )
        self.bouton_annuler = self.AjouterAction(
            _(u"Annuler"),
            callback=self.OnBoutonAnnuler,
            icone="dismiss",
            alignement="droite",
        )
        self.bouton_ok = self.AjouterAction(
            _(u"Valider"),
            callback=self.OnBoutonOk,
            icone="check",
            variante="primaire",
            alignement="droite",
        )

    def _ConfigurerTooltips(self):
        self.ctrl_code_etab.SetToolTip(wx.ToolTip(_(u"Saisissez le code établissement")))
        self.ctrl_code_guichet.SetToolTip(wx.ToolTip(_(u"Saisissez le code guichet")))
        self.ctrl_numero.SetToolTip(wx.ToolTip(_(u"Saisissez le numéro de compte")))
        self.ctrl_cle_rib.SetToolTip(wx.ToolTip(_(u"Saisissez la clé RIB")))
        self.ctrl_controle.SetToolTip(wx.ToolTip(_(u"Validité des coordonnées bancaires")))
        self.ctrl_banque.SetToolTip(wx.ToolTip(_(u"Sélectionnez l'établissement du compte")))
        self.radio_membre.SetToolTip(wx.ToolTip(_(u"Sélectionner un membre de la famille")))
        self.ctrl_membre.SetToolTip(wx.ToolTip(_(u"Sélectionnez le titulaire du compte")))
        self.radio_individu.SetToolTip(wx.ToolTip(_(u"Saisir manuellement un autre titulaire")))
        self.ctrl_individu_nom.SetToolTip(wx.ToolTip(_(u"Saisissez le nom du titulaire")))
        self.ctrl_individu_rue.SetToolTip(wx.ToolTip(_(u"Saisissez la rue du titulaire")))
        self.ctrl_memo.SetToolTip(wx.ToolTip(_(u"Saisissez des observations")))

    def _LierEvenements(self):
        for ctrl in (
            self.ctrl_cle_iban,
            self.ctrl_code_etab,
            self.ctrl_code_guichet,
            self.ctrl_numero,
            self.ctrl_cle_rib,
        ):
            ctrl.Bind(wx.EVT_TEXT, self.OnSaisieRIB)
        self.bouton_banques.Bind(wx.EVT_BUTTON, self.OnBoutonBanques)
        self.radio_membre.Bind(wx.EVT_RADIOBUTTON, self.OnRadioTitulaire)
        self.radio_individu.Bind(wx.EVT_RADIOBUTTON, self.OnRadioTitulaire)

    def OnSaisieRIB(self, event):
        self.ControleRIB()
        if event is not None:
            event.Skip()

    def ControleRIB(self):
        cle_iban = self.ctrl_cle_iban.GetValue()
        etab = self.ctrl_code_etab.GetValue()
        guichet = self.ctrl_code_guichet.GetValue()
        numero = self.ctrl_numero.GetValue()
        cle = self.ctrl_cle_rib.GetValue()
        rib = u"%s%s%s%s" % (etab, guichet, numero, cle)
        UTILS_Prelevements.AlgoControleRIB(rib)

        iban = ""
        if cle_iban != "" and rib != "":
            iban = cle_iban + rib
            if UTILS_Prelevements.ControleIBAN(iban) is False:
                iban = ""
        if iban != "":
            self.ctrl_controle.SetEtat(_(u"Coordonnées valides"), "succes")
            return True
        self.ctrl_controle.SetEtat(_(u"À vérifier"), "attention")
        return False

    def OnBoutonBanques(self, event):
        IDbanque = self.ctrl_banque.GetID()
        from Dlg import DLG_Banques
        dlg = DLG_Banques.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.ctrl_banque.MAJ()
        self.ctrl_banque.SetID(IDbanque)

    def OnRadioTitulaire(self, event):
        etat = self.radio_membre.GetValue()
        self.ctrl_membre.Enable(etat)
        self.ctrl_individu_nom.Enable(not etat)
        self.ctrl_individu_rue.Enable(not etat)
        self.ctrl_individu_ville.Enable(not etat)

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Rglements1")

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def Importation(self):
        if self.IDfamille is None:
            return
        DB = GestionDB.DB()
        req = """SELECT
        prelevement_etab, prelevement_guichet, prelevement_numero, prelevement_cle, prelevement_banque,
        prelevement_individu, prelevement_nom, prelevement_rue, prelevement_cp, prelevement_ville,
        prelevement_cle_iban, prelevement_iban, prelevement_bic,
        prelevement_reference_mandat, prelevement_date_mandat, prelevement_memo
        FROM familles
        WHERE IDfamille=%d;""" % self.IDfamille
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0:
            return
        etab, guichet, numero, cle, IDbanque, IDindividu, nom, rue, cp, ville, cle_iban, iban, bic, reference_mandat, date_mandat, memo = listeDonnees[0]

        etab = etab or ""
        guichet = guichet or ""
        numero = numero or ""
        cle = cle or ""
        nom = nom or ""
        rue = rue or ""
        cp = cp or ""
        ville = ville or ""
        cle_iban = cle_iban or "FR76"
        memo = memo or ""

        self.ctrl_code_etab.SetValue(etab)
        self.ctrl_code_guichet.SetValue(guichet)
        self.ctrl_numero.SetValue(numero)
        self.ctrl_cle_rib.SetValue(cle)
        self.ctrl_banque.SetID(IDbanque)
        self.ctrl_cle_iban.SetValue(cle_iban)
        self.ControleRIB()

        if IDindividu is not None:
            self.radio_membre.SetValue(True)
            self.ctrl_membre.SetID(IDindividu)
        else:
            self.radio_individu.SetValue(True)
            self.ctrl_individu_nom.SetValue(nom)
            self.ctrl_individu_rue.SetValue(rue)
            self.ctrl_individu_ville.SetValueCP(cp)
            self.ctrl_individu_ville.SetValueVille(ville)

        self.ctrl_memo.SetValue(memo)

    def OnBoutonOk(self, event):
        etab = self.ctrl_code_etab.GetValue()
        guichet = self.ctrl_code_guichet.GetValue()
        numero = self.ctrl_numero.GetValue()
        cle = self.ctrl_cle_rib.GetValue()
        IDbanque = self.ctrl_banque.GetID()
        IDindividu = self.ctrl_membre.GetID()
        nom = self.ctrl_individu_nom.GetValue()
        rue = self.ctrl_individu_rue.GetValue()
        cp = self.ctrl_individu_ville.GetValueCP()
        ville = self.ctrl_individu_ville.GetValueVille()
        cle_iban = self.ctrl_cle_iban.GetValue()
        memo = self.ctrl_memo.GetValue()

        if self.radio_membre.GetValue() is True:
            nom = None
            rue = None
            cp = None
            ville = None
        else:
            IDindividu = None

        if self.ControleRIB() is False:
            dlg = wx.MessageDialog(
                self,
                _(u"Il est impossible d'activer le prélèvement :\nLes coordonnées bancaires ne sont pas valides !"),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_code_etab.SetFocus()
            return

        if IDbanque is None:
            dlg = wx.MessageDialog(
                self,
                _(u"Il est impossible d'activer le prélèvement :\nVous n'avez sélectionné aucun établissement bancaire !"),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_banque.SetFocus()
            return

        if self.radio_membre.GetValue() is True:
            if IDindividu is None:
                dlg = wx.MessageDialog(
                    self,
                    _(u"Il est impossible d'activer le prélèvement :\nVous n'avez pas sélectionné de titulaire du compte bancaire !"),
                    _(u"Erreur de saisie"),
                    wx.OK | wx.ICON_EXCLAMATION,
                )
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_membre.SetFocus()
                return
        elif nom == "" or rue == "" or cp in ("", None) or ville in ("", None):
            dlg = wx.MessageDialog(
                self,
                _(u"Il est impossible d'activer le prélèvement :\nVous n'avez pas renseigné le titulaire du compte bancaire !"),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_individu_nom.SetFocus()
            return

        DB = GestionDB.DB()
        listeDonnees = [
            ("prelevement_etab", etab),
            ("prelevement_guichet", guichet),
            ("prelevement_numero", numero),
            ("prelevement_cle", cle),
            ("prelevement_banque", IDbanque),
            ("prelevement_individu", IDindividu),
            ("prelevement_nom", nom),
            ("prelevement_rue", rue),
            ("prelevement_cp", cp),
            ("prelevement_ville", ville),
            ("prelevement_cle_iban", cle_iban),
            ("prelevement_memo", memo),
        ]
        DB.ReqMAJ("familles", listeDonnees, "IDfamille", self.IDfamille)
        DB.Close()
        self.EndModal(wx.ID_OK)


if __name__ == u"__main__":
    app = wx.App(0)
    dialog_1 = Dialog(None, IDfamille=14)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
