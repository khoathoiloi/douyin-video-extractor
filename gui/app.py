"""
GUI Module: Douyin Video Extractor & AI Filter Desktop Application
Built with CustomTkinter for a modern, responsive user experience.
"""

import os
import sys
import json
import webbrowser
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk

from core.cloud_client import DouyinCloudClient, DEFAULT_SERVER_URL
from core.analyzer import DouyinAIAnalyzer, DOUYIN_TAXONOMY
from core.filters import DouyinFilter
from core.exporter import DouyinExporter

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


class DouyinExtractorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Douyin Video Extractor & AI Cloud Client - by khoathoiloi")
        self.geometry("1100x750")
        self.minsize(950, 650)

        # Application state
        self.raw_videos = []
        self.filtered_videos = []
        self.is_searching = False
        self.is_downloading = False

        # Load configuration
        self.config = self._load_config()

        # Initialize Cloud Client (Default: http://127.0.0.1:8000 or custom Cloud URL)
        self.cloud_client = DouyinCloudClient(server_url=self.config.get("server_url", DEFAULT_SERVER_URL))

        # Local fallback analyzer
        self.analyzer = DouyinAIAnalyzer(
            api_key=self.config.get("ai_api_key", ""),
            provider=self.config.get("ai_provider", "gemini")
        )

        # Build UI layout
        self._build_ui()

        # Ping server on startup
        self.after(500, self._check_server_health)

    def _load_config(self) -> dict:
        default_config = {
            "server_url": DEFAULT_SERVER_URL,
            "ai_provider": "gemini",
            "ai_api_key": "",
            "douyin_cookie": "",
            "download_folder": os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads"),
            "theme": "Dark"
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception:
                pass
        return default_config

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Left Navigation Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="🎵 Douyin Client",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 5))

        self.version_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Cloud API Edition v2.0",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.version_label.grid(row=1, column=0, padx=20, pady=(0, 15))

        # Cloud Status badge
        self.status_badge = ctk.CTkLabel(
            self.sidebar_frame,
            text="☁️ Đang kết nối Cloud...",
            font=ctk.CTkFont(size=11),
            text_color="#CBD5E0",
            fg_color="#2D3748",
            corner_radius=6,
            height=25
        )
        self.status_badge.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")

        # Navigation buttons
        self.nav_btn_ai = ctk.CTkButton(
            self.sidebar_frame, text="🧠 AI Studio & Video", command=lambda: self._select_tab("ai"),
            height=40, font=ctk.CTkFont(size=13, weight="bold")
        )
        self.nav_btn_ai.grid(row=3, column=0, padx=15, pady=6, sticky="ew")

        self.nav_btn_search = ctk.CTkButton(
            self.sidebar_frame, text="🔍 Tìm Kiếm & Lọc", command=lambda: self._select_tab("search"),
            height=40, font=ctk.CTkFont(size=13, weight="bold")
        )
        self.nav_btn_search.grid(row=4, column=0, padx=15, pady=6, sticky="ew")

        self.nav_btn_export = ctk.CTkButton(
            self.sidebar_frame, text="📊 Xuất & Tải Video", command=lambda: self._select_tab("export"),
            height=40, font=ctk.CTkFont(size=13, weight="bold")
        )
        self.nav_btn_export.grid(row=5, column=0, padx=15, pady=6, sticky="ew")

        self.nav_btn_settings = ctk.CTkButton(
            self.sidebar_frame, text="⚙️ Cài Đặt Cloud", command=lambda: self._select_tab("settings"),
            height=40, font=ctk.CTkFont(size=13, weight="bold")
        )
        self.nav_btn_settings.grid(row=6, column=0, padx=15, pady=6, sticky="ew")

    def _check_server_health(self):
        def _worker():
            res = self.cloud_client.ping()
            self.after(0, lambda: self._update_server_badge(res))
        threading.Thread(target=_worker, daemon=True).start()

    def _update_server_badge(self, res: dict):
        if res.get("connected"):
            self.status_badge.configure(
                text=f"🟢 Cloud Online ({res.get('latency_ms')}ms)",
                fg_color="#1C4532",
                text_color="#9AE6B4"
            )
        else:
            self.status_badge.configure(
                text="🔴 Cloud Mất Kết Nối",
                fg_color="#742A2A",
                text_color="#FEB2B2"
            )

        # Bottom stats
        self.status_box = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.status_box.grid(row=7, column=0, padx=15, pady=20, sticky="s")

        self.lbl_stats = ctk.CTkLabel(
            self.status_box,
            text="Video đã quét: 0",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        self.lbl_stats.pack(anchor="w")

        # Right Main Container
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.tab_frames = {
            "ai": self._create_ai_tab(),
            "search": self._create_search_tab(),
            "export": self._create_export_tab(),
            "settings": self._create_settings_tab()
        }

        self._select_tab("ai")

    def _select_tab(self, tab_name: str):
        for name, frame in self.tab_frames.items():
            if name == tab_name:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

        buttons = {
            "ai": self.nav_btn_ai,
            "search": self.nav_btn_search,
            "export": self.nav_btn_export,
            "settings": self.nav_btn_settings
        }
        for name, btn in buttons.items():
            if name == tab_name:
                btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            else:
                btn.configure(fg_color="transparent")

    # ================= TAB 1: AI STUDIO & VIDEO =================
    def _create_ai_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_rowconfigure(4, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(
            frame,
            text="🧠 Phân Tích Ý Tưởng, Link & Video Đa Phương Thức (Cloud AI)",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        sub_lbl = ctk.CTkLabel(
            frame,
            text="Dán Link Douyin/TikTok, Chọn Video từ máy tính hoặc nhập ý tưởng. Toàn bộ xử lý AI (ASR, OCR, Keyframes, 20 Queries) chạy trên Cloud Server.",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
            wraplength=800,
            justify="left"
        )
        sub_lbl.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        # Input Area
        input_box = ctk.CTkFrame(frame)
        input_box.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        input_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(input_box, text="Link / Ý Tưởng / File:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.ai_input_text = ctk.CTkTextbox(input_box, height=65)
        self.ai_input_text.grid(row=0, column=1, columnspan=2, padx=10, pady=8, sticky="ew")
        self.ai_input_text.insert("0.0", "https://www.douyin.com/video/7268899827364121914")

        btn_select_file = ctk.CTkButton(
            input_box,
            text="📁 Chọn Video...",
            width=110,
            fg_color="#4A5568",
            command=self._on_select_local_video
        )
        btn_select_file.grid(row=0, column=3, padx=10, pady=8)

        # Row 2
        ctk.CTkLabel(input_box, text="Chủ đề gợi ý:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        niche_names = ["Tự động phát hiện"] + [v["name"] for v in DOUYIN_TAXONOMY.values()]
        self.niche_combo = ctk.CTkComboBox(input_box, values=niche_names, width=280)
        self.niche_combo.set("Tự động phát hiện")
        self.niche_combo.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.deep_search_check = ctk.CTkCheckBox(input_box, text="Deep Search (Quét sâu 50-300 video)")
        self.deep_search_check.grid(row=1, column=2, padx=10, pady=10, sticky="w")

        self.btn_run_ai = ctk.CTkButton(
            input_box,
            text="🚀 Gửi Lên Cloud Phân Tích",
            font=ctk.CTkFont(weight="bold"),
            command=self._on_run_ai_analysis,
            height=35
        )
        self.btn_run_ai.grid(row=1, column=3, padx=10, pady=10)

        # Progress bar
        self.ai_progress_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.ai_progress_frame.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        self.ai_progress_frame.grid_columnconfigure(0, weight=1)

        self.ai_progress_bar = ctk.CTkProgressBar(self.ai_progress_frame)
        self.ai_progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.ai_progress_bar.set(0)

        self.lbl_ai_stage = ctk.CTkLabel(self.ai_progress_frame, text="Trạng thái: Sẵn sàng gửi tác vụ lên Cloud", text_color="gray70", font=ctk.CTkFont(size=12))
        self.lbl_ai_stage.grid(row=1, column=0, sticky="w")

        # Result display
        result_box = ctk.CTkFrame(frame)
        result_box.grid(row=4, column=0, padx=20, pady=(5, 15), sticky="nsew")
        result_box.grid_rowconfigure(1, weight=1)
        result_box.grid_columnconfigure(0, weight=1)

        result_header = ctk.CTkFrame(result_box, fg_color="transparent")
        result_header.grid(row=0, column=0, padx=10, pady=8, sticky="ew")
        result_header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(result_header, text="📋 Kết quả Từ Khóa & Phân Tích:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w")
        
        self.btn_use_keyword = ctk.CTkButton(
            result_header,
            text="➡️ Đưa Kết Quả Sang Bảng Tìm Kiếm",
            command=self._on_transfer_keyword_to_search,
            fg_color="#2FA572",
            hover_color="#1E7A52",
            height=30
        )
        self.btn_use_keyword.grid(row=0, column=2, sticky="e")

        self.ai_output_text = ctk.CTkTextbox(result_box, font=ctk.CTkFont(family="Consolas", size=13))
        self.ai_output_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        return frame

    def _on_select_local_video(self):
        f = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv *.webm")])
        if f:
            self.ai_input_text.delete("0.0", "end")
            self.ai_input_text.insert("0.0", f)

    def _on_run_ai_analysis(self):
        user_input = self.ai_input_text.get("0.0", "end").strip()
        if not user_input:
            messagebox.showwarning("Thông báo", "Vui lòng dán Link Douyin, chọn Video hoặc nhập ý tưởng.")
            return

        self.btn_run_ai.configure(state="disabled", text="⏳ Đang xử lý trên Cloud...")
        self.ai_progress_bar.set(0.05)
        self.lbl_ai_stage.configure(text="Đang gửi dữ liệu lên Cloud Server...")
        self.ai_output_text.delete("0.0", "end")
        deep_search = bool(self.deep_search_check.get())

        def _progress_cb(pct, stage_name, job_data):
            self.after(0, lambda: self._update_ai_progress(pct, stage_name))

        def _worker():
            if user_input.startswith("http://") or user_input.startswith("https://"):
                res = self.cloud_client.analyze_url(user_input, deep_search=deep_search, progress_callback=_progress_cb)
            elif os.path.exists(user_input) and os.path.isfile(user_input):
                res = self.cloud_client.analyze_video_file(user_input, deep_search=deep_search, progress_callback=_progress_cb)
            else:
                search_res = self.cloud_client.search_keyword(user_input, limit=50 if deep_search else 20, deep_search=deep_search)
                if search_res.get("success"):
                    d = search_res["data"]
                    res = {
                        "success": True,
                        "job_id": d.get("job_id"),
                        "queries": [user_input],
                        "results": d.get("results", []),
                        "analysis": {"summary": f"Tìm kiếm từ khóa '{user_input}'", "main_topic": user_input}
                    }
                else:
                    res = search_res

            self.after(0, lambda: self._display_cloud_ai_result(res))

        threading.Thread(target=_worker, daemon=True).start()

    def _update_ai_progress(self, pct: int, stage_name: str):
        self.ai_progress_bar.set(pct / 100.0)
        self.lbl_ai_stage.configure(text=f"Tiến độ Cloud: {pct}% — {stage_name}")

    def _display_cloud_ai_result(self, res: dict):
        self.btn_run_ai.configure(state="normal", text="🚀 Gửi Lên Cloud Phân Tích")
        self.ai_progress_bar.set(1.0)
        self.lbl_ai_stage.configure(text="Trạng thái: Hoàn tất!")

        if not res.get("success", False):
            err = res.get("error", "Không xác định")
            self.ai_output_text.insert("0.0", f"❌ Lỗi từ Cloud Server:\n{err}")
            messagebox.showerror("Lỗi Cloud", err)
            return

        analysis = res.get("analysis") or {}
        queries = res.get("queries") or []
        results = res.get("results") or []

        output_str = "=== ☁️ KẾT QUẢ PHÂN TÍCH TỪ CLOUD SERVER ===\n\n"
        if analysis:
            output_str += f"📌 Chủ Đề Chính: {analysis.get('main_topic', 'N/A')}\n"
            output_str += f"📝 Tóm Tắt Nội Dung: {analysis.get('summary', 'N/A')}\n"
            if analysis.get('transcript'):
                output_str += f"🎙️ Giọng Nói (ASR): {analysis.get('transcript')}\n"
            output_str += "\n"

        if queries:
            output_str += f"🔥 20 TỪ KHÓA TÌM KIẾM TIẾNG TRUNG TỐI ƯU (SEO DOUYIN):\n"
            for i, q in enumerate(queries, 1):
                output_str += f"   {i:2d}. {q}\n"
            output_str += "\n"

        if results:
            output_str += f"🎬 ĐÃ TÌM THẤY & XẾP HẠNG {len(results)} VIDEO LIÊN QUAN TRÊN DOUYIN:\n"
            for i, r in enumerate(results[:5], 1):
                output_str += f"   [{i}] Điểm: {r.get('score')}% ({r.get('match_tier')}) — {r.get('title')}\n"
                output_str += f"       Tác giả: {r.get('author')} | Likes: {r.get('like_count'):,} | Link: {r.get('url')}\n"
            if len(results) > 5:
                output_str += f"   ... và {len(results) - 5} video khác. Bấm 'Đưa Kết Quả Sang Bảng Tìm Kiếm' để xem đầy đủ!\n"

        self.ai_output_text.insert("0.0", output_str)
        self.last_cloud_results = results
        self.last_generated_keyword = queries[0] if queries else ""

    def _on_transfer_keyword_to_search(self):
        if hasattr(self, "last_cloud_results") and self.last_cloud_results:
            self._display_results_in_table(self.last_cloud_results)
            self._select_tab("search")
        elif getattr(self, "last_generated_keyword", ""):
            self.search_entry.delete(0, "end")
            self.search_entry.insert(0, self.last_generated_keyword)
            self._select_tab("search")
        else:
            messagebox.showinfo("Thông báo", "Vui lòng phân tích từ khóa hoặc video trước.")

    # ================= TAB 2: SEARCH & FILTER =================
    def _create_search_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Search Controls Bar
        ctrl_frame = ctk.CTkFrame(frame)
        ctrl_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        ctrl_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(ctrl_frame, text="Từ khóa Douyin:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.search_entry = ctk.CTkEntry(ctrl_frame, placeholder_text="Nhập từ khóa tiếng Trung / Việt (ví dụ: 搞笑短剧, gái xinh, 美食教程)...", height=35)
        self.search_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.search_entry.insert(0, "搞笑短剧")

        self.btn_search = ctk.CTkButton(
            ctrl_frame,
            text="🔍 Tìm Kiếm Cloud",
            font=ctk.CTkFont(weight="bold"),
            command=self._on_start_search,
            width=140,
            height=35
        )
        self.btn_search.grid(row=0, column=2, padx=10, pady=10)

        # Filter Options Accordion/Frame
        filter_frame = ctk.CTkFrame(frame)
        filter_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        # Row 1 of filters
        ctk.CTkLabel(filter_frame, text="Số lượng:").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.count_combo = ctk.CTkComboBox(filter_frame, values=["10", "20", "50", "100"], width=80)
        self.count_combo.set("20")
        self.count_combo.grid(row=0, column=1, padx=5, pady=8, sticky="w")

        ctk.CTkLabel(filter_frame, text="Likes tối thiểu:").grid(row=0, column=2, padx=(15, 5), pady=8, sticky="w")
        self.min_likes_combo = ctk.CTkComboBox(filter_frame, values=["0", "5,000", "10,000", "50,000", "100,000", "500,000"], width=110)
        self.min_likes_combo.set("10,000")
        self.min_likes_combo.grid(row=0, column=3, padx=5, pady=8, sticky="w")

        self.search_deep_check = ctk.CTkCheckBox(filter_frame, text="Deep Search")
        self.search_deep_check.grid(row=0, column=4, padx=15, pady=8, sticky="w")

        self.btn_apply_filter = ctk.CTkButton(
            filter_frame,
            text="⚡ Lọc Lại",
            command=self._apply_current_filters,
            width=100,
            fg_color="#4A5568"
        )
        self.btn_apply_filter.grid(row=0, column=5, padx=10, pady=8)

        # Table Results Area
        table_frame = ctk.CTkFrame(frame)
        table_frame.grid(row=2, column=0, padx=15, pady=(10, 15), sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        columns = ("stt", "score", "id", "title", "author", "likes", "comments", "query")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")
        
        self.tree.heading("stt", text="#")
        self.tree.heading("score", text="Điểm AI")
        self.tree.heading("id", text="ID Video")
        self.tree.heading("title", text="Tiêu đề Video")
        self.tree.heading("author", text="Tác giả")
        self.tree.heading("likes", text="Lượt Thích")
        self.tree.heading("comments", text="Bình Luận")
        self.tree.heading("query", text="Từ Khóa")

        self.tree.column("stt", width=40, anchor="center")
        self.tree.column("score", width=70, anchor="center")
        self.tree.column("id", width=130, anchor="center")
        self.tree.column("title", width=360, anchor="w")
        self.tree.column("author", width=120, anchor="w")
        self.tree.column("likes", width=100, anchor="e")
        self.tree.column("comments", width=80, anchor="e")
        self.tree.column("query", width=120, anchor="w")

        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Double-1>", self._on_tree_double_click)

        return frame

    def _on_start_search(self):
        kw = self.search_entry.get().strip()
        if not kw:
            messagebox.showwarning("Thông báo", "Vui lòng nhập từ khóa tìm kiếm Douyin.")
            return

        count = int(self.count_combo.get())
        deep_search = bool(self.search_deep_check.get())
        self.btn_search.configure(state="disabled", text="⏳ Đang quét Cloud...")

        def _worker():
            res = self.cloud_client.search_keyword(kw, limit=count, deep_search=deep_search)
            self.after(0, lambda: self._on_search_completed(res))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_search_completed(self, res: dict):
        self.btn_search.configure(state="normal", text="🔍 Tìm Kiếm Cloud")
        if not res.get("success"):
            err = res.get("error", "Không thể tìm kiếm trên Cloud.")
            messagebox.showerror("Lỗi Tìm Kiếm", err)
            return

        items = res.get("data", {}).get("results", [])
        self._display_results_in_table(items)

    def _display_results_in_table(self, items: list):
        self.raw_videos = []
        for it in items:
            self.raw_videos.append({
                "aweme_id": it.get("video_id", ""),
                "title": it.get("title", ""),
                "author_name": it.get("author", ""),
                "digg_count": it.get("like_count", 0),
                "comment_count": it.get("comment_count", 0),
                "share_count": it.get("share_count", 0),
                "duration": it.get("duration", 30),
                "web_url": it.get("url", ""),
                "video_no_watermark_url": it.get("url", ""),
                "score": it.get("score", 90),
                "search_query": it.get("search_query", "")
            })

        self._apply_current_filters()

    def _apply_current_filters(self):
        likes_str = self.min_likes_combo.get().replace(",", "").replace(".", "").strip()
        min_likes = int(likes_str) if likes_str.isdigit() else 0

        self.filtered_videos = [v for v in self.raw_videos if v.get("digg_count", 0) >= min_likes]

        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, v in enumerate(self.filtered_videos, 1):
            score_text = f"{v.get('score', 90)}%"
            self.tree.insert("", "end", values=(
                i,
                score_text,
                v.get("aweme_id", ""),
                v.get("title", ""),
                v.get("author_name", ""),
                f"{v.get('digg_count', 0):,}",
                f"{v.get('comment_count', 0):,}",
                v.get("search_query", "")
            ))

        if hasattr(self, "lbl_export_count"):
            self.lbl_export_count.configure(text=f"Số lượng video sẵn sàng xuất: {len(self.filtered_videos)}")

    def _on_tree_double_click(self, event):
        selected_item = self.tree.focus()
        if not selected_item:
            return
        vals = self.tree.item(selected_item, "values")
        if vals:
            video_id = vals[2]
            url = f"https://www.douyin.com/video/{video_id}"
            webbrowser.open(url)

    # ================= TAB 3: EXPORT & DOWNLOAD =================
    def _create_export_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(frame, text="📥 Trích Xuất Dữ Liệu & Tải Video Hàng Loạt", font=ctk.CTkFont(size=18, weight="bold"))
        lbl.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        self.lbl_export_count = ctk.CTkLabel(
            frame,
            text="Số lượng video sẵn sàng xuất: 0",
            font=ctk.CTkFont(size=14),
            text_color="gray70"
        )
        self.lbl_export_count.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        btn_box = ctk.CTkFrame(frame)
        btn_box.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        btn_box.grid_columnconfigure((0, 1), weight=1)

        # Left export box
        left_box = ctk.CTkFrame(btn_box)
        left_box.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        ctk.CTkLabel(left_box, text="📊 Xuất Báo Cáo & Danh Sách", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=15, pady=(15, 10), anchor="w")

        btn_excel = ctk.CTkButton(
            left_box,
            text="📊 Xuất File Excel (.xlsx)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#107C41",
            hover_color="#0B5C30",
            height=40,
            command=self._on_export_excel
        )
        btn_excel.pack(padx=15, pady=8, fill="x")

        btn_csv = ctk.CTkButton(
            left_box,
            text="📄 Xuất File CSV (.csv)",
            font=ctk.CTkFont(size=13),
            fg_color="#2D3748",
            height=40,
            command=self._on_export_csv
        )
        btn_csv.pack(padx=15, pady=8, fill="x")

        btn_txt = ctk.CTkButton(
            left_box,
            text="📝 Xuất Danh Sách Link (.txt)",
            font=ctk.CTkFont(size=13),
            fg_color="#2D3748",
            height=40,
            command=self._on_export_txt
        )
        btn_txt.pack(padx=15, pady=8, fill="x")

        btn_copy = ctk.CTkButton(
            left_box,
            text="📋 Sao Chép Tất Cả Link Không Logo",
            font=ctk.CTkFont(size=13),
            fg_color="#4A5568",
            height=40,
            command=self._on_copy_all_links
        )
        btn_copy.pack(padx=15, pady=8, fill="x")

        # Right download box
        right_box = ctk.CTkFrame(btn_box)
        right_box.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        ctk.CTkLabel(right_box, text="⬇️ Tải Video Trực Tiếp Về Máy", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=15, pady=(15, 10), anchor="w")

        self.btn_download_batch = ctk.CTkButton(
            right_box,
            text="⬇️ Bắt Đầu Tải Hàng Loạt Video (HD No-WM)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#E53E3E",
            hover_color="#C53030",
            height=45,
            command=self._on_start_batch_download
        )
        self.btn_download_batch.pack(padx=15, pady=(15, 10), fill="x")

        self.download_progress = ctk.CTkProgressBar(right_box)
        self.download_progress.pack(padx=15, pady=10, fill="x")
        self.download_progress.set(0)

        self.lbl_download_status = ctk.CTkLabel(right_box, text="Trạng thái: Sẵn sàng", text_color="gray70")
        self.lbl_download_status.pack(padx=15, pady=5, anchor="w")

        return frame

    def _on_export_excel(self):
        if not self.filtered_videos:
            messagebox.showwarning("Thông báo", "Chưa có dữ liệu video để xuất.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")], initialfile="douyin_videos.xlsx")
        if filepath:
            DouyinExporter.export_to_excel(self.filtered_videos, filepath)
            messagebox.showinfo("Thành công", f"Đã xuất {len(self.filtered_videos)} video ra file Excel:\n{filepath}")

    def _on_export_csv(self):
        if not self.filtered_videos:
            messagebox.showwarning("Thông báo", "Chưa có dữ liệu video để xuất.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")], initialfile="douyin_videos.csv")
        if filepath:
            DouyinExporter.export_to_csv(self.filtered_videos, filepath)
            messagebox.showinfo("Thành công", f"Đã xuất file CSV:\n{filepath}")

    def _on_export_txt(self):
        if not self.filtered_videos:
            messagebox.showwarning("Thông báo", "Chưa có dữ liệu video để xuất.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")], initialfile="douyin_links.txt")
        if filepath:
            DouyinExporter.export_to_txt(self.filtered_videos, filepath, only_links=True)
            messagebox.showinfo("Thành công", f"Đã xuất danh sách link ra file:\n{filepath}")

    def _on_copy_all_links(self):
        if not self.filtered_videos:
            messagebox.showwarning("Thông báo", "Chưa có dữ liệu video để sao chép.")
            return
        links = [v.get("web_url") or f"https://www.douyin.com/video/{v.get('aweme_id')}" for v in self.filtered_videos]
        self.clipboard_clear()
        self.clipboard_append("\n".join(links))
        messagebox.showinfo("Thành công", f"Đã sao chép {len(links)} link xem video Douyin (mở được ngay trên trình duyệt) vào Clipboard!")

    def _on_start_batch_download(self):
        if not self.filtered_videos:
            messagebox.showwarning("Thông báo", "Chưa có danh sách video để tải.")
            return

        download_dir = self.config.get("download_folder", "")
        if not download_dir or not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)

        self.btn_download_batch.configure(state="disabled", text="⏳ Đang tải video...")
        total = len(self.filtered_videos)
        self.download_progress.set(0)

        def _progress(completed, total_count, res):
            prog = completed / total_count
            self.download_progress.set(prog)
            self.lbl_download_status.configure(text=f"Đang tải: {completed}/{total_count} video ({int(prog*100)}%)")

        def _worker():
            cookie = self.config.get("douyin_cookie", "")
            results = DouyinExporter.batch_download(self.filtered_videos, download_dir, cookie=cookie, progress_callback=_progress)
            success_count = sum(1 for r in results if r.get("success"))
            self.after(0, lambda: self._on_download_complete(success_count, len(results)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_download_complete(self, success_count, total_count):
        self.btn_download_batch.configure(state="normal", text="⬇️ Bắt Đầu Tải Hàng Loạt Video (HD No-WM)")
        if success_count > 0:
            self.lbl_download_status.configure(text=f"✅ Đã tải thành công {success_count}/{total_count} video!")
            messagebox.showinfo("Hoàn tất", f"Đã tải thành công {success_count}/{total_count} video về thư mục:\n{self.config.get('download_folder')}")
        else:
            self.lbl_download_status.configure(text="⚠️ Cần Cookie Douyin để tải trực tiếp file về máy")
            messagebox.showinfo(
                "Thông báo tải video",
                "Máy chủ Douyin yêu cầu Cookie trình duyệt để tải trực tiếp file .mp4 về máy.\n\n"
                "👉 Giải pháp:\n"
                "1. Bạn có thể bấm '📊 Xuất File Excel' hoặc '📋 Sao Chép Link' để click mở xem trực tiếp trên trình duyệt (Cốc Cốc/Chrome) ngay lập tức.\n"
                "2. Hoặc vào tab '⚙️ Cài Đặt' dán Cookie tài khoản Douyin để mở khóa tải tự động 100%!"
            )

    # ================= TAB 4: SETTINGS =================
    def _create_settings_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="⚙️ Cài Đặt Kết Nối Cloud Server & Client", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")

        box = ctk.CTkFrame(frame)
        box.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        box.grid_columnconfigure(1, weight=1)

        # Cloud Server URL
        ctk.CTkLabel(box, text="Cloud Server URL:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=15, pady=12, sticky="w")
        url_frame = ctk.CTkFrame(box, fg_color="transparent")
        url_frame.grid(row=0, column=1, padx=15, pady=12, sticky="ew")
        url_frame.grid_columnconfigure(0, weight=1)

        self.set_server_url = ctk.CTkEntry(url_frame, placeholder_text="http://127.0.0.1:8000 hoặc https://api.yourdomain.com")
        self.set_server_url.insert(0, self.config.get("server_url", DEFAULT_SERVER_URL))
        self.set_server_url.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        btn_ping = ctk.CTkButton(url_frame, text="⚡ Ping Server", width=100, command=self._on_test_server_connection)
        btn_ping.grid(row=0, column=1)

        ctk.CTkLabel(box, text="Thư mục lưu video:").grid(row=1, column=0, padx=15, pady=12, sticky="w")
        dir_frame = ctk.CTkFrame(box, fg_color="transparent")
        dir_frame.grid(row=1, column=1, padx=15, pady=12, sticky="ew")
        dir_frame.grid_columnconfigure(0, weight=1)

        self.set_download_dir = ctk.CTkEntry(dir_frame)
        self.set_download_dir.insert(0, self.config.get("download_folder", ""))
        self.set_download_dir.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        btn_browse = ctk.CTkButton(dir_frame, text="📁 Chọn...", width=80, command=self._on_browse_folder)
        btn_browse.grid(row=0, column=1)

        ctk.CTkLabel(box, text="Douyin Cookie (tùy chọn):").grid(row=2, column=0, padx=15, pady=12, sticky="w")
        self.set_cookie = ctk.CTkEntry(box, placeholder_text="Dán Cookie Douyin nếu muốn đồng bộ lên Cloud...")
        self.set_cookie.insert(0, self.config.get("douyin_cookie", ""))
        self.set_cookie.grid(row=2, column=1, padx=15, pady=12, sticky="ew")

        btn_save = ctk.CTkButton(
            frame,
            text="💾 Lưu Cấu Hình & Đồng Bộ Cloud",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._on_save_settings
        )
        btn_save.grid(row=2, column=0, padx=20, pady=20, sticky="e")

        return frame

    def _on_test_server_connection(self):
        new_url = self.set_server_url.get().strip()
        self.cloud_client.set_server_url(new_url)
        res = self.cloud_client.ping()
        self._update_server_badge(res)
        if res.get("connected"):
            messagebox.showinfo("Kết nối thành công", f"Đã kết nối tới Cloud Server!\nĐộ trễ: {res.get('latency_ms')} ms\nPhiên bản API: {res.get('version')}")
        else:
            messagebox.showerror("Kết nối thất bại", f"Không thể kết nối:\n{res.get('error')}")

    def _on_browse_folder(self):
        f = filedialog.askdirectory(initialdir=self.config.get("download_folder"))
        if f:
            self.set_download_dir.delete(0, "end")
            self.set_download_dir.insert(0, f)

    def _on_save_settings(self):
        self.config["server_url"] = self.set_server_url.get().strip()
        self.config["douyin_cookie"] = self.set_cookie.get().strip()
        self.config["download_folder"] = self.set_download_dir.get().strip()
        self._save_config()

        self.cloud_client.set_server_url(self.config["server_url"])
        
        if self.config["douyin_cookie"]:
            self.cloud_client.update_cloud_settings({"douyin_cookie": self.config["douyin_cookie"]})

        self._check_server_health()
        messagebox.showinfo("Thành công", "Đã lưu cấu hình và đồng bộ Cloud Server thành công!")


def main():
    app = DouyinExtractorApp()
    app.mainloop()

if __name__ == "__main__":
    main()
