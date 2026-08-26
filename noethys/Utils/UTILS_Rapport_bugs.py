#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-19 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
import wx
import six
from Ctrl import CTRL_Bouton_image
import sys
import os
import codecs
import platform
import traceback
import datetime
import GestionDB
import webbrowser
import wx.lib.dialogs
from Utils import UTILS_Config
from Utils import UTILS_Customize
from Utils import UTILS_Fichiers

URL_SUIVI_BUGS = "https://github.com/fr4nck/Noethys/issues"
PARAM_DESTINATAIRE = "adresse_rapport_bugs"
DESTINATAIRE_DEFAUT = "multimedia@pelemele.org"


def _GetRepLogs():
    """Retourne le répertoire local des journaux Vanilla sans jamais bloquer Noethys."""
    try:
        rep = UTILS_Fichiers.GetRepUtilisateur("Logs")
        if not os.path.isdir(rep):
            os.makedirs(rep)
        return rep
    except Exception:
        return None


def _EcrireCrashLocal(texte):
    """Archive chaque crash localement. Une erreur d'écriture ne doit jamais masquer le crash initial."""
    try:
        rep = _GetRepLogs()
        if rep is None:
            return None
        chemin = os.path.join(rep, "vanilla_crash.log")
        with codecs.open(chemin, "a", "utf-8") as fichier:
            fichier.write(u"\n%s\n" % (u"=" * 100))
            fichier.write(texte)
            if not texte.endswith(u"\n"):
                fichier.write(u"\n")
        return chemin
    except Exception:
        return None


def Activer_rapport_erreurs(version=""):
    def my_excepthook(exctype, value, tb):
        dateDuJour = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        systeme = u"%s %s %s %s" % (sys.platform, platform.system(), platform.release(), platform.machine())
        infos = u"## %s | %s | wxPython %s | %s ##" % (dateDuJour, version, wx.version(), systeme)
        bug = ''.join(traceback.format_exception(exctype, value, tb))

        print(bug)

        try:
            if six.PY2:
                bug = bug.decode("utf8")
        except Exception:
            pass

        texte = u"%s\n%s" % (infos, bug)
        _EcrireCrashLocal(texte)

        try:
            if UTILS_Config.GetParametre("rapports_bugs", True) == False:
                return
        except Exception:
            pass

        try:
            dlg = DLG_Rapport(None, texte)
            dlg.ShowModal()
            dlg.Destroy()
        except Exception:
            pass

    sys.excepthook = my_excepthook


class DLG_Rapport(wx.Dialog):
    def __init__(self, parent, texte=""):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.parent = parent

        self.ctrl_image = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(Chemins.GetStaticPath(u"Images/48x48/Erreur.png"), wx.BITMAP_TYPE_ANY))
        self.label_ligne_1 = wx.StaticText(self, wx.ID_ANY, _(u"Noethys a rencontré un problème !"))
        self.label_ligne_2 = wx.StaticText(self, wx.ID_ANY, _(u"Le rapport d'erreur ci-dessous a été enregistré localement.\nVous pouvez l'envoyer à l'adresse de maintenance de votre choix."))
        self.ctrl_rapport = wx.TextCtrl(self, wx.ID_ANY, texte, style=wx.TE_MULTILINE | wx.TE_READONLY)

        self.bouton_envoyer = CTRL_Bouton_image.CTRL(self, texte=_(u"Envoyer le rapport"), cheminImage="Images/32x32/Emails_exp.png")
        self.bouton_forum = CTRL_Bouton_image.CTRL(self, texte=_(u"Accéder au suivi"), cheminImage="Images/32x32/Forum.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, texte=_(u"Fermer"), cheminImage="Images/32x32/Fermer.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonEnvoyer, self.bouton_envoyer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonForum, self.bouton_forum)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFermer, self.bouton_fermer)

        try:
            clipdata = wx.TextDataObject()
            clipdata.SetText(texte)
            wx.TheClipboard.Open()
            wx.TheClipboard.SetData(clipdata)
            wx.TheClipboard.Close()
        except Exception:
            pass

        self.bouton_fermer.SetFocus()

    def __set_properties(self):
        self.SetTitle(_(u"Rapport d'erreurs"))
        self.label_ligne_1.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.ctrl_rapport.SetToolTip(wx.ToolTip(_(u"Ce rapport d'erreur a été copié dans le presse-papiers et enregistré dans Portable/Logs lorsqu'un mode portable est utilisé")))
        self.bouton_envoyer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour envoyer ce rapport d'erreur par Email")))
        self.bouton_forum.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour accéder au suivi des bugs de cette version maintenue de Noethys")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour fermer")))
        self.SetMinSize((650, 450))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(2, 1, 10, 10)
        grid_sizer_bas = wx.FlexGridSizer(1, 5, 10, 10)
        grid_sizer_haut = wx.FlexGridSizer(1, 2, 10, 10)
        grid_sizer_droit = wx.FlexGridSizer(3, 1, 10, 10)
        grid_sizer_haut.Add(self.ctrl_image, 0, wx.ALL, 10)
        grid_sizer_droit.Add(self.label_ligne_1, 0, 0, 0)
        grid_sizer_droit.Add(self.label_ligne_2, 0, 0, 0)
        grid_sizer_droit.Add(self.ctrl_rapport, 0, wx.EXPAND, 0)
        grid_sizer_droit.AddGrowableRow(2)
        grid_sizer_droit.AddGrowableCol(0)
        grid_sizer_haut.Add(grid_sizer_droit, 1, wx.RIGHT | wx.TOP | wx.EXPAND, 10)
        grid_sizer_haut.AddGrowableRow(0)
        grid_sizer_haut.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_haut, 1, wx.EXPAND, 0)
        grid_sizer_bas.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_bas.Add(self.bouton_envoyer, 0, 0, 0)
        grid_sizer_bas.Add(self.bouton_forum, 0, 0, 0)
        grid_sizer_bas.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_bas.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_bas, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonFermer(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonEnvoyer(self, event):
        texteRapport = self.ctrl_rapport.GetValue()
        dlg = DLG_Envoi(self, texteRapport)
        reponse = dlg.ShowModal()
        commentaires = dlg.GetCommentaires()
        joindre_journal = dlg.GetJoindreJournal()
        destinataire = dlg.GetDestinataire()
        dlg.Destroy()

        if reponse == wx.ID_OK:
            self.Envoyer_mail(commentaires, joindre_journal, destinataire)

    def OnBoutonForum(self, event):
        webbrowser.open(URL_SUIVI_BUGS)

    def GetAdresseExpDefaut(self):
        dictAdresse = {}
        DB = GestionDB.DB()
        req = """SELECT IDadresse, moteur, adresse, motdepasse, smtp, port, defaut, connexionAuthentifiee, startTLS, utilisateur, parametres
        FROM adresses_mail WHERE defaut=1 ORDER BY adresse; """
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0:
            return None
        IDadresse, moteur, adresse, motdepasse, smtp, port, defaut, connexionAuthentifiee, startTLS, utilisateur, parametres = listeDonnees[0]
        dictAdresse = {"adresse": adresse, "moteur": moteur, "motdepasse": motdepasse, "smtp": smtp, "port": port, "auth": connexionAuthentifiee, "startTLS": startTLS, "utilisateur": utilisateur, "parametres": parametres}
        return dictAdresse

    def Envoyer_mail(self, commentaires="", joindre_journal=False, destinataire=""):
        from Utils import UTILS_Envoi_email

        if destinataire is None:
            destinataire = ""
        destinataire = destinataire.strip()
        if len(destinataire) == 0:
            destinataire = UTILS_Config.GetParametre(PARAM_DESTINATAIRE, DESTINATAIRE_DEFAUT) or DESTINATAIRE_DEFAUT
        if len(destinataire) == 0 or "@" not in destinataire:
            dlg = wx.MessageDialog(self, _(u"Veuillez renseigner une adresse de réception valide pour le rapport d'erreur."), _(u"Envoi impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        dictExp = self.GetAdresseExpDefaut()
        if dictExp == None:
            dlg = wx.MessageDialog(self, _(u"Vous devez d'abord saisir une adresse d'expéditeur depuis le menu Paramétrage > Adresses d'expédition d'Emails."), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        moteur = dictExp["moteur"]
        adresseExpediteur = dictExp["adresse"]
        serveur = dictExp["smtp"]
        port = dictExp["port"]
        startTLS = dictExp["startTLS"]
        motdepasse = dictExp["motdepasse"]
        utilisateur = dictExp["utilisateur"]
        parametres = dictExp["parametres"]

        if adresseExpediteur == None:
            dlg = wx.MessageDialog(self, _(u"L'adresse d'expédition ne semble pas valide. Veuillez la vérifier."), _(u"Envoi impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        fichiers = []
        if joindre_journal == True:
            customize = UTILS_Customize.Customize()
            nom_journal = UTILS_Fichiers.GetRepUtilisateur(customize.GetValeur("journal", "nom", "journal.log"))
            if os.path.isfile(nom_journal):
                fichiers.append(nom_journal)
            nom_crash = os.path.join(_GetRepLogs() or "", "vanilla_crash.log")
            if os.path.isfile(nom_crash):
                fichiers.append(nom_crash)

        IDrapport = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        texteRapport = self.ctrl_rapport.GetValue().replace("\n", "<br/>")
        if len(commentaires) == 0:
            commentaires = _(u"Aucun")
        texte_html = _(u"<u>Rapport de bug %s :</u><br/><br/>%s<br/><u>Commentaires :</u><br/><br/>%s") % (IDrapport, texteRapport, commentaires)

        sujet = _(u"Rapport de bug Noethys n°%s") % IDrapport
        message = UTILS_Envoi_email.Message(destinataires=[destinataire], sujet=sujet, texte_html=texte_html, fichiers=fichiers)

        try:
            messagerie = UTILS_Envoi_email.Messagerie(backend=moteur, hote=serveur, port=port, utilisateur=utilisateur, motdepasse=motdepasse, email_exp=adresseExpediteur, use_tls=startTLS, parametres=parametres)
            messagerie.Connecter()
            messagerie.Envoyer(message)
            messagerie.Fermer()
        except Exception as err:
            dlg = wx.MessageDialog(self, _(u"Le message n'a pas pu être envoyé. Le rapport reste disponible dans le dossier Logs.\n\nErreur : %s !") % err, _(u"Envoi impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        dlg = wx.MessageDialog(self, _(u"Le rapport d'erreur a été envoyé avec succès à %s.") % destinataire, _(u"Rapport envoyé"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        return True


class DLG_Envoi(wx.Dialog):
    def __init__(self, parent, texteRapport=u""):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.parent = parent
        self.texteRapport = texteRapport

        self.label_ligne_1 = wx.StaticText(self, wx.ID_ANY, _(u"Le rapport est prêt à être envoyé..."))
        self.label_ligne_2 = wx.StaticText(self, wx.ID_ANY, _(u"Choisissez l'adresse de réception, puis ajoutez si besoin un commentaire avant l'envoi."))
        self.label_destinataire = wx.StaticText(self, wx.ID_ANY, _(u"Adresse de réception :"))
        self.ctrl_destinataire = wx.TextCtrl(self, wx.ID_ANY, UTILS_Config.GetParametre(PARAM_DESTINATAIRE, DESTINATAIRE_DEFAUT) or DESTINATAIRE_DEFAUT)
        self.ctrl_commentaires = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_MULTILINE)
        self.check_journal = wx.CheckBox(self, -1, _(u"Joindre les journaux d'erreurs (Recommandé)"))

        self.bouton_apercu = CTRL_Bouton_image.CTRL(self, texte=_(u"Aperçu"), cheminImage="Images/32x32/Apercu.png")
        self.bouton_envoyer = CTRL_Bouton_image.CTRL(self, texte=_(u"Envoyer l'Email"), cheminImage="Images/32x32/Emails_exp.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_(u"Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonApercu, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEnvoyer, self.bouton_envoyer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

    def __set_properties(self):
        self.SetTitle(_(u"Envoyer le rapport d'erreur"))
        self.label_ligne_1.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.ctrl_destinataire.SetToolTip(wx.ToolTip(_(u"Adresse Email qui recevra les futurs crashreports. Elle sera mémorisée sur ce poste.")))
        self.ctrl_commentaires.SetToolTip(wx.ToolTip(_(u"Vous pouvez saisir des commentaires ici")))
        self.check_journal.SetToolTip(wx.ToolTip(_(u"Pour faciliter la résolution du bug, joignez les journaux locaux")))
        self.SetMinSize((600, 400))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(7, 1, 10, 10)
        grid_sizer_dest = wx.FlexGridSizer(1, 2, 10, 10)
        grid_sizer_boutons = wx.FlexGridSizer(1, 4, 10, 10)

        grid_sizer_base.Add(self.label_ligne_1, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        grid_sizer_base.Add(self.label_ligne_2, 0, wx.LEFT | wx.RIGHT, 10)
        grid_sizer_dest.Add(self.label_destinataire, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_dest.Add(self.ctrl_destinataire, 1, wx.EXPAND, 0)
        grid_sizer_dest.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_dest, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        grid_sizer_base.Add(self.ctrl_commentaires, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        grid_sizer_base.Add(self.check_journal, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        grid_sizer_boutons.Add(self.bouton_apercu, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_envoyer, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(3)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonApercu(self, event):
        commentaires = self.ctrl_commentaires.GetValue()
        if len(commentaires) == 0:
            commentaires = _(u"Aucun")
        message = _(u"Destinataire : %s\n\nRapport : \n\n%s\nCommentaires : \n\n%s") % (self.GetDestinataire(), self.texteRapport, commentaires)
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, message, _(u"Visualisation du contenu du message"))
        dlg.ShowModal()
        dlg.Destroy()

    def OnBoutonEnvoyer(self, event):
        destinataire = self.GetDestinataire()
        if len(destinataire) == 0 or "@" not in destinataire:
            dlg = wx.MessageDialog(self, _(u"Veuillez saisir une adresse de réception valide."), _(u"Adresse invalide"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        UTILS_Config.SetParametre(PARAM_DESTINATAIRE, destinataire)
        self.EndModal(wx.ID_OK)

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def GetCommentaires(self):
        return self.ctrl_commentaires.GetValue()

    def GetJoindreJournal(self):
        return self.check_journal.GetValue()

    def GetDestinataire(self):
        return self.ctrl_destinataire.GetValue().strip()


if __name__ == u"__main__":
    app = wx.App(0)
    dialog_1 = DLG_Rapport(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
