/**
 * HandwriteAI - Client Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
    // State
    const state = {
        masterSource: "demo-master",
        studentSource: "demo-students",
        masterFile: null,
        studentFiles: [],
        demoMasterData: null,
        lastBatchResult: null,
        currentFilter: "all",
        hasApiKey: false,
    };

    // DOM Elements
    const engineBadge = document.getElementById("engineStatusBadge");
    const engineText = document.getElementById("engineStatusText");
    const demoQuestionsPeek = document.getElementById("demoQuestionsPeek");
    const demoStudentsList = document.getElementById("demoStudentsList");
    const masterDropzone = document.getElementById("masterDropzone");
    const masterFileInput = document.getElementById("masterFileInput");
    const masterSelectedFile = document.getElementById("masterSelectedFile");
    const studentsDropzone = document.getElementById("studentsDropzone");
    const studentsFileInput = document.getElementById("studentsFileInput");
    const uploadedFilesPreview = document.getElementById("uploadedFilesPreview");
    const btnRunEvaluation = document.getElementById("btnRunEvaluation");

    const welcomePlaceholder = document.getElementById("welcomePlaceholder");
    const processingCard = document.getElementById("processingCard");
    const resultsDashboard = document.getElementById("resultsDashboard");
    const progressBar = document.getElementById("evaluationProgressBar");
    const processingTitle = document.getElementById("processingTitle");
    const processingDetail = document.getElementById("processingDetail");

    const studentCardsContainer = document.getElementById("studentCardsContainer");
    const filterPills = document.getElementById("filterPills");

    // Modal Elements
    const settingsModal = document.getElementById("settingsModal");
    const btnOpenSettings = document.getElementById("btnOpenSettings");
    const btnCloseSettings = document.getElementById("btnCloseSettings");
    const btnSaveSettings = document.getElementById("btnSaveSettings");
    const btnTestApiKey = document.getElementById("btnTestApiKey");
    const settingApiKey = document.getElementById("settingApiKey");
    const apiKeyTestStatus = document.getElementById("apiKeyTestStatus");

    const imageModal = document.getElementById("imageModal");
    const btnCloseImageModal = document.getElementById("btnCloseImageModal");
    const modalFullImage = document.getElementById("modalFullImage");
    const imageModalTitle = document.getElementById("imageModalTitle");

    // 1. Initial Load & Setup
    async function init() {
        await checkStatus();
        await loadDemoMaster();
        setupTabs();
        setupDropzones();
        setupModals();
        setupExports();
    }

    // 2. Fetch Backend Status
    async function checkStatus() {
        try {
            const res = await fetch("/api/status");
            const data = await res.json();
            state.hasApiKey = data.has_api_key;

            if (data.has_api_key) {
                engineBadge.className = "status-badge live";
                engineText.textContent = `Gemini Live (${data.model_name})`;
            } else {
                engineBadge.className = "status-badge mock";
                engineText.textContent = "Offline Simulation Mode";
            }

            renderDemoStudents(data.demo_students || []);
        } catch (err) {
            console.error("Status check failed:", err);
            engineBadge.className = "status-badge mock";
            engineText.textContent = "Offline Mode";
        }
    }

    // 3. Load Demo Master Solution Data
    async function loadDemoMaster() {
        try {
            const res = await fetch("/api/demo/master");
            const data = await res.json();
            state.demoMasterData = data;

            document.getElementById("demoMasterTitle").textContent = data.title;
            demoQuestionsPeek.innerHTML = "";

            data.questions.forEach((q) => {
                const item = document.createElement("div");
                item.className = "peek-item";
                item.innerHTML = `<strong>${q.question_id}:</strong> ${q.question_text} <span style="color:#818cf8;float:right">${q.max_marks} marks</span>`;
                demoQuestionsPeek.appendChild(item);
            });
        } catch (err) {
            console.error("Failed to load demo master:", err);
        }
    }

    // 4. Render Demo Students in Left Panel
    function renderDemoStudents(students) {
        demoStudentsList.innerHTML = "";
        students.forEach((st) => {
            const card = document.createElement("div");
            card.className = "demo-student-card";

            let tagClass = "tag-med";
            let tagText = "Average";
            if (st.name.includes("Alice")) {
                tagClass = "tag-high";
                tagText = "High / Neat";
            } else if (st.name.includes("Charlie")) {
                tagClass = "tag-low";
                tagText = "Low / Messy";
            }

            card.innerHTML = `
                <img src="${st.url}" class="demo-student-thumb" alt="${st.name}">
                <div class="demo-student-name">${st.name}</div>
                <span class="demo-student-tag ${tagClass}">${tagText}</span>
            `;
            card.addEventListener("click", () => showImagePreview(st.url, `${st.name}'s Handwritten Paper`));
            demoStudentsList.appendChild(card);
        });
    }

    // 5. Tabs Setup
    function setupTabs() {
        // Master tabs
        document.querySelectorAll("#masterSourceTabs .pill-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                document.querySelectorAll("#masterSourceTabs .pill-btn").forEach((b) => b.classList.remove("active"));
                document.querySelectorAll("#tab-demo-master, #tab-upload-master, #tab-paste-master").forEach((el) => el.classList.remove("active"));

                btn.classList.add("active");
                const target = btn.dataset.tab;
                state.masterSource = target;
                document.getElementById(`tab-${target}`).classList.add("active");
            });
        });

        // Student tabs
        document.querySelectorAll("#studentSourceTabs .pill-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                document.querySelectorAll("#studentSourceTabs .pill-btn").forEach((b) => b.classList.remove("active"));
                document.querySelectorAll("#tab-demo-students, #tab-upload-students").forEach((el) => el.classList.remove("active"));

                btn.classList.add("active");
                const target = btn.dataset.tab;
                state.studentSource = target;
                document.getElementById(`tab-${target}`).classList.add("active");
            });
        });
    }

    // 6. Dropzones Setup
    function setupDropzones() {
        // Master Solution Dropzone
        masterDropzone.addEventListener("click", () => masterFileInput.click());
        masterDropzone.addEventListener("dragover", (e) => {
            e.preventDefault();
            masterDropzone.classList.add("dragover");
        });
        masterDropzone.addEventListener("dragleave", () => masterDropzone.classList.remove("dragover"));
        masterDropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            masterDropzone.classList.remove("dragover");
            if (e.dataTransfer.files.length > 0) {
                handleMasterFile(e.dataTransfer.files[0]);
            }
        });
        masterFileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                handleMasterFile(e.target.files[0]);
            }
        });

        // Student Submissions Dropzone
        studentsDropzone.addEventListener("click", () => studentsFileInput.click());
        studentsDropzone.addEventListener("dragover", (e) => {
            e.preventDefault();
            studentsDropzone.classList.add("dragover");
        });
        studentsDropzone.addEventListener("dragleave", () => studentsDropzone.classList.remove("dragover"));
        studentsDropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            studentsDropzone.classList.remove("dragover");
            handleStudentFiles(e.dataTransfer.files);
        });
        studentsFileInput.addEventListener("change", (e) => {
            handleStudentFiles(e.target.files);
        });
    }

    function handleMasterFile(file) {
        state.masterFile = file;
        masterSelectedFile.style.display = "inline-block";
        masterSelectedFile.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    }

    function handleStudentFiles(fileList) {
        for (const file of fileList) {
            state.studentFiles.push(file);
        }
        renderUploadedFilesPreview();
    }

    function renderUploadedFilesPreview() {
        uploadedFilesPreview.innerHTML = "";
        state.studentFiles.forEach((file, idx) => {
            const chip = document.createElement("div");
            chip.className = "upload-item-chip";
            chip.innerHTML = `
                <span>📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)</span>
                <button type="button" style="background:none;border:none;color:#fb7185;cursor:pointer;font-weight:bold" data-idx="${idx}">&times;</button>
            `;
            chip.querySelector("button").addEventListener("click", (e) => {
                e.stopPropagation();
                state.studentFiles.splice(idx, 1);
                renderUploadedFilesPreview();
            });
            uploadedFilesPreview.appendChild(chip);
        });
    }

    // 7. Evaluation Action
    btnRunEvaluation.addEventListener("click", async () => {
        await runEvaluation();
    });

    async function runEvaluation() {
        welcomePlaceholder.style.display = "none";
        resultsDashboard.style.display = "none";
        processingCard.style.display = "block";

        const formData = new FormData();
        const strictness = document.getElementById("strictnessSelect").value;
        const forceMock = document.getElementById("chkForceMock").checked;
        formData.append("strictness", strictness);
        formData.append("force_mock", forceMock ? "true" : "false");

        // Master Solution
        if (state.masterSource === "demo-master") {
            formData.append("use_demo_master", "true");
        } else if (state.masterSource === "upload-master" && state.masterFile) {
            formData.append("master_file", state.masterFile);
        } else if (state.masterSource === "paste-master") {
            const text = document.getElementById("masterTextInput").value.trim();
            if (text) formData.append("master_text", text);
            else formData.append("use_demo_master", "true");
        } else {
            formData.append("use_demo_master", "true");
        }

        // Students
        if (state.studentSource === "demo-students") {
            formData.append("use_demo_students", "true");
        } else if (state.studentSource === "upload-students" && state.studentFiles.length > 0) {
            state.studentFiles.forEach((f) => formData.append("student_files", f));
        } else {
            formData.append("use_demo_students", "true");
        }

        // Animate progress steps for smooth UX
        let progress = 10;
        progressBar.style.width = `${progress}%`;
        const steps = [
            { pct: 30, title: "Optimizing Images & Normalizing Scans...", desc: "Applying adaptive contrast and resizing for fast multimodal OCR" },
            { pct: 60, title: "Transcribing Handwriting Strokes...", desc: "Recognizing handwritten answers using deep vision models" },
            { pct: 85, title: "Cross-Referencing Master Rubrics...", desc: "Evaluating semantic alignment and assigning marks per question" },
            { pct: 95, title: "Computing Precision Confidence Scores...", desc: "Auditing handwriting legibility and flagging edge cases" }
        ];

        let stepIndex = 0;
        const interval = setInterval(() => {
            if (stepIndex < steps.length) {
                const s = steps[stepIndex];
                progressBar.style.width = `${s.pct}%`;
                processingTitle.textContent = s.title;
                processingDetail.textContent = s.desc;
                stepIndex++;
            }
        }, 350);

        try {
            const res = await fetch("/api/evaluate", {
                method: "POST",
                body: formData
            });

            clearInterval(interval);
            progressBar.style.width = "100%";

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.error || "Evaluation failed");
            }

            const data = await res.json();
            state.lastBatchResult = data;

            setTimeout(() => {
                processingCard.style.display = "none";
                resultsDashboard.style.display = "block";
                renderResults(data);
            }, 300);

        } catch (err) {
            clearInterval(interval);
            processingCard.style.display = "none";
            welcomePlaceholder.style.display = "block";
            alert(`Evaluation Error: ${err.message}`);
        }
    }

    // 8. Render Results Dashboard
    function renderResults(batch) {
        // Analytics Strip
        document.getElementById("metricClassAvg").textContent = `${batch.class_average_score} / 20`;
        document.getElementById("metricClassPct").textContent = `${batch.class_average_percentage}%`;
        document.getElementById("metricAvgConf").textContent = `${batch.average_confidence}%`;

        const confBadge = document.getElementById("metricConfQuality");
        if (batch.average_confidence >= 85) {
            confBadge.textContent = "High Reliability";
            confBadge.className = "metric-badge conf-badge";
        } else if (batch.average_confidence >= 70) {
            confBadge.textContent = "Moderate";
            confBadge.className = "metric-badge";
        } else {
            confBadge.textContent = "Audit Needed";
            confBadge.className = "metric-badge badge-rose";
        }

        document.getElementById("metricTotalSubs").textContent = batch.total_submissions;
        document.getElementById("metricProcTime").textContent = `in ${batch.processing_time_total_seconds}s`;
        document.getElementById("metricFlaggedCount").textContent = batch.flagged_for_review_count;

        // Toolbar Counts
        const verifiedCount = batch.results.filter(r => !r.requires_manual_review).length;
        document.getElementById("countAll").textContent = batch.total_submissions;
        document.getElementById("countVerified").textContent = verifiedCount;
        document.getElementById("countFlagged").textContent = batch.flagged_for_review_count;

        setupFilters(batch.results);
        renderStudentCards(batch.results);
    }

    // 9. Filter Setup
    function setupFilters(results) {
        filterPills.querySelectorAll(".filter-btn").forEach(btn => {
            btn.onclick = () => {
                filterPills.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                state.currentFilter = btn.dataset.filter;

                let filtered = results;
                if (state.currentFilter === "verified") {
                    filtered = results.filter(r => !r.requires_manual_review);
                } else if (state.currentFilter === "flagged") {
                    filtered = results.filter(r => r.requires_manual_review);
                }
                renderStudentCards(filtered);
            };
        });
    }

    // 10. Render Student Evaluation Cards
    function renderStudentCards(students) {
        studentCardsContainer.innerHTML = "";

        if (students.length === 0) {
            studentCardsContainer.innerHTML = `
                <div style="text-align:center;padding:40px;color:var(--text-muted)">
                    No submissions found matching this filter.
                </div>
            `;
            return;
        }

        students.forEach((st, idx) => {
            const card = document.createElement("div");
            card.className = `student-eval-card ${st.requires_manual_review ? "flagged" : ""}`;

            const initials = st.student_name.split(" ").map(p => p[0]).join("").slice(0, 2).toUpperCase() || "ST";
            
            // Confidence gauge calculations
            const radius = 24;
            const circumference = 2 * Math.PI * radius;
            const offset = circumference - (st.overall_confidence_score / 100) * circumference;
            let gaugeColor = "#10b981"; // emerald
            if (st.overall_confidence_score < 70) gaugeColor = "#f43f5e"; // rose
            else if (st.overall_confidence_score < 85) gaugeColor = "#f59e0b"; // amber

            card.innerHTML = `
                <div class="student-card-top">
                    <div class="student-meta">
                        <div class="student-avatar">${initials}</div>
                        <div>
                            <h3 class="student-name-title">${st.student_name}</h3>
                            <div class="student-id-sub">${st.student_id} &bull; ${st.file_name}</div>
                        </div>
                    </div>

                    <div class="scores-block">
                        <div class="score-box">
                            <div class="score-big">${st.total_score} <span style="font-size:0.9rem;color:var(--text-muted)">/ ${st.max_possible_score}</span></div>
                            <div class="score-pct">${st.percentage}%</div>
                        </div>

                        <div class="gauge-wrapper" title="Checking Accuracy Confidence: ${st.overall_confidence_score}%">
                            <svg class="gauge-svg" viewBox="0 0 58 58">
                                <circle class="gauge-bg" cx="29" cy="29" r="${radius}"></circle>
                                <circle class="gauge-fill" cx="29" cy="29" r="${radius}" 
                                    stroke="${gaugeColor}" 
                                    stroke-dasharray="${circumference}" 
                                    stroke-dashoffset="${offset}"></circle>
                            </svg>
                            <span class="gauge-value">${Math.round(st.overall_confidence_score)}%</span>
                        </div>
                    </div>
                </div>

                ${st.requires_manual_review ? `
                    <div class="review-alert-banner">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                            <line x1="12" y1="9" x2="12" y2="13"></line>
                            <line x1="12" y1="17" x2="12.01" y2="17"></line>
                        </svg>
                        <div>
                            <div class="review-alert-title">Flagged for Teacher Manual Verification</div>
                            <ul class="review-alert-list">
                                ${st.review_reasons.map(r => `<li>${r}</li>`).join("")}
                            </ul>
                        </div>
                    </div>
                ` : ""}

                <div class="details-toggle-bar">
                    <button class="btn btn-secondary btn-sm" id="btnPreviewPaper-${idx}">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                            <circle cx="8.5" cy="8.5" r="1.5"></circle>
                            <polyline points="21 15 16 10 5 21"></polyline>
                        </svg>
                        <span>View Original Handwritten Page</span>
                    </button>

                    <button class="btn-toggle-details" id="btnToggleQ-${idx}">
                        <span>Show Question Breakdown (${st.question_evaluations.length})</span>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </button>
                </div>

                <div class="questions-breakdown-panel" id="qPanel-${idx}" style="display:none">
                    ${st.question_evaluations.map(q => `
                        <div class="question-eval-card">
                            <div class="q-card-header">
                                <span class="q-title">${q.question_id}</span>
                                <div style="display:flex;gap:8px;align-items:center">
                                    <span style="font-size:0.75rem;color:var(--text-muted)">Confidence: <strong>${q.confidence_score}%</strong> &bull; Legibility: <strong>${q.legibility_score}%</strong></span>
                                    <span class="q-marks-badge">${q.marks_awarded} / ${q.max_marks} marks</span>
                                </div>
                            </div>

                            <div class="transcription-box">
                                <div class="transcription-label">Student Handwritten Answer (AI Transcribed):</div>
                                "${q.student_transcription}"
                            </div>

                            <div class="feedback-box">
                                <strong>Feedback & Rationale:</strong> ${q.feedback}
                            </div>

                            <div class="concepts-row">
                                ${q.key_concepts_covered.map(c => `<span class="concept-tag hit">&check; ${c}</span>`).join("")}
                                ${q.missing_concepts.map(c => `<span class="concept-tag miss">&times; Missing: ${c}</span>`).join("")}
                            </div>
                        </div>
                    `).join("")}
                </div>
            `;

            // Toggle Questions Accordion
            const qBtn = card.querySelector(`#btnToggleQ-${idx}`);
            const qPanel = card.querySelector(`#qPanel-${idx}`);
            qBtn.addEventListener("click", () => {
                const isOpen = qPanel.style.display !== "none";
                qPanel.style.display = isOpen ? "none" : "flex";
                qBtn.querySelector("span").textContent = isOpen 
                    ? `Show Question Breakdown (${st.question_evaluations.length})` 
                    : "Hide Question Breakdown";
                qBtn.querySelector("svg").style.transform = isOpen ? "rotate(0deg)" : "rotate(180deg)";
            });

            // Preview Original Paper
            const previewBtn = card.querySelector(`#btnPreviewPaper-${idx}`);
            previewBtn.addEventListener("click", () => {
                const url = st.preview_url || `/static/demo/${st.file_name}`;
                showImagePreview(url, `${st.student_name}'s Handwritten Submission`);
            });

            studentCardsContainer.appendChild(card);
        });
    }

    // 11. Image Preview Modal
    function showImagePreview(url, title) {
        modalFullImage.src = url;
        imageModalTitle.textContent = title;
        imageModal.style.display = "flex";
    }

    // 12. Modals & Settings
    function setupModals() {
        btnOpenSettings.addEventListener("click", () => {
            apiKeyTestStatus.style.display = "none";
            settingsModal.style.display = "flex";
        });

        btnCloseSettings.addEventListener("click", () => {
            settingsModal.style.display = "none";
        });

        btnCloseImageModal.addEventListener("click", () => {
            imageModal.style.display = "none";
        });

        // Close when clicking backdrop
        window.addEventListener("click", (e) => {
            if (e.target === settingsModal) settingsModal.style.display = "none";
            if (e.target === imageModal) imageModal.style.display = "none";
        });

        // Test API Key
        btnTestApiKey.addEventListener("click", async () => {
            const key = settingApiKey.value.trim();
            apiKeyTestStatus.style.display = "block";
            apiKeyTestStatus.className = "test-feedback";
            apiKeyTestStatus.textContent = "Pinging Gemini API...";

            try {
                const res = await fetch("/api/test-gemini", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ api_key: key })
                });
                const data = await res.json();
                if (res.ok) {
                    apiKeyTestStatus.className = "test-feedback success";
                    apiKeyTestStatus.textContent = `Success! ${data.message} ("${data.reply}")`;
                } else {
                    apiKeyTestStatus.className = "test-feedback error";
                    apiKeyTestStatus.textContent = data.message || "Failed to connect.";
                }
            } catch (err) {
                apiKeyTestStatus.className = "test-feedback error";
                apiKeyTestStatus.textContent = `Error: ${err.message}`;
            }
        });

        // Save Settings
        btnSaveSettings.addEventListener("click", async () => {
            const key = settingApiKey.value.trim();
            const model = document.getElementById("settingModel").value;
            const threshold = document.getElementById("settingThreshold").value;

            try {
                const res = await fetch("/api/settings", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        gemini_api_key: key,
                        model_name: model,
                        review_threshold: threshold
                    })
                });
                if (res.ok) {
                    settingsModal.style.display = "none";
                    await checkStatus();
                }
            } catch (err) {
                alert(`Error saving settings: ${err.message}`);
            }
        });
    }

    // 13. Export Handlers
    function setupExports() {
        document.getElementById("btnExportCSV").addEventListener("click", () => {
            window.location.href = "/api/export/csv";
        });

        document.getElementById("btnExportJSON").addEventListener("click", () => {
            window.location.href = "/api/export/json";
        });
    }

    // Start application
    init();
});
