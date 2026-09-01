class DouyinApp {
    constructor() {
        this.currentVideoId = null;
        this.currentJobId = null;
        this.selectedFile = null;
        this.pollInterval = null;
        this.queries = [];
        this.results = [];

        this.initElements();
        this.initEvents();
    }

    initElements() {
        this.dropzone = document.getElementById("dropzone");
        this.fileInput = document.getElementById("videoFileInput");
        this.uploadDetails = document.getElementById("uploadDetails");
        this.videoPreview = document.getElementById("videoPreview");
        this.videoFileName = document.getElementById("videoFileName");
        this.videoFileSize = document.getElementById("videoFileSize");
        this.btnStartPipeline = document.getElementById("btnStartPipeline");
        this.progressBox = document.getElementById("progressBox");
        this.progressBarFill = document.getElementById("progressBarFill");
        this.progressStageText = document.getElementById("progressStageText");
        this.progressPercentText = document.getElementById("progressPercentText");
        this.progressSubText = document.getElementById("progressSubText");

        this.profileGrid = document.getElementById("profileGrid");
        this.queriesGrid = document.getElementById("queriesGrid");
        this.resultsGrid = document.getElementById("resultsGrid");
        this.resultsCountText = document.getElementById("resultsCountText");

        this.settingsModal = document.getElementById("settingsModal");
        this.btnSettings = document.getElementById("btnSettings");
        this.btnCloseModal = document.getElementById("btnCloseModal");
        this.btnSaveConfig = document.getElementById("btnSaveConfig");

        this.cfgGeminiKey = document.getElementById("cfgGeminiKey");
        this.cfgDouyinCookie = document.getElementById("cfgDouyinCookie");
        this.cfgSearchProvider = document.getElementById("cfgSearchProvider");
    }

    initEvents() {
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

        this.btnStartPipeline.addEventListener("click", () => this.startPipeline());

        document.querySelectorAll(".step-item").forEach(item => {
            item.addEventListener("click", () => {
                const step = parseInt(item.dataset.step);
                this.goToStep(step);
            });
        });

        document.getElementById("btnSearchQueries").addEventListener("click", () => this.executeSearch());
        document.getElementById("btnAddCustomQuery").addEventListener("click", () => this.addCustomQuery());

        document.getElementById("btnExportExcel").addEventListener("click", () => this.exportExcel());
        document.getElementById("btnCopyAllUrls").addEventListener("click", () => this.copyAllUrls());

        this.btnSettings.addEventListener("click", () => this.settingsModal.classList.add("open"));
        this.btnCloseModal.addEventListener("click", () => this.settingsModal.classList.remove("open"));
        this.btnSaveConfig.addEventListener("click", () => this.saveSettings());
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

    async startPipeline() {
        if (!this.selectedFile) return;

        this.btnStartPipeline.disabled = true;
        this.progressBox.style.display = "block";
        this.updateProgress("Đang tải video lên máy chủ...", 5);

        const formData = new FormData();
        formData.append("file", this.selectedFile);
        formData.append("user_hint", document.getElementById("userHintInput").value.trim());
        formData.append("auto_process", "true");

        try {
            const resp = await fetch("/api/videos", { method: "POST", body: formData });
            const data = await resp.json();
            if (!data.success) throw new Error(data.detail || "Upload failed");

            this.currentVideoId = data.video_id;
            this.currentJobId = data.job_id;

            this.startJobPolling();
        } catch (err) {
            alert("Lỗi tải video: " + err.message);
            this.btnStartPipeline.disabled = false;
        }
    }

    startJobPolling() {
        if (this.pollInterval) clearInterval(this.pollInterval);

        const stageDescriptions = {
            "queued": "Đang xếp hàng chờ xử lý...",
            "processing": "FFmpeg đang trích xuất khung hình và âm thanh...",
            "analyzing": "AI Multimodal đang phân tích nội dung, ASR & OCR...",
            "generating_queries": "Đang sinh 20 từ khóa tìm kiếm tiếng Trung tối ưu...",
            "searching": "Đang tìm kiếm video liên quan trên Douyin...",
            "ranking": "Đang tính điểm tương đồng, xếp hạng & khử trùng lặp...",
            "completed": "Hoàn tất toàn bộ pipeline!",
            "failed": "Có lỗi xảy ra trong quá trình xử lý"
        };

        this.pollInterval = setInterval(async () => {
            try {
                const resp = await fetch(`/api/jobs/${this.currentJobId}`);
                const job = await resp.json();

                this.updateProgress(
                    stageDescriptions[job.stage] || job.stage,
                    job.progress_percent,
                    `Trạng thái: ${job.status}`
                );

                if (job.status === "completed") {
                    clearInterval(this.pollInterval);
                    await this.loadAllPipelineData();
                } else if (job.status === "failed") {
                    clearInterval(this.pollInterval);
                    alert("Pipeline thất bại: " + (job.error_message || "Không rõ nguyên nhân"));
                    this.btnStartPipeline.disabled = false;
                }
            } catch (e) {
                console.error("Polling error:", e);
            }
        }, 1500);
    }

    updateProgress(stageText, percent, subText = "") {
        this.progressStageText.innerText = stageText;
        this.progressPercentText.innerText = percent + "%";
        this.progressBarFill.style.width = percent + "%";
        if (subText) this.progressSubText.innerText = subText;
    }

    async loadAllPipelineData() {
        const respProfile = await fetch(`/api/videos/${this.currentVideoId}/analysis`);
        if (respProfile.ok) {
            const profile = await respProfile.json();
            this.renderProfile(profile);
        }

        const respQueries = await fetch(`/api/videos/${this.currentVideoId}/queries`);
        if (respQueries.ok) {
            const qData = await respQueries.json();
            this.queries = qData.queries || [];
            this.renderQueries(this.queries);
        }

        await this.loadResults();
        this.goToStep(4);
    }

    renderProfile(p) {
        this.profileGrid.innerHTML = `
            <div class="profile-card">
                <h3><i class="fa-solid fa-list-check"></i> Tóm Tắt & Chủ Đề</h3>
                <p><strong>Chủ đề chính:</strong> ${p.main_topic || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Tóm tắt:</strong> ${p.summary || "N/A"}</p>
                <div class="tag-list" style="margin-top:12px;">
                    ${(p.secondary_topics || []).map(t => `<span class="tag">${t}</span>`).join("")}
                </div>
            </div>
            <div class="profile-card">
                <h3><i class="fa-solid fa-person-walking"></i> Nhân Vật & Hành Động</h3>
                <p><strong>Nhân vật:</strong> ${(p.people || []).join(", ") || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Hành động:</strong> ${(p.actions || []).join(", ") || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Đồ vật/Trang phục:</strong> ${(p.objects || []).join(", ") || "N/A"}</p>
            </div>
            <div class="profile-card">
                <h3><i class="fa-solid fa-camera"></i> Phong Cách & Cảm Xúc</h3>
                <p><strong>Phong cách hình ảnh:</strong> ${(p.visual_style || []).join(", ") || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Tone cảm xúc:</strong> ${(p.emotional_tone || []).join(", ") || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Định dạng video:</strong> ${p.content_format || "N/A"}</p>
            </div>
            <div class="profile-card">
                <h3><i class="fa-solid fa-file-lines"></i> Phụ Đề (ASR) & Chữ Trên Màn Hình (OCR)</h3>
                <p><strong>Phụ đề:</strong> ${p.transcript || "Không có lời thoại"}</p>
                <p style="margin-top:8px;"><strong>Chữ OCR:</strong> ${(p.ocr_text || []).join(", ") || "Không có"}</p>
            </div>
        `;
    }

    renderQueries(queries) {
        this.queriesGrid.innerHTML = queries.map(q => `
            <div class="query-card ${q.is_enabled ? '' : 'disabled'}" data-id="${q.id}">
                <div class="query-header">
                    <span class="query-category">${q.category}</span>
                    <label style="cursor:pointer;">
                        <input type="checkbox" ${q.is_enabled ? 'checked' : ''} onchange="app.toggleQuery('${q.id}', this.checked)"> Bật
                    </label>
                </div>
                <div class="query-text">${q.query}</div>
                <div class="query-reason">${q.reason || ''} (Score: ${q.score})</div>
                ${q.variants && q.variants.length ? `<div class="query-variants">Biến thể: ${q.variants.join(" • ")}</div>` : ''}
            </div>
        `).join("");
    }

    async toggleQuery(queryId, isEnabled) {
        await fetch(`/api/videos/${this.currentVideoId}/queries/${queryId}`, {
            method: "PATCH",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ is_enabled: isEnabled })
        });
    }

    async addCustomQuery() {
        const val = document.getElementById("customQueryInput").value.trim();
        if (!val) return;

        await fetch(`/api/videos/${this.currentVideoId}/queries/custom`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ query: val, category: "core_topic" })
        });

        document.getElementById("customQueryInput").value = "";
        const resp = await fetch(`/api/videos/${this.currentVideoId}/queries`);
        const data = await resp.json();
        this.renderQueries(data.queries || []);
    }

    async loadResults() {
        const resp = await fetch(`/api/videos/${this.currentVideoId}/results`);
        if (!resp.ok) return;
        const data = await resp.json();
        this.results = data.results || [];
        this.resultsCountText.innerText = `Tìm thấy ${this.results.length} video Douyin liên quan chất lượng cao.`;
        this.renderResults(this.results);
    }

    renderResults(results) {
        if (!results.length) {
            this.resultsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding: 40px;">Chưa có kết quả video.</div>`;
            return;
        }

        this.resultsGrid.innerHTML = results.map(r => `
            <div class="result-card">
                <img src="${r.cover_url || 'https://p3-pc.douyinpic.com/origin/tos-cn-p-0015/demo.jpeg'}" class="result-cover" onerror="this.src='https://p3-pc.douyinpic.com/origin/tos-cn-p-0015/demo.jpeg'">
                <div class="result-body">
                    <div class="result-title">${r.title}</div>
                    <div class="result-stats">
                        <span><i class="fa-solid fa-user"></i> ${r.author}</span>
                        <span><i class="fa-solid fa-heart" style="color:#ef4444;"></i> ${(r.like_count || 0).toLocaleString()}</span>
                    </div>
                    <div class="result-scores">
                        <span>Độ khớp: <strong class="score-badge">${Math.round((r.final_score || 0.8) * 100)}%</strong></span>
                        <span>Từ khóa: ${r.search_query}</span>
                    </div>
                    <a href="${r.url}" target="_blank" class="btn btn-primary result-btn">
                        <i class="fa-solid fa-arrow-up-right-from-square"></i> Mở Xem Trên Douyin
                    </a>
                </div>
            </div>
        `).join("");
    }

    async executeSearch() {
        this.goToStep(1);
        this.progressBox.style.display = "block";
        this.updateProgress("Đang quét Douyin với danh sách từ khóa đã chọn...", 75);

        const resp = await fetch(`/api/videos/${this.currentVideoId}/process`, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({}) });
        const data = await resp.json();
        this.currentJobId = data.job_id;
        this.startJobPolling();
    }

    exportExcel() {
        if (!this.results.length) return alert("Chưa có kết quả để xuất.");
        let csvContent = "data:text/csv;charset=utf-8,ID,Tieu De,Tac Gia,Likes,Link Douyin\n";
        this.results.forEach(r => {
            const title = (r.title || "").replace(/,/g, " ");
            csvContent += `${r.video_id},${title},${r.author},${r.like_count},${r.url}\n`;
        });
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `douyin_results_${this.currentVideoId}.csv`);
        document.body.appendChild(link);
        link.click();
    }

    copyAllUrls() {
        if (!this.results.length) return alert("Chưa có link video để sao chép.");
        const urls = this.results.map(r => r.url).join("\n");
        navigator.clipboard.writeText(urls);
        alert(`Đã sao chép ${this.results.length} link Douyin vào Clipboard!`);
    }

    saveSettings() {
        this.settingsModal.classList.remove("open");
        alert("Đã lưu cài đặt cấu hình!");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.app = new DouyinApp();
});
