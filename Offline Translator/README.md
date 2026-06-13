# Offline Translator (Local Translate)

This application provides 100% offline, local translation of your teammates' voice chat. It listens to their audio, transcribes it locally using `faster-whisper`, translates it using **LM Studio**, and displays it as subtitles on your screen.

## 🛠️ Requirements
- **LM Studio**: Must be running locally with a loaded text model (e.g., Gemma).
- **Faster-Whisper**: The local Speech-to-Text engine. Install via: `pip install faster-whisper`
- **VB-Audio Virtual Cable**: Required to capture Discord audio.

## 🎧 Audio Routing Setup

To capture your teammates' voices without capturing the game audio (like gunshots):

1. **Discord / Game Voice Chat Settings**
   - **Output Device (Speaker)**: Set to `CABLE Input`

2. **Windows Sound Control Panel**
   - **`CABLE Output` (Recording Tab)**: Check "Listen to this device" and set it to your `Turtle Beach` headphones ONLY if you want to hear your teammates' original voices mixed with game audio.

3. **App Settings (Offline Translator)**
   - **Microphone**: `cable output` (Listens to the Discord audio)
   - **Output Device**: `turtle beach` (Where the AI voice plays, if enabled)

## ✨ New Features
- **Subtitle Overlay**: Enable a silent, transparent, click-through window overlay to read what your teammates are saying in real-time.
- **Play Audio (TTS) Toggle**: Turn this OFF for a completely silent, subtitles-only experience.

## 🚀 Usage
Double-click `Offline Translator.bat`. Ensure LM Studio is running its local server on `http://127.0.0.1:1234/v1`.

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
