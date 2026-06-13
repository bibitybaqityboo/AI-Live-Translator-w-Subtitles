# AI Voice Translation Suite

A comprehensive suite of real-time AI translation tools designed for gaming, streaming, and Discord. This suite allows you to translate your own voice to other languages in real-time, and perfectly intercept and translate your teammates' voices into English via text-to-speech or a transparent click-through subtitle overlay.

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
   - *Requires: LM Studio, faster-whisper, & VB-Cable*

3. **[Game Audio Translator](./Game%20Audio%20Translator)**
   - Cloud-based (Gemini API) translation of your teammates' voices.
   - Reads the translated audio out loud to your headphones in real-time.
   - *Requires: Gemini API Key & VB-Cable*

4. **[Gaming Subtitles](./Gaming%20Subtitles)**
   - Cloud-based (Gemini API) translation of teammates' voices.
   - Provides silent, real-time translated subtitles via an invisible, click-through overlay.
   - *Requires: Gemini API Key & VB-Cable*

## 🛠️ Setup & Installation

Each application requires specific audio routing (using Virtual Audio Cables) to ensure there are no infinite audio loops or echoing while gaming. 

**Please navigate to the specific folder of the app you want to use and read its dedicated `README.md` for precise setup instructions, required dependencies, and step-by-step audio routing guides.**

## 🔑 Environment Variables
For the cloud-based apps, you must create a `.env` file in the root directory of this project with your Google Gemini API key:
```env
GEMINI_API_KEY=your_api_key_here
```
*(Note: Never upload your `.env` file to GitHub! It is safely ignored by default in the provided `.gitignore`)*
