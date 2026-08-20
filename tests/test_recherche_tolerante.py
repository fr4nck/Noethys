# -*- coding: utf-8 -*-

from noethys.Utils import UTILS_Recherche


class Individu(object):
    def __init__(self, prenom="", nom="", tel="", rue="", ville="", mail=""):
        self.prenom = prenom
        self.nom = nom
        self.tel_mobile = tel
        self.rue_resid = rue
        self.ville_resid = ville
        self.mail = mail


def index(individu):
    return UTILS_Recherche.ConstruireIndex(
        individu,
        attributs=("prenom", "nom", "rue_resid", "ville_resid", "mail", "tel_mobile"),
        attributs_telephones=("tel_mobile",),
    )


def test_accents_et_tremas_sont_equivalents():
    noe = index(Individu(prenom="Noé"))
    noe_trema = index(Individu(prenom="Noë"))
    assert UTILS_Recherche.Correspond(noe, "noe")
    assert UTILS_Recherche.Correspond(noe_trema, "noe")


def test_nhoe_retrouve_noe_en_mode_approximatif():
    noe = index(Individu(prenom="Noé"))
    assert not UTILS_Recherche.Correspond(noe, "nhoé", approximatif=False)
    assert UTILS_Recherche.Correspond(noe, "nhoé", approximatif=True)


def test_recherche_telephone_sans_separateurs():
    personne = index(Individu(tel="06 12 34 56 78"))
    assert UTILS_Recherche.Correspond(personne, "0612345678")
    assert UTILS_Recherche.Correspond(personne, "123456")


def test_recherche_adresse_et_email():
    personne = index(Individu(rue="12 rue de l'Église", ville="La Guerche-de-Bretagne", mail="test@example.fr"))
    assert UTILS_Recherche.Correspond(personne, "eglise")
    assert UTILS_Recherche.Correspond(personne, "guerche bretagne")
    assert UTILS_Recherche.Correspond(personne, "test example")


def test_fuzzy_ne_s_applique_pas_aux_termes_trop_courts():
    lea = index(Individu(prenom="Léa"))
    assert not UTILS_Recherche.Correspond(lea, "leo", approximatif=True)
