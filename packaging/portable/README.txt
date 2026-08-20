NOETHYS - MODE PORTABLE
=======================

La présence de ce dossier active le mode portable historique de Noethys.

Dans ce mode :
- Config.json, Customize.ini et journal.log restent dans ce dossier Portable ;
- les bases locales sont stockées dans Portable\Data ;
- les dossiers Temp, Updates, Lang, Sync et Extensions sont créés ici à la demande ;
- le profil Windows (AppData) n'est pas utilisé pour ces données Noethys.

DIAGNOSTIC / DEBUG
------------------
En cas de problème, les fichiers utiles sont dans ce même dossier Portable :
- journal.log : déroulement général + contexte technique de chaque session ;
- noethys_crash.log : exceptions Python/wx/threads et erreurs fatales ;
- noethys_hang.log : créé si l'interface wx ne répond plus pendant environ 30 secondes.

Le diagnostic enregistre la version du build, Python/wx, le thread concerné et les
piles techniques. Il ne collecte pas les mots de passe, la configuration complète
ni le contenu des fiches métiers.

Pour signaler un crash ou un gel reproductible, transmettre si possible les trois
fichiers ci-dessus sans les modifier. noethys_hang.log peut n'exister que lorsqu'un
gel a réellement été détecté.

Pour une recette avec une base existante : travaillez uniquement sur une COPIE de la base.
Ne déplacez jamais ici votre unique base de production pour tester une RC.

Pour revenir au comportement utilisateur classique, utilisez une distribution sans dossier Portable ; ne supprimez pas ce dossier d'une installation qui contient déjà sa configuration ou ses bases sans les sauvegarder auparavant.
