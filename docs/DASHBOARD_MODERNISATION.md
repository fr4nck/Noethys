# Dashboard Noethys — trajectoire de modernisation

> **Statut : cible UI**, à appliquer progressivement. Ce document décrit le dashboard souhaité ; il ne signifie pas que chaque panneau ci-dessous est déjà intégré dans `master`.
>
> Références communes : `DESIGN_SYSTEM_UI_UX.md`, `WXPYTHON_UI_RULES.md` et `IMPLEMENTATION_ORDER.md`.

Le nouvel accueil doit devenir un tableau de bord opérationnel et modulaire, sans sacrifier la densité métier ni imposer des dépendances réseau.

## Panneaux cibles

1. **Aujourd'hui / Échéancier**
   - date et informations utiles du jour ;
   - météo et lever/coucher du soleil uniquement si Internet est disponible et si cette fonction est activée ;
   - prochaines échéances métier et périodes de vacances ;
   - alertes essentielles.

2. **Semaine équipe**
   - vue sur sept jours ;
   - animateurs et éducateurs sportifs ;
   - activités, sites, absences/remplacements et conflits éventuels ;
   - panneau dockable/redimensionnable ;
   - respecter la frontière : Noethys expose le besoin/planning métier, PMSL-Équipe reste la source RH des affectations lorsque l'intégration est utilisée.

3. **Messagerie** *(module optionnel, désactivé par défaut)*
   - réception IMAP et envoi via le moteur existant ou le fournisseur configuré ;
   - dossiers Réception, Envoyés, Brouillons, Archives, Corbeille ;
   - rattachement aux familles, individus, associations, écoles, collectivités, organismes et entreprises ;
   - aucune connexion, aucun timer et aucun panneau lorsque le module est désactivé.

4. **Alertes métier**
   - commandes de repas ;
   - capacités/réservations incohérentes ;
   - éléments nécessitant une action immédiate ;
   - ne pas dupliquer une règle métier déjà portée par un autre moteur Noethys.

## Règles de layout

- panneaux visibles et dockés au premier démarrage ; jamais `.Float()` par défaut ;
- séparations entre panneaux suffisamment visibles pour structurer l'écran ;
- pas de panneaux décoratifs ou de remplissage ;
- la largeur disponible est réellement utilisée ;
- perspectives AUI versionnées ; une perspective d'une ancienne version ne doit pas être restaurée aveuglément ;
- masquer un panneau ne reconstruit pas le dashboard : masquer/détacher puis `Update()` ;
- aucune hauteur/largeur historique rigide ne doit devenir un nouveau contrat d'interface ;
- fonctionnement correct en clair/sombre et aux échelles courantes ;
- les fonctions Internet restent optionnelles et ne bloquent jamais l'accueil.

## Ordre de réalisation

Le dashboard ne doit pas devenir un laboratoire de styles locaux. Avant d'y ajouter de nouveaux panneaux :

1. stabiliser les composants communs ;
2. stabiliser scaling et thème ;
3. stabiliser le docking AUI ;
4. ajouter uniquement les panneaux ayant une valeur métier démontrée.
