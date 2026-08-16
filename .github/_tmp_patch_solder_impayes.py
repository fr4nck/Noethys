from pathlib import Path

path = Path('noethys/Dlg/DLG_Solder_impayes.py')
text = path.read_text(encoding='utf-8')

text = text.replace('''        # Sauvegarde des règlements + ventilation
        for track in tracks :
''','''        # Sauvegarde des règlements + ventilation
        try:
            for track in tracks :
''',1)

start = text.index('            for track in tracks :')
end = text.index('        DB.Close()', start)
block = text[start:end]
lines = block.splitlines(True)
block = lines[0] + ''.join(('    ' + line if line.strip() else line) for line in lines[1:])
text = text[:start] + block + text[end:]

text = text.replace('''                    IDpayeur = DB.ReqInsert("payeurs", [("IDcompte_payeur", track.IDcompte_payeur), ("nom", nomTitulaire)])
''','''                    IDpayeur = DB.ReqInsert("payeurs", [("IDcompte_payeur", track.IDcompte_payeur), ("nom", nomTitulaire)], commit=False)
                    if IDpayeur is None:
                        raise RuntimeError(_(u"La création du payeur a échoué."))
                    dictPayeurs[track.IDcompte_payeur] = [{"nom": nomTitulaire, "IDpayeur": IDpayeur}]
''',1)

text = text.replace('''                IDreglement = DB.ReqInsert("reglements", listeDonnees)
''','''                IDreglement = DB.ReqInsert("reglements", listeDonnees, commit=False)
                if IDreglement is None:
                    raise RuntimeError(_(u"La création du règlement a échoué."))
''',1)

text = text.replace('''                    IDventilation = DB.ReqInsert("ventilation", listeDonnees)        
                    
        DB.Close() 
''','''                    IDventilation = DB.ReqInsert("ventilation", listeDonnees, commit=False)
                    if IDventilation is None:
                        raise RuntimeError(_(u"La ventilation du règlement a échoué."))

            DB.Commit()
        except Exception as err:
            try:
                DB.connexion.rollback()
            except Exception:
                pass
            DB.Close()
            dlg = wx.MessageDialog(self, _(u"Désolé, la création des règlements a échoué :\\n\\n%s\\n\\nAucun règlement du lot n'a été conservé.") % err, _(u"Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False
                    
        DB.Close() 
''',1)

path.write_text(text, encoding='utf-8')
