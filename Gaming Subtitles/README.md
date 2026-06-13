# Gaming Subtitles

This application uses the Gemini API to listen to your teammates and provide silent, real-time translated subtitles via an invisible, click-through overlay while you game.

## 🛠️ Requirements
- **Gemini API Key**: Required for cloud translation.
- **VB-Audio Virtual Cable**: Required to capture Discord audio cleanly.

## 🎧 Audio Routing Setup

1. **Discord / Game Voice Chat Settings**
   - **Output Device (Speaker)**: Set to `CABLE Input`

2. **Windows Sound Control Panel**
   - **`CABLE Output` (Recording Tab)**: Check "Listen to this device" and point it to your `Turtle Beach` headphones so you can still hear the original audio while reading the subtitles.

3. **App Settings (Gaming Subtitles)**
   - **Microphone**: `cable output` (Listens to the teammates)

## 🚀 Usage
Double-click `Gaming Subtitles.bat`. Use the built-in sliders to adjust subtitle size, color, and vertical position on your screen.

## 🖥️ Creating a Desktop Shortcut

If you want to launch this app directly from your Desktop without opening a terminal, you can create a simple batch file shortcut:

1. Right-click on your Desktop and select **New > Text Document**.
2. Name it `Gaming Subtitles.bat` (ensure you remove the `.txt` extension).
3. Right-click the file and select **Edit**.
4. Paste the following code, making sure to replace the path with your actual folder path:
   ```bat
   @echo off
   cd /d "C:\Path\To\Your\Project\Folder"
   start pythonw.exe "Gaming Subtitles\subtitle_overlay.py"
   ```
5. Save the file. You can now double-click this shortcut to launch the app silently in the background!
