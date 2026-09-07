# AI Voice Translation Suite

A comprehensive suite of real-time AI translation tools designed for gaming, streaming, and Discord. This suite allows you to translate your own voice to other languages in real-time, and perfectly intercept and translate your teammates' voices into your preferred language via text-to-speech or a transparent click-through subtitle overlay.

> **🖥️ Cross-Platform:** Works on both **Windows** and **macOS**. See the [Audio Setup](#-required-audio-software-virtual-cables) section below for platform-specific instructions.

## 🚀 Included Applications

This repository contains four distinct applications, each tailored for a different use case:

1. **[Live Voice Translator](./Live%20Voice%20Translator)**
   - Translates your physical microphone into another language in real-time.
   - Routes the translated audio directly to Discord/Game chat so your teammates hear the AI voice.
   - *Requires: Gemini API Key & VoiceMeeter*

2. **[Offline Translator (Local)](./Offline%20Translator)**
   - 100% offline, private translation of your teammates' voices.
   - Uses `faster-whisper` and `LM Studio` running locally on your hardware.
   - Displays a transparent subtitle overlay on your screen with optional Text-to-Speech (TTS).
   - *Requires: LM Studio, faster-whisper, & VB-Audio Virtual Cable*

3. **[Game Audio Translator](./Game%20Audio%20Translator)**
   - Cloud-based (Gemini API) translation of your teammates' voices.
   - Reads the translated audio out loud to your headphones in real-time.
   - *Requires: Gemini API Key & VB-Audio Virtual Cable*

4. **[Gaming Subtitles](./Gaming%20Subtitles)**
   - Cloud-based (Gemini API) translation of teammates' voices.
   - Provides silent, real-time translated subtitles via an invisible, click-through overlay.
   - *Requires: Gemini API Key & VB-Audio Virtual Cable*

## 🔑 Environment Variables & Setup (.env)
The cloud-based applications in this suite rely on the Google Gemini API to perform lightning-fast, real-time translations. To authorize the app to use the API, you must provide your personal API key.

> [!WARNING]
> For security reasons, API keys should **never** be hardcoded into the scripts or uploaded to GitHub. Instead, we use a hidden `.env` file.

**How to set up your `.env` file:**
1. Go to [Google AI Studio](https://aistudio.google.com/apikey) and generate a free API key.
2. In the root directory of this project (where this README is), create a new text file and name it exactly: `.env`
3. Open the file in Notepad and add the following line:
   ```env
   GEMINI_API_KEY=paste_your_api_key_here
   ```
4. Save the file. The applications will automatically detect and load this key when you launch them.

> [!TIP]
> Your `.env` file is safely ignored by default in the provided `.gitignore` file, so it will not be uploaded to GitHub.

## 🛠️ Setup & Installation

### Option 1: Download Source Code (For Python Users)
1. Click the green **"Code"** button at the top of this GitHub page and select **"Download ZIP"**.
2. Extract the folder to your Desktop.
3. Open a terminal or command prompt inside the folder and install the required libraries by running:
   ```cmd
   pip install -r requirements.txt
   ```

### Option 2: Standalone .exe (Recommended for Gamers)
If you do not have Python installed, simply navigate to the **"Releases"** tab on the right side of the GitHub page. You can download the standalone `.exe` versions of these apps and run them immediately—no installation required!

### 🎧 Required Audio Software (Virtual Cables)
Each application requires specific audio routing to ensure there are no infinite audio loops or echoing while gaming. You will need to download and install the free audio drivers below depending on which app you use:

#### Windows
- [VB-Audio Virtual Cable (Free)](https://vb-audio.com/Cable/) - *Required for capturing teammates' voices without game audio.*
- [VoiceMeeter (Free)](https://vb-audio.com/Voicemeeter/) - *Required for routing your own translated voice to Discord.*

#### macOS
- [BlackHole (Free, Open Source)](https://github.com/ExistentialAudio/BlackHole) - *Virtual audio driver that replaces both VB-Cable and VoiceMeeter on Mac.*

<details>
<summary><b>📖 macOS Setup Guide (Click to expand)</b></summary>

### Step 1: Install BlackHole
```bash
brew install blackhole-2ch
```
If you don't have Homebrew, install it first:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Alternatively, download the installer directly from the [BlackHole GitHub Releases](https://github.com/ExistentialAudio/BlackHole/releases).

### Step 2: Create a Multi-Output Device (to hear audio + route it)
1. Open **Audio MIDI Setup** (search for it in Spotlight with `Cmd + Space`).
2. Click the **`+`** button in the bottom-left corner and select **"Create Multi-Output Device"**.
3. Check **both** your headphones/speakers **and** `BlackHole 2ch`.
4. Right-click the new Multi-Output Device and select **"Use This Device For Sound Output"**.

This lets you hear your game audio while simultaneously routing a copy to BlackHole for the translator to capture.

### Step 3: Configure Discord (for Live Voice Translator)
1. Open Discord → Settings → Voice & Video.
2. Set **Output Device** to your **Multi-Output Device**.
3. The translator app will automatically detect BlackHole as the virtual cable.

### Step 4: Configure the Translator Apps
- The apps will automatically detect `BlackHole` as the virtual audio device on macOS.
- If BlackHole is not detected, you can manually type `blackhole` into the device selection dropdown.

> [!NOTE]
> **macOS Subtitle Overlay:** The subtitle overlay works on macOS but uses a semi-transparent dark background instead of the fully invisible click-through overlay available on Windows. This is a limitation of macOS's window manager. The subtitles will still appear on top of your game in **Windowed Fullscreen** mode.

> [!TIP]
> **macOS Microphone Permissions:** The first time you run the app, macOS will ask for Microphone permission. Click **Allow** in the system popup, or go to **System Settings → Privacy & Security → Microphone** and enable it for Terminal/Python.

</details>

**Please navigate to the specific folder of the app you want to use and read its dedicated `README.md` for precise setup instructions, required dependencies, and step-by-step audio routing guides.**
