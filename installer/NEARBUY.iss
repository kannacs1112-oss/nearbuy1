#define MyAppName "NEARBUY"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "NEARBUY"
#define MyAppExeName "NEARBUY.exe"
[Setup]
AppId={{B17B0E3C-7C61-4A11-94C2-8ECA4E7F6D21}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\NEARBUY
DefaultGroupName=NEARBUY
OutputDir=..\release
OutputBaseFilename=NEARBUY-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
[Files]
Source: "..\dist\NEARBUY\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\NEARBUY"; Filename: "{app}\NEARBUY.exe"
Name: "{autodesktop}\NEARBUY"; Filename: "{app}\NEARBUY.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"
[Run]
Filename: "{app}\NEARBUY.exe"; Description: "Launch NEARBUY"; Flags: nowait postinstall skipifsilent
