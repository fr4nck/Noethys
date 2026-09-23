// Logique de détermination/validation du dossier d'installation par défaut.
// Fichier partagé, inclus (#include) à la fois par vanilla-installer.iss
// (l'installateur réellement distribué) et par
// vanilla-installer-dirlogic.test.iss (harnais de test CI, jamais
// distribué) : toute correction doit se faire ICI, jamais dupliquée.
//
// Contexte : UsePreviousAppDir=yes fait confiance, SANS AUCUNE VALIDATION,
// à la valeur "InstallLocation" déjà enregistrée dans le registre pour cet
// AppId -- y compris si cette valeur provient d'une installation de TEST
// (silencieuse, /DIR= vers un dossier temporaire) jamais désinstallée
// proprement. EstCheminPrecedentValide() sert de garde-fou, appelé depuis
// CurPageChanged() dans vanilla-installer.iss.
//
// NOTE : ce fichier est inclus DANS une section [Code] (Pascal Script) --
// il doit donc utiliser exclusivement des commentaires Pascal (// ou { }),
// jamais la syntaxe ";" des fichiers .iss classiques.

function GetDefaultDirName(Param: String): String;
var
  CheminHistorique: String;
begin
  // Valeur de repli normale (Program Files) -- UsePreviousAppDir=yes prend
  // de toute façon le dessus sur ce résultat si Inno connaît déjà un
  // dossier d'installation précédent pour cet AppId ET que ce dossier est
  // jugé valide par EstCheminPrecedentValide() (voir CurPageChanged).
  Result := ExpandConstant('{autopf}\Noethys');

  CheminHistorique := 'C:\Noethys';
  if FileExists(CheminHistorique + '\Noethys.exe') then
    Result := CheminHistorique;
end;

function EstCheminSousDossierTemporaire(Chemin: String): Boolean;
var
  CheminMinuscule, TempEnv, TmpEnv: String;
begin
  CheminMinuscule := LowerCase(Chemin);
  Result := False;

  TempEnv := LowerCase(GetEnv('TEMP'));
  if (TempEnv <> '') and (Pos(TempEnv, CheminMinuscule) = 1) then
    Result := True;

  TmpEnv := LowerCase(GetEnv('TMP'));
  if (TmpEnv <> '') and (Pos(TmpEnv, CheminMinuscule) = 1) then
    Result := True;

  // Constante Inno {tmp} elle-même (dossier de travail temporaire propre à
  // cette exécution du Setup), au cas où elle diffèrerait de %TEMP%/%TMP%.
  if Pos(LowerCase(ExpandConstant('{tmp}')), CheminMinuscule) = 1 then
    Result := True;
end;

function EstNomDeDossierDeTest(Chemin: String): Boolean;
var
  NomDossier: String;
begin
  NomDossier := LowerCase(ExtractFileName(RemoveBackslashUnlessRoot(Chemin)));
  // Couvre explicitement noethys-*-installed-test et noethys-rc*-installed-test
  // (dossiers créés par les tests d'installation silencieuse de la CI), et
  // plus généralement tout dossier dont le nom trahit une origine de test.
  Result := (Pos('noethys-', NomDossier) = 1) and
            ((Pos('-installed-test', NomDossier) > 0) or
             (Pos('-rc', NomDossier) > 0) or
             (Pos('-test', NomDossier) > 0));
end;

function EstCheminPrecedentValide(Chemin: String): Boolean;
begin
  Result := (Chemin <> '') and
            (not EstCheminSousDossierTemporaire(Chemin)) and
            (not EstNomDeDossierDeTest(Chemin)) and
            FileExists(AddBackslash(Chemin) + 'Noethys.exe');
end;
