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
from reportlab.platypus import Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle


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
    flottants. """
    story = []
    for objet in objetsFlottants:
        texte = modeleDoc.GetValeur(objet, dictChamps)
        if not texte:
            continue
        style = ParagraphStyle(
            "convention_objet_%s" % id(objet),
            fontName=_PoliceReportLab(objet),
            fontSize=objet.taillePolicePDF,
            leading=objet.taillePolicePDF * 1.25,
        )
        for paragraphe in texte.split(u"\n\n"):
            texte_html = escape(paragraphe).replace(u"\n", u"<br/>")
            if texte_html.strip():
                story.append(Paragraph(texte_html, style))
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
    l'appelant (voir Impression() ci-dessous). """
    modeleDoc = DLG_Noedoc.ModeleDoc(IDmodele=IDmodele)
    cadre, objetsFlottants = _SepareObjetsFixesEtFlottants(modeleDoc)
    story = _ConstruitStory(modeleDoc, objetsFlottants, dictChamps)
    if not story:
        raise ValueError(_(u"Le modèle choisi ne contient aucun texte dans son cadre principal."))

    if nomDoc is None:
        nomDoc = FonctionsPerso.GenerationNomDoc("CONVENTION", "pdf")

    doc = BaseDocTemplate(nomDoc, pagesize=TAILLE_PAGE)
    doc.addPageTemplates([_GabaritConvention(cadre, modeleDoc, dictChamps, objetsFlottants)])
    doc.build(story)

    if afficherDoc:
        FonctionsPerso.LanceFichierExterne(nomDoc)
    return nomDoc


def Impression(IDfamille=None, IDmodele=None, date_debut=None, date_fin=None,
                saison=None, listeIDindividus=None, nomDoc=None, afficherDoc=True):
    """ Point d'entrée : construit les champs depuis les données Noethys
    réelles de la famille, puis délègue tout le rendu au moteur Noedoc.

    Aucun champ n'est obligatoire côté données : un représentant, un
    tarif ou une partie du planning introuvables automatiquement restent
    simplement vides dans le PDF généré (à compléter dans le modèle ou
    en relançant avec des valeurs saisies manuellement), plutôt que de
    bloquer la génération ou d'inventer une valeur.
    """
    if IDfamille is None:
        raise ValueError(_(u"IDfamille obligatoire."))
    if IDmodele is None:
        raise ValueError(_(u"Choisissez un modèle de convention."))

    try:
        champs, dictDonnees = UTILS_Convention_champs.GetChampsConvention(
            IDfamille=IDfamille, date_debut=date_debut, date_fin=date_fin,
            saison=saison, listeIDindividus=listeIDindividus,
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
