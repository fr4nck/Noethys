#!/usr/bin/env python3
from pathlib import Path

path = Path('noethys/Dlg/DLG_Saisie_tarification.py')
text = path.read_text(encoding='utf-8')
replacements = {
    '("generalites", _(u"Généralités"), "CTRL_Tarification_generalites.Panel(self, IDactivite=IDactivite, IDtarif=IDtarif, cacher_dates=cacher_dates)", "Information.png")': '("generalites", _(u"Généralités"), lambda: CTRL_Tarification_generalites.Panel(self, IDactivite=IDactivite, IDtarif=IDtarif, cacher_dates=cacher_dates), "Information.png")',
    '("conditions", _(u"Conditions d\'application"), "CTRL_Tarification_conditions.Panel(self, IDactivite=IDactivite, IDtarif=IDtarif)", "Filtre.png")': '("conditions", _(u"Conditions d\'application"), lambda: CTRL_Tarification_conditions.Panel(self, IDactivite=IDactivite, IDtarif=IDtarif), "Filtre.png")',
    '("type", _(u"Type de tarif"), "CTRL_Tarification_type.Panel(self, IDactivite=IDactivite, IDtarif=IDtarif, nouveauTarif=nouveauTarif)", "Outils.png")': '("type", _(u"Type de tarif"), lambda: CTRL_Tarification_type.Panel(self, IDactivite=IDactivite, IDtarif=IDtarif, nouveauTarif=nouveauTarif), "Outils.png")',
    '("calcul", _(u"Calcul du tarif"), "CTRL_Tarification_calcul.Panel(self, IDactivite=IDactivite, IDtarif=IDtarif, track_tarif=track_tarif)", "Calculatrice.png")': '("calcul", _(u"Calcul du tarif"), lambda: CTRL_Tarification_calcul.Panel(self, IDactivite=IDactivite, IDtarif=IDtarif, track_tarif=track_tarif), "Calculatrice.png")',
    'ctrl = eval(ctrl)': 'ctrl = ctrl()',
}
for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f'motif absent: {old}')
    text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('DLG_Saisie_tarification.py corrigé')
