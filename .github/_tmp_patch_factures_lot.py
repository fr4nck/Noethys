from pathlib import Path

p = Path('noethys/Dlg/DLG_Factures_generation_selection.py')
s = p.read_text(encoding='utf-8')

old = '''                        if not DB.ReqMAJ("prestations", listeDonnees, "IDprestation", IDprestation, commit=False):\n                            raise RuntimeError(_(u"Le rattachement d'une prestation à la facture a échoué."))\n                DB.Commit()\n                \n                listeFacturesGenerees.append(IDfacture) \n'''
new = '''                        if not DB.ReqMAJ("prestations", listeDonnees, "IDprestation", IDprestation, commit=False):\n                            raise RuntimeError(_(u"Le rattachement d'une prestation à la facture a échoué."))\n\n                listeFacturesGenerees.append(IDfacture) \n'''
if old not in s:
    raise SystemExit('bloc commit par facture introuvable')
s = s.replace(old, new, 1)

old = '''                numero += 1\n                index += 1\n\n            DB.Close() \n            self.EcritStatusbar(u"")\n'''
new = '''                numero += 1\n                index += 1\n\n            # Le lot complet est validé uniquement si toutes les factures et\n            # tous leurs rattachements de prestations ont été enregistrés.\n            DB.Commit()\n            DB.Close() \n            self.EcritStatusbar(u"")\n'''
if old not in s:
    raise SystemExit('fin de boucle introuvable')
s = s.replace(old, new, 1)

old = '''        except Exception as err:\n            DB.Close()\n            dlgProgress.Destroy()\n'''
new = '''        except Exception as err:\n            try:\n                DB.connexion.rollback()\n            except Exception:\n                pass\n            DB.Close()\n            dlgProgress.Destroy()\n'''
if old not in s:
    raise SystemExit('bloc exception introuvable')
s = s.replace(old, new, 1)

s = '\n'.join(line.rstrip() for line in s.splitlines()) + '\n'
p.write_text(s, encoding='utf-8')
