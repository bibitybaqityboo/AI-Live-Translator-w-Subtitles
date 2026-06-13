#!/usr/bin/env python3
"""Local Voice Translate - Offline (LM Studio) Version with Subtitles."""

import asyncio
import io
import json
import math
import os
import queue
import struct
import sys
import threading
import time
import wave
import ctypes
from pathlib import Path
from typing import Optional

import customtkinter as ctk
import tkinter as tk
import edge_tts
import pyaudio
import pygame
import pygame._sdl2.audio as sdl2_audio
from openai import AsyncOpenAI

# ── App Info ──────────────────────────────────────────────────────────────────
APP_NAME = "Offline Translator"
CONFIG_PATH = Path(__file__).parent / "translate_local_config.json"
TEMP_MP3 = Path(__file__).parent / "temp_tts.mp3"
TEMP_WAV = Path(__file__).parent / "temp_stt.wav"

# ── Audio ─────────────────────────────────────────────────────────────────────
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_RATE = 16_000
CHUNK = 1_600

# ── Theme ─────────────────────────────────────────────────────────────────────
BG           = "#0d1117"
BG_CARD      = "#161b22"
BG_INPUT     = "#21262d"
BORDER       = "#30363d"
ACCENT       = "#58a6ff"
ACCENT_HOVER = "#79c0ff"
SUCCESS      = "#3fb950"
SUCCESS_DIM  = "#238636"
ERROR        = "#f85149"
WARNING      = "#d29922"
TEXT         = "#e6edf3"
TEXT_MUT     = "#8b949e"
TEXT_DIM     = "#484f58"
FONT         = "Segoe UI"

# ── Languages ─────────────────────────────────────────────────────────────────
LANGUAGES = {
    "Spanish": "es", "French": "fr", "German": "de",
    "Italian": "it", "Portuguese": "pt", "Arabic": "ar",
    "Chinese": "zh", "Japanese": "ja", "Korean": "ko",
    "Hindi": "hi", "Russian": "ru", "English": "en",
}
LANG_NAMES = list(LANGUAGES.keys())

COLORS = ["Yellow", "White", "Cyan", "Green", "Red", "Magenta"]

EDGE_VOICES = {
    "es": "es-ES-AlvaroNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",
    "it": "it-IT-DiegoNeural",
    "pt": "pt-BR-AntonioNeural",
    "ar": "ar-SA-HamedNeural",
    "zh": "zh-CN-YunxiNeural",
    "ja": "ja-JP-KeitaNeural",
    "ko": "ko-KR-InJoonNeural",
    "hi": "hi-IN-MadhurNeural",
    "ru": "ru-RU-DmitryNeural",
    "en": "en-US-ChristopherNeural"
}

# ═════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═════════════════════════════════════════════════════════════════════════════
def find_input_device(pya, keyword):
    for i in range(pya.get_device_count()):
        info = pya.get_device_info_by_index(i)
        if info.get("maxInputChannels", 0) > 0 and keyword.lower() in info.get("name", "").lower():
            return i, info.get("name", "")
    return None, None

def find_pygame_output(keyword):
    try:
        pygame.init()
        for name in sdl2_audio.get_audio_device_names(False):
            if keyword.lower() in name.lower():
                return name
    except Exception:
        pass
    return None

def rms(data: bytes) -> float:
    if len(data) < 2:
        return 0.0
    n = len(data) // 2
    shorts = struct.unpack(f"<{n}h", data[:n * 2])
    s = sum(x * x for x in shorts)
    return min(math.sqrt(s / n) / 32768.0 * 4.0, 1.0)

def save_wav(pcm_data: bytes, path: Path):
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(SEND_RATE)
        wf.writeframes(pcm_data)

# ── Config ────────────────────────────────────────────────────────────────────
def load_config():
    defaults = {"url": "http://127.0.0.1:1234/v1", "language": "Spanish", 
                "mic": "cable output", "output": "cable input", "vad_thresh": 0.03,
                "enable_subtitles": False, "enable_tts": True, "sub_color": "Yellow", "sub_font": 36, "sub_y": 85}
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                d = json.load(f)
                defaults.update(d)
    except Exception:
        pass
    return defaults

def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

# ═════════════════════════════════════════════════════════════════════════════
#  Transparent Overlay Window
# ═════════════════════════════════════════════════════════════════════════════
class SubtitleOverlay(tk.Toplevel):
    def __init__(self, parent, font_size_ref, y_offset_ref, color_ref):
        super().__init__(parent)
        self.font_size_ref = font_size_ref
        self.y_offset_ref = y_offset_ref
        self.color_ref = color_ref
        
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
        outline_width = 2
        
        # Draw outline
        for dx in range(-outline_width, outline_width + 1, 2):
            for dy in range(-outline_width, outline_width + 1, 2):
                if dx == 0 and dy == 0: continue
                self.canvas.create_text(x + dx, y + dy, text=text, font=font, fill='black', justify='center')
                
        # Draw text
        self.canvas.create_text(x, y, text=text, font=font, fill=color, justify='center')

# ═════════════════════════════════════════════════════════════════════════════
#  Translation Engine
# ═════════════════════════════════════════════════════════════════════════════
class LocalTranslationEngine:
    def __init__(self, url, target_lang, mic_kw, out_kw, thresh,
                 transcript_q, level_q, status_cb, enable_tts_ref):
        self.url = url
        self.target_lang = target_lang
        self.mic_kw = mic_kw
        self.out_kw = out_kw
        self.thresh = thresh
        self.transcript_q = transcript_q
        self.level_q = level_q
        self.status_cb = status_cb
        self.enable_tts_ref = enable_tts_ref
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
        
        self.status_cb("connecting", "Loading Whisper...")
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("base.en", device="cpu", compute_type="int8")
        except ImportError:
            self.status_cb("error", "faster-whisper is not installed. Run: pip install faster-whisper")
            return
        except Exception as e:
            self.status_cb("error", f"Failed to load Whisper: {e}")
            return

        self.status_cb("connected", "Listening...")
        client = AsyncOpenAI(base_url=self.url, api_key="lm-studio")
        
        pya = pyaudio.PyAudio()
        idx, _ = find_input_device(pya, self.mic_kw)
        if idx is None:
            idx = int(pya.get_default_input_device_info()["index"])
            
        stream = pya.open(format=FORMAT, channels=CHANNELS, rate=SEND_RATE,
                          input=True, input_device_index=idx, frames_per_buffer=CHUNK)

        out_name = find_pygame_output(self.out_kw)

        try:
            is_recording = False
            silence_frames = 0
            audio_buffer = []
            
            while not self._stop.is_set():
                data = stream.read(CHUNK, exception_on_overflow=False)
                vol = rms(data)
                
                try:
                    self.level_q.put_nowait(vol)
                except queue.Full:
                    pass

                if vol > self.thresh:
                    if not is_recording:
                        is_recording = True
                        audio_buffer = []
                        self.status_cb("connected", "Recording...")
                    silence_frames = 0
                else:
                    if is_recording:
                        silence_frames += 1

                if is_recording:
                    audio_buffer.append(data)
                    
                    # Stop recording if there's silence OR if we've recorded for 5 seconds continuously
                    if silence_frames > 15 or len(audio_buffer) > 50:
                        is_recording = False
                        if len(audio_buffer) > 15:
                            self.status_cb("connected", "Transcribing...")
                            pcm = b"".join(audio_buffer)
                            save_wav(pcm, TEMP_WAV)
                            
                            segments, _ = await asyncio.to_thread(model.transcribe, str(TEMP_WAV))
                            transcribed_text = " ".join([segment.text for segment in segments]).strip()
                            
                            if transcribed_text:
                                self.transcript_q.put(("source", "English", transcribed_text))
                                self.status_cb("connected", "Translating...")
                                await self._process_text(client, transcribed_text, out_name)
                                
                        self.status_cb("connected", "Listening...")
                        audio_buffer = []

                await asyncio.sleep(0.01)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.status_cb("error", str(e))
        finally:
            stream.stop_stream(); stream.close(); pya.terminate()
            self.status_cb("stopped", "")

    async def _process_text(self, client, text, out_name):
        try:
            messages = [
                {"role": "system", "content": f"You are a translator. Translate the following text strictly into {self.target_lang}. Output ONLY the translated text, nothing else."},
                {"role": "user", "content": text}
            ]

            resp = await client.chat.completions.create(
                model="local-model",
                messages=messages,
                temperature=0.1
            )
            
            try:
                translated_text = resp.choices[0].message.content
                if not translated_text:
                    raise ValueError("Model returned empty text.")
            except Exception as e:
                raise Exception(f"LM Studio gave an invalid response: {repr(resp)}")
                
            translated_text = translated_text.strip()
            self.transcript_q.put(("translation", LANGUAGES[self.target_lang], translated_text))
            
            if self.enable_tts_ref[0]:
                import uuid
                unique_mp3 = Path(__file__).parent / f"temp_tts_{uuid.uuid4().hex}.mp3"
                
                # Generate TTS
                voice = EDGE_VOICES.get(LANGUAGES[self.target_lang], "en-US-ChristopherNeural")
                comm = edge_tts.Communicate(translated_text, voice)
                await comm.save(str(unique_mp3))
                
                # Play
                if out_name:
                    pygame.mixer.init(devicename=out_name)
                else:
                    pygame.mixer.init()
                    
                pygame.mixer.music.load(str(unique_mp3))
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                    
                try:
                    pygame.mixer.music.unload()
                except AttributeError:
                    pass
                pygame.mixer.quit()
                
                try:
                    os.remove(unique_mp3)
                except Exception:
                    pass
            
        except Exception as e:
            self.transcript_q.put(("source", "error", f"API Error: {str(e)}"))

# ═════════════════════════════════════════════════════════════════════════════
#  Settings Dialog
# ═════════════════════════════════════════════════════════════════════════════
class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, cfg, on_save):
        super().__init__(parent)
        self.cfg = cfg
        self.on_save = on_save
        self.title("Local Settings")
        self.geometry("400x420")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.transient(parent)
        self.grab_set()

        pad = {"padx": 20, "pady": (10, 0)}

        ctk.CTkLabel(self, text="LM Studio URL", font=(FONT, 13, "bold"), text_color=TEXT).pack(anchor="w", **pad)
        self.url_var = ctk.StringVar(value=cfg.get("url", ""))
        ctk.CTkEntry(self, textvariable=self.url_var, width=360, fg_color=BG_INPUT, border_color=BORDER, text_color=TEXT).pack(padx=20, pady=(4, 0))

        ctk.CTkLabel(self, text="Microphone (search keyword)", font=(FONT, 13, "bold"), text_color=TEXT).pack(anchor="w", **pad)
        self.mic_var = ctk.StringVar(value=cfg.get("mic", "usb pnp audio"))
        ctk.CTkEntry(self, textvariable=self.mic_var, width=360, fg_color=BG_INPUT, border_color=BORDER, text_color=TEXT).pack(padx=20, pady=(4, 0))

        ctk.CTkLabel(self, text="Output Device (search keyword)", font=(FONT, 13, "bold"), text_color=TEXT).pack(anchor="w", **pad)
        self.out_var = ctk.StringVar(value=cfg.get("output", "cable input"))
        ctk.CTkEntry(self, textvariable=self.out_var, width=360, fg_color=BG_INPUT, border_color=BORDER, text_color=TEXT).pack(padx=20, pady=(4, 0))

        ctk.CTkLabel(self, text="Mic Sensitivity (VAD Threshold)", font=(FONT, 13, "bold"), text_color=TEXT).pack(anchor="w", **pad)
        self.thresh_var = ctk.DoubleVar(value=cfg.get("vad_thresh", 0.03))
        ctk.CTkSlider(self, variable=self.thresh_var, from_=0.005, to=0.2, width=360, progress_color=ACCENT, button_color=ACCENT).pack(padx=20, pady=(4, 0))

        ctk.CTkButton(self, text="Save", font=(FONT, 14, "bold"), width=360, height=42, corner_radius=10, fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#0d1117", command=self._save).pack(padx=20, pady=(24, 20))

    def _save(self):
        self.cfg["url"] = self.url_var.get().strip()
        self.cfg["mic"] = self.mic_var.get().strip()
        self.cfg["output"] = self.out_var.get().strip()
        self.cfg["vad_thresh"] = self.thresh_var.get()
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

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True, padx=8, pady=8)

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
        self.geometry("440x840")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.cfg = load_config()
        self.engine: Optional[LocalTranslationEngine] = None
        self.overlay: Optional[SubtitleOverlay] = None
        self.is_running = False
        self.transcript_q = queue.Queue()
        self.level_q = queue.Queue(maxsize=5)
        self._level_smooth = 0.0
        self._settings_win = None
        
        self.sub_font_ref = [self.cfg.get("sub_font", 36)]
        self.sub_y_ref = [self.cfg.get("sub_y", 85)]
        self.sub_color_ref = [self.cfg.get("sub_color", "Yellow")]
        self.enable_tts_ref = [self.cfg.get("enable_tts", True)]
        
        self.current_subtitle = ""
        self.last_text_time = 0

        self._build_ui()
        self._poll()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.pack(fill="x", padx=24, pady=(20, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="OFFLINE", font=(FONT, 22, "bold"), text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(header, text=" TRANSLATOR", font=(FONT, 22), text_color=TEXT).pack(side="left")

        ctk.CTkButton(header, text="\u2699", width=36, height=36, corner_radius=18, font=(FONT, 18), fg_color=BG_CARD, hover_color=BG_INPUT, text_color=TEXT_MUT, border_width=1, border_color=BORDER, command=self._open_settings).pack(side="right")
        ctk.CTkLabel(self, text="100% Local Pipeline: STT -> LM Studio -> TTS", font=(FONT, 12), text_color=TEXT_DIM).pack(anchor="w", padx=26, pady=(0, 16))
        ctk.CTkFrame(self, fg_color=BORDER, height=1).pack(fill="x", padx=24)

        lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        lang_frame.pack(fill="x", padx=24, pady=(20, 0))
        ctk.CTkLabel(lang_frame, text="TRANSLATE TO", font=(FONT, 11, "bold"), text_color=TEXT_DIM).pack(anchor="w")
        self.lang_var = ctk.StringVar(value=self.cfg.get("language", "Spanish"))
        self.lang_menu = ctk.CTkOptionMenu(lang_frame, variable=self.lang_var, values=LANG_NAMES, width=392, height=42, corner_radius=10, font=(FONT, 14), fg_color=BG_CARD, button_color=BG_INPUT, button_hover_color=BORDER, dropdown_fg_color=BG_CARD, dropdown_hover_color=BG_INPUT, text_color=TEXT)
        self.lang_menu.pack(pady=(6, 0))

        # Subtitles Integration
        sub_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10)
        sub_frame.pack(fill="x", padx=24, pady=(16, 0))
        
        self.sub_enable_var = ctk.BooleanVar(value=self.cfg.get("enable_subtitles", False))
        ctk.CTkSwitch(sub_frame, text="Enable Subtitle Overlay", variable=self.sub_enable_var, font=(FONT, 13, "bold"), text_color=TEXT, progress_color=ACCENT, command=self._on_sub_toggle).pack(anchor="w", padx=16, pady=16)

        self.tts_enable_var = ctk.BooleanVar(value=self.cfg.get("enable_tts", True))
        ctk.CTkSwitch(sub_frame, text="Play Audio (TTS)", variable=self.tts_enable_var, font=(FONT, 13, "bold"), text_color=TEXT, progress_color=ACCENT, command=self._on_tts_toggle).pack(anchor="w", padx=16, pady=(0, 16))

        self.sub_controls = ctk.CTkFrame(sub_frame, fg_color="transparent")
        if self.sub_enable_var.get():
            self.sub_controls.pack(fill="x", padx=16, pady=(0, 16))
            
        color_btn = ctk.CTkButton(self.sub_controls, text=self.sub_color_ref[0], width=100, height=32, corner_radius=8, fg_color=BG_INPUT, text_color=TEXT, command=self._open_color_picker)
        color_btn.pack(side="left", padx=(0, 16))
        self.color_btn = color_btn
        
        y_slider = ctk.CTkSlider(self.sub_controls, from_=0, to=100, width=120, command=self._on_y_change)
        y_slider.set(self.sub_y_ref[0])
        y_slider.pack(side="left", padx=(0, 16))
        
        font_slider = ctk.CTkSlider(self.sub_controls, from_=16, to=72, width=100, command=self._on_font_change)
        font_slider.set(self.sub_font_ref[0])
        font_slider.pack(side="left")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=100)
        btn_frame.pack(fill="x", padx=24, pady=(20, 0))
        btn_frame.pack_propagate(False)

        self.start_btn = ctk.CTkButton(btn_frame, text="\U0001F3A4  START", width=200, height=64, corner_radius=32, font=(FONT, 18, "bold"), fg_color=SUCCESS_DIM, hover_color=SUCCESS, text_color="#ffffff", command=self._toggle)
        self.start_btn.place(relx=0.5, rely=0.5, anchor="center")

        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(pady=(0, 0))
        self.status_dot = ctk.CTkLabel(self.status_frame, text="\u25CF", font=(FONT, 10), text_color=TEXT_DIM)
        self.status_dot.pack(side="left", padx=(0, 6))
        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready", font=(FONT, 12), text_color=TEXT_MUT)
        self.status_label.pack(side="left")

        meter_frame = ctk.CTkFrame(self, fg_color="transparent")
        meter_frame.pack(fill="x", padx=24, pady=(12, 0))
        self.level_bar = ctk.CTkProgressBar(meter_frame, width=392, height=8, corner_radius=4, fg_color=BG_INPUT, progress_color=ACCENT)
        self.level_bar.pack()
        self.level_bar.set(0)

        tr_header = ctk.CTkFrame(self, fg_color="transparent")
        tr_header.pack(fill="x", padx=24, pady=(12, 0))
        ctk.CTkLabel(tr_header, text="LIVE TRANSCRIPT", font=(FONT, 11, "bold"), text_color=TEXT_DIM).pack(side="left")
        ctk.CTkButton(tr_header, text="Clear", width=50, height=24, corner_radius=6, font=(FONT, 11), fg_color=BG_INPUT, hover_color=BORDER, text_color=TEXT_MUT, command=self._clear_transcript).pack(side="right")

        self.transcript = ctk.CTkTextbox(self, width=392, height=140, corner_radius=10, fg_color=BG_CARD, text_color=TEXT, font=(FONT, 13), border_width=1, border_color=BORDER, state="disabled", wrap="word")
        self.transcript.pack(padx=24, pady=(6, 0))
        self.transcript._textbox.tag_configure("source_tag", foreground=TEXT_MUT, font=(FONT, 11, "italic"))
        self.transcript._textbox.tag_configure("source_text", foreground=TEXT_MUT, font=(FONT, 13, "italic"))
        self.transcript._textbox.tag_configure("trans_tag", foreground=ACCENT, font=(FONT, 11, "bold"))
        self.transcript._textbox.tag_configure("trans_text", foreground=TEXT, font=(FONT, 13))

    def _on_sub_toggle(self):
        self.cfg["enable_subtitles"] = self.sub_enable_var.get()
        save_config(self.cfg)
        if self.sub_enable_var.get():
            self.sub_controls.pack(fill="x", padx=16, pady=(0, 16))
            if self.is_running and not self.overlay:
                self.overlay = SubtitleOverlay(self, self.sub_font_ref, self.sub_y_ref, self.sub_color_ref)
        else:
            self.sub_controls.pack_forget()
            if self.overlay:
                self.overlay.destroy()
                self.overlay = None

    def _on_tts_toggle(self):
        self.enable_tts_ref[0] = self.tts_enable_var.get()
        self.cfg["enable_tts"] = self.tts_enable_var.get()
        save_config(self.cfg)

    def _open_color_picker(self):
        SelectionDialog(self, "Select Color", COLORS, self.sub_color_ref[0], self._on_color_selected)

    def _on_color_selected(self, val):
        self.sub_color_ref[0] = val
        self.color_btn.configure(text=val)
        self.cfg["sub_color"] = val
        save_config(self.cfg)
        if self.overlay: self.overlay.set_text(self.current_subtitle)

    def _on_y_change(self, val):
        self.sub_y_ref[0] = int(val)
        self.cfg["sub_y"] = int(val)
        save_config(self.cfg)
        if self.overlay: self.overlay.set_text(self.current_subtitle)

    def _on_font_change(self, val):
        self.sub_font_ref[0] = int(val)
        self.cfg["sub_font"] = int(val)
        save_config(self.cfg)
        if self.overlay: self.overlay.set_text(self.current_subtitle)

    def _toggle(self):
        if self.is_running:
            self._stop()
        else:
            self._start()

    def _start(self):
        lang_name = self.lang_var.get()
        self.cfg["language"] = lang_name
        save_config(self.cfg)

        base_url = self.cfg.get("url", "http://127.0.0.1:1234/v1")
        if not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        self.engine = LocalTranslationEngine(
            url=base_url,
            target_lang=lang_name,
            mic_kw=self.cfg.get("mic", "cable output"),
            out_kw=self.cfg.get("output", "cable input"),
            thresh=self.cfg.get("vad_thresh", 0.03),
            transcript_q=self.transcript_q,
            level_q=self.level_q,
            status_cb=self._on_status,
            enable_tts_ref=self.enable_tts_ref
        )
        self.engine.start()
        
        if self.sub_enable_var.get() and not self.overlay:
            self.overlay = SubtitleOverlay(self, self.sub_font_ref, self.sub_y_ref, self.sub_color_ref)
            
        self.is_running = True
        self.start_btn.configure(text="\u23F9  STOP", fg_color=ERROR, hover_color="#da3633")
        self.lang_menu.configure(state="disabled")

    def _stop(self):
        if self.engine:
            self.engine.stop()
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
            
        self.is_running = False
        self.start_btn.configure(text="\U0001F3A4  START", fg_color=SUCCESS_DIM, hover_color=SUCCESS)
        self.lang_menu.configure(state="normal")
        self.level_bar.set(0)
        self._level_smooth = 0.0

    def _on_status(self, status, detail):
        self.after(0, self._update_status, status, detail)

    def _update_status(self, status, detail):
        colors = {"connecting": (WARNING, detail), "connected": (SUCCESS, detail), "stopped": (TEXT_DIM, "Ready"), "error": (ERROR, f"Error: {detail}")}
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
                    self.transcript.insert("end", f"  [{lang}] ", "source_tag")
                    self.transcript.insert("end", f"{text}\n", "source_text")
                else:
                    self.transcript.insert("end", f"  [{lang}] ", "trans_tag")
                    self.transcript.insert("end", f"{text}\n", "trans_text")
                    self.current_subtitle = text
                    self.last_text_time = time.time()
                    if self.overlay: self.overlay.set_text(self.current_subtitle)
                self.transcript.configure(state="disabled")
                self.transcript.see("end")
        except queue.Empty:
            pass
            
        if self.current_subtitle and time.time() - self.last_text_time > 4.0:
            self.current_subtitle = ""
            if self.overlay: self.overlay.set_text("")

        try:
            while True:
                lvl = self.level_q.get_nowait()
                self._level_smooth = self._level_smooth * 0.5 + lvl * 0.5
        except queue.Empty:
            pass

        if self.is_running:
            self.level_bar.set(self._level_smooth)
            self._level_smooth *= 0.85
        else:
            self.level_bar.set(max(self._level_smooth * 0.3, 0))

        self.after(50, self._poll)

    def _on_close(self):
        if self.is_running:
            self._stop()
        self.after(200, self.destroy)

if __name__ == "__main__":
    app = App()
    app.mainloop()
