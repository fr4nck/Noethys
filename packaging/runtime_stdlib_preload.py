# -*- coding: utf-8 -*-
"""Précharge les modules stdlib qui entrent en collision avec le bundle wx plat.

Le layout historique de Noethys place les modules wxPython à côté de l'EXE.
Une fois ``wx`` chargé, un ``import html`` tardif peut alors être résolu vers
``wx/html.py`` comme module de premier niveau. Ce fichier contient des imports
relatifs et échoue dans ce contexte (``attempted relative import with no known
parent package``).

Le préchargement de la stdlib a lieu avant tout hook qui importe ``wx`` et fixe
``sys.modules['html']`` sur le paquet Python attendu par ``CTRL_Bandeau``.
"""

import html as _stdlib_html  # noqa: F401  -- préchargement volontaire
