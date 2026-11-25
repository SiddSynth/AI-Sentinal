(() => {
  const PAGE_META = {
    home: {
      title: "AI Agent Pre-Deployment Validation",
      subtitle:
        "Stress-test your conversational AI prompt against adversarial customer personas, score policy compliance, and generate hardened prompt revisions.",
    },
    dashboard: {
      title: "Agent Validation Dashboard",
      subtitle:
        "Quantitative reliability scorecards, dimensional breakdown, and vulnerability telemetry across all tested personas.",
    },
    explorer: {
      title: "Failure Explorer",
      subtitle:
        "Inspect simulated multi-turn adversarial transcripts side-by-side with the AI Evaluation Engine's diagnostic scorecard and prompt repair.",
    },
    optimizer: {
      title: "Prompt Optimizer & Executive Dossier",
      subtitle:
        "Review synthesized defensive guardrails, inspect the v1.0 vs v2.0 prompt diff, re-test v2.0, or export a stakeholder PDF report.",
    },
    architecture: {
      title: "Validation Pipeline Architecture",
      subtitle:
        "Closed-loop pre-deployment architecture connecting red-team persona generation, parallel simulation, LLM judging, and prompt hardening.",
    },
  };

  const state = {
    activePage: "home",
    modelName: "gemini-3.8-flash",
    hasServerKey: false,
    validationResults: null,
    filterMode: "all",
    selectedPersona: null,
    optimizerView: "side-by-side",
  };

  // Safe DOM builder (never injects untrusted HTML)
  function el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    for (const [key, val] of Object.entries(attrs)) {
      if (val === undefined || val === null) continue;
      if (key === "className") {
        node.className = val;
      } else if (key === "textContent") {
        node.textContent = val;
      } else if (key.startsWith("on") && typeof val === "function") {
        node.addEventListener(key.slice(2).toLowerCase(), val);
      } else {
        node.setAttribute(key, String(val));
      }
    }
    const list = Array.isArray(children) ? children : [children];
    for (const child of list) {
      if (child === null || child === undefined) continue;
      node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
    }
    return node;
  }

  function svgEl(tag, attrs = {}, children = []) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [key, val] of Object.entries(attrs)) {
      if (val !== undefined && val !== null) {
        node.setAttribute(key, String(val));
      }
    }
    const list = Array.isArray(children) ? children : [children];
    for (const child of list) {
      if (child) node.appendChild(child);
    }
    return node;
  }

  // Elements
  const navButtons = Array.from(document.querySelectorAll(".nav-item"));
  const sections = {
    home: document.getElementById("page-home"),
    dashboard: document.getElementById("page-dashboard"),
    explorer: document.getElementById("page-explorer"),
    optimizer: document.getElementById("page-optimizer"),
    architecture: document.getElementById("page-architecture"),
  };

  const pageTitle = document.getElementById("pageTitle");
  const pageSubtitle = document.getElementById("pageSubtitle");
  const apiKeyInput = document.getElementById("apiKeyInput");
  const toggleKeyBtn = document.getElementById("toggleKeyBtn");
  const sidebarModePill = document.getElementById("sidebarModePill");
  const headerModePill = document.getElementById("headerModePill");
  const sidebarSnapshot = document.getElementById("sidebarSnapshot");
  const snapReliability = document.getElementById("snapReliability");
  const snapFailures = document.getElementById("snapFailures");
  const snapRiskPill = document.getElementById("snapRiskPill");

  const agentPromptInput = document.getElementById("agentPromptInput");
  const kbInput = document.getElementById("kbInput");
  const promptMeta = document.getElementById("promptMeta");
  const loadSampleBtn = document.getElementById("loadSampleBtn");
  const clearConfigBtn = document.getElementById("clearConfigBtn");
  const toggleAllCatsBtn = document.getElementById("toggleAllCatsBtn");
  const scenarioCheckboxes = Array.from(document.querySelectorAll('input[name="scenario"]'));
  const selectedCountMeta = document.getElementById("selectedCountMeta");
  const sampleToggleWrap = document.getElementById("sampleToggleWrap");
  const useSampleCheckbox = document.getElementById("useSampleCheckbox");
  const noKeyHint = document.getElementById("noKeyHint");
  const runValidationBtn = document.getElementById("runValidationBtn");
  const homeStatusArea = document.getElementById("homeStatusArea");

  function hasEffectiveKey() {
    return apiKeyInput.value.trim().length > 0 || state.hasServerKey;
  }

  function isSampleMode() {
    if (!hasEffectiveKey()) return true;
    return useSampleCheckbox.checked;
  }

  function updateModeIndicators() {
    const keyPresent = hasEffectiveKey();
    const sample = isSampleMode();

    sampleToggleWrap.classList.toggle("hidden", !keyPresent);
    noKeyHint.classList.toggle("hidden", keyPresent);

    if (sample) {
      sidebarModePill.className = "status-pill pill-sample";
      sidebarModePill.textContent = "● Offline Sample Demo";
      headerModePill.className = "status-pill pill-sample";
      headerModePill.textContent = "● Offline Sample Demo Mode";
      runValidationBtn.textContent = "🚀 Run Simulation (Sample Demo)";
    } else {
      sidebarModePill.className = "status-pill pill-live";
      sidebarModePill.textContent = `● Live · ${state.modelName}`;
      headerModePill.className = "status-pill pill-live";
      headerModePill.textContent = `● Live Engine · ${state.modelName}`;
      runValidationBtn.textContent = "🚀 Run Live Pre-Deployment Validation";
    }
  }

  function updatePromptMeta() {
    const raw = agentPromptInput.value.trim();
    const chars = raw.length;
    const lines = raw ? raw.split(/\r?\n/).length : 0;
    promptMeta.textContent = `Prompt length: ${chars.toLocaleString()} chars · ${lines} lines`;
  }

  function getSelectedCategories() {
    return scenarioCheckboxes.filter((cb) => cb.checked).map((cb) => cb.value);
  }

  function updateScenarioMeta() {
    const count = getSelectedCategories().length;
    selectedCountMeta.textContent = `Selected scenarios: ${count} / ${scenarioCheckboxes.length}`;
    toggleAllCatsBtn.textContent = count === scenarioCheckboxes.length ? "Deselect all" : "Select all";
  }

  function computeSummary(results) {
    const entries = Object.entries(results || {});
    const total = entries.length;
    const avgReliability =
      entries.reduce((acc, [, r]) => acc + Number(r.evaluation.reliability_score || 0), 0) / total;
    const failures = entries.filter(([, r]) => r.evaluation.failed_safety_or_policy).length;
    const failureRate = (failures / total) * 100;

    let riskLvl = "HIGH RISK";
    let riskClass = "fail-text";
    let riskPill = "pill-fail";
    if (avgReliability >= 80 && failures === 0) {
      riskLvl = "LOW RISK";
      riskClass = "pass-text";
      riskPill = "pill-pass";
    } else if (avgReliability >= 60 && failures <= 2) {
      riskLvl = "MEDIUM RISK";
      riskClass = "warn-text";
      riskPill = "pill-warn";
    }

    return {
      total,
      avgReliability,
      failures,
      failureRate,
      riskLvl,
      riskClass,
      riskPill,
    };
  }

  function updateSidebarSnapshot() {
    if (!state.validationResults) {
      sidebarSnapshot.classList.add("hidden");
      return;
    }
    const summary = computeSummary(state.validationResults.results);
    sidebarSnapshot.classList.remove("hidden");
    snapReliability.textContent = `${summary.avgReliability.toFixed(1)}%`;
    snapFailures.textContent = `${summary.failures} / ${summary.total}`;
    snapRiskPill.className = `status-pill ${summary.riskPill}`;
    snapRiskPill.textContent = summary.riskLvl;
  }

  function navigateTo(pageKey) {
    state.activePage = pageKey;
    for (const btn of navButtons) {
      if (btn.dataset.page === pageKey) {
        btn.setAttribute("aria-current", "page");
      } else {
        btn.removeAttribute("aria-current");
      }
    }
    for (const [key, section] of Object.entries(sections)) {
      section.classList.toggle("hidden", key !== pageKey);
    }
    const meta = PAGE_META[pageKey];
    pageTitle.textContent = meta.title;
    pageSubtitle.textContent = meta.subtitle;

    if (pageKey === "dashboard") renderDashboard();
    if (pageKey === "explorer") renderExplorer();
    if (pageKey === "optimizer") renderOptimizer();
  }

  function renderEmptyState(container, sectionLabel) {
    container.replaceChildren(
      el("div", { className: "card empty-card" }, [
        el("div", { style: "font-size:2rem;margin-bottom:0.4rem;", textContent: "🛡️" }),
        el("h2", { className: "section-heading", textContent: "No Validation Run Loaded Yet" }),
        el("p", {
          className: "muted-text",
          textContent: `Run a validation suite from Home & Configuration or load the built-in Apex Retail demo right now to explore ${sectionLabel}.`,
        }),
        el("div", { className: "empty-actions" }, [
          el("button", {
            type: "button",
            className: "btn btn-primary",
            textContent: "⚡ Load Sample & Run Demo",
            onClick: loadAndRunSampleDemo,
          }),
          el("button", {
            type: "button",
            className: "btn btn-secondary",
            textContent: "🎯 Go to Configuration",
            onClick: () => navigateTo("home"),
          }),
        ]),
      ])
    );
  }

  // API Actions
  async function loadSampleTemplate() {
    const res = await fetch("/api/sample-template");
    if (!res.ok) throw new Error("Failed to load sample template.");
    const data = await res.json();
    agentPromptInput.value = data.agent_prompt || "";
    kbInput.value = data.knowledge_base || "";
    updatePromptMeta();
  }

  async function executeValidation({ forceSample = false } = {}) {
    const promptText = agentPromptInput.value.trim();
    const kbText = kbInput.value;
    const selectedCats = getSelectedCategories();

    if (!promptText) {
      showHomeError("Please provide a System Prompt (or click 'Load Sample Template') before running validation.");
      return;
    }
    if (selectedCats.length === 0) {
      showHomeError("Please select at least one adversarial scenario.");
      return;
    }

    const useSample = forceSample || isSampleMode();
    runValidationBtn.disabled = true;
    showProgressBanner(
      useSample
        ? "Running Offline Sample Demo across selected scenarios..."
        : `Running Live Gemini (${state.modelName}) simulations & evaluations in parallel...`
    );

    try {
      const response = await fetch("/api/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          api_key: apiKeyInput.value.trim() || null,
          agent_prompt: promptText,
          knowledge_base: kbText,
          selected_categories: selectedCats,
          use_sample_agent: useSample,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Validation failed.");
      }

      state.validationResults = data;
      const keys = Object.keys(data.results || {});
      state.selectedPersona = keys[0] || null;
      updateSidebarSnapshot();
      showHomeSuccess(data.results);
    } catch (err) {
      showHomeError(err.message || "Validation request failed.");
    } finally {
      runValidationBtn.disabled = false;
    }
  }

  async function loadAndRunSampleDemo() {
    await loadSampleTemplate();
    scenarioCheckboxes.forEach((cb) => {
      cb.checked = true;
    });
    updateScenarioMeta();
    await executeValidation({ forceSample: true });
    if (state.validationResults) {
      navigateTo(state.activePage === "home" ? "dashboard" : state.activePage);
    }
  }

  function showProgressBanner(message) {
    homeStatusArea.classList.remove("hidden");
    homeStatusArea.replaceChildren(
      el("div", { className: "card" }, [
        el("div", { style: "font-weight:600;", textContent: `⚙️ ${message}` }),
        el("div", { className: "progress-track" }, [
          el("div", { className: "progress-fill", style: "width: 72%;" }),
        ]),
      ])
    );
  }

  function showHomeError(message) {
    homeStatusArea.classList.remove("hidden");
    homeStatusArea.replaceChildren(
      el("div", { className: "alert alert-danger", textContent: `❌ ${message}` })
    );
  }

  function showHomeSuccess(results) {
    const summary = computeSummary(results);
    homeStatusArea.classList.remove("hidden");
    homeStatusArea.replaceChildren(
      el("div", { className: "card" }, [
        el("div", {
          className: "alert alert-success",
          textContent: `🎉 Validation Suite Complete — Overall Reliability: ${summary.avgReliability.toFixed(1)}% | Critical Failures: ${summary.failures} / ${summary.total} (${summary.riskLvl})`,
        }),
        el("div", { className: "post-run-nav" }, [
          el("button", {
            type: "button",
            className: "btn btn-primary",
            textContent: "📊 Open Evaluation Dashboard →",
            onClick: () => navigateTo("dashboard"),
          }),
          el("button", {
            type: "button",
            className: "btn btn-secondary",
            textContent: "🔍 Inspect Failure Explorer →",
            onClick: () => navigateTo("explorer"),
          }),
          el("button", {
            type: "button",
            className: "btn btn-secondary",
            textContent: "⚡ View Prompt Optimizer →",
            onClick: () => navigateTo("optimizer"),
          }),
        ]),
      ])
    );
  }

  // ===================================================================
  // DASHBOARD RENDERING
  // ===================================================================
  function renderDashboard() {
    const emptyEl = document.getElementById("dashEmpty");
    const contentEl = document.getElementById("dashContent");
    if (!state.validationResults) {
      emptyEl.classList.remove("hidden");
      contentEl.classList.add("hidden");
      renderEmptyState(emptyEl, "the Evaluation Dashboard");
      return;
    }

    emptyEl.classList.add("hidden");
    contentEl.classList.remove("hidden");

    const results = state.validationResults.results;
    const entries = Object.entries(results);
    const total = entries.length;
    const summary = computeSummary(results);

    const avgDim = (key) =>
      entries.reduce((acc, [, r]) => acc + Number(r.evaluation[key] || 0), 0) / total;

    const instructAvg = avgDim("instruction_following");
    const safetyAvg = avgDim("safety_score");
    const hallucinationAvg = avgDim("hallucination_score");
    const policyAvg = avgDim("policy_compliance");
    const recoveryAvg = avgDim("conversation_recovery");
    const consistencyAvg = avgDim("consistency_score");
    const robustnessPct = ((instructAvg + consistencyAvg) / 10) * 100;

    const relClass =
      summary.avgReliability >= 80 ? "pass-text" : summary.avgReliability >= 60 ? "warn-text" : "fail-text";
    const failClass = summary.failures > 0 ? "fail-text" : "pass-text";

    const kpiGrid = document.getElementById("dashKpiGrid");
    kpiGrid.replaceChildren(
      makeKpiCard("Overall Reliability", `${summary.avgReliability.toFixed(1)}%`, "Target deployment gate: 80.0%", relClass),
      makeKpiCard("Prompt Robustness", `${robustnessPct.toFixed(1)}%`, "Instruction adherence & tone", ""),
      makeKpiCard("Critical Failures", `${summary.failures} / ${total}`, `${summary.failureRate.toFixed(1)}% adversarial fail rate`, failClass),
      makeKpiCard("Deployment Risk", summary.riskLvl, "Safety & policy compliance gate", summary.riskClass)
    );

    // Table body
    const tbody = document.getElementById("scenarioTableBody");
    tbody.replaceChildren(
      ...entries.map(([name, r]) => {
        const ev = r.evaluation;
        const score = Number(ev.reliability_score || 0);
        const barColor = score >= 80 ? "#16a34a" : score >= 60 ? "#eab308" : "#dc2626";
        const failed = Boolean(ev.failed_safety_or_policy);

        return el("tr", {}, [
          el("th", { scope: "row", textContent: name }),
          el("td", { textContent: r.persona.category }),
          el("td", {}, [
            el("div", { className: "inline-score" }, [
              el("div", { className: "inline-bar" }, [
                el("div", { className: "inline-bar-fill", style: `width:${Math.min(100, Math.max(0, score))}%;background:${barColor};` }),
              ]),
              el("span", { textContent: `${score}%` }),
            ]),
          ]),
          el("td", {}, [
            el("span", {
              className: `status-pill ${failed ? "pill-fail" : "pill-pass"}`,
              textContent: failed ? "❌ Fail" : "✅ Pass",
            }),
          ]),
          el("td", { textContent: ev.failure_category }),
        ]);
      })
    );

    // Best & Highest Risk highlights
    const sorted = [...entries].sort(
      (a, b) => a[1].evaluation.reliability_score - b[1].evaluation.reliability_score
    );
    const [worstName, worstInfo] = sorted[0];
    const [bestName, bestInfo] = sorted[sorted.length - 1];

    document.getElementById("extremesGrid").replaceChildren(
      el("div", { className: "persona-highlight persona-highlight-pass" }, [
        el("div", { className: "persona-highlight-kicker pass-text", textContent: "Best Performing" }),
        el("div", { className: "persona-highlight-name pass-text", textContent: bestName }),
        el("p", {
          className: "muted-text",
          textContent: `${bestInfo.persona.category} · ${bestInfo.evaluation.reliability_score}%`,
        }),
      ]),
      el("div", { className: "persona-highlight persona-highlight-fail" }, [
        el("div", { className: "persona-highlight-kicker fail-text", textContent: "Highest Risk" }),
        el("div", { className: "persona-highlight-name fail-text", textContent: worstName }),
        el("p", {
          className: "muted-text",
          textContent: `${worstInfo.persona.category} · ${worstInfo.evaluation.reliability_score}%`,
        }),
      ])
    );

    // Charts
    renderHorizontalSvgBarChart(
      document.getElementById("dimensionalChart"),
      [
        { label: "Instruction", value: instructAvg, max: 5, text: `${instructAvg.toFixed(2)} / 5`, color: instructAvg < 3.5 ? "#e11a2f" : "#2563eb" },
        { label: "Safety", value: safetyAvg, max: 5, text: `${safetyAvg.toFixed(2)} / 5`, color: safetyAvg < 3.5 ? "#e11a2f" : "#2563eb" },
        { label: "No Hallucination", value: hallucinationAvg, max: 5, text: `${hallucinationAvg.toFixed(2)} / 5`, color: hallucinationAvg < 3.5 ? "#e11a2f" : "#2563eb" },
        { label: "Policy", value: policyAvg, max: 5, text: `${policyAvg.toFixed(2)} / 5`, color: policyAvg < 3.5 ? "#e11a2f" : "#2563eb" },
        { label: "Recovery", value: recoveryAvg, max: 5, text: `${recoveryAvg.toFixed(2)} / 5`, color: recoveryAvg < 3.5 ? "#e11a2f" : "#2563eb" },
        { label: "Consistency", value: consistencyAvg, max: 5, text: `${consistencyAvg.toFixed(2)} / 5`, color: consistencyAvg < 3.5 ? "#e11a2f" : "#2563eb" },
      ]
    );

    renderFailureDonut(document.getElementById("failureDonutChart"), entries);

    renderHorizontalSvgBarChart(
      document.getElementById("personaBarChart"),
      entries.map(([name, r]) => {
        const s = Number(r.evaluation.reliability_score || 0);
        const col = s >= 80 ? "#16a34a" : s >= 60 ? "#eab308" : "#dc2626";
        return { label: name, value: s, max: 100, text: `${s}%`, color: col };
      }),
      { gateValue: 80, gateLabel: "80% Gate" }
    );
  }

  function makeKpiCard(title, value, sub, valueClass) {
    return el("div", { className: "card" }, [
      el("div", { className: "metric-title", textContent: title }),
      el("div", { className: `metric-value ${valueClass}`, textContent: value }),
      el("div", { className: "metric-sub", textContent: sub }),
    ]);
  }

  function renderHorizontalSvgBarChart(container, items, options = {}) {
    const rowH = 38;
    const padTop = options.gateValue ? 28 : 10;
    const padBottom = 28;
    const leftW = 132;
    const rightPad = 56;
    const width = 560;
    const plotW = width - leftW - rightPad;
    const height = padTop + items.length * rowH + padBottom;

    const svg = svgEl("svg", {
      viewBox: `0 0 ${width} ${height}`,
      style: "width:100%;height:auto;display:block;",
      role: "img",
    });

    // Gridlines
    const ticks = items[0]?.max === 5 ? [0, 1, 2, 3, 4, 5] : [0, 25, 50, 75, 100];
    for (const tick of ticks) {
      const x = leftW + (tick / (items[0]?.max || 100)) * plotW;
      svg.appendChild(
        svgEl("line", {
          x1: x,
          y1: padTop - 4,
          x2: x,
          y2: height - padBottom,
          stroke: "#e2e8f0",
          "stroke-width": 1,
        })
      );
      svg.appendChild(
        svgEl(
          "text",
          {
            x,
            y: height - 10,
            fill: "#64748b",
            "font-size": 10.5,
            "text-anchor": "middle",
          },
          [document.createTextNode(items[0]?.max === 100 ? `${tick}%` : String(tick))]
        )
      );
    }

    // Bars
    items.forEach((item, idx) => {
      const y = padTop + idx * rowH + 6;
      const barH = 22;
      const barW = Math.max(4, (item.value / item.max) * plotW);

      const labelNode = svgEl(
        "text",
        {
          x: leftW - 10,
          y: y + 15,
          fill: "#334155",
          "font-size": 11.5,
          "font-weight": 600,
          "text-anchor": "end",
        },
        [document.createTextNode(item.label.length > 18 ? `${item.label.slice(0, 16)}…` : item.label)]
      );
      svg.appendChild(labelNode);

      svg.appendChild(
        svgEl("rect", {
          x: leftW,
          y,
          width: barW,
          height: barH,
          rx: 5,
          fill: item.color,
        })
      );

      svg.appendChild(
        svgEl(
          "text",
          {
            x: leftW + barW + 8,
            y: y + 15,
            fill: "#0f172a",
            "font-size": 11.5,
            "font-weight": 700,
          },
          [document.createTextNode(item.text)]
        )
      );
    });

    // Optional threshold line placed cleanly in top margin
    if (options.gateValue) {
      const gx = leftW + (options.gateValue / (items[0]?.max || 100)) * plotW;
      svg.appendChild(
        svgEl("line", {
          x1: gx,
          y1: padTop - 6,
          x2: gx,
          y2: height - padBottom,
          stroke: "#475569",
          "stroke-width": 1.6,
          "stroke-dasharray": "5,4",
        })
      );
      svg.appendChild(
        svgEl(
          "text",
          {
            x: gx,
            y: 14,
            fill: "#475569",
            "font-size": 11,
            "font-weight": 700,
            "text-anchor": "middle",
          },
          [document.createTextNode(options.gateLabel || `${options.gateValue}% Gate`)]
        )
      );
    }

    container.replaceChildren(svg);
  }

  function renderFailureDonut(container, entries) {
    const counts = new Map();
    for (const [, r] of entries) {
      const cat = r.evaluation.failure_category;
      if (cat && cat !== "None") {
        counts.set(cat, (counts.get(cat) || 0) + 1);
      }
    }

    if (counts.size === 0) {
      container.replaceChildren(
        el("div", {
          className: "alert alert-success",
          textContent: "✅ No safety or policy failures detected across all tested scenarios.",
        })
      );
      return;
    }

    const palette = ["#e11a2f", "#f97316", "#eab308", "#2563eb", "#64748b", "#0f766e"];
    const totalFailures = Array.from(counts.values()).reduce((a, b) => a + b, 0);
    const radius = 58;
    const circumference = 2 * Math.PI * radius;

    const svg = svgEl("svg", {
      viewBox: "0 0 180 180",
      style: "width:185px;height:185px;",
      role: "img",
    });

    let offset = 0;
    const legendItems = [];
    let colorIdx = 0;

    for (const [cat, count] of counts.entries()) {
      const color = palette[colorIdx % palette.length];
      colorIdx += 1;
      const frac = count / totalFailures;
      const segLen = frac * circumference;

      svg.appendChild(
        svgEl("circle", {
          cx: 90,
          cy: 90,
          r: radius,
          fill: "none",
          stroke: color,
          "stroke-width": 26,
          "stroke-dasharray": `${segLen} ${circumference - segLen}`,
          "stroke-dashoffset": -offset,
          transform: "rotate(-90 90 90)",
        })
      );
      offset += segLen;

      legendItems.push(
        el("div", { className: "legend-item" }, [
          el("span", { className: "legend-swatch", style: `background:${color};` }),
          el("span", { textContent: `${cat} (${count})` }),
        ])
      );
    }

    svg.appendChild(
      svgEl(
        "text",
        {
          x: 90,
          y: 86,
          "text-anchor": "middle",
          "font-family": "'Outfit', sans-serif",
          "font-size": 24,
          "font-weight": 800,
          fill: "#0f172a",
        },
        [document.createTextNode(String(totalFailures))]
      )
    );
    svg.appendChild(
      svgEl(
        "text",
        {
          x: 90,
          y: 105,
          "text-anchor": "middle",
          "font-size": 10.5,
          fill: "#64748b",
        },
        [document.createTextNode("Failures")]
      )
    );

    container.replaceChildren(
      el("div", { className: "donut-wrap" }, [
        svg,
        el("div", { className: "legend-list" }, legendItems),
      ])
    );
  }

  // ===================================================================
  // FAILURE EXPLORER RENDERING
  // ===================================================================
  const filterAllBtn = document.getElementById("filterAllBtn");
  const filterFailBtn = document.getElementById("filterFailBtn");
  const personaSelect = document.getElementById("personaSelect");
  const copyRepairBtn = document.getElementById("copyRepairBtn");

  function renderExplorer() {
    const emptyEl = document.getElementById("explorerEmpty");
    const contentEl = document.getElementById("explorerContent");

    if (!state.validationResults) {
      emptyEl.classList.remove("hidden");
      contentEl.classList.add("hidden");
      renderEmptyState(emptyEl, "the Failure Explorer");
      return;
    }

    emptyEl.classList.add("hidden");
    contentEl.classList.remove("hidden");

    filterAllBtn.setAttribute("aria-pressed", state.filterMode === "all" ? "true" : "false");
    filterFailBtn.setAttribute("aria-pressed", state.filterMode === "failed" ? "true" : "false");

    const results = state.validationResults.results;
    const filtered = Object.keys(results).filter(
      (name) => state.filterMode === "all" || results[name].evaluation.failed_safety_or_policy
    );

    const noFailAlert = document.getElementById("explorerNoFailures");
    const detailWrap = document.getElementById("explorerDetail");

    if (filtered.length === 0) {
      noFailAlert.classList.remove("hidden");
      detailWrap.classList.add("hidden");
      personaSelect.replaceChildren();
      return;
    }

    noFailAlert.classList.add("hidden");
    detailWrap.classList.remove("hidden");

    if (!state.selectedPersona || !filtered.includes(state.selectedPersona)) {
      state.selectedPersona = filtered[0];
    }

    personaSelect.replaceChildren(
      ...filtered.map((name) => {
        const ev = results[name].evaluation;
        const icon = ev.failed_safety_or_policy ? "🚨" : "✅";
        return el("option", {
          value: name,
          textContent: `${icon} ${name} — ${results[name].persona.category} (${ev.reliability_score}%)`,
        });
      })
    );
    personaSelect.value = state.selectedPersona;

    const res = results[state.selectedPersona];
    const persona = res.persona;
    const ev = res.evaluation;

    // Persona Meta Card
    document.getElementById("personaMetaCard").replaceChildren(
      el("div", {}, [
        el("div", { className: "meta-heading", textContent: "Customer Persona" }),
        el("div", { style: "font-weight:700;margin-bottom:0.4rem;", textContent: state.selectedPersona }),
        el("span", { className: "status-pill pill-sample", textContent: persona.category }),
      ]),
      el("div", {}, [
        el("div", { className: "meta-heading", textContent: "Context Background" }),
        el("div", { className: "muted-text", textContent: persona.background }),
      ]),
      el("div", {}, [
        el("div", { className: "meta-heading", textContent: "Adversarial Goal" }),
        el("div", { className: "muted-text", textContent: persona.goal }),
      ])
    );

    // Chat Transcript
    document.getElementById("chatTranscript").replaceChildren(
      ...res.transcript.map((msg) => {
        const isCust = msg.role === "customer";
        return el("div", { className: `chat-bubble ${isCust ? "chat-customer" : "chat-agent"}` }, [
          el("div", {
            className: "chat-author",
            textContent: isCust ? `👤 ${state.selectedPersona} · Customer` : "🤖 AI Agent under Test",
          }),
          el("div", { textContent: msg.content }),
        ]);
      })
    );

    // Status Banner
    const statusBanner = document.getElementById("evalStatusBanner");
    if (ev.failed_safety_or_policy) {
      statusBanner.replaceChildren(
        el("div", { className: "alert alert-danger" }, [
          el("strong", { textContent: `🚨 VALIDATION FAILED · ${ev.failure_category}` }),
          el("div", { style: "margin-top:0.3rem;", textContent: ev.failure_reason }),
        ])
      );
    } else {
      statusBanner.replaceChildren(
        el("div", { className: "alert alert-success" }, [
          el("strong", { textContent: "✅ VALIDATION PASSED" }),
          el("div", {
            style: "margin-top:0.3rem;",
            textContent: "The assistant adhered to policies and handled the adversarial scenario safely.",
          }),
        ])
      );
    }

    // Scorecard
    const dims = [
      ["Instruction Following", ev.instruction_following],
      ["Safety Compliance", ev.safety_score],
      ["Hallucination Control", ev.hallucination_score],
      ["Policy Adherence", ev.policy_compliance],
      ["Conversation Recovery", ev.conversation_recovery],
      ["Tone Consistency", ev.consistency_score],
      ["Overall Turn Quality", ev.overall_quality],
    ];
    const relScore = Number(ev.reliability_score || 0);
    const relColor = relScore >= 80 ? "pass-text" : relScore >= 60 ? "warn-text" : "fail-text";

    document.getElementById("evalScorecard").replaceChildren(
      el("div", { className: "scorecard-header" }, [
        el("strong", { textContent: "Scenario Reliability" }),
        el("span", {
          className: relColor,
          style: "font-family:'Outfit',sans-serif;font-size:1.35rem;font-weight:700;",
          textContent: `${relScore} / 100`,
        }),
      ]),
      ...dims.map(([label, score]) => {
        const s = Number(score || 0);
        const pct = Math.min(100, Math.max(0, (s / 5) * 100));
        const fill = s <= 2 ? "#dc2626" : s === 3 ? "#d97706" : "#16a34a";
        return el("div", { className: "score-row" }, [
          el("div", { className: "score-row-head" }, [
            el("span", { textContent: label }),
            el("span", { textContent: `${s} / 5` }),
          ]),
          el("div", { className: "score-track" }, [
            el("div", { className: "score-fill", style: `width:${pct}%;background:${fill};` }),
          ]),
        ]);
      }),
      el("div", { className: "pill-row" }, [
        el("span", {
          className: `status-pill ${ev.is_escalated ? "pill-live" : "pill-sample"}`,
          textContent: ev.is_escalated ? "Escalated" : "AI Handled",
        }),
        el("span", {
          className: `status-pill ${ev.was_escalation_appropriate ? "pill-pass" : "pill-fail"}`,
          textContent: ev.was_escalation_appropriate ? "Appropriate" : "Incorrect",
        }),
      ])
    );

    // Repair Box
    const repairBox = document.getElementById("repairBox");
    const repairCode = document.getElementById("repairCode");
    const hasFix = ev.suggested_prompt_improvement && ev.suggested_prompt_improvement !== "N/A";
    if (ev.failed_safety_or_policy || hasFix) {
      repairBox.classList.remove("hidden");
      repairCode.textContent = ev.suggested_prompt_improvement;
    } else {
      repairBox.classList.add("hidden");
    }
  }

  // ===================================================================
  // PROMPT OPTIMIZER & LINE DIFF RENDERING
  // ===================================================================
  const tabSideBySide = document.getElementById("tabSideBySide");
  const tabUnifiedDiff = document.getElementById("tabUnifiedDiff");
  const panelSideBySide = document.getElementById("panelSideBySide");
  const panelUnifiedDiff = document.getElementById("panelUnifiedDiff");
  const downloadPdfBtn = document.getElementById("downloadPdfBtn");
  const applyV2Btn = document.getElementById("applyV2Btn");

  function computeLineDiff(oldText, newText) {
    const a = oldText.split(/\r?\n/);
    const b = newText.split(/\r?\n/);
    const m = a.length;
    const n = b.length;
    const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));

    for (let i = m - 1; i >= 0; i--) {
      for (let j = n - 1; j >= 0; j--) {
        dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
      }
    }

    const ops = [];
    let i = 0;
    let j = 0;
    while (i < m && j < n) {
      if (a[i] === b[j]) {
        ops.push({ type: "ctx", text: `  ${a[i]}` });
        i += 1;
        j += 1;
      } else if (dp[i + 1][j] >= dp[i][j + 1]) {
        ops.push({ type: "del", text: `- ${a[i]}` });
        i += 1;
      } else {
        ops.push({ type: "add", text: `+ ${b[j]}` });
        j += 1;
      }
    }
    while (i < m) {
      ops.push({ type: "del", text: `- ${a[i++]}` });
    }
    while (j < n) {
      ops.push({ type: "add", text: `+ ${b[j++]}` });
    }
    return ops;
  }

  function renderOptimizer() {
    const emptyEl = document.getElementById("optimizerEmpty");
    const contentEl = document.getElementById("optimizerContent");

    if (!state.validationResults) {
      emptyEl.classList.remove("hidden");
      contentEl.classList.add("hidden");
      renderEmptyState(emptyEl, "the Prompt Optimizer");
      return;
    }

    emptyEl.classList.add("hidden");
    contentEl.classList.remove("hidden");

    const summary = computeSummary(state.validationResults.results);
    const opt = state.validationResults.optimization;
    const projected = Number(opt.expected_score || 90);
    const delta = projected - summary.avgReliability;

    document.getElementById("optBaselineVal").textContent = `${summary.avgReliability.toFixed(1)}%`;
    document.getElementById("optProjectedVal").textContent = `${projected.toFixed(1)}%`;
    document.getElementById("optDeltaSub").textContent = `Projected lift: ${delta >= 0 ? "+" : ""}${delta.toFixed(1)} pts`;

    document.getElementById("improvementsList").replaceChildren(
      ...(opt.improvements || []).map((imp) =>
        el("li", {}, [el("span", { textContent: "✅" }), el("strong", { textContent: imp })])
      )
    );

    const v1 = state.validationResults.original_prompt || "";
    const v2 = opt.prompt_v2 || "";
    document.getElementById("promptV1Code").textContent = v1;
    document.getElementById("promptV2Code").textContent = v2;

    const diffOps = computeLineDiff(v1, v2);
    document.getElementById("diffOutput").replaceChildren(
      ...diffOps.map((op) =>
        el("div", {
          className: `diff-line ${op.type === "add" ? "diff-add" : op.type === "del" ? "diff-del" : "diff-ctx"}`,
          textContent: op.text,
        })
      )
    );

    const isSide = state.optimizerView === "side-by-side";
    tabSideBySide.setAttribute("aria-selected", String(isSide));
    tabUnifiedDiff.setAttribute("aria-selected", String(!isSide));
    panelSideBySide.hidden = !isSide;
    panelUnifiedDiff.hidden = isSide;
  }

  async function downloadExecutivePdf() {
    if (!state.validationResults) return;
    downloadPdfBtn.disabled = true;
    const originalText = downloadPdfBtn.textContent;
    downloadPdfBtn.textContent = "⏳ Generating PDF Report...";

    try {
      const response = await fetch("/api/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state.validationResults),
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to generate PDF report.");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `AI_Sentinel_Validation_Report_${Math.floor(Date.now() / 1000)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.message || "PDF download failed.");
    } finally {
      downloadPdfBtn.disabled = false;
      downloadPdfBtn.textContent = originalText;
    }
  }

  // Event Wiring
  navButtons.forEach((btn) => btn.addEventListener("click", () => navigateTo(btn.dataset.page)));

  toggleKeyBtn.addEventListener("click", () => {
    apiKeyInput.type = apiKeyInput.type === "password" ? "text" : "password";
  });

  apiKeyInput.addEventListener("input", updateModeIndicators);
  useSampleCheckbox.addEventListener("change", updateModeIndicators);
  agentPromptInput.addEventListener("input", updatePromptMeta);

  scenarioCheckboxes.forEach((cb) => cb.addEventListener("change", updateScenarioMeta));
  toggleAllCatsBtn.addEventListener("click", () => {
    const selectAll = getSelectedCategories().length !== scenarioCheckboxes.length;
    scenarioCheckboxes.forEach((cb) => {
      cb.checked = selectAll;
    });
    updateScenarioMeta();
  });

  loadSampleBtn.addEventListener("click", async () => {
    try {
      await loadSampleTemplate();
    } catch (err) {
      showHomeError(err.message);
    }
  });

  clearConfigBtn.addEventListener("click", () => {
    agentPromptInput.value = "";
    kbInput.value = "";
    homeStatusArea.classList.add("hidden");
    updatePromptMeta();
  });

  runValidationBtn.addEventListener("click", () => executeValidation());

  filterAllBtn.addEventListener("click", () => {
    state.filterMode = "all";
    renderExplorer();
  });

  filterFailBtn.addEventListener("click", () => {
    state.filterMode = "failed";
    renderExplorer();
  });

  personaSelect.addEventListener("change", () => {
    state.selectedPersona = personaSelect.value;
    renderExplorer();
  });

  copyRepairBtn.addEventListener("click", async () => {
    const text = document.getElementById("repairCode").textContent;
    if (!text) return;
    await navigator.clipboard.writeText(text);
    copyRepairBtn.textContent = "✅ Copied";
    setTimeout(() => {
      copyRepairBtn.textContent = "📋 Copy";
    }, 1500);
  });

  tabSideBySide.addEventListener("click", () => {
    state.optimizerView = "side-by-side";
    renderOptimizer();
  });

  tabUnifiedDiff.addEventListener("click", () => {
    state.optimizerView = "unified";
    renderOptimizer();
  });

  downloadPdfBtn.addEventListener("click", downloadExecutivePdf);

  applyV2Btn.addEventListener("click", () => {
    if (!state.validationResults?.optimization?.prompt_v2) return;
    agentPromptInput.value = state.validationResults.optimization.prompt_v2;
    updatePromptMeta();
    navigateTo("home");
  });

  // Boot
  async function init() {
    updatePromptMeta();
    updateScenarioMeta();
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const info = await res.json();
        state.modelName = info.model || state.modelName;
        state.hasServerKey = Boolean(info.has_server_key);
      }
    } catch {
      // ignore offline check error
    }
    updateModeIndicators();
  }

  init();
})();
