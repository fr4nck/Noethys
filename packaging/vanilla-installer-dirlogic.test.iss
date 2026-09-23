; Harnais de test du dossier d'installation par défaut/validation du
; dossier précédent -- JAMAIS distribué (n'apparaît dans aucun artefact
; publié). Inclut le VRAI fichier de logique
; (vanilla-installer-dirlogic.inc.iss), le même que celui utilisé par
; vanilla-installer.iss : aucune duplication, ce test exerce le code
; réellement embarqué dans le Setup distribué.
;
; Deux modes, sélectionnés par la variable d'environnement
; NOETHYS_DIRLOGIC_MODE au lancement du Setup compilé :
;
; - mode absent ou "ABCD" (par défaut) : InitializeSetup() exerce les
;   fonctions partagées directement (CAS A/B/C/D), écrit les résultats dans
;   un fichier texte, puis annule l'installation (Result := False) avant
;   toute copie de fichier -- rien n'est jamais réellement installé.
;
; - mode "EF" : InitializeSetup() laisse l'assistant progresser normalement
;   jusqu'à la page de sélection du dossier (CurPageChanged), qui applique
;   AppliquerGardeFouDossierPropose() -- exactement la même fonction que
;   vanilla-installer.iss -- puis, en mode CAS "F", simule une saisie
;   manuelle de l'utilisateur juste après. NextButtonClick() enregistre la
;   valeur finale du champ avant de laisser l'installation se terminer
;   normalement (le [Files] ci-dessous ne copie jamais rien réellement,
;   Flags: dontcopy : une installation "complète" ici est sans risque).
;
; AppId distinct (NoethysTestDirLogic) : n'interfère jamais avec une
; installation réelle de Noethys sur la même machine. UsePreviousAppDir et
; DefaultDirName={code:GetDefaultDirName} sont configurés à l'identique de
; vanilla-installer.iss pour que l'assistant se comporte exactement de la
; même façon (seule LireCheminPrecedentDuRegistre() lit toujours la clé
; Noethys_is1, volontairement -- voir cette fonction dans le fichier
; partagé -- ce qui est correct : c'est bien l'historique du VRAI produit
; Noethys qu'il faut valider, quel que soit l'AppId du harnais qui appelle
; la fonction).

[Setup]
AppId=NoethysTestDirLogic
AppName=NoethysTestDirLogic
AppVersion=0.0.1
DefaultDirName={code:GetDefaultDirName}
UsePreviousAppDir=yes
OutputDir=.
OutputBaseFilename=dirlogic-test-setup
DisableDirPage=no
; PrivilegesRequired=admin (et non lowest) : {autopf} dans GetDefaultDirName()
; se resout differemment selon ce reglage (Program Files machine si admin,
; {localappdata}\Programs par utilisateur sinon). vanilla-installer.iss
; distribue est PrivilegesRequired=admin -- le harnais doit reproduire
; exactement le meme contexte pour que les CAS A/D_REPLI (qui attendent
; {autopf}\Noethys) testent reellement le comportement de production.
PrivilegesRequired=admin

[Files]
Source: "vanilla-installer-dirlogic.inc.iss"; DestDir: "{app}"; Flags: dontcopy

[Code]
#include "vanilla-installer-dirlogic.inc.iss"

var
  ModeTest: String;

procedure Ajoute(var Resultats: TArrayOfString; Ligne: String);
begin
  SetArrayLength(Resultats, GetArrayLength(Resultats) + 1);
  Resultats[GetArrayLength(Resultats) - 1] := Ligne;
end;

function InitializeSetup(): Boolean;
var
  Resultats: TArrayOfString;
  CheminHistorique, CheminValideTest, CheminTempTest: String;
begin
  ModeTest := GetEnv('NOETHYS_DIRLOGIC_MODE');

  if ModeTest = 'EF' then
  begin
    // CAS E/F : laisse l'assistant progresser réellement jusqu'à
    // wpSelectDir (voir CurPageChanged/NextButtonClick ci-dessous).
    Result := True;
    Exit;
  end;

  // CAS A/B/C/D : exercice direct des fonctions partagées, jamais
  // d'affichage de page, annulation avant toute copie de fichier.
  SetArrayLength(Resultats, 0);

  CheminHistorique := 'C:\Noethys';
  // {localappdata} (et non {tmp}) : {tmp}\.. reste sous %TEMP%, ce qui
  // ferait rejeter ce chemin par EstCheminSousDossierTemporaire() et
  // fausserait ce cas -- un "previous AppDir valide" doit être hors TEMP.
  CheminValideTest := ExpandConstant('{localappdata}') + '\_noethys_test_valide_prevdir';
  CheminTempTest := GetEnv('TEMP') + '\noethys-rc3-installed-test';

  // Nettoyage préalable (l'environnement CI est jetable, mais on reste
  // prudent : jamais de suppression en dehors de nos propres dossiers de
  // test explicitement nommés ci-dessus).
  if DirExists(CheminHistorique) then
    DelTree(CheminHistorique, True, True, True);
  if DirExists(CheminValideTest) then
    DelTree(CheminValideTest, True, True, True);

  // CAS A : aucune installation existante -> {autopf}\Noethys
  Ajoute(Resultats, 'CAS_A=' + GetDefaultDirName(''));

  // CAS B : C:\Noethys\Noethys.exe historique présent -> C:\Noethys proposé
  ForceDirectories(CheminHistorique);
  SaveStringToFile(CheminHistorique + '\Noethys.exe', 'test', False);
  Ajoute(Resultats, 'CAS_B=' + GetDefaultDirName(''));
  DelTree(CheminHistorique, True, True, True);

  // CAS C : previous AppDir valide (dossier réel, hors TEMP, avec Noethys.exe)
  ForceDirectories(CheminValideTest);
  SaveStringToFile(CheminValideTest + '\Noethys.exe', 'test', False);
  if EstCheminPrecedentValide(CheminValideTest) then
    Ajoute(Resultats, 'CAS_C=ACCEPTE')
  else
    Ajoute(Resultats, 'CAS_C=REJETE');
  DelTree(CheminValideTest, True, True, True);

  // CAS D : previous AppDir = un dossier de test sous %TEMP% (le bug réel
  // constaté en recette RC3) -> doit être rejeté, puis repli sur
  // GetDefaultDirName() (C:\Noethys si présent, sinon {autopf}\Noethys ;
  // aucun des deux n'est présent ici, donc {autopf}\Noethys attendu).
  if EstCheminPrecedentValide(CheminTempTest) then
    Ajoute(Resultats, 'CAS_D_REJETE=NON')
  else
    Ajoute(Resultats, 'CAS_D_REJETE=OUI');
  Ajoute(Resultats, 'CAS_D_REPLI=' + GetDefaultDirName(''));

  SaveStringsToFile(ExpandConstant('{tmp}\..\resultat-dirlogic.txt'), Resultats, False);

  Result := False;  // annule toujours l'installation, jamais de copie réelle
end;

procedure CurPageChanged(CurPageID: Integer);
var
  CheminUtilisateurSimule: String;
begin
  if (ModeTest = 'EF') and (CurPageID = wpSelectDir) then
  begin
    // Exactement la même fonction que vanilla-installer.iss::CurPageChanged.
    AppliquerGardeFouDossierPropose(WizardForm.DirEdit);

    if GetEnv('NOETHYS_DIRLOGIC_CAS') = 'F' then
    begin
      // Simule un utilisateur qui, juste après l'affichage de la page (et
      // la correction éventuelle ci-dessus), tape lui-même un chemin
      // personnalisé avant de cliquer sur Suivant.
      CheminUtilisateurSimule := GetEnv('NOETHYS_DIRLOGIC_CHEMIN_UTILISATEUR');
      WizardForm.DirEdit.Text := CheminUtilisateurSimule;
    end;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Resultats: TArrayOfString;
begin
  Result := True;  // laisse toujours l'assistant progresser normalement
  if (ModeTest = 'EF') and (CurPageID = wpSelectDir) then
  begin
    SetArrayLength(Resultats, 0);
    // Valeur du champ au moment de quitter la page -- après un éventuel
    // /DIR= (CAS E) ou la saisie simulée ci-dessus (CAS F) : prouve que
    // rien (ni AppliquerGardeFouDossierPropose, ni autre chose) ne l'a
    // réécrite entre-temps.
    if GetEnv('NOETHYS_DIRLOGIC_CAS') = 'E' then
      Ajoute(Resultats, 'CAS_E=' + WizardForm.DirEdit.Text)
    else if GetEnv('NOETHYS_DIRLOGIC_CAS') = 'F' then
      Ajoute(Resultats, 'CAS_F=' + WizardForm.DirEdit.Text);
    SaveStringsToFile(ExpandConstant('{tmp}\..\resultat-dirlogic-ef.txt'), Resultats, False);
  end;
end;
