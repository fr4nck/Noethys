#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Impression dediee des conventions d'encadrement sportif."""

import datetime
import re
import sys
from decimal import Decimal
from xml.sax.saxutils import escape

import wx

import FonctionsPerso
import GestionDB
from Utils import UTILS_Config, UTILS_Organisateur, UTILS_Questionnaires
from Utils.UTILS_Traduction import _

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", u"€")
QUESTION_SAISON = u"Saison de la convention"
QUESTION_TYPE = u"Type de structure"
TYPE_ASSOCIATION = u"Association sportive"
JOURS = [u"Lundi", u"Mardi", u"Mercredi", u"Jeudi", u"Vendredi", u"Samedi", u"Dimanche"]


def _txt(value):
    return u"" if value is None else u"%s" % value


def _safe(value):
    return escape(_txt(value))


def _date(value):
    if isinstance(value, datetime.date):
        return value
    return datetime.datetime.strptime(_txt(value)[:10], "%Y-%m-%d").date()


def _saison(value):
    match = re.match(r"^\s*(\d{4})\s*[-/]\s*(\d{4})\s*$", _txt(value))
    if not match or int(match.group(2)) != int(match.group(1)) + 1:
        raise ValueError(_(u"La saison doit etre au format 2026-2027."))
    debut = int(match.group(1))
    return datetime.date(debut, 9, 1), datetime.date(debut + 1, 8, 31)


def _minutes(debut, fin):
    try:
        h1, m1 = [int(x) for x in _txt(debut).split(":")[:2]]
        h2, m2 = [int(x) for x in _txt(fin).split(":")[:2]]
        a, b = h1 * 60 + m1, h2 * 60 + m2
        if b < a:
            b += 1440
        return b - a
    except Exception:
        return 0


def _heure(value):
    return _txt(value)[:5].replace(":", "h")


def _duree(minutes):
    return u"%dh%02d" % (minutes // 60, minutes % 60)


def _date_fr(value):
    return u"%02d/%02d/%04d" % (value.day, value.month, value.year)


def _montant(value):
    value = Decimal(str(value or 0)).quantize(Decimal("0.01"))
    entier, decimales = (u"%.2f" % float(value)).split(".")
    morceaux = []
    while entier:
        morceaux.insert(0, entier[-3:])
        entier = entier[:-3]
    return u"%s,%s %s" % (u" ".join(morceaux), decimales, SYMBOLE)


def _questionnaire(IDfamille):
    # Utiliser le moteur natif est indispensable pour convertir les ID des
    # listes deroulantes en libelles (ex. "Association sportive").
    champs = UTILS_Questionnaires.ChampsEtReponses(type="famille")
    return dict((_txt(item["label"]), _txt(item["reponse"]))
                for item in champs.GetDonnees(IDfamille))


def _representants(IDfamille):
    DB = GestionDB.DB()
    DB.ExecuterReq("""SELECT individus.IDindividu, individus.nom, individus.prenom,
        individus.rue_resid, individus.cp_resid, individus.ville_resid,
        individus.profession, rattachements.titulaire
        FROM rattachements
        LEFT JOIN individus ON individus.IDindividu=rattachements.IDindividu
        WHERE rattachements.IDfamille=%d AND rattachements.IDcategorie=1
        ORDER BY rattachements.titulaire DESC, rattachements.IDrattachement;""" % IDfamille)
    rows = DB.ResultatReq()
    DB.Close()
    return [{
        "IDindividu": r[0], "nom": _txt(r[1]), "prenom": _txt(r[2]),
        "rue": _txt(r[3]), "cp": _txt(r[4]), "ville": _txt(r[5]),
        "profession": _txt(r[6]), "titulaire": r[7] or 0,
    } for r in rows]


def _structure(IDfamille):
    reps = _representants(IDfamille)
    if not reps:
        raise ValueError(_(u"Aucun representant n'est rattache a cette famille."))
    entites = [r for r in reps if r["titulaire"] and not r["prenom"].strip()]
    if not entites:
        entites = [r for r in reps if not r["prenom"].strip()]
    structure = entites[0] if entites else reps[0]
    personnes = [r for r in reps if r["prenom"].strip()]
    return structure, (personnes[0] if personnes else None)


def _etiquettes():
    DB = GestionDB.DB()
    DB.ExecuterReq("SELECT IDetiquette, label FROM etiquettes;")
    rows = DB.ResultatReq()
    DB.Close()
    return dict((int(ID), _txt(label)) for ID, label in rows)


def _labels(value, etiquettes):
    resultats = []
    for token in re.split(r"[;,|\s]+", _txt(value).strip()):
        try:
            label = etiquettes.get(int(token))
        except Exception:
            label = None
        if label and label not in resultats:
            resultats.append(label)
    return resultats


def _planning(IDfamille, debut, fin):
    DB = GestionDB.DB()
    DB.ExecuterReq("""SELECT consommations.IDconso, consommations.IDindividu,
        consommations.date, consommations.heure_debut, consommations.heure_fin,
        consommations.etat, consommations.IDprestation, consommations.etiquettes,
        activites.nom, groupes.nom, individus.nom, individus.prenom, prestations.montant
        FROM consommations
        LEFT JOIN inscriptions ON inscriptions.IDinscription=consommations.IDinscription
        LEFT JOIN activites ON activites.IDactivite=consommations.IDactivite
        LEFT JOIN groupes ON groupes.IDgroupe=consommations.IDgroupe
        LEFT JOIN individus ON individus.IDindividu=consommations.IDindividu
        LEFT JOIN prestations ON prestations.IDprestation=consommations.IDprestation
        WHERE inscriptions.IDfamille=%d
        AND consommations.date>='%s' AND consommations.date<='%s'
        AND (consommations.etat IS NULL OR consommations.etat<>'refus')
        ORDER BY consommations.date, consommations.heure_debut, individus.nom, individus.prenom;""" %
        (IDfamille, debut.isoformat(), fin.isoformat()))
    rows = DB.ResultatReq()
    DB.Close()
    etiquettes = _etiquettes()
    resultats = []
    for r in rows:
        resultats.append({
            "IDconso": r[0], "IDindividu": r[1], "date": _date(r[2]),
            "debut": _txt(r[3]), "fin": _txt(r[4]), "etat": _txt(r[5]),
            "IDprestation": r[6], "educateurs": _labels(r[7], etiquettes),
            "activite": _txt(r[8]), "public": _txt(r[9]),
            "groupe": _txt(r[11]).strip() or _txt(r[10]).strip(),
            "minutes": _minutes(r[3], r[4]), "montant": r[12],
        })
    return resultats


def _groupes(planning):
    groupes = {}
    for ligne in planning:
        key = (ligne["IDindividu"], ligne["date"].weekday(), ligne["debut"], ligne["fin"])
        groupe = groupes.setdefault(key, {
            "jour": ligne["date"].weekday(), "debut": ligne["debut"], "fin": ligne["fin"],
            "groupe": ligne["groupe"], "public": ligne["public"], "activites": [], "lignes": [],
        })
        if ligne["activite"] and ligne["activite"] not in groupe["activites"]:
            groupe["activites"].append(ligne["activite"])
        groupe["lignes"].append(ligne)
    resultats = list(groupes.values())
    resultats.sort(key=lambda g: (g["jour"], g["debut"], g["fin"], g["groupe"].lower()))
    for groupe in resultats:
        groupe["lignes"].sort(key=lambda l: l["date"])
    return resultats


def _tarifs(planning):
    resultats = {}
    for ligne in planning:
        if ligne["montant"] is None or not ligne["minutes"]:
            continue
        taux = (Decimal(str(ligne["montant"])) * Decimal(60) /
                Decimal(ligne["minutes"])).quantize(Decimal("0.01"))
        resultats.setdefault(ligne["activite"], set()).add(taux)
    return resultats


def _total(planning):
    # Une prestation peut, dans certains parametrages, etre referencee par
    # plusieurs consommations. Elle ne doit etre comptee qu'une fois.
    prestations = {}
    for ligne in planning:
        if ligne["IDprestation"] is not None and ligne["montant"] is not None:
            prestations[ligne["IDprestation"]] = Decimal(str(ligne["montant"]))
    return sum(prestations.values(), Decimal("0.00"))


def _educateurs(groupe):
    labels, renseignees = [], 0
    for ligne in groupe["lignes"]:
        if ligne["educateurs"]:
            renseignees += 1
        for label in ligne["educateurs"]:
            if label not in labels:
                labels.append(label)
    return labels, renseignees


def _export_logo_temp(bitmap):
    """Exporte le logo organisateur en PNG temporaire pour ReportLab."""
    if bitmap is None:
        return None
    try:
        import os
        import tempfile
        image = bitmap.ConvertToImage()
        chemin = os.path.join(tempfile.gettempdir(),
                              "noethys_convention_logo_%s.png" % os.getpid())
        if image.SaveFile(chemin, wx.BITMAP_TYPE_PNG):
            return chemin
    except Exception:
        pass
    return None


def _register_ar_christy():
    """Utilise AR Christy si elle est installée sur Windows, sinon Helvetica."""
    try:
        import os
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        dossier = os.path.join(os.environ.get("WINDIR", r"C:\\Windows"), "Fonts")
        for nom in os.listdir(dossier):
            normalise = nom.lower().replace(" ", "").replace("_", "").replace("-", "")
            if "christy" in normalise and nom.lower().endswith((".ttf", ".otf")):
                pdfmetrics.registerFont(TTFont("ARChristy", os.path.join(dossier, nom)))
                return "ARChristy"
    except Exception:
        pass
    return "Helvetica-Bold"


def _pdf_association(saison, structure, signataire, planning, nomDoc, afficherDoc):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    if sys.platform.startswith("win"):
        nomDoc = nomDoc.replace("/", "\\")
    # Demande une grande zone de travail afin de ne pas agrandir la miniature
    # 40x40 utilisée par défaut dans Noethys.
    org = UTILS_Organisateur.GetDonnees(tailleLogo=(600, 400))
    nom_org = org.get("nom") or u"PÊLE-MÊLE SPORTS ET LOISIRS"
    base = getSampleStyleSheet()["Normal"]
    normal = ParagraphStyle("conv", parent=base, fontName="Helvetica", fontSize=9.2, leading=12, spaceAfter=4)
    titre = ParagraphStyle("conv_titre", parent=normal, fontName="Helvetica-Bold", fontSize=14, leading=17, alignment=TA_CENTER)
    article = ParagraphStyle("conv_article", parent=normal, fontName="Helvetica-Bold", fontSize=10, spaceBefore=7, spaceAfter=4)
    petit = ParagraphStyle("conv_petit", parent=normal, fontSize=8, leading=10)
    nom_asso = ParagraphStyle("conv_nom_asso", parent=normal,
                              fontName=_register_ar_christy(), fontSize=15.5,
                              leading=17, alignment=TA_CENTER)

    story = []
    temp_logo = _export_logo_temp(org.get("logo"))

    def P(text, style=normal, after=5):
        story.append(Paragraph(text, style))
        if after:
            story.append(Spacer(1, after))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(A4[0] / 2.0, 9 * mm, _(u"Convention %s - page %d") % (saison, doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(nomDoc, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=17*mm)
    # En-tête proche du modèle PMSL : logo à gauche, coordonnées à droite.
    logo_cell = Paragraph(u"<b>%s</b>" % _safe(nom_org), titre)
    if temp_logo:
        try:
            logo = Image(temp_logo)
            max_w, max_h = 54 * mm, 36 * mm
            ratio = min(max_w / float(logo.imageWidth), max_h / float(logo.imageHeight))
            logo.drawWidth = logo.imageWidth * ratio
            logo.drawHeight = logo.imageHeight * ratio
            logo_cell = logo
        except Exception:
            pass

    contact = u"%s<br/>%s %s" % (_safe(org.get("rue")),
                                  _safe(org.get("cp")), _safe(org.get("ville")))
    if org.get("tel"):
        contact += u"<br/>%s" % _safe(org.get("tel"))
    if org.get("mail"):
        contact += u"<br/><u>%s</u>" % _safe(org.get("mail"))

    coordonnees = Table([
        [Paragraph(_safe(nom_org.upper()), nom_asso)],
        [Paragraph(contact, ParagraphStyle("conv_coord", parent=normal,
                                           fontName="Helvetica-Bold",
                                           fontSize=10.2, leading=13,
                                           alignment=TA_CENTER))],
    ], colWidths=[86 * mm])
    coordonnees.setStyle(TableStyle([
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))

    entete_table = Table([[logo_cell, coordonnees]], colWidths=[78 * mm, 86 * mm])
    entete_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (0,0), (0,0), "CENTER"),
        ("BOX", (1,0), (1,0), 1.0, colors.black),
        ("TOPPADDING", (1,0), (1,0), 8),
        ("BOTTOMPADDING", (1,0), (1,0), 8),
    ]))
    story.extend([entete_table, Spacer(1, 8)])

    titre_table = Table([[Paragraph(_(u"Convention d'encadrement sportif %s") %
                                    _safe(saison.replace("-", "/")), titre)]],
                        colWidths=[164 * mm])
    titre_table.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 1.2, colors.black),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.extend([titre_table, Spacer(1, 10)])

    signataire_txt = _(u"Non renseigné dans Noethys")
    if signataire:
        signataire_txt = u"%s %s" % (_safe(signataire["prenom"]), _safe(signataire["nom"]))
        if signataire["profession"]:
            signataire_txt += u", %s" % _safe(signataire["profession"])
    parties = [[Paragraph(_(u"<b>ENTRE :</b><br/><b>%s</b><br/>%s<br/>%s %s") %
                          (_safe(nom_org), _safe(org.get("rue")), _safe(org.get("cp")), _safe(org.get("ville"))), normal),
                Paragraph(_(u"Représentée par Madame Nelly ESTIER, Présidente"), normal)],
               [Paragraph(_(u"<b>ET :</b><br/><b>%s</b><br/>%s<br/>%s %s") %
                          (_safe(structure["nom"]), _safe(structure["rue"]), _safe(structure["cp"]), _safe(structure["ville"])), normal),
                Paragraph(_(u"Représentée par %s") % signataire_txt, normal)]]
    table = Table(parties, colWidths=[83*mm, 81*mm])
    table.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("BOTTOMPADDING", (0,0), (-1,-1), 8)]))
    story.extend([table, Spacer(1, 8)])
    P(_(u"Il a été convenu ce qui suit :"))

    P(_(u"ARTICLE 1 : OBJET ET ENGAGEMENT"), article, 0)
    P(_(u"L'association %s, adhérente à %s pour la saison %s, bénéficie de la mise à disposition d'éducateurs sportifs pour l'encadrement des activités prévues au planning annexé à la présente convention.") % (_safe(structure["nom"]), _safe(nom_org), _safe(saison)))
    P(_(u"ARTICLE 2 : DURÉE DE LA CONVENTION"), article, 0)
    P(_(u"%s s'engage à encadrer les séances prévues pour la saison %s, en période scolaire, selon les créneaux définis dans l'annexe 1.") % (_safe(nom_org), _safe(saison)))
    P(_(u"Le calendrier prévisionnel de la saison sportive est joint à la présente convention. Il appartient à l'association partenaire de le vérifier et de le signer."))
    P(_(u"Toute intervention exceptionnelle en dehors des dates prévues au calendrier initial devra faire l'objet d'une demande écrite."))
    P(_(u"ARTICLE 3 : ABSENCE ET ANNULATION"), article, 0)
    P(_(u"Pour des raisons de formation, l'éducateur sportif peut être amené à s'absenter. Dans ce cas et pour toute autre absence prévisible, l'association adhérente sera prévenue au moins 15 jours à l'avance. Dans la mesure du possible, il sera procédé à son remplacement."))
    P(_(u"Si l'association adhérente devait annuler une séance, le secrétariat de %s devra être prévenu au moins une semaine à l'avance.") % _safe(nom_org))
    P(_(u"ARTICLE 4 : RESPONSABILITÉS"), article, 0)
    P(_(u"%s gère les éducateurs sportifs mis à disposition de l'association adhérente. Les éducateurs restent placés sous la responsabilité de %s en sa qualité d'employeur. Ils déclinent toute responsabilité en dehors de leurs heures d'encadrement.") % (_safe(nom_org), _safe(nom_org)))
    P(_(u"%s assure la protection morale et physique des participants au sein des activités que son personnel anime. Elle respecte la législation applicable à l'encadrement, déclare et verse les cotisations sociales de son personnel et applique la Convention Collective Nationale du Sport. À titre d'information, elle a souscrit un contrat d'assurance auprès de Groupama.") % _safe(nom_org))
    P(_(u"ARTICLE 5 : LITIGES"), article, 0)
    P(_(u"Tout litige relatif à l'exécution de la présente convention doit être porté à la connaissance du responsable de l'association adhérente et de la Présidence de %s. L'éducateur sportif n'a pas qualité pour régler seul le litige. À défaut de règlement amiable, le litige sera porté devant la juridiction territorialement compétente conformément aux règles de droit commun.") % _safe(nom_org))
    P(_(u"ARTICLE 6 : FACTURATION DES INTERVENTIONS"), article, 0)
    P(_(u"La facturation des séances encadrées est mensuelle et établie à la fin de chaque mois. Le règlement est effectué à réception de la facture, selon les modalités indiquées sur celle-ci."))
    P(_(u"Les interventions sont facturées selon les tarifs en vigueur dans %s pour les activités et périodes concernées.") % _safe(nom_org))
    tarifs = _tarifs(planning)
    for activite in sorted(tarifs):
        P(u"• %s : %s" % (_safe(activite), _safe(u", ".join(_montant(x) + u"/h" for x in sorted(tarifs[activite])))), petit, 2)
    P(_(u"Toute heure annulée pour un motif justifié et non imputable à l'association adhérente ne lui sera pas facturée."))
    story.append(Spacer(1, 8))
    P(_(u"Fait en deux exemplaires, à La Guerche-de-Bretagne, le ................................"), normal, 8)
    signatures = [[Paragraph(_(u"<b>Pour l'association adhérente</b><br/>%s<br/><br/><br/>Signature et cachet") % signataire_txt, normal),
                   Paragraph(_(u"<b>Pour %s</b><br/>La Présidente<br/>Madame Nelly ESTIER<br/><br/>Signature") % _safe(nom_org), normal)]]
    table = Table(signatures, colWidths=[82*mm, 82*mm])
    table.setStyle(TableStyle([("BOX",(0,0),(-1,-1),0.4,colors.grey),("INNERGRID",(0,0),(-1,-1),0.25,colors.lightgrey),("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),7)]))
    story.append(table)

    story.append(PageBreak())
    P(_(u"ANNEXE 1 - PLANNING PRÉVISIONNEL DES INTERVENTIONS SPORTIVES"), titre, 4)
    P(u"<b>%s - Saison %s</b>" % (_safe(structure["nom"]), _safe(saison)), normal, 10)
    total_minutes = total_seances = 0
    for groupe in _groupes(planning):
        lignes = groupe["lignes"]
        minutes = sum(l["minutes"] for l in lignes)
        total_minutes += minutes
        total_seances += len(lignes)
        P(_(u"<b>Créneau : %s - %s à %s</b>") % (JOURS[groupe["jour"]], _heure(groupe["debut"]), _heure(groupe["fin"])), article, 2)
        P(u"<b>%s</b>" % _safe(groupe["groupe"]), normal, 2)
        if groupe["activites"]:
            P(_(u"Activité : %s") % _safe(u", ".join(groupe["activites"])), petit, 2)
        labels, renseignees = _educateurs(groupe)
        if labels:
            texte = _(u"Éducateur(s) sportif(s) prévu(s) : %s") % _safe(u", ".join(labels))
            if renseignees != len(lignes):
                texte += _(u" (%d séance(s) renseignée(s) sur %d)") % (renseignees, len(lignes))
            P(texte, petit, 4)
        data = [[_(u"Date"), _(u"Début"), _(u"Fin"), _(u"Durée")]] + [[_date_fr(l["date"]), _heure(l["debut"]), _heure(l["fin"]), _duree(l["minutes"])] for l in lignes]
        table = Table(data, colWidths=[45*mm,38*mm,38*mm,38*mm], repeatRows=1)
        table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.35,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E8E8E8")),("FONT",(0,0),(-1,-1),"Helvetica",8),("FONT",(0,0),(-1,0),"Helvetica-Bold",8),("ALIGN",(1,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
        story.extend([table, Spacer(1,4)])
        durees = set(l["minutes"] for l in lignes)
        if len(durees) == 1:
            P(_(u"Soit %d séance(s) d'une durée de %s, représentant un volume prévisionnel total de %s pour la saison %s.") % (len(lignes), _duree(list(durees)[0]), _duree(minutes), saison), petit, 10)
        else:
            P(_(u"Soit %d séance(s), représentant un volume prévisionnel total de %s pour la saison %s.") % (len(lignes), _duree(minutes), saison), petit, 10)

    recap = [[_(u"Nombre total de séances"), u"%d" % total_seances], [_(u"Volume prévisionnel total"), _duree(total_minutes)], [_(u"Montant prévisionnel global des interventions"), _montant(_total(planning))]]
    table = Table(recap, colWidths=[120*mm,44*mm])
    table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,colors.grey),("FONT",(0,0),(0,-1),"Helvetica-Bold",9),("ALIGN",(1,0),(1,-1),"RIGHT"),("PADDING",(0,0),(-1,-1),5)]))
    story.append(table)

    try:
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
    finally:
        if temp_logo:
            try:
                import os
                os.remove(temp_logo)
            except Exception:
                pass
    if afficherDoc:
        FonctionsPerso.LanceFichierExterne(nomDoc)
    return {"nomDoc": nomDoc, "nbre_seances": total_seances, "volume_minutes": total_minutes, "montant": _total(planning)}


def Impression(IDfamille=None, nomDoc=None, afficherDoc=True):
    if IDfamille is None:
        raise ValueError(_(u"IDfamille obligatoire."))
    questionnaire = _questionnaire(IDfamille)
    saison = questionnaire.get(QUESTION_SAISON, u"").strip()
    type_structure = questionnaire.get(QUESTION_TYPE, u"").strip()
    if not saison or not type_structure:
        raise ValueError(_(u"Renseignez la saison et le type de structure dans le questionnaire Famille."))
    debut, fin = _saison(saison)
    structure, signataire = _structure(IDfamille)
    planning = _planning(IDfamille, debut, fin)
    if not planning:
        raise ValueError(_(u"Aucune séance trouvée pour la saison %s.") % saison)
    if type_structure != TYPE_ASSOCIATION:
        raise ValueError(_(u"Premier moteur : seules les associations sportives sont encore prises en charge."))
    if nomDoc is None:
        nomDoc = FonctionsPerso.GenerationNomDoc("CONVENTION", "pdf")
    try:
        return _pdf_association(saison, structure, signataire, planning, nomDoc, afficherDoc)
    except Exception as err:
        dlg = wx.MessageDialog(None, _(u"Impossible de générer la convention.\n\n%s") % _txt(err), _(u"Convention"), wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        return False
