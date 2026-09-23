            return 0
        return min(abs((reference - debut).days), abs((reference - fin).days))
    groupe = min(groupes, key=distance)
    return groupe[0], groupe[-1]


def SaisonDepuisPeriode(date_debut, date_fin):
    debut = _date_simple(date_debut)
    fin = _date_simple(date_fin)
    if debut is None or fin is None:
        return u""
    if debut.year == fin.year:
        return str(debut.year)
    return u"%d-%d" % (debut.year, fin.year)


def ComposerAdresseConvention(rue=None, cp=None, ville=None):
    """Compose une adresse sans répéter CP/ville déjà inclus dans la rue."""
    rue = (rue or u"").strip()
    cp = (str(cp).strip() if cp not in (None, u"") else u"")
    ville = (ville or u"").strip()
    suffixe = u" ".join(partie for partie in (cp, ville) if partie).strip()
    lignes = [ligne.strip() for ligne in rue.splitlines() if ligne.strip()]
    if suffixe:
        suffixe_upper = suffixe.upper()
        if lignes and lignes[-1].upper().endswith(suffixe_upper):
            prefixe = lignes[-1][:-len(suffixe)].rstrip(u" ,-")
            if prefixe:
                lignes[-1] = prefixe
            else:
                lignes.pop()
        if not lignes or lignes[-1].upper() != suffixe_upper:
            lignes.append(suffixe)
    return u"\n".join(lignes)


# ---------------------------------------------------------------------------
# Représentant : réutilise le mécanisme historique {REPRESENTANT_RATTACHE_x_*}
# ---------------------------------------------------------------------------

def GetRepresentant(IDfamille, informations=None, DB=None):
    """ Retourne le représentant/signataire structuré lorsqu'il existe,
    puis retombe sur le mécanisme historique du premier représentant
    nommé. La fonction métier n'est donc inventée dans aucun cas.

    Retour : {"nom", "prenom", "nom_complet", "fonction", ...} ou None.
    Le stockage structuré est porté par le rattachement individu <->
    entité (UTILS_Fonctions_entites) : une même personne peut donc avoir
    des fonctions différentes dans plusieurs entités. Une base ancienne
    sans cette table continue d'utiliser le mécanisme historique.
    """
    from Utils import UTILS_Fonctions_entites

    contact = UTILS_Fonctions_entites.GetRepresentantConvention(IDfamille, DB=DB)
    if contact is not None and contact.get("prenom"):
        return contact

    if informations is None:
        from Utils import UTILS_Infos_individus
        informations = UTILS_Infos_individus.Informations(
            qf=False, inscriptions=False, messages=False, infosMedicales=False,
            cotisationsManquantes=False, piecesManquantes=False,
            questionnaires=False, scolarite=False, cotisations=False,
        )
    dictValeurs = informations.GetDictValeurs(mode="famille", ID=IDfamille, formatChamp=True)
    try:
        nbre = int(dictValeurs.get("{NBRE_REPRESENTANTS_RATTACHES}", 0) or 0)
    except (TypeError, ValueError):
        nbre = 0

    for index in range(1, nbre + 1):
        prefixe = "REPRESENTANT_RATTACHE_%d" % index
        prenom = (dictValeurs.get("{%s_PRENOM}" % prefixe) or u"").strip()
        if not prenom:
            # Entrée institutionnelle (la structure elle-même) : pas une
            # personne à présenter comme représentant.
            continue
        nom = (dictValeurs.get("{%s_NOM}" % prefixe) or u"").strip()
        nom_complet = (dictValeurs.get("{%s_NOM_COMPLET}" % prefixe) or u"").strip()
        # Compatibilité stricte avec le contrat historique de cette
        # fonction : le repli renvoie exactement les trois clés d'origine.
        # GetChampsConvention utilise .get("fonction") et accepte donc
        # naturellement l'absence de fonction sur une ancienne base.
        return {"nom": nom, "prenom": prenom, "nom_complet": nom_complet}
    return None


def GetRepresentantsDisponibles(IDfamille, DB=None):
    """Liste les représentants/signataires structurés proposés dans le
    menu déroulant du générateur de convention."""
    from Utils import UTILS_Fonctions_entites
    contacts = UTILS_Fonctions_entites.GetContactsFamille(IDfamille, DB=DB)
    resultat = []
    for contact in contacts:
        if (contact.get("signataire") or contact.get("representant")) and contact.get("prenom"):
            resultat.append(contact)
    return resultat


def GetReferentsFacturationDisponibles(IDfamille, DB=None):
    from Utils import UTILS_Fonctions_entites
    return [
        contact for contact in UTILS_Fonctions_entites.GetContactsFamille(
            IDfamille, usage="facturation", DB=DB
        )
        if contact.get("prenom")
    ]


# ---------------------------------------------------------------------------
# Tarifs : automatique si déterministe, manuel sinon
# ---------------------------------------------------------------------------

def _duree_heures(heure_debut, heure_fin):
    try:
        h1, m1 = (int(x) for x in str(heure_debut).split(":")[:2])
        h2, m2 = (int(x) for x in str(heure_fin).split(":")[:2])
    except (ValueError, TypeError, AttributeError):
        return None
    minutes = (h2 * 60 + m2) - (h1 * 60 + m1)
    if minutes <= 0:
        return None
    return minutes / 60.0


def _montant_decimal(montant):
    try:
        return Decimal(str(montant))
    except (InvalidOperation, TypeError):