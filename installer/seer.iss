; Inno Setup script for Seer.
; Build with: ISCC.exe seer.iss   (Inno Setup 6 from https://jrsoftware.org/isinfo.php)
;
; Output: installer/Output/seer-setup-X.Y.Z.exe
;
; What it does:
;   1. Copies seer.exe, seer-tray.exe, seer-native-host.exe to {app}
;   2. Copies the Chrome extension folder to {app}\extension\
;   3. Registers the Native Messaging Host in HKCU\Software\Google\Chrome\NativeMessagingHosts
;      (manifest path = {app}\com.seer.host.json, written at install time)
;   4. Adds seer-tray.exe to Windows Startup (HKCU\...\Run)
;   5. Optionally opens chrome://extensions on completion so the user can load the extension

#define MyAppName "Seer"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Seer"
#define MyAppURL "https://github.com/av29nassh-sketch/seer"
#define MyAppExeName "seer-tray.exe"
#define HostName "com.seer.host"

[Setup]
AppId={{B6AE0F4D-3F2B-4D5E-9C8A-7B1F2A5E3D9C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=Output
OutputBaseFilename=seer-setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\seer-tray.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "startuptray"; Description: "Start Seer tray app on Windows startup"; GroupDescription: "Startup:"
Name: "openchromeext"; Description: "Open chrome://extensions to load the Seer Bridge extension after install"; GroupDescription: "Setup:"

[Files]
Source: "dist\seer.exe";              DestDir: "{app}"; Flags: ignoreversion
Source: "dist\seer-tray.exe";         DestDir: "{app}"; Flags: ignoreversion
Source: "dist\seer-native-host.exe";  DestDir: "{app}"; Flags: ignoreversion
Source: "dist\extension\*";           DestDir: "{app}\extension"; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
; Native messaging host registration — points Chrome at our manifest JSON.
Root: HKCU; Subkey: "Software\Google\Chrome\NativeMessagingHosts\{#HostName}"; \
  ValueType: string; ValueName: ""; ValueData: "{app}\{#HostName}.json"; Flags: uninsdeletevalue uninsdeletekeyifempty

; Optional: launch seer-tray on Windows login.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "SeerTray"; ValueData: """{app}\seer-tray.exe"""; \
  Flags: uninsdeletevalue; Tasks: startuptray

[Run]
Filename: "{app}\seer-tray.exe"; Description: "Launch Seer tray"; Flags: nowait postinstall skipifsilent
Filename: "chrome.exe"; Parameters: "chrome://extensions"; Description: "Open chrome://extensions"; \
  Flags: nowait postinstall skipifsilent shellexec; Tasks: openchromeext

[Code]
// Write the Native Messaging Host manifest at install time (path needs to be templated to {app}).
// allowed_origins is left as a placeholder — the user runs install_native_host CLI inside the app folder
// (or seer-tray prompts on first launch) once they know their extension ID.
procedure CurStepChanged(CurStep: TSetupStep);
var
  ExePath: string;
  ManifestPath: string;
  Json: string;
begin
  if CurStep = ssPostInstall then
  begin
    ExePath := ExpandConstant('{app}\seer-native-host.exe');
    ManifestPath := ExpandConstant('{app}\{#HostName}.json');
    // Inno's StringChangeEx modifies in place; do it before we build the JSON literal.
    StringChangeEx(ExePath, '\', '\\', True);
    Json :=
      '{' + #13#10 +
      '  "name": "{#HostName}",' + #13#10 +
      '  "description": "Seer Bridge native messaging host",' + #13#10 +
      '  "path": "' + ExePath + '",' + #13#10 +
      '  "type": "stdio",' + #13#10 +
      '  "allowed_origins": ["chrome-extension://REPLACE_WITH_EXTENSION_ID/"]' + #13#10 +
      '}';
    SaveStringToFile(ManifestPath, Json, False);
  end;
end;
