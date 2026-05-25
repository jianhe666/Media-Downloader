import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import threading
import traceback
import re
import json
import sys
import subprocess
import requests
import yt_dlp
import os
import shutil
import zipfile
import tempfile
import time
import glob

try:
    from playwright.sync_api import sync_playwright
    _HAS_PLAYWRIGHT = True
except ImportError:
    _HAS_PLAYWRIGHT = False

class MediaDownloader:
    DISCLAIMER = (
        "免责声明\n\n"
        "本工具仅供学习交流使用，严禁用于任何商业或非法用途。\n\n"
        "使用本工具下载的任何音视频内容，其版权归相关权利人所有。\n"
        "请勿将下载内容用于商业用途或未经授权的传播。\n"
        "使用者应确保自身行为符合相关平台的服务条款及当地法律法规。\n\n"
        "本工具不存储任何用户数据，开发者不对使用者的下载行为\n"
        "承担任何直接或间接责任。\n\n"
        "点击「同意」即表示您已阅读并理解以上条款，\n"
        "并愿意自行承担使用本工具的一切责任和后果。"
    )

    def __init__(self, root):
        self.root = root

        if not self._check_disclaimer():
            root.destroy()
            return

        self.root.title("Media Downloader V1.0")
        self.root.geometry("760x620")
        self.root.resizable(True, True)
        self.root.minsize(600, 520)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # --- Warm natural palette ---
        BG       = "#FBF7F2"   # warm cream
        CARD     = "#FFFFFF"
        ACCENT   = "#F59E0B"   # warm amber
        A_HOVER  = "#E8900A"
        BLUE_SOFT = "#8BAABB"  # muted lake blue
        BLUE_PALE = "#DCE8EC"  # pale sky
        TEXT     = "#3D3628"   # warm dark brown
        SUBTLE   = "#7A6E5C"
        MUTED    = "#A49882"
        RED      = "#E0554A"
        LOG_BG   = "#1A2744"
        LOG_FG   = "#B4C6E0"
        SEP      = "#EDE8E0"

        root.configure(bg=BG)

        FT  = ("Microsoft YaHei UI", 12)
        FT_S = ("Microsoft YaHei UI", 11)
        FT_XS = ("Microsoft YaHei UI", 10)
        FT_H1 = ("Microsoft YaHei UI", 22, "bold")
        FT_H2 = ("Microsoft YaHei UI", 14, "bold")
        FT_MONO = ("Cascadia Code", 10)

        # --- main (tk, not ctk - avoids unnecessary custom drawing) ---
        main = tk.Frame(root, bg=BG)
        main.pack(fill="both", expand=True)

        # --- header (tk) ---
        hero = tk.Frame(main, bg=BG)
        hero.pack(fill="x", padx=24, pady=(28, 20))
        tk.Label(hero, text="Media Downloader", bg=BG, fg=TEXT,
                 font=FT_H1).pack(anchor="w")
        tk.Label(hero, text="让下载更简单", bg=BG, fg=MUTED,
                 font=FT_XS).pack(anchor="w", pady=(4, 0))

        # --- card 1: link ---
        c1 = tk.Frame(main, bg=CARD, highlightbackground="#E8E3DA",
                      highlightthickness=1)
        c1.pack(fill="x", padx=24)

        tk.Label(c1, text="链接", bg=CARD, fg=TEXT, font=FT_H2).pack(anchor="w", padx=18, pady=(16, 0))
        tk.Frame(c1, bg=SEP, height=1).pack(fill="x", padx=18, pady=(8, 0))

        url_row = tk.Frame(c1, bg=CARD)
        url_row.pack(fill="x", padx=18, pady=(12, 0))
        self.url_var = tk.StringVar()
        self.url_entry = ctk.CTkEntry(url_row, textvariable=self.url_var, font=FT,
                                      fg_color="#F9F7F2", text_color=TEXT,
                                      border_color="#E5E0D8", corner_radius=10, height=38)
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Control-v>", lambda e: self.url_entry.event_generate("<<Paste>>"))
        ctk.CTkButton(url_row, text="粘贴", font=FT_S, fg_color="#F5F0E8",
                      text_color=SUBTLE, hover_color="#EDE6D8", corner_radius=10,
                      height=38, width=56, command=self.paste_url).pack(side="left", padx=(8, 0))

        dir_row = tk.Frame(c1, bg=CARD)
        dir_row.pack(fill="x", padx=18, pady=(8, 16))
        tk.Label(dir_row, text="保存至", bg=CARD, fg=SUBTLE, font=FT_S).pack(side="left", padx=(0, 8))
        self.dir_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.dir_entry = ctk.CTkEntry(dir_row, textvariable=self.dir_var, font=FT_S,
                                      fg_color="#F9F7F2", text_color=TEXT,
                                      border_color="#E5E0D8", corner_radius=10, height=32)
        self.dir_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(dir_row, text="浏览", font=FT_S, fg_color="#F5F0E8",
                      text_color=SUBTLE, hover_color="#EDE6D8", corner_radius=10,
                      height=32, width=56, command=self.browse_dir).pack(side="left", padx=(8, 0))

        # --- card 2: options ---
        c2 = tk.Frame(main, bg=CARD, highlightbackground="#E8E3DA",
                      highlightthickness=1)
        c2.pack(fill="x", padx=24, pady=(14, 0))

        tk.Label(c2, text="选项", bg=CARD, fg=TEXT, font=FT_H2).pack(anchor="w", padx=18, pady=(16, 0))
        tk.Frame(c2, bg=SEP, height=1).pack(fill="x", padx=18, pady=(8, 0))

        opt_top = tk.Frame(c2, bg=CARD)
        opt_top.pack(fill="x", padx=18, pady=(12, 22))
        self.cookie_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(opt_top, text="使用浏览器 Cookie 下载（推荐）",
                        variable=self.cookie_var, font=FT,
                        text_color=TEXT, fg_color=BLUE_SOFT,
                        hover_color="#7B9BAB", checkmark_color="white",
                        corner_radius=4).pack(side="left")
        self.audio_only_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(opt_top, text="仅下载音频", variable=self.audio_only_var,
                        font=FT, text_color=TEXT, fg_color=BLUE_SOFT,
                        hover_color="#7B9BAB", checkmark_color="white",
                        corner_radius=4).pack(side="right")

        self.browser_var = tk.StringVar(value="edge")

        # --- controls (tk) ---
        ctrl = tk.Frame(main, bg=BG)
        ctrl.pack(fill="x", padx=24, pady=(20, 0))

        self.dl_btn = ctk.CTkButton(ctrl, text="开始下载", font=FT_H2,
                                    fg_color=ACCENT, hover_color=A_HOVER,
                                    text_color="white", corner_radius=12,
                                    height=42, width=130, command=self.start_download)
        self.dl_btn.pack(side="left")
        self.cancel_btn = ctk.CTkButton(ctrl, text="取消", font=FT_S,
                                        fg_color="transparent", text_color=RED,
                                        hover_color="#FBEBE9", corner_radius=12,
                                        height=42, width=72,
                                        command=self.cancel_download, state="disabled")
        self.cancel_btn.pack(side="left", padx=(10, 0))

        self.info_var = tk.StringVar()
        tk.Label(ctrl, textvariable=self.info_var, bg=BG, fg=MUTED,
                 font=FT_XS).pack(side="left", padx=(16, 0))

        ctk.CTkButton(ctrl, text="打开目录", font=FT_XS, fg_color="transparent",
                      text_color=MUTED, hover_color="#F5F0E8", corner_radius=8,
                      height=30, command=self.open_dir).pack(side="right")
        ctk.CTkButton(ctrl, text="免责声明", font=FT_XS, fg_color="transparent",
                      text_color=MUTED, hover_color="#F5F0E8", corner_radius=8,
                      height=30, command=self.show_disclaimer).pack(side="right", padx=(0, 4))

        # --- progress (CTkProgressBar) ---
        self.progress_bar = ctk.CTkProgressBar(main, fg_color="#EBE6DD",
                                               progress_color=ACCENT,
                                               corner_radius=3, height=5)
        self.progress_bar.pack(fill="x", padx=24, pady=(16, 0))
        self.progress_bar.set(0)

        # --- log ---
        log_shell = tk.Frame(main, bg=LOG_BG)
        log_shell.pack(fill="both", expand=True, padx=24, pady=(14, 18))
        tk.Label(log_shell, text="  日志", bg=LOG_BG, fg="#6B7DA8",
                 font=FT_XS, anchor="w").pack(fill="x", padx=10, pady=(6, 2))
        tk.Frame(log_shell, bg="#243358", height=1).pack(fill="x", padx=10)
        self.log_text = tk.Text(log_shell, font=FT_MONO, bg=LOG_BG, fg=LOG_FG,
                                insertbackground=LOG_FG, relief="flat", borderwidth=0,
                                padx=10, pady=6, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=(2, 6))

        # --- init ---
        self.is_downloading = False
        self._cancel_flag = False
        self._cookie_tmp_file = None
        self._result_title = ""
        self._result_resolution = ""

    def _get_flag_path(self):
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable), ".disclaimer_accepted")
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), ".disclaimer_accepted")

    def _check_disclaimer(self):
        flag = self._get_flag_path()
        if os.path.exists(flag):
            return True
        # Show dialog directly on main thread — do NOT use threading.Event here
        result = [False]
        dlg = tk.Toplevel(self.root)
        dlg.title("免责声明")
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)
        dlg.configure(bg="#FBF7F2")
        f = tk.Frame(dlg, bg="#FBF7F2", padx=22, pady=22)
        f.pack()
        tk.Label(f, text="免责声明", bg="#FBF7F2", fg="#3D3628",
                 font=("Microsoft YaHei UI", 14, "bold")).pack(anchor="w")
        tk.Label(f, text=self.DISCLAIMER, bg="#FBF7F2", fg="#5C5042",
                 font=("Microsoft YaHei UI", 10), justify="left",
                 wraplength=400).pack(anchor="w", pady=(10, 16))
        btns = tk.Frame(f, bg="#FBF7F2")
        btns.pack()
        ctk.CTkButton(btns, text="同意", font=("Microsoft YaHei UI", 11),
                      fg_color="#F59E0B", hover_color="#E8900A",
                      corner_radius=8, height=34, width=90,
                      command=lambda: [result.__setitem__(0, True), dlg.destroy()]
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="拒绝", font=("Microsoft YaHei UI", 11),
                      fg_color="transparent", text_color="#7A6E5C",
                      hover_color="#F5F0E8", corner_radius=8, height=34,
                      command=dlg.destroy).pack(side="left")
        dlg.update_idletasks()
        dw, dh = dlg.winfo_width(), dlg.winfo_height()
        px = self.root.winfo_x() + (self.root.winfo_width() - dw) // 2
        py = self.root.winfo_y() + (self.root.winfo_height() - dh) // 2
        dlg.geometry(f"+{px}+{py}")
        dlg.wait_window()
        if result[0]:
            try:
                with open(flag, "w") as f:
                    f.write("accepted")
            except Exception:
                pass
            return True
        return False

    def show_disclaimer(self):
        self._show_styled_dialog("免责声明", self.DISCLAIMER, confirm="我知道了")

    def _show_styled_dialog(self, title, message, confirm="确定", cancel=None):
        """Show a styled dialog matching the app's warm theme.
        Returns True if confirm clicked, False if cancel/window closed.
        Safe to call from any thread."""
        result = [False]
        is_main = (threading.current_thread() is threading.main_thread())

        def show():
            dlg = tk.Toplevel(self.root)
            dlg.title(title)
            dlg.transient(self.root)
            dlg.grab_set()
            dlg.resizable(False, False)
            dlg.configure(bg="#FBF7F2")

            f = tk.Frame(dlg, bg="#FBF7F2", padx=22, pady=22)
            f.pack()

            tk.Label(f, text=title, bg="#FBF7F2", fg="#3D3628",
                     font=("Microsoft YaHei UI", 14, "bold")).pack(anchor="w")
            tk.Label(f, text=message, bg="#FBF7F2", fg="#5C5042",
                     font=("Microsoft YaHei UI", 10), justify="left",
                     wraplength=400).pack(anchor="w", pady=(10, 16))

            btns = tk.Frame(f, bg="#FBF7F2")
            btns.pack()
            ctk.CTkButton(btns, text=confirm, font=("Microsoft YaHei UI", 11),
                          fg_color="#F59E0B", hover_color="#E8900A",
                          corner_radius=8, height=34, width=90,
                          command=lambda: [result.__setitem__(0, True), dlg.destroy()]
                          ).pack(side="left", padx=(0, 8))
            if cancel:
                ctk.CTkButton(btns, text=cancel, font=("Microsoft YaHei UI", 11),
                              fg_color="transparent", text_color="#7A6E5C",
                              hover_color="#F5F0E8", corner_radius=8, height=34,
                              command=dlg.destroy).pack(side="left")

            dlg.update_idletasks()
            dw, dh = dlg.winfo_width(), dlg.winfo_height()
            px = self.root.winfo_x() + (self.root.winfo_width() - dw) // 2
            py = self.root.winfo_y() + (self.root.winfo_height() - dh) // 2
            dlg.geometry(f"+{px}+{py}")
            dlg.wait_window()
            if not is_main:
                event.set()

        if is_main:
            show()
        else:
            event = threading.Event()
            self.root.after(0, show)
            event.wait()
        return result[0]

    def _extract_url(self, text):
        """从分享口令等混合文本中提取 URL"""
        urls = re.findall(r"https?://[^\s]+", text)
        return urls[0].rstrip(".,;:!?）)") if urls else text.strip()

    def paste_url(self):
        try:
            text = self.root.clipboard_get()
            if text:
                url = self._extract_url(text)
                self.url_var.set(url)
                if url != text.strip():
                    self.log("已从分享文本中提取链接")
                else:
                    self.log("已粘贴剪贴板内容")
        except Exception:
            pass

    def browse_dir(self):
        path = filedialog.askdirectory(title="选择保存目录")
        if path:
            self.dir_var.set(path)

    def open_dir(self):
        path = self.dir_var.get()
        os.makedirs(path, exist_ok=True)
        os.startfile(path)

    def log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def cancel_download(self):
        self._cancel_flag = True
        self.log("正在取消...")

    def start_download(self):
        raw = self.url_var.get().strip()
        if not raw:
            messagebox.showwarning("提示", "请先粘贴链接")
            return

        url = self._extract_url(raw)
        self.url_var.set(url)  # show cleaned URL in the input box

        out_dir = self.dir_var.get().strip()
        if not out_dir:
            messagebox.showwarning("提示", "请选择保存目录")
            return

        self.is_downloading = True
        self._cancel_flag = False
        self.dl_btn.configure(text="正在下载...", state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.info_var.set("")
        self._clear_log()

        thread = threading.Thread(target=self.download, args=(url, out_dir), daemon=True)
        thread.start()

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def progress_hook(self, d):
        if self._cancel_flag:
            raise Exception("用户取消")

        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                pct = downloaded / total * 100
                self.progress_bar.set(pct / 100.0)
                self.root.after(0, lambda p=pct: self.dl_btn.configure(text=f"下载中 {p:.0f}%"))
            speed = d.get("speed")
            speed_str = self._fmt_speed(speed) if speed else "N/A"
            size_str = f"{self._fmt_size(downloaded)}"
            if total > 0:
                size_str += f" / {self._fmt_size(total)}"
            self.info_var.set(f"下载中... {size_str} · {speed_str}")

        elif d["status"] == "finished":
            self.progress_bar.set(1)
            self.info_var.set("处理完成，正在封装...")
            self.root.after(0, lambda: self.dl_btn.configure(text="封装中..."))

    def _fmt_speed(self, speed):
        if speed is None:
            return "N/A"
        if speed < 1024:
            return f"{speed:.0f} B/s"
        elif speed < 1024 * 1024:
            return f"{speed / 1024:.1f} KB/s"
        else:
            return f"{speed / (1024 * 1024):.1f} MB/s"

    def _fmt_size(self, size):
        if size is None:
            return "?"
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"

    def _get_quality_options(self, formats, has_ffmpeg, audio_only):
        """Parse formats into (label, format_selector) tuples for user selection."""
        if audio_only:
            return self._get_audio_options(formats)
        return self._get_video_options(formats, has_ffmpeg)

    def _get_video_options(self, formats, has_ffmpeg):
        options = [("最佳画质", "bestvideo+bestaudio/best" if has_ffmpeg else "best")]

        seen_heights = set()
        for f in formats:
            height = f.get("height")
            if height and isinstance(height, int) and height > 0:
                seen_heights.add(height)

        for h in sorted(seen_heights, reverse=True):
            if has_ffmpeg:
                sel = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"
            else:
                sel = f"best[height<={h}]"
            options.append((f"{h}p", sel))

        return options

    def _get_audio_options(self, formats):
        options = [("最佳音质", "bestaudio/best")]
        added = set()
        entries = []

        for f in formats:
            # Skip formats that contain video
            vcodec = f.get("vcodec")
            if vcodec and vcodec != "none":
                continue
            if f.get("height") or f.get("width"):
                continue

            fid = f.get("format_id", "")
            if not fid:
                continue

            abr = f.get("abr")
            note = f.get("format_note", "")
            acodec = f.get("acodec", "")

            # Derive label and dedup key from whatever info is available
            if abr is not None and abr > 0:
                abr = int(abr)
                acodec_lower = acodec.lower()
                if any(t in acodec_lower for t in ("flac", "alac", "wav", "pcm")):
                    if abr <= 1200:
                        label = f"无损 ({acodec.upper()})"
                    elif abr <= 4000:
                        label = f"环绕声 ({acodec.upper()})"
                    else:
                        label = f"母带 ({acodec.upper()})"
                    key = f"lossless:{abr}"
                elif abr >= 256:
                    label = f"高品 {abr}kbps"
                    key = f"a{abr}"
                elif abr >= 128:
                    label = f"标准 {abr}kbps"
                    key = f"a{abr}"
                else:
                    label = f"低品 {abr}kbps"
                    key = f"a{abr}"
            elif note:
                label = note
                key = note
            else:
                label = fid
                key = fid

            if key in added:
                continue
            added.add(key)
            entries.append((label, fid))

        for label, fid in entries:
            options.append((label, fid))

        return options

    def _show_quality_dialog(self, options, audio_mode=False):
        """Show quality selection dialog. Blocks until user selects or cancels."""
        self._quality_result = None
        self._quality_event = threading.Event()
        label_text = "请选择音质：" if audio_mode else "请选择画质："
        title_text = "选择下载音质" if audio_mode else "选择下载画质"

        def show():
            dialog = tk.Toplevel(self.root)
            dialog.title(title_text)
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.resizable(False, False)
            dialog.configure(bg="#FBF7F2")

            main = tk.Frame(dialog, bg="#FBF7F2", padx=22, pady=22)
            main.pack(fill="both", expand=True)

            tk.Label(main, text=label_text, bg="#FBF7F2", fg="#3D3628",
                     font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", pady=(0, 12))

            var = tk.StringVar(value=options[0][0])

            rb_frame = tk.Frame(main, bg="#FBF7F2")
            rb_frame.pack(fill="x")
            for label, _ in options:
                ttk.Radiobutton(rb_frame, text=label, variable=var, value=label).pack(anchor="w", pady=3)

            def on_ok():
                selected = var.get()
                for label, sel in options:
                    if label == selected:
                        self._quality_result = sel
                        self._result_resolution = label
                        break
                dialog.destroy()

            def on_cancel():
                self._quality_result = None
                dialog.destroy()

            def check_cancel():
                if self._cancel_flag:
                    dialog.destroy()
                    return
                dialog.after(200, check_cancel)

            dialog.protocol("WM_DELETE_WINDOW", on_cancel)

            btn_frame = tk.Frame(main, bg="#FBF7F2")
            btn_frame.pack(pady=(14, 0))
            ctk.CTkButton(btn_frame, text="确定", font=("Microsoft YaHei UI", 11),
                          fg_color="#F59E0B", hover_color="#E8900A",
                          corner_radius=8, height=32, width=80,
                          command=on_ok).pack(side="left", padx=(0, 8))
            ctk.CTkButton(btn_frame, text="取消", font=("Microsoft YaHei UI", 11),
                          fg_color="transparent", text_color="#7A6E5C",
                          hover_color="#F5F0E8", corner_radius=8, height=32,
                          command=on_cancel).pack(side="left")

            dialog.update_idletasks()
            dw = dialog.winfo_width()
            dh = dialog.winfo_height()
            px = self.root.winfo_x() + (self.root.winfo_width() - dw) // 2
            py = self.root.winfo_y() + (self.root.winfo_height() - dh) // 2
            dialog.geometry(f"+{px}+{py}")

            dialog.after(200, check_cancel)
            dialog.wait_window()
            self._quality_event.set()

        self.root.after(0, show)
        self._quality_event.wait()

        if self._cancel_flag:
            return None
        return self._quality_result

    COOKIE_BROWSERS = ["edge", "chrome", "firefox"]

    # ---- Douyin via Playwright extractor (no cookies needed) ----

    def _resolve_douyin_api(self, url):
        """Try to resolve Douyin video info via Playwright. Returns (title, video_url, duration) or None."""
        if self._cancel_flag:
            return None

        try:
            from douyin_extractor import extract
            data = extract(url)
            if data is None:
                self.log("  [失败] Playwright 未能解析出视频地址")
                return None
            if "error" in data:
                self.log(f"  [失败] {data['error']}")
                return None

            video_url = data.get("video_url")
            if not video_url:
                self.log("  [失败] 未获取到视频地址")
                return None

            title = data.get("title", "未知")
            duration = f"{data.get('duration_sec', 0)}秒"
            return (title, video_url, duration)

        except ImportError:
            self.log("  [错误] douyin_extractor 模块未找到")
            return None
        except Exception as e:
            self.log(f"  [异常] {e}")
            return None

    # ---- End API parser ----

    def _ensure_ffmpeg(self):
        """Ensure ffmpeg is available. Returns path or None."""
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            return system_ffmpeg

        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        # Check next to exe/script
        ffmpeg_exe = os.path.join(base_dir, "ffmpeg.exe")
        if os.path.exists(ffmpeg_exe):
            return ffmpeg_exe

        # Check ffmpeg/ subdirectory
        ffmpeg_exe = os.path.join(base_dir, "ffmpeg", "ffmpeg.exe")
        if os.path.exists(ffmpeg_exe):
            return ffmpeg_exe

        # Download fallback — try mirror first, then GitHub
        mirrors = [
            "https://ghproxy.net/https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-win64-lgpl-shared.zip",
            "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-win64-lgpl-shared.zip",
        ]
        tmp = os.path.join(tempfile.gettempdir(), "ffmpeg_temp.zip")
        ffmpeg_dir = os.path.join(base_dir, "ffmpeg")

        for url in mirrors:
            try:
                self.log(f"  [提示] 正在下载 ffmpeg...")
                resp = requests.get(url, stream=True, timeout=60,
                                    headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                downloaded = 0
                with open(tmp, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if self._cancel_flag:
                            break
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                self.progress_bar.set(downloaded / total)
                                self.info_var.set(f"下载 ffmpeg... {downloaded / total * 100:.0f}%")
                if self._cancel_flag:
                    os.unlink(tmp)
                    return None

                os.makedirs(ffmpeg_dir, exist_ok=True)
                with zipfile.ZipFile(tmp, "r") as zf:
                    for name in zf.namelist():
                        if "/bin/" in name or name.startswith("bin/"):
                            basename = os.path.basename(name)
                            if basename:
                                with zf.open(name) as src, open(os.path.join(ffmpeg_dir, basename), "wb") as dst:
                                    dst.write(src.read())
                os.unlink(tmp)
                self.log("  ffmpeg 就绪")
                return os.path.join(ffmpeg_dir, "ffmpeg.exe")

            except Exception as e:
                self.log(f"  [提示] 从 {url[:40]}... 下载失败: {e}")
                if os.path.exists(tmp):
                    try:
                        os.unlink(tmp)
                    except Exception:
                        pass
                continue

        self.log("  [警告] ffmpeg 下载失败，无法合并视频音轨，画质将受限")
        self.log("  [提示] 请手动将 ffmpeg.exe 放到程序同目录下")
        return None

    def _extract_cookies_playwright(self, browser):
        """Use Playwright to extract cookies from a Chromium browser profile.
        This bypasses App-Bound Encryption since the actual browser process handles
        decryption. Returns path to a Netscape-format cookie file, or None."""
        if browser not in ("edge", "chrome"):
            return None

        if not _HAS_PLAYWRIGHT:
            self.log("  [警告] Playwright 未安装，无法提取浏览器 Cookie")
            return None

        profile_paths = {
            "edge": os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data"),
            "chrome": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
        }
        user_data_dir = profile_paths.get(browser)
        if not user_data_dir or not os.path.exists(user_data_dir):
            self.log(f"  [警告] 未找到 {browser.title()} 用户数据目录")
            return None

        channel_map = {"edge": "msedge", "chrome": "chrome"}
        channel = channel_map[browser]

        self.log(f"  正在通过 Playwright 提取 {browser.title()} Cookie...")
        self._unlock_browser_cookies(browser)
        # Remove stale profile lock files that survive process kill
        for pattern in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
            for f in glob.glob(os.path.join(user_data_dir, pattern + "*")):
                try:
                    os.unlink(f)
                except Exception:
                    pass
        time.sleep(0.5)

        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    channel=channel,
                    headless=True,
                    timeout=30000,
                )
                page = context.new_page()
                try:
                    page.goto("https://www.bilibili.com", wait_until="domcontentloaded", timeout=15000)
                except Exception:
                    pass

                cookies = context.cookies()
                context.close()

                # Write Netscape-format cookie file for yt-dlp
                import tempfile
                fd, path = tempfile.mkstemp(suffix=".txt", prefix="ytdl_cookies_")
                with os.fdopen(fd, "w", newline="\n") as f:
                    f.write("# Netscape HTTP Cookie File\n")
                    for c in cookies:
                        domain = c.get("domain", "")
                        flag = "TRUE" if domain.startswith(".") else "FALSE"
                        path_c = c.get("path", "/")
                        secure = "TRUE" if c.get("secure") else "FALSE"
                        expires = str(int(c.get("expires", 0))) if c.get("expires", -1) != -1 else "0"
                        name = c.get("name", "")
                        value = c.get("value", "")
                        f.write(f"{domain}\t{flag}\t{path_c}\t{secure}\t{expires}\t{name}\t{value}\n")

                return path

        except Exception as e:
            self.log(f"  [警告] Playwright Cookie 提取失败: {e}")
            return None

    def _build_ydl_opts(self, out_dir):
        ydl_opts = {
            "outtmpl": os.path.join(out_dir, "%(title).100s.%(ext)s"),
            "progress_hooks": [self.progress_hook],
            "quiet": True,
            "no_warnings": True,
            "retries": 5,
            "extractor_retries": 5,
            "fragment_retries": 5,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/131.0.0.0 Safari/537.36",
            },
        }

        ffmpeg_path = self._ensure_ffmpeg()
        if ffmpeg_path:
            ydl_opts["ffmpeg_location"] = ffmpeg_path

        if self.cookie_var.get():
            # Try Playwright extraction first (bypasses App-Bound Encryption)
            # Start with user's selected browser, then try others
            browsers_to_try = [self.browser_var.get()] + \
                [b for b in self.COOKIE_BROWSERS if b != self.browser_var.get()]
            for b in browsers_to_try:
                cookie_file = self._extract_cookies_playwright(b)
                if cookie_file:
                    ydl_opts["cookiefile"] = cookie_file
                    self._cookie_tmp_file = cookie_file
                    break
            # Fall back to yt-dlp built-in (only useful for Firefox, or if Playwright missing)
            if not ydl_opts.get("cookiefile"):
                ydl_opts["cookiesfrombrowser"] = (self.browser_var.get(),)

        if self.audio_only_var.get():
            ydl_opts["format"] = "bestaudio/best"
            if ffmpeg_path:
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }]
        else:
            ydl_opts["format"] = "bestvideo+bestaudio/best" if ffmpeg_path else "best"
            if ffmpeg_path:
                ydl_opts["merge_output_format"] = "mp4"

        return ydl_opts

    def _unlock_browser_cookies(self, browser):
        """Kill background browser processes that have no visible windows (Win11 keeps
        Edge alive 24/7 even when the user closes all windows). Firefox uses SQLite WAL
        mode so no unlock is needed."""
        exe_map = {"edge": "msedge.exe", "chrome": "chrome.exe"}
        exe = exe_map.get(browser, "")
        if not exe:
            return
        try:
            # Only kill processes without visible windows (i.e. background services)
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"Get-Process -Name '{exe[:-4]}' -ErrorAction SilentlyContinue "
                 "| Where-Object { $_.MainWindowTitle -eq '' } "
                 "| Stop-Process -Force"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                timeout=15,
            )
        except Exception:
            pass

    def _is_cookie_error(self, err):
        return ("Could not copy" in err
                or "cookie" in err.lower()
                or "DPAPI" in err
                or "Failed to decrypt" in err)

    def _resolve_file_conflict(self, filepath):
        """Check if file exists. If so, ask user to overwrite/rename/cancel.
        Returns final path or None if cancelled."""
        if not os.path.exists(filepath):
            return filepath

        result = [None]
        event = threading.Event()

        def show():
            dlg = tk.Toplevel(self.root)
            dlg.title("文件已存在")
            dlg.transient(self.root)
            dlg.grab_set()
            dlg.resizable(False, False)
            dlg.configure(bg="#FBF7F2")

            f = tk.Frame(dlg, bg="#FBF7F2", padx=20, pady=20)
            f.pack()

            tk.Label(f, text="文件已存在，如何处理？", bg="#FBF7F2", fg="#3D3628",
                     font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")
            tk.Label(f, text=os.path.basename(filepath), bg="#FBF7F2", fg="#7A6E5C",
                     font=("Microsoft YaHei UI", 9)).pack(anchor="w", pady=(4, 14))

            var = tk.StringVar(value="rename")

            opts = tk.Frame(f, bg="#FBF7F2")
            opts.pack(fill="x")
            ttk.Radiobutton(opts, text="自动重命名（末尾加序号）", variable=var,
                            value="rename").pack(anchor="w", pady=2)
            ttk.Radiobutton(opts, text="覆盖原文件", variable=var,
                            value="overwrite").pack(anchor="w", pady=2)

            btns = tk.Frame(f, bg="#FBF7F2")
            btns.pack(pady=(14, 0))
            ctk.CTkButton(btns, text="确定", font=("Microsoft YaHei UI", 11),
                          fg_color="#F59E0B", hover_color="#E8900A",
                          corner_radius=8, height=34, width=80,
                          command=lambda: [result.__setitem__(0, var.get()), dlg.destroy()]
                          ).pack(side="left", padx=(0, 8))
            ctk.CTkButton(btns, text="取消下载", font=("Microsoft YaHei UI", 11),
                          fg_color="transparent", text_color="#E0554A",
                          hover_color="#FBEBE9", corner_radius=8, height=34,
                          command=dlg.destroy).pack(side="left")

            dlg.update_idletasks()
            dw, dh = dlg.winfo_width(), dlg.winfo_height()
            px = self.root.winfo_x() + (self.root.winfo_width() - dw) // 2
            py = self.root.winfo_y() + (self.root.winfo_height() - dh) // 2
            dlg.geometry(f"+{px}+{py}")
            dlg.wait_window()
            event.set()

        self.root.after(0, show)
        event.wait()

        if self._cancel_flag or result[0] is None:
            return None
        if result[0] == "overwrite":
            return filepath
        # auto-rename: find next available (1), (2), etc.
        base, ext = os.path.splitext(filepath)
        counter = 1
        while os.path.exists(f"{base} ({counter}){ext}"):
            counter += 1
        return f"{base} ({counter}){ext}"

    def _download_direct(self, video_url, out_dir, title):
        """Download video directly from a URL with progress tracking."""
        # Sanitize: strip newlines, control chars, and filesystem-illegal characters
        safe_title = title.replace("\n", " ").replace("\r", " ")
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", safe_title)
        safe_title = "".join(c for c in safe_title if c.isprintable())
        safe_title = safe_title.strip()[:100]
        filepath = os.path.join(out_dir, safe_title + ".mp4")
        filepath = self._resolve_file_conflict(filepath)
        if filepath is None:
            raise Exception("用户取消")

        resp = requests.get(video_url, stream=True, timeout=60,
                            headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))

        downloaded = 0
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if self._cancel_flag:
                    raise Exception("用户取消")
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded / total * 100
                        self.progress_bar.set(pct / 100.0)
                        speed = downloaded / 1024 / 1024  # rough
                        self.info_var.set(f"下载中... {self._fmt_size(downloaded)} / {self._fmt_size(total) if total > 0 else '?'}")

        self.progress_bar.set(1)
        return filepath

    def _is_douyin_url(self, url):
        return "douyin.com" in url.lower()

    def _expand_short_url(self, url):
        """Resolve v.douyin.com short links to full www.douyin.com URLs."""
        if "v.douyin.com" not in url:
            return url
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/148.0.0.0 Safari/537.36"
                )},
                allow_redirects=True, timeout=15,
            )
            if "douyin.com/video/" in resp.url or "douyin.com/note/" in resp.url:
                self.log(f"  已解析短链接")
                return resp.url
        except Exception:
            pass
        return url

    def download(self, url, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        self.log("=" * 50)
        self.log(f"目标链接: {url[:80]}{'...' if len(url) > 80 else ''}")
        self.log(f"保存目录: {out_dir}")

        # Resolve v.douyin.com short links so Playwright/yt-dlp get the full URL
        url = self._expand_short_url(url)

        # Try Douyin via Playwright (no cookies needed)
        if self._is_douyin_url(url) and not self.audio_only_var.get():
            self.log("--- 方式1: Playwright 解析（无需登录） ---")
            result = self._resolve_douyin_api(url)
            if result:
                title, video_url, duration = result
                self._result_title = title
                self._result_resolution = "未知（抖音直链）"
                self.log(f"标题: {title}")
                self.log(f"时长: {duration}")
                self.log("开始下载...")
                try:
                    self._download_direct(video_url, out_dir, title)
                    self.root.after(0, lambda: self._on_complete())
                    return
                except Exception as e:
                    err = str(e)
                    if "用户取消" in err:
                        self.root.after(0, lambda: self._on_cancel())
                        return
                    self.log(f"  [失败] 直链下载失败: {err}")
                    self.log("  [失败] Playwright 未能解析出视频地址")
            else:
                self.log("  [失败] Playwright 未能解析出视频地址")

        # yt-dlp download (with optional cookie fallback)
        if self._is_douyin_url(url):
            self.log("--- 方式2: yt-dlp 兜底 ---")
        else:
            self.log("--- yt-dlp 下载 ---")
        ydl_opts = self._build_ydl_opts(out_dir)

        # Try with cookies; fall back through browsers, then cookieless
        tried_browsers = []
        while True:
            try:
                self.log("正在获取视频信息...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get("title", "未知")
                    duration = info.get("duration_string") or f"{info.get('duration', 0)}秒"
                    uploader = info.get("uploader") or info.get("channel") or "未知"
                    height = info.get("height") or 0
                    self._result_title = title
                    self._result_resolution = f"{height}p" if height else "未知"

                    if not ydl_opts.get("cookiesfrombrowser"):
                        if 0 < height <= 480:
                            self.log(f"  [提示] 当前最高画质仅 {height}p，部分网站登录后可获取更高画质")
                            self.log(f"  [提示] 请勾选「使用浏览器 Cookie」后重试")

                    self.root.after(0, lambda t=title: self.log(f"标题: {t}"))
                    self.root.after(0, lambda u=uploader: self.log(f"作者: {u}"))
                    self.root.after(0, lambda d=duration: self.log(f"时长: {d}"))

                # Quality selection
                formats = info.get("formats", [])
                ffmpeg_ok = bool(ydl_opts.get("ffmpeg_location"))
                audio_only = self.audio_only_var.get()

                # Auto-detect: if no format has video, treat as audio
                if not audio_only and formats:
                    has_video = any(
                        f.get("height") or f.get("width") or
                        (f.get("vcodec") and f.get("vcodec") != "none")
                        for f in formats
                    )
                    if not has_video:
                        audio_only = True

                options = self._get_quality_options(formats, ffmpeg_ok, audio_only)
                selected_format = self._show_quality_dialog(options, audio_mode=audio_only)
                if selected_format is None:
                    self.root.after(0, lambda: self._on_cancel())
                    return
                ydl_opts["format"] = selected_format

                if audio_only and ffmpeg_ok and "postprocessors" not in ydl_opts:
                    ydl_opts["postprocessors"] = [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                    }]

                # Check for duplicate files before downloading
                expected_ext = "mp3" if audio_only else "mp4"
                safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)[:100]
                expected_path = os.path.join(out_dir, safe_title + "." + expected_ext)
                final_path = self._resolve_file_conflict(expected_path)
                if final_path is None:
                    self.root.after(0, lambda: self._on_cancel())
                    return
                if final_path != expected_path:
                    ydl_opts["outtmpl"] = os.path.join(out_dir, os.path.splitext(os.path.basename(final_path))[0] + ".%(ext)s")

                self.root.after(0, lambda: self.log("开始下载..."))

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                self.root.after(0, lambda: self._on_complete())
                return

            except Exception as e:
                err = str(e)
                if "用户取消" in err:
                    self.root.after(0, lambda: self._on_cancel())
                    return

                if self._is_cookie_error(err) and (ydl_opts.get("cookiesfrombrowser") or ydl_opts.get("cookiefile")):
                    if ydl_opts.get("cookiefile"):
                        # Playwright cookie file failed — remove it and try next browser
                        self._cleanup_cookies()
                        ydl_opts.pop("cookiefile", None)
                    if ydl_opts.get("cookiesfrombrowser"):
                        tried_browsers.append(ydl_opts["cookiesfrombrowser"][0])
                        ydl_opts.pop("cookiesfrombrowser", None)

                    remaining = [b for b in self.COOKIE_BROWSERS if b not in tried_browsers]
                    if remaining:
                        nxt = remaining[0]
                        self.log(f"尝试 {nxt.title()} 浏览器 Cookie...")
                        # Try Playwright first for Chromium browsers
                        cookie_file = self._extract_cookies_playwright(nxt)
                        if cookie_file:
                            ydl_opts["cookiefile"] = cookie_file
                            self._cookie_tmp_file = cookie_file
                        else:
                            ydl_opts["cookiesfrombrowser"] = (nxt,)
                            self._unlock_browser_cookies(nxt)
                        continue
                    else:
                        # All browsers exhausted — fall back to cookieless
                        self.log("  所有浏览器 Cookie 均不可用，降级为无登录下载...")
                        if ydl_opts.get("ffmpeg_location"):
                            ydl_opts["format"] = "bestvideo+bestaudio/best"
                        else:
                            ydl_opts["format"] = "best"
                        continue

                tb = traceback.format_exc()
                self.root.after(0, lambda e=err, t=tb: self._on_error(e, t))
                return

    def _cleanup_cookies(self):
        if self._cookie_tmp_file and os.path.exists(self._cookie_tmp_file):
            try:
                os.unlink(self._cookie_tmp_file)
            except Exception:
                pass
            self._cookie_tmp_file = None

    def _on_complete(self):
        self._cleanup_cookies()
        self.is_downloading = False
        self.dl_btn.configure(text="开始下载", state="normal")
        self.cancel_btn.configure(state="disabled")
        self.info_var.set("完成！")
        self.log("下载完成，文件已保存到目标目录")
        title = self._result_title or "未知"
        res = self._result_resolution or "未知"
        quality_label = "品质" if self.audio_only_var.get() else "清晰度"
        messagebox.showinfo("下载完成", f"《{title}》\n{quality_label}：{res}")

    def _on_cancel(self):
        self._cleanup_cookies()
        self.is_downloading = False
        self.dl_btn.configure(text="开始下载", state="normal")
        self.cancel_btn.configure(state="disabled")
        self.info_var.set("已取消")
        self.log("下载已取消")

    def _on_error(self, err, tb):
        self._cleanup_cookies()
        self.is_downloading = False
        self.dl_btn.configure(text="开始下载", state="normal")
        self.cancel_btn.configure(state="disabled")
        self.info_var.set("下载失败，查看下方日志")
        self.log(f"错误: {err}")
        if tb:
            self.log("--- 完整错误信息 ---")
            for line in tb.strip().split("\n"):
                self.log(line)


if __name__ == "__main__":
    root = tk.Tk()
    app = MediaDownloader(root)
    root.mainloop()
