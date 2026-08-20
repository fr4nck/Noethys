# Dashboard Noethys — trajectoire de modernisation

Le nouvel accueil doit devenir un tableau de bord opérationnel et modulaire.

## Panneaux cibles

1. **Aujourd'hui / Échéancier**
   - date et informations utiles du jour ;
   - météo et lever/coucher du soleil si Internet est disponible ;
   - prochaines échéances métier et périodes de vacances ;
   - alertes essentielles.

2. **Semaine équipe**
   - vue sur sept jours ;
   - animateurs et éducateurs sportifs ;
   - activités, sites, absences/remplacements et conflits éventuels ;
   - panneau dockable/redimensionnable.

3. **Messagerie** *(module optionnel, désactivé par défaut)*
   - réception IMAP et envoi SMTP existant ;
   - dossiers Réception, Envoyés, Brouillons, Archives, Corbeille ;
   - rattachement aux familles, individus, associations, écoles, collectivités, organismes et entreprises ;
   - aucune connexion, aucun timer et aucun panneau lorsque le module est désactivé.

4. **Alertes métier**
   - commandes de repas ;
   - capacités/réservations incohérentes ;
   - éléments nécessitant une action immédiate.

## Règles de layout

- Panneaux visibles et dockés au premier démarrage ; jamais `.Float()` par défaut.
- Séparations entre panneaux suffisamment visibles pour structurer l'écran.
- Pas de panneaux décoratifs ou de remplissage.
- La largeur disponible est réellement utilisée.
- Perspectives AUI versionnées ; une perspective d'une ancienne version ne doit pas être restaurée aveuglément.
- Masquer un panneau ne reconstruit pas le dashboard : masquer/détacher puis `Update()`.
