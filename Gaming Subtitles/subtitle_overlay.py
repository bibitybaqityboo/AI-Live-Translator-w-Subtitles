#!/usr/bin/env python3
"""Gemini Subtitles - Transparent Overlay Application."""

import asyncio
import json
import math
import os
import queue
import struct
import sys
import threading
import time
from pathlib import Path
from typing import Optional

import customtkinter as ctk
import tkinter as tk
import ctypes

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

import pyaudio
from google import genai
from google.genai import types

# ── App Info ──────────────────────────────────────────────────────────────────
APP_NAME = "Gaming Subtitles"
CONFIG_PATH = Path(__file__).parent / "subtitle_config.json"

# ── Audio ─────────────────────────────────────────────────────────────────────
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_RATE = 16_000
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

# ── Choices ───────────────────────────────────────────────────────────────────
COLORS = ["Yellow", "White", "Cyan", "Green", "Red", "Magenta"]
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
    defaults = {
        "api_key": "", "language": "English (en)", "mic": "cable output", 
        "in_volume": 1.0, "font_size": 36, "color": "Yellow", 
        "y_offset": 85, "outline": 2
    }
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
#  Translation Engine
# ═════════════════════════════════════════════════════════════════════════════
class TranslationEngine:
    def __init__(self, api_key, target_lang, mic_kw, transcript_q, level_q, status_cb, in_volume_ref):
        self.api_key = api_key
        self.target_lang = target_lang
        self.mic_kw = mic_kw
        self.transcript_q = transcript_q
        self.level_q = level_q
        self.status_cb = status_cb
        self.in_volume_ref = in_volume_ref
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

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
                response_modalities=[types.Modality.AUDIO], # Keeps transcription format perfect
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
                    )
                ),
                translation_config=types.TranslationConfig(
                    target_language_code=self.target_lang,
                    echo_target_language=False,
                ),
                input_audio_transcription=types.AudioTranscriptionConfig(),
                output_audio_transcription=types.AudioTranscriptionConfig(),
            )
            audio_in = asyncio.Queue(maxsize=10)

            async with client.aio.live.connect(model=MODEL, config=config) as session:
                self.status_cb("connected", "")
                try:
                    async with asyncio.TaskGroup() as tg:
                        tg.create_task(self._mic(audio_in))
                        tg.create_task(self._send(session, audio_in))
                        tg.create_task(self._recv(session))
                        tg.create_task(self._watch_stop())
                except* asyncio.CancelledError:
                    pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.status_cb("error", str(e))
            self.error_occurred = True
        finally:
            if not getattr(self, "error_occurred", False):
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
                in_vol = self.in_volume_ref[0]
                if in_vol != 1.0:
                    data = adjust_volume(data, in_vol)
                await q.put(data)
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

    async def _recv(self, session):
        try:
            async for resp in session.receive():
                sc = resp.server_content
                if not sc:
                    continue
                if sc.output_transcription and sc.output_transcription.text:
                    self.transcript_q.put(("translation", sc.output_transcription.text))
        except asyncio.CancelledError:
            pass

# ═════════════════════════════════════════════════════════════════════════════
#  Transparent Overlay Window
# ═════════════════════════════════════════════════════════════════════════════
class SubtitleOverlay(tk.Toplevel):
    def __init__(self, parent, font_size_ref, y_offset_ref, color_ref, outline_ref):
        super().__init__(parent)
        self.font_size_ref = font_size_ref
        self.y_offset_ref = y_offset_ref
        self.color_ref = color_ref
        self.outline_ref = outline_ref
        
        # Cover the entire screen
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.config(bg='black')
        self.attributes('-transparentcolor', 'black')

        self.canvas = tk.Canvas(self, bg='black', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        self._make_click_through()

    def _make_click_through(self):
        self.update()
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        try:
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        except Exception:
            pass

    def set_text(self, text):
        self.canvas.delete("all")
        if not text:
            return
            
        font_size = int(self.font_size_ref[0])
        font = ('Segoe UI', font_size, 'bold')
        x = self.winfo_screenwidth() // 2
        y = int(self.winfo_screenheight() * (self.y_offset_ref[0] / 100))
        
        color = self.color_ref[0].lower()
        outline_width = int(self.outline_ref[0])
        
        # Draw outline
        if outline_width > 0:
            for dx in range(-outline_width, outline_width + 1, max(1, outline_width // 2)):
                for dy in range(-outline_width, outline_width + 1, max(1, outline_width // 2)):
                    if dx == 0 and dy == 0: continue
                    self.canvas.create_text(x + dx, y + dy, text=text, font=font, fill='black', justify='center')
                
        # Draw main text
        self.canvas.create_text(x, y, text=text, font=font, fill=color, justify='center')

# ═════════════════════════════════════════════════════════════════════════════
#  Settings Dialog
# ═════════════════════════════════════════════════════════════════════════════
class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, cfg, on_save):
        super().__init__(parent)
        self.cfg = cfg
        self.on_save = on_save
        self.title("Settings")
        self.geometry("400x240")
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
        ctk.CTkLabel(self, text="Desktop Audio (search keyword)", font=(FONT, 13, "bold"),
                     text_color=TEXT).pack(anchor="w", **pad)
        self.mic_var = ctk.StringVar(value=cfg.get("mic", "cable output"))
        ctk.CTkEntry(self, textvariable=self.mic_var, width=360,
                     fg_color=BG_INPUT, border_color=BORDER,
                     text_color=TEXT).pack(padx=20, pady=(4, 0))

        # Save
        ctk.CTkButton(self, text="Save", font=(FONT, 14, "bold"), width=360,
                      height=42, corner_radius=10, fg_color=ACCENT,
                      hover_color=ACCENT_HOVER, text_color="#0d1117",
                      command=self._save).pack(padx=20, pady=(24, 20))

    def _save(self):
        self.cfg["api_key"] = self.key_var.get().strip()
        self.cfg["mic"] = self.mic_var.get().strip()
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
        self.geometry("400x740")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.cfg = load_config()
        self.engine: Optional[TranslationEngine] = None
        self.overlay: Optional[SubtitleOverlay] = None
        self.is_running = False
        self.transcript_q = queue.Queue()
        self.level_q = queue.Queue(maxsize=5)
        self._level_smooth = 0.0
        self._settings_win = None
        
        # References for real-time updating
        self.in_volume_ref = [self.cfg.get("in_volume", 1.0)]
        self.font_size_ref = [self.cfg.get("font_size", 36)]
        self.color_ref = [self.cfg.get("color", "Yellow")]
        self.y_offset_ref = [self.cfg.get("y_offset", 85)]
        self.outline_ref = [self.cfg.get("outline", 2)]
        
        self.current_subtitle = ""
        self.last_text_time = 0

        self._build_ui()
        self._poll()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header.pack(fill="x", padx=20, pady=(12, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="AI", font=(FONT, 20, "bold"),
                     text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(header, text=" Subtitles", font=(FONT, 20),
                     text_color=TEXT).pack(side="left")

        settings_btn = ctk.CTkButton(
            header, text="\u2699", width=36, height=36, corner_radius=18,
            font=(FONT, 18), fg_color="transparent", hover_color=BG_INPUT,
            text_color=TEXT_MUT, command=self._open_settings)
        settings_btn.pack(side="right")

        # Status Area
        status_card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=20, height=80)
        status_card.pack(fill="x", padx=20, pady=16)
        status_card.pack_propagate(False)
        
        status_inner = ctk.CTkFrame(status_card, fg_color="transparent")
        status_inner.place(relx=0.5, rely=0.5, anchor="center")

        self.status_dot = ctk.CTkLabel(status_inner, text="\u25CF", font=(FONT, 14), text_color=TEXT_DIM)
        self.status_dot.pack(side="left", padx=(0, 6))
        self.status_label = ctk.CTkLabel(status_inner, text="Ready", font=(FONT, 14, "bold"), text_color=TEXT_MUT)
        self.status_label.pack(side="left")

        # Controls
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=20, pady=(0, 20))

        # Language Selector
        self.lang_btn = ctk.CTkButton(
            controls, text=self.cfg.get("language", "English (en)"),
            font=(FONT, 14, "bold"), fg_color=BG_INPUT, hover_color=BORDER,
            text_color=TEXT, corner_radius=20, height=44,
            command=self._open_lang_picker)
        self.lang_btn.pack(fill="x", pady=(0, 16))
        
        # Color Selector
        self.color_btn = ctk.CTkButton(
            controls, text=self.cfg.get("color", "Yellow"),
            font=(FONT, 14, "bold"), fg_color=BG_INPUT, hover_color=BORDER,
            text_color=TEXT, corner_radius=20, height=44,
            command=self._open_color_picker)
        self.color_btn.pack(fill="x", pady=(0, 20))

        # Font Size slider
        font_frame = ctk.CTkFrame(controls, fg_color="transparent")
        font_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(font_frame, text="Aa", font=(FONT, 16, "bold"), text_color=TEXT_DIM, width=24).pack(side="left", padx=(0, 8))
        self.font_var = ctk.DoubleVar(value=self.cfg.get("font_size", 36))
        self.font_slider = ctk.CTkSlider(font_frame, variable=self.font_var, from_=16, to=72, number_of_steps=56, command=self._on_font_change)
        self.font_slider.pack(side="left", fill="x", expand=True)
        self.font_label = ctk.CTkLabel(font_frame, text=f"{int(self.font_var.get())}pt", font=(FONT, 12), text_color=TEXT_MUT, width=36)
        self.font_label.pack(side="right", padx=(4, 0))
        
        # Outline Thickness slider
        outline_frame = ctk.CTkFrame(controls, fg_color="transparent")
        outline_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(outline_frame, text="\u25A2", font=(FONT, 20, "bold"), text_color=TEXT_DIM, width=24).pack(side="left", padx=(0, 8))
        self.outline_var = ctk.DoubleVar(value=self.cfg.get("outline", 2))
        self.outline_slider = ctk.CTkSlider(outline_frame, variable=self.outline_var, from_=0, to=8, number_of_steps=8, command=self._on_outline_change)
        self.outline_slider.pack(side="left", fill="x", expand=True)
        self.outline_label = ctk.CTkLabel(outline_frame, text=f"{int(self.outline_var.get())}px", font=(FONT, 12), text_color=TEXT_MUT, width=36)
        self.outline_label.pack(side="right", padx=(4, 0))
        
        # Vertical Position slider
        pos_frame = ctk.CTkFrame(controls, fg_color="transparent")
        pos_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(pos_frame, text="\u2195", font=(FONT, 18, "bold"), text_color=TEXT_DIM, width=24).pack(side="left", padx=(0, 8))
        self.y_offset_var = ctk.DoubleVar(value=self.cfg.get("y_offset", 85))
        self.y_offset_slider = ctk.CTkSlider(pos_frame, variable=self.y_offset_var, from_=0, to=100, number_of_steps=100, command=self._on_pos_change)
        self.y_offset_slider.pack(side="left", fill="x", expand=True)
        self.y_offset_label = ctk.CTkLabel(pos_frame, text=f"{int(self.y_offset_var.get())}%", font=(FONT, 12), text_color=TEXT_MUT, width=36)
        self.y_offset_label.pack(side="right", padx=(4, 0))

        # Input Sensitivity slider
        vol_frame = ctk.CTkFrame(controls, fg_color="transparent")
        vol_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(vol_frame, text="\U0001F3A4", font=(FONT, 16), text_color=TEXT_DIM, width=24).pack(side="left", padx=(0, 8))
        self.in_vol_var = ctk.DoubleVar(value=self.cfg.get("in_volume", 1.0))
        self.in_vol_slider = ctk.CTkSlider(vol_frame, variable=self.in_vol_var, from_=0.0, to=2.0, command=self._on_in_vol_change)
        self.in_vol_slider.pack(side="left", fill="x", expand=True)
        self.in_vol_label = ctk.CTkLabel(vol_frame, text=f"{int(self.in_vol_var.get() * 100)}%", font=(FONT, 12), text_color=TEXT_MUT, width=36)
        self.in_vol_label.pack(side="right", padx=(4, 0))

        # Big Mic Button container
        mic_container = ctk.CTkFrame(self, fg_color="transparent")
        mic_container.pack(fill="both", expand=True)

        self.level_bar = ctk.CTkProgressBar(
            mic_container, width=200, height=4, corner_radius=2,
            fg_color=BG_INPUT, progress_color=ACCENT)
        self.level_bar.place(relx=0.5, rely=0.1, anchor="center")
        self.level_bar.set(0)

        self.start_btn = ctk.CTkButton(
            mic_container, text="START SUBTITLES", width=220, height=54,
            corner_radius=27, font=(FONT, 16, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color="#0d1117", command=self._toggle)
        self.start_btn.place(relx=0.5, rely=0.6, anchor="center")

    def _open_lang_picker(self):
        SelectionDialog(self, "Select Language", LANG_NAMES, self.cfg.get("language"), self._on_lang_selected)
        
    def _open_color_picker(self):
        SelectionDialog(self, "Select Color", COLORS, self.cfg.get("color"), self._on_color_selected)

    def _on_lang_selected(self, val):
        self.cfg["language"] = val
        self.lang_btn.configure(text=val)
        save_config(self.cfg)
        
    def _on_color_selected(self, val):
        self.cfg["color"] = val
        self.color_btn.configure(text=val)
        self.color_ref[0] = val
        save_config(self.cfg)
        if self.overlay: self.overlay.set_text(self.current_subtitle)

    def _on_in_vol_change(self, val):
        self.in_vol_label.configure(text=f"{int(val * 100)}%")
        self.in_volume_ref[0] = val
        self.cfg["in_volume"] = val
        save_config(self.cfg)

    def _on_font_change(self, val):
        val = int(val)
        self.font_label.configure(text=f"{val}pt")
        self.font_size_ref[0] = val
        self.cfg["font_size"] = val
        save_config(self.cfg)
        if self.overlay: self.overlay.set_text(self.current_subtitle)
        
    def _on_outline_change(self, val):
        val = int(val)
        self.outline_label.configure(text=f"{val}px")
        self.outline_ref[0] = val
        self.cfg["outline"] = val
        save_config(self.cfg)
        if self.overlay: self.overlay.set_text(self.current_subtitle)
        
    def _on_pos_change(self, val):
        val = int(val)
        self.y_offset_label.configure(text=f"{val}%")
        self.y_offset_ref[0] = val
        self.cfg["y_offset"] = val
        save_config(self.cfg)
        if self.overlay: self.overlay.set_text(self.current_subtitle)

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

        lang_name = self.cfg.get("language", "English (en)")
        lang_code = LANGUAGES.get(lang_name, "en")

        self.engine = TranslationEngine(
            api_key=key,
            target_lang=lang_code,
            mic_kw=self.cfg.get("mic", "cable output"),
            transcript_q=self.transcript_q,
            level_q=self.level_q,
            status_cb=self._on_status,
            in_volume_ref=self.in_volume_ref
        )
        self.error_occurred = False
        self.engine.start()
        
        if not self.overlay:
            self.overlay = SubtitleOverlay(self, self.font_size_ref, self.y_offset_ref, self.color_ref, self.outline_ref)
        
        self.is_running = True
        self.start_btn.configure(text="STOP SUBTITLES", fg_color=ERROR, hover_color=ERROR_DIM, text_color=BG)
        self.lang_btn.configure(state="disabled")
        self.color_btn.configure(state="disabled")

    def _stop(self):
        if self.engine:
            self.engine.stop()
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
            
        self.is_running = False
        self.start_btn.configure(text="START SUBTITLES", fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#0d1117")
        self.lang_btn.configure(state="normal")
        self.color_btn.configure(state="normal")
        self.level_bar.set(0)
        self._level_smooth = 0.0

    def _on_status(self, status, detail):
        self.after(0, self._update_status, status, detail)

    def _update_status(self, status, detail):
        colors = {"connecting": (WARNING, "Connecting..."),
                  "connected": (SUCCESS, "Live"),
                  "stopped": (TEXT_DIM, "Ready"),
                  "error": (ERROR, f"Error: {detail}")}
        color, text = colors.get(status, (TEXT_DIM, status))
        self.status_dot.configure(text_color=color)
        self.status_label.configure(text=text, text_color=color)
        if status == "error":
            self.error_occurred = True
            
        if status in ("error", "stopped") and not getattr(self, "error_occurred", False):
            self._stop()

    def _open_settings(self):
        if self._settings_win is None or not self._settings_win.winfo_exists():
            self._settings_win = SettingsDialog(self, self.cfg, self._on_settings_save)
            self._settings_win.focus()
        else:
            self._settings_win.focus()

    def _on_settings_save(self, new_cfg):
        self.cfg = new_cfg

    def _poll(self):
        # Update text
        try:
            while True:
                kind, text = self.transcript_q.get_nowait()
                if kind == "translation":
                    self.current_subtitle = text
                    self.last_text_time = time.time()
                    if self.overlay:
                        self.overlay.set_text(self.current_subtitle)
        except queue.Empty:
            pass

        # Clear text after 4 seconds of silence
        if self.current_subtitle and time.time() - self.last_text_time > 4.0:
            self.current_subtitle = ""
            if self.overlay:
                self.overlay.set_text("")

        # Level meter
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

        self.after(30, self._poll)

    def _on_close(self):
        if self.is_running:
            self._stop()
        self.after(200, self.destroy)

if __name__ == "__main__":
    app = App()
    app.mainloop()
