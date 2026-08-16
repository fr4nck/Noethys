from pathlib import Path

path = Path('noethys/Dlg/DLG_Saisie_lot_cotisations.py')
text = path.read_text(encoding='utf-8')

old = '''            IDcotisation = DB.ReqInsert("cotisations", listeDonnees)

            # Sauvegarde de la prestation
'''
new = '''            IDcotisation = DB.ReqInsert("cotisations", listeDonnees, commit=False)
            if IDcotisation is None:
                raise RuntimeError(_(u"La création de la cotisation a échoué."))

            # Sauvegarde de la prestation
'''
assert old in text
text = text.replace(old, new, 1)

old = '''                IDprestation = DB.ReqInsert("prestations", listeDonnees)

                # Insertion du IDprestation dans la cotisation
                DB.ReqMAJ("cotisations", [("IDprestation", IDprestation), ], "IDcotisation", IDcotisation)
'''
new = '''                IDprestation = DB.ReqInsert("prestations", listeDonnees, commit=False)
                if IDprestation is None:
                    raise RuntimeError(_(u"La création de la prestation associée à la cotisation a échoué."))

                # Insertion du IDprestation dans la cotisation
                if not DB.ReqMAJ("cotisations", [("IDprestation", IDprestation), ], "IDcotisation", IDcotisation, commit=False):
                    raise RuntimeError(_(u"Le rattachement de la prestation à la cotisation a échoué."))

            DB.Commit()
'''
assert old in text
text = text.replace(old, new, 1)

start_marker = '        for track in liste_tracks :\n'
end_marker = '        DB.Close()\n'
start = text.index(start_marker)
end = text.index(end_marker, start)
block = text[start:end]
indented_block = ''.join(('    ' + line if line.strip() else line) for line in block.splitlines(True))
text = text[:start] + '        try:\n' + indented_block + text[end:]

old = '''        DB.Close()
        dlgprogress.Destroy()

        # Succès
'''
new = '''        except Exception as err:
            try:
                DB.connexion.rollback()
            except Exception:
                pass
            DB.Close()
            dlgprogress.Destroy()
            dlg = wx.MessageDialog(self, _(u"Désolé, la génération des cotisations a échoué :\\n\\n%s") % err, _(u"Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        DB.Close()
        dlgprogress.Destroy()

        # Succès
'''
assert old in text
text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
