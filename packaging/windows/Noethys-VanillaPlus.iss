#define MyAppName "Noethys Vanilla+"
#define MyAppExeName "Noethys.exe"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif

[Setup]
AppId={{8D89C258-714E-4CB4-A0A8-0FCEBC6EEBA8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=PMSL
DefaultDirName={code:GetInstallDir}
DisableDirPage=auto
UsePreviousAppDir=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
OutputDir=..\..\dist-installer
OutputBaseFilename=Noethys-VanillaPlus-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
Uninstallable=yes
SetupLogging=yes

[Files]
Source: "..\..\dist\Noethys\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "Portable\*"

[Icons]
Name: "{autoprograms}\Noethys"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\Noethys"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer Noethys"; Flags: nowait postinstall skipifsilent

[Code]
function ExistingNoethysDir(): String;
var
  Candidate: String;
begin
  Result := '';
  if RegQueryStringValue(HKLM32, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Noethys_is1', 'InstallLocation', Candidate) and DirExists(Candidate) then begin Result := Candidate; exit; end;
  if RegQueryStringValue(HKLM64, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Noethys_is1', 'InstallLocation', Candidate) and DirExists(Candidate) then begin Result := Candidate; exit; end;
  Candidate := ExpandConstant('{pf32}\Noethys');
  if FileExists(AddBackslash(Candidate) + '{#MyAppExeName}') then begin Result := Candidate; exit; end;
  Candidate := ExpandConstant('{pf}\Noethys');
  if FileExists(AddBackslash(Candidate) + '{#MyAppExeName}') then Result := Candidate;
end;

function GetInstallDir(Param: String): String;
var
  Existing: String;
begin
  Existing := ExistingNoethysDir();
  if Existing <> '' then Result := Existing else Result := ExpandConstant('{autopf}\Noethys');
end;

function InitializeSetup(): Boolean;
var
  Existing: String;
begin
  Result := True;
  Existing := ExistingNoethysDir();
  if Existing <> '' then
    Log('Installation Noethys existante détectée : ' + Existing)
  else
    Log('Aucune installation Noethys existante détectée : installation standard.');
end;
