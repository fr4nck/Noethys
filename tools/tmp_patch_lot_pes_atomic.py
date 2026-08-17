from pathlib import Path

p = Path('noethys/Ol/OL_PES_pieces.py')
s = p.read_text(encoding='utf-8')
start = s.index('    def Sauvegarde(self, IDlot=None, datePrelevement=None, IDcompte=None, IDmode=None):')
end = s.index('\n\n\n\n\n# -------------------------------------------------------------------------------------------------------------------------------------------', start)
old = s[start:end]
new = '''    def Sauvegarde(self, IDlot=None, datePrelevement=None, IDcompte=None, IDmode=None, DB=None, commit=True):
        """ Sauvegarde des données. Une DB externe permet d'englober lot, pièces et règlements dans une même transaction. """
        DB_externe = DB is not None
        if DB is None:
            DB = GestionDB.DB()

        ok = True
        listeMAJPieces = []

        # Ajouts et modifications
        for track in self.GetObjects():
            listeDonnees = [
                ("IDlot", IDlot),
                ("IDfamille", track.IDfamille),
                ("prelevement", track.prelevement),
                ("prelevement_iban", track.prelevement_iban),
                ("prelevement_bic", track.prelevement_bic),
                ("prelevement_rum", track.prelevement_rum),
                ("prelevement_date_mandat", track.prelevement_date_mandat),
                ("prelevement_IDmandat", track.prelevement_IDmandat),
                ("prelevement_sequence", track.prelevement_sequence),
                ("prelevement_titulaire", track.prelevement_titulaire),
                ("prelevement_statut", track.prelevement_statut),
                ("titulaire_helios", track.titulaire_helios),
                ("tiers_solidaire", track.tiers_solidaire),
                ("type", track.type),
                ("IDfacture", track.IDfacture),
                ("numero", track.numero),
                ("libelle", track.libelle),
                ("montant", track.montant),
            ]

            if track.etat == "ajout":
                IDpiece = DB.ReqInsert("pes_pieces", listeDonnees, commit=False)
                if IDpiece is None:
                    ok = False
                    break
                listeMAJPieces.append((track, IDpiece))
            elif track.etat == "modif":
                if not DB.ReqMAJ("pes_pieces", listeDonnees, "IDpiece", track.IDpiece, commit=False):
                    ok = False
                    break

        # Suppressions : dépendances avant la pièce
        if ok:
            for track in self.listeSuppressions:
                if track.IDreglement is not None:
                    if not DB.ReqDEL("ventilation", "IDreglement", track.IDreglement, commit=False):
                        ok = False
                        break
                    if not DB.ReqDEL("reglements", "IDreglement", track.IDreglement, commit=False):
                        ok = False
                        break
                if track.IDpiece is not None:
                    if not DB.ReqDEL("pes_pieces", "IDpiece", track.IDpiece, commit=False):
                        ok = False
                        break

        # Les règlements partagent la même transaction
        if ok:
            ok = self.SauvegardeReglements(date=datePrelevement, IDcompte=IDcompte, IDmode=IDmode, DB=DB, commit=False)

        if not ok:
            try:
                DB.connexion.rollback()
            except Exception:
                pass
            if not DB_externe:
                DB.Close()
            return False

        if commit:
            DB.Commit()
        if not DB_externe:
            DB.Close()

        for track, IDpiece in listeMAJPieces:
            track.IDpiece = IDpiece
            self.RefreshObject(track)
        return True

    def SauvegardeReglements(self, date=None, IDcompte=None, IDmode=None, DB=None, commit=True):
        """ Sauvegarde règlements et ventilations, éventuellement dans une transaction externe. """
        DB_externe = DB is not None
        if DB is None:
            DB = GestionDB.DB()
        ok = True
        listeMAJTracks = []

        # Recherche des payeurs
        req = """SELECT IDpayeur, IDcompte_payeur, nom
        FROM payeurs;"""
        if not DB.ExecuterReq(req):
            ok = False
        listeDonnees = DB.ResultatReq() if ok else []
        dictPayeurs = {}
        for IDpayeur, IDcompte_payeur, nom in listeDonnees:
            if IDcompte_payeur not in dictPayeurs:
                dictPayeurs[IDcompte_payeur] = []
            dictPayeurs[IDcompte_payeur].append({"nom": nom, "IDpayeur": IDpayeur})

        listeIDfactures = [track.IDfacture for track in self.GetObjects() if track.IDfacture is not None]
        if len(listeIDfactures) == 0:
            conditionFactures = "()"
        elif len(listeIDfactures) == 1:
            conditionFactures = "(%d)" % listeIDfactures[0]
        else:
            conditionFactures = str(tuple(listeIDfactures))

        req = """SELECT
        prestations.IDprestation, prestations.IDcompte_payeur, prestations.montant,
        prestations.IDfacture, SUM(ventilation.montant) AS montant_ventilation
        FROM prestations
        LEFT JOIN ventilation ON prestations.IDprestation = ventilation.IDprestation
        WHERE prestations.IDfacture IN %s
        GROUP BY prestations.IDprestation
        ;""" % conditionFactures
        if ok and not DB.ExecuterReq(req):
            ok = False
        listeDonnees = DB.ResultatReq() if ok else []

        dictFactures = {}
        dictAventiler = {}
        for IDprestation, IDcompte_payeur, montant, IDfacture, ventilation in listeDonnees:
            if ventilation is None:
                ventilation = 0.0
            montant = decimal.Decimal(montant)
            ventilation = decimal.Decimal(ventilation)
            aventiler = montant - ventilation
            if aventiler != decimal.Decimal(0.0):
                dictFactures.setdefault(IDfacture, []).append({"IDprestation": IDprestation, "IDcompte_payeur": IDcompte_payeur, "montant": montant, "ventilation": ventilation, "aventiler": aventiler})
                dictAventiler[IDfacture] = dictAventiler.get(IDfacture, decimal.Decimal(0.0)) + aventiler

        for track in self.GetObjects():
            if not ok:
                break
            if track.reglement is True:
                if track.IDfacture in dictAventiler:
                    IDpayeur = None
                    if track.IDcompte_payeur in dictPayeurs:
                        for dictPayeur in dictPayeurs[track.IDcompte_payeur]:
                            if dictPayeur["nom"] == track.prelevement_titulaire:
                                IDpayeur = dictPayeur["IDpayeur"]
                    if IDpayeur is None:
                        IDpayeur = DB.ReqInsert("payeurs", [("IDcompte_payeur", track.IDcompte_payeur), ("nom", track.prelevement_titulaire)], commit=False)
                        if IDpayeur is None:
                            ok = False
                            break

                    montant = dictAventiler[track.IDfacture]
                    listeDonnees = [
                        ("IDcompte_payeur", track.IDcompte_payeur), ("date", date), ("IDmode", IDmode),
                        ("IDemetteur", None), ("numero_piece", None), ("montant", float(montant)),
                        ("IDpayeur", IDpayeur), ("observations", None), ("numero_quittancier", None),
                        ("IDcompte", IDcompte), ("date_differe", None), ("encaissement_attente", 0),
                        ("date_saisie", datetime.date.today()), ("IDutilisateur", UTILS_Identification.GetIDutilisateur()),
                        ("IDpiece", track.IDpiece),
                    ]
                    if track.IDreglement is None:
                        IDreglement = DB.ReqInsert("reglements", listeDonnees, commit=False)
                        if IDreglement is None:
                            ok = False
                            break
                    else:
                        IDreglement = track.IDreglement
                        if not DB.ReqMAJ("reglements", listeDonnees, "IDreglement", IDreglement, commit=False):
                            ok = False
                            break
                    listeMAJTracks.append((track, IDreglement, date))

                    for dictFacture in dictFactures.get(track.IDfacture, []):
                        listeVentilation = [
                            ("IDreglement", IDreglement), ("IDcompte_payeur", track.IDcompte_payeur),
                            ("IDprestation", dictFacture["IDprestation"]), ("montant", float(dictFacture["aventiler"])),
                        ]
                        if DB.ReqInsert("ventilation", listeVentilation, commit=False) is None:
                            ok = False
                            break
            elif track.IDreglement is not None:
                if not DB.ReqDEL("ventilation", "IDreglement", track.IDreglement, commit=False):
                    ok = False
                    break
                if not DB.ReqDEL("reglements", "IDreglement", track.IDreglement, commit=False):
                    ok = False
                    break

        if not ok:
            try:
                DB.connexion.rollback()
            except Exception:
                pass
            if not DB_externe:
                DB.Close()
            return False

        if commit:
            DB.Commit()
        if not DB_externe:
            DB.Close()
        for track, IDreglement, dateReglement in listeMAJTracks:
            track.IDreglement = IDreglement
            track.dateReglement = dateReglement
            self.RefreshObject(track)
        return True
'''
s = s[:start] + new + s[end:]
p.write_text(s, encoding='utf-8')

p = Path('noethys/Dlg/DLG_Saisie_lot_tresor_public.py')
s = p.read_text(encoding='utf-8')
old = '''        DB = GestionDB.DB()\n        if self.IDlot == None :\n            # Ajout\n            self.IDlot = DB.ReqInsert("pes_lots", listeDonnees)\n        else :\n            # Modification\n            DB.ReqMAJ("pes_lots", listeDonnees, "IDlot", self.IDlot)\n        DB.Close() \n        \n        # Sauvegarde des prélèvements du lot\n        self.ctrl_pieces.Sauvegarde(IDlot=self.IDlot, datePrelevement=date_prelevement, IDcompte=IDcompte, IDmode=IDmode) \n'''
new = '''        DB = GestionDB.DB()\n        ancien_IDlot = self.IDlot\n        if ancien_IDlot is None:\n            IDlot = DB.ReqInsert("pes_lots", listeDonnees, commit=False)\n            if IDlot is None:\n                DB.Close()\n                return False\n        else:\n            IDlot = ancien_IDlot\n            if not DB.ReqMAJ("pes_lots", listeDonnees, "IDlot", IDlot, commit=False):\n                DB.Close()\n                return False\n\n        # Sauvegarde pièces + règlements dans la même transaction que le lot\n        if not self.ctrl_pieces.Sauvegarde(IDlot=IDlot, datePrelevement=date_prelevement, IDcompte=IDcompte, IDmode=IDmode, DB=DB, commit=False):\n            try:\n                DB.connexion.rollback()\n            except Exception:\n                pass\n            DB.Close()\n            return False\n        DB.Commit()\n        DB.Close()\n        self.IDlot = IDlot\n'''
if old not in s:
    raise SystemExit('bloc lot PES introuvable')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
