"""yt-mp3-mp4 — YouTube'dan MP3 / MP4 indirici (customtkinter + yt-dlp)."""
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
import yt_dlp

SETTINGS = Path.home() / ".yt-mp3-mp4.json"
QUALITIES = {"MP3": ["320 kbps", "192 kbps", "128 kbps"], "MP4": ["Max", "1080p", "720p", "480p"]}
LINK_RE = re.compile(r"^(https?://|www\.|(m\.|music\.)?youtube\.com/|youtu\.be/)", re.I)

TEXT = {
    "tr": {
        "title": "YouTube İndirici",
        "subtitle": "Link yapıştır ya da şarkı adı yaz — her satır ayrı bir indirme.",
        "input": "Linkler veya aramalar",
        "download": "İndir",
        "queue": "İndirmeler",
        "empty": "Henüz indirme yok. Yukarıya bir link ya da şarkı adı yaz.",
        "open": "Klasörü aç",
        "clear": "Temizle",
        "pick": "İndirme klasörünü seç",
        "waiting": "Sırada",
        "downloading": "{p}%  ·  {s}",
        "processing": "Dönüştürülüyor…",
        "done": "Tamamlandı",
        "error": "Hata: {e}",
        "notfound": "Bulunamadı",
    },
    "en": {
        "title": "YouTube Downloader",
        "subtitle": "Paste a link or type a song name — one download per line.",
        "input": "Links or searches",
        "download": "Download",
        "queue": "Downloads",
        "empty": "No downloads yet. Type a link or song name above.",
        "open": "Open folder",
        "clear": "Clear",
        "pick": "Choose download folder",
        "waiting": "Queued",
        "downloading": "{p}%  ·  {s}",
        "processing": "Converting…",
        "done": "Done",
        "error": "Error: {e}",
        "notfound": "Not found",
    },
}

# (açık, koyu) renk çiftleri
BG = ("#F3F4F7", "#0D0F13")
CARD = ("#FFFFFF", "#15181E")
FIELD = ("#F5F6F8", "#1C2028")
BORDER = ("#E2E5EB", "#262B35")
FG = ("#111318", "#ECEEF2")
MUTED = ("#6B7280", "#8A92A0")
ACCENT, ACCENT_HOVER = "#FF3D52", "#E52E43"
OK, BAD = "#22C55E", "#EF4444"
FONT = "Segoe UI" if sys.platform == "win32" else None


def to_target(line):
    """Linkse olduğu gibi, değilse YouTube'da ilk sonucu arayan hedefe çevir."""
    line = line.strip()
    if not LINK_RE.match(line):
        return f"ytsearch1:{line}"
    return line if line.lower().startswith("http") else "https://" + line


def clean_settings(saved):
    """Ayar dosyasından yalnız geçerli değerleri al; bozuk dosya uygulamayı açılmaz yapmasın."""
    if not isinstance(saved, dict):
        return {}
    valid = {
        "lang": lambda v: v in TEXT,
        "theme": lambda v: v in ("dark", "light"),
        "format": lambda v: v in QUALITIES,
        "quality": lambda v: isinstance(v, str),
        "folder": lambda v: isinstance(v, str) and v,
    }
    return {k: v for k, v in saved.items() if k in valid and valid[k](v)}


def ffmpeg_path():
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


def build_opts(fmt, quality, folder, hook):
    opts = {
        # ara dosyalar (parçalar, kapak) geçici klasörde kalır; klasöre yalnız bitmiş dosya taşınır
        "paths": {"home": folder, "temp": os.path.join(tempfile.gettempdir(), "yt-mp3-mp4")},
        "outtmpl": "%(title)s.%(ext)s",
        "ffmpeg_location": ffmpeg_path(),
        # YouTube imza çözümü için JS çalışma ortamı gerekir; hangisi kuruluysa o kullanılır
        "js_runtimes": {"deno": {}, "node": {}, "bun": {}},
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "progress_hooks": [hook],
        "postprocessor_hooks": [hook],
    }
    if fmt == "MP3":
        opts |= {
            "format": "ba/b",
            "writethumbnail": True,
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": quality.split()[0]},
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
        }
    else:
        res = "res" if quality == "Max" else f"res:{quality[:-1]}"
        opts |= {"format": "bv*+ba/b", "format_sort": [res, "ext:mp4:m4a"], "merge_output_format": "mp4"}
    return opts


def human_speed(bps):
    if not bps:
        return "…"
    for unit in ("B/s", "KB/s", "MB/s"):
        if bps < 1024:
            return f"{bps:.1f} {unit}" if unit == "MB/s" else f"{bps:.0f} {unit}"
        bps /= 1024
    return f"{bps:.1f} GB/s"


class Row(ctk.CTkFrame):
    def __init__(self, master, app, query, fmt):
        super().__init__(master, fg_color=FIELD, corner_radius=12)
        self.app = app
        self.status = ("waiting", {})
        self.grid_columnconfigure(1, weight=1)
        badge = ctk.CTkLabel(self, text="♪" if fmt == "MP3" else "▶", width=34, height=34, corner_radius=10,
                             fg_color=ACCENT, text_color="white", font=ctk.CTkFont(FONT, 15, "bold"))
        badge.grid(row=0, column=0, rowspan=2, padx=(12, 10), pady=12)
        self.title = ctk.CTkLabel(self, text=query, anchor="w", text_color=FG, font=ctk.CTkFont(FONT, 13, "bold"))
        self.title.grid(row=0, column=1, sticky="ew", pady=(10, 0))
        self.info = ctk.CTkLabel(self, text="", anchor="e", text_color=MUTED, font=ctk.CTkFont(FONT, 12))
        self.info.grid(row=0, column=2, padx=(8, 14), pady=(10, 0))
        self.bar = ctk.CTkProgressBar(self, height=5, corner_radius=3, progress_color=ACCENT, fg_color=BORDER)
        self.bar.set(0)
        self.bar.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 14), pady=(4, 12))
        self.render()

    def set_title(self, title):
        self.title.configure(text=title if len(title) <= 70 else title[:67] + "…")

    def update_status(self, key, **kw):
        self.status = (key, kw)
        if key == "downloading":
            self.bar.set(kw["p"] / 100)
        elif key in ("processing", "done", "error", "notfound"):
            self.bar.set(1)
        self.bar.configure(progress_color={"done": OK, "error": BAD, "notfound": BAD}.get(key, ACCENT))
        self.render()

    def render(self):
        key, kw = self.status
        self.info.configure(text=self.app.t(key).format(**kw),
                            text_color={"done": OK, "error": BAD, "notfound": BAD}.get(key, MUTED))


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = {"lang": "tr", "theme": "dark", "format": "MP3", "quality": "320 kbps",
                    "folder": str(Path.home() / "Downloads")}
        try:
            saved = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            saved = {}
        self.cfg |= clean_settings(saved)
        ctk.set_appearance_mode(self.cfg["theme"])
        self.rows = []
        self.labels = []  # (widget, metin anahtarı) — dil değişince yeniden yazılır
        self.jobs, self.events = queue.Queue(), queue.Queue()
        threading.Thread(target=self.worker, daemon=True).start()

        self.title("yt-mp3-mp4")
        self.geometry("820x720")
        self.minsize(640, 560)
        self.configure(fg_color=BG)
        self.build()
        self.bind("<Control-Return>", lambda e: self.start())
        self.after(100, self.poll)

    # ---------- arayüz ----------
    def t(self, key):
        return TEXT[self.cfg["lang"]][key]

    def label(self, master, key, size=13, weight="normal", color=FG):
        w = ctk.CTkLabel(master, text=self.t(key), text_color=color, anchor="w",
                         font=ctk.CTkFont(FONT, size, weight))
        self.labels.append((w, key))
        return w

    def card(self):
        return ctk.CTkFrame(self, fg_color=CARD, corner_radius=18, border_width=1, border_color=BORDER)

    def build(self):
        pad = {"padx": 28}
        # başlık
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", pady=(24, 18), **pad)
        ctk.CTkLabel(head, text="▶", width=46, height=46, corner_radius=14, fg_color=ACCENT,
                     text_color="white", font=ctk.CTkFont(FONT, 20, "bold")).pack(side="left")
        titles = ctk.CTkFrame(head, fg_color="transparent")
        titles.pack(side="left", padx=14)
        self.label(titles, "title", 22, "bold").pack(anchor="w")
        self.label(titles, "subtitle", 12, color=MUTED).pack(anchor="w")
        self.theme_btn = ctk.CTkButton(head, text="", width=38, height=32, corner_radius=10, fg_color=FIELD,
                                       hover_color=BORDER, text_color=FG, font=ctk.CTkFont(FONT, 15),
                                       command=self.toggle_theme)
        self.theme_btn.pack(side="right")
        lang = ctk.CTkSegmentedButton(head, values=["TR", "EN"], command=self.set_lang, height=32,
                                      selected_color=ACCENT, selected_hover_color=ACCENT_HOVER,
                                      unselected_color=FIELD, unselected_hover_color=BORDER, fg_color=FIELD,
                                      text_color=FG, font=ctk.CTkFont(FONT, 12, "bold"))
        lang.set(self.cfg["lang"].upper())
        lang.pack(side="right", padx=8)
        self.update_theme_icon()

        # giriş kartı
        top = self.card()
        top.pack(fill="x", **pad)
        self.label(top, "input", 12, "bold", MUTED).pack(fill="x", padx=20, pady=(16, 6))
        self.box = ctk.CTkTextbox(top, height=120, corner_radius=12, fg_color=FIELD, border_width=1,
                                  border_color=BORDER, text_color=FG, font=ctk.CTkFont(FONT, 13), wrap="none")
        self.box.pack(fill="x", padx=20)
        self.box.focus_set()

        bar = ctk.CTkFrame(top, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=16)
        seg = {"selected_color": ACCENT, "selected_hover_color": ACCENT_HOVER, "unselected_color": FIELD,
               "unselected_hover_color": BORDER, "fg_color": FIELD, "text_color": FG, "height": 38,
               "font": ctk.CTkFont(FONT, 13, "bold")}
        self.fmt = ctk.CTkSegmentedButton(bar, values=["MP3", "MP4"], command=self.set_format, width=130, **seg)
        self.fmt.set(self.cfg["format"])
        self.fmt.pack(side="left")
        self.quality = ctk.CTkOptionMenu(bar, values=QUALITIES[self.cfg["format"]], width=118, height=38,
                                         corner_radius=10, fg_color=FIELD, button_color=FIELD,
                                         button_hover_color=BORDER, text_color=FG, dropdown_fg_color=CARD,
                                         dropdown_text_color=FG, dropdown_hover_color=FIELD,
                                         font=ctk.CTkFont(FONT, 13), command=lambda v: self.save(quality=v))
        self.quality.set(self.cfg["quality"] if self.cfg["quality"] in QUALITIES[self.cfg["format"]]
                         else QUALITIES[self.cfg["format"]][0])
        self.quality.pack(side="left", padx=10)
        self.folder_btn = ctk.CTkButton(bar, text="", height=38, corner_radius=10, fg_color=FIELD,
                                        hover_color=BORDER, text_color=FG, anchor="w",
                                        font=ctk.CTkFont(FONT, 13), command=self.pick_folder)
        self.folder_btn.pack(side="left", fill="x", expand=True)
        self.update_folder()
        self.go = ctk.CTkButton(bar, text=self.t("download") + "  ↓", height=38, width=130, corner_radius=10,
                                fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="white",
                                font=ctk.CTkFont(FONT, 14, "bold"), command=self.start)
        self.go.pack(side="right", padx=(10, 0))

        # kuyruk kartı
        bottom = self.card()
        bottom.pack(fill="both", expand=True, pady=(16, 24), **pad)
        qhead = ctk.CTkFrame(bottom, fg_color="transparent")
        qhead.pack(fill="x", padx=20, pady=(16, 8))
        self.label(qhead, "queue", 15, "bold").pack(side="left")
        small = {"height": 30, "corner_radius": 8, "fg_color": FIELD, "hover_color": BORDER, "text_color": FG,
                 "font": ctk.CTkFont(FONT, 12)}
        self.clear_btn = ctk.CTkButton(qhead, text=self.t("clear"), width=80, command=self.clear, **small)
        self.clear_btn.pack(side="right")
        self.open_btn = ctk.CTkButton(qhead, text=self.t("open"), width=100, command=self.open_folder, **small)
        self.open_btn.pack(side="right", padx=8)
        self.list = ctk.CTkScrollableFrame(bottom, fg_color="transparent", scrollbar_button_color=BORDER)
        self.list.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.empty = self.label(self.list, "empty", 13, color=MUTED)
        self.empty.configure(anchor="center")
        self.empty.pack(fill="x", pady=40)

    def update_folder(self):
        path = self.cfg["folder"]
        shown = path if len(path) <= 42 else "…" + path[-41:]
        self.folder_btn.configure(text=f"📁  {shown}")

    def update_theme_icon(self):
        self.theme_btn.configure(text="☀" if self.cfg["theme"] == "dark" else "☾")

    # ---------- eylemler ----------
    def save(self, **kw):
        self.cfg |= kw
        try:
            SETTINGS.write_text(json.dumps(self.cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def set_lang(self, value):
        self.save(lang=value.lower())
        for w, key in self.labels:
            w.configure(text=self.t(key))
        self.go.configure(text=self.t("download") + "  ↓")
        self.open_btn.configure(text=self.t("open"))
        self.clear_btn.configure(text=self.t("clear"))
        for row in self.rows:
            row.render()

    def toggle_theme(self):
        self.save(theme="light" if self.cfg["theme"] == "dark" else "dark")
        ctk.set_appearance_mode(self.cfg["theme"])
        self.update_theme_icon()

    def set_format(self, fmt):
        self.quality.configure(values=QUALITIES[fmt])
        self.quality.set(QUALITIES[fmt][0])
        self.save(format=fmt, quality=QUALITIES[fmt][0])

    def pick_folder(self):
        path = filedialog.askdirectory(initialdir=self.cfg["folder"], title=self.t("pick"))
        if path:
            self.save(folder=os.path.normpath(path))
            self.update_folder()

    def open_folder(self):
        path = self.cfg["folder"]
        os.makedirs(path, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(path)
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])

    def clear(self):
        for row in [r for r in self.rows if r.status[0] in ("done", "error", "notfound")]:
            row.destroy()
            self.rows.remove(row)
        if not self.rows:
            self.empty.pack(fill="x", pady=40)

    def start(self):
        lines = [ln.strip() for ln in self.box.get("1.0", "end").splitlines() if ln.strip()]
        if not lines:
            self.box.configure(border_color=ACCENT)
            self.after(900, lambda: self.box.configure(border_color=BORDER))
            return "break"
        self.empty.pack_forget()
        fmt, quality, folder = self.fmt.get(), self.quality.get(), self.cfg["folder"]
        for line in lines:
            row = Row(self.list, self, line, fmt)
            row.pack(fill="x", padx=8, pady=5)
            self.rows.append(row)
            self.jobs.put((row, to_target(line), fmt, quality, folder))
        self.box.delete("1.0", "end")
        return "break"

    # ---------- arka plan ----------
    def worker(self):
        # ponytail: tek işçi, sırayla indirir; paralel indirme gerekirse birden çok thread başlat
        while True:
            row, target, fmt, quality, folder = self.jobs.get()

            seen = {"title": None, "any": False}

            def hook(d, row=row, seen=seen):
                seen["any"] = True
                title = (d.get("info_dict") or {}).get("title")
                if title and title != seen["title"]:
                    seen["title"] = title
                    self.events.put((row, "title", {"title": title}))
                if "postprocessor" in d:  # dönüştürme / birleştirme adımı
                    if d["status"] == "started":
                        self.events.put((row, "processing", {}))
                elif d["status"] == "downloading":
                    # ponytail: MP4'te video ve ses ayrı iner, çubuk ses için 0'dan tekrar başlar
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                    p = int(d.get("downloaded_bytes", 0) * 100 / total) if total else 0
                    self.events.put((row, "downloading", {"p": min(p, 100), "s": human_speed(d.get("speed"))}))

            try:
                os.makedirs(folder, exist_ok=True)
                with yt_dlp.YoutubeDL(build_opts(fmt, quality, folder, hook)) as ydl:
                    ydl.download([target])
                self.events.put((row, "done" if seen["any"] else "notfound", {}))
            except Exception as e:  # yt-dlp hatası satırda gösterilir, uygulama çökmez
                msg = re.sub(r"^ERROR:\s*(\[\w+\]\s*)?(Got error:\s*)?", "", str(e)).split("\n")[0]
                self.events.put((row, "error", {"e": msg[:80]}))

    def poll(self):
        while not self.events.empty():
            row, kind, kw = self.events.get()
            if not row.winfo_exists():
                continue
            if kind == "title":
                row.set_title(kw["title"])
            else:
                row.update_status(kind, **kw)
        self.after(100, self.poll)


if __name__ == "__main__":
    App().mainloop()
