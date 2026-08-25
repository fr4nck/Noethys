# Provenance des bugs confirmés — passe de hardening

Ce document accompagne #97/#98 et prépare le lot upstream #99.

Règles :

- `HISTORIQUE_IVAN` : le motif fautif est attesté dans `Noethys/Noethys` avant notre fork ;
- `PORTAGE_PY3_WX` : le motif historique est attesté upstream mais devient invalide ou dangereux avec le runtime/API moderne ;
- `FORK_REPENS` : défaut introduit par notre fork ;
- `INDETERMINE` : preuve insuffisante ; aucune attribution par intuition.

Les références `upstream` ci-dessous pointent vers le `master` public de `Noethys/Noethys` observé pendant la passe. Le SHA de blob permet de figer la preuve même si l'upstream évolue ensuite.

| # | Défaut confirmé | Fichier / fonction | Provenance | Preuve upstream | Correction / contrat dans notre fork | Upstream applicable |
|---|---|---|---|---|---|---|
| 1 | Le règlement d'une facture depuis une fiche famille perd l'`IDfacture` exact et appelle `ReglerFacture()` sans argument. | `Ctrl/CTRL_Numfacture.py` — `CTRL.ReglerFacture` | `HISTORIQUE_IVAN` | blob `4033decc3cb0603bac064f933aeda950c374af74` : branche `IDfamille` avec `ReglerFacture()` alors que le chemin voisin transmet `IDfacture`. | commit `b55df62ccc3d458d134475e0f0345e8ffa2d087a`, `test_numfacture_forwarding_contract.py` | oui |
| 2 | Une base individus initialement vide peut faire retourner `None` à `GetTracks()` puis propager `None` comme données de liste. | `Ol/OL_Individus.py` — `GetTracks` / `MAJ` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : retour `None` dès que `dictIndividus == self.dictIndividus`, y compris au premier chargement vide. | #98, `test_empty_initial_database_does_not_turn_list_data_into_none` | oui |
| 3 | Le dialogue de création de famille n'est pas détruit après `ShowModal()`. | `Ol/OL_Individus.py` — `Ajouter` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : `ShowModal()` suivi directement de la MAJ. | #98, `test_new_family_dialog_is_destroyed` | oui |
| 4 | Un code-barres individu invalide réinitialise `IDfamille` au lieu d'`IDindividu`. | `Ol/OL_Individus.py` — `BarreRecherche.OnText` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : `except: IDfamille = None` dans la branche `I...`. | #98, `test_invalid_individual_barcode_resets_individual_id` | oui |
| 5 | Après lecture d'un code-barres famille, `BarreRecherche` peut appeler `self.MAJ()` alors que cette classe ne définit pas cette méthode. | `Ol/OL_Individus.py` — `BarreRecherche.OnText` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : branche `else: self.MAJ()`. | #98, `test_individual_search_barcode_contract.py` | oui |
| 6 | L'anti-rebond RFID ne bloque pas une deuxième lecture du même badge. | `Ol/OL_Individus.py` — `OnTimerRFID` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : mise à jour de `dernierRFID` seulement si différent, sans retour pour un doublon. | #98, contrat RFID anti-rebond | oui |
| 7 | Le callback RFID arrête son timer puis bloque la boucle wx avec `time.sleep(2)` ; une exception peut laisser la détection coupée. | `Ol/OL_Individus.py` — `OnTimerRFID` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : `Stop()`, `sleep(2)`, `Start()` dans un `try` silencieux. | #98, contrat callback RFID non bloquant | oui |
| 8 | Un individu trouvé par RFID mais absent de la liste filtrée provoque un `KeyError` sur `dictTracks`. | `Ol/OL_Individus.py` — `OnTimerRFID` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : `self.dictTracks[IDindividu]`. | #98, lookup `.get()` + contrat | oui |
| 9 | Une action de synchronisation déjà en anomalie utilise `resultat` avant affectation ou réutilise la valeur du track précédent. | `Dlg/DLG_Synchronisation_donnees.py` — `Traitement.run` | `HISTORIQUE_IVAN` | blob `91593e4a0ac48a5cdd053f70e55a6cfa1434b4fc` : concaténation de `resultat` dans la branche anomalie. | #98, contrat synchronisation | oui |
| 10 | Avec exactement un mémo journalier existant, la synchronisation le considère absent et peut insérer un doublon. | `Dlg/DLG_Synchronisation_donnees.py` — `Traitement.run` | `HISTORIQUE_IVAN` | blob `91593e4a0ac48a5cdd053f70e55a6cfa1434b4fc` : `if len(listeMemos) > 1`. | #98, contrat mémo unique | oui |
| 11 | L'état du thread de synchronisation est testé avec `Thread.isAlive()` ; en Python moderne l'`AttributeError` est interprété comme « traitement arrêté ». | `Dlg/DLG_Synchronisation_donnees.py` — `Dialog_Traitement.Fermer` | `PORTAGE_PY3_WX` | blob `91593e4a0ac48a5cdd053f70e55a6cfa1434b4fc`. | #98, `is_alive()` + contrat | oui |
| 12 | Si la préparation/listen du serveur Nomadhys échoue, le code continue, peut lire `port` avant affectation et lancer le reactor. | `Ctrl/CTRL_Serveur_nomade.py` — `StartServer` | `HISTORIQUE_IVAN` | blob `7324da32e8a517e0d54792d7efafcc402147660a`. | #98, retour immédiat + contrat | oui |
| 13 | Si la requête des avatars échoue, `listeAvatars` n'est jamais définie puis est itérée. | `Utils/UTILS_Utilisateurs.py` — `GetListeUtilisateurs` | `HISTORIQUE_IVAN` | blob `4fd36e2d268f0f09cd12848e45183b94f0be0037`. | #98, repli `[]` + contrat | oui |
| 14 | Si la lecture de l'organisateur échoue, `origine` est utilisée ensuite sans être définie. | `Utils/UTILS_Stats_individus.py` — `GetDictVilles` | `HISTORIQUE_IVAN` | blob `0acf6ee04ddad668942f92c5e7aae0c33312cbde`. | #98, initialisation + contrat | oui |
| 15 | A9061 masque silencieusement un échec d'`UPDATE documents` / `Commit()`. | `Utils/UTILS_Procedures.py` — `A9061` | `HISTORIQUE_IVAN` | blob `f8eedb72fa263085ae6e04d042ee0dd797a8bfee` : mutation dans `try` suivi de `except: pass`. | #98, propagation + `finally Close()` + contrat zéro HIGH | oui |
| 16 | La migration d'une ancienne base masque l'échec du renommage en `_archive.dat`, permettant une recopie ultérieure de la source. | `Utils/UTILS_Fichiers.py` — `DeplaceFichiers` | `HISTORIQUE_IVAN` | blob `efa66625c5dc1cc17ef32f8bb62c8c9494010dec`. | #98, `os.replace(source, archive)` + contrat | oui |
| 17 | L'arrêt du téléchargement de mise à jour utilise `self.downloader.isAlive()` ; l'API supprimée fait croire que le téléchargement n'est pas en cours. | `Dlg/DLG_Updater.py` — `Arreter_telechargement` | `PORTAGE_PY3_WX` | blob `fbd9c50d747b667428253e2a8115213a847da8ab`. | #98, audit API supprimées, `is_alive()` | oui |
| 18 | Recalcul des prestations : les deux contrôles d'état du thread utilisent `self.traitement.isAlive()` et tombent sur le faux repli « arrêté » en Python moderne. | `Dlg/DLG_Recalculer_prestations.py` — `Arreter` / `OnBoutonOk` | `PORTAGE_PY3_WX` | blob `0eb2ff7cbea5c6952b48324acca341768ae03672`. | #98, audit API supprimées, `is_alive()` | oui |
| 19 | Saisie globale de consommations : même défaut `isAlive()` dans les chemins arrêt/lancement. | `Dlg/DLG_Saisie_lot_conso_global.py` — `Arreter` / `OnBoutonOk` | `PORTAGE_PY3_WX` | blob `78f7172059cd1a3599a16635c2398127ca62fa8c`. | #98, audit API supprimées, `is_alive()` | oui |
| 20 | Saisie de forfaits-crédits : même défaut `isAlive()` dans les chemins arrêt/lancement. | `Dlg/DLG_Saisie_lot_forfaits_credits.py` — `Arreter` / `OnBoutonOk` | `PORTAGE_PY3_WX` | blob `817e33409a486f047c489baf04ba4285a0a4b412`. | #98, audit API supprimées, `is_alive()` | oui |
| 21 | Plusieurs dialogues de badgeage lisent `GetSelections()` après `dlg.Destroy()`, dépendant d'un cycle de vie wx historique fragile. | `Dlg/DLG_Badgeage_interface.py` — choix famille / arrivée-départ / réservation | `PORTAGE_PY3_WX` | blob `54d1190bf89783d7f5e0b1a597747b2d0dcd7989` : trois lectures après `Destroy()`. | commit `19ec4312b40bc62ba1d861e6ae46fd88a751acf9`, audit `use_after_destroy=0` | oui |
| 22 | Le dialogue de mesure de distance détruit le `wx.SingleChoiceDialog` avant de lire `GetSelection()`. | `Dlg/DLG_Saisie_location_demande.py` — `Dialog.Mesurer_distance` | `PORTAGE_PY3_WX` | blob `918ce8fd884d9ae6ae8f523a69bb849e2eee6eec` : `dlg.Destroy()` précède `dlg.GetSelection()`. | commit `dd93f248d3b15f548a365563ec342bf118a18765`, `test_location_request_wx_lifecycle_contract.py` | oui |
| 23 | Le traitement manuel des réservations portail détruit le dialogue avant de sauvegarder `dlg.ctrl_grille`. | `Dlg/DLG_Saisie_portail_demande.py` — `Dialog.Traitement_reservations` | `PORTAGE_PY3_WX` | blob `6921ce7cb14f2216c8c8f58f74b6270dba6f8a65` : `dlg.Destroy()` précède `Save_grille(dlg.ctrl_grille)`. | commit `c56294238c77c300c2bde397e8f6693be1ff7917`, `test_portail_destroy_contract.py` | oui |

## Compteur provisoire vérifié

Au stade de cette photographie :

- `HISTORIQUE_IVAN` démontré : **15** ;
- `PORTAGE_PY3_WX` démontré : **8** ;
- total de défauts/familles confirmés et sourcés dans ce tableau : **23** ;
- `FORK_REPENS` : à inventorier séparément à partir des PR/commits du fork ;
- `INDETERMINE` : tout défaut non encore comparé à une source upstream reste dans cette catégorie par défaut.

Ce compteur est volontairement conservateur : il ne compte pas les 530 anciens `except:` comme 530 bugs, ni les signaux d'audit non confirmés. Les autres défauts déjà corrigés dans le fork seront rétroclassés au fur et à mesure de la comparaison avec `Noethys/Noethys`.
