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

old = '''        index = 1
        for track in liste_tracks :

            dlgprogress.Update(index, _(u"Génération de la cotisation %d sur %d") % (index, len(liste_tracks)))
'''
new = '''        index = 1
        try:
            for track in liste_tracks :

                dlgprogress.Update(index, _(u"Génération de la cotisation %d sur %d") % (index, len(liste_tracks)))
'''
assert old in text
text = text.replace(old, new, 1)

# Indent the loop body until DB.Close(), preserving the newly inserted try.
start = text.index('            for track in liste_tracks :')
end = text.index('        DB.Close()', start)
block = text[start:end]
lines = block.splitlines(True)
# first line already correctly indented inside try; everything after it needs +4 spaces
block2 = lines[0] + ''.join(('    ' + line if line.strip() else line) for line in lines[1:])
text = text[:start] + block2 + text[end:]

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
