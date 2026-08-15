#!/usr/bin/env python3
from pathlib import Path

path = Path('noethys/Ctrl/CTRL_Saisie_transport.py')
text = path.read_text(encoding='utf-8')

repls = {
    '"CTRL_Compagnies(self, categorie=\'bus\')"': 'lambda parent=self: CTRL_Compagnies(parent, categorie=\'bus\')',
    '"CTRL_Compagnies(self, categorie=\'car\')"': 'lambda parent=self: CTRL_Compagnies(parent, categorie=\'car\')',
    '"CTRL_Compagnies(self, categorie=\'navette\')"': 'lambda parent=self: CTRL_Compagnies(parent, categorie=\'navette\')',
    '"CTRL_Compagnies(self, categorie=\'taxi\')"': 'lambda parent=self: CTRL_Compagnies(parent, categorie=\'taxi\')',
    '"CTRL_Compagnies(self, categorie=\'train\')"': 'lambda parent=self: CTRL_Compagnies(parent, categorie=\'train\')',
    '"CTRL_Compagnies(self, categorie=\'avion\')"': 'lambda parent=self: CTRL_Compagnies(parent, categorie=\'avion\')',
    '"CTRL_Compagnies(self, categorie=\'bateau\')"': 'lambda parent=self: CTRL_Compagnies(parent, categorie=\'bateau\')',
    '"CTRL_Compagnies(self, categorie=\'metro\')"': 'lambda parent=self: CTRL_Compagnies(parent, categorie=\'metro\')',
    '"CTRL_Lignes(self, categorie=\'bus\')"': 'lambda parent=self: CTRL_Lignes(parent, categorie=\'bus\')',
    '"CTRL_Lignes(self, categorie=\'car\')"': 'lambda parent=self: CTRL_Lignes(parent, categorie=\'car\')',
    '"CTRL_Lignes(self, categorie=\'navette\')"': 'lambda parent=self: CTRL_Lignes(parent, categorie=\'navette\')',
    '"CTRL_Lignes(self, categorie=\'bateau\')"': 'lambda parent=self: CTRL_Lignes(parent, categorie=\'bateau\')',
    '"CTRL_Lignes(self, categorie=\'metro\')"': 'lambda parent=self: CTRL_Lignes(parent, categorie=\'metro\')',
    '"CTRL_Lignes(self, categorie=\'pedibus\')"': 'lambda parent=self: CTRL_Lignes(parent, categorie=\'pedibus\')',
    '"CTRL_Numero(self, categorie=\'avion\')"': 'lambda parent=self: CTRL_Numero(parent, categorie=\'avion\')',
    '"CTRL_Numero(self, categorie=\'train\')"': 'lambda parent=self: CTRL_Numero(parent, categorie=\'train\')',
    '"CTRL_Details(self)"': 'lambda parent=self: CTRL_Details(parent)',
    '"CTRL_Observations(self)"': 'lambda parent=self: CTRL_Observations(parent)',
    '"CTRL_DateHeure(self)"': 'lambda parent=self: CTRL_DateHeure(parent)',
    '"CTRL_Arrets(self, categorie=\'bus\')"': 'lambda parent=self: CTRL_Arrets(parent, categorie=\'bus\')',
    '"CTRL_Arrets(self, categorie=\'car\')"': 'lambda parent=self: CTRL_Arrets(parent, categorie=\'car\')',
    '"CTRL_Arrets(self, categorie=\'navette\')"': 'lambda parent=self: CTRL_Arrets(parent, categorie=\'navette\')',
    '"CTRL_Arrets(self, categorie=\'bateau\')"': 'lambda parent=self: CTRL_Arrets(parent, categorie=\'bateau\')',
    '"CTRL_Arrets(self, categorie=\'metro\')"': 'lambda parent=self: CTRL_Arrets(parent, categorie=\'metro\')',
    '"CTRL_Arrets(self, categorie=\'pedibus\')"': 'lambda parent=self: CTRL_Arrets(parent, categorie=\'pedibus\')',
    '"CTRL_Lieux(self, categorie=\'gare\')"': 'lambda parent=self: CTRL_Lieux(parent, categorie=\'gare\')',
    '"CTRL_Lieux(self, categorie=\'aeroport\')"': 'lambda parent=self: CTRL_Lieux(parent, categorie=\'aeroport\')',
    '"CTRL_Lieux(self, categorie=\'port\')"': 'lambda parent=self: CTRL_Lieux(parent, categorie=\'port\')',
    '"CTRL_Localisation(self)"': 'lambda parent=self: CTRL_Localisation(parent)',
}

for old, new in repls.items():
    if old not in text:
        raise SystemExit(f'motif absent: {old}')
    text = text.replace(old, new)

old = '            nomControle = dictControle["ctrl"]\n            ctrl = eval(nomControle)'
new = '            constructeur = dictControle["ctrl"]\n            ctrl = constructeur()'
if old not in text:
    raise SystemExit('bloc eval transport absent')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('CTRL_Saisie_transport.py: eval supprimé')
