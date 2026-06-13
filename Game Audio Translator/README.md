# Game Audio Translator

This application uses the cloud-based Google Gemini API to listen to your teammates' voice chat and read the translated audio out loud to your headphones in real-time.

## 🛠️ Requirements
- **Gemini API Key**: Set in the `.env` file in the root directory.
- **VB-Audio Virtual Cable**: A free virtual audio cable required to isolate Discord audio from game audio.

## 🎧 Audio Routing Setup

To capture your teammates' voices without capturing the game audio (like gunshots or background music):

1. **Discord / Game Voice Chat Settings**
   - **Output Device (Speaker)**: Set to `CABLE Input`. (This sends your teammates' voices down the virtual cable).

2. **Windows Sound Control Panel**
   - Open Windows Sound Settings > More Sound Settings > **Recording Tab**.
   - Right-click `CABLE Output` > Properties > **Listen Tab**.
   - **Check "Listen to this device"** and select your primary headphones/speakers from the dropdown list. *(This ensures you can still hear your teammates' original voices mixed with your game audio while the AI translates them).*

3. **App Settings (Game Audio Translator)**
   - Click the settings gear icon in the app.
   - **Microphone**: Type `cable output` (This tells the app to listen to the teammates).
   - **Output Device**: Type the name of your primary headphones (e.g., `headphones`, `speakers`, `arctis`). (This is where the translated AI voice plays).

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
