# -*- coding: utf-8 -*-
"""Fixture d'une base Noethys SQLite temporaire pour les tests.

Construit un sous-ensemble du schema reel (via GestionDB.CreationTable +
Data.DATA_Tables, le schema canonique) et y insere des donnees
synthetiques et anonymisees, structurellement proches d'un cas reel de
convention d'encadrement sportif mais sans aucune donnee personnelle ou
associative reelle.

N'importe jamais depuis le dossier "references" (sauvegarde de recette
reelle, hors depot, jamais utilisee par les tests).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

NOETHYS_DIR = Path(__file__).resolve().parents[1] / "noethys"
if str(NOETHYS_DIR) not in sys.path:
    sys.path.insert(0, str(NOETHYS_DIR))

import GestionDB  # noqa: E402
from Data import DATA_Tables as Tables  # noqa: E402

_DB_ORIGINALE = GestionDB.DB


class _DBRedirigeeVersFichierTest(_DB_ORIGINALE):
    """ GestionDB.DB() sans argument se resout normalement via un fichier
    de configuration sur disque ou une fenetre wx active (aucun des deux
    n'existe en test). Cette sous-classe redirige uniquement les appels
    "par defaut" (aucun nomFichier explicite) vers la base de test, sans
    toucher au comportement des appels qui precisent deja un fichier
    (ex. GestionDB.DB(suffixe="PHOTOS")). """

    chemin_test = None

    def __init__(self, suffixe="DATA", nomFichier="", modeCreation=False, IDconnexion=None, pooling=True):
        if nomFichier == "" and _DBRedirigeeVersFichierTest.chemin_test:
            nomFichier = _DBRedirigeeVersFichierTest.chemin_test
            suffixe = None
        _DB_ORIGINALE.__init__(
            self, suffixe=suffixe, nomFichier=nomFichier,
            modeCreation=modeCreation, IDconnexion=IDconnexion, pooling=pooling,
        )


class RedirectionGestionDB:
    """ Contexte : le temps du bloc, GestionDB.DB() (sans argument) ouvre
    la base de test donnee au lieu de la base par defaut de Noethys.
    Utilise uniquement pour exercer le vrai moteur Noedoc (qui appelle
    toujours GestionDB.DB() en interne, sans parametre injectable) contre
    une base de test isolee, jamais contre une vraie base. """

    def __init__(self, chemin):
        self.chemin = chemin

    def __enter__(self):
        _DBRedirigeeVersFichierTest.chemin_test = self.chemin
        GestionDB.DB = _DBRedirigeeVersFichierTest
        return self

    def __exit__(self, *exc_info):
        GestionDB.DB = _DB_ORIGINALE
        _DBRedirigeeVersFichierTest.chemin_test = None


TABLES_REQUISES = (
    "organisateur", "familles", "individus", "rattachements",
    "activites", "groupes", "unites", "consommations", "prestations",
    "agrements", "documents_modeles", "documents_objets",
    # Tables interrogees sans condition par UTILS_Infos_individus.Informations
    # (representant/famille) : vides ici, juste pour eviter les erreurs
    # "no such table" bruyantes dans les tests.
    "secteurs", "caisses", "regimes", "liens", "parametres",
    "medecins", "categories_travail",
)


class BaseTest:
    """Cree une base SQLite temporaire, la detruit a la fermeture."""

    def __init__(self):
        self._tmpdir = tempfile.TemporaryDirectory(prefix="noethys-test-db-")
        self.chemin = str(Path(self._tmpdir.name) / "test.dat")
        self.db = GestionDB.DB(nomFichier=self.chemin, suffixe=None, modeCreation=True)
        for nom_table in TABLES_REQUISES:
            self.db.CreationTable(nom_table, dicoDB=Tables.DB_DATA)
        self.db.Commit()

    def inserer(self, table, colonnes, lignes):
        placeholders = ", ".join(colonnes)
        for ligne in lignes:
            valeurs = ", ".join(_sql_valeur(v) for v in ligne)
            self.db.ExecuterReq(
                "INSERT INTO %s (%s) VALUES (%s);" % (table, placeholders, valeurs)
            )
        self.db.Commit()

    def fermer(self):
        self.db.Close()
        self._tmpdir.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.fermer()


def _sql_valeur(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    texte = str(v).replace("'", "''")
    return "'%s'" % texte


def creer_base_association_simple():
    """Structure anonymisee proche d'Atout Sports : deux creneaux hebdo recurrents."""
    base = BaseTest()

    base.inserer(
        "organisateur",
        ["IDorganisateur", "nom", "rue", "cp", "ville", "tel", "mail"],
        [(1, "Association Test Loisirs", "1 rue des Tests", "00000", "Testville", "00.00.00.00.00", "test@example.org")],
    )
    base.inserer("familles", ["IDfamille"], [(1,)])
    base.inserer(
        "individus",
        ["IDindividu", "nom", "prenom", "IDcivilite"],
        [
            (1, "STRUCTURE SPORTIVE TEST", "", 3),
            (2, "STRUCTURE SPORTIVE TEST", "Groupe A enfants", 3),
            (3, "STRUCTURE SPORTIVE TEST", "Groupe B adultes", 3),
            (4, "DUPUIS", "Jean", 1),
        ],
    )
    base.inserer(
        "rattachements",
        ["IDrattachement", "IDfamille", "IDindividu", "IDcategorie", "titulaire"],
        [
            (1, 1, 1, 1, 1),
            (2, 1, 2, 2, 0),
            (3, 1, 3, 2, 0),
            (4, 1, 4, 1, 0),
        ],
    )
    base.inserer(
        "activites",
        ["IDactivite", "nom"],
        [(10, "Encadrement sportif enfants"), (11, "Encadrement sportif adultes")],
    )
    base.inserer(
        "groupes",
        ["IDgroupe", "IDactivite", "nom"],
        [(20, 10, "Enfants"), (21, 11, "Adultes")],
    )
    base.inserer(
        "unites",
        ["IDunite", "IDactivite", "nom", "ordre", "type"],
        [(30, 10, "Enfant", 1, "Horaire"), (31, 11, "Adulte", 1, "Horaire")],
    )

    lignes_conso = []
    lignes_prestation = []
    IDprestation = 100
    IDconso = 1000
    # Groupe A enfants : mercredi 17h30-19h00, 24 euros/h -> 36.00 la seance
    for jour in ("2026-09-02", "2026-09-09", "2026-09-16"):
        lignes_prestation.append((IDprestation, "Encadrement sportif enfants", 36.00))
        lignes_conso.append((IDconso, 2, 10, jour, 30, "17:30", "19:00", "reservation", 20, IDprestation))
        IDprestation += 1
        IDconso += 1
    # Groupe B adultes : lundi 19h30-20h30, 36.50 euros/h -> 36.50 la seance
    for jour in ("2026-09-07", "2026-09-14", "2026-09-21"):
        lignes_prestation.append((IDprestation, "Encadrement sportif adultes", 36.50))
        lignes_conso.append((IDconso, 3, 11, jour, 31, "19:30", "20:30", "reservation", 21, IDprestation))
        IDprestation += 1
        IDconso += 1

    base.inserer(
        "prestations",
        ["IDprestation", "label", "montant"],
        lignes_prestation,
    )
    base.inserer(
        "consommations",
        ["IDconso", "IDindividu", "IDactivite", "date", "IDunite", "heure_debut", "heure_fin", "etat", "IDgroupe", "IDprestation"],
        lignes_conso,
    )
    return base


_DEFAUTS_OBJET = {
    "nbreMax": None, "obligatoire": 0, "points": None, "image": None,
    "typeImage": None, "verrouillageX": 0, "verrouillageY": 0,
    "Xmodifiable": 1, "Ymodifiable": 1, "largeurModifiable": 1,
    "hauteurModifiable": 1, "largeurMin": 1, "largeurMax": 10000,
    "hauteurMin": 1, "hauteurMax": 10000, "verrouillageLargeur": 0,
    "verrouillageHauteur": 0, "verrouillageProportions": 0,
    "interditModifProportions": 0, "couleurTrait": None, "styleTrait": "Transparent",
    "epaissTrait": 1.0, "coulRemplis": None, "styleRemplis": "Transparent",
    "couleurTexte": "(0, 0, 0)", "couleurFond": None, "padding": 0.0,
    "interligne": 1.0, "taillePolice": 9, "nomPolice": "", "familyPolice": 74,
    "stylePolice": 90, "weightPolice": 90, "soulignePolice": 0,
    "alignement": "left", "largeurTexte": None, "norme": None,
    "afficheNumero": None, "IDdonnee": None, "champ": None, "texte": None,
}


def inserer_modele_document(base, nom, categorie, objets):
    """ Insere un modele documents_modeles/documents_objets synthetique,
    en suivant exactement le meme schema que
    Utils.UTILS_Export_documents.Importer() (mais sans dependre de la
    connexion par defaut de GestionDB : on ecrit directement sur la base
    de test injectee). Contenu entierement fictif : aucun texte, nom ou
    donnee reelle de PMSL/Atout Sports/La Providence.
    """
    IDmodele = base.db.ReqInsert("documents_modeles", [
        ("nom", nom), ("categorie", categorie), ("supprimable", 1),
        ("largeur", 210), ("hauteur", 297), ("observations", ""),
        ("IDfond", None), ("defaut", 0),
    ])
    for objet in objets:
        valeurs = dict(_DEFAUTS_OBJET)
        valeurs.update(objet)
        valeurs["IDmodele"] = IDmodele
        base.db.ReqInsert("documents_objets", list(valeurs.items()))
    base.db.Commit()
    return IDmodele


def inserer_modele_convention_fictif(base):
    """ Modele de convention fictif : cadre principal + deux blocs de
    texte utilisant la syntaxe reelle {CHAMP}/[[SI ...]], mais avec un
    contenu entierement invente pour les tests (aucun article, aucune
    identite PMSL). """
    objets = [
        {
            "nom": "Cadre principal", "categorie": "special", "champ": "cadre_principal",
            "ordre": 0, "x": 13, "y": 20, "largeur": 182, "hauteur": 250,
        },
        {
            "nom": "Titre", "categorie": "bloc_texte", "ordre": 1,
            "x": 20, "y": 270, "largeur": 170,
            "texte": "CONVENTION DE TEST {CONVENTION_SAISON}",
        },
        {
            "nom": "Corps", "categorie": "bloc_texte", "ordre": 2,
            "x": 13, "y": 20, "largeur": 182,
            "texte": (
                "ENTRE : {ORGANISATEUR_NOM}\n"
                "ET : {FAMILLE_NOM}\n\n"
                "ARTICLE FICTIF 1 : ENGAGEMENT\n"
                "Ceci est un article de test.[[SI {CONVENTION_REPRESENTANT_NOM_COMPLET}<>-> Representant : {CONVENTION_REPRESENTANT_NOM_COMPLET}.]]\n\n"
                "ARTICLE FICTIF 2 : PLANNING\n"
                "{CONVENTION_PLANNING_DETAIL}\n\n"
                "Volume total : {CONVENTION_PLANNING_TOTAL_HEURES}"
            ),
        },
    ]
    return inserer_modele_document(base, "Convention de test", "convention", objets)
