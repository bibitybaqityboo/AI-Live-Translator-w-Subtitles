#!/usr/bin/env python3
"""
Gemini Live Translate — Real-time voice-to-voice translation CLI.

Captures microphone audio (16kHz, 16-bit PCM, mono), streams it to the
Gemini Live API using the gemini-3.5-live-translate-preview model, and
plays back translated audio (24kHz) in real time.  Source and translated
transcripts are printed to the console as they arrive.

Usage:
    python live_translate.py                    # defaults: English target
    python live_translate.py --target es        # translate to Spanish
    python live_translate.py --target fr --no-echo  # silent when input is already French

Requirements:
    pip install google-genai pyaudio python-dotenv

Environment:
    Set GEMINI_API_KEY (or GOOGLE_API_KEY) before running.

Note:
    Use headphones!  Without hardware echo cancellation the model may
    hear its own translated output and create a feedback loop.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import signal
import sys
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

import pyaudio
from google import genai
from google.genai import types

import tkinter as tk
import threading
import queue

IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"

if IS_WINDOWS:
    import ctypes

class OverlayController:
    def __init__(self):
        self.q = queue.Queue()
        self.root = None
        self.lbl = None
        threading.Thread(target=self._run_gui, daemon=True).start()
        
    def _run_gui(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.config(bg="black")
        
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x150+0+{h - 250}")
        
        if IS_WINDOWS:
            # Windows: use transparent color key + click-through via Win32 API
            self.root.attributes("-transparentcolor", "black")
            self.root.update_idletasks()
            hwnd = self.root.winfo_id()
            try:
                styles = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, styles | 0x00000020 | 0x00080000)
            except Exception:
                pass
        elif IS_MACOS:
            # macOS: use native alpha transparency (no click-through API available)
            self.root.attributes("-alpha", 0.85)
            self.root.config(bg="gray10")
        else:
            # Linux/other: use alpha transparency
            self.root.attributes("-alpha", 0.85)
            
        # Pick a cross-platform font: Impact on Windows, Helvetica Neue on macOS
        font_family = "Impact" if IS_WINDOWS else "Helvetica Neue"
        bg_color = "black" if IS_WINDOWS else "gray10"
        
        self.lbl = tk.Label(self.root, text="", font=(font_family, 42, "bold"),
                            fg="yellow", bg=bg_color, wraplength=w-100)
        self.lbl.pack(expand=True, fill="both")
        
        self._check_queue()
        self.root.mainloop()
        
    def _check_queue(self):
        try:
            while True:
                msg = self.q.get_nowait()
                if self.lbl:
                    self.lbl.config(text=msg)
        except queue.Empty:
            pass
        if self.root:
            self.root.after(50, self._check_queue)
            
    def update_text(self, text):
        self.q.put(text)

overlay = OverlayController()

# ─── Audio constants ──────────────────────────────────────────────────────────
FORMAT = pyaudio.paInt16       # 16-bit signed PCM
CHANNELS = 1                   # mono
SEND_SAMPLE_RATE = 16_000      # input  (mic → API)
RECEIVE_SAMPLE_RATE = 24_000   # output (API → speaker)
CHUNK_SIZE = 1_600             # 100 ms of audio at 16 kHz  (1600 samples × 2 B)
CHUNK_BYTES = CHUNK_SIZE * 2   # 3 200 bytes per chunk

# ─── Model ────────────────────────────────────────────────────────────────────
MODEL = "gemini-3.5-live-translate-preview"

# ─── Device name keywords (case-insensitive matching) ─────────────────────────
MIC_KEYWORD = "usb pnp audio"           # Your PNP microphone (fallback: default mic)
HEADSET_KEYWORD = "turtle beach"        # Turtle Beach headset (speakers)

# Virtual cable: VB-CABLE on Windows, BlackHole on macOS
if IS_MACOS:
    VBCABLE_KEYWORD = "blackhole"       # BlackHole virtual audio driver (macOS)
else:
    VBCABLE_KEYWORD = "cable input"     # VB-CABLE virtual speaker (Windows)

# ─── ANSI helpers (for pretty console output) ─────────────────────────────────
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"
ITALIC = "\033[3m"


def find_device_index(pya: pyaudio.PyAudio, keyword: str, need_input: bool) -> Optional[int]:
    """Search for an audio device whose name contains *keyword* (case-insensitive).
    If *need_input* is True, look for input devices; otherwise output devices."""
    channel_key = "maxInputChannels" if need_input else "maxOutputChannels"
    for i in range(pya.get_device_count()):
        info = pya.get_device_info_by_index(i)
        if info.get(channel_key, 0) > 0 and keyword.lower() in info.get("name", "").lower():
            return i
    return None


# ═══════════════════════════════════════════════════════════════════════════════
#  Microphone capture
# ═══════════════════════════════════════════════════════════════════════════════
async def capture_microphone(audio_in_q: asyncio.Queue) -> None:
    """
    Opens the USB PnP microphone and continuously reads 100 ms chunks,
    placing raw PCM bytes into *audio_in_q*.
    """
    pya = pyaudio.PyAudio()
    stream: Optional[pyaudio.Stream] = None

    # Find the PNP mic by name
    mic_idx = find_device_index(pya, MIC_KEYWORD, need_input=True)
    if mic_idx is not None:
        mic_info = pya.get_device_info_by_index(mic_idx)
        print(f"{GREEN}✓ Mic found: {mic_info['name']} (Index {mic_idx}){RESET}")
    else:
        mic_info = pya.get_default_input_device_info()
        mic_idx = int(mic_info["index"])
        print(f"{YELLOW}! PNP mic not found, falling back to default: {mic_info['name']}{RESET}")

    try:
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_idx,
            frames_per_buffer=CHUNK_SIZE,
        )
        print(
            f"{GREEN}✓ Microphone open "
            f"({SEND_SAMPLE_RATE} Hz, "
            f"{CHUNK_SIZE}-sample chunks){RESET}"
        )

        while True:
            data = await asyncio.to_thread(
                stream.read, CHUNK_SIZE, exception_on_overflow=False
            )
            await audio_in_q.put(data)
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        print(f"{RED}✗ Microphone error: {exc}{RESET}")
    finally:
        if stream is not None:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        pya.terminate()


# ═══════════════════════════════════════════════════════════════════════════════
#  Send audio upstream
# ═══════════════════════════════════════════════════════════════════════════════
async def send_audio(session, audio_in_q: asyncio.Queue) -> None:
    """
    Reads chunks from *audio_in_q* and sends them to the Gemini session
    using ``send_realtime_input``.
    """
    try:
        while True:
            chunk: bytes = await audio_in_q.get()
            await session.send_realtime_input(
                audio=types.Blob(
                    data=chunk,
                    mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}",
                )
            )
            audio_in_q.task_done()
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        print(f"{RED}✗ Send error: {exc}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
#  Receive translated audio + transcripts
# ═══════════════════════════════════════════════════════════════════════════════
async def receive_responses(session, cable_q: asyncio.Queue) -> None:
    """
    Iterates over the streaming responses from Gemini.  Audio data is
    enqueued for VB-CABLE playback; transcripts are printed inline.
    """
    last_text_time = asyncio.get_event_loop().time()
    
    async def clear_overlay():
        nonlocal last_text_time
        while True:
            await asyncio.sleep(1)
            if asyncio.get_event_loop().time() - last_text_time > 4.0:
                overlay.update_text("")
                
    clear_task = asyncio.create_task(clear_overlay())
    
    try:
        async for response in session.receive():
            sc = response.server_content
            if sc is None:
                continue

            # ── Translated audio data → VB-CABLE → Fortnite ──────────────
            if sc.model_turn:
                for part in sc.model_turn.parts:
                    if part.inline_data and isinstance(part.inline_data.data, bytes):
                        cable_q.put_nowait(part.inline_data.data)

            # ── Input (source) transcript ────────────────────────────────
            if sc.input_transcription and sc.input_transcription.text:
                lang = (
                    f" ({sc.input_transcription.language_code})"
                    if sc.input_transcription.language_code
                    else ""
                )
                print(
                    f"\r{ITALIC}{DIM}[Source{lang}]{RESET} "
                    f"{ITALIC}{sc.input_transcription.text}{RESET}",
                    flush=True,
                )

            # ── Output (translated) transcript ───────────────────────────
            if sc.output_transcription and sc.output_transcription.text:
                lang = (
                    f" ({sc.output_transcription.language_code})"
                    if sc.output_transcription.language_code
                    else ""
                )
                print(
                    f"\r{BOLD}{CYAN}[Translation{lang}]{RESET} "
                    f"{sc.output_transcription.text}",
                    flush=True,
                )
                # Update the Gaming HUD!
                overlay.update_text(sc.output_transcription.text)
                last_text_time = asyncio.get_event_loop().time()

        # If the receive loop exits normally (model finished), drain audio
        # queue to allow playback to complete gracefully.
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        print(f"{RED}✗ Receive error: {exc}{RESET}")
    finally:
        clear_task.cancel()


# ═══════════════════════════════════════════════════════════════════════════════
#  Play translated audio
# ═══════════════════════════════════════════════════════════════════════════════
async def play_to_device(device_name: str, device_keyword: str,
                         audio_q: asyncio.Queue) -> None:
    """
    Opens an output stream on a specific device (found by *device_keyword*)
    and continuously writes PCM chunks from *audio_q*.
    """
    pya = pyaudio.PyAudio()
    stream: Optional[pyaudio.Stream] = None

    dev_idx = find_device_index(pya, device_keyword, need_input=False)
    if dev_idx is not None:
        info = pya.get_device_info_by_index(dev_idx)
        print(f"{GREEN}✓ {device_name} output: {info['name']} (Index {dev_idx}){RESET}")
    else:
        print(f"{YELLOW}! {device_name} not found (searched for '{device_keyword}'). Skipping.{RESET}")
        pya.terminate()
        # Drain the queue so the other output task isn't blocked
        try:
            while True:
                await audio_q.get()
                audio_q.task_done()
        except asyncio.CancelledError:
            pass
        return

    try:
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
            output_device_index=dev_idx,
        )

        while True:
            data: bytes = await audio_q.get()
            await asyncio.to_thread(stream.write, data)
            audio_q.task_done()
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        print(f"{RED}✗ {device_name} playback error: {exc}{RESET}")
    finally:
        if stream is not None:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        pya.terminate()


# ═══════════════════════════════════════════════════════════════════════════════
#  Main orchestrator
# ═══════════════════════════════════════════════════════════════════════════════
async def run(target_lang: str, echo: bool, voice: str) -> None:
    """
    1. Initialise the GenAI client
    2. Build the LiveConnectConfig with translation settings
    3. Open a bidirectional session and fan out to concurrent tasks
    """

    # ── Resolve API key ──────────────────────────────────────────────────
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print(
            f"{RED}✗ No API key found.  "
            f"Set GEMINI_API_KEY or GOOGLE_API_KEY.{RESET}"
        )
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # ── Session config ───────────────────────────────────────────────────
    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=voice
                )
            )
        ),
        translation_config=types.TranslationConfig(
            target_language_code=target_lang,
            echo_target_language=echo,
        ),
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )

    audio_in_q: asyncio.Queue[bytes] = asyncio.Queue(maxsize=10)
    cable_q: asyncio.Queue[bytes] = asyncio.Queue()    # → VB-CABLE → Fortnite

    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  AI Live Translate{RESET}")
    print(f"  Model : {YELLOW}{MODEL}{RESET}")
    print(f"  Target: {CYAN}{target_lang}{RESET}   Echo: {echo}")
    print(f"  Voice : {CYAN}{voice}{RESET}")
    print(f"  Mic   : {CYAN}{MIC_KEYWORD}{RESET}")
    print(f"  Game  : {CYAN}{VBCABLE_KEYWORD}{RESET}  (Fortnite / Discord)")
    print(f"{BOLD}{'═' * 60}{RESET}\n")
    print(f"{DIM}Connecting ...{RESET}")

    try:
        async with client.aio.live.connect(
            model=MODEL, config=config
        ) as session:
            print(f"{GREEN}✓ Connected to Gemini Live.  Start speaking!{RESET}")
            print(f"{DIM}  (Ctrl+C to quit.){RESET}\n")

            async with asyncio.TaskGroup() as tg:
                tg.create_task(capture_microphone(audio_in_q))
                tg.create_task(send_audio(session, audio_in_q))
                tg.create_task(receive_responses(session, cable_q))
                tg.create_task(play_to_device("VB-CABLE", VBCABLE_KEYWORD, cable_q))

    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"\n{RED}✗ Session error: {exc}{RESET}")
    finally:
        print(f"\n{DIM}Connection closed.{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
#  CLI entry point
# ═══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Real-time voice-to-voice translation via Gemini Live API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python live_translate.py --target es            # --> Spanish\n"
            "  python live_translate.py --target fr --voice Aoede # --> French with Aoede voice\n"
            "  python live_translate.py --target ar --no-echo  # --> Arabic, silent on same-lang input\n"
            "\n"
            "Supported languages (70+): en, es, fr, de, it, pt, ar, zh, ja, ko, hi, pl, ...\n"
            "Full list: https://ai.google.dev/gemini-api/docs/live-api/live-translate#supported-languages"
        ),
    )
    parser.add_argument(
        "--target",
        default="en",
        metavar="LANG",
        help="BCP-47 target language code (default: en)",
    )
    parser.add_argument(
        "--echo",
        dest="echo",
        action="store_true",
        default=True,
        help="Echo (parrot) input that is already in the target language (default)",
    )
    parser.add_argument(
        "--no-echo",
        dest="echo",
        action="store_false",
        help="Stay silent when input speech is already in the target language",
    )
    parser.add_argument(
        "--voice",
        dest="voice",
        default="Puck",
        choices=["Puck", "Charon", "Kore", "Fenrir", "Aoede"],
        help="Voice to use for the Gemini Live output (default: Puck)",
    )
    args = parser.parse_args()

    # Graceful shutdown on Windows (where SIGINT doesn't always propagate)
    if sys.platform == "win32":
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        asyncio.run(run(target_lang=args.target, echo=args.echo, voice=args.voice))
    except KeyboardInterrupt:
        print(f"\n{DIM}Interrupted by user.{RESET}")


if __name__ == "__main__":
    main()
