#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Fonctions proposées pour les individus rattachés à une entité.
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _


# Les IDs 6 à 9 sont les civilités historiques des personnes morales.
# L'ID 10 est ajouté par Noethys SL pour les écoles. On ne change aucun
# ID existant afin de rester compatible avec les bases historiques.
TYPE_ENTITE_PAR_CIVILITE = {
    6: "collectivite",
    7: "association",
    8: "organisme",
    9: "entreprise",
    10: "ecole",
}

LABEL_TYPE_ENTITE = {
    "collectivite": _(u"Collectivité"),
    "association": _(u"Association"),
    "organisme": _(u"Organisme"),
    "entreprise": _(u"Entreprise"),
    "ecole": _(u"École"),
    "autre": _(u"Autre"),
}


# Chaque entrée : (code stable, libellé masculin, libellé féminin,
# libellé neutre). Le code n'est pas enregistré en base pour l'instant :
# la valeur métier conservée est le libellé réellement choisi, ce qui
# laisse aussi la place à une saisie libre.
FONCTIONS_COMMUNES = [
    ("president", _(u"Président"), _(u"Présidente"), _(u"Président(e)")),
    ("vice_president", _(u"Vice-président"), _(u"Vice-présidente"), _(u"Vice-président(e)")),
    ("tresorier", _(u"Trésorier"), _(u"Trésorière"), _(u"Trésorier(ère)")),
    ("secretaire", _(u"Secrétaire"), _(u"Secrétaire"), _(u"Secrétaire")),
    ("directeur", _(u"Directeur"), _(u"Directrice"), _(u"Directeur/Directrice")),
    ("responsable", _(u"Responsable"), _(u"Responsable"), _(u"Responsable")),
    ("coordinateur", _(u"Coordinateur"), _(u"Coordinatrice"), _(u"Coordinateur/Coordinatrice")),
]

FONCTIONS_PAR_TYPE = {
    "association": [
        ("membre_bureau", _(u"Membre du bureau"), _(u"Membre du bureau"), _(u"Membre du bureau")),
        ("responsable_section", _(u"Responsable de section"), _(u"Responsable de section"), _(u"Responsable de section")),
    ],
    "ecole": [
        ("chef_etablissement", _(u"Chef d'établissement"), _(u"Cheffe d'établissement"), _(u"Chef(fe) d'établissement")),
        ("enseignant", _(u"Enseignant"), _(u"Enseignante"), _(u"Enseignant(e)")),
        ("president_ogec", _(u"Président d'OGEC"), _(u"Présidente d'OGEC"), _(u"Président(e) d'OGEC")),
        ("tresorier_ogec", _(u"Trésorier d'OGEC"), _(u"Trésorière d'OGEC"), _(u"Trésorier(ère) d'OGEC")),
    ],
    "entreprise": [
        ("gerant", _(u"Gérant"), _(u"Gérante"), _(u"Gérant(e)")),
        ("responsable_administratif", _(u"Responsable administratif"), _(u"Responsable administrative"), _(u"Responsable administratif(ve)")),
        ("comptable", _(u"Comptable"), _(u"Comptable"), _(u"Comptable")),
    ],
    "collectivite": [
        ("maire", _(u"Maire"), _(u"Maire"), _(u"Maire")),
        ("adjoint", _(u"Adjoint"), _(u"Adjointe"), _(u"Adjoint(e)")),
        ("responsable_service", _(u"Responsable de service"), _(u"Responsable de service"), _(u"Responsable de service")),
        ("agent", _(u"Agent"), _(u"Agente"), _(u"Agent(e)")),
    ],
    "organisme": [
        ("responsable_service", _(u"Responsable de service"), _(u"Responsable de service"), _(u"Responsable de service")),
    ],
}


def GetTypeDepuisCivilite(IDcivilite):
    try:
        IDcivilite = int(IDcivilite)
    except (TypeError, ValueError):
        return None
    return TYPE_ENTITE_PAR_CIVILITE.get(IDcivilite)


def GetLabelType(type_entite):
    return LABEL_TYPE_ENTITE.get(type_entite or "autre", LABEL_TYPE_ENTITE["autre"])


def _libelle_selon_sexe(entree, sexe=None):
    _code, masculin, feminin, neutre = entree
    if sexe == "M":
        return masculin
    if sexe == "F":
        return feminin
    return neutre


def GetFonctions(type_entite=None, sexe=None):
    """Retourne une liste de libellés, sans doublon, adaptée au type
    d'entité et au genre de la personne. La saisie libre reste toujours
    possible dans l'interface : cette liste n'est qu'une aide."""
    entrees = list(FONCTIONS_COMMUNES)
    entrees.extend(FONCTIONS_PAR_TYPE.get(type_entite, []))
    resultat = []
    for entree in entrees:
        label = _libelle_selon_sexe(entree, sexe=sexe)
        if label not in resultat:
            resultat.append(label)
    return resultat
