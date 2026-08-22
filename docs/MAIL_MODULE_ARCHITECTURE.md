# Module Messagerie Noethys

> **Statut : architecture cible optionnelle.** Ce document décrit le contrat souhaité du module ; il ne doit pas être interprété comme la preuve que l'ensemble de cette messagerie est déjà livré dans `master`.

## Activation

La messagerie doit rester un module optionnel, **désactivé par défaut**.

Contrat attendu :

- si désactivé : pas de panneau, pas d'import inutile du client IMAP, pas de timer, pas de connexion réseau ;
- si activé : le panneau Messagerie peut être affiché/masqué par utilisateur comme les autres panneaux AUI ;
- l'activation ne doit pas modifier le comportement métier des installations qui n'utilisent pas la messagerie.

## Périmètre fonctionnel cible

- réception IMAP ; envoi via le moteur Noethys existant ou le fournisseur configuré ;
- Réception, Envoyés, Brouillons, Archives, Corbeille ;
- lecture texte/HTML, pièces jointes, répondre, répondre à tous, transférer ;
- recherche et fils de discussion ;
- rattachement automatique ou manuel aux entités Noethys :
  - familles ;
  - individus ;
  - associations/clubs ;
  - écoles ;
  - collectivités/mairies ;
  - organismes/institutions ;
  - entreprises/fournisseurs ;
- onglet/chronologie « Échanges » sur les fiches concernées lorsque le modèle métier correspondant est disponible.

## Contraintes

- aucun secret mail stocké en clair dans la base métier ;
- ne pas charger toute la boîte en mémoire : synchroniser d'abord les en-têtes et charger le contenu à la demande ;
- conserver l'historique Noethys actuel et ajouter une mémoire structurée des communications sans dupliquer inutilement les données ;
- réutiliser les modèles, critères de mailing et fonctionnalités d'envoi groupé existants ;
- aucune connexion réseau au démarrage si le module est désactivé ;
- les erreurs réseau ne doivent pas bloquer le lancement de Noethys ;
- respecter le design system commun et les règles wxPython ;
- ne pas introduire une dépendance fournisseur obligatoire dans le cœur historique.

## Positionnement par rapport au registre d'extensions

Si le registre d'extensions optionnelles est stabilisé, les fournisseurs de communication pourront constituer un premier cas d'usage. Le contrat métier de messagerie doit cependant rester indépendant d'un fournisseur particulier.

## Ordre de réalisation

La messagerie vient **après** la stabilisation des composants UI communs, du dashboard et des règles de stockage/secret. Elle ne doit pas retarder la qualification du socle Noethys lorsqu'elle est désactivée.
