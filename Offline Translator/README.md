# Offline Translator (Local Translate)

This application provides 100% offline, local translation of your teammates' voice chat. It listens to their audio, transcribes it locally using `faster-whisper`, translates it using **LM Studio**, and displays it as subtitles on your screen. No API keys required!

## 🛠️ Requirements
- **LM Studio**: Must be running locally with a loaded text model (e.g., Gemma, Llama). The local server must be started on port 1234.
- **Faster-Whisper**: The local Speech-to-Text engine. Install via terminal: `pip install faster-whisper`
- **VB-Audio Virtual Cable**: A free virtual audio cable required to isolate Discord audio from game audio.

## 🎧 Audio Routing Setup

To capture your teammates' voices without capturing the game audio (like gunshots or background music):

1. **Discord / Game Voice Chat Settings**
   - **Output Device (Speaker)**: Set to `CABLE Input`. (This sends your teammates' voices down the virtual cable).

2. **Windows Sound Control Panel**
   - Open Windows Sound Settings > More Sound Settings > **Recording Tab**.
   - Right-click `CABLE Output` > Properties > **Listen Tab**.
   - **Check "Listen to this device"** and select your primary headphones/speakers from the dropdown list. *(This ensures you can still hear your teammates' original voices mixed with your game audio).*

3. **App Settings (Offline Translator)**
   - Click the settings gear icon in the app.
   - **Microphone**: Type `cable output` (This tells the app to listen to the teammates).
   - **Output Device**: Type the name of your primary headphones (e.g., `headphones`, `speakers`, `arctis`). (This is where the translated AI voice plays, if you enable TTS).

## ✨ Features
- **Subtitle Overlay**: Enable a silent, transparent, click-through window overlay to read what your teammates are saying in real-time while you game.
- **Play Audio (TTS) Toggle**: Turn this switch OFF for a completely silent, subtitles-only experience.

## 🖥️ Creating a Desktop Shortcut

If you want to launch this app directly from your Desktop without opening a terminal, you can create a simple batch file shortcut:

1. Right-click on your Desktop and select **New > Text Document**.
2. Name it `Offline Translator.bat` (ensure you remove the `.txt` extension).
3. Right-click the file and select **Edit**.
4. Paste the following code, making sure to replace the path with your actual folder path:
   ```bat
   @echo off
   cd /d "C:\Path\To\Your\Project\Folder"
   start pythonw.exe "Offline Translator\live_translate_local.py"
   ```
5. Save the file. You can now double-click this shortcut to launch the app silently in the background!
