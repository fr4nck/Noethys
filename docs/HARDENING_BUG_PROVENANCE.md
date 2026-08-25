# Provenance des bugs confirmés — passe de hardening

Ce document accompagne #97/#98 et prépare le lot upstream #99.

Règles :

- `HISTORIQUE_IVAN` : le motif fautif est attesté dans `Noethys/Noethys` avant notre fork ;
- `PORTAGE_PY3_WX` : le motif historique est attesté upstream mais devient invalide avec le runtime/API moderne ;
- `FORK_REPENS` : défaut introduit par notre fork ;
- `INDETERMINE` : preuve insuffisante ; aucune attribution par intuition.

Les références `upstream` ci-dessous pointent vers le `master` public de `Noethys/Noethys` observé pendant la passe. Le SHA de blob permet de figer la preuve même si l'upstream évolue ensuite.

| # | Défaut confirmé | Fichier / fonction | Provenance | Preuve upstream | Correction / contrat dans notre fork | Upstream applicable |
|---|---|---|---|---|---|---|
| 1 | Le règlement d'une facture depuis une fiche famille perd l'`IDfacture` exact et appelle `ReglerFacture()` sans argument. | `Ctrl/CTRL_Numfacture.py` — `CTRL.ReglerFacture` | `HISTORIQUE_IVAN` | `Noethys/Noethys`, blob `4033decc3cb0603bac064f933aeda950c374af74` : branche `IDfamille` avec `self.GetGrandParent().ReglerFacture()` alors que le chemin voisin transmet `IDfacture`. | commit `b55df62ccc3d458d134475e0f0345e8ffa2d087a`, `test_numfacture_forwarding_contract.py` | oui |
| 2 | Une base individus initialement vide peut faire retourner `None` à `GetTracks()` puis propager `None` comme données de liste. | `Ol/OL_Individus.py` — `GetTracks` / `MAJ` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : retour `None` dès que `dictIndividus == self.dictIndividus`, y compris au premier chargement vide. | #98, `test_empty_initial_database_does_not_turn_list_data_into_none` | oui |
| 3 | Le dialogue de création de famille n'est pas détruit après `ShowModal()`. | `Ol/OL_Individus.py` — `Ajouter` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : `ShowModal()` suivi directement de la MAJ, sans `dlg.Destroy()`. | #98, `test_new_family_dialog_is_destroyed` | oui |
| 4 | Un code-barres individu invalide réinitialise `IDfamille` au lieu d'`IDindividu`. | `Ol/OL_Individus.py` — `BarreRecherche.OnText` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : `except: IDfamille = None` dans la branche du code `I...`. | #98, `test_invalid_individual_barcode_resets_individual_id` | oui |
| 5 | Après lecture d'un code-barres famille, `BarreRecherche` peut appeler `self.MAJ()` alors que cette classe ne définit pas cette méthode. | `Ol/OL_Individus.py` — `BarreRecherche.OnText` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : branche `else: self.MAJ()`. | #98, `test_individual_search_barcode_contract.py` | oui |
| 6 | L'anti-rebond RFID ne bloque pas une deuxième lecture du même badge : seul le cas différent met à jour `dernierRFID`, puis le traitement continue dans tous les cas. | `Ol/OL_Individus.py` — `OnTimerRFID` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : `if self.dernierRFID != IDbadge: self.dernierRFID = IDbadge` sans retour pour un doublon. | #98, `test_rfid_duplicate_badge_is_rejected_before_database_lookup` | oui |
| 7 | Le callback RFID arrête son timer puis bloque la boucle wx avec `time.sleep(2)` ; une exception avant le `Start()` final peut laisser la détection coupée. | `Ol/OL_Individus.py` — `OnTimerRFID` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : `timer_rfid.Stop()`, `time.sleep(2)`, `Start()` dans un `try` dont l'exception est silencieuse. | #98, `test_rfid_handler_does_not_block_ui_or_stop_its_timer` | oui |
| 8 | Un individu trouvé par RFID mais absent de la liste filtrée provoque un `KeyError` sur `dictTracks`. | `Ol/OL_Individus.py` — `OnTimerRFID` | `HISTORIQUE_IVAN` | blob `ec13da25faaef73a43902dbea367d31b49be061d` : `track = self.dictTracks[IDindividu]`. | #98, `test_rfid_filtered_individual_does_not_raise_key_error` | oui |
| 9 | Une action de synchronisation déjà marquée en anomalie construit `texte` avec `resultat` avant toute affectation pour le premier track, ou avec la valeur du track précédent. | `Dlg/DLG_Synchronisation_donnees.py` — `Traitement.run` | `HISTORIQUE_IVAN` | blob `91593e4a0ac48a5cdd053f70e55a6cfa1434b4fc` : `texte = track.detail + ... + resultat` dans la branche `track.anomalie`. | #98, `test_anomaly_branch_does_not_read_previous_result` | oui |
| 10 | Avec exactement un mémo journalier existant, la synchronisation le considère absent et peut insérer un doublon au lieu de le modifier. | `Dlg/DLG_Synchronisation_donnees.py` — `Traitement.run` | `HISTORIQUE_IVAN` | blob `91593e4a0ac48a5cdd053f70e55a6cfa1434b4fc` : test `if len(listeMemos) > 1` au lieu de reconnaître le cas `1`. | #98, `test_single_existing_memo_is_updated_instead_of_duplicated` | oui |
| 11 | L'état du thread est testé avec l'ancienne API `Thread.isAlive()` ; sur Python moderne l'`AttributeError` est interprété comme « aucun traitement en cours ». | `Dlg/DLG_Synchronisation_donnees.py` — `Dialog_Traitement.Fermer` | `PORTAGE_PY3_WX` | blob `91593e4a0ac48a5cdd053f70e55a6cfa1434b4fc` : `self.traitement.isAlive()` puis `except AttributeError: TraitmentEnCours = False`. | #98, `test_thread_state_uses_python3_api` | oui |
| 12 | Si la préparation/listen du serveur Nomadhys échoue, le code continue, peut lire `port` avant affectation, annoncer « serveur prêt » et lancer le reactor. | `Ctrl/CTRL_Serveur_nomade.py` — `StartServer` | `HISTORIQUE_IVAN` | blob `7324da32e8a517e0d54792d7efafcc402147660a` : l'`except` du bloc factory/listen ne retourne pas ; le code utilise ensuite `port` et `reactor.run()`. | #98, `test_nomadhys_aborts_before_ready_state_when_listen_setup_fails` | oui |
| 13 | Si la requête des avatars échoue, `listeAvatars` n'est jamais définie puis est itérée immédiatement après. | `Utils/UTILS_Utilisateurs.py` — `GetListeUtilisateurs` | `HISTORIQUE_IVAN` | blob `4fd36e2d268f0f09cd12848e45183b94f0be0037` : affectation de `listeAvatars` seulement dans le `try`, `except: pass`, puis boucle `for ... in listeAvatars`. | #98, `test_avatar_query_failure_has_an_empty_fallback` | oui |
| 14 | Si la lecture de l'organisateur échoue avant l'affectation, `origine` est utilisée ensuite sans être définie. | `Utils/UTILS_Stats_individus.py` — `GetDictVilles` | `HISTORIQUE_IVAN` | blob `0acf6ee04ddad668942f92c5e7aae0c33312cbde` : `origine` n'est définie que dans le `try`, `except: pass`, puis `key != origine` hors du bloc. | #98, `test_stats_distance_origin_is_always_defined` | oui |
| 15 | La procédure A9061 masque silencieusement un échec d'`UPDATE documents ...` / `Commit()`, ce qui peut faire croire que la procédure s'est terminée correctement. | `Utils/UTILS_Procedures.py` — `A9061` | `HISTORIQUE_IVAN` | blob `f8eedb72fa263085ae6e04d042ee0dd797a8bfee` : mutation/commit dans `try` suivi de `except: pass`. | #98, audit `silent_business_mutation`, `test_procedure_a9061_hardening.py` + contrat zéro HIGH | oui |
| 16 | Lors de la migration des anciennes bases locales, l'échec du renommage en `_archive.dat` est ignoré. La base source reste alors éligible à une nouvelle copie au démarrage suivant et peut réécraser la copie migrée. | `Utils/UTILS_Fichiers.py` — `DeplaceFichiers` | `HISTORIQUE_IVAN` | blob `efa66625c5dc1cc17ef32f8bb62c8c9494010dec` : `os.rename(...)` entouré d'un `except: pass` après la copie de la base. | #98, `os.replace(source, archive)`, audit `silent_filesystem_mutation`, `test_file_migration_hardening.py` | oui |

## Compteur provisoire vérifié

Au stade de cette photographie :

- `HISTORIQUE_IVAN` démontré : **15** ;
- `PORTAGE_PY3_WX` démontré : **1** ;
- `FORK_REPENS` : à inventorier séparément à partir des PR/commits du fork ;
- `INDETERMINE` : tout défaut non encore comparé à une source upstream reste dans cette catégorie par défaut.

Ce compteur est volontairement conservateur : il ne compte pas les 530 anciens `except:` comme 530 bugs, ni les signaux d'audit non confirmés. Les autres défauts déjà corrigés dans le fork seront rétroclassés au fur et à mesure de la comparaison avec `Noethys/Noethys`.
