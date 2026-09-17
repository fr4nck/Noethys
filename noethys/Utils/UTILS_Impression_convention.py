#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activites
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------------
"""Generation des conventions d'encadrement sportif.

La convention est un document metier distinct du devis. Les donnees sont lues
dans la fiche Famille, le questionnaire Famille et le planning Noethys.
"""

import datetime
import re
import sys
from decimal import Decimal
from xml.sax.saxutils import escape

import wx

import FonctionsPerso
import GestionDB
from Utils import UTILS_Config
from Utils import UTILS_Organisateur
from Utils.UTILS_Traduction import _

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", u"€")
QUESTION_SAISON = u"Saison de la convention"
QUESTION_TYPE = u"Type de structure"
TYPE_ASSOCIATION = u"Association sportive"
JOURS = [u"Lundi", u"Mardi", u"Mercredi", u"Jeudi", u"Vendredi", u"Samedi", u"Dimanche"]


def _texte(value):
    if value is None:
        return u""
    try:
        return u"%s" % value
    except Exception:
        return str(value)


def _safe(value):
    return escape(_texte(value))


def _date_from_db(value):
    if isinstance(value, datetime.date):
        return value
    return datetime.datetime.strptime(_texte(value)[:10], "%Y-%m-%d").date()


def _parse_saison(saison):
    match = re.match(r"^\s*(\d{4})\s*[-/]\s*(\d{4})\s*$", _texte(saison))
    if match is None:
        raise ValueError(_(u"La saison de la convention doit etre au format 2026-2027."))
    annee_debut, annee_fin = int(match.group(1)), int(match.group(2))
    if annee_fin != annee_debut + 1:
        raise ValueError(_(u"La saison de la convention est incoherente."))
    return datetime.date(annee_debut, 9, 1), datetime.date(annee_fin, 8, 31)


def _minutes(heure_debut, heure_fin):
    try:
        hd, hf = _texte(heure_debut).split(":"), _texte(heure_fin).split(":")
        debut = int(hd[0]) * 60 + int(hd[1])
        fin = int(hf[0]) * 60 + int(hf[1])
        if fin < debut:
            fin += 24 * 60
        return max(0, fin - debut)
    except Exception:
        return 0


def _format_heure(value):
    value = _texte(value)
    return value[:5].replace(":", "h") if len(value) >= 5 else value


def _format_duree(minutes):
    return u"%dh%02d" % (int(minutes // 60), int(minutes % 60))


def _format_date(date):
    return u"%02d/%02d/%04d" % (date.day, date.month, date.year)


def _format_montant(montant):
    try:
        valeur = Decimal(str(montant)).quantize(Decimal("0.01"))
    except Exception:
        valeur = Decimal("0.00")
    entier, decimals = (u"%.2f" % float(valeur)).split(".")
    groupes = []
    while entier:
        groupes.insert(0, entier[-3:])
        entier = entier[:-3]
    return u"%s,%s %s" % (u" ".join(groupes), decimals, SYMBOLE)


def _get_questionnaire(IDfamille):
    DB = GestionDB.DB()
    req = """SELECT questionnaire_questions.label, questionnaire_reponses.reponse
    FROM questionnaire_reponses
    LEFT JOIN questionnaire_questions ON questionnaire_questions.IDquestion = questionnaire_reponses.IDquestion
    WHERE questionnaire_reponses.IDfamille=%d;""" % IDfamille
    DB.ExecuterReq(req)
    rows = DB.ResultatReq()
    DB.Close()
    return dict((_texte(label), _texte(reponse)) for label, reponse in rows)


def _get_representants(IDfamille):
    DB = GestionDB.DB()
    req = """SELECT individus.IDindividu, individus.nom, individus.prenom,
    individus.rue_resid, individus.cp_resid, individus.ville_resid,
    individus.profession, rattachements.titulaire
    FROM rattachements
    LEFT JOIN individus ON individus.IDindividu = rattachements.IDindividu
    WHERE rattachements.IDfamille=%d AND rattachements.IDcategorie=1
    ORDER BY rattachements.titulaire DESC, rattachements.IDrattachement;""" % IDfamille
    DB.ExecuterReq(req)
    rows = DB.ResultatReq()
    DB.Close()
    resultats = []
    for row in rows:
        resultats.append({
            "IDindividu": row[0], "nom": _texte(row[1]), "prenom": _texte(row[2]),
            "rue": _texte(row[3]), "cp": _texte(row[4]), "ville": _texte(row[5]),
            "profession": _texte(row[6]), "titulaire": row[7] or 0,
        })
    return resultats


def _get_structure_et_signataire(IDfamille):
    representants = _get_representants(IDfamille)
    if not representants:
        raise ValueError(_(u"Aucun representant n'est rattache a cette famille."))
    structures = [x for x in representants if x["titulaire"] == 1 and not x["prenom"].strip()]
    if not structures:
        structures = [x for x in representants if not x["prenom"].strip()]
    structure = structures[0] if structures else representants[0]
    personnes = [x for x in representants if x["prenom"].strip()]
    return structure, (personnes[0] if personnes else None)


def _get_etiquettes():
    DB = GestionDB.DB()
    DB.ExecuterReq("SELECT IDetiquette, label FROM etiquettes;")
    rows = DB.ResultatReq()
    DB.Close()
    return dict((int(IDetiquette), _texte(label)) for IDetiquette, label in rows)


def _parse_etiquettes(value, dict_etiquettes):
    if value in (None, u"", ""):
        return []
    resultats = []
    for token in re.split(r"[;,|\s]+", _texte(value).strip()):
        if not token:
            continue
        try:
            IDetiquette = int(token)
        except Exception:
            continue
        if IDetiquette in dict_etiquettes and dict_etiquettes[IDetiquette] not in resultats:
            resultats.append(dict_etiquettes[IDetiquette])
    return resultats


def _get_planning(IDfamille, date_debut, date_fin):
    DB = GestionDB.DB()
    req = """SELECT consommations.IDconso, consommations.IDindividu,
    consommations.date, consommations.heure_debut, consommations.heure_fin,
    consommations.etat, consommations.IDprestation, consommations.etiquettes,
    activites.nom, groupes.nom, individus.nom, individus.prenom,
    prestations.montant
    FROM consommations
    LEFT JOIN inscriptions ON inscriptions.IDinscription = consommations.IDinscription
    LEFT JOIN activites ON activites.IDactivite = consommations.IDactivite
    LEFT JOIN groupes ON groupes.IDgroupe = consommations.IDgroupe
    LEFT JOIN individus ON individus.IDindividu = consommations.IDindividu
    LEFT JOIN prestations ON prestations.IDprestation = consommations.IDprestation
    WHERE inscriptions.IDfamille=%d
    AND consommations.date>='%s' AND consommations.date<='%s'
    AND (consommations.etat IS NULL OR consommations.etat<>'refus')
    ORDER BY consommations.date, consommations.heure_debut, individus.nom, individus.prenom;""" % (
        IDfamille, date_debut.isoformat(), date_fin.isoformat())
    DB.ExecuterReq(req)
    rows = DB.ResultatReq()
    DB.Close()
    dict_etiquettes = _get_etiquettes()
    planning = []
    for row in rows:
        date = _date_from_db(row[2])
        prenom, nom_individu = _texte(row[11]).strip(), _texte(row[10]).strip()
        planning.append({
            "IDconso": row[0], "IDindividu": row[1], "date": date,
            "heure_debut": _texte(row[3]), "heure_fin": _texte(row[4]),
            "etat": _texte(row[5]), "IDprestation": row[6],
            "educateurs": _parse_etiquettes(row[7], dict_etiquettes),
            "activite": _texte(row[8]), "public": _texte(row[9]),
            "groupe": prenom if prenom else nom_individu,
            "minutes": _minutes(row[3], row[4]), "montant": row[12],
        })
    return planning


def _group_planning(planning):
    groupes = {}
    for ligne in planning:
        key = (ligne["IDindividu"], ligne["date"].weekday(), ligne["heure_debut"], ligne["heure_fin"])
        if key not in groupes:
            groupes[key] = {
                "IDindividu": ligne["IDindividu"], "jour": ligne["date"].weekday(),
                "heure_debut": ligne["heure_debut"], "heure_fin": ligne["heure_fin"],
                "groupe": ligne["groupe"], "public": ligne["public"],
                "activites": [], "lignes": [],
            }
        groupe = groupes[key]
        if ligne["activite"] and ligne["activite"] not in groupe["activites"]:
            groupe["activites"].append(ligne["activite"])
        groupe["lignes"].append(ligne)
    resultats = list(groupes.values())
    resultats.sort(key=lambda x: (x["jour"], x["heure_debut"], x["heure_fin"], x["groupe"].lower()))
    for groupe in resultats:
        groupe["lignes"].sort(key=lambda x: x["date"])
    return resultats


def _get_tarifs(planning):
    tarifs = {}
    for ligne in planning:
        if ligne["montant"] is None or ligne["minutes"] <= 0:
            continue
        try:
            montant = Decimal(str(ligne["montant"]))
            taux = (montant * Decimal("60") / Decimal(str(ligne["minutes"]))).quantize(Decimal("0.01"))
        except Exception:
            continue
        activite = ligne["activite"] or _(u"Interventions sportives")
        tarifs.setdefault(activite, set()).add(taux)
    return tarifs


def _get_montant_global(planning):
    prestations = {}
    for ligne in planning:
        if ligne["IDprestation"] is not None and ligne["montant"] is not None:
            prestations[ligne["IDprestation"]] = Decimal(str(ligne["montant"]))
    return sum(prestations.values(), Decimal("0.00"))


def _educateurs_groupe(groupe):
    compteur, renseignees = {}, 0
    for ligne in groupe["lignes"]:
        if ligne["educateurs"]:
            renseignees += 1
        for label in ligne["educateurs"]:
            compteur[label] = compteur.get(label, 0) + 1
    return sorted(compteur.keys()), renseignees, len(groupe["lignes"])


def _ajoute_paragraphe(story, texte, style, espace=6):
    from reportlab.platypus import Paragraph, Spacer
    story.append(Paragraph(texte, style))
    if espace:
        story.append(Spacer(1, espace))


def _impression_association(IDfamille, saison, structure, signataire, planning, nomDoc, afficherDoc=True):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    if sys.platform.startswith("win"):
        nomDoc = nomDoc.replace("/", "\\")

    organisateur = UTILS_Organisateur.GetDonnees()
    nom_organisateur = organisateur.get("nom", u"") or u"PÊLE-MÊLE SPORTS ET LOISIRS"
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("ConventionNormal", parent=styles["Normal"], fontName="Helvetica", fontSize=9.2, leading=12, spaceAfter=4, alignment=TA_LEFT)
    titre = ParagraphStyle("ConventionTitre", parent=normal, fontName="Helvetica-Bold", fontSize=14, leading=17, alignment=TA_CENTER, spaceAfter=10)
    article = ParagraphStyle("ConventionArticle", parent=normal, fontName="Helvetica-Bold", fontSize=10, leading=12, spaceBefore=8, spaceAfter=5)
    sous_titre = ParagraphStyle("ConventionSousTitre", parent=normal, fontName="Helvetica-Bold", fontSize=10, leading=12, spaceBefore=6, spaceAfter=4)
    petit = ParagraphStyle("ConventionPetit", parent=normal, fontSize=8, leading=10)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(A4[0] / 2.0, 9 * mm, _(u"Convention %s - page %d") % (saison, doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(nomDoc, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=15 * mm, bottomMargin=17 * mm,
                            title=_(u"Convention d'encadrement sportif %s") % saison)
    story = []

    lignes_org = [u"<b>%s</b>" % _safe(nom_organisateur)]
    adresse_org = u"%s - %s %s" % (_texte(organisateur.get("rue")), _texte(organisateur.get("cp")), _texte(organisateur.get("ville")))
    if adresse_org.replace("-", "").strip():
        lignes_org.append(_safe(adresse_org))
    contact_org = u" - ".join(x for x in (_texte(organisateur.get("tel")), _texte(organisateur.get("mail"))) if x)
    if contact_org:
        lignes_org.append(_safe(contact_org))
    _ajoute_paragraphe(story, u"<br/>".join(lignes_org), normal, 10)
    _ajoute_paragraphe(story, _(u"CONVENTION D'ENCADREMENT SPORTIF %s") % _safe(saison), titre, 8)

    adresse_structure = u"%s<br/>%s %s" % (_safe(structure["rue"]), _safe(structure["cp"]), _safe(structure["ville"]))
    texte_signataire = _(u"Non renseigné dans Noethys")
    if signataire:
        texte_signataire = u"%s %s" % (_safe(signataire["prenom"]), _safe(signataire["nom"]))
        if signataire["profession"]:
            texte_signataire += u", %s" % _safe(signataire["profession"])

    parties = [
        [Paragraph(_(u"<b>ENTRE :</b>"), normal), u""],
        [Paragraph(_(u"<b>%s</b>") % _safe(nom_organisateur), normal), Paragraph(_(u"Représentée par Madame Nelly ESTIER, Présidente"), normal)],
        [Paragraph(u"%s<br/>%s %s" % (_safe(organisateur.get("rue")), _safe(organisateur.get("cp")), _safe(organisateur.get("ville"))), normal), u""],
        [Paragraph(_(u"<b>ET :</b>"), normal), u""],
        [Paragraph(u"<b>%s</b><br/>%s" % (_safe(structure["nom"]), adresse_structure), normal), Paragraph(_(u"Représentée par %s") % texte_signataire, normal)],
    ]
    tableau = Table(parties, colWidths=[80 * mm, 84 * mm])
    tableau.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 2)]))
    story.append(tableau)
    story.append(Spacer(1, 10))
    _ajoute_paragraphe(story, _(u"Il a été convenu ce qui suit :"), normal, 5)

    _ajoute_paragraphe(story, _(u"ARTICLE 1 : OBJET ET ENGAGEMENT"), article, 0)
    _ajoute_paragraphe(story, _(u"L'association %s, adhérente à %s pour la saison %s, bénéficie de la mise à disposition d'éducateurs sportifs pour l'encadrement des activités prévues au planning annexé à la présente convention.") % (_safe(structure["nom"]), _safe(nom_organisateur), _safe(saison)), normal)

    _ajoute_paragraphe(story, _(u"ARTICLE 2 : DURÉE DE LA CONVENTION"), article, 0)
    _ajoute_paragraphe(story, _(u"%s s'engage à encadrer les séances prévues pour la saison %s, en période scolaire, selon les créneaux définis dans l'annexe 1.") % (_safe(nom_organisateur), _safe(saison)), normal)
    _ajoute_paragraphe(story, _(u"Le calendrier prévisionnel de la saison sportive est joint à la présente convention. Il appartient à l'association partenaire de le vérifier et de le signer."), normal)
    _ajoute_paragraphe(story, _(u"Toute intervention exceptionnelle en dehors des dates prévues au calendrier initial devra faire l'objet d'une demande écrite."), normal)

    _ajoute_paragraphe(story, _(u"ARTICLE 3 : ABSENCE ET ANNULATION"), article, 0)
    _ajoute_paragraphe(story, _(u"Pour des raisons de formation, l'éducateur sportif peut être amené à s'absenter. Dans ce cas et pour toute autre absence prévisible, l'association adhérente sera prévenue au moins 15 jours à l'avance. Dans la mesure du possible, il sera procédé à son remplacement."), normal)
    _ajoute_paragraphe(story, _(u"Si, pour des raisons qui devront être précisées, l'association adhérente devait annuler une séance, le secrétariat de %s devra être prévenu au moins une semaine à l'avance.") % _safe(nom_organisateur), normal)

    _ajoute_paragraphe(story, _(u"ARTICLE 4 : RESPONSABILITÉS"), article, 0)
    _ajoute_paragraphe(story, _(u"%s gère les éducateurs sportifs mis à disposition de l'association adhérente. Les éducateurs restent placés sous la responsabilité de %s en sa qualité d'employeur. Ils déclinent toute responsabilité en dehors de leurs heures d'encadrement.") % (_safe(nom_organisateur), _safe(nom_organisateur)), normal)
    _ajoute_paragraphe(story, _(u"%s assure la protection morale et physique des participants au sein des activités que son personnel anime. L'association s'applique au respect de la législation du travail, des lois et des décrets relatifs à l'encadrement, notamment dans le domaine de l'enfance et de l'adolescence. En sa qualité d'employeur, elle déclare et verse les cotisations sociales de son personnel aux organismes habilités. L'action professionnelle de son personnel est régie par la Convention Collective Nationale du Sport.") % _safe(nom_organisateur), normal)
    _ajoute_paragraphe(story, _(u"À titre d'information, %s a souscrit un contrat d'assurance auprès de Groupama.") % _safe(nom_organisateur), normal)

    _ajoute_paragraphe(story, _(u"ARTICLE 5 : LITIGES"), article, 0)
    _ajoute_paragraphe(story, _(u"Tout litige relatif à l'exécution de la présente convention doit être porté à la connaissance du responsable de l'association adhérente et de la Présidence de %s. L'éducateur sportif n'a pas qualité pour régler seul le litige. En cas de problème urgent, l'association adhérente doit en informer immédiatement la Présidence de %s. À défaut de règlement amiable, le litige sera porté devant la juridiction territorialement compétente conformément aux règles de droit commun.") % (_safe(nom_organisateur), _safe(nom_organisateur)), normal)

    _ajoute_paragraphe(story, _(u"ARTICLE 6 : FACTURATION DES INTERVENTIONS"), article, 0)
    _ajoute_paragraphe(story, _(u"La facturation des séances encadrées est mensuelle et établie à la fin de chaque mois. Le règlement est effectué à réception de la facture, selon les modalités indiquées sur celle-ci."), normal)
    _ajoute_paragraphe(story, _(u"Les interventions prévues par la présente convention sont facturées selon les tarifs en vigueur dans %s pour les activités et périodes concernées.") % _safe(nom_organisateur), normal)
    tarifs = _get_tarifs(planning)
    if tarifs:
        lignes_tarifs = []
        for activite in sorted(tarifs.keys()):
            valeurs = u", ".join(_format_montant(x) + _(u"/h") for x in sorted(tarifs[activite]))
            lignes_tarifs.append(u"• %s : %s" % (_safe(activite), _safe(valeurs)))
        _ajoute_paragraphe(story, u"<br/>".join(lignes_tarifs), normal)
    _ajoute_paragraphe(story, _(u"Toute heure annulée pour un motif justifié et non imputable à l'association adhérente ne lui sera pas facturée."), normal)

    story.append(Spacer(1, 10))
    _ajoute_paragraphe(story, _(u"Fait en deux exemplaires, à La Guerche-de-Bretagne, le ................................"), normal, 10)
    signatures = [[
        Paragraph(_(u"<b>Pour l'association adhérente</b><br/>%s<br/><br/><br/>Signature et cachet") % texte_signataire, normal),
        Paragraph(_(u"<b>Pour %s</b><br/>La Présidente<br/>Madame Nelly ESTIER<br/><br/>Signature") % _safe(nom_organisateur), normal),
    ]]
    tableau = Table(signatures, colWidths=[82 * mm, 82 * mm])
    tableau.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.4, colors.grey),
                                  ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey), ("TOPPADDING", (0, 0), (-1, -1), 7),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("LEFTPADDING", (0, 0), (-1, -1), 7)]))
    story.append(tableau)

    story.append(PageBreak())
    _ajoute_paragraphe(story, _(u"ANNEXE 1 – PLANNING PRÉVISIONNEL DES INTERVENTIONS SPORTIVES"), titre, 4)
    _ajoute_paragraphe(story, u"<b>%s – Saison %s</b>" % (_safe(structure["nom"]), _safe(saison)), normal, 10)

    groupes = _group_planning(planning)
    total_minutes, total_seances = 0, 0
    for groupe in groupes:
        lignes = groupe["lignes"]
        if not lignes:
            continue
        total_seances += len(lignes)
        minutes_groupe = sum(x["minutes"] for x in lignes)
        total_minutes += minutes_groupe
        bloc = [Paragraph(_(u"<b>Créneau : %s – %s à %s</b>") % (
            _safe(JOURS[groupe["jour"]]), _safe(_format_heure(groupe["heure_debut"])), _safe(_format_heure(groupe["heure_fin"]))), sous_titre),
            Paragraph(u"<b>%s</b>" % _safe(groupe["groupe"]), normal)]
        if groupe["activites"]:
            bloc.append(Paragraph(_(u"Activité : %s") % _safe(u", ".join(groupe["activites"])), petit))
        if groupe["public"]:
            bloc.append(Paragraph(_(u"Public : %s") % _safe(groupe["public"]), petit))
        educateurs, renseignees, nbre_lignes = _educateurs_groupe(groupe)
        if len(educateurs) == 1 and renseignees == nbre_lignes:
            bloc.append(Paragraph(_(u"Éducateur sportif prévu : %s") % _safe(educateurs[0]), petit))
        elif educateurs:
            texte_educ = _(u"Éducateur(s) sportif(s) prévu(s) : %s") % _safe(u", ".join(educateurs))
            if renseignees != nbre_lignes:
                texte_educ += _(u" (%d séance(s) renseignée(s) sur %d)") % (renseignees, nbre_lignes)
            bloc.append(Paragraph(texte_educ, petit))
        bloc.append(Spacer(1, 4))
        data = [[Paragraph(_(u"<b>Date</b>"), petit), Paragraph(_(u"<b>Début</b>"), petit),
                 Paragraph(_(u"<b>Fin</b>"), petit), Paragraph(_(u"<b>Durée</b>"), petit)]]
        for ligne in lignes:
            data.append([_format_date(ligne["date"]), _format_heure(ligne["heure_debut"]),
                         _format_heure(ligne["heure_fin"]), _format_duree(ligne["minutes"])])
        table = Table(data, colWidths=[45 * mm, 38 * mm, 38 * mm, 38 * mm], repeatRows=1)
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
                                   ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
                                   ("FONT", (0, 1), (-1, -1), "Helvetica", 8), ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                                   ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        bloc.append(table)
        durees = set(x["minutes"] for x in lignes)
        if len(durees) == 1:
            resume = _(u"Soit %d séance(s) d'une durée de %s, représentant un volume prévisionnel total de %s pour la saison %s.") % (
                len(lignes), _format_duree(list(durees)[0]), _format_duree(minutes_groupe), saison)
        else:
            resume = _(u"Soit %d séance(s), représentant un volume prévisionnel total de %s pour la saison %s.") % (
                len(lignes), _format_duree(minutes_groupe), saison)
        bloc.extend([Spacer(1, 4), Paragraph(resume, petit), Spacer(1, 10)])
        story.append(KeepTogether(bloc))

    montant_global = _get_montant_global(planning)
    story.append(Spacer(1, 6))
    recap = [
        [Paragraph(_(u"<b>Nombre total de séances</b>"), normal), u"%d" % total_seances],
        [Paragraph(_(u"<b>Volume prévisionnel total</b>"), normal), _format_duree(total_minutes)],
        [Paragraph(_(u"<b>Montant prévisionnel global des interventions</b>"), normal), _format_montant(montant_global)],
    ]
    table = Table(recap, colWidths=[120 * mm, 44 * mm])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey), ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                               ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 5),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.append(table)

    try:
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
    except Exception as err:
        print("Erreur dans ouverture PDF :", err)
        dlg = wx.MessageDialog(None, _(u"Noethys ne peut pas créer la convention PDF.\n\n%s") % _texte(err),
                               _(u"Erreur d'édition"), wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        return False
    if afficherDoc:
        FonctionsPerso.LanceFichierExterne(nomDoc)
    return {"nomDoc": nomDoc, "nbre_seances": total_seances, "volume_minutes": total_minutes, "montant": montant_global}


def Impression(IDfamille=None, nomDoc=None, afficherDoc=True):
    """Genere la convention de la famille a partir des donnees Noethys."""
    if IDfamille is None:
        raise ValueError(_(u"IDfamille obligatoire pour générer une convention."))
    questionnaire = _get_questionnaire(IDfamille)
    saison = questionnaire.get(QUESTION_SAISON, u"").strip()
    type_structure = questionnaire.get(QUESTION_TYPE, u"").strip()
    if not saison:
        raise ValueError(_(u"Renseignez d'abord 'Saison de la convention' dans le questionnaire Famille."))
    if not type_structure:
        raise ValueError(_(u"Renseignez d'abord 'Type de structure' dans le questionnaire Famille."))
    date_debut, date_fin = _parse_saison(saison)
    structure, signataire = _get_structure_et_signataire(IDfamille)
    planning = _get_planning(IDfamille, date_debut, date_fin)
    if not planning:
        raise ValueError(_(u"Aucune séance n'a été trouvée dans le planning Noethys pour la saison %s.") % saison)
    if nomDoc is None:
        nomDoc = FonctionsPerso.GenerationNomDoc("CONVENTION", "pdf")
    if type_structure == TYPE_ASSOCIATION:
        return _impression_association(IDfamille, saison, structure, signataire, planning, nomDoc, afficherDoc)
    raise ValueError(_(u"Le type de structure '%s' n'est pas encore pris en charge par ce premier moteur de convention.") % type_structure)


if __name__ == "__main__":
    pass
