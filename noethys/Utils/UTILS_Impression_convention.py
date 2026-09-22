#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Orchestration de l'impression d'une convention.

Ce module ne contient AUCUN texte d'article, AUCUNE identité PMSL,
AUCUNE mise en page spécifique aux conventions : tout cela vit dans le
modèle .ndc choisi (documents_modeles/documents_objets), édité avec le
concepteur Noedoc habituel (Dlg/DLG_Noedoc.py), exactement comme une
facture ou une attestation.

Ce module se contente de :
- construire le dictionnaire de champs {CODE: valeur} depuis les données
  Noethys réelles (Utils/UTILS_Convention_champs.py) ;
- charger le modèle choisi (DLG_Noedoc.ModeleDoc) ;
- déclencher le rendu en réutilisant le même mécanisme générique que les
  autres catégories : fond/formes/images/codes-barres dessinés à
  position fixe par ModeleDoc, et les blocs de texte placés dans le
  cadre principal transformés en paragraphes ReportLab (Platypus) pour
  bénéficier de la même pagination automatique que les factures et
  attestations fiscales. Aucune logique de pagination propre aux
  conventions n'est réintroduite ici.
- gérer le fichier final (nom, ouverture).

Audit ciblé (dernier jalon avant recette utilisateur) : BaseDocTemplate/
PageTemplate/Frame/Paragraph ne sont utilisés ici QUE pour permettre
l'écoulement multipage du contenu du cadre principal -- exactement le
même besoin que pour une facture longue. Aucun de ces objets ne reçoit
de texte, de style ou de coordonnées écrits en dur dans ce fichier :
le texte et le style de police viennent de objet.texte/GetValeur() et
objet.taillePolicePDF/Weight/Style (colonnes documents_objets, éditées
dans le concepteur Noedoc), les coordonnées viennent de
modeleDoc.GetCoordsObjet(cadre_principal).

L'ordre de lecture des blocs flottants (et l'ordre de dessin des objets
fixes qui se chevauchent) suit exclusivement la colonne "ordre" de
documents_objets, PAS l'ordre d'insertion en base ni la position
géométrique d'un objet. Cette colonne est réécrite par
DLG_Noedoc.ModeleDoc.Sauvegarde() selon l'ordre d'empilement du canvas
(index de self.GetObjets()), donc SEULES les actions explicites
"Mettre au premier/arrière-plan" du concepteur changent cet ordre :
déplacer un bloc (changer x/y) ne le modifie jamais. Un bloc déplacé
hors du cadre principal bascule en revanche de "flottant" à "fixe" (ou
inversement) via la règle géométrique _ObjetDansCadre -- c'est le seul
changement de comportement attendu d'un déplacement visuel, et il est
volontaire : un objet sorti du cadre n'est plus paginable, donc il doit
redevenir un objet à position fixe. Voir
tests/test_vanilla_convention_rendering.py::
test_ordre_des_blocs_flottants_suit_la_colonne_ordre_pas_l_insertion.

Audit fidélité (recette réelle Atout Sports) : le rendu flottant ne
restituait que police/taille/interligne fixe des objets Noedoc, perdant
couleur de texte, fond, bordure, padding, alignement et soulignement
réellement définis dans le concepteur. _StyleReportLab() les traduit
maintenant en ParagraphStyle (textColor/backColor/borderColor/
borderWidth/borderPadding/alignment), à partir des mêmes attributs déjà
stockés sur l'objet FloatCanvas par DLG_Noedoc.ImportationObjets/
AjouterBlocTexte (Color/BackgroundColor/LineColor/LineWidth/PadSize/
Alignment/LineSpacing/Underlined) -- aucune valeur n'est inventée, une
propriété non définie sur l'objet (None) n'est simplement jamais
appliquée. Voir tests/test_vanilla_convention_rendu_fidelite.py.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

import wx

import FonctionsPerso
from Utils.UTILS_Traduction import _
from Dlg import DLG_Noedoc
from Utils import UTILS_Convention_champs

from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus import Paragraph, KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import mm as mmPDF


TAILLE_PAGE = A4


def _PoliceReportLab(objet):
    """ Traduit Weight/Style de l'objet Noedoc en nom de police ReportLab.

    Reproduit exactement la même règle que la fonction GetPolice interne
    (non exportée) de Dlg.DLG_Noedoc.DessineObjetPDF : ce n'est pas un
    nouveau style, c'est la même correspondance déjà utilisée par le
    moteur générique pour dessiner les objets à position fixe. """
    police = "Arial"
    if objet.Weight == wx.BOLD:
        police = "Arial-Bold"
    if objet.Style == wx.ITALIC:
        police = "Arial-Oblique"
    if objet.Style == wx.ITALIC and objet.Weight == wx.BOLD:
        police = "Arial-BoldOblique"
    return police


ALIGNEMENTS_REPORTLAB = {
    "left": TA_LEFT,
    "right": TA_RIGHT,
    "center": TA_CENTER,
    "justify": TA_JUSTIFY,
}


def _CouleurReportLab(couleurRGB):
    """ objet.Color/BackgroundColor/LineColor (Dlg.DLG_Noedoc, objets
    FloatCanvas ScaledTextBox) sont des tuples (r, g, b) 0-255 ou None --
    exactement la même représentation que
    DLG_Noedoc.ImportationObjets.ConvertCouleur(), jamais reconvertie ni
    devinée ici. """
    if not couleurRGB:
        return None
    r, g, b = couleurRGB
    return colors.Color(r / 255.0, g / 255.0, b / 255.0)


def _StyleReportLab(objet):
    """ Traduit en ParagraphStyle ReportLab les propriétés visuelles
    réellement portées par l'objet Noedoc -- les mêmes que celles
    éditées dans le concepteur et stockées par
    DLG_Noedoc.ImportationObjets/AjouterBlocTexte sur l'objet FloatCanvas
    ScaledTextBox sous-jacent (attributs Color, BackgroundColor,
    LineColor/LineWidth, PadSize, Alignment, LineSpacing) : couleur de
    texte, fond, bordure, padding, alignement, interligne. Le
    soulignement (Underlined) est appliqué séparément (balise <u> autour
    du texte, car ParagraphStyle ne porte pas de propriété "souligné"
    globale). Gras/italique sont déjà gérés par _PoliceReportLab via le
    nom de police (comme pour les objets à position fixe). Aucune valeur
    n'est codée en dur : une propriété non définie sur l'objet (None)
    n'est simplement jamais appliquée au style. """
    style = ParagraphStyle(
        "convention_objet_%s" % id(objet),
        fontName=_PoliceReportLab(objet),
        fontSize=objet.taillePolicePDF,
        leading=objet.taillePolicePDF * 1.2 * (objet.LineSpacing or 1.0),
        alignment=ALIGNEMENTS_REPORTLAB.get(objet.Alignment, TA_LEFT),
        textColor=_CouleurReportLab(objet.Color) or colors.black,
        # Espacement générique entre paragraphes (pas une règle
        # spécifique à un modèle) : sans lui, des paragraphes consécutifs
        # se retrouvent collés, ce qui contribue à une page 1 trop dense.
        spaceAfter=objet.taillePolicePDF * 0.5,
    )
    couleurFond = _CouleurReportLab(objet.BackgroundColor)
    if couleurFond is not None:
        style.backColor = couleurFond
    couleurBordure = _CouleurReportLab(objet.LineColor)
    if couleurBordure is not None:
        style.borderColor = couleurBordure
        style.borderWidth = (objet.LineWidth or 0) * mmPDF
    if objet.PadSize:
        style.borderPadding = objet.PadSize * mmPDF
    return style


def _ObjetDansCadre(modeleDoc, objet, cadre):
    """ Un objet texte placé à l'intérieur du cadre principal porte du
    contenu éditable destiné à s'écouler sur plusieurs pages (articles,
    résumé de planning, ...) ; tout objet hors de ce cadre reste dessiné
    à position fixe par le moteur générique, exactement comme pour les
    autres catégories de document. Règle purement géométrique et
    générique : elle ne connaît rien de "convention". """
    x, y, largeur, hauteur = cadre
    ox, oy, _l, _h = modeleDoc.GetCoordsObjet(objet)
    return (x <= ox <= x + largeur) and (y <= oy <= y + hauteur)


def _SepareObjetsFixesEtFlottants(modeleDoc):
    cadre_principal = modeleDoc.FindObjet("cadre_principal")
    if cadre_principal is None:
        raise ValueError(_(u"Le modèle choisi n'a pas de cadre principal."))
    cadre = modeleDoc.GetCoordsObjet(cadre_principal)

    # modeleDoc.listeObjets est déjà trié par "ordre" (ImportationObjets
    # exécute "ORDER BY ordre") : on ne retrie donc pas nous-mêmes.
    objetsFlottants = [
        objet for objet in modeleDoc.listeObjets
        if "texte" in objet.categorie and _ObjetDansCadre(modeleDoc, objet, cadre)
    ]
    return cadre, objetsFlottants


def _ConstruitStory(modeleDoc, objetsFlottants, dictChamps):
    """ Résout chaque bloc de texte du modèle (mêmes mécanismes {CHAMP}
    et [[SI ...]] que partout ailleurs dans Noethys, via
    ModeleDoc.GetValeur) et le transforme en paragraphes ReportLab
    flottants, avec les propriétés visuelles réellement définies sur
    chaque objet (voir _StyleReportLab).

    Le dernier objet flottant réellement rendu (typiquement le bloc de
    clôture/signatures d'un modèle) est maintenu groupé (KeepTogether) :
    sans cela, un bloc final court peut se retrouver seul en haut d'une
    page presque vide alors qu'il aurait pu tenir avec la fin du bloc
    précédent. Seule la fin du document est concernée, par position dans
    le modèle (le dernier objet), jamais par une règle liée à un modèle
    particulier : les objets précédents continuent de s'écouler
    librement sur plusieurs pages, un long article n'est jamais rendu
    "insécable". """
    objetsAvecTexte = []
    for objet in objetsFlottants:
        texte = modeleDoc.GetValeur(objet, dictChamps)
        if texte:
            objetsAvecTexte.append((objet, texte))

    story = []
    for index, (objet, texte) in enumerate(objetsAvecTexte):
        style = _StyleReportLab(objet)
        groupeObjet = []
        for paragraphe in texte.split(u"\n\n"):
            texte_html = escape(paragraphe).replace(u"\n", u"<br/>")
            if texte_html.strip():
                if objet.Underlined:
                    texte_html = u"<u>%s</u>" % texte_html
                groupeObjet.append(Paragraph(texte_html, style))
        if not groupeObjet:
            continue
        if index == len(objetsAvecTexte) - 1:
            story.append(KeepTogether(groupeObjet))
        else:
            story.extend(groupeObjet)
    return story


def _DessineObjetsFixes(canvas, modeleDoc, dictChamps, objetsFlottants):
    canvas.saveState()
    modeleDoc.DessineFond(canvas, dictChamps=dictChamps)
    modeleDoc.DessineFormes(canvas)
    modeleDoc.DessineImages(canvas, dictChamps=dictChamps)
    modeleDoc.DessineCodesBarres(canvas, dictChamps=dictChamps)
    ensembleFlottants = set(id(o) for o in objetsFlottants)
    for objet in modeleDoc.listeObjets:
        if "texte" in objet.categorie and id(objet) not in ensembleFlottants:
            valeur = modeleDoc.GetValeur(objet, dictChamps)
            DLG_Noedoc.DessineObjetPDF(objet, canvas, valeur=valeur)
    canvas.restoreState()


class _GabaritConvention(PageTemplate):
    def __init__(self, cadre, modeleDoc, dictChamps, objetsFlottants):
        x, y, largeur, hauteur = cadre
        frame = Frame(x, y, largeur, hauteur, id="F1",
                       leftPadding=0, topPadding=0, rightPadding=0, bottomPadding=0)
        self._modeleDoc = modeleDoc
        self._dictChamps = dictChamps
        self._objetsFlottants = objetsFlottants
        PageTemplate.__init__(self, "convention", [frame], self._DessinePage)

    def _DessinePage(self, canvas, doc):
        _DessineObjetsFixes(canvas, self._modeleDoc, self._dictChamps, self._objetsFlottants)


def GenererPDF(IDmodele, dictChamps, nomDoc=None, afficherDoc=True):
    """ Charge le modèle Noedoc choisi et rend le PDF. Ne contient aucune
    donnée métier : dictChamps est déjà entièrement préparé par
    l'appelant (voir Impression() ci-dessous).

    ModeleDoc.__init__ charge toujours modeleDoc.dictOrganisateur (source
    historique Noedoc, {ORGANISATEUR_NOM}/{ORGANISATEUR_RUE}/...,
    ImportationOrganisateur) : c'est la même source que pour les autres
    catégories de documents, aucune nouvelle requête SQL. GetValeur() ne
    résout que les clés réellement présentes dans le dict qu'on lui donne
    (toute clé absente est silencieusement effacée du texte rendu) : sans
    cette fusion, un modèle Convention utilisant {ORGANISATEUR_*} verrait
    ces champs disparaître du PDF. dictChamps (calculé par
    UTILS_Convention_champs.GetChampsConvention) reste prioritaire sur
    dictOrganisateur en cas de clé identique. """
    modeleDoc = DLG_Noedoc.ModeleDoc(IDmodele=IDmodele)
    dictRendu = dict(modeleDoc.dictOrganisateur)
    dictRendu.update(dictChamps)

    cadre, objetsFlottants = _SepareObjetsFixesEtFlottants(modeleDoc)
    story = _ConstruitStory(modeleDoc, objetsFlottants, dictRendu)
    if not story:
        raise ValueError(_(u"Le modèle choisi ne contient aucun texte dans son cadre principal."))

    if nomDoc is None:
        nomDoc = FonctionsPerso.GenerationNomDoc("CONVENTION", "pdf")

    doc = BaseDocTemplate(nomDoc, pagesize=TAILLE_PAGE)
    doc.addPageTemplates([_GabaritConvention(cadre, modeleDoc, dictRendu, objetsFlottants)])
    doc.build(story)

    if afficherDoc:
        FonctionsPerso.LanceFichierExterne(nomDoc)
    return nomDoc


def Impression(IDfamille=None, IDmodele=None, date_debut=None, date_fin=None,
                saison=None, listeIDindividus=None, nomDoc=None, afficherDoc=True,
                overrides=None):
    """ Point d'entrée : construit les champs depuis les données Noethys
    réelles de la famille, puis délègue tout le rendu au moteur Noedoc.

    Aucun champ n'est obligatoire côté données : un représentant, un
    tarif ou une partie du planning introuvables automatiquement restent
    simplement vides dans le PDF généré (à compléter dans le modèle ou
    en relançant avec des valeurs saisies manuellement), plutôt que de
    bloquer la génération ou d'inventer une valeur.

    overrides : dict optionnel {"{CODE}": valeur} transmis tel quel à
    UTILS_Convention_champs.GetChampsConvention -- les corrections
    saisies par l'utilisateur dans DLG_Generation_convention (nom du
    représentant, fonction, date/lieu de signature, tarif horaire).
    N'écrit jamais rien dans Noethys : ce sont des valeurs de génération
    uniquement, propres à ce PDF.
    """
    if IDfamille is None:
        raise ValueError(_(u"IDfamille obligatoire."))
    if IDmodele is None:
        raise ValueError(_(u"Choisissez un modèle de convention."))

    try:
        champs, dictDonnees = UTILS_Convention_champs.GetChampsConvention(
            IDfamille=IDfamille, date_debut=date_debut, date_fin=date_fin,
            saison=saison, listeIDindividus=listeIDindividus, overrides=overrides,
        )
        nomDocFinal = GenererPDF(IDmodele, champs, nomDoc=nomDoc, afficherDoc=afficherDoc)
    except Exception as err:
        dlg = wx.MessageDialog(
            None, _(u"Impossible de générer la convention.\n\n%s") % err,
            _(u"Convention"), wx.OK | wx.ICON_ERROR,
        )
        dlg.ShowModal()
        dlg.Destroy()
        return False

    return {"nomDoc": nomDocFinal, "champs": champs}
