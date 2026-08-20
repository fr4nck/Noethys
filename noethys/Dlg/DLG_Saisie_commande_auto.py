#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------
# Couche de compatibilité pour la saisie des commandes de repas.
# Elle conserve le dialogue historique et remplace uniquement son contrôle
# repas par la variante capable de retrouver les réservations réelles.
# -----------------------------------------------------------

from Ctrl import CTRL_Commande_repas
from Ctrl import CTRL_Commande_repas_auto
from Dlg import DLG_Saisie_commandes_colonne_layout

# Corrige aussi les grands sélecteurs du paramétrage des colonnes : unités,
# groupes et colonnes à totaliser doivent occuper la hauteur disponible.
DLG_Saisie_commandes_colonne_layout.Installer()

# Le dialogue historique importe le module CTRL_Commande_repas puis instancie
# CTRL_Commande_repas.CTRL. On remplace donc cette classe avant son import.
CTRL_Commande_repas.CTRL = CTRL_Commande_repas_auto.CTRL

from Dlg import DLG_Saisie_commande as DLG_Saisie_commande_legacy


class Dialog(DLG_Saisie_commande_legacy.Dialog):
    def __init__(self, parent, IDmodele=None, IDcommande=None):
        super(Dialog, self).__init__(parent, IDmodele=IDmodele, IDcommande=IDcommande)

        # Une nouvelle commande historique s'ouvre sans période, ce qui empêche
        # le moteur de voir la moindre réservation. On propose uniquement une
        # période initiale lorsque les deux champs sont encore vides.
        if IDcommande is None and self.ctrl_date_debut.GetDate() is None and self.ctrl_date_fin.GetDate() is None:
            date_debut, date_fin = CTRL_Commande_repas_auto.GetProchainePeriodeRepas()
            if date_debut is not None and date_fin is not None:
                self.ctrl_date_debut.SetDate(date_debut)
                self.ctrl_date_fin.SetDate(date_fin)
                self.MAJ()
