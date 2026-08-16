from pathlib import Path

# CTRL_Vignettes_documents: atomiser chaque sauvegarde dans la base DOCUMENTS et retourner False sur erreur.
p=Path('noethys/Ctrl/CTRL_Vignettes_documents.py')
s=p.read_text(encoding='utf-8')
a=s.index('    def Sauvegarde(self, ID=None):\n')
b=s.index('    def ImportationScanner(self', a)
new='''    def Sauvegarde(self, ID=None):
        nbreDocuments = len(self.listePages)
        if len(self.listePages) == 0 and len(self.listePagesInitiale) == 0 :
            return nbreDocuments

        DB = GestionDB.DB(suffixe="DOCUMENTS")
        ok = True

        # Insère les nouveaux documents sans commit intermédiaire.
        for track in self.listePages :
            if track.IDdocument == 0 :
                if self.type_donnee == "piece" :
                    listeDonnees = [("IDpiece", ID), ("type", track.type), ("label", track.label), ("last_update", datetime.datetime.now())]
                elif self.type_donnee == "reponse" :
                    listeDonnees = [("IDreponse", ID), ("type", track.type), ("label", track.label), ("last_update", datetime.datetime.now())]
                elif self.type_donnee == "type_piece" :
                    listeDonnees = [("IDtype_piece", ID), ("type", track.type), ("label", track.label), ("last_update", datetime.datetime.now())]
                else :
                    ok = False
                    break

                IDdocument = DB.ReqInsert("documents", listeDonnees, commit=False)
                if IDdocument is None :
                    ok = False
                    break
                if DB.MAJimage(table="documents", key="IDdocument", IDkey=IDdocument, blobImage=track.buffer, nomChampBlob="document", commit=False) is False :
                    ok = False
                    break

        # Suppression des documents retirés.
        if ok :
            for track in self.listePagesInitiale :
                if track not in self.listePages :
                    if not DB.ReqDEL("documents", "IDdocument", track.IDdocument, commit=False) :
                        ok = False
                        break

        if ok :
            DB.Commit()
        else :
            try :
                DB.connexion.rollback()
            except Exception :
                pass
        DB.Close()

        if not ok :
            return False
        return nbreDocuments

'''
s=s[:a]+new+s[b:]
s='\n'.join(line.rstrip() for line in s.splitlines())+'\n'
p.write_text(s,encoding='utf-8')

# CTRL_Questionnaire: propager l'échec du stockage de documents.
p=Path('noethys/Ctrl/CTRL_Questionnaire.py')
s=p.read_text(encoding='utf-8')
old='''                if reponse == "##DOCUMENTS##":\n                    nbreDocuments = self.SauvegardeDocuments(IDquestion, IDreponse)\n                    if nbreDocuments == 0 and IDreponse != None:\n                        if not DBT.ReqDEL("questionnaire_reponses", "IDreponse", IDreponse, commit=not DBexterne):\n                            ok = False\n                            break\n'''
new='''                if reponse == "##DOCUMENTS##":\n                    nbreDocuments = self.SauvegardeDocuments(IDquestion, IDreponse)\n                    if nbreDocuments is False:\n                        ok = False\n                        break\n                    if nbreDocuments == 0 and IDreponse != None:\n                        if not DBT.ReqDEL("questionnaire_reponses", "IDreponse", IDreponse, commit=not DBexterne):\n                            ok = False\n                            break\n'''
if old not in s:
    raise SystemExit('bloc documents questionnaire introuvable')
s=s.replace(old,new,1)
s='\n'.join(line.rstrip() for line in s.splitlines())+'\n'
p.write_text(s,encoding='utf-8')
