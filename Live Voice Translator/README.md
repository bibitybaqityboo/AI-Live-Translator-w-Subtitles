# Live Voice Translator

This application translates your physical microphone into another language in real-time and routes it to your communication apps (like Discord) so your teammates can hear the translated voice.

## 🛠️ Requirements
- **Gemini API Key**: Required for cloud translation.
- **VoiceMeeter**: Required to route the translated audio to Discord without you hearing yourself.

## 🎧 Audio Routing Setup

To avoid infinite loops and echoing, follow this exact setup:

1. **App Settings (Live Voice Translator)**
   - **Microphone**: `usb pnp audio` (Your real, physical microphone)
   - **Output Device**: `voicemeeter input`

2. **VoiceMeeter Application**
   - Open VoiceMeeter on your PC.
   - Under the 3rd column (**VIRTUAL INPUT / Voicemeeter Input**):
     - Turn **OFF** the `A` button (so you don't hear yourself).
     - Turn **ON** the `B` button (so the audio routes to the digital output).

3. **Discord / Game Voice Chat Settings**
   - **Input Device (Mic)**: Set to `VoiceMeeter Output` (This allows them to hear your translation).

## 🚀 Usage
Simply double-click the `Live Voice Translator.bat` shortcut. Ensure your API key is configured in the settings gear icon.

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
