; Installateur Windows de la ligne Vanilla maintenue.
; Réutilise l'identité historique Inno Setup afin qu'une mise à jour remplace
; proprement l'installation existante au lieu de créer un second désinstalleur.
;
; UsePreviousAppDir=yes ne fonctionne QUE si Inno Setup a lui-même déjà
; installé Noethys une première fois sous ce même AppId (il relit alors sa
; propre clé de registre HKLM\...\Noethys_is1). Une installation historique
; C:\Noethys posée par un mécanisme différent (ancien installeur, copie
; manuelle) n'a jamais écrit cette clé : Inno ne peut donc pas la "voir",
; et retombe sur DefaultDirName={autopf}\Noethys (Program Files), d'où deux
; installations distinctes sur le même poste si l'utilisateur ne change pas
; le dossier proposé. GetDefaultDirName() ci-dessous ne fait que PROPOSER
; C:\Noethys quand ce cas est détecté ; DisableDirPage=no garantit que la
; page reste affichée pour que l'utilisateur garde la main (choix final
; toujours à l'utilisateur, rien n'est déplacé ni supprimé automatiquement).

#ifndef MyAppVersion
  #define MyAppVersion "1.3.4.2-r2"
#endif

[Setup]
AppId=Noethys
AppName=Noethys
AppVersion={#MyAppVersion}
AppPublisher=Noethys
DefaultDirName={code:GetDefaultDirName}
DefaultGroupName=Noethys
DisableProgramGroupPage=yes
DisableDirPage=no
UsePreviousAppDir=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
OutputDir=..\installer-output
OutputBaseFilename=Noethys-Vanilla-Setup
SetupIconFile=..\noethys\Icone.ico
UninstallDisplayIcon={app}\Noethys.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
ChangesAssociations=no
ChangesEnvironment=no
SetupLogging=yes

[Files]
Source: "..\dist\Noethys-installable\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Noethys"; Filename: "{app}\Noethys.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Noethys"; Filename: "{app}\Noethys.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: unchecked

[Run]
Filename: "{app}\Noethys.exe"; Description: "Lancer Noethys"; Flags: nowait postinstall skipifsilent

[Code]
function GetDefaultDirName(Param: String): String;
var
  CheminHistorique: String;
begin
  // Valeur de repli normale (Program Files) -- UsePreviousAppDir=yes prend
  // de toute façon le dessus sur ce résultat si Inno connaît déjà un
  // dossier d'installation précédent pour cet AppId.
  Result := ExpandConstant('{autopf}\Noethys');

  CheminHistorique := 'C:\Noethys';
  if FileExists(CheminHistorique + '\Noethys.exe') then
    Result := CheminHistorique;
end;
