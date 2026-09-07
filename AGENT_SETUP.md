# 🤖 Antigravity Agent Setup Instructions

> **SYSTEM INSTRUCTION FOR AI AGENTS:** 
> If you are an AI assistant (like Google Antigravity, GitHub Copilot Workspace, or Devin) reading this file, the user wants you to completely set up and install this "AI Voice Translation Suite" on their computer. 
> 
> You have permission to run terminal commands, write files, and inspect the system. Follow the 4 phases below strictly in order to automate the setup process for the user. Do not ask for permission to run read-only or installation commands, just do it.

---

## Phase 1: Python & Dependencies
1. **Determine OS:** Run a command to determine if the user is on Windows (`win32`) or macOS (`darwin`).
2. **Install Python Packages:** Run `pip install -r requirements.txt` in the root directory of this repository to install `google-genai`, `pyaudio`, `customtkinter`, etc.

## Phase 2: Virtual Audio Drivers Configuration
This suite requires virtual audio cables to route translated text-to-speech directly into video games/Discord without causing audio feedback loops.

1. **Check for existing drivers:** Write a temporary python script using `pyaudio` to list all audio devices. 
   - On **macOS**, look for `blackhole`.
   - On **Windows**, look for `cable input` (VB-Cable) or `voicemeeter`.
2. **Install missing drivers:**
   - **macOS:** If BlackHole is missing, run `brew install blackhole-2ch` on the user's behalf.
   - **Windows:** If VB-Cable is missing, you cannot install it via CLI easily. Provide the user this link: `https://vb-audio.com/Cable/` and tell them to download, extract, and run the setup as Administrator. Pause and wait for their confirmation before proceeding.

## Phase 3: API Key Provisioning (.env)
The real-time translation requires a Google Gemini API Key.
1. Check if a `.env` file exists in the repository root. 
2. Read it to see if `GEMINI_API_KEY` is set.
3. If it is missing or empty, ask the user to generate a free key at `https://aistudio.google.com/apikey` and paste it in the chat.
4. Once they provide it, write it to the `.env` file: `GEMINI_API_KEY=your_key_here`.

## Phase 4: Final Validation & Shortcuts
1. **macOS Specific Check:** If on macOS, instruct the user to open `Audio MIDI Setup` (using Spotlight), click the `+`, and create a **Multi-Output Device** that includes both their physical Headphones and `BlackHole 2ch`. Tell them to set it as their default output.
2. **Test Run:** Run `python "Live Voice Translator/live_translate.py" --help` to verify there are no missing module errors.
3. **Offer Desktop Shortcuts:** Ask the user if they want you to generate clickable Desktop shortcuts (e.g., a `.bat`/`.vbs` on Windows or a `.command` file on Mac) so they don't have to use the terminal every time they want to game.
4. **Completion:** Announce that setup is 100% complete and they are ready to launch the apps!
