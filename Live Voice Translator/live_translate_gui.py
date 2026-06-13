#!/usr/bin/env python3
"""Gemini Live Translate - Modern GUI Application."""

import asyncio
import json
import math
import os
import queue
import struct
import sys
import threading

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass
import time
from pathlib import Path
from typing import Optional

import customtkinter as ctk
import pyaudio
from google import genai
from google.genai import types

# ── App Info ──────────────────────────────────────────────────────────────────
APP_NAME = "Live Voice Translator"
CONFIG_PATH = Path(__file__).parent / "translate_config.json"

# ── Audio ─────────────────────────────────────────────────────────────────────
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_RATE = 16_000
RECV_RATE = 24_000
CHUNK = 1_600
MODEL = "gemini-3.5-live-translate-preview"

# ── Theme ─────────────────────────────────────────────────────────────────────
BG           = "#1e1e1e"
BG_CARD      = "#2b2b2b"
BG_INPUT     = "#333333"
BORDER       = "#444746"
ACCENT       = "#a8c7fa"
ACCENT_HOVER = "#d3e3fd"
SUCCESS      = "#6dd58c"
SUCCESS_DIM  = "#146c2e"
ERROR        = "#f2b8b5"
ERROR_DIM    = "#8c1d18"
WARNING      = "#f9ab00"
TEXT         = "#e3e3e3"
TEXT_MUT     = "#c4c7c5"
TEXT_DIM     = "#8e918f"
FONT         = "Segoe UI"

# ── Languages ─────────────────────────────────────────────────────────────────
LANGUAGES = {
    "Afrikaans (af)": "af", "Albanian (sq)": "sq", "Amharic (am)": "am",
    "Arabic (ar)": "ar", "Armenian (hy)": "hy", "Azerbaijani (az)": "az",
    "Basque (eu)": "eu", "Belarusian (be)": "be", "Bengali (bn)": "bn",
    "Bosnian (bs)": "bs", "Bulgarian (bg)": "bg", "Catalan (ca)": "ca",
    "Cebuano (ceb)": "ceb", "Chinese (zh)": "zh", "Corsican (co)": "co",
    "Croatian (hr)": "hr", "Czech (cs)": "cs", "Danish (da)": "da",
    "Dutch (nl)": "nl", "English (en)": "en", "Esperanto (eo)": "eo",
    "Estonian (et)": "et", "Filipino (tl)": "tl", "Finnish (fi)": "fi",
    "French (fr)": "fr", "Galician (gl)": "gl", "Georgian (ka)": "ka",
    "German (de)": "de", "Greek (el)": "el", "Gujarati (gu)": "gu",
    "Haitian Creole (ht)": "ht", "Hausa (ha)": "ha", "Hawaiian (haw)": "haw",
    "Hebrew (he)": "he", "Hindi (hi)": "hi", "Hmong (hmn)": "hmn",
    "Hungarian (hu)": "hu", "Icelandic (is)": "is", "Igbo (ig)": "ig",
    "Indonesian (id)": "id", "Irish (ga)": "ga", "Italian (it)": "it",
    "Japanese (ja)": "ja", "Javanese (jv)": "jv", "Kannada (kn)": "kn",
    "Kazakh (kk)": "kk", "Khmer (km)": "km", "Korean (ko)": "ko",
    "Kurdish (ku)": "ku", "Kyrgyz (ky)": "ky", "Lao (lo)": "lo",
    "Latin (la)": "la", "Latvian (lv)": "lv", "Lithuanian (lt)": "lt",
    "Luxembourgish (lb)": "lb", "Macedonian (mk)": "mk", "Malagasy (mg)": "mg",
    "Malay (ms)": "ms", "Malayalam (ml)": "ml", "Maltese (mt)": "mt",
    "Maori (mi)": "mi", "Marathi (mr)": "mr", "Mongolian (mn)": "mn",
    "Myanmar (my)": "my", "Nepali (ne)": "ne", "Norwegian (no)": "no",
    "Nyanja (ny)": "ny", "Pashto (ps)": "ps", "Persian (fa)": "fa",
    "Polish (pl)": "pl", "Portuguese (pt)": "pt", "Punjabi (pa)": "pa",
    "Romanian (ro)": "ro", "Russian (ru)": "ru", "Samoan (sm)": "sm",
    "Scottish Gaelic (gd)": "gd", "Serbian (sr)": "sr", "Shona (sn)": "sn",
    "Sindhi (sd)": "sd", "Sinhala (si)": "si", "Slovak (sk)": "sk",
    "Slovenian (sl)": "sl", "Somali (so)": "so", "Southern Sotho (st)": "st",
    "Spanish (es)": "es", "Sundanese (su)": "su", "Swahili (sw)": "sw",
    "Swedish (sv)": "sv", "Tajik (tg)": "tg", "Tamil (ta)": "ta",
    "Tatar (tt)": "tt", "Telugu (te)": "te", "Thai (th)": "th",
    "Turkish (tr)": "tr", "Turkmen (tk)": "tk", "Ukrainian (uk)": "uk",
    "Urdu (ur)": "ur", "Uyghur (ug)": "ug", "Uzbek (uz)": "uz",
    "Vietnamese (vi)": "vi", "Welsh (cy)": "cy", "Xhosa (xh)": "xh",
    "Yiddish (yi)": "yi", "Yoruba (yo)": "yo", "Zulu (zu)": "zu"
}
LANG_NAMES = list(LANGUAGES.keys())

# ── Voices ────────────────────────────────────────────────────────────────────
VOICES = {
    "Puck (Upbeat)": "Puck",
    "Charon (Smooth)": "Charon",
    "Kore (Firm)": "Kore",
    "Fenrir (Energetic)": "Fenrir",
    "Aoede (Breezy)": "Aoede",
    "Vega (Bright/High)": "Vega",
    "Lyra (Bright/High)": "Lyra",
    "Capella (British/High)": "Capella"
}
VOICE_NAMES = list(VOICES.keys())

# ═════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═════════════════════════════════════════════════════════════════════════════
def find_device(pya, keyword, is_input):
    key = "maxInputChannels" if is_input else "maxOutputChannels"
    for i in range(pya.get_device_count()):
        info = pya.get_device_info_by_index(i)
        if info.get(key, 0) > 0 and keyword.lower() in info.get("name", "").lower():
            return i, info.get("name", "")
    return None, None

def get_devices(is_input):
    pya = pyaudio.PyAudio()
    key = "maxInputChannels" if is_input else "maxOutputChannels"
    devs = []
    for i in range(pya.get_device_count()):
        info = pya.get_device_info_by_index(i)
        if info.get(key, 0) > 0:
            devs.append(info.get("name", f"Device {i}"))
    pya.terminate()
    return devs

def rms(data: bytes) -> float:
    if len(data) < 2:
        return 0.0
    n = len(data) // 2
    shorts = struct.unpack(f"<{n}h", data[:n * 2])
    s = sum(x * x for x in shorts)
    return min(math.sqrt(s / n) / 32768.0 * 4.0, 1.0)

def adjust_volume(data: bytes, volume: float) -> bytes:
    if volume == 1.0 or not data:
        return data
    n = len(data) // 2
    shorts = struct.unpack(f"<{n}h", data[:n * 2])
    shorts = [max(-32768, min(32767, int(x * volume))) for x in shorts]
    return struct.pack(f"<{n}h", *shorts)

# ── Config ────────────────────────────────────────────────────────────────────
def load_config():
    defaults = {"api_key": "", "language": "Spanish (es)", "voice": "Puck (Upbeat)", "mic": "usb pnp audio",
                "output": "cable input", "echo": True, "volume": 1.0, "monitor_mic": False}
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                d = json.load(f)
                defaults.update(d)
    except Exception:
        pass
        
    if not defaults.get("api_key"):
        defaults["api_key"] = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        
    return defaults

def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

# ═════════════════════════════════════════════════════════════════════════════
#  Translation Engine (runs in background thread)
# ═════════════════════════════════════════════════════════════════════════════
class TranslationEngine:
    def __init__(self, api_key, target_lang, voice_name, echo, mic_kw, out_kw,
                 transcript_q, level_q, status_cb, volume_ref, monitor_ref):
        self.api_key = api_key
        self.target_lang = target_lang
        self.voice_name = voice_name
        self.echo = echo
        self.mic_kw = mic_kw
        self.out_kw = out_kw
        self.transcript_q = transcript_q
        self.level_q = level_q
        self.status_cb = status_cb
        self.volume_ref = volume_ref
        self.monitor_ref = monitor_ref
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.monitor_q = asyncio.Queue(maxsize=10)

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_thread, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._loop:
            self._loop.call_soon_threadsafe(self._cancel_tasks)

    def _cancel_tasks(self):
        for t in asyncio.all_tasks(self._loop):
            t.cancel()

    def _run_thread(self):
        try:
            asyncio.run(self._main())
        except Exception as e:
            self.status_cb("error", str(e))

    async def _main(self):
        self._loop = asyncio.get_event_loop()
        self.status_cb("connecting", "")
        try:
            client = genai.Client(api_key=self.api_key)
            config = types.LiveConnectConfig(
                response_modalities=[types.Modality.AUDIO],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.voice_name
                        )
                    )
                ),
                translation_config=types.TranslationConfig(
                    target_language_code=self.target_lang,
                    echo_target_language=self.echo,
                ),
                input_audio_transcription=types.AudioTranscriptionConfig(),
                output_audio_transcription=types.AudioTranscriptionConfig(),
            )
            audio_in = asyncio.Queue(maxsize=10)
            audio_out = asyncio.Queue()

            async with client.aio.live.connect(model=MODEL, config=config) as session:
                self.status_cb("connected", "")
                try:
                    async with asyncio.TaskGroup() as tg:
                        tg.create_task(self._mic(audio_in))
                        tg.create_task(self._send(session, audio_in))
                        tg.create_task(self._recv(session, audio_out))
                        tg.create_task(self._play(audio_out))
                        tg.create_task(self._monitor_play())
                        tg.create_task(self._watch_stop())
                except* asyncio.CancelledError:
                    pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.status_cb("error", str(e))
        finally:
            self.status_cb("stopped", "")

    async def _watch_stop(self):
        while not self._stop.is_set():
            await asyncio.sleep(0.2)
        raise asyncio.CancelledError

    async def _mic(self, q):
        pya = pyaudio.PyAudio()
        idx, name = find_device(pya, self.mic_kw, True)
        if idx is None:
            info = pya.get_default_input_device_info()
            idx = int(info["index"])
            name = info["name"]
        stream = await asyncio.to_thread(
            pya.open, format=FORMAT, channels=CHANNELS, rate=SEND_RATE,
            input=True, input_device_index=idx, frames_per_buffer=CHUNK)
        try:
            while not self._stop.is_set():
                data = await asyncio.to_thread(stream.read, CHUNK, exception_on_overflow=False)
                await q.put(data)
                if self.monitor_ref[0]:
                    try:
                        self.monitor_q.put_nowait(data)
                    except asyncio.QueueFull:
                        pass
                try:
                    self.level_q.put_nowait(rms(data))
                except queue.Full:
                    pass
        except asyncio.CancelledError:
            pass
        finally:
            stream.stop_stream(); stream.close(); pya.terminate()

    async def _send(self, session, q):
        try:
            while True:
                chunk = await q.get()
                await session.send_realtime_input(
                    audio=types.Blob(data=chunk, mime_type=f"audio/pcm;rate={SEND_RATE}"))
                q.task_done()
        except asyncio.CancelledError:
            pass

    async def _recv(self, session, q):
        try:
            async for resp in session.receive():
                sc = resp.server_content
                if not sc:
                    continue
                if sc.model_turn:
                    for p in sc.model_turn.parts:
                        if p.inline_data and isinstance(p.inline_data.data, bytes):
                            q.put_nowait(p.inline_data.data)
                if sc.input_transcription and sc.input_transcription.text:
                    lang = sc.input_transcription.language_code or "?"
                    self.transcript_q.put(("source", lang, sc.input_transcription.text))
                if sc.output_transcription and sc.output_transcription.text:
                    lang = sc.output_transcription.language_code or "?"
                    self.transcript_q.put(("translation", lang, sc.output_transcription.text))
        except asyncio.CancelledError:
            pass

    async def _play(self, q):
        pya = pyaudio.PyAudio()
        idx, _ = find_device(pya, self.out_kw, False)
        if idx is None:
            pya.terminate()
            try:
                while True:
                    await q.get(); q.task_done()
            except asyncio.CancelledError:
                pass
            return
        stream = await asyncio.to_thread(
            pya.open, format=FORMAT, channels=CHANNELS, rate=RECV_RATE,
            output=True, output_device_index=idx)
        try:
            while True:
                data = await q.get()
                vol = self.volume_ref[0]
                if vol != 1.0:
                    data = adjust_volume(data, vol)
                await asyncio.to_thread(stream.write, data)
                q.task_done()
        except asyncio.CancelledError:
            pass
        finally:
            stream.stop_stream(); stream.close(); pya.terminate()

    async def _monitor_play(self):
        pya = pyaudio.PyAudio()
        try:
            info = pya.get_default_output_device_info()
            idx = int(info["index"])
            stream = await asyncio.to_thread(
                pya.open, format=FORMAT, channels=CHANNELS, rate=SEND_RATE,
                output=True, output_device_index=idx)
        except Exception:
            pya.terminate()
            return
            
        try:
            while not self._stop.is_set():
                try:
                    data = self.monitor_q.get_nowait()
                    await asyncio.to_thread(stream.write, data)
                except asyncio.QueueEmpty:
                    await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        finally:
            stream.stop_stream(); stream.close(); pya.terminate()

# ═════════════════════════════════════════════════════════════════════════════
#  Settings Dialog
# ═════════════════════════════════════════════════════════════════════════════
class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, cfg, on_save):
        super().__init__(parent)
        self.cfg = cfg
        self.on_save = on_save
        self.title("Settings")
        self.geometry("400x420")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.transient(parent)
        self.grab_set()

        pad = {"padx": 20, "pady": (10, 0)}

        # API Key
        ctk.CTkLabel(self, text="API Key", font=(FONT, 13, "bold"),
                     text_color=TEXT).pack(anchor="w", **pad)
        self.key_var = ctk.StringVar(value=cfg.get("api_key", ""))
        ctk.CTkEntry(self, textvariable=self.key_var, show="*", width=360,
                     fg_color=BG_INPUT, border_color=BORDER,
                     text_color=TEXT).pack(padx=20, pady=(4, 0))
        ctk.CTkLabel(self, text="Get one at aistudio.google.com/apikey",
                     font=(FONT, 11), text_color=TEXT_DIM).pack(anchor="w", padx=20, pady=(2, 0))

        # Mic keyword
        ctk.CTkLabel(self, text="Microphone (search keyword)", font=(FONT, 13, "bold"),
                     text_color=TEXT).pack(anchor="w", **pad)
        self.mic_var = ctk.StringVar(value=cfg.get("mic", "usb pnp audio"))
        ctk.CTkEntry(self, textvariable=self.mic_var, width=360,
                     fg_color=BG_INPUT, border_color=BORDER,
                     text_color=TEXT).pack(padx=20, pady=(4, 0))

        # Output keyword
        ctk.CTkLabel(self, text="Output Device (search keyword)", font=(FONT, 13, "bold"),
                     text_color=TEXT).pack(anchor="w", **pad)
        self.out_var = ctk.StringVar(value=cfg.get("output", "cable input"))
        ctk.CTkEntry(self, textvariable=self.out_var, width=360,
                     fg_color=BG_INPUT, border_color=BORDER,
                     text_color=TEXT).pack(padx=20, pady=(4, 0))

        # Echo toggle
        self.echo_var = ctk.BooleanVar(value=cfg.get("echo", True))
        ctk.CTkSwitch(self, text="Echo when input is already target language",
                      variable=self.echo_var, font=(FONT, 12),
                      text_color=TEXT_MUT, progress_color=ACCENT,
                      fg_color=BG_INPUT).pack(anchor="w", padx=20, pady=(16, 0))

        # Monitor toggle
        self.monitor_var = ctk.BooleanVar(value=cfg.get("monitor_mic", False))
        ctk.CTkSwitch(self, text="Monitor Mic (Hear yourself)",
                      variable=self.monitor_var, font=(FONT, 12),
                      text_color=TEXT_MUT, progress_color=ACCENT,
                      fg_color=BG_INPUT).pack(anchor="w", padx=20, pady=(12, 0))

        # Save
        ctk.CTkButton(self, text="Save", font=(FONT, 14, "bold"), width=360,
                      height=42, corner_radius=10, fg_color=ACCENT,
                      hover_color=ACCENT_HOVER, text_color="#0d1117",
                      command=self._save).pack(padx=20, pady=(24, 20))

    def _save(self):
        self.cfg["api_key"] = self.key_var.get().strip()
        self.cfg["mic"] = self.mic_var.get().strip()
        self.cfg["output"] = self.out_var.get().strip()
        self.cfg["echo"] = self.echo_var.get()
        self.cfg["monitor_mic"] = self.monitor_var.get()
        save_config(self.cfg)
        self.on_save(self.cfg)
        self.destroy()

# ═════════════════════════════════════════════════════════════════════════════
#  Selection Dialog
# ═════════════════════════════════════════════════════════════════════════════
class SelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, items, current_val, on_select):
        super().__init__(parent)
        self.title(title)
        self.geometry("340x500")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.transient(parent)
        self.grab_set()

        self.items = items
        self.on_select = on_select
        self.current_val = current_val

        # Search bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=16, pady=(16, 8))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        self.search_entry = ctk.CTkEntry(
            search_frame, textvariable=self.search_var, placeholder_text="Search...",
            height=40, corner_radius=20, fg_color=BG_INPUT, border_color=BORDER,
            text_color=TEXT, font=(FONT, 14)
        )
        self.search_entry.pack(fill="x")

        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.buttons = []
        self._populate(self.items)

    def _populate(self, items):
        for btn in self.buttons:
            btn.destroy()
        self.buttons.clear()

        for item in items:
            is_active = (item == self.current_val)
            fg = ACCENT if is_active else "transparent"
            text_col = BG if is_active else TEXT
            hov = ACCENT_HOVER if is_active else BG_INPUT

            btn = ctk.CTkButton(
                self.scroll, text=item, anchor="w", height=44, corner_radius=12,
                fg_color=fg, hover_color=hov, text_color=text_col,
                font=(FONT, 14, "bold" if is_active else "normal"),
                command=lambda val=item: self._select(val)
            )
            btn.pack(fill="x", pady=2, padx=8)
            self.buttons.append(btn)

    def _on_search(self, *args):
        query = self.search_var.get().lower()
        filtered = [item for item in self.items if query in item.lower()]
        self._populate(filtered)

    def _select(self, val):
        self.on_select(val)
        self.destroy()

# ═════════════════════════════════════════════════════════════════════════════
#  Main Application
# ═════════════════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title(APP_NAME)
        self.geometry("440x740")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.cfg = load_config()
        self.engine: Optional[TranslationEngine] = None
        self.is_running = False
        self.transcript_q = queue.Queue()
        self.level_q = queue.Queue(maxsize=5)
        self._level_smooth = 0.0
        self._pulse_phase = 0.0
        self._settings_win = None
        self.volume_ref = [self.cfg.get("volume", 1.0)]
        self.monitor_ref = [self.cfg.get("monitor_mic", False)]

        self._build_ui()
        self._poll()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header.pack(fill="x", padx=20, pady=(12, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="AI", font=(FONT, 20, "bold"),
                     text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(header, text=" Translate", font=(FONT, 20),
                     text_color=TEXT).pack(side="left")

        settings_btn = ctk.CTkButton(
            header, text="\u2699", width=36, height=36, corner_radius=18,
            font=(FONT, 18), fg_color="transparent", hover_color=BG_INPUT,
            text_color=TEXT_MUT, command=self._open_settings)
        settings_btn.pack(side="right")

        # Transcript Area (Large Card)
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=20)
        card.pack(fill="both", expand=True, padx=20, pady=16)

        tr_header = ctk.CTkFrame(card, fg_color="transparent")
        tr_header.pack(fill="x", padx=20, pady=(16, 8))
        
        self.status_dot = ctk.CTkLabel(tr_header, text="\u25CF", font=(FONT, 12), text_color=TEXT_DIM)
        self.status_dot.pack(side="left", padx=(0, 6))
        self.status_label = ctk.CTkLabel(tr_header, text="Ready", font=(FONT, 13), text_color=TEXT_MUT)
        self.status_label.pack(side="left")

        ctk.CTkButton(tr_header, text="Clear", width=50, height=28,
                      corner_radius=14, font=(FONT, 12), fg_color=BG_INPUT,
                      hover_color=BORDER, text_color=TEXT_MUT,
                      command=self._clear_transcript).pack(side="right")

        self.transcript = ctk.CTkTextbox(
            card, fg_color="transparent", text_color=TEXT, font=(FONT, 15),
            wrap="word", activate_scrollbars=False)
        self.transcript.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Text tags
        self.transcript._textbox.tag_configure("source_tag", foreground=TEXT_MUT, font=(FONT, 12, "bold"))
        self.transcript._textbox.tag_configure("source_text", foreground=TEXT_MUT, font=(FONT, 15))
        self.transcript._textbox.tag_configure("trans_tag", foreground=ACCENT, font=(FONT, 12, "bold"))
        self.transcript._textbox.tag_configure("trans_text", foreground=TEXT, font=(FONT, 18, "bold"))

        # Bottom Controls
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent", height=140)
        bottom_frame.pack(fill="x", padx=20, pady=(0, 20))
        bottom_frame.pack_propagate(False)

        # Selectors bar
        sel_bar = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        sel_bar.pack(fill="x", pady=(0, 16))

        self.lang_btn = ctk.CTkButton(
            sel_bar, text=self.cfg.get("language", "Spanish (es)"),
            font=(FONT, 14, "bold"), fg_color=BG_INPUT, hover_color=BORDER,
            text_color=TEXT, corner_radius=20, height=40,
            command=self._open_lang_picker)
        self.lang_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))

        self.voice_btn = ctk.CTkButton(
            sel_bar, text=self.cfg.get("voice", "Puck (Upbeat)"),
            font=(FONT, 14, "bold"), fg_color=BG_INPUT, hover_color=BORDER,
            text_color=TEXT, corner_radius=20, height=40,
            command=self._open_voice_picker)
        self.voice_btn.pack(side="right", expand=True, fill="x", padx=(8, 0))

        # Volume slider
        vol_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        vol_frame.pack(fill="x", pady=(0, 16))
        
        ctk.CTkLabel(vol_frame, text="\U0001F508", font=(FONT, 16), text_color=TEXT_DIM).pack(side="left", padx=(0, 8))
        self.vol_var = ctk.DoubleVar(value=self.cfg.get("volume", 1.0))
        self.vol_slider = ctk.CTkSlider(vol_frame, variable=self.vol_var, from_=0.0, to=2.0, command=self._on_vol_change)
        self.vol_slider.pack(side="left", fill="x", expand=True)
        self.vol_label = ctk.CTkLabel(vol_frame, text=f"{int(self.vol_var.get() * 100)}%", font=(FONT, 12), text_color=TEXT_MUT, width=40)
        self.vol_label.pack(side="right", padx=(8, 0))

        # Big Mic Button container
        mic_container = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        mic_container.pack(fill="both", expand=True)

        self.level_bar = ctk.CTkProgressBar(
            mic_container, width=200, height=4, corner_radius=2,
            fg_color=BG_INPUT, progress_color=ACCENT)
        self.level_bar.place(relx=0.5, rely=0.1, anchor="center")
        self.level_bar.set(0)

        self.start_btn = ctk.CTkButton(
            mic_container, text="\U0001F3A4", width=72, height=72,
            corner_radius=36, font=(FONT, 28),
            fg_color=BG_INPUT, hover_color=BORDER,
            text_color=ACCENT, command=self._toggle)
        self.start_btn.place(relx=0.5, rely=0.6, anchor="center")

    def _open_lang_picker(self):
        SelectionDialog(self, "Select Language", LANG_NAMES, self.cfg.get("language"), self._on_lang_selected)

    def _on_lang_selected(self, val):
        self.cfg["language"] = val
        self.lang_btn.configure(text=val)
        save_config(self.cfg)

    def _open_voice_picker(self):
        SelectionDialog(self, "Select Voice", VOICE_NAMES, self.cfg.get("voice"), self._on_voice_selected)

    def _on_voice_selected(self, val):
        self.cfg["voice"] = val
        self.voice_btn.configure(text=val)
        save_config(self.cfg)

    def _on_vol_change(self, val):
        self.vol_label.configure(text=f"{int(val * 100)}%")
        self.volume_ref[0] = val
        self.cfg["volume"] = val
        save_config(self.cfg)

    def _toggle(self):
        if self.is_running:
            self._stop()
        else:
            self._start()

    def _start(self):
        key = self.cfg.get("api_key", "").strip()
        if not key:
            self._open_settings()
            return

        lang_name = self.cfg.get("language", "Spanish (es)")
        lang_code = LANGUAGES.get(lang_name, "es")
        voice_name_full = self.cfg.get("voice", "Puck (Upbeat)")
        voice_name = VOICES.get(voice_name_full, "Puck")

        self.engine = TranslationEngine(
            api_key=key,
            target_lang=lang_code,
            voice_name=voice_name,
            echo=self.cfg.get("echo", True),
            mic_kw=self.cfg.get("mic", "usb pnp audio"),
            out_kw=self.cfg.get("output", "cable input"),
            transcript_q=self.transcript_q,
            level_q=self.level_q,
            status_cb=self._on_status,
            volume_ref=self.volume_ref,
            monitor_ref=self.monitor_ref
        )
        self.engine.start()
        self.is_running = True
        self.start_btn.configure(text="\u23F9", fg_color=ERROR, hover_color=ERROR_DIM, text_color=BG)
        self.lang_btn.configure(state="disabled")
        self.voice_btn.configure(state="disabled")

    def _stop(self):
        if self.engine:
            self.engine.stop()
        self.is_running = False
        self.start_btn.configure(text="\U0001F3A4", fg_color=BG_INPUT, hover_color=BORDER, text_color=ACCENT)
        self.lang_btn.configure(state="normal")
        self.voice_btn.configure(state="normal")
        self.level_bar.set(0)
        self._level_smooth = 0.0

    def _on_status(self, status, detail):
        self.after(0, self._update_status, status, detail)

    def _update_status(self, status, detail):
        colors = {"connecting": (WARNING, "Connecting..."),
                  "connected": (SUCCESS, "Connected - Translating"),
                  "stopped": (TEXT_DIM, "Ready"),
                  "error": (ERROR, f"Error: {detail}")}
        color, text = colors.get(status, (TEXT_DIM, status))
        self.status_dot.configure(text_color=color)
        self.status_label.configure(text=text, text_color=color)
        if status in ("error", "stopped"):
            self._stop()

    def _open_settings(self):
        if self._settings_win is None or not self._settings_win.winfo_exists():
            self._settings_win = SettingsDialog(self, self.cfg, self._on_settings_save)
            self._settings_win.focus()
        else:
            self._settings_win.focus()

    def _on_settings_save(self, new_cfg):
        self.cfg = new_cfg
        self.monitor_ref[0] = self.cfg.get("monitor_mic", False)

    def _clear_transcript(self):
        self.transcript.configure(state="normal")
        self.transcript.delete("1.0", "end")
        self.transcript.configure(state="disabled")

    def _poll(self):
        try:
            while True:
                kind, lang, text = self.transcript_q.get_nowait()
                self.transcript.configure(state="normal")
                if kind == "source":
                    self.transcript.insert("end", f"[{lang}] ", "source_tag")
                    self.transcript.insert("end", f"{text}\n\n", "source_text")
                else:
                    self.transcript.insert("end", f"[{lang}] ", "trans_tag")
                    self.transcript.insert("end", f"{text}\n\n", "trans_text")
                self.transcript.configure(state="disabled")
                self.transcript.see("end")
        except queue.Empty:
            pass

        try:
            while True:
                lvl = self.level_q.get_nowait()
                self._level_smooth = self._level_smooth * 0.4 + lvl * 0.6
        except queue.Empty:
            pass

        if self.is_running:
            self.level_bar.set(self._level_smooth)
            self._level_smooth *= 0.70  # Faster decay for snappiness
        else:
            self._level_smooth *= 0.5
            self.level_bar.set(max(self._level_smooth, 0))

        self.after(30, self._poll) # 30ms for snappier UI polling

    def _on_close(self):
        if self.is_running:
            self._stop()
        self.after(200, self.destroy)


if __name__ == "__main__":
    app = App()
    app.mainloop()
