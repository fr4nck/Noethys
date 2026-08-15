#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 1) DLG_Portail_config.py : conditions codées en dur -> prédicats lambda
path = ROOT / "noethys/Dlg/DLG_Portail_config.py"
text = path.read_text(encoding="utf-8")
start = text.index("        liste_conditions = [")
end = text.index("        # Vérifie les conditions d'affichage", start)
block = text[start:end]
repls = {
    '"p(\'hebergement_type\') == 0"': "lambda: p('hebergement_type') == 0",
    '"p(\'hebergement_type\') == 1"': "lambda: p('hebergement_type') == 1",
    '"p(\'hebergement_type\') == 2"': "lambda: p('hebergement_type') == 2",
    '"p(\'db_type\') == 1"': "lambda: p('db_type') == 1",
    '"p(\'serveur_type\') == 0"': "lambda: p('serveur_type') == 0",
    '"p(\'serveur_type\') == 1"': "lambda: p('serveur_type') == 1",
    '"p(\'paiement_ligne_actif\') == True"': "lambda: p('paiement_ligne_actif') is True",
    '"p(\'paiement_ligne_systeme\') == 3"': "lambda: p('paiement_ligne_systeme') == 3",
    '"p(\'paiement_ligne_systeme\') == 1"': "lambda: p('paiement_ligne_systeme') == 1",
}
for old, new in repls.items():
    block = block.replace(old, new)
text = text[:start] + block + text[end:]
old = "            if eval(condition) == True :"
new = "            if condition():"
if old not in text:
    raise SystemExit("eval portail absent")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("DLG_Portail_config.py: eval supprimé")

# 2) DLG_Saisie_lot_ouvertures2.py : constructeurs d'onglets -> callables
path = ROOT / "noethys/Dlg/DLG_Saisie_lot_ouvertures2.py"
text = path.read_text(encoding="utf-8")
old_pages = '''        self.listePages = [\n            (_(u"dates"), _(u"Dates"), _(u"Page_dates(self, afficheElements=afficheElements, IDactivite=IDactivite)"), "Calendrier_jour.png"),\n            (_(u"evenements"), _(u"Evènements"), _(u"Page_evenements(self, IDactivite=IDactivite, ctrl_calendrier=ctrl_calendrier)"), "Evenement.png"),\n        ]'''
new_pages = '''        self.listePages = [\n            (_(u"dates"), _(u"Dates"), lambda: Page_dates(self, afficheElements=afficheElements, IDactivite=IDactivite), "Calendrier_jour.png"),\n            (_(u"evenements"), _(u"Evènements"), lambda: Page_evenements(self, IDactivite=IDactivite, ctrl_calendrier=ctrl_calendrier), "Evenement.png"),\n        ]'''
if old_pages not in text:
    raise SystemExit("listePages ouvertures absente")
text = text.replace(old_pages, new_pages, 1)
old = 'setattr(self, "page%s" % index, eval(ctrlPage))'
new = 'setattr(self, "page%s" % index, ctrlPage())'
if old not in text:
    raise SystemExit("eval ouvertures absent")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("DLG_Saisie_lot_ouvertures2.py: eval supprimé")
