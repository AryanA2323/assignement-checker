/**
 * Assignment Checker — Enterprise-Grade Frontend Controller
 * Powered by Lucide Icons, Chart.js, and Canvas Confetti
 */

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------------------
    // Application State
    // -------------------------------------------------------------------------
    const state = {
        masterMode: "upload", // 'upload' | 'paste' | 'ai_direct'
        masterFile: null,
        studentFiles: [],
        useSampleAss1: false,
        currentBatchResults: null,
        activeFilter: "all",
        searchQuery: "",
        chartInstance: null
    };

    // -------------------------------------------------------------------------
    // DOM Element Selectors
    // -------------------------------------------------------------------------
    // Top Nav & Sample
    const btnQuickSample = document.getElementById("btnQuickSample");
    const systemStatusPill = document.getElementById("systemStatusPill");

    // Master Key Elements
    const btnModeUpload = document.getElementById("btnModeUpload");
    const btnModePaste = document.getElementById("btnModePaste");
    const btnModeAIDirect = document.getElementById("btnModeAIDirect");
    const masterFileSection = document.getElementById("masterFileSection");
    const masterTextSection = document.getElementById("masterTextSection");
    const masterAIDirectSection = document.getElementById("masterAIDirectSection");
    const masterDropZone = document.getElementById("masterDropZone");
    const masterFileInput = document.getElementById("masterFileInput");
    const masterFileInfo = document.getElementById("masterFileInfo");
    const masterTextInput = document.getElementById("masterTextInput");
    const btnInsertSampleText = document.getElementById("btnInsertSampleText");
    const subjectTopicInput = document.getElementById("subjectTopicInput");

    // Student Submissions Elements
    const studentsDropZone = document.getElementById("studentsDropZone");
    const studentsFileInput = document.getElementById("studentsFileInput");
    const studentsFilesList = document.getElementById("studentsFilesList");
    const filesContainer = document.getElementById("filesContainer");
    const filesCount = document.getElementById("filesCount");
    const btnClearFiles = document.getElementById("btnClearFiles");

    // Action Bar Elements
    const strictnessSelect = document.getElementById("strictnessSelect");
    const btnEvaluate = document.getElementById("btnEvaluate");
    const btnEvaluateText = document.getElementById("btnEvaluateText");
    const loadingCard = document.getElementById("loadingCard");
    const loadingTitle = document.getElementById("loadingTitle");
    const loadingSubtitle = document.getElementById("loadingSubtitle");
    const ms1 = document.getElementById("ms1");
    const ms2 = document.getElementById("ms2");
    const ms3 = document.getElementById("ms3");

    // Results Dashboard Elements
    const resultsSection = document.getElementById("resultsSection");
    const metricTotal = document.getElementById("metricTotal");
    const metricAverage = document.getElementById("metricAverage");
    const metricAveragePct = document.getElementById("metricAveragePct");
    const metricConfidence = document.getElementById("metricConfidence");
    const metricReviewCount = document.getElementById("metricReviewCount");
    const metricReviewBox = document.getElementById("metricReviewBox");
    const btnFilterReviewOnly = document.getElementById("btnFilterReviewOnly");

    // Chart & Toolbar Elements
    const analyticsChartContainer = document.getElementById("analyticsChartContainer");
    const btnToggleChart = document.getElementById("btnToggleChart");
    const btnToggleChartText = document.getElementById("btnToggleChartText");
    const searchInput = document.getElementById("searchInput");
    const filterPills = document.querySelectorAll(".filter-pill");
    const countAll = document.getElementById("countAll");
    const countVerified = document.getElementById("countVerified");
    const countFlagged = document.getElementById("countFlagged");
    const resultsTableBody = document.getElementById("resultsTableBody");
    const btnExportCSV = document.getElementById("btnExportCSV");
    const btnPrintReport = document.getElementById("btnPrintReport");

    // Detail Inspection Modal Elements
    const detailModal = document.getElementById("detailModal");
    const btnCloseModal = document.getElementById("btnCloseModal");
    const modalStudentAvatar = document.getElementById("modalStudentAvatar");
    const modalStudentName = document.getElementById("modalStudentName");
    const modalModeBadge = document.getElementById("modalModeBadge");
    const modalStudentSub = document.getElementById("modalStudentSub");
    const modalTabs = document.querySelectorAll(".modal-tab");
    const tabRubric = document.getElementById("tabRubric");
    const tabScan = document.getElementById("tabScan");
    const tabAudit = document.getElementById("tabAudit");
    const scanPreviewImage = document.getElementById("scanPreviewImage");
    const scanDownloadBtn = document.getElementById("scanDownloadBtn");
    const scanFileName = document.getElementById("scanFileName");
    const diagnosticsContent = document.getElementById("diagnosticsContent");

    // Settings Modal Elements
    const settingsModal = document.getElementById("settingsModal");
    const btnOpenSettings = document.getElementById("btnOpenSettings");
    const btnCloseSettings = document.getElementById("btnCloseSettings");
    const btnSaveSettings = document.getElementById("btnSaveSettings");
    const btnTestApi = document.getElementById("btnTestApi");
    const settingApiKey = document.getElementById("settingApiKey");
    const settingModel = document.getElementById("settingModel");
    const settingThreshold = document.getElementById("settingThreshold");
    const settingsStatus = document.getElementById("settingsStatus");

    // -------------------------------------------------------------------------
    // Initialization
    // -------------------------------------------------------------------------
    initLucide();
    checkApiStatus();
    setupMasterModeSwitch();
    setupDropZones();
    setupQuickTags();
    setupQuickSampleLoader();
    setupModals();
    setupTableFilters();
    setupActionButtons();

    function initLucide() {
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    // -------------------------------------------------------------------------
    // 1. API Status Check
    // -------------------------------------------------------------------------
    async function checkApiStatus() {
        try {
            const res = await fetch("/api/status");
            const data = await res.json();
            if (data.has_api_key) {
                settingModel.value = data.model_name || "gemini-3.5-flash-lite";
                settingThreshold.value = data.review_threshold || 70;
            }
        } catch (err) {
            console.warn("Could not fetch API status:", err);
        }
    }

    // -------------------------------------------------------------------------
    // 2. Step 1 Mode Toggle (Upload, Paste, AI Direct)
    // -------------------------------------------------------------------------
    function setupMasterModeSwitch() {
        btnModeUpload.addEventListener("click", () => setMasterMode("upload"));
        btnModePaste.addEventListener("click", () => setMasterMode("paste"));
        btnModeAIDirect.addEventListener("click", () => setMasterMode("ai_direct"));

        if (btnInsertSampleText) {
            btnInsertSampleText.addEventListener("click", () => {
                masterTextInput.value = `Title: CS 545: Advanced Distributed Systems
Subject: Distributed Computing & Fault Tolerance

Q1: Explain the Raft Log Matching Property and commit safety rules.
Marks: 12
Answer: If two logs contain an entry with identical index and term, they store identical commands and histories. A leader cannot commit older entries solely by counting replicas; it must commit an entry from its current term by majority.

Q2: Distinguish Strict 2PL from Rigorous 2PL and explain Snapshot Isolation Write Skew.
Marks: 13
Answer: Strict 2PL holds write locks until commit; Rigorous 2PL holds all locks until commit. Write skew occurs under Snapshot Isolation when transactions make concurrent updates to disjoint records that collectively violate an invariant.`;
            });
        }
    }

    function setMasterMode(mode) {
        state.masterMode = mode;
        state.useSampleAss1 = false; // Reset sample flag if user explicitly switches mode

        // Update segmented button classes
        btnModeUpload.classList.toggle("active", mode === "upload");
        btnModePaste.classList.toggle("active", mode === "paste");
        btnModeAIDirect.classList.toggle("active", mode === "ai_direct");

        // Toggle panes
        masterFileSection.style.display = (mode === "upload") ? "block" : "none";
        masterTextSection.style.display = (mode === "paste") ? "block" : "none";
        masterAIDirectSection.style.display = (mode === "ai_direct") ? "block" : "none";

        // Update CTA label
        if (mode === "ai_direct") {
            btnEvaluateText.textContent = "Run Direct AI Evaluation (Google Data)";
        } else {
            btnEvaluateText.textContent = "Run AI Assignment Checking";
        }

        initLucide();
    }

    function setupQuickTags() {
        document.querySelectorAll(".quick-tag").forEach(tag => {
            tag.addEventListener("click", () => {
                subjectTopicInput.value = tag.getAttribute("data-tag");
                subjectTopicInput.focus();
            });
        });
    }

    // -------------------------------------------------------------------------
    // 3. One-Click Sample Dataset Loader (CS 545 ass_1)
    // -------------------------------------------------------------------------
    function setupQuickSampleLoader() {
        btnQuickSample.addEventListener("click", async () => {
            try {
                btnQuickSample.innerHTML = `<i data-lucide="loader-2" class="btn-icon-svg" style="animation:spinRing 1s linear infinite"></i> Loading...`;
                initLucide();

                const res = await fetch("/api/sample/info");
                const info = await res.json();

                // Set state to use sample ass_1
                state.useSampleAss1 = true;
                setMasterMode("upload");

                // Set Master File visual badge
                state.masterFile = { name: "ass_1/master_solution.pdf", size: 9499, isSample: true };
                masterFileInfo.style.display = "inline-flex";
                masterFileInfo.innerHTML = `
                    <div style="display:flex;align-items:center;gap:8px">
                        <i data-lucide="file-check" style="width:16px;height:16px;color:#a5b4fc"></i>
                        <span>${info.course} — Official Master Key (PDF)</span>
                    </div>
                    <button type="button" class="file-btn-remove" title="Remove">&times;</button>
                `;
                masterFileInfo.querySelector(".file-btn-remove").onclick = () => {
                    state.masterFile = null;
                    state.useSampleAss1 = false;
                    masterFileInfo.style.display = "none";
                };

                // Populate student submissions
                state.studentFiles = info.students.map(s => ({
                    name: s.file,
                    size: 650000,
                    isSample: true,
                    meta: s
                }));

                renderStudentFilesList();

                // Reset button text
                btnQuickSample.innerHTML = `<i data-lucide="check" class="btn-icon-svg"></i> <span>Sample Loaded!</span>`;
                setTimeout(() => {
                    btnQuickSample.innerHTML = `<i data-lucide="zap" class="btn-icon-svg"></i> <span>Load Sample Dataset</span>`;
                    initLucide();
                }, 2200);

                initLucide();

                // Scroll smoothly to action bar
                document.querySelector(".action-bar").scrollIntoView({ behavior: "smooth" });

            } catch (err) {
                console.error("Error loading sample:", err);
                alert("Failed to load sample dataset: " + err.message);
                btnQuickSample.innerHTML = `<i data-lucide="zap" class="btn-icon-svg"></i> <span>Load Sample Dataset</span>`;
                initLucide();
            }
        });
    }

    // -------------------------------------------------------------------------
    // 4. Drag & Drop Surfaces
    // -------------------------------------------------------------------------
    function setupDropZones() {
        // Master File Zone
        masterDropZone.addEventListener("click", () => masterFileInput.click());
        bindDropEvents(masterDropZone, files => {
            if (files.length > 0) setMasterFile(files[0]);
        });
        masterFileInput.addEventListener("change", e => {
            if (e.target.files.length > 0) setMasterFile(e.target.files[0]);
        });

        // Students Zone
        studentsDropZone.addEventListener("click", () => studentsFileInput.click());
        bindDropEvents(studentsDropZone, files => addStudentFiles(files));
        studentsFileInput.addEventListener("change", e => addStudentFiles(e.target.files));

        btnClearFiles.addEventListener("click", () => {
            state.studentFiles = [];
            state.useSampleAss1 = false;
            renderStudentFilesList();
        });
    }

    function bindDropEvents(zone, onDropCallback) {
        zone.addEventListener("dragover", e => {
            e.preventDefault();
            zone.classList.add("dragover");
        });
        zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
        zone.addEventListener("drop", e => {
            e.preventDefault();
            zone.classList.remove("dragover");
            if (e.dataTransfer.files.length > 0) {
                onDropCallback(e.dataTransfer.files);
            }
        });
    }

    function setMasterFile(file) {
        state.masterFile = file;
        state.useSampleAss1 = false;
        masterFileInfo.style.display = "inline-flex";
        masterFileInfo.innerHTML = `
            <div style="display:flex;align-items:center;gap:8px">
                <i data-lucide="file-text" style="width:16px;height:16px;color:#a5b4fc"></i>
                <span>${file.name} <small style="color:var(--text-muted)">(${(file.size / 1024).toFixed(1)} KB)</small></span>
            </div>
            <button type="button" class="file-btn-remove" title="Remove">&times;</button>
        `;
        masterFileInfo.querySelector(".file-btn-remove").onclick = () => {
            state.masterFile = null;
            masterFileInput.value = "";
            masterFileInfo.style.display = "none";
        };
        initLucide();
    }

    function addStudentFiles(fileList) {
        state.useSampleAss1 = false;
        for (const file of fileList) {
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
            const ext = file.name.split(".").pop().toUpperCase();
            const isPdf = ext === "PDF";

            const card = document.createElement("div");
            card.className = "file-entry-card";
            card.innerHTML = `
                <div class="file-entry-left">
                    <span class="file-format-badge ${isPdf ? 'pdf' : ''}">${ext}</span>
                    <div>
                        <div class="file-entry-name" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</div>
                        <div class="file-entry-size">${(file.size / 1024).toFixed(1)} KB</div>
                    </div>
                </div>
                <button type="button" class="file-btn-remove" title="Remove attachment">&times;</button>
            `;

            card.querySelector(".file-btn-remove").addEventListener("click", e => {
                e.stopPropagation();
                state.studentFiles.splice(index, 1);
                renderStudentFilesList();
            });

            filesContainer.appendChild(card);
        });

        initLucide();
    }

    // -------------------------------------------------------------------------
    // 5. Evaluation Execution
    // -------------------------------------------------------------------------
    function setupActionButtons() {
        btnEvaluate.addEventListener("click", runEvaluation);

        btnExportCSV.addEventListener("click", () => {
            window.location.href = "/api/export/csv";
        });

        btnPrintReport.addEventListener("click", () => {
            window.print();
        });

        if (btnFilterReviewOnly) {
            btnFilterReviewOnly.addEventListener("click", () => {
                setTableFilter("flagged");
            });
        }

        if (btnToggleChart) {
            btnToggleChart.addEventListener("click", () => {
                const isHidden = analyticsChartContainer.style.display === "none";
                analyticsChartContainer.style.display = isHidden ? "block" : "none";
                btnToggleChartText.textContent = isHidden ? "Hide Chart" : "Show Chart";
            });
        }
    }

    async function runEvaluation() {
        // Validation
        if (state.masterMode === "upload" && !state.masterFile && !state.useSampleAss1) {
            alert("Please provide a Master Solution file, or switch to '✨ Check with AI'.");
            return;
        }
        if (state.masterMode === "paste" && !masterTextInput.value.trim()) {
            alert("Please paste your questions and answers in the text editor.");
            return;
        }
        if (state.studentFiles.length === 0 && !state.useSampleAss1) {
            alert("Please attach at least one student handwritten assignment.");
            return;
        }

        // Prepare Form Data
        const formData = new FormData();
        formData.append("strictness", strictnessSelect.value);
        formData.append("evaluation_mode", state.masterMode === "ai_direct" ? "ai_direct" : "master_solution");

        if (state.useSampleAss1) {
            formData.append("use_sample_ass1", "true");
        } else {
            if (state.masterMode === "upload") {
                formData.append("master_file", state.masterFile);
            } else if (state.masterMode === "paste") {
                formData.append("master_text", masterTextInput.value.trim());
            }

            state.studentFiles.forEach(file => {
                formData.append("student_files", file);
            });
        }

        if (state.masterMode === "ai_direct") {
            const subject = subjectTopicInput ? subjectTopicInput.value.trim() : "";
            if (subject) formData.append("subject_or_topic", subject);
        }

        // Show animated progress state
        loadingCard.style.display = "block";
        resultsSection.style.display = "none";
        btnEvaluate.disabled = true;

        // Animate milestones
        animateMilestones();

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

            // Celebration Confetti
            triggerCelebration();

        } catch (err) {
            loadingCard.style.display = "none";
            alert(`Evaluation Error: ${err.message}`);
        } finally {
            btnEvaluate.disabled = false;
        }
    }

    function animateMilestones() {
        ms1.className = "milestone-item active";
        ms2.className = "milestone-item";
        ms3.className = "milestone-item";

        setTimeout(() => {
            ms1.className = "milestone-item";
            ms2.className = "milestone-item active";
        }, 1800);

        setTimeout(() => {
            ms2.className = "milestone-item";
            ms3.className = "milestone-item active";
        }, 3600);
    }

    function triggerCelebration() {
        if (window.confetti) {
            window.confetti({
                particleCount: 65,
                spread: 70,
                origin: { y: 0.65 },
                colors: ["#6366f1", "#8b5cf6", "#10b981", "#d946ef"]
            });
        }
    }

    // -------------------------------------------------------------------------
    // 6. Render Results Dashboard & Chart.js
    // -------------------------------------------------------------------------
    function renderResults(batch) {
        // Summary Metrics
        metricTotal.textContent = batch.total_submissions;
        metricAverage.textContent = batch.class_average_score;
        metricAveragePct.textContent = `${batch.class_average_percentage}%`;
        metricConfidence.textContent = `${batch.average_confidence}%`;
        metricReviewCount.textContent = batch.flagged_for_review_count;

        if (batch.flagged_for_review_count > 0) {
            metricReviewBox.style.borderColor = "var(--amber-border)";
        } else {
            metricReviewBox.style.borderColor = "var(--border-subtle)";
        }

        // Update counts
        countAll.textContent = batch.results.length;
        countVerified.textContent = batch.results.filter(r => !r.requires_manual_review).length;
        countFlagged.textContent = batch.flagged_for_review_count;

        // Render Table & Chart
        renderFilteredTable();
        renderChart(batch);

        initLucide();

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: "smooth" });
    }

    function setupTableFilters() {
        filterPills.forEach(pill => {
            pill.addEventListener("click", () => {
                setTableFilter(pill.getAttribute("data-filter"));
            });
        });

        if (searchInput) {
            searchInput.addEventListener("input", e => {
                state.searchQuery = e.target.value.toLowerCase().trim();
                renderFilteredTable();
            });
        }
    }

    function setTableFilter(filter) {
        state.activeFilter = filter;
        filterPills.forEach(p => {
            p.classList.toggle("active", p.getAttribute("data-filter") === filter);
        });
        renderFilteredTable();
    }

    function renderFilteredTable() {
        if (!state.currentBatchResults) return;

        let items = state.currentBatchResults.results;

        // Filter by tab
        if (state.activeFilter === "verified") {
            items = items.filter(r => !r.requires_manual_review);
        } else if (state.activeFilter === "flagged") {
            items = items.filter(r => r.requires_manual_review);
        }

        // Filter by search query
        if (state.searchQuery) {
            items = items.filter(r =>
                r.student_name.toLowerCase().includes(state.searchQuery) ||
                r.student_id.toLowerCase().includes(state.searchQuery) ||
                r.file_name.toLowerCase().includes(state.searchQuery)
            );
        }

        resultsTableBody.innerHTML = "";

        if (items.length === 0) {
            resultsTableBody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align:center;padding:32px;color:var(--text-muted);">
                        No student submissions match the current filter.
                    </td>
                </tr>
            `;
            return;
        }

        items.forEach((student, index) => {
            const row = document.createElement("tr");

            // Confidence class
            let confClass = "conf-high";
            if (student.overall_confidence_score < 70) confClass = "conf-low";
            else if (student.overall_confidence_score < 85) confClass = "conf-med";

            // Status badge
            const statusHtml = student.requires_manual_review
                ? `<span class="status-badge-cell status-flagged"><i data-lucide="alert-triangle" style="width:13px;height:13px"></i> Needs Review</span>`
                : `<span class="status-badge-cell status-verified"><i data-lucide="check-circle" style="width:13px;height:13px"></i> Verified</span>`;

            // Mode badge
            const isAiDirect = student.evaluation_mode === "ai_direct" || state.currentBatchResults.evaluation_mode === "ai_direct";
            const modeHtml = isAiDirect
                ? `<span class="mode-badge-tag"><i data-lucide="sparkles" style="width:12px;height:12px"></i> Google Data</span>`
                : `<span class="mode-badge-tag master"><i data-lucide="file-check" style="width:12px;height:12px"></i> Master Key</span>`;

            const initials = getInitials(student.student_name);
            const ext = student.file_name.split(".").pop().toUpperCase();

            row.innerHTML = `
                <td>
                    <div class="student-cell">
                        <div class="student-avatar">${initials}</div>
                        <div class="student-info">
                            <span class="student-name-row">${escapeHtml(student.student_name)}</span>
                            <span class="student-id-row">
                                <span class="file-type-pill">${ext}</span>
                                <span>${escapeHtml(student.student_id)}</span>
                            </span>
                        </div>
                    </div>
                </td>
                <td>${modeHtml}</td>
                <td><span class="score-display-cell">${student.total_score} / ${student.max_possible_score}</span></td>
                <td>
                    <div class="pct-bar-cell">
                        <div class="pct-bar-bg">
                            <div class="pct-bar-fill" style="width:${student.percentage}%"></div>
                        </div>
                        <span style="font-size:0.82rem;font-weight:700">${student.percentage}%</span>
                    </div>
                </td>
                <td><span class="confidence-pill ${confClass}">${student.overall_confidence_score}%</span></td>
                <td>${statusHtml}</td>
                <td style="text-align:right">
                    <button type="button" class="btn-inspect" data-idx="${index}">
                        <span>Inspect</span>
                        <i data-lucide="arrow-right" style="width:14px;height:14px"></i>
                    </button>
                </td>
            `;

            row.querySelector(".btn-inspect").addEventListener("click", () => {
                showStudentDetail(student);
            });

            resultsTableBody.appendChild(row);
        });

        initLucide();
    }

    function renderChart(batch) {
        if (!window.Chart) return;

        const ctx = document.getElementById("classPerformanceChart");
        if (!ctx) return;

        if (state.chartInstance) {
            state.chartInstance.destroy();
        }

        const labels = batch.results.map(r => r.student_name);
        const scores = batch.results.map(r => r.percentage);
        const confidences = batch.results.map(r => r.overall_confidence_score);

        state.chartInstance = new window.Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Grade Score (%)",
                        data: scores,
                        backgroundColor: "rgba(99, 102, 241, 0.75)",
                        borderColor: "#6366f1",
                        borderWidth: 1.5,
                        borderRadius: 6,
                        barPercentage: 0.55
                    },
                    {
                        label: "AI Confidence (%)",
                        data: confidences,
                        backgroundColor: "rgba(16, 185, 129, 0.75)",
                        borderColor: "#10b981",
                        borderWidth: 1.5,
                        borderRadius: 6,
                        barPercentage: 0.55
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "rgba(13, 19, 34, 0.95)",
                        titleColor: "#ffffff",
                        bodyColor: "#cbd5e1",
                        borderColor: "rgba(255, 255, 255, 0.15)",
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: "rgba(255, 255, 255, 0.05)"
                        },
                        ticks: {
                            color: "#94a3b8",
                            font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 }
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: "#f1f5f9",
                            font: { family: "'Plus Jakarta Sans', sans-serif", size: 12, weight: "bold" }
                        }
                    }
                }
            }
        });
    }

    // -------------------------------------------------------------------------
    // 7. Student Detail Modal Inspector (Tabs & Scan Preview)
    // -------------------------------------------------------------------------
    function showStudentDetail(student) {
        modalStudentAvatar.textContent = getInitials(student.student_name);
        modalStudentName.textContent = student.student_name;

        const isAiDirect = student.evaluation_mode === "ai_direct";
        modalModeBadge.textContent = isAiDirect ? "✨ Grounded Google Data" : "📄 Master Answer Key";
        modalStudentSub.textContent = `${student.file_name} • Score: ${student.total_score}/${student.max_possible_score} (${student.percentage}%) • Confidence: ${student.overall_confidence_score}%`;

        // Tab 1: Rubric breakdown
        let rubricHtml = "";

        if (student.requires_manual_review && student.review_reasons.length > 0) {
            rubricHtml += `
                <div class="detail-review-banner">
                    <strong>⚠️ Teacher Audit Flagged:</strong>
                    <ul>
                        ${student.review_reasons.map(r => `<li>${escapeHtml(r)}</li>`).join("")}
                    </ul>
                </div>
            `;
        }

        if (student.summary_feedback) {
            rubricHtml += `
                <div class="detail-summary-card">
                    <strong>Teacher Feedback Summary:</strong> ${escapeHtml(student.summary_feedback)}
                </div>
            `;
        }

        rubricHtml += `<div class="detail-q-grid">`;
        student.question_evaluations.forEach(q => {
            const conceptsCoveredHtml = (q.key_concepts_covered || []).map(c =>
                `<span class="concept-chip concept-covered">✓ ${escapeHtml(c)}</span>`
            ).join("");

            const conceptsMissingHtml = (q.missing_concepts || []).map(m =>
                `<span class="concept-chip concept-missing">✗ ${escapeHtml(m)}</span>`
            ).join("");

            rubricHtml += `
                <div class="detail-q-card">
                    <div class="detail-q-header">
                        <span class="detail-q-title">${escapeHtml(q.question_id)}</span>
                        <span class="detail-q-marks-pill">${q.marks_awarded} / ${q.max_marks} marks</span>
                    </div>

                    <div class="detail-transcription-box">
                        <small style="color:var(--text-muted);display:block;margin-bottom:3px;font-style:normal;">Transcribed from student handwriting:</small>
                        "${escapeHtml(q.student_transcription)}"
                    </div>

                    <div class="detail-concepts-row">
                        ${conceptsCoveredHtml}
                        ${conceptsMissingHtml}
                    </div>

                    <div class="detail-feedback-text">
                        <strong>Feedback:</strong> ${escapeHtml(q.feedback)}
                    </div>
                </div>
            `;
        });
        rubricHtml += `</div>`;
        tabRubric.innerHTML = rubricHtml;

        // Tab 2: Scan preview
        if (student.preview_url) {
            scanPreviewImage.src = student.preview_url;
            scanDownloadBtn.href = student.preview_url;
            scanFileName.textContent = `${student.file_name} — High-Res Stitched Multi-Page Scan`;
            tabScan.querySelector(".scan-viewer-box").style.display = "flex";
        } else {
            tabScan.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-muted)">Preview scan not available for this submission.</div>`;
        }

        // Tab 3: Diagnostics
        diagnosticsContent.innerHTML = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
                <div class="glass-card" style="padding:18px;">
                    <div style="font-size:0.8rem;color:var(--text-muted);margin-bottom:4px">Overall Confidence</div>
                    <div style="font-size:1.8rem;font-weight:800;color:#10b981">${student.overall_confidence_score}%</div>
                    <p style="font-size:0.78rem;color:var(--text-secondary);margin-top:6px">Probability of flawless transcription and rubric alignment.</p>
                </div>
                <div class="glass-card" style="padding:18px;">
                    <div style="font-size:0.8rem;color:var(--text-muted);margin-bottom:4px">Average Legibility</div>
                    <div style="font-size:1.8rem;font-weight:800;color:#6366f1">${student.average_legibility}%</div>
                    <p style="font-size:0.78rem;color:var(--text-secondary);margin-top:6px">Clarity, penmanship stroke definition, and page scan resolution.</p>
                </div>
            </div>
            <div class="glass-card" style="padding:18px;">
                <h4 style="font-size:0.92rem;font-weight:700;color:white;margin-bottom:8px">Teacher Audit Heuristics</h4>
                <p style="font-size:0.82rem;color:var(--text-secondary);line-height:1.5">
                    ${student.requires_manual_review
                        ? "This submission has been flagged for manual verification because one or more questions had low handwriting legibility or border-line confidence scores."
                        : "All questions scored with high confidence above the 70% threshold. Handwriting transcription was verified accurately without ambiguities."
                    }
                </p>
            </div>
        `;

        // Switch to Rubric tab by default
        switchModalTab("tabRubric");

        detailModal.style.display = "flex";
        initLucide();
    }

    function setupModals() {
        btnCloseModal.addEventListener("click", () => detailModal.style.display = "none");
        window.addEventListener("click", e => {
            if (e.target === detailModal) detailModal.style.display = "none";
            if (e.target === settingsModal) settingsModal.style.display = "none";
        });

        // Modal Tab Switcher
        modalTabs.forEach(tab => {
            tab.addEventListener("click", () => {
                switchModalTab(tab.getAttribute("data-tab"));
            });
        });

        // Settings Modal
        btnOpenSettings.addEventListener("click", () => {
            settingsStatus.style.display = "none";
            settingsModal.style.display = "flex";
            initLucide();
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
                    settingsStatus.className = "status-alert-box success";
                    settingsStatus.textContent = "Configuration updated successfully!";
                    settingsStatus.style.display = "block";
                    setTimeout(() => {
                        settingsModal.style.display = "none";
                        checkApiStatus();
                    }, 800);
                }
            } catch (err) {
                settingsStatus.className = "status-alert-box error";
                settingsStatus.textContent = err.message;
                settingsStatus.style.display = "block";
            }
        });

        if (btnTestApi) {
            btnTestApi.addEventListener("click", async () => {
                btnTestApi.textContent = "Testing...";
                try {
                    const res = await fetch("/api/test-gemini", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ api_key: settingApiKey.value.trim() || undefined })
                    });
                    const d = await res.json();
                    if (d.success) {
                        settingsStatus.className = "status-alert-box success";
                        settingsStatus.textContent = `✓ Connected to ${settingModel.value}: ${d.reply}`;
                    } else {
                        settingsStatus.className = "status-alert-box error";
                        settingsStatus.textContent = `Connection failed: ${d.message}`;
                    }
                    settingsStatus.style.display = "block";
                } catch (e) {
                    settingsStatus.className = "status-alert-box error";
                    settingsStatus.textContent = `Error: ${e.message}`;
                    settingsStatus.style.display = "block";
                } finally {
                    btnTestApi.textContent = "Test Connection";
                }
            });
        }
    }

    function switchModalTab(tabId) {
        modalTabs.forEach(t => {
            t.classList.toggle("active", t.getAttribute("data-tab") === tabId);
        });
        tabRubric.style.display = (tabId === "tabRubric") ? "block" : "none";
        tabScan.style.display = (tabId === "tabScan") ? "block" : "none";
        tabAudit.style.display = (tabId === "tabAudit") ? "block" : "none";
        initLucide();
    }

    // -------------------------------------------------------------------------
    // Utilities
    // -------------------------------------------------------------------------
    function getInitials(name) {
        if (!name) return "ST";
        const parts = name.trim().split(" ");
        if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
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
