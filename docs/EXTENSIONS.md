# Extensions Noethys Desktop

## Objectif

Permettre d'étendre progressivement Noethys Desktop sans transformer chaque intégration ou besoin local en dépendance du cœur historique.

Le socle initial est volontairement minimal : un registre explicite d'extensions et de capacités. Aucun chargement automatique de code tiers n'est activé.

## Principes

- le cœur reste fonctionnel sans extension ;
- une extension s'enregistre explicitement ;
- aucun parcours automatique de dossiers ni import arbitraire n'est réalisé ;
- les capacités servent à rechercher un service sans dépendre de son fournisseur ;
- une extension ne doit pas modifier directement une autre extension ;
- les dépendances entre extensions doivent rester exceptionnelles et explicites ;
- les migrations de base éventuelles doivent être versionnées et réversibles lorsque raisonnable ;
- les données métier existantes restent sous l'autorité du moteur Noethys concerné.

## Exemple

```python
from Extensions import Extension, get_registry

registry = get_registry()
registry.register(
    Extension(
        "communication.sms.example",
        "Passerelle SMS exemple",
        version="1.0",
        capabilities=("sms.send", "sms.status"),
        factory=build_sms_provider,
    )
)
```

Le consommateur recherche ensuite une capacité plutôt qu'un fournisseur codé en dur :

```python
providers = get_registry().by_capability("sms.send")
```

## Capacités envisagées

La liste n'est pas encore un contrat stable. Les premiers domaines candidats sont :

- `email.send` / `email.status` ;
- `sms.send` / `sms.status` ;
- `export.*` pour les exports spécifiques ;
- `report.*` pour les statistiques et rapports ;
- `integration.dolibarr` ;
- `integration.helloasso` ;
- `integration.piwigo` ;
- connecteurs et synchronisations externes.

## Ce que ce socle ne fait pas encore

- découverte automatique de plugins ;
- installation/désinstallation depuis l'interface ;
- téléchargement de code ;
- permissions propres aux extensions ;
- migrations de schéma pilotées par extension ;
- hooks UI ;
- hooks métier génériques.

Ces fonctions ne seront ajoutées qu'en réponse à des besoins concrets. Le registre sert d'abord à découpler proprement les futurs fournisseurs et intégrations du cœur de Noethys.
