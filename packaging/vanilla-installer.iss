; Installateur Windows de la ligne Vanilla maintenue.
; Réutilise l'identité historique Inno Setup afin qu'une mise à jour remplace
; proprement l'installation existante au lieu de créer un second désinstalleur.

#ifndef MyAppVersion
  #define MyAppVersion "1.3.4.2-r2"
#endif

[Setup]
AppId=Noethys
AppName=Noethys
AppVersion={#MyAppVersion}
AppPublisher=Noethys
DefaultDirName={autopf}\Noethys
DefaultGroupName=Noethys
DisableProgramGroupPage=yes
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
