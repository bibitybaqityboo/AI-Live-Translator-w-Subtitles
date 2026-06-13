# Game Audio Translator

This application uses the cloud-based Gemini API to listen to your teammates' voice chat and read the translated audio out loud to your headphones.

## 🛠️ Requirements
- **Gemini API Key**: Required for cloud translation.
- **VB-Audio Virtual Cable**: Required to capture Discord audio cleanly.

## 🎧 Audio Routing Setup

1. **Discord / Game Voice Chat Settings**
   - **Output Device (Speaker)**: Set to `CABLE Input`

2. **Windows Sound Control Panel**
   - **`CABLE Output` (Recording Tab)**: Check "Listen to this device" and set it to your `Turtle Beach` headphones if you still want to hear your teammates' native voices alongside the AI translation.

3. **App Settings (Game Audio Translator)**
   - **Microphone**: `cable output` (Listens to the teammates)
   - **Output Device**: `turtle beach` (Where the AI translation plays)

## 🚀 Usage
Double-click `Game Audio Translator.bat`. Configure your Gemini API key in the settings gear icon.

## 🖥️ Creating a Desktop Shortcut

If you want to launch this app directly from your Desktop without opening a terminal, you can create a simple batch file shortcut:

1. Right-click on your Desktop and select **New > Text Document**.
2. Name it `Game Audio Translator.bat` (ensure you remove the `.txt` extension).
3. Right-click the file and select **Edit**.
4. Paste the following code, making sure to replace the path with your actual folder path:
   ```bat
   @echo off
   cd /d "C:\Path\To\Your\Project\Folder"
   start pythonw.exe "Game Audio Translator\game_translate_gui.py"
   ```
5. Save the file. You can now double-click this shortcut to launch the app silently in the background!
