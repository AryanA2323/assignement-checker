/**
 * Assignment Checker - Minimal, Clean Frontend Logic
 */

document.addEventListener("DOMContentLoaded", () => {
    // State
    const state = {
        masterMode: "upload", // 'upload' or 'paste'
        masterFile: null,
        studentFiles: [],
        currentBatchResults: null
    };

    // Master Solution
    const btnModeUpload = document.getElementById("btnModeUpload");
    const btnModePaste = document.getElementById("btnModePaste");
    const masterFileSection = document.getElementById("masterFileSection");
    const masterTextSection = document.getElementById("masterTextSection");
    const masterDropZone = document.getElementById("masterDropZone");
    const masterFileInput = document.getElementById("masterFileInput");
    const masterFileInfo = document.getElementById("masterFileInfo");
    const masterTextInput = document.getElementById("masterTextInput");

    // Student Submissions
    const studentsDropZone = document.getElementById("studentsDropZone");
    const studentsFileInput = document.getElementById("studentsFileInput");
    const studentsFilesList = document.getElementById("studentsFilesList");
    const filesContainer = document.getElementById("filesContainer");
    const filesCount = document.getElementById("filesCount");
    const btnClearFiles = document.getElementById("btnClearFiles");

    // Action & Controls
    const strictnessSelect = document.getElementById("strictnessSelect");
    const btnEvaluate = document.getElementById("btnEvaluate");
    const loadingCard = document.getElementById("loadingCard");

    // Results
    const resultsSection = document.getElementById("resultsSection");
    const metricTotal = document.getElementById("metricTotal");
    const metricAverage = document.getElementById("metricAverage");
    const metricConfidence = document.getElementById("metricConfidence");
    const metricReviewCount = document.getElementById("metricReviewCount");
    const resultsTableBody = document.getElementById("resultsTableBody");
    const btnExportCSV = document.getElementById("btnExportCSV");

    // Modals
    const detailModal = document.getElementById("detailModal");
    const btnCloseModal = document.getElementById("btnCloseModal");
    const modalStudentName = document.getElementById("modalStudentName");
    const modalStudentSub = document.getElementById("modalStudentSub");
    const modalBody = document.getElementById("modalBody");

    const settingsModal = document.getElementById("settingsModal");
    const btnOpenSettings = document.getElementById("btnOpenSettings");
    const btnCloseSettings = document.getElementById("btnCloseSettings");
    const btnSaveSettings = document.getElementById("btnSaveSettings");
    const settingApiKey = document.getElementById("settingApiKey");
    const settingModel = document.getElementById("settingModel");
    const settingThreshold = document.getElementById("settingThreshold");
    const settingsStatus = document.getElementById("settingsStatus");

    // 1. Initial Load
    checkApiStatus();
    setupMasterModeSwitch();
    setupDropZones();
    setupModals();

    async function checkApiStatus() {
        try {
            const res = await fetch("/api/status");
            const data = await res.json();
            if (data.has_api_key) {
                settingModel.value = data.model_name || "gemini-3.5-flash-lite";
                settingThreshold.value = data.review_threshold || 70;
            }
        } catch (err) {
            console.error("Status error:", err);
        }
    }

    // 2. Master Solution Mode Toggle
    function setupMasterModeSwitch() {
        btnModeUpload.addEventListener("click", () => {
            state.masterMode = "upload";
            btnModeUpload.classList.add("active");
            btnModePaste.classList.remove("active");
            masterFileSection.style.display = "block";
            masterTextSection.style.display = "none";
        });

        btnModePaste.addEventListener("click", () => {
            state.masterMode = "paste";
            btnModePaste.classList.add("active");
            btnModeUpload.classList.remove("active");
            masterFileSection.style.display = "none";
            masterTextSection.style.display = "block";
        });
    }

    // 3. Setup Drag & Drop Handlers
    function setupDropZones() {
        // Master File
        masterDropZone.addEventListener("click", () => masterFileInput.click());
        masterDropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            masterDropZone.classList.add("dragover");
        });
        masterDropZone.addEventListener("dragleave", () => masterDropZone.classList.remove("dragover"));
        masterDropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            masterDropZone.classList.remove("dragover");
            if (e.dataTransfer.files.length > 0) {
                setMasterFile(e.dataTransfer.files[0]);
            }
        });
        masterFileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                setMasterFile(e.target.files[0]);
            }
        });

        // Student Files
        studentsDropZone.addEventListener("click", () => studentsFileInput.click());
        studentsDropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            studentsDropZone.classList.add("dragover");
        });
        studentsDropZone.addEventListener("dragleave", () => studentsDropZone.classList.remove("dragover"));
        studentsDropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            studentsDropZone.classList.remove("dragover");
            addStudentFiles(e.dataTransfer.files);
        });
        studentsFileInput.addEventListener("change", (e) => {
            addStudentFiles(e.target.files);
        });

        btnClearFiles.addEventListener("click", () => {
            state.studentFiles = [];
            renderStudentFilesList();
        });
    }

    function setMasterFile(file) {
        state.masterFile = file;
        masterFileInfo.style.display = "inline-flex";
        masterFileInfo.innerHTML = `
            <span>📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)</span>
            <button type="button" style="background:none;border:none;color:#ef4444;cursor:pointer;margin-left:6px;font-weight:bold">&times;</button>
        `;
        masterFileInfo.querySelector("button").onclick = () => {
            state.masterFile = null;
            masterFileInput.value = "";
            masterFileInfo.style.display = "none";
        };
    }

    function addStudentFiles(fileList) {
        for (const file of fileList) {
            // Avoid duplicate by name and size
            if (!state.studentFiles.some(f => f.name === file.name && f.size === file.size)) {
                state.studentFiles.push(file);
            }
        }
        renderStudentFilesList();
    }

    function renderStudentFilesList() {
        if (state.studentFiles.length === 0) {
            studentsFilesList.style.display = "none";
            filesContainer.innerHTML = "";
            filesCount.textContent = "0";
            return;
        }

        studentsFilesList.style.display = "block";
        filesCount.textContent = state.studentFiles.length;
        filesContainer.innerHTML = "";

        state.studentFiles.forEach((file, index) => {
            const chip = document.createElement("div");
            chip.className = "file-chip";
            chip.innerHTML = `
                <span>📄 ${file.name} <small style="color:var(--text-muted)">(${(file.size / 1024).toFixed(1)} KB)</small></span>
                <button type="button" class="file-chip-remove" title="Remove">&times;</button>
            `;
            chip.querySelector(".file-chip-remove").addEventListener("click", (e) => {
                e.stopPropagation();
                state.studentFiles.splice(index, 1);
                renderStudentFilesList();
            });
            filesContainer.appendChild(chip);
        });
    }

    // 4. Run Evaluation
    btnEvaluate.addEventListener("click", async () => {
        // Validation
        if (state.masterMode === "upload" && !state.masterFile) {
            alert("Please select or drop a Master Solution file, or switch to 'Paste Text'.");
            return;
        }
        if (state.masterMode === "paste" && !masterTextInput.value.trim()) {
            alert("Please paste your questions and answers in the text area.");
            return;
        }
        if (state.studentFiles.length === 0) {
            alert("Please upload at least one student handwritten assignment.");
            return;
        }

        // Prepare request
        const formData = new FormData();
        formData.append("strictness", strictnessSelect.value);

        if (state.masterMode === "upload") {
            formData.append("master_file", state.masterFile);
        } else {
            formData.append("master_text", masterTextInput.value.trim());
        }

        state.studentFiles.forEach(file => {
            formData.append("student_files", file);
        });

        // Show loading state
        loadingCard.style.display = "block";
        resultsSection.style.display = "none";
        btnEvaluate.disabled = true;

        try {
            const res = await fetch("/api/evaluate", {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.error || "Evaluation failed");
            }

            const data = await res.json();
            state.currentBatchResults = data;

            loadingCard.style.display = "none";
            resultsSection.style.display = "block";
            renderResults(data);

        } catch (err) {
            loadingCard.style.display = "none";
            alert(`Error: ${err.message}`);
        } finally {
            btnEvaluate.disabled = false;
        }
    });

    // 5. Render Results
    function renderResults(batch) {
        // Summary metrics
        metricTotal.textContent = batch.total_submissions;
        metricAverage.textContent = `${batch.class_average_score} (${batch.class_average_percentage}%)`;
        metricConfidence.textContent = `${batch.average_confidence}%`;
        metricReviewCount.textContent = batch.flagged_for_review_count;

        if (batch.flagged_for_review_count > 0) {
            document.getElementById("metricReviewBox").style.borderColor = "rgba(245, 158, 11, 0.4)";
        } else {
            document.getElementById("metricReviewBox").style.borderColor = "var(--border-color)";
        }

        // Populate Table
        resultsTableBody.innerHTML = "";
        batch.results.forEach((student, index) => {
            const row = document.createElement("tr");

            // Confidence class
            let confClass = "conf-high";
            if (student.overall_confidence_score < 70) confClass = "conf-low";
            else if (student.overall_confidence_score < 85) confClass = "conf-med";

            // Status
            const statusHtml = student.requires_manual_review
                ? `<span class="status-badge status-flagged">Needs Review</span>`
                : `<span class="status-badge status-verified">Verified</span>`;

            row.innerHTML = `
                <td>
                    <div class="student-name-cell">${escapeHtml(student.student_name)}</div>
                    <div class="student-sub-cell">${escapeHtml(student.file_name)} &bull; ${escapeHtml(student.student_id)}</div>
                </td>
                <td class="score-cell">${student.total_score} / ${student.max_possible_score}</td>
                <td>${student.percentage}%</td>
                <td><span class="conf-tag ${confClass}">${student.overall_confidence_score}%</span></td>
                <td>${statusHtml}</td>
                <td>
                    <button type="button" class="btn-secondary btn-view-detail" data-idx="${index}">View Breakdown</button>
                </td>
            `;

            row.querySelector(".btn-view-detail").addEventListener("click", () => {
                showStudentDetail(student);
            });

            resultsTableBody.appendChild(row);
        });

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: "smooth" });
    }

    // 6. Student Detail Modal
    function showStudentDetail(student) {
        modalStudentName.textContent = student.student_name;
        modalStudentSub.textContent = `${student.file_name} • Score: ${student.total_score}/${student.max_possible_score} (${student.percentage}%) • Confidence: ${student.overall_confidence_score}%`;

        let html = "";

        // If flagged for review
        if (student.requires_manual_review && student.review_reasons.length > 0) {
            html += `
                <div class="detail-review-alert">
                    <strong>Review Recommended:</strong>
                    <ul>
                        ${student.review_reasons.map(r => `<li>${escapeHtml(r)}</li>`).join("")}
                    </ul>
                </div>
            `;
        }

        // Overall teacher summary
        if (student.summary_feedback) {
            html += `
                <div style="margin-bottom:16px;padding:12px;background:var(--bg-page);border-radius:var(--radius-sm);font-size:0.86rem;">
                    <strong>Evaluation Summary:</strong> ${escapeHtml(student.summary_feedback)}
                </div>
            `;
        }

        // Question-by-question list
        html += `<div class="detail-q-list">`;
        student.question_evaluations.forEach(q => {
            html += `
                <div class="detail-q-box">
                    <div class="detail-q-top">
                        <span class="detail-q-id">${escapeHtml(q.question_id)}</span>
                        <span class="detail-q-marks">${q.marks_awarded} / ${q.max_marks} marks</span>
                    </div>

                    <div class="detail-transcription">
                        <small style="color:var(--text-muted);display:block;margin-bottom:2px">Transcribed from Handwriting:</small>
                        "${escapeHtml(q.student_transcription)}"
                    </div>

                    <div class="detail-feedback">
                        <strong>Feedback:</strong> ${escapeHtml(q.feedback)}
                    </div>
                </div>
            `;
        });
        html += `</div>`;

        modalBody.innerHTML = html;
        detailModal.style.display = "flex";
    }

    // 7. Modals Setup
    function setupModals() {
        btnCloseModal.addEventListener("click", () => detailModal.style.display = "none");
        window.addEventListener("click", (e) => {
            if (e.target === detailModal) detailModal.style.display = "none";
            if (e.target === settingsModal) settingsModal.style.display = "none";
        });

        // Settings Modal
        btnOpenSettings.addEventListener("click", () => {
            settingsStatus.style.display = "none";
            settingsModal.style.display = "flex";
        });

        btnCloseSettings.addEventListener("click", () => settingsModal.style.display = "none");

        btnSaveSettings.addEventListener("click", async () => {
            const key = settingApiKey.value.trim();
            const model = settingModel.value.trim();
            const threshold = settingThreshold.value.trim();

            try {
                const res = await fetch("/api/settings", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        gemini_api_key: key || undefined,
                        model_name: model,
                        review_threshold: threshold
                    })
                });

                if (res.ok) {
                    settingsStatus.className = "status-msg success";
                    settingsStatus.textContent = "Settings saved!";
                    settingsStatus.style.display = "block";
                    setTimeout(() => {
                        settingsModal.style.display = "none";
                        checkApiStatus();
                    }, 800);
                }
            } catch (err) {
                settingsStatus.className = "status-msg error";
                settingsStatus.textContent = err.message;
                settingsStatus.style.display = "block";
            }
        });

        // Export CSV
        btnExportCSV.addEventListener("click", () => {
            window.location.href = "/api/export/csv";
        });
    }

    function escapeHtml(text) {
        if (!text) return "";
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
