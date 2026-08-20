# Module Messagerie Noethys

## Activation

La messagerie est un module optionnel, désactivé par défaut.

- `module_messagerie_actif = False` par défaut.
- Si désactivé : pas de panneau, pas d'import du client IMAP, pas de timer, pas de connexion réseau.
- Si activé : le panneau Messagerie peut être affiché/masqué par utilisateur comme les autres panneaux AUI.

## Périmètre fonctionnel cible

- Réception IMAP ; envoi via le moteur SMTP Noethys existant.
- Réception, Envoyés, Brouillons, Archives, Corbeille.
- Lecture texte/HTML, pièces jointes, répondre, répondre à tous, transférer.
- Recherche et fils de discussion.
- Rattachement automatique ou manuel aux entités Noethys :
  - familles ;
  - individus ;
  - associations/clubs ;
  - écoles ;
  - collectivités/mairies ;
  - organismes/institutions ;
  - entreprises/fournisseurs.
- Onglet/chronologie « Échanges » sur les fiches concernées.

## Contraintes

- Aucun secret mail stocké en clair dans la base métier.
- Ne pas charger toute la boîte en mémoire : synchroniser d'abord les en-têtes et charger le contenu à la demande.
- Conserver l'historique Noethys actuel et ajouter une mémoire structurée des communications.
- Réutiliser les modèles, critères de mailing et fonctionnalités d'envoi groupé existants.
