; Installateur Windows de la ligne Upgrade Noethys.
; Les données et la configuration utilisateur ne sont jamais embarquées ici :
; elles restent gérées par UTILS_Fichiers dans le profil utilisateur.

#ifndef MyAppVersion
  #define MyAppVersion "1.3.4.2-upgrade"
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
OutputDir=..\installer-output
OutputBaseFilename=Noethys-Upgrade-Setup
SetupIconFile=..\noethys\Icone.ico
UninstallDisplayIcon={app}\Noethys.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
ChangesAssociations=no
ChangesEnvironment=no

[Files]
Source: "..\dist\Noethys-installable\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Noethys"; Filename: "{app}\Noethys.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Noethys"; Filename: "{app}\Noethys.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: unchecked

[Run]
Filename: "{app}\Noethys.exe"; Description: "Lancer Noethys"; Flags: nowait postinstall skipifsilent
