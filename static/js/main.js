/**
 * ResumeIQ — main.js
 * ===================
 * Handles all frontend interactions:
 *   - File drag-and-drop + browse
 *   - Job description character count
 *   - POST /analyze API call
 *   - Loading animation with step progression
 *   - Results rendering: score ring, bars, skill tags, charts, ATS, courses
 */

"use strict";

// ── DOM references ─────────────────────────────────────────────────────────
const uploadZone    = document.getElementById("uploadZone");
const resumeFile    = document.getElementById("resumeFile");
const browseBtn     = document.getElementById("browseBtn");
const fileSelected  = document.getElementById("fileSelected");
const fileNameEl    = document.getElementById("fileName");
const jobDescription= document.getElementById("jobDescription");
const charCount     = document.getElementById("charCount");
const analyzeBtn    = document.getElementById("analyzeBtn");
const clearBtn      = document.getElementById("clearBtn");
const errorBanner   = document.getElementById("errorBanner");
const errorText     = document.getElementById("errorText");

const uploadSection = document.getElementById("uploadSection");
const loadingState  = document.getElementById("loadingState");
const resultsSection= document.getElementById("resultsSection");
const reanalyzeBtn  = document.getElementById("reanalyzeBtn");
const downloadPdfBtn= document.getElementById("downloadPdfBtn");

let lastAnalysisData = null;
let lastJobDescription = "";

// Score elements
const scoreNumber   = document.getElementById("scoreNumber");
const scoreLabel    = document.getElementById("scoreLabel");
const ringFill      = document.getElementById("ringFill");
const matchedBar    = document.getElementById("matchedBar");
const missingBar    = document.getElementById("missingBar");
const matchedCount  = document.getElementById("matchedCount");
const missingCount  = document.getElementById("missingCount");

// Skills
const matchedSkillsTags = document.getElementById("matchedSkillsTags");
const missingSkillsTags = document.getElementById("missingSkillsTags");

// ATS
const atsScoreBadge = document.getElementById("atsScoreBadge");
const atsFlags      = document.getElementById("atsFlags");
const atsSuggestions= document.getElementById("atsSuggestions");

// Recs
const recsGrid      = document.getElementById("recsGrid");
const recsSection   = document.getElementById("recsSection");

// Chart instances — kept so we can destroy before re-render
let barChartInstance   = null;
let donutChartInstance = null;

// ── File Upload ─────────────────────────────────────────────────────────────

browseBtn.addEventListener("click", () => resumeFile.click());
uploadZone.addEventListener("click", (e) => {
  if (e.target !== browseBtn) resumeFile.click();
});

resumeFile.addEventListener("change", () => {
  const file = resumeFile.files[0];
  if (file) setFileSelected(file.name);
});

// Drag-and-drop
uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("drag-over");
});
uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("drag-over");
});
uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) {
    // Assign to the file input so FormData picks it up
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    resumeFile.files = dataTransfer.files;
    setFileSelected(file.name);
  }
});

function setFileSelected(name) {
  fileNameEl.textContent = name;
  fileSelected.hidden = false;
  checkFormReady();
}

// ── Job description character count ────────────────────────────────────────

jobDescription.addEventListener("input", () => {
  const len = jobDescription.value.length;
  charCount.textContent = `${len} character${len !== 1 ? "s" : ""}`;
  checkFormReady();
});

function checkFormReady() {
  const hasFile = resumeFile.files && resumeFile.files.length > 0;
  const hasJD   = jobDescription.value.trim().length >= 50;
  analyzeBtn.disabled = !(hasFile && hasJD);
}

// ── Clear button ────────────────────────────────────────────────────────────

clearBtn.addEventListener("click", resetForm);

function resetForm() {
  resumeFile.value = "";
  fileSelected.hidden = true;
  fileNameEl.textContent = "";
  jobDescription.value = "";
  charCount.textContent = "0 characters";
  analyzeBtn.disabled = true;
  hideError();
  showSection("upload");
}

// ── Analyze ─────────────────────────────────────────────────────────────────

analyzeBtn.addEventListener("click", runAnalysis);

async function runAnalysis() {
  hideError();
  showSection("loading");
  animateLoadingSteps();

  const formData = new FormData();
  formData.append("resume", resumeFile.files[0]);
  formData.append("job_description", jobDescription.value.trim());

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body: formData,
    });

    const textData = await response.text();
    let data;
    try {
      data = JSON.parse(textData);
    } catch (e) {
      showSection("upload");
      showError(`Server crashed. Raw response: ${textData.substring(0, 150)}...`);
      return;
    }

    if (!response.ok) {
      showSection("upload");
      showError(data.error || "An unexpected error occurred. Please try again.");
      return;
    }

    lastAnalysisData = data;
    lastJobDescription = jobDescription.value.trim();

    renderResults(data);
    showSection("results");

  } catch (err) {
    showSection("upload");
    showError(`Network error or crash: ${err.message}`);
  }
}

// ── Loading step animation ──────────────────────────────────────────────────

function animateLoadingSteps() {
  const steps = ["step1", "step2", "step3", "step4"];
  let current = 0;

  steps.forEach((id) => {
    const el = document.getElementById(id);
    el.classList.remove("active", "done");
  });

  document.getElementById(steps[0]).classList.add("active");

  const interval = setInterval(() => {
    if (current < steps.length - 1) {
      document.getElementById(steps[current]).classList.replace("active", "done");
      current++;
      document.getElementById(steps[current]).classList.add("active");
    } else {
      clearInterval(interval);
    }
  }, 900);
}

// ── Render Results ──────────────────────────────────────────────────────────

function renderResults(data) {
  renderScore(data.match_score, data.matched_skills, data.missing_skills);
  renderSkillTags(data.matched_skills, data.missing_skills);
  renderCharts(data.matched_skills, data.missing_skills, data.jd_skills);
  renderATS(data.ats);
  renderRecommendations(data.recommendations);
}

// Score ring + bars
function renderScore(score, matched, missing) {
  // Animate number counter
  animateCounter(scoreNumber, 0, score, 1200);

  // Score label
  if      (score >= 80) { scoreLabel.textContent = "🎯 Excellent match — you're highly qualified!"; }
  else if (score >= 60) { scoreLabel.textContent = "👍 Good match — a few gaps to address"; }
  else if (score >= 40) { scoreLabel.textContent = "🔧 Moderate match — skills development recommended"; }
  else                  { scoreLabel.textContent = "⚠️ Low match — significant skill gaps identified"; }

  // Ring fill: circumference = 2π × 52 ≈ 327
  const circumference = 327;
  const offset = circumference - (score / 100) * circumference;
  setTimeout(() => {
    ringFill.style.strokeDashoffset = offset;
    // Color by score
    if      (score >= 80) ringFill.style.stroke = "#00D4AA";
    else if (score >= 60) ringFill.style.stroke = "#F5C542";
    else                  ringFill.style.stroke = "#FF5C6A";
  }, 100);

  // Bars
  const total = matched.length + missing.length;
  if (total > 0) {
    setTimeout(() => {
      matchedBar.style.width = `${(matched.length / total) * 100}%`;
      missingBar.style.width = `${(missing.length / total) * 100}%`;
    }, 200);
  }
  matchedCount.textContent = matched.length;
  missingCount.textContent = missing.length;
}

function animateCounter(el, start, end, duration) {
  const startTime = performance.now();
  function update(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (end - start) * eased);
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// Skill tags
function renderSkillTags(matched, missing) {
  matchedSkillsTags.innerHTML = "";
  missingSkillsTags.innerHTML = "";

  matched.forEach((skill) => {
    const tag = document.createElement("span");
    tag.className = "skill-tag skill-tag--matched";
    tag.textContent = skill;
    matchedSkillsTags.appendChild(tag);
  });

  missing.forEach((skill) => {
    const tag = document.createElement("span");
    tag.className = "skill-tag skill-tag--missing";
    tag.textContent = skill;
    missingSkillsTags.appendChild(tag);
  });

  if (!matched.length) matchedSkillsTags.innerHTML = '<span style="color:var(--text-3);font-size:13px">None matched</span>';
  if (!missing.length) missingSkillsTags.innerHTML = '<span style="color:var(--teal);font-size:13px">🎉 No skill gaps detected!</span>';
}

// Charts
function renderCharts(matched, missing, jdSkills) {
  // Destroy previous instances if re-analyzing
  if (barChartInstance)   { barChartInstance.destroy();   barChartInstance = null; }
  if (donutChartInstance) { donutChartInstance.destroy(); donutChartInstance = null; }

  // Bar chart — top skills
  const allSkills = [...new Set([...matched, ...missing])].slice(0, 12);
  const barColors = allSkills.map((s) => matched.includes(s) ? "#00D4AA" : "#FF5C6A");
  const barValues = allSkills.map((s) => matched.includes(s) ? 1 : 0);

  const barCtx = document.getElementById("skillsBarChart").getContext("2d");
  barChartInstance = new Chart(barCtx, {
    type: "bar",
    data: {
      labels: allSkills,
      datasets: [{
        label: "Match Status",
        data: barValues,
        backgroundColor: barColors,
        borderRadius: 6,
        barThickness: 18,
      }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: {
        callbacks: {
          label: (ctx) => matched.includes(ctx.label) ? "✅ Matched" : "❌ Missing"
        }
      }},
      scales: {
        x: {
          display: false, max: 1.2,
          grid: { color: "#1E2D45" }
        },
        y: {
          ticks: { color: "#8B9DBF", font: { size: 11, family: "'DM Sans', sans-serif" } },
          grid: { color: "#1E2D45" }
        }
      }
    }
  });

  // Donut chart
  const donutCtx = document.getElementById("matchDonutChart").getContext("2d");
  donutChartInstance = new Chart(donutCtx, {
    type: "doughnut",
    data: {
      labels: ["Matched", "Missing"],
      datasets: [{
        data: [matched.length, missing.length],
        backgroundColor: ["#00D4AA", "#FF5C6A"],
        borderColor: ["#00A886", "#CC4055"],
        borderWidth: 2,
        hoverOffset: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "65%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#8B9DBF", font: { size: 12, family: "'DM Sans', sans-serif" }, padding: 16 }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${ctx.raw} skill${ctx.raw !== 1 ? "s" : ""}`
          }
        }
      }
    }
  });
}

// ATS
function renderATS(ats) {
  if (!ats) return;

  const score = ats.ats_score;
  atsScoreBadge.textContent = `ATS Score: ${score}/100`;
  atsScoreBadge.className = "ats-score-badge";
  if      (score >= 75) atsScoreBadge.classList.add("good");
  else if (score >= 50) atsScoreBadge.classList.add("warn");
  else                  atsScoreBadge.classList.add("bad");

  atsFlags.innerHTML = "";
  (ats.flags || []).forEach((flag) => {
    const div = document.createElement("div");
    div.className = "ats-flag";
    div.innerHTML = `<span>⚠️</span><span>${formatAtsFlag(flag)}</span>`;
    atsFlags.appendChild(div);
  });

  atsSuggestions.innerHTML = "";
  (ats.suggestions || []).forEach((sug) => {
    const div = document.createElement("div");
    div.className = "ats-suggestion";
    div.innerHTML = `<span>💡</span><span>${sug}</span>`;
    atsSuggestions.appendChild(div);
  });

  if (!ats.flags?.length && !ats.suggestions?.length) {
    atsSuggestions.innerHTML = '<div class="ats-suggestion"><span>✅</span><span>No ATS issues detected.</span></div>';
  }
}

function formatAtsFlag(flag) {
  const labels = {
    tables_detected:   "Tables detected — ATS parsers struggle with tabular content",
    images_detected:   "Images / graphics detected — text inside images cannot be read by ATS",
    multi_column_layout: "Multi-column layout detected — may cause content to be read out of order",
    image_resume:      "This is an image-based resume — not ATS-parseable",
  };
  return labels[flag] || flag.replace(/_/g, " ");
}

// Recommendations
function renderRecommendations(recs) {
  recsGrid.innerHTML = "";
  if (!recs || !recs.length) {
    recsSection.hidden = true;
    return;
  }
  recsSection.hidden = false;

  recs.forEach((rec) => {
    const card = document.createElement("a");
    card.className = "rec-card";
    card.href = rec.url;
    card.target = "_blank";
    card.rel = "noopener noreferrer";
    card.innerHTML = `
      <div class="rec-skill">${rec.skill}</div>
      <div class="rec-title">${rec.title}</div>
      <div class="rec-meta">
        <span class="rec-platform">${rec.platform}</span>
        <span class="rec-level ${rec.level}">${rec.level}</span>
      </div>
    `;
    recsGrid.appendChild(card);
  });
}

// ── Actions ─────────────────────────────────────────────────────────────────

reanalyzeBtn.addEventListener("click", resetForm);

if (downloadPdfBtn) {
  downloadPdfBtn.addEventListener("click", async () => {
    if (!lastAnalysisData) return;
    
    const btnText = downloadPdfBtn.innerHTML;
    downloadPdfBtn.innerHTML = "⏳ Generating PDF...";
    downloadPdfBtn.disabled = true;

    try {
      const payload = {
        job_description: lastJobDescription,
        match_score: lastAnalysisData.match_score,
        matched_skills: lastAnalysisData.matched_skills,
        missing_skills: lastAnalysisData.missing_skills,
        recommendations: lastAnalysisData.recommendations,
        ats: lastAnalysisData.ats
      };

      const response = await fetch("/download-report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error("Failed to generate PDF");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;
      a.download = "ResumeIQ_Evaluation_Report.pdf";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Error generating PDF: " + err.message);
    } finally {
      downloadPdfBtn.innerHTML = btnText;
      downloadPdfBtn.disabled = false;
    }
  });
}

// ── Section visibility ──────────────────────────────────────────────────────

function showSection(section) {
  uploadSection.hidden   = section !== "upload";
  loadingState.hidden    = section !== "loading";
  resultsSection.hidden  = section !== "results";
}

function showError(msg) {
  errorText.textContent = msg;
  errorBanner.hidden = false;
}

function hideError() {
  errorBanner.hidden = true;
  errorText.textContent = "";
}
