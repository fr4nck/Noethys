#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import GestionDB
import wx
import six


def GetNom():
    DB = GestionDB.DB()
    req = """SELECT nom, rue, cp, ville
    FROM organisateur WHERE IDorganisateur=1;"""
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    if len(listeDonnees) == 0 : return ""
    nom = listeDonnees[0][0]
    if nom == None :
        nom = ""
    return nom

def RecadreImg(img=None, tailleImage=(40, 40), fondBlanc=True):
    # Recadre l'image en fonction de la taille du staticBitmap.
    # Le ratio est conservé et les petits logos ne sont pas agrandis.
    tailleMaxi = max(tailleImage)
    largeur, hauteur = img.GetSize()
    if max(largeur, hauteur) > tailleMaxi :
        if largeur > hauteur :
            hauteur = int(hauteur * tailleMaxi / largeur)
            largeur = int(tailleMaxi)
        else:
            largeur = int(largeur * tailleMaxi / hauteur)
            hauteur = int(tailleMaxi)
    else:
        largeur = int(largeur)
        hauteur = int(hauteur)
    img.Rescale(width=largeur, height=hauteur, quality=wx.IMAGE_QUALITY_HIGH)
    position = (int((tailleImage[0] - largeur) / 2), int((tailleImage[1] - hauteur) / 2))

    # Pour l'accueil, conserver le canal alpha évite de cuire un fond blanc
    # dans le bitmap, source de halos sur un fond non blanc.
    if fondBlanc or not img.HasAlpha():
        img.Resize(tailleImage, position, 255, 255, 255)
        return img

    canvas = wx.Image(tailleImage[0], tailleImage[1])
    canvas.InitAlpha()
    canvas.SetRGB(wx.Rect(0, 0, tailleImage[0], tailleImage[1]), 255, 255, 255)
    alpha = bytearray(tailleImage[0] * tailleImage[1])
    canvas.SetAlpha(bytes(alpha))
    canvas.Paste(img, position[0], position[1])
    return canvas


def EvaluerLisibiliteLogo(tailleOriginale=(0, 0), tailleLogo=(80, 80), seuilDimension=24):
    """Evalue le risque de perte de lisibilite apres reduction du logo.

    Ce seuil ne pretend pas reconnaitre le texte dans l'image : il signale
    simplement les reductions ou la plus petite dimension utile devient trop
    faible pour des textes fins et des details serres.
    """
    largeur, hauteur = tailleOriginale
    if largeur <= 0 or hauteur <= 0:
        return "inconnue"
    facteur = min(1.0, float(tailleLogo[0]) / largeur, float(tailleLogo[1]) / hauteur)
    largeur_finale = max(1, int(round(largeur * facteur)))
    hauteur_finale = max(1, int(round(hauteur * facteur)))
    dimension_min = min(largeur_finale, hauteur_finale)
    if dimension_min < seuilDimension:
        return "trop_petit"
    if dimension_min < seuilDimension * 2:
        return "limite"
    return "exploitable"

def GetDonnees(tailleLogo=(40, 40), fondLogoBlanc=True) :
    DB = GestionDB.DB()
    req = """SELECT nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape, logo, logo_update
    FROM organisateur WHERE IDorganisateur=1;"""
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    if listeDonnees:
        nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape, logo, logo_update = listeDonnees[0]
    else:
        nom = rue = cp = ville = tel = fax = mail = site = num_agrement = num_siret = code_ape = u""
        logo, logo_update = None, None
    if nom == None : nom = u""
    if rue == None : rue = u""
    if cp == None : cp = u""
    if ville == None : ville = u""
    if tel == None : tel = u""
    if fax == None : fax = u""
    if mail == None : mail = u""
    if site == None : site = u""
    if num_agrement == None : num_agrement = u""
    if num_siret == None : num_siret = u""
    if code_ape == None : code_ape = u""
    if logo != None :
        io = six.BytesIO(logo)
        if 'phoenix' in wx.PlatformInfo:
            img = wx.Image(io, wx.BITMAP_TYPE_ANY)
        else :
            img = wx.ImageFromStream(io, wx.BITMAP_TYPE_ANY)
        img = RecadreImg(img, tailleLogo, fondBlanc=fondLogoBlanc)
        logo = img.ConvertToBitmap()
    dictDonnees = {
        "nom":nom, "rue":rue, "cp":cp, "ville":ville, "tel":tel, "fax":fax, "mail":mail, "site":site, 
        "num_agrement":num_agrement, "num_siret":num_siret, "code_ape":code_ape, "logo":logo, "logo_update":logo_update,
        }
    return dictDonnees




if __name__ == '__main__':
    print(GetNom())