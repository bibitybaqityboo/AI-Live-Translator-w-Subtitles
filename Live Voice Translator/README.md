# Live Voice Translator

This application translates your physical microphone into another language in real-time and routes it to your communication apps (like Discord) so your teammates can hear the translated voice instead of your real voice.

## 🛠️ Requirements
- **Gemini API Key**: Set in the `.env` file in the root directory.
- **VoiceMeeter**: A free audio mixer required to route the translated audio to Discord without you hearing yourself.

## 🎧 Audio Routing Setup

To avoid infinite loops and echoing, you must route your audio using VoiceMeeter. Follow this exact setup:

1. **App Settings (Live Voice Translator)**
   - Click the settings gear icon in the app.
   - **Microphone**: Type the name of your real, physical microphone (e.g., `usb mic`, `yeti`, `hyperx`).
   - **Output Device**: Type `voicemeeter input`.

2. **VoiceMeeter Application**
   - Open VoiceMeeter on your PC.
   - Look at the 3rd column labeled **VIRTUAL INPUT / Voicemeeter Input**.
   - Under that column, turn **OFF** the `A` button (this stops the AI voice from playing in your headphones).
   - Turn **ON** the `B` button (this routes the audio to the digital output for Discord).

3. **Discord / Game Voice Chat Settings**
   - **Input Device (Microphone)**: Set to `VoiceMeeter Output`. (This allows your teammates to hear your translated AI voice).

## 🖥️ Creating a Desktop Shortcut

If you want to launch this app directly from your Desktop without opening a terminal, you can create a simple batch file shortcut:

1. Right-click on your Desktop and select **New > Text Document**.
2. Name it `Live Voice Translator.bat` (ensure you remove the `.txt` extension).
3. Right-click the file and select **Edit**.
4. Paste the following code, making sure to replace the path with your actual folder path:
   ```bat
   @echo off
   cd /d "C:\Path\To\Your\Project\Folder"
   start pythonw.exe "Live Voice Translator\live_translate_gui.py"
   ```
5. Save the file. You can now double-click this shortcut to launch the app silently in the background!
