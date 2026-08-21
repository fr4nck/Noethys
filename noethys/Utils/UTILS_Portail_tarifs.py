#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Licence:          GNU GPL
#------------------------------------------------------------------------

"""Description sûre des barèmes Noethys pour les supports de publication.

Ce module ne calcule pas une facture et ne dépend ni de wxPython, ni de la
base de données. Il transforme les dictionnaires tarifaires déjà utilisés par
le moteur Noethys en une représentation canonique publiable.

Règle importante : un tarif qui dépend d'une consommation, d'un événement,
d'une durée, d'un questionnaire ou d'une autre condition métier reste marqué
comme contextuel. Le portail ne doit jamais présenter ce type de règle comme
« votre prix ».
"""

import datetime
import html


METHODES_DESCRIPTIBLES = {
    "montant_unique",
    "qf",
    "montant_unique_date",
    "qf_date",
    "choix",
}

LIBELLES_METHODES = {
    "montant_unique": "Montant fixe",
    "qf": "Selon le quotient familial",
    "montant_unique_date": "Selon la date",
    "qf_date": "Selon la date et le quotient familial",
    "choix": "Selon l'option choisie",
    "variable": "Montant saisi selon la situation",
    "montant_evenement": "Selon l'événement",
    "horaire_montant_unique": "Selon les horaires",
    "horaire_qf": "Selon les horaires et le quotient familial",
    "duree_montant_unique": "Selon la durée",
    "duree_qf": "Selon la durée et le quotient familial",
    "montant_unique_nbre_ind": "Selon le nombre de personnes présentes",
    "qf_nbre_ind": "Selon le quotient familial et le nombre de personnes présentes",
    "montant_unique_nbre_ind_degr": "Tarif dégressif selon le nombre de personnes présentes",
    "qf_nbre_ind_degr": "Tarif dégressif selon le quotient familial et le nombre de personnes présentes",
    "duree_coeff_montant_unique": "Au prorata de la durée",
    "duree_coeff_qf": "Au prorata de la durée et du quotient familial",
    "taux_montant_unique": "Selon un taux d'effort",
    "taux_qf": "Selon un taux d'effort et le quotient familial",
    "taux_date": "Selon un taux d'effort et la date",
    "duree_taux_montant_unique": "Selon la durée et un taux d'effort",
    "duree_taux_qf": "Selon la durée, le quotient familial et un taux d'effort",
    "forfait_contrat": "Selon le forfait contractuel",
}


CONDITIONS_CONTEXTUELLES = {
    "groupes": "groupe de l'inscription",
    "etiquettes": "étiquette de consommation",
    "cotisations": "cotisation en cours de validité",
    "caisses": "caisse de rattachement",
    "filtres": "réponse à un questionnaire",
    "jours_scolaires": "jour scolaire",
    "jours_vacances": "période de vacances",
    "combinaisons_unites": "combinaison d'unités consommées",
    "condition_nbre_combi": "nombre de consommations combinées",
    "condition_periode": "période de consommation",
    "condition_nbre_jours": "nombre de jours consommés",
    "condition_conso_facturees": "consommations déjà facturées",
    "condition_dates_continues": "continuité des dates de consommation",
    "etats": "état de la consommation",
    "IDevenement": "événement associé",
}


def _date(valeur):
    if valeur in (None, ""):
        return None
    if isinstance(valeur, datetime.datetime):
        return valeur.date()
    if isinstance(valeur, datetime.date):
        return valeur
    texte = str(valeur).strip()
    try:
        return datetime.datetime.strptime(texte[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _nombre(valeur):
    if valeur in (None, ""):
        return None
    try:
        return float(valeur)
    except (TypeError, ValueError):
        return None


def formater_montant(valeur):
    montant = _nombre(valeur)
    if montant is None:
        return None
    texte = ("%.2f" % montant).replace(".", ",")
    return "%s €" % texte


def formater_date(valeur):
    valeur = _date(valeur)
    if valeur is None:
        return None
    return valeur.strftime("%d/%m/%Y")


def _statut_validite(date_debut, date_fin, date_reference=None):
    reference = _date(date_reference) or datetime.date.today()
    debut = _date(date_debut)
    fin = _date(date_fin)
    if debut and reference < debut:
        return "futur"
    if fin and reference > fin:
        return "expire"
    return "en_vigueur"


def _condition_presente(valeur):
    if valeur in (None, "", False, 0, "0", [], {}, ()):
        return False
    return True


def _avertissements_contextuels(tarif):
    avertissements = []
    for cle, libelle in CONDITIONS_CONTEXTUELLES.items():
        if _condition_presente(tarif.get(cle)):
            avertissements.append("Applicable selon : %s." % libelle)

    methode = str(tarif.get("methode") or "")
    if methode and methode not in METHODES_DESCRIPTIBLES:
        avertissements.append(
            "Le montant exact dépend du contexte réel de réservation ou de facturation."
        )

    # Certains champs d'options sont opaques sans le moteur métier qui les
    # interprète. Leur seule présence suffit donc à empêcher l'affichage d'un
    # faux prix certain.
    if _condition_presente(tarif.get("options")):
        avertissements.append("Ce tarif comporte des options métier supplémentaires.")

    # Les forfaits crédit peuvent nécessiter une consommation ou un stock de
    # crédit déjà existant.
    type_tarif = str(tarif.get("type") or "")
    if type_tarif == "CREDIT":
        avertissements.append(
            "Ce tarif fonctionne avec un crédit/forfait ; le solde disponible n'est pas déduit ici."
        )
    return avertissements


def _regle_montant_unique(lignes):
    if not lignes:
        return []
    montant = formater_montant(lignes[0].get("montant_unique"))
    if montant is None:
        return []
    return [{"type": "montant", "montant": montant}]


def _regles_qf(lignes):
    regles = []
    for ligne in lignes:
        minimum = _nombre(ligne.get("qf_min"))
        maximum = _nombre(ligne.get("qf_max"))
        montant = formater_montant(ligne.get("montant_unique"))
        if montant is None:
            continue
        regles.append({
            "type": "qf",
            "qf_min": minimum,
            "qf_max": maximum,
            "montant": montant,
        })
    return regles


def _regles_date(lignes, avec_qf=False):
    regles = []
    for ligne in lignes:
        date_ligne = formater_date(ligne.get("date"))
        montant = formater_montant(ligne.get("montant_unique"))
        if not date_ligne or montant is None:
            continue
        regle = {
            "type": "qf_date" if avec_qf else "date",
            "date": date_ligne,
            "montant": montant,
        }
        if avec_qf:
            regle["qf_min"] = _nombre(ligne.get("qf_min"))
            regle["qf_max"] = _nombre(ligne.get("qf_max"))
        regles.append(regle)
    return regles


def _regles_choix(lignes):
    regles = []
    for ligne in lignes:
        montant = formater_montant(ligne.get("montant_unique"))
        label = str(ligne.get("label") or "").strip()
        if montant is None and not label:
            continue
        regles.append({
            "type": "choix",
            "label": label or "Option",
            "montant": montant,
        })
    return regles


def decrire_tarif(tarif, date_reference=None):
    """Retourne une description canonique d'un dictionnaire tarifaire Noethys."""
    tarif = dict(tarif or {})
    methode = str(tarif.get("methode") or "").strip()
    lignes = list(tarif.get("lignes_calcul") or [])

    if methode == "montant_unique":
        regles = _regle_montant_unique(lignes)
    elif methode == "qf":
        regles = _regles_qf(lignes)
    elif methode == "montant_unique_date":
        regles = _regles_date(lignes, avec_qf=False)
    elif methode == "qf_date":
        regles = _regles_date(lignes, avec_qf=True)
    elif methode == "choix":
        regles = _regles_choix(lignes)
    else:
        regles = []

    avertissements = _avertissements_contextuels(tarif)
    descriptible = methode in METHODES_DESCRIPTIBLES and bool(regles)
    exact_sans_contexte = (
        methode == "montant_unique"
        and bool(regles)
        and not avertissements
    )

    return {
        "IDtarif": tarif.get("IDtarif"),
        "IDactivite": tarif.get("IDactivite"),
        "activite": str(tarif.get("nom_activite") or tarif.get("activite") or "").strip(),
        "nom": str(tarif.get("nom_tarif") or tarif.get("nom") or "Tarif").strip(),
        "description": str(tarif.get("description_tarif") or tarif.get("description") or "").strip(),
        "IDcategorie_tarif": tarif.get("IDcategorie_tarif"),
        "categorie_tarif": str(tarif.get("nom_categorie_tarif") or "").strip(),
        "date_debut": formater_date(tarif.get("date_debut")),
        "date_fin": formater_date(tarif.get("date_fin")),
        "statut": _statut_validite(tarif.get("date_debut"), tarif.get("date_fin"), date_reference),
        "methode": methode,
        "methode_label": LIBELLES_METHODES.get(methode, "Règle tarifaire contextuelle"),
        "regles": regles,
        "descriptible": descriptible,
        "exact_sans_contexte": exact_sans_contexte,
        "avertissements": avertissements,
    }


def decrire_tarifs(tarifs, date_reference=None, inclure_expires=False):
    descriptions = []
    for tarif in tarifs or []:
        description = decrire_tarif(tarif, date_reference=date_reference)
        if inclure_expires or description["statut"] != "expire":
            descriptions.append(description)
    descriptions.sort(key=lambda x: (
        x.get("activite") or "",
        x.get("nom") or "",
        x.get("date_debut") or "",
    ))
    return descriptions


def _qf_label(regle):
    minimum = regle.get("qf_min")
    maximum = regle.get("qf_max")
    if minimum is None and maximum is None:
        return "Quotient familial"
    if minimum is None:
        return "QF ≤ %g" % maximum
    if maximum is None:
        return "QF ≥ %g" % minimum
    return "QF %g à %g" % (minimum, maximum)


def construire_html(descriptions, titre=None):
    """Génère un HTML autonome depuis des descriptions déjà normalisées."""
    morceaux = ['<div class="noethys-tarifs">']
    if titre:
        morceaux.append("<h3>%s</h3>" % html.escape(str(titre)))

    for tarif in descriptions or []:
        morceaux.append('<section class="noethys-tarif" style="margin-bottom:18px;">')
        morceaux.append("<h4>%s</h4>" % html.escape(tarif.get("nom") or "Tarif"))

        meta = []
        if tarif.get("activite"):
            meta.append(tarif["activite"])
        if tarif.get("categorie_tarif"):
            meta.append(tarif["categorie_tarif"])
        if tarif.get("date_debut") and tarif.get("date_fin"):
            meta.append("du %s au %s" % (tarif["date_debut"], tarif["date_fin"]))
        elif tarif.get("date_debut"):
            meta.append("à partir du %s" % tarif["date_debut"])
        elif tarif.get("date_fin"):
            meta.append("jusqu'au %s" % tarif["date_fin"])
        if tarif.get("statut") == "futur":
            meta.append("tarif à venir")
        if meta:
            morceaux.append('<p style="opacity:0.8;">%s</p>' % html.escape(" · ".join(meta)))

        if tarif.get("description"):
            morceaux.append("<p>%s</p>" % html.escape(tarif["description"]))
        morceaux.append("<p><strong>%s</strong></p>" % html.escape(tarif.get("methode_label") or "Tarification"))

        regles = tarif.get("regles") or []
        if regles:
            morceaux.append('<table style="width:100%;border-collapse:collapse;">')
            for regle in regles:
                type_regle = regle.get("type")
                if type_regle == "montant":
                    libelle = "Tarif"
                elif type_regle == "qf":
                    libelle = _qf_label(regle)
                elif type_regle == "date":
                    libelle = regle.get("date") or "Date"
                elif type_regle == "qf_date":
                    libelle = "%s · %s" % (regle.get("date") or "Date", _qf_label(regle))
                elif type_regle == "choix":
                    libelle = regle.get("label") or "Option"
                else:
                    libelle = "Tarif"
                morceaux.append(
                    '<tr><td style="padding:4px 8px 4px 0;">%s</td>'
                    '<td style="padding:4px 0;text-align:right;"><strong>%s</strong></td></tr>' % (
                        html.escape(str(libelle)),
                        html.escape(str(regle.get("montant") or "—")),
                    )
                )
            morceaux.append("</table>")
        else:
            morceaux.append(
                "<p>Le montant dépend de la réservation ou de la situation réelle.</p>"
            )

        avertissements = tarif.get("avertissements") or []
        if avertissements:
            morceaux.append('<ul style="margin-top:8px;">')
            for avertissement in avertissements:
                morceaux.append("<li>%s</li>" % html.escape(avertissement))
            morceaux.append("</ul>")
        morceaux.append("</section>")

    morceaux.append("</div>")
    return "".join(morceaux)
