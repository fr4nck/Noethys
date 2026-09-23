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
;
; BUG REEL CORRIGE (recette RC3) : UsePreviousAppDir=yes fait AUSSI
; confiance, sans la moindre validation, à la valeur "InstallLocation"
; déjà enregistrée dans le registre pour AppId=Noethys -- y compris si
; cette valeur provient d'une installation de TEST (silencieuse, /DIR=
; vers un dossier temporaire) jamais désinstallée proprement. Preuve
; directe constatée : HKLM\SOFTWARE\WOW6432Node\...\Uninstall\Noethys_is1
; \InstallLocation pointait vers
; "C:\Users\<utilisateur>\AppData\Local\Temp\noethys-rc3-installed-test\",
; un dossier de recette CI qui n'existait même plus -- et Inno proposait
; ce chemin mort à un utilisateur réel, AVANT même que GetDefaultDirName()
; ne soit consulté (UsePreviousAppDir est prioritaire sur DefaultDirName
; dès qu'un chemin précédent existe, quelle que soit sa validité).
; CurPageChanged() ci-dessous intercepte la page de sélection du dossier et
; REMPLACE la valeur qu'Inno vient d'y pré-remplir si elle est suspecte
; (sous %TEMP%/%TMP%, ou nom de dossier de test), en retombant sur
; GetDefaultDirName() -- jamais l'inverse : un dossier précédent réellement
; valide reste toujours proposé en priorité, et l'utilisateur peut toujours
; saisir n'importe quel autre dossier de son choix (la page reste visible et
; modifiable). La logique de validation vit dans
; vanilla-installer-dirlogic.inc.iss (jamais dupliquée), testée par
; vanilla-installer-dirlogic.test.iss (4 cas, voir CI).
;
; REGRESSION CORRIGEE APRES COUP : une première version de CurPageChanged()
; validait WizardForm.DirEdit.Text tel quel, quelle que soit son origine.
; Or ce champ contient AUSSI la valeur d'un /DIR= explicite (installation
; silencieuse CI) ou d'une saisie manuelle -- une installation NEUVE, qui
; n'a par définition pas encore Noethys.exe sur place. EstCheminPrecedentValide()
; l'exigeant, ce /DIR= explicite était systématiquement rejeté et remplacé
; par GetDefaultDirName(), cassant toute installation vers un nouveau
; dossier (constaté en CI : "Tester installation et conservation de la
; configuration" échouait, Noethys.exe absent du dossier /DIR= demandé).
; Correctif : LireCheminPrecedentDuRegistre() lit directement la valeur que
; UsePreviousAppDir a lui-même utilisée pour pré-remplir le champ ; on ne
; corrige le champ que si sa valeur ACTUELLE est identique à cette valeur de
; registre ET que celle-ci est invalide -- jamais un /DIR= ou une saisie
; utilisateur, qui diffèrent toujours de ce chemin précédent.

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
#include "vanilla-installer-dirlogic.inc.iss"

procedure CurPageChanged(CurPageID: Integer);
var
  CheminRegistrePrecedent: String;
begin
  // UsePreviousAppDir a déjà pré-rempli WizardForm.DirEdit.Text avec la
  // valeur du registre à ce stade (sans aucune validation de sa part). On
  // ne corrige CE champ QUE si sa valeur ACTUELLE correspond exactement au
  // chemin lu directement dans le registre (LireCheminPrecedentDuRegistre)
  // ET que ce chemin est invalide : cela prouve qu'Inno a bien pré-rempli
  // depuis ce chemin précédent, par opposition à un /DIR= passé en ligne de
  // commande ou à une saisie manuelle de l'utilisateur -- ces derniers
  // visent une installation NEUVE qui n'a par définition pas encore
  // Noethys.exe sur place, et ne doivent donc jamais être rejetés ici.
  // Un dossier précédent réellement valide n'est jamais modifié.
  if CurPageID = wpSelectDir then
  begin
    CheminRegistrePrecedent := LireCheminPrecedentDuRegistre();
    if (CheminRegistrePrecedent <> '') and
       (RemoveBackslashUnlessRoot(WizardForm.DirEdit.Text) = CheminRegistrePrecedent) and
       (not EstCheminPrecedentValide(CheminRegistrePrecedent)) then
      WizardForm.DirEdit.Text := GetDefaultDirName('');
  end;
end;
