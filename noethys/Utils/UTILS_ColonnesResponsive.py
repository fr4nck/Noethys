# -*- coding: utf-8 -*-
"""Distribution responsive des colonnes de listes desktop Noethys.

Les écrans déclarent pour chaque colonne une largeur minimale et un poids.
La largeur disponible supplémentaire est répartie entre les colonnes pondérées.
Si la fenêtre devient trop étroite, les minima sont conservés et le contrôle
natif garde son défilement horizontal.

Ce module ne connaît aucun écran métier et ne monkey-patche aucun contrôle.
"""


def _normaliser_specs(specs):
    normalisees = []
    for spec in specs or ():
        if isinstance(spec, dict):
            minimum = spec.get("minimum", spec.get("min", 0))
            poids = spec.get("poids", spec.get("weight", 0))
        else:
            try:
                minimum, poids = spec
            except Exception:
                minimum, poids = 0, 0
        try:
            minimum = max(0, int(minimum))
        except Exception:
            minimum = 0
        try:
            poids = max(0.0, float(poids))
        except Exception:
            poids = 0.0
        normalisees.append((minimum, poids))
    return tuple(normalisees)


def CalculerLargeurs(largeur_disponible, specs, marge=24):
    """Retourne la largeur de chaque colonne, sans jamais passer sous son minimum."""
    specs = _normaliser_specs(specs)
    if not specs:
        return []

    try:
        largeur_disponible = max(0, int(largeur_disponible))
    except Exception:
        largeur_disponible = 0
    try:
        marge = max(0, int(marge))
    except Exception:
        marge = 24

    total_minimum = sum(minimum for minimum, _poids in specs)
    surplus = max(0, largeur_disponible - total_minimum - marge)
    total_poids = sum(poids for _minimum, poids in specs)

    if surplus <= 0 or total_poids <= 0:
        return [minimum for minimum, _poids in specs]

    allocations = []
    distribue = 0
    for minimum, poids in specs:
        ajout = int((surplus * poids) / total_poids) if poids > 0 else 0
        allocations.append(minimum + ajout)
        distribue += ajout

    # Les quelques pixels issus des arrondis vont aux colonnes les plus utiles.
    reste = surplus - distribue
    ordre = sorted(range(len(specs)), key=lambda i: specs[i][1], reverse=True)
    index = 0
    while reste > 0 and ordre:
        cible = ordre[index % len(ordre)]
        if specs[cible][1] > 0:
            allocations[cible] += 1
            reste -= 1
        index += 1
        if index > (len(ordre) * (surplus + 1)):
            break

    return allocations


def Ajuster(controle):
    """Applique immédiatement les largeurs calculées au ListCtrl/ObjectListView."""
    specs = getattr(controle, "_noethys_specs_colonnes", None)
    if not specs:
        return False
    try:
        largeur = controle.GetClientSize().GetWidth()
    except Exception:
        return False

    largeurs = CalculerLargeurs(
        largeur,
        specs,
        marge=getattr(controle, "_noethys_marge_colonnes", 24),
    )
    try:
        nombre_colonnes = controle.GetColumnCount()
    except Exception:
        nombre_colonnes = len(largeurs)

    for index, largeur_colonne in enumerate(largeurs):
        if index >= nombre_colonnes:
            break
        try:
            controle.SetColumnWidth(index, largeur_colonne)
        except Exception:
            pass
    return True


def Installer(controle, specs, marge=24):
    """Installe un recalcul débouncé sur un contrôle de liste existant."""
    if controle is None:
        return False
    specs = _normaliser_specs(specs)
    if not specs:
        return False

    controle._noethys_specs_colonnes = specs
    controle._noethys_marge_colonnes = marge
    controle._noethys_colonnes_pending = False

    try:
        import wx
    except Exception:
        return False

    def _appliquer_plus_tard():
        try:
            controle._noethys_colonnes_pending = False
            Ajuster(controle)
        except Exception:
            controle._noethys_colonnes_pending = False

    def _on_size(event):
        event.Skip()
        if getattr(controle, "_noethys_colonnes_pending", False):
            return
        controle._noethys_colonnes_pending = True
        wx.CallAfter(_appliquer_plus_tard)

    try:
        controle.Bind(wx.EVT_SIZE, _on_size)
        wx.CallAfter(Ajuster, controle)
        return True
    except Exception:
        return False
