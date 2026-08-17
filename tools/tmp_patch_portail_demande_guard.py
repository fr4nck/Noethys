from pathlib import Path
p=Path('noethys/Dlg/DLG_Saisie_portail_demande.py')
s=p.read_text(encoding='utf-8')
old='''            DB.ExecuterReq(req)\n            IDcompte_bancaire = DB.ResultatReq()[0][0]\n            num_piece = "auth_num-" + self.dict_parametres["numauto"]\n'''
new='''            DB.ExecuterReq(req)\n            resultat_compte = DB.ResultatReq()\n            if resultat_compte:\n                IDcompte_bancaire = resultat_compte[0][0]\n            num_piece = "auth_num-" + self.dict_parametres["numauto"]\n'''
if old not in s:
    raise SystemExit('bloc TIPI introuvable')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
