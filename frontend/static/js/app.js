class DouyinApp {
    constructor() {
        this.currentVideoId = null;
        this.currentJobId = null;
        this.currentDownloadJobId = null;
        this.selectedFile = null;
        this.pollInterval = null;
        this.downloadPollInterval = null;
        this.rawResults = [];
        this.filteredResults = [];
        this.selectedVideoIds = new Set();

        this.initElements();
        this.initEvents();
    }

    initElements() {
        // Tabs
        this.inputTabs = document.querySelectorAll(".input-tab");
        this.tabContents = {
            "upload": document.getElementById("tabUpload"),
            "url": document.getElementById("tabUrl"),
            "keyword": document.getElementById("tabKeyword")
        };

        // Inputs
        this.dropzone = document.getElementById("dropzone");
        this.fileInput = document.getElementById("videoFileInput");
        this.uploadDetails = document.getElementById("uploadDetails");
        this.videoPreview = document.getElementById("videoPreview");
        this.videoFileName = document.getElementById("videoFileName");
        this.videoFileSize = document.getElementById("videoFileSize");
        this.btnStartUploadPipeline = document.getElementById("btnStartUploadPipeline");

        this.douyinUrlInput = document.getElementById("douyinUrlInput");
        this.btnAnalyzeUrl = document.getElementById("btnAnalyzeUrl");

        this.manualKeywordInput = document.getElementById("manualKeywordInput");
        this.btnSearchManualKeyword = document.getElementById("btnSearchManualKeyword");

        // Progress
        this.progressBox = document.getElementById("progressBox");
        this.progressBarFill = document.getElementById("progressBarFill");
        this.progressStageText = document.getElementById("progressStageText");
        this.progressPercentText = document.getElementById("progressPercentText");
        this.progressSubText = document.getElementById("progressSubText");

        // Profile & Queries & Results
        this.profileGrid = document.getElementById("profileGrid");
        this.queriesGrid = document.getElementById("queriesGrid");
        this.resultsGrid = document.getElementById("resultsGrid");
        this.resultsCountText = document.getElementById("resultsCountText");

        // Selection & Batch Download
        this.btnSelectAll = document.getElementById("btnSelectAll");
        this.btnDeselectAll = document.getElementById("btnDeselectAll");
        this.btnDownloadSelected = document.getElementById("btnDownloadSelected");
        this.selectedCountBadge = document.getElementById("selectedCountBadge");

        // Download Modal
        this.downloadModal = document.getElementById("downloadModal");
        this.btnCloseDownloadModal = document.getElementById("btnCloseDownloadModal");
        this.btnCancelDownload = document.getElementById("btnCancelDownload");
        this.btnStartBatchDownloadAction = document.getElementById("btnStartBatchDownloadAction");
        this.btnRetryFailedDownloads = document.getElementById("btnRetryFailedDownloads");
        this.chkUploadDrive = document.getElementById("chkUploadDrive");
        this.txtDriveFolder = document.getElementById("txtDriveFolder");
        this.downloadProgressContainer = document.getElementById("downloadProgressContainer");
        this.dlJobStatusText = document.getElementById("dlJobStatusText");
        this.dlJobProgressText = document.getElementById("dlJobProgressText");
        this.dlProgressBarFill = document.getElementById("dlProgressBarFill");
        this.downloadItemsList = document.getElementById("downloadItemsList");

        // Filters
        this.rngMinScore = document.getElementById("rngMinScore");
        this.lblMinScore = document.getElementById("lblMinScore");
        this.selSortBy = document.getElementById("selSortBy");
        this.numMinLikes = document.getElementById("numMinLikes");
        this.btnApplyFilters = document.getElementById("btnApplyFilters");

        // History Drawer & Settings Modal
        this.historyDrawer = document.getElementById("historyDrawer");
        this.btnOpenHistory = document.getElementById("btnOpenHistory");
        this.btnCloseHistory = document.getElementById("btnCloseHistory");
        this.historyList = document.getElementById("historyList");

        this.settingsModal = document.getElementById("settingsModal");
        this.btnSettings = document.getElementById("btnSettings");
        this.btnCloseModal = document.getElementById("btnCloseModal");
        this.btnSaveConfig = document.getElementById("btnSaveConfig");
    }

    initEvents() {
        // Tab switching
        this.inputTabs.forEach(tab => {
            tab.addEventListener("click", () => {
                const targetTab = tab.dataset.tab;
                this.inputTabs.forEach(t => t.classList.remove("active"));
                tab.classList.add("active");
                Object.keys(this.tabContents).forEach(k => {
                    this.tabContents[k].style.display = (k === targetTab) ? "block" : "none";
                });
            });
        });

        // Dropzone
        this.dropzone.addEventListener("dragover", (e) => { e.preventDefault(); this.dropzone.classList.add("dragover"); });
        this.dropzone.addEventListener("dragleave", () => this.dropzone.classList.remove("dragover"));
        this.dropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            this.dropzone.classList.remove("dragover");
            if (e.dataTransfer.files.length > 0) this.handleFileSelected(e.dataTransfer.files[0]);
        });
        this.fileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) this.handleFileSelected(e.target.files[0]);
        });

        // Action Buttons
        this.btnStartUploadPipeline.addEventListener("click", () => this.startUploadPipeline());
        this.btnAnalyzeUrl.addEventListener("click", () => this.startUrlPipeline());
        this.btnSearchManualKeyword.addEventListener("click", () => this.startKeywordSearch());

        // Stepper
        document.querySelectorAll(".step-item").forEach(item => {
            item.addEventListener("click", () => this.goToStep(parseInt(item.dataset.step)));
        });

        // Filter slider
        this.rngMinScore.addEventListener("input", (e) => {
            this.lblMinScore.innerText = `${e.target.value}%`;
            this.applyLocalFilters();
        });
        this.selSortBy.addEventListener("change", () => this.applyLocalFilters());
        this.btnApplyFilters.addEventListener("click", () => this.applyLocalFilters());

        // Multi-select & Batch Download Events
        this.btnSelectAll.addEventListener("click", () => this.selectAllVideos());
        this.btnDeselectAll.addEventListener("click", () => this.deselectAllVideos());
        this.btnDownloadSelected.addEventListener("click", () => this.openDownloadModal());

        this.btnCloseDownloadModal.addEventListener("click", () => this.closeDownloadModal());
        this.btnCancelDownload.addEventListener("click", () => this.closeDownloadModal());
        this.btnStartBatchDownloadAction.addEventListener("click", () => this.startBatchDownload());
        this.btnRetryFailedDownloads.addEventListener("click", () => this.retryFailedDownloads());

        // Export & Copy
        document.getElementById("btnExportCSV").addEventListener("click", () => this.exportCSV());
        document.getElementById("btnCopyAll").addEventListener("click", () => this.copyAllUrls());

        // History Drawer
        this.btnOpenHistory.addEventListener("click", () => {
            this.historyDrawer.classList.add("open");
            this.loadHistory();
        });
        this.btnCloseHistory.addEventListener("click", () => this.historyDrawer.classList.remove("open"));

        // Settings Modal
        this.btnSettings.addEventListener("click", () => this.settingsModal.classList.add("open"));
        this.btnCloseModal.addEventListener("click", () => this.settingsModal.classList.remove("open"));
        this.btnSaveConfig.addEventListener("click", () => this.saveConfig());
    }

    handleFileSelected(file) {
        this.selectedFile = file;
        this.videoFileName.innerText = file.name;
        this.videoFileSize.innerText = (file.size / (1024 * 1024)).toFixed(2) + " MB";
        this.videoPreview.src = URL.createObjectURL(file);
        this.uploadDetails.style.display = "grid";
        this.dropzone.style.display = "none";
    }

    goToStep(stepNumber) {
        document.querySelectorAll(".step-item").forEach(item => {
            item.classList.toggle("active", parseInt(item.dataset.step) === stepNumber);
        });
        document.querySelectorAll(".step-section").forEach(sec => sec.classList.remove("active"));
        document.getElementById(`step${stepNumber}Section`).classList.add("active");
    }

    async startUploadPipeline() {
        if (!this.selectedFile) return;
        this.btnStartUploadPipeline.disabled = true;
        this.showProgress("Đang tải video lên máy chủ...", 5);

        const isDeep = document.getElementById("chkDeepSearchUpload").checked;
        const formData = new FormData();
        formData.append("file", this.selectedFile);
        formData.append("user_hint", document.getElementById("userHintInput").value.trim());
        formData.append("deep_search", isDeep ? "true" : "false");

        try {
            const resp = await fetch("/api/input/upload", { method: "POST", body: formData });
            const data = await resp.json();
            if (!data.success) throw new Error(data.detail || "Upload failed");

            this.currentVideoId = data.video_id;
            this.currentJobId = data.job_id;
            this.startJobPolling();
        } catch (err) {
            alert("Lỗi: " + err.message);
            this.btnStartUploadPipeline.disabled = false;
        }
    }

    async startUrlPipeline() {
        const url = this.douyinUrlInput.value.trim();
        if (!url) return alert("Vui lòng dán link Douyin hoặc TikTok.");

        this.btnAnalyzeUrl.disabled = true;
        this.showProgress("Đang phân tích link Douyin/TikTok...", 10);

        try {
            const resp = await fetch("/api/input/url", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ url: url })
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.detail || "Parse link failed");

            this.currentVideoId = data.video_id;
            this.currentJobId = data.job_id;
            this.startJobPolling();
        } catch (err) {
            alert("Lỗi: " + err.message);
            this.btnAnalyzeUrl.disabled = false;
        }
    }

    async startKeywordSearch() {
        const kw = this.manualKeywordInput.value.trim();
        if (!kw) return alert("Vui lòng nhập từ khóa tiếng Trung.");

        this.btnSearchManualKeyword.disabled = true;
        this.showProgress(`Đang quét trực tiếp Douyin theo từ khóa '${kw}'...`, 60);

        try {
            const resp = await fetch("/api/input/keyword", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ keyword: kw, limit: 30 })
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.detail || "Search failed");

            this.currentVideoId = data.video_id;
            this.rawResults = data.results || [];
            this.applyLocalFilters();
            this.goToStep(4);
            this.progressBox.style.display = "none";
            this.btnSearchManualKeyword.disabled = false;
        } catch (err) {
            alert("Lỗi: " + err.message);
            this.btnSearchManualKeyword.disabled = false;
        }
    }

    showProgress(stageText, percent) {
        this.progressBox.style.display = "block";
        this.progressStageText.innerText = stageText;
        this.progressPercentText.innerText = percent + "%";
        this.progressBarFill.style.width = percent + "%";
    }

    startJobPolling() {
        if (this.pollInterval) clearInterval(this.pollInterval);

        const stageDescriptions = {
            "queued": "Đang xếp hàng chờ xử lý...",
            "processing": "FFmpeg đang trích xuất khung hình và âm thanh...",
            "analyzing": "AI Multimodal đang phân tích bối cảnh, ASR & OCR...",
            "generating_queries": "Đang tạo bộ truy vấn tiếng Trung phân tầng...",
            "searching": "Đang chạy 4-Phase Waterfall Search & Lọc video chết/private...",
            "ranking": "Đang tính điểm tương đồng 7 chiều & tối ưu chất lượng...",
            "completed": "Hoàn tất toàn bộ pipeline!",
            "failed": "Có lỗi xảy ra trong quá trình xử lý"
        };

        this.pollInterval = setInterval(async () => {
            try {
                const resp = await fetch(`/api/jobs/${this.currentJobId}`);
                const job = await resp.json();

                this.showProgress(stageDescriptions[job.stage] || job.stage, job.progress_percent);

                if (job.status === "completed") {
                    clearInterval(this.pollInterval);
                    await this.loadAllPipelineData();
                } else if (job.status === "failed") {
                    clearInterval(this.pollInterval);
                    alert("Pipeline thất bại: " + (job.error_message || "Không rõ nguyên nhân"));
                    this.btnStartUploadPipeline.disabled = false;
                    this.btnAnalyzeUrl.disabled = false;
                }
            } catch (e) {
                console.error("Polling error:", e);
            }
        }, 1500);
    }

    async loadAllPipelineData() {
        // Load Profile
        const respProf = await fetch(`/api/videos/${this.currentVideoId}/analysis`);
        if (respProf.ok) {
            const p = await respProf.json();
            this.renderProfile(p);
        }

        // Load Queries
        const respQ = await fetch(`/api/videos/${this.currentVideoId}/queries`);
        if (respQ.ok) {
            const qData = await respQ.json();
            this.renderQueries(qData.queries || []);
        }

        // Load Results
        const respRes = await fetch(`/api/videos/${this.currentVideoId}/results`);
        if (respRes.ok) {
            const rData = await respRes.json();
            this.rawResults = rData.results || [];
            this.applyLocalFilters();
        }

        this.goToStep(4);
    }

    renderProfile(p) {
        this.profileGrid.innerHTML = `
            <div class="profile-card">
                <h3><i class="fa-solid fa-list-check"></i> Tóm Tắt & Chủ Đề</h3>
                <p><strong>Chủ đề:</strong> ${p.main_topic || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Tóm tắt:</strong> ${p.summary || "N/A"}</p>
                <div class="tag-list">
                    ${(p.secondary_topics || []).map(t => `<span class="tag">${t}</span>`).join("")}
                </div>
            </div>
            <div class="profile-card">
                <h3><i class="fa-solid fa-person-walking"></i> Nhân Vật & Hành Động</h3>
                <p><strong>Đối tượng/Nhân vật:</strong> ${(p.people || []).join(", ") || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Hành động:</strong> ${(p.actions || []).join(", ") || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Bối cảnh:</strong> ${(p.locations || []).join(", ") || "N/A"}</p>
            </div>
            <div class="profile-card">
                <h3><i class="fa-solid fa-camera"></i> Phong Cách & Cảm Xúc</h3>
                <p><strong>Phong cách hình ảnh:</strong> ${(p.visual_style || []).join(", ") || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Góc quay:</strong> ${(p.camera_style || []).join(", ") || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Tone cảm xúc:</strong> ${(p.emotional_tone || []).join(", ") || "N/A"}</p>
            </div>
            <div class="profile-card">
                <h3><i class="fa-solid fa-file-lines"></i> Phụ Đề & Chữ Trên Màn Hình</h3>
                <p><strong>Phụ đề (ASR):</strong> ${p.transcript || "Không có lời thoại"}</p>
                <p style="margin-top:8px;"><strong>Chữ OCR:</strong> ${(p.ocr_text || []).join(", ") || "Không phát hiện"}</p>
            </div>
        `;
    }

    renderQueries(queries) {
        this.queriesGrid.innerHTML = queries.map(q => `
            <div class="query-card">
                <div class="query-header">
                    <span class="query-category">${q.category}</span>
                    <span style="font-size:12px; color:#10b981;">Score: ${q.score}</span>
                </div>
                <div class="query-text">${q.query}</div>
                <div style="font-size:12px; color:#94a3b8;">${q.reason || ''}</div>
            </div>
        `).join("");
    }

    applyLocalFilters() {
        const minScore = parseFloat(this.rngMinScore.value);
        const minLikes = parseInt(this.numMinLikes.value) || 0;
        const sortBy = this.selSortBy.value;

        let list = [...this.rawResults].filter(r => {
            const score = (r.final_score || 0.8) * 100;
            if (score < minScore) return false;
            if (minLikes > 0 && (r.like_count || 0) < minLikes) return false;
            return true;
        });

        // Sorting
        if (sortBy === "likes") list.sort((a, b) => (b.like_count || 0) - (a.like_count || 0));
        else if (sortBy === "comments") list.sort((a, b) => (b.comment_count || 0) - (a.comment_count || 0));
        else if (sortBy === "shares") list.sort((a, b) => (b.share_count || 0) - (a.share_count || 0));
        else if (sortBy === "newest") list.sort((a, b) => (b.publish_time || "").localeCompare(a.publish_time || ""));
        else list.sort((a, b) => (b.final_score || 0) - (a.final_score || 0));

        this.filteredResults = list;
        this.resultsCountText.innerText = `Tìm thấy ${list.length} video Douyin đang hoạt động (Đã lọc từ ${this.rawResults.length} candidates)`;
        this.renderResults(list);
        this.updateSelectionCount();
    }

    renderResults(results) {
        if (!results.length) {
            this.resultsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding: 40px; color:#94a3b8;">Không có video nào đạt tiêu chí lọc này. Hãy hạ thấp mức điểm tương đồng hoặc số like.</div>`;
            return;
        }

        const placeholderSvg = "/api/v1/placeholder/cover.svg";

        this.resultsGrid.innerHTML = results.map(r => {
            const scorePct = Math.round((r.final_score || 0.8) * 100);
            let tierClass = "good";
            if (scorePct >= 90) tierClass = "vhigh";
            else if (scorePct >= 80) tierClass = "high";
            else if (scorePct < 60) tierClass = "low";

            const vid = r.remote_video_id || r.video_id || r.url;
            const isChecked = this.selectedVideoIds.has(vid);

            // Safe cover URL with proxy fallback on error
            let coverSrc = r.cover_url;
            if (!coverSrc || !coverSrc.startsWith("http")) {
                coverSrc = placeholderSvg;
            }

            return `
            <div class="result-card ${isChecked ? 'selected' : ''}" data-video-id="${vid}">
                <div style="position:relative; width:100%; height:200px; overflow:hidden; background:#0f172a; border-radius:8px 8px 0 0;">
                    <input type="checkbox" class="video-select-chk" data-video-id="${vid}" ${isChecked ? 'checked' : ''} style="position:absolute; top:12px; left:12px; width:22px; height:22px; z-index:10; cursor:pointer; accent-color:#38bdf8;">
                    <img src="${coverSrc}" 
                         class="result-cover" 
                         loading="lazy" 
                         referrerpolicy="no-referrer" 
                         style="width:100%; height:100%; object-fit:cover;" 
                         onerror="if (!this.dataset.triedProxy) { this.dataset.triedProxy = 'true'; this.src = '/api/v1/proxy/thumbnail?url=' + encodeURIComponent('${coverSrc}'); } else { this.src = '${placeholderSvg}'; }">
                </div>
                <div class="result-body">
                    <div class="result-title">${r.title || 'Douyin Video'}</div>
                    <div class="result-stats">
                        <span><i class="fa-solid fa-user"></i> ${r.author || 'Creator'}</span>
                        <span><i class="fa-solid fa-heart" style="color:#ef4444;"></i> ${(r.like_count || 0).toLocaleString()}</span>
                    </div>
                    <div class="result-scores">
                        <span>Độ khớp: <strong class="score-badge ${tierClass}">${scorePct}%</strong></span>
                        <span>Từ khóa: ${r.search_query || 'General'}</span>
                    </div>
                    <div style="display:flex; gap:8px; margin-top:auto;">
                        <a href="${r.url}" target="_blank" class="btn btn-primary result-btn" referrerpolicy="no-referrer">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i> Mở Douyin
                        </a>
                        <button class="btn btn-outline" onclick="navigator.clipboard.writeText('${r.url}'); alert('Đã sao chép link!');" title="Sao chép link">
                            <i class="fa-solid fa-copy"></i>
                        </button>
                    </div>
                </div>
            </div>
            `;
        }).join("");

        // Attach checkbox change events
        document.querySelectorAll(".video-select-chk").forEach(chk => {
            chk.addEventListener("change", (e) => {
                const vid = e.target.dataset.videoId;
                if (e.target.checked) this.selectedVideoIds.add(vid);
                else this.selectedVideoIds.delete(vid);

                const card = document.querySelector(`.result-card[data-video-id="${vid}"]`);
                if (card) card.classList.toggle("selected", e.target.checked);
                this.updateSelectionCount();
            });
        });
    }

    selectAllVideos() {
        this.filteredResults.forEach(r => {
            const vid = r.remote_video_id || r.video_id || r.url;
            this.selectedVideoIds.add(vid);
        });
        document.querySelectorAll(".video-select-chk").forEach(c => c.checked = true);
        document.querySelectorAll(".result-card").forEach(card => card.classList.add("selected"));
        this.updateSelectionCount();
    }

    deselectAllVideos() {
        this.selectedVideoIds.clear();
        document.querySelectorAll(".video-select-chk").forEach(c => c.checked = false);
        document.querySelectorAll(".result-card").forEach(card => card.classList.remove("selected"));
        this.updateSelectionCount();
    }

    updateSelectionCount() {
        const count = this.selectedVideoIds.size;
        this.selectedCountBadge.innerText = count;
        this.btnDownloadSelected.disabled = (count === 0);
    }

    openDownloadModal() {
        if (this.selectedVideoIds.size === 0) {
            return alert("Vui lòng tích chọn ít nhất 1 video để tải.");
        }
        this.downloadModal.classList.add("open");
        this.downloadProgressContainer.style.display = "none";
        this.btnStartBatchDownloadAction.disabled = false;
        this.btnStartBatchDownloadAction.innerHTML = `<i class="fa-solid fa-play"></i> Bắt Đầu Tải (${this.selectedVideoIds.size} video)`;
        this.btnRetryFailedDownloads.style.display = "none";
    }

    closeDownloadModal() {
        this.downloadModal.classList.remove("open");
        if (this.downloadPollInterval) clearInterval(this.downloadPollInterval);
    }

    async startBatchDownload() {
        const selectedList = this.filteredResults.filter(r => {
            const vid = r.remote_video_id || r.video_id || r.url;
            return this.selectedVideoIds.has(vid);
        });

        if (!selectedList.length) return alert("Chưa chọn video nào.");

        this.btnStartBatchDownloadAction.disabled = true;
        this.downloadProgressContainer.style.display = "block";
        this.dlJobStatusText.innerText = "Đang khởi tạo hàng đợi trên Render Cloud...";
        this.dlJobProgressText.innerText = "0%";
        this.dlProgressBarFill.style.width = "0%";
        this.downloadItemsList.innerHTML = "";

        const payload = {
            videos: selectedList.map(r => ({
                video_id: r.remote_video_id || r.video_id || "",
                url: r.url || "",
                title: r.title || "",
                author: r.author || "",
                cover_url: r.cover_url || "",
                availability_status: "ACTIVE"
            })),
            upload_to_drive: this.chkUploadDrive.checked,
            drive_folder: this.txtDriveFolder.value.trim() || "Douyin Downloader"
        };

        try {
            const resp = await fetch("/api/v1/download", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await resp.json();
            if (!resp.ok || !data.success) throw new Error(data.detail?.error?.message || data.detail || "Download queue failed");

            this.currentDownloadJobId = data.job_id;
            this.pollDownloadJobProgress();
        } catch (err) {
            alert("Lỗi tạo tác vụ tải: " + err.message);
            this.btnStartBatchDownloadAction.disabled = false;
        }
    }

    pollDownloadJobProgress() {
        if (this.downloadPollInterval) clearInterval(this.downloadPollInterval);

        const statusLabels = {
            "pending": "<span style='color:#94a3b8;'>Đang xếp hàng</span>",
            "fetching_source": "<span style='color:#38bdf8;'><i class='fa-solid fa-spinner fa-spin'></i> Đang lấy nguồn video HD</span>",
            "downloading": "<span style='color:#f59e0b;'><i class='fa-solid fa-spinner fa-spin'></i> Đang tải video HD</span>",
            "uploading_drive": "<span style='color:#818cf8;'><i class='fa-solid fa-cloud-arrow-up fa-bounce'></i> Đang upload Drive</span>",
            "completed": "<span style='color:#10b981;'><i class='fa-solid fa-circle-check'></i> Hoàn thành</span>",
            "failed": "<span style='color:#ef4444;'><i class='fa-solid fa-circle-xmark'></i> Lỗi</span>"
        };

        this.downloadPollInterval = setInterval(async () => {
            try {
                const resp = await fetch(`/api/v1/download/jobs/${this.currentDownloadJobId}`);
                if (!resp.ok) return;
                const job = await resp.json();

                const total = job.total_items || 1;
                const completed = job.completed_items || 0;
                const failed = job.failed_items || 0;
                const pct = job.progress_percent || 0;

                this.dlProgressBarFill.style.width = `${pct}%`;
                this.dlJobProgressText.innerText = `${pct}%`;
                this.dlJobStatusText.innerText = `Đang xử lý: ${completed}/${total} video hoàn thành (Lỗi: ${failed})`;

                // Render items
                this.downloadItemsList.innerHTML = (job.items || []).map((it, idx) => `
                    <div style="background:#1e293b; padding:10px; border-radius:6px; font-size:13px; display:flex; justify-content:space-between; align-items:center;">
                        <div style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:65%;">
                            <strong>[${idx + 1}]</strong> ${it.title}
                            <div style="font-size:11px; color:#64748b;">${it.filename || it.video_id} ${it.quality_label ? `(${it.quality_label})` : ''}</div>
                        </div>
                        <div style="text-align:right;">
                            <div>${statusLabels[it.status] || it.status}</div>
                            ${it.drive_link ? `<a href="${it.drive_link}" target="_blank" style="color:#38bdf8; font-size:11px;"><i class="fa-solid fa-arrow-up-right-from-square"></i> Mở Drive</a>` : ''}
                            ${it.error_message ? `<div style="color:#ef4444; font-size:11px;" title="${it.error_message}">Lỗi: ${it.error_message.slice(0, 25)}...</div>` : ''}
                        </div>
                    </div>
                `).join("");

                if (job.status === "completed" || job.status === "completed_with_errors" || job.status === "failed") {
                    clearInterval(this.downloadPollInterval);
                    if (failed > 0) {
                        this.btnRetryFailedDownloads.style.display = "inline-block";
                    }
                    this.btnStartBatchDownloadAction.disabled = false;
                    this.btnStartBatchDownloadAction.innerHTML = `<i class="fa-solid fa-rotate-left"></i> Tải Lại`;
                }
            } catch (e) {
                console.error("Poll download error:", e);
            }
        }, 1000);
    }

    async retryFailedDownloads() {
        if (!this.currentDownloadJobId) return;
        this.btnRetryFailedDownloads.disabled = true;
        try {
            await fetch(`/api/v1/download/jobs/${this.currentDownloadJobId}/retry`, { method: "POST" });
            this.pollDownloadJobProgress();
        } catch (e) {
            alert("Lỗi khi gửi yêu cầu thử lại: " + e.message);
        } finally {
            this.btnRetryFailedDownloads.disabled = false;
        }
    }

    exportCSV() {
        if (!this.filteredResults.length) return alert("Không có dữ liệu để xuất.");
        let csv = "Rank,Title,Author,Likes,Score,Search_Query,Douyin_URL\n";
        this.filteredResults.forEach((r, idx) => {
            const cleanTitle = (r.title || "").replace(/[\r\n,]/g, " ");
            csv += `${idx + 1},${cleanTitle},${r.author},${r.like_count},${Math.round((r.final_score || 0.8) * 100)}%,${r.search_query},${r.url}\n`;
        });
        this.downloadFile(csv, `douyin_results_${this.currentVideoId || 'export'}.csv`, "text/csv;charset=utf-8;");
    }

    copyAllUrls() {
        if (!this.filteredResults.length) return alert("Không có link để sao chép.");
        const urls = this.filteredResults.map(r => r.url).join("\n");
        navigator.clipboard.writeText(urls);
        alert(`Đã sao chép ${this.filteredResults.length} link Douyin vào Clipboard!`);
    }

    downloadFile(content, fileName, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    async loadHistory() {
        this.historyList.innerHTML = `
            <div style="background:#0f172a; padding:12px; border-radius:8px; margin-bottom:10px;">
                <div style="font-weight:bold; color:#38bdf8;">Phiên tìm kiếm gần nhất</div>
                <div style="font-size:12px; color:#94a3b8; margin-top:4px;">Video: ${this.currentVideoId || 'Chưa có'}</div>
                <div style="font-size:12px; color:#10b981; margin-top:2px;">Kết quả: ${this.rawResults.length} video</div>
            </div>
        `;
    }

    saveConfig() {
        this.settingsModal.classList.remove("open");
        alert("Đã lưu cấu hình!");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.app = new DouyinApp();
});
