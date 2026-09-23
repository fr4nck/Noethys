; Harnais de test du dossier d'installation par défaut/validation du
; dossier précédent -- JAMAIS distribué (n'apparaît dans aucun artefact
; publié). Inclut le VRAI fichier de logique
; (vanilla-installer-dirlogic.inc.iss), le même que celui utilisé par
; vanilla-installer.iss : aucune duplication, ce test exerce le code
; réellement embarqué dans le Setup distribué.
;
; N'installe jamais réellement rien : InitializeSetup() écrit les
; résultats des 4 cas dans un fichier texte puis annule l'installation
; (Result := False) avant toute copie de fichier.

[Setup]
AppId=NoethysTestDirLogic
AppName=NoethysTestDirLogic
AppVersion=0.0.1
DefaultDirName={autopf}\NoethysTestDirLogic
OutputDir=.
OutputBaseFilename=dirlogic-test-setup
DisableDirPage=no
PrivilegesRequired=lowest

[Files]
Source: "vanilla-installer-dirlogic.inc.iss"; DestDir: "{app}"; Flags: dontcopy

[Code]
#include "vanilla-installer-dirlogic.inc.iss"

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
