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
import os
import sys
import base64
import zipfile
import GestionDB
import subprocess
import shutil
import time
import re
import hashlib
import uuid
import io

import GestionDB
from Utils import UTILS_Fichiers
from Utils import UTILS_Config
from Utils import UTILS_Cryptage_fichier
from Utils import UTILS_Fichiers
from Utils import UTILS_Envoi_email
from Utils import UTILS_Customize

LISTE_CATEGORIES = [
    (_(u"Données de base"), "DATA"),
    (_(u"Photos individuelles"), "PHOTOS"),
    (_(u"Documents"), "DOCUMENTS"),
    ]

EXTENSIONS = {
    "decrypte" : "nod",
    "crypte" : "noc",
    }


def _SupprimerFichiersSauvegardeTemp(nom):
    """ Supprime les archives temporaires sans masquer l'erreur principale. """
    for extension in EXTENSIONS.values():
        fichier = UTILS_Fichiers.GetRepTemp(fichier=u"%s.%s" % (nom, extension))
        try:
            if os.path.isfile(fichier) == True:
                os.remove(fichier)
        except OSError:
            pass


def _SupprimerRepertoireTemp(repertoire):
    """ Supprime un répertoire temporaire sans masquer l'erreur principale. """
    try:
        if repertoire and os.path.isdir(repertoire):
            shutil.rmtree(repertoire)
    except OSError:
        pass


def _TexteErreurProcessus(valeur):
    """ Normalise la sortie des clients MySQL pour l'affichage des erreurs. """
    if isinstance(valeur, bytes):
        return valeur.decode("utf-8", errors="replace")
    return str(valeur)


_SQL_MANIFESTE_ENTETE = b"-- NOETHYS-SQL-MANIFEST-V1 "
_SQL_MANIFESTE_FIN = b"-- NOETHYS-SQL-MANIFEST-END-V1 "
_SQL_MANIFESTE_FIN_RE = re.compile(
    b"^-- NOETHYS-SQL-MANIFEST-END-V1 ([0-9a-f]{32}) ([0-9]+) ([0-9a-f]{64})\\n?$"
)
_TAILLE_BLOC_SQL = 1024 * 1024
_TAILLE_PREFIXE_INSTRUCTION_SQL = 16 * 1024
_IDENTIFIANT_SQL = r'(?:`(?:``|[^`])+`|"(?:""|[^"])+"|[A-Za-z0-9_$]+)'
_NOM_QUALIFIE_SQL = r"(?:(?:%s)\s*\.\s*)?(?P<nom>%s)" % (_IDENTIFIANT_SQL, _IDENTIFIANT_SQL)
_MODIFICATEURS_CREATE_SQL = (
    r"(?P<modificateurs>(?:(?:OR\s+REPLACE|TEMPORARY|ALGORITHM\s*=\s*\S+|"
    r"DEFINER\s*=\s*\S+(?:\s*@\s*\S+)?|SQL\s+SECURITY\s+\w+)\s+)*)"
)
_CREATE_OBJET_SQL_RE = re.compile(
    r"\bCREATE\s+%s(?P<type>TABLE|VIEW|TRIGGER|PROCEDURE|FUNCTION|EVENT)\s+"
    r"(?:IF\s+NOT\s+EXISTS\s+)?%s" % (_MODIFICATEURS_CREATE_SQL, _NOM_QUALIFIE_SQL),
    re.IGNORECASE,
)
_ECRITURE_TABLE_SQL_RE = re.compile(
    r"\b(?:INSERT(?:\s+(?:LOW_PRIORITY|DELAYED|HIGH_PRIORITY|IGNORE))*|"
    r"REPLACE(?:\s+(?:LOW_PRIORITY|DELAYED))*)\s+INTO\s+%s" % _NOM_QUALIFIE_SQL,
    re.IGNORECASE,
)


def _EncoderAscii(texte):
    if isinstance(texte, bytes):
        return texte
    return texte.encode("ascii")


def _LireFichierBinaire(fichier):
    with open(fichier, "rb") as flux:
        return flux.read()


def _AjouterManifesteIntegriteSQL(fichier):
    """ Enveloppe un dump sans changer son caractère exécutable par les anciens clients. """
    jeton = uuid.uuid4().hex
    jetonBytes = _EncoderAscii(jeton)
    fichierTemp = u"%s.noethys-manifest" % fichier
    empreinte = hashlib.sha256()
    taille = 0

    try:
        with open(fichier, "rb") as source, open(fichierTemp, "wb") as destination:
            destination.write(_SQL_MANIFESTE_ENTETE + jetonBytes + b"\n")
            while True:
                bloc = source.read(_TAILLE_BLOC_SQL)
                if not bloc:
                    break
                empreinte.update(bloc)
                taille += len(bloc)
                destination.write(bloc)

            # Cette ligne vide sépare toujours la charge originale du manifeste terminal.
            destination.write(b"\n")
            destination.write(
                _SQL_MANIFESTE_FIN
                + jetonBytes
                + b" "
                + _EncoderAscii(str(taille))
                + b" "
                + _EncoderAscii(empreinte.hexdigest())
                + b"\n"
            )

        os.remove(fichier)
        os.rename(fichierTemp, fichier)
    except Exception:
        try:
            if os.path.isfile(fichierTemp):
                os.remove(fichierTemp)
        except OSError:
            pass
        raise


def _ExtraireChargeSQL(contenu):
    """ Retourne (charge, avec_manifeste, erreur) et valide taille/empreinte si présentes. """
    if not contenu.startswith(_SQL_MANIFESTE_ENTETE):
        if re.search(b"(?m)^-- NOETHYS-SQL-MANIFEST-END-V1 ", contenu):
            return None, False, _(u"le manifeste terminal est présent sans son en-tête")
        return contenu, False, None

    finEntete = contenu.find(b"\n")
    if finEntete == -1:
        return None, True, _(u"l'en-tête du manifeste SQL est tronqué")

    jeton = contenu[len(_SQL_MANIFESTE_ENTETE):finEntete]
    if re.match(b"^[0-9a-f]{32}$", jeton) is None:
        return None, True, _(u"l'identifiant du manifeste SQL est invalide")

    debutFin = contenu.rfind(b"\n" + _SQL_MANIFESTE_FIN)
    if debutFin == -1:
        return None, True, _(u"le manifeste terminal du dump SQL est absent")

    ligneFin = contenu[debutFin + 1:]
    correspondance = _SQL_MANIFESTE_FIN_RE.match(ligneFin)
    if correspondance is None:
        return None, True, _(u"le manifeste terminal du dump SQL est tronqué ou invalide")

    jetonFin, tailleTexte, empreinteAttendue = correspondance.groups()
    if jetonFin != jeton:
        return None, True, _(u"les identifiants de début et de fin du dump SQL diffèrent")

    charge = contenu[finEntete + 1:debutFin]
    if len(charge) != int(tailleTexte):
        return None, True, _(u"la taille du dump SQL ne correspond pas au manifeste")

    empreinteReelle = _EncoderAscii(hashlib.sha256(charge).hexdigest())
    if empreinteReelle != empreinteAttendue:
        return None, True, _(u"l'empreinte du dump SQL ne correspond pas au manifeste")

    return charge, True, None


def _NettoyerSQLPourAnalyse(texte):
    """ Retire commentaires et littéraux sans masquer les identifiants SQL quotés. """
    texte = re.sub(r"/\*!\d{5,6}\s*(.*?)\*/", r"\1", texte, flags=re.S)
    resultat = io.StringIO()
    index = 0
    longueur = len(texte)

    while index < longueur:
        caractere = texte[index]

        if caractere == u"'":
            quote = caractere
            resultat.write(u" __NOETHYS_SQL_STRING__ ")
            index += 1
            ferme = False
            while index < longueur:
                caractere = texte[index]
                if caractere == u"\\":
                    index += 2
                    continue
                if caractere == quote:
                    if index + 1 < longueur and texte[index + 1] == quote:
                        index += 2
                        continue
                    index += 1
                    ferme = True
                    break
                index += 1
            if ferme == False:
                return resultat.getvalue(), False
            continue

        if caractere in (u"`", u'"'):
            quote = caractere
            debut = index
            index += 1
            ferme = False
            while index < longueur:
                if texte[index] == quote:
                    if index + 1 < longueur and texte[index + 1] == quote:
                        index += 2
                        continue
                    index += 1
                    ferme = True
                    break
                if texte[index] == u"\\":
                    index += 2
                    continue
                index += 1
            resultat.write(texte[debut:index])
            if ferme == False:
                return resultat.getvalue(), False
            continue

        if caractere == u"/" and index + 1 < longueur and texte[index + 1] == u"*":
            finCommentaire = texte.find(u"*/", index + 2)
            if finCommentaire == -1:
                return resultat.getvalue(), False
            resultat.write(u" ")
            index = finCommentaire + 2
            continue

        if caractere == u"#":
            finLigne = texte.find(u"\n", index + 1)
            if finLigne == -1:
                break
            resultat.write(u"\n")
            index = finLigne + 1
            continue

        if caractere == u"-" and index + 1 < longueur and texte[index + 1] == u"-":
            suivant = texte[index + 2:index + 3]
            if suivant == u"" or suivant.isspace():
                finLigne = texte.find(u"\n", index + 2)
                if finLigne == -1:
                    break
                resultat.write(u"\n")
                index = finLigne + 1
                continue

        resultat.write(caractere)
        index += 1

    return resultat.getvalue(), True


def _NouvelInventaireObjetsSQL():
    return {
        "tables": set(),
        "vues": set(),
        "triggers": set(),
        "procedures": set(),
        "fonctions": set(),
        "evenements": set(),
    }


def _ClasserInstructionSQL(instruction, objets):
    correspondances = {
        "TABLE": "tables",
        "VIEW": "vues",
        "TRIGGER": "triggers",
        "PROCEDURE": "procedures",
        "FUNCTION": "fonctions",
        "EVENT": "evenements",
    }

    correspondance = _CREATE_OBJET_SQL_RE.match(instruction)
    if correspondance is not None:
        typeObjet = correspondance.group("type").upper()
        modificateurs = correspondance.group("modificateurs") or u""
        if typeObjet != "TABLE" or re.search(r"\bTEMPORARY\b", modificateurs, re.IGNORECASE) is None:
            objets[correspondances[typeObjet]].add(_NomObjetSQL(correspondance.group("nom")))
        return

    correspondance = _ECRITURE_TABLE_SQL_RE.match(instruction)
    if correspondance is not None:
        objets["tables"].add(_NomObjetSQL(correspondance.group("nom")))


def _DecouperInstructionsSQL(texte):
    """ Classe les instructions de premier niveau en respectant DELIMITER, avec mémoire bornée par instruction. """
    objets = _NouvelInventaireObjetsSQL()
    tampon = []
    tailleTampon = 0
    tamponSignificatif = False
    delimiteur = u";"
    index = 0
    debutLigne = True
    longueur = len(texte)

    while index < longueur:
        if debutLigne and tamponSignificatif == False:
            finLigne = texte.find(u"\n", index)
            if finLigne == -1:
                finLigne = longueur
            ligne = texte[index:finLigne]
            correspondance = re.match(r"^[ \t]*DELIMITER[ \t]+(\S+)[ \t\r]*$", ligne, re.IGNORECASE)
            if correspondance is not None:
                delimiteur = correspondance.group(1)
                tampon = []
                tailleTampon = 0
                index = finLigne + (1 if finLigne < longueur else 0)
                debutLigne = True
                continue

        caractere = texte[index]
        if caractere in (u"`", u'"'):
            quote = caractere
            debut = index
            index += 1
            while index < longueur:
                if texte[index] == quote:
                    if index + 1 < longueur and texte[index + 1] == quote:
                        index += 2
                        continue
                    index += 1
                    break
                if texte[index] == u"\\":
                    index += 2
                    continue
                index += 1
            fragment = texte[debut:index]
            if tailleTampon < _TAILLE_PREFIXE_INSTRUCTION_SQL:
                fragmentPrefixe = fragment[:_TAILLE_PREFIXE_INSTRUCTION_SQL - tailleTampon]
                tampon.append(fragmentPrefixe)
                tailleTampon += len(fragmentPrefixe)
            tamponSignificatif = True
            debutLigne = fragment.endswith(u"\n")
            continue

        if delimiteur and texte.startswith(delimiteur, index):
            instruction = u"".join(tampon).strip()
            if tamponSignificatif and instruction:
                _ClasserInstructionSQL(instruction, objets)
            tampon = []
            tailleTampon = 0
            tamponSignificatif = False
            index += len(delimiteur)
            debutLigne = False
            continue

        if tailleTampon < _TAILLE_PREFIXE_INSTRUCTION_SQL:
            tampon.append(caractere)
            tailleTampon += 1
        if not caractere.isspace():
            tamponSignificatif = True
        debutLigne = caractere == u"\n"
        index += 1

    # Un objet explicitement créé comme vue ne doit pas être accepté comme table ordinaire.
    objets["tables"].difference_update(objets["vues"])
    return objets, tamponSignificatif, delimiteur


def _NomObjetSQL(valeur):
    valeur = valeur.strip()
    if valeur.startswith(u"`") and valeur.endswith(u"`"):
        valeur = valeur[1:-1].replace(u"``", u"`")
    elif valeur.startswith(u'"') and valeur.endswith(u'"'):
        valeur = valeur[1:-1].replace(u'""', u'"')
    return valeur.lower()


def _AnalyserDumpSQL(fichier):
    """ Valide l'intégrité disponible et extrait les objets persistants attendus. """
    try:
        contenu = _LireFichierBinaire(fichier)
    except (IOError, OSError) as err:
        return None, _(u"lecture impossible : %s") % err

    charge, avecManifeste, erreur = _ExtraireChargeSQL(contenu)
    if erreur is not None:
        return None, erreur
    if not charge or not charge.strip():
        return None, _(u"le dump SQL est vide")

    if isinstance(charge, bytes):
        texte = charge.decode("utf-8", "ignore")
    else:
        texte = charge

    texteNettoye, ferme = _NettoyerSQLPourAnalyse(texte)
    if ferme == False:
        return None, _(u"le dump SQL se termine dans une chaîne, un identifiant ou un commentaire non fermé")

    objets, reste, delimiteur = _DecouperInstructionsSQL(texteNettoye)
    if reste:
        return None, _(u"la dernière instruction SQL est incomplète")
    if delimiteur != u";":
        return None, _(u"le dump SQL ne rétablit pas le délimiteur standard en fin de fichier")

    if not any(objets.values()):
        return None, _(u"aucun objet persistant ou chargement de table n'a été trouvé")

    return {"avec_manifeste": avecManifeste, "objets": objets}, None


def _SQLContientChargeRestauratrice(fichier):
    analyse, erreur = _AnalyserDumpSQL(fichier)
    return analyse is not None and erreur is None


def _QuoteIdentifiantMySQL(valeur):
    return u"`%s`" % valeur.replace(u"`", u"``")


def _EchapperLitteralMySQL(valeur):
    return valeur.replace(u"\\", u"\\\\").replace(u"'", u"\\'")


def _AjouterMarqueurTerminalSQL(fichier, nomBase):
    """ Ajoute au fichier extrait un objet éphémère qui ne peut exister que si la fin est exécutée. """
    jeton = uuid.uuid4().hex
    nomTable = u"__noethys_restore_%s" % jeton
    tableQualifiee = u"%s.%s" % (_QuoteIdentifiantMySQL(nomBase), _QuoteIdentifiantMySQL(nomTable))
    sql = (
        u"\n-- NOETHYS-RESTORE-END-V1 %s\n"
        u"CREATE TABLE %s (`jeton` CHAR(32) NOT NULL PRIMARY KEY);\n"
        u"INSERT INTO %s (`jeton`) VALUES ('%s');\n"
    ) % (jeton, tableQualifiee, tableQualifiee, jeton)
    with open(fichier, "ab") as flux:
        flux.write(sql.encode("utf-8"))
    return {"table": nomTable, "jeton": jeton}


def _NomFichierReseau(dictConnexion, fichier):
    return u"%s;%s;%s;%s[RESEAU]%s" % (
        dictConnexion["port"], dictConnexion["host"], dictConnexion["user"], dictConnexion["password"], fichier)


def _ExecuterRequeteResultat(DB, requete):
    if DB.ExecuterReq(requete) != 1:
        return None
    return DB.ResultatReq()


def _NormaliserValeurSQL(valeur):
    if isinstance(valeur, bytes):
        return valeur.decode("utf-8", "ignore").lower()
    return (u"%s" % valeur).lower()


def _DiagnosticObjetsManquants(categorie, manquants):
    return u"%s : %s" % (categorie, u", ".join(sorted(manquants)))


def _VerifierPostconditionRestaurationMySQL(dictConnexion, fichier, marqueur, objetsAttendus):
    """ Vérifie le marqueur terminal puis chaque type d'objet attendu, et retire le marqueur. """
    DB = GestionDB.DB(suffixe=None, nomFichier=_NomFichierReseau(dictConnexion, fichier))
    resultat = (False, _(u"la base restaurée n'est pas accessible"))
    nettoyageOk = False

    try:
        if getattr(DB, "echec", 1) == 1:
            return resultat

        tableMarqueur = _QuoteIdentifiantMySQL(marqueur["table"])
        jeton = _EchapperLitteralMySQL(marqueur["jeton"])
        lignes = _ExecuterRequeteResultat(
            DB,
            u"SELECT `jeton` FROM %s WHERE `jeton`='%s' LIMIT 1;" % (tableMarqueur, jeton),
        )
        if lignes is None or len(lignes) != 1 or _NormaliserValeurSQL(lignes[0][0]) != marqueur["jeton"].lower():
            resultat = (False, _(u"le marqueur terminal n'a pas été exécuté"))
        else:
            lignes = _ExecuterRequeteResultat(DB, u"SHOW FULL TABLES;")
            if lignes is None:
                resultat = (False, _(u"la liste des tables et vues restaurées est illisible"))
            else:
                tables = set()
                vues = set()
                nomMarqueur = marqueur["table"].lower()
                for ligne in lignes:
                    if not ligne:
                        continue
                    nomObjet = _NormaliserValeurSQL(ligne[0])
                    if nomObjet == nomMarqueur:
                        continue
                    typeObjet = _NormaliserValeurSQL(ligne[1]) if len(ligne) > 1 else u"base table"
                    if typeObjet == u"view":
                        vues.add(nomObjet)
                    else:
                        tables.add(nomObjet)

                manquants = []
                tablesManquantes = objetsAttendus["tables"] - tables
                vuesManquantes = objetsAttendus["vues"] - vues
                if tablesManquantes:
                    manquants.append(_DiagnosticObjetsManquants(_(u"tables"), tablesManquantes))
                if vuesManquantes:
                    manquants.append(_DiagnosticObjetsManquants(_(u"vues"), vuesManquantes))

                nomBase = _EchapperLitteralMySQL(fichier)
                if not manquants and objetsAttendus["triggers"]:
                    lignes = _ExecuterRequeteResultat(
                        DB,
                        u"SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='%s';" % nomBase,
                    )
                    if lignes is None:
                        manquants.append(_(u"triggers : vérification impossible"))
                    else:
                        trouves = set(_NormaliserValeurSQL(ligne[0]) for ligne in lignes)
                        absents = objetsAttendus["triggers"] - trouves
                        if absents:
                            manquants.append(_DiagnosticObjetsManquants(_(u"triggers"), absents))

                if not manquants and (objetsAttendus["procedures"] or objetsAttendus["fonctions"]):
                    lignes = _ExecuterRequeteResultat(
                        DB,
                        u"SELECT ROUTINE_NAME, ROUTINE_TYPE FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA='%s';" % nomBase,
                    )
                    if lignes is None:
                        manquants.append(_(u"routines : vérification impossible"))
                    else:
                        procedures = set()
                        fonctions = set()
                        for ligne in lignes:
                            if len(ligne) < 2:
                                continue
                            if _NormaliserValeurSQL(ligne[1]) == u"procedure":
                                procedures.add(_NormaliserValeurSQL(ligne[0]))
                            elif _NormaliserValeurSQL(ligne[1]) == u"function":
                                fonctions.add(_NormaliserValeurSQL(ligne[0]))
                        absents = objetsAttendus["procedures"] - procedures
                        if absents:
                            manquants.append(_DiagnosticObjetsManquants(_(u"procédures"), absents))
                        absents = objetsAttendus["fonctions"] - fonctions
                        if absents:
                            manquants.append(_DiagnosticObjetsManquants(_(u"fonctions"), absents))

                if not manquants and objetsAttendus["evenements"]:
                    lignes = _ExecuterRequeteResultat(
                        DB,
                        u"SELECT EVENT_NAME FROM information_schema.EVENTS WHERE EVENT_SCHEMA='%s';" % nomBase,
                    )
                    if lignes is None:
                        manquants.append(_(u"événements : vérification impossible"))
                    else:
                        trouves = set(_NormaliserValeurSQL(ligne[0]) for ligne in lignes)
                        absents = objetsAttendus["evenements"] - trouves
                        if absents:
                            manquants.append(_DiagnosticObjetsManquants(_(u"événements"), absents))

                if manquants:
                    resultat = (False, _(u"des objets attendus sont absents ou de type incorrect : %s") % u" ; ".join(manquants))
                else:
                    resultat = (True, u"")
    except Exception as err:
        resultat = (False, _(u"la vérification post-restauration a échoué : %s") % err)
    finally:
        try:
            if getattr(DB, "echec", 1) != 1:
                nettoyageOk = DB.ExecuterReq(
                    u"DROP TABLE IF EXISTS %s;" % _QuoteIdentifiantMySQL(marqueur["table"])
                ) == 1
        except Exception:
            nettoyageOk = False
        DB.Close()

    if resultat[0] and nettoyageOk == False:
        return False, _(u"le marqueur terminal n'a pas pu être supprimé après vérification")
    return resultat


def _SupprimerMarqueurRestaurationMySQL(dictConnexion, fichier, marqueur):
    """ Nettoyage de secours après un échec du client ou une exception locale. """
    DB = GestionDB.DB(suffixe=None, nomFichier=_NomFichierReseau(dictConnexion, fichier))
    try:
        if getattr(DB, "echec", 1) == 1:
            return False
        return DB.ExecuterReq(
            u"DROP TABLE IF EXISTS %s;" % _QuoteIdentifiantMySQL(marqueur["table"])
        ) == 1
    except Exception:
        return False
    finally:
        DB.Close()



def Sauvegarde(listeFichiersLocaux=[], listeFichiersReseau=[], nom="", repertoire=None, motdepasse=None, listeEmails=None, dictConnexion=None):
    """ Processus de de création du ZIP """
    # Si aucun fichier à sauvegarder
    if len(listeFichiersLocaux) == 0 and len(listeFichiersReseau) == 0 : 
        return False

    # Une sauvegarde réseau sans paramètres de connexion serait silencieusement incomplète
    if len(listeFichiersReseau) > 0 and dictConnexion is None :
        return False
    
    # Initialisation de la barre de progression
    nbreEtapes = 3
    nbreEtapes += len(listeFichiersLocaux)
    nbreEtapes += len(listeFichiersReseau)
    if motdepasse != None : nbreEtapes += 1
    if repertoire != None : nbreEtapes += 1
    if listeEmails != None : nbreEtapes += 1
    
    # Création du nom du fichier de destination
    if motdepasse != None :
        extension = EXTENSIONS["crypte"]
    else:
        extension = EXTENSIONS["decrypte"]

    # Vérifie si fichier de destination existe déjà
    if repertoire != None :
        fichierDest = u"%s/%s.%s" % (repertoire, nom, extension)
        if os.path.isfile(fichierDest) == True :
            dlg = wx.MessageDialog(None, _(u"Un fichier de sauvegarde portant ce nom existe déjà. \n\nVoulez-vous le remplacer ?"), "Attention !", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return False

    # Récupération des paramètres de l'adresse d'expéditeur par défaut
    if listeEmails != None :
        dictAdresse = UTILS_Envoi_email.GetAdresseExpDefaut()
        if dictAdresse == None :
            dlgErreur = wx.MessageDialog(None, _(u"Envoi par Email impossible :\n\nAucune adresse d'expéditeur n'a été définie. Veuillez la saisir dans le menu Paramétrage du logiciel..."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)
            dlgErreur.ShowModal() 
            dlgErreur.Destroy()
            return False

    # Fenêtre de progression
    dlgprogress = wx.ProgressDialog(_(u"Sauvegarde"), _(u"Lancement de la sauvegarde..."), maximum=nbreEtapes, parent=None, style= wx.PD_SMOOTH | wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    
    # Création du fichier ZIP temporaire
    nomFichierTemp = u"%s.%s" % (nom, EXTENSIONS["decrypte"])
    fichierZip = zipfile.ZipFile(UTILS_Fichiers.GetRepTemp(fichier=nomFichierTemp), "w", allowZip64=True, compression=zipfile.ZIP_DEFLATED)
    numEtape = 1
    dlgprogress.Update(numEtape, _(u"Création du fichier de compression..."));numEtape += 1
    
    # Intégration des fichiers locaux
    for nomFichier in listeFichiersLocaux :
        dlgprogress.Update(numEtape, _(u"Compression du fichier %s...") % nomFichier);numEtape += 1
        fichier = UTILS_Fichiers.GetRepData(nomFichier)
        if os.path.isfile(fichier) == True :
            fichierZip.write(fichier, nomFichier)
        else :
            dlgprogress.Destroy()
            dlgErreur = wx.MessageDialog(None, _(u"Le fichier '%s' n'existe plus sur cet ordinateur. \n\nVeuillez ôter ce fichier de la procédure de sauvegarde automatique (Menu Fichier > Sauvegardes automatiques)") % nomFichier, _(u"Erreur"), wx.OK | wx.ICON_ERROR)
            dlgErreur.ShowModal() 
            dlgErreur.Destroy()
            fichierZip.close()
            _SupprimerFichiersSauvegardeTemp(nom)
            return False
        
    # Intégration des fichiers réseau
    if len(listeFichiersReseau) > 0 and dictConnexion != None :
        repTemp = UTILS_Fichiers.GetRepTemp(fichier="savetemp")
        try:
            if os.path.isdir(repTemp) == True :
                shutil.rmtree(repTemp)
            os.mkdir(repTemp)

            # Recherche du répertoire d'installation de MySQL
            repMySQL = GetRepertoireMySQL(dictConnexion)
            if repMySQL == None :
                dlgprogress.Destroy()
                dlgErreur = wx.MessageDialog(None, _(u"Noethys n'a pas réussi à localiser MySQL sur votre ordinateur.\n\nNotez bien que MySQL doit être installé obligatoirement pour créer une sauvegarde réseau."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)
                dlgErreur.ShowModal()
                dlgErreur.Destroy()
                fichierZip.close()
                _SupprimerFichiersSauvegardeTemp(nom)
                return False

            # Création du fichier de login
            nomFichierLoginTemp = repTemp + "/logintemp.cnf"
            CreationFichierLoginTemp(host=dictConnexion["host"], port=dictConnexion["port"], user=dictConnexion["user"], password=dictConnexion["password"], nomFichier=nomFichierLoginTemp)

            # Création du backup pour chaque fichier MySQL
            for nomFichier in listeFichiersReseau :
                dlgprogress.Update(numEtape, _(u"Compression du fichier %s...") % nomFichier);numEtape += 1
                fichierSave = u"%s/%s.sql" % (repTemp, nomFichier)
                options = UTILS_Customize.GetValeur("sauvegarde", "options", "", ajouter_si_manquant=False)

                # --opt active notamment --lock-tables : les options transactionnelles doivent suivre.
                args = u""""%sbin/mysqldump" --defaults-extra-file="%s" --opt --single-transaction --skip-lock-tables %s --databases %s > "%s" """ % (repMySQL, nomFichierLoginTemp, options or "", nomFichier, fichierSave)
                print(("Chemin mysqldump =", args))
                if six.PY2:
                    args = args.encode('utf8')
                proc = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
                out, temp = proc.communicate()

                if proc.returncode != 0:
                    print((out,))
                    out = _TexteErreurProcessus(out)
                    dlgprogress.Destroy()
                    dlgErreur = wx.MessageDialog(None, _(u"Une erreur a été détectée dans la procédure de sauvegarde !\n\nErreur : %s") % out, _(u"Erreur"), wx.OK | wx.ICON_ERROR)
                    dlgErreur.ShowModal()
                    dlgErreur.Destroy()
                    fichierZip.close()
                    _SupprimerFichiersSauvegardeTemp(nom)
                    return False

                # Ajoute un manifeste SQL non cassant (commentaires) avant archivage.
                _AjouterManifesteIntegriteSQL(fichierSave)

                # Insère le fichier Sql dans le ZIP
                try :
                    fichierZip.write(fichierSave, u"%s.sql" % nomFichier)
                except Exception as err :
                    dlgprogress.Destroy()
                    print(("insertion sql dans zip : ", err,))
                    try :
                        if six.PY2:
                            err = str(err).decode("utf8")
                    except Exception:
                        pass
                    dlgErreur = wx.MessageDialog(None, _(u"Une erreur est survenue dans la sauvegarde !\n\nErreur : %s") % err, _(u"Erreur"), wx.OK | wx.ICON_ERROR)
                    dlgErreur.ShowModal()
                    dlgErreur.Destroy()
                    fichierZip.close()
                    _SupprimerFichiersSauvegardeTemp(nom)
                    return False

        except Exception as err:
            dlgprogress.Destroy()
            print(("Echec commande de sauvegarde MySQL :", err,))
            try:
                fichierZip.close()
            except Exception:
                pass
            _SupprimerFichiersSauvegardeTemp(nom)
            dlgErreur = wx.MessageDialog(None, _(u"Une erreur a été détectée dans la procédure de sauvegarde !\n\nErreur : %s") % err, _(u"Erreur"), wx.OK | wx.ICON_ERROR)
            dlgErreur.ShowModal()
            dlgErreur.Destroy()
            return False
        finally:
            _SupprimerRepertoireTemp(repTemp)

    # Finalise le fichier ZIP
    fichierZip.close()
    
    # Cryptage du fichier
    if motdepasse != None :
        dlgprogress.Update(numEtape, _(u"Cryptage du fichier..."));numEtape += 1
        fichierCrypte = u"%s.%s" % (nom, EXTENSIONS["crypte"])
        motdepasse = base64.b64decode(motdepasse)
        if six.PY3:
            motdepasse = motdepasse.decode('utf8')
        ancienne_methode = UTILS_Customize.GetValeur("version_cryptage", "sauvegarde", "1", ajouter_si_manquant=False) in ("1", None)
        UTILS_Cryptage_fichier.CrypterFichier(UTILS_Fichiers.GetRepTemp(fichier=nomFichierTemp), UTILS_Fichiers.GetRepTemp(fichier=fichierCrypte), motdepasse, ancienne_methode=ancienne_methode)
        nomFichierTemp = fichierCrypte
        extension = EXTENSIONS["crypte"]
    else:
        extension = EXTENSIONS["decrypte"]
    
    # Copie le fichier obtenu dans le répertoire donné
    if repertoire != None :
        dlgprogress.Update(numEtape, _(u"Création du fichier dans le répertoire cible..."));numEtape += 1
        try :
            shutil.copy2(UTILS_Fichiers.GetRepTemp(fichier=nomFichierTemp), fichierDest)
        except Exception as err:
            dlgprogress.Destroy()
            print(("Echec copie sauvegarde vers %s :" % fichierDest, err))
            dlgErreur = wx.MessageDialog(None, _(u"La sauvegarde a bien été créée temporairement mais n'a pas pu être copiée vers le répertoire de destination.\n\nDestination : %s\n\nErreur : %s") % (fichierDest, err), _(u"Erreur de sauvegarde"), wx.OK | wx.ICON_ERROR)
            dlgErreur.ShowModal()
            dlgErreur.Destroy()
            _SupprimerFichiersSauvegardeTemp(nom)
            return False

    # Préparation du message
    message = UTILS_Envoi_email.Message(destinataires=listeEmails, sujet=_(u"Sauvegarde Noethys : %s") % nom,
                                        texte_html=_(u"Envoi de la sauvegarde de Noethys"),
                                        fichiers=[UTILS_Fichiers.GetRepTemp(fichier=nomFichierTemp),])

    # Envoi par Email
    if listeEmails != None :
        dlgprogress.Update(numEtape, _(u"Expédition de la sauvegarde par Email..."));numEtape += 1
        messagerie = None
        try :
            messagerie = UTILS_Envoi_email.Messagerie(backend=dictAdresse["moteur"], hote=dictAdresse["smtp"], port=dictAdresse["port"], utilisateur=dictAdresse["utilisateur"],
                                                      motdepasse=dictAdresse["motdepasse"], email_exp=dictAdresse["adresse"], use_tls=dictAdresse["startTLS"],
                                                      timeout=60*3, parametres=dictAdresse["parametres"])
            messagerie.Connecter()
            messagerie.Envoyer(message)
            messagerie.Fermer()
            messagerie = None
        except Exception as err:
            dlgprogress.Destroy()
            print((err,))
            if six.PY2:
                err = str(err).decode("utf8")
            dlgErreur = wx.MessageDialog(None, _(u"Une erreur a été détectée dans l'envoi par Email !\n\nErreur : %s") % err, _(u"Erreur"), wx.OK | wx.ICON_ERROR)
            dlgErreur.ShowModal() 
            dlgErreur.Destroy()
            _SupprimerFichiersSauvegardeTemp(nom)
            return False
        finally:
            if messagerie is not None:
                try:
                    messagerie.Fermer()
                except Exception:
                    pass
    
    # Suppression des répertoires et fichiers temporaires
    dlgprogress.Update(numEtape, _(u"Suppression des fichiers temporaires..."));numEtape += 1
    _SupprimerFichiersSauvegardeTemp(nom)
    
    # Fin du processus
    dlgprogress.Update(numEtape, _(u"Sauvegarde terminée avec succès !"))
    dlgprogress.Destroy()
    
    return True

def VerificationZip(fichier=""):
    """ Vérifie que le fichier est une archive zip valide """
    return zipfile.is_zipfile(fichier)
    
def GetListeFichiersZIP(fichier):
    """ Récupère la liste des fichiers du ZIP """
    with zipfile.ZipFile(fichier, "r") as fichierZip:
        return list(fichierZip.namelist())
    
def Restauration(parent=None, fichier="", listeFichiersLocaux=[], listeFichiersReseau=[], dictConnexion=None):
    """ Restauration à partir des listes de fichiers locaux et réseau """
    listeFichiersRestaures = []
    dlgprogress = None
    
    # Initialisation de la barre de progression
    fichierZip = zipfile.ZipFile(fichier, "r")
    #fichierZip = MyZipFile(fichier, "r")

    # Une restauration réseau nécessite les paramètres de connexion
    if len(listeFichiersReseau) > 0 and dictConnexion is None :
        fichierZip.close()
        return False

    # Restauration des fichiers locaux Sqlite ------------------------------------------------------------------------------
    if len(listeFichiersLocaux) > 0 :

        # Vérifie qu'on les remplace bien
        listeExistantsTemp = []
        for fichier in listeFichiersLocaux :
            if os.path.isfile(UTILS_Fichiers.GetRepData(fichier)) == True :
                listeExistantsTemp.append(fichier)
                
        if len(listeExistantsTemp) > 0 :
            if len(listeExistantsTemp) == 1 :
                message = _(u"Le fichier '%s' existe déjà.\n\nSouhaitez-vous vraiment le remplacer ?") % listeExistantsTemp[0]
            else :
                message = _(u"Les fichiers suivants existent déjà :\n\n   - %s\n\nSouhaitez-vous vraiment les remplacer ?") % "\n   - ".join(listeExistantsTemp)
            dlg = wx.MessageDialog(parent, message, "Attention !", wx.YES_NO | wx.CANCEL |wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_YES :
                fichierZip.close()
                return False
        
        # Restauration
        nbreEtapes = len(listeFichiersLocaux)
        dlgprogress = wx.ProgressDialog(_(u"Merci de patienter"), _(u"Lancement de la restauration..."), maximum=nbreEtapes, parent=parent, style= wx.PD_SMOOTH | wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
        numEtape = 1

        for fichier in listeFichiersLocaux :
            dlgprogress.Update(numEtape, _(u"Restauration du fichier %s...") % fichier);numEtape += 1
            try :
                # buffer = fichierZip.read(fichier)
                # f = open(UTILS_Fichiers.GetRepData(fichier), "wb")
                # f.write(buffer)
                # f.close()
                fichierZip.extract(fichier, UTILS_Fichiers.GetRepData())
            except Exception as err:
                dlgprogress.Destroy()
                print(err)
                dlg = wx.MessageDialog(None, _(u"La restauration du fichier '%s' a rencontré l'erreur suivante : \n%s") % (fichier, err), "Erreur", wx.OK| wx.ICON_ERROR)  
                dlg.ShowModal()
                dlg.Destroy()
                fichierZip.close()
                return False
            
            listeFichiersRestaures.append(fichier[:-4])

    # Restauration des fichiers réseau MySQL -------------------------------------------------------------------------------------------------------------------------
    if len(listeFichiersReseau) > 0 :
                        
        # Récupération de la liste des fichiers MySQL de l'ordinateur
        listeFichiersExistants = GetListeFichiersReseau(dictConnexion)

        # Recherche du répertoire d'installation de MySQL
        repMySQL = GetRepertoireMySQL(dictConnexion) 
        if repMySQL == None :
            dlgErreur = wx.MessageDialog(None, _(u"Noethys n'a pas réussi à localiser MySQL sur votre ordinateur.\nNotez bien que MySQL doit être installé obligatoirement pour créer une restauration réseau."), _(u"Erreur"), wx.OK | wx.ICON_ERROR)
            dlgErreur.ShowModal() 
            dlgErreur.Destroy()
            fichierZip.close()
            return False

        # Vérifie qu'on les remplace bien
        listeExistantsTemp = []
        for fichier in listeFichiersReseau :
            fichier = fichier[:-4]
            if fichier in listeFichiersExistants :
                listeExistantsTemp.append(fichier)
                
        if len(listeExistantsTemp) > 0 :
            if len(listeExistantsTemp) == 1 :
                message = _(u"Le fichier '%s' existe déjà.\n\nSouhaitez-vous vraiment le remplacer ?") % listeExistantsTemp[0]
            else :
                message = _(u"Les fichiers suivants existent déjà :\n\n   - %s\n\nSouhaitez-vous vraiment les remplacer ?") % "\n   - ".join(listeExistantsTemp)
            dlg = wx.MessageDialog(parent, message, "Attention !", wx.YES_NO | wx.CANCEL |wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_YES :
                fichierZip.close()
                return False

        # Création du répertoire temporaire et restauration réseau
        repTemp = UTILS_Fichiers.GetRepTemp(fichier="restoretemp")
        try:
            if os.path.isdir(repTemp) == True :
                shutil.rmtree(repTemp)
            os.mkdir(repTemp)

            # Création du fichier de login
            nomFichierLoginTemp = repTemp + "/logintemp.cnf"
            CreationFichierLoginTemp(host=dictConnexion["host"], port=dictConnexion["port"], user=dictConnexion["user"], password=dictConnexion["password"], nomFichier=nomFichierLoginTemp)

            # Restauration
            nbreEtapes = len(listeFichiersReseau)
            dlgprogress = wx.ProgressDialog(_(u"Merci de patienter"), _(u"Lancement de la restauration..."), maximum=nbreEtapes, parent=parent, style= wx.PD_SMOOTH | wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
            numEtape = 1

            for fichier in listeFichiersReseau:
                fichier = fichier[:-4]

                # Copie du fichier SQL dans le répertoire Temp / restoretemp
                fichierZip.extract(u"%s.sql" % fichier, repTemp)
                fichierRestore = u"%s/%s.sql" % (repTemp, fichier)

                # Valide le manifeste lorsqu'il existe, la terminaison SQL et les objets attendus.
                analyseSQL, erreurSQL = _AnalyserDumpSQL(fichierRestore)
                if analyseSQL is None:
                    dlgprogress.Destroy()
                    dlgErreur = wx.MessageDialog(None, _(u"Le fichier SQL '%s' est incomplet ou invalide :\n\n%s") % (fichier, erreurSQL), _(u"Erreur"), wx.OK | wx.ICON_ERROR)
                    dlgErreur.ShowModal()
                    dlgErreur.Destroy()
                    fichierZip.close()
                    return False

                # Création de la base uniquement après validation de la charge SQL.
                if fichier not in listeFichiersExistants :
                    nomFichier = u"%s;%s;%s;%s[RESEAU]%s" % (dictConnexion["port"], dictConnexion["host"], dictConnexion["user"], dictConnexion["password"], fichier)
                    DB = GestionDB.DB(suffixe=None, nomFichier=nomFichier, modeCreation=True)
                    try:
                        if getattr(DB, "echec", 1) == 1:
                            raise RuntimeError(_(u"La base MySQL '%s' n'a pas pu être créée.") % fichier)
                    finally:
                        DB.Close()

                # Le marqueur est ajouté uniquement à la copie extraite. Il doit être exécuté en toute fin d'import.
                marqueurRestauration = _AjouterMarqueurTerminalSQL(fichierRestore, fichier)
                try:
                    # Importation du fichier SQL dans MySQL
                    dlgprogress.Update(numEtape, _(u"Restauration du fichier %s...") % fichier);numEtape += 1

                    args = u""""%sbin/mysql" --defaults-extra-file="%s" %s < "%s" """ % (repMySQL, nomFichierLoginTemp, fichier, fichierRestore)
                    print(("Chemin mysql =", args))
                    if six.PY2:
                        args = args.encode("utf8")
                    proc = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
                    out, temp = proc.communicate()

                    if proc.returncode != 0:
                        print(("subprocess de restauration mysql :", out))
                        out = _TexteErreurProcessus(out)
                        dlgprogress.Destroy()
                        dlgErreur = wx.MessageDialog(None, _(u"Une erreur a été détectée dans la procédure de restauration !\n\nErreur : %s") % out, _(u"Erreur"), wx.OK | wx.ICON_ERROR)
                        dlgErreur.ShowModal()
                        dlgErreur.Destroy()
                        fichierZip.close()
                        return False

                    postconditionOk, diagnostic = _VerifierPostconditionRestaurationMySQL(
                        dictConnexion, fichier, marqueurRestauration, analyseSQL["objets"]
                    )
                    if postconditionOk == False:
                        dlgprogress.Destroy()
                        dlgErreur = wx.MessageDialog(None, _(u"Le client MySQL n'a signalé aucune erreur, mais la restauration est incomplète :\n\n%s") % diagnostic, _(u"Erreur"), wx.OK | wx.ICON_ERROR)
                        dlgErreur.ShowModal()
                        dlgErreur.Destroy()
                        fichierZip.close()
                        return False
                finally:
                    if marqueurRestauration is not None:
                        _SupprimerMarqueurRestaurationMySQL(dictConnexion, fichier, marqueurRestauration)

                listeFichiersRestaures.append(fichier)

        except Exception as err:
            if dlgprogress is not None:
                dlgprogress.Destroy()
            print(("Echec commande de restauration MySQL :", err,))
            dlgErreur = wx.MessageDialog(None, _(u"Une erreur a été détectée dans la procédure de restauration !\n\nErreur : %s") % err, _(u"Erreur"), wx.OK | wx.ICON_ERROR)
            dlgErreur.ShowModal()
            dlgErreur.Destroy()
            fichierZip.close()
            return False
        finally:
            _SupprimerRepertoireTemp(repTemp)

    # Fin de la procédure
    if dlgprogress is not None:
        dlgprogress.Destroy()
    fichierZip.close()
    return listeFichiersRestaures
    

def GetListeFichiersReseau(dictValeurs={}):
    """ Récupère la liste des fichiers MySQL existants 
         dictValeurs = valeurs de connexion
    """
    hote = dictValeurs["hote"]
    utilisateur = dictValeurs["utilisateur"]
    motdepasse = dictValeurs["mdp"]
    port = dictValeurs["port"]

    DB = GestionDB.DB(nomFichier=u"%s;%s;%s;%s[RESEAU]" % (port, hote, utilisateur, motdepasse))
    if DB.echec == 1 :
        DB.Close()
        return []
    
    DB.ExecuterReq("SHOW DATABASES;")
    listeValeurs = DB.ResultatReq()
    DB.Close()
    
    listeDatabases = []
    for valeurs in listeValeurs :
        listeDatabases.append(valeurs[0])
    
    return listeDatabases

def GetRepertoireMySQL(dictValeurs={}):
    """ Récupère le répertoire d'installation MySQL 
         dictValeurs = valeurs de connexion
    """
    # Récupération du chemin de MySQL à partir de la base de données

    # 1- Recherche automatique
    if "linux" in sys.platform :
        if os.path.isfile(u"/usr/bin/mysqldump") and os.path.isfile(u"/usr/bin/mysql") :
            return u"/usr/"
    else :
        
        # Vérifie le chemin Canon (x86)
        chemin = "C:/Program Files (x86)/Canon/Easy-WebPrint EX/"
        if os.path.isfile(chemin + "bin/mysql.exe") :
            return chemin
        
        # Vérifie le chemin Canon
        chemin = "C:/Program Files/Canon/Easy-WebPrint EX/"
        if os.path.isfile(chemin + "bin/mysql.exe") :
            return chemin
        
        # Vérifie le chemin MySQL classique
        try :
            listeFichiers1 = os.listdir(u"C:/")
            for fichier1 in listeFichiers1 :
                
                if "Program" in fichier1 :
                    listeFichiers2 = os.listdir(u"C:/%s" % fichier1)
                    for fichier2 in listeFichiers2 :
                        if "MySQL" in fichier2 :
                            listeFichiers3 = os.listdir(u"C:/%s/%s" % (fichier1, fichier2))
                            listeFichiers3.sort(reverse=True)
                            for fichier3 in listeFichiers3 :
                                if "MySQL Server" in fichier3 :
                                    chemin = u"C:/%s/%s/%s/" % (fichier1, fichier2, fichier3)
                                    if os.path.isfile(chemin + "bin/mysql.exe") :
                                        return chemin
        except Exception:
            pass
        
    # 2- Recherche dans le fichier Config
    try :
        chemin = UTILS_Config.GetParametre("sauvegarde_cheminmysql", defaut=None)
        if chemin != None :
            if os.path.isdir(chemin) :
                return chemin
    except Exception:
        pass
        
    # 3- Demande le chemin à l'utilisateur
    try :
        if "linux" in sys.platform :
            message = _(u"Pour effectuer la sauvegarde de fichiers réseau, mysqlclient doit être installé. Sélectionnez ici le répertoire où se trouve 'mysqldump' sur votre ordinateur.")
        else :
            message = _(u"Pour effectuer la sauvegarde de fichiers réseau, Noethys \ndoit utiliser les outils de MySQL. Sélectionnez ici le répertoire qui se nomme 'MySQL Server...' sur votre ordinateur.")
        dlg = wx.DirDialog(None, message, style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            chemin = dlg.GetPath() + u"/"
            dlg.Destroy()    
        else:
            dlg.Destroy()    
            return None
    except Exception:
        pass
    
    try :
        if os.path.isdir(chemin + _(u"bin/")) :
            UTILS_Config.SetParametre("sauvegarde_cheminmysql", chemin)
            return chemin
    except Exception:
        pass
        
    return None

def CreationFichierLoginTemp(host="", user="", port="3306", password="", nomFichier=""):
    password = GestionDB.DecodeMdpReseau(password)
    if os.path.isfile(nomFichier) == True :
        os.remove(nomFichier)
    fichier = open(nomFichier, "w", encoding="utf-8")
    fichier.write(u"[client]\nhost=%s\nuser=%s\nport=%s\npassword=%s" % (host, user, port, password))
    fichier.close()


if __name__ == u"__main__":
    app = wx.App(0)
    from Dlg import DLG_Sauvegarde
    frame_1 = DLG_Sauvegarde.Dialog(None)
    app.SetTopWindow(frame_1)
    frame_1.ShowModal()
    app.MainLoop()
