# AI Voice Translation Suite

A comprehensive suite of real-time AI translation tools designed for gaming, streaming, and Discord. This suite allows you to translate your own voice to other languages in real-time, and perfectly intercept and translate your teammates' voices into your preferred language via text-to-speech or a transparent click-through subtitle overlay.

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

For security reasons, API keys should **never** be hardcoded into the scripts or uploaded to GitHub. Instead, we use a hidden `.env` file.

**How to set up your `.env` file:**
1. Go to [Google AI Studio](https://aistudio.google.com/apikey) and generate a free API key.
2. In the root directory of this project (where this README is), create a new text file and name it exactly: `.env`
3. Open the file in Notepad and add the following line:
   ```env
   GEMINI_API_KEY=paste_your_api_key_here
   ```
4. Save the file. The applications will automatically detect and load this key when you launch them.
*(Note: Your `.env` file is safely ignored by default in the provided `.gitignore` file, so it will not be uploaded to GitHub).*

## 🛠️ Setup & Installation

### Option 1: Download Source Code (For Python Users)
1. Click the green **"Code"** button at the top of this GitHub page and select **"Download ZIP"**.
2. Extract the folder to your Desktop.
3. Open a terminal or command prompt inside the folder and install the required libraries by running:
   ```cmd
   pip install -r requirements.txt
   ```

### Option 2: Standalone .exe (Coming Soon)
If you do not have Python installed, check the **"Releases"** tab on the right side of the GitHub page to download the standalone `.exe` versions of these apps.

### Audio Routing (Virtual Cables)
Each application requires specific audio routing (using Virtual Audio Cables) to ensure there are no infinite audio loops or echoing while gaming. 

**Please navigate to the specific folder of the app you want to use and read its dedicated `README.md` for precise setup instructions, required dependencies, and step-by-step audio routing guides.**
