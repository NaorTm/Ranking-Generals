(function () {
  const DATA = window.DASHBOARD_DATA;
  const COMMANDERS = DATA.commanders;
  const MODELS = DATA.metadata.models;
  const MODEL_KEYS = MODELS.map((item) => item.key);

  const COLORS = {
    robust_elite_core: "#227c5d",
    strong_upper_tier: "#c77d22",
    high_confidence_upper_band: "#2f6db3",
    model_sensitive_band: "#b74a4a",
    other_ranked: "#6f7a72",
    battle: "#2f6db3",
    operation: "#5b8c5a",
    campaign: "#b27c2f",
    war: "#894d9c",
    victory: "#2e8f63",
    indecisive: "#b88b2b",
    defeat: "#b74646",
    unknown: "#7b8480",
  };

  const GROUP_LABELS = {
    robust_elite_core: "Robust elite core",
    strong_upper_tier: "Strong upper tier",
    high_confidence_upper_band: "High-confidence upper band",
    model_sensitive_band: "Model-sensitive band",
    other_ranked: "Other ranked",
  };

  const ERA_LABELS = {
    ancient: "Ancient",
    medieval: "Medieval",
    early_modern: "Early modern",
    modern: "Modern",
    contemporary: "Contemporary",
  };

  const PAGE_CLASS_LABELS = {
    battle_dominant: "Battle dominant",
    mixed_profile: "Mixed profile",
    war_campaign_heavy: "War/campaign heavy",
    operation_heavy: "Operation heavy",
  };

  const state = {
    modelKey: "hierarchical_trust_v2",
    metricKey: "rank",
    eraFilter: "all",
    pageTypeFilter: "all",
    robustnessFilter: "all",
    minEngagements: 0,
    searchTerm: "",
    topN: 20,
    eraView: "modern",
    selectedIds: [],
    tableSortKey: "metric",
    tableSortDirection: "default",
  };

  const commanderById = new Map(COMMANDERS.map((commander) => [commander.id, commander]));
  const searchInput = document.getElementById("search-input");

  function formatRank(value) {
    return value == null ? "NA" : `#${Math.round(value)}`;
  }

  function formatScore(value) {
    return value == null ? "NA" : value.toFixed(2);
  }

  function formatPercent(value) {
    return value == null ? "NA" : `${(value * 100).toFixed(1)}%`;
  }

  function formatNumber(value) {
    if (value == null) return "NA";
    return Number(value).toLocaleString();
  }

  function titleCase(text) {
    if (!text) return "Unknown";
    return text
      .replace(/_/g, " ")
      .replace(/\b\w/g, (match) => match.toUpperCase());
  }

  function getModelLabel(modelKey) {
    const match = MODELS.find((item) => item.key === modelKey);
    return match ? match.label : modelKey;
  }

  function commanderTierLabel(commander) {
    if (commander.synthesis && commander.synthesis.tier) return commander.synthesis.tier;
    if (commander.confidenceAdjustedTier && commander.confidenceAdjustedTier.label) return commander.confidenceAdjustedTier.label;
    return commander.tier && commander.tier.label ? commander.tier.label : "Unclassified";
  }

  function commanderStabilityLabel(commander) {
    const category = commander.stabilityCategory || (commander.stability && commander.stability.category);
    const score = commander.stabilityScore || (commander.stability && commander.stability.score);
    if (!category && score == null) return "Unknown";
    const scoreText = score == null ? "" : ` (${Number(score).toFixed(1)})`;
    return `${titleCase(category || "unknown")}${scoreText}`;
  }

  function commanderConfidenceLabel(commander) {
    const confidence = commander.rankConfidence || {};
    if (!confidence.confidenceCategory && !confidence.rankInterval80) return "Unknown";
    const interval = confidence.rankInterval80 ? `80% ${confidence.rankInterval80}` : "80% NA";
    return `${titleCase(confidence.confidenceCategory || "unknown")} · ${interval}`;
  }

  function commanderRoleLabel(commander) {
    const role = commander.roleSensitivity || commander.roleContribution || {};
    if (!role.dominantRoleClass) return "Unclassified";
    return titleCase(role.dominantRoleClass);
  }

  function commanderMetricValue(commander, modelKey, metricKey) {
    return metricKey === "score" ? commander.scores[modelKey] : commander.ranks[modelKey];
  }

  function compareForCurrentMetric(left, right) {
    const leftValue = commanderMetricValue(left, state.modelKey, state.metricKey);
    const rightValue = commanderMetricValue(right, state.modelKey, state.metricKey);

    if (leftValue == null && rightValue == null) return left.name.localeCompare(right.name);
    if (leftValue == null) return 1;
    if (rightValue == null) return -1;
    if (state.metricKey === "rank") return leftValue - rightValue;
    return rightValue - leftValue;
  }

  function tableSortValue(commander, key) {
    if (key === "name") return commander.name;
    if (key === "era") return ERA_LABELS[commander.interpretiveEra] || titleCase(commander.interpretiveEra);
    if (key === "category") return GROUP_LABELS[commander.robustnessCategory] || "Other ranked";
    if (key === "tier") return commander.tier && commander.tier.sort != null ? commander.tier.sort : 99;
    if (key === "stability") return commander.stabilityScore || 0;
    if (key === "confidence") return commander.rankConfidence && commander.rankConfidence.rankBandWidth80 != null ? commander.rankConfidence.rankBandWidth80 : 999999;
    if (key === "role") return commanderRoleLabel(commander);
    if (key === "audit") return (commander.auditFlags || []).length;
    if (key === "metric") return commanderMetricValue(commander, state.modelKey, state.metricKey);
    if (key === "engagements") return commander.engagementCount || 0;
    if (key === "spread") return commander.rankRange || 0;
    if (key === "profile") return PAGE_CLASS_LABELS[commander.pageTypeProfileClass] || titleCase(commander.pageTypeProfileClass || "mixed");
    return null;
  }

  function compareTableRows(left, right) {
    if (state.tableSortKey === "metric" && state.tableSortDirection === "default") {
      return compareForCurrentMetric(left, right);
    }

    const leftValue = tableSortValue(left, state.tableSortKey);
    const rightValue = tableSortValue(right, state.tableSortKey);
    const direction = state.tableSortDirection === "asc" ? 1 : -1;

    if (typeof leftValue === "string" || typeof rightValue === "string") {
      return direction * String(leftValue || "").localeCompare(String(rightValue || ""));
    }
    if (leftValue == null && rightValue == null) return left.name.localeCompare(right.name);
    if (leftValue == null) return 1;
    if (rightValue == null) return -1;
    if (leftValue === rightValue) return left.name.localeCompare(right.name);
    return direction * (Number(leftValue) - Number(rightValue));
  }

  function sortableHeader(key, label) {
    const active = state.tableSortKey === key;
    const marker = active && state.tableSortDirection !== "default"
      ? (state.tableSortDirection === "asc" ? " ▲" : " ▼")
      : "";
    return `<th data-sort-key="${key}" class="${active ? "sorted" : ""}">${label}${marker}</th>`;
  }

  function handleTableSort(key) {
    if (state.tableSortKey === key) {
      state.tableSortDirection = state.tableSortDirection === "desc" ? "asc" : "desc";
    } else {
      state.tableSortKey = key;
    state.tableSortDirection = key === "name" || key === "era" || key === "category" || key === "profile" || key === "tier" || key === "role" ? "asc" : "desc";
    }
    renderExplorerTable();
  }

  function filteredCommanders() {
    return COMMANDERS.filter((commander) => {
      if (state.eraFilter !== "all" && commander.interpretiveEra !== state.eraFilter) return false;
      if (state.pageTypeFilter !== "all" && commander.pageTypeProfileClass !== state.pageTypeFilter) return false;
      if (state.robustnessFilter !== "all" && commander.robustnessCategory !== state.robustnessFilter) return false;
      if ((commander.engagementCount || 0) < state.minEngagements) return false;
      if (state.searchTerm) {
        const auditText = (commander.auditFlags || []).map((flag) => flag.flag).join(" ");
        const confidenceText = commander.rankConfidence ? `${commander.rankConfidence.confidenceCategory || ""} ${commander.rankConfidence.rankInterval80 || ""}` : "";
        const roleText = commanderRoleLabel(commander);
        const haystack = `${commander.name} ${commander.primaryEraBucket || ""} ${commander.interpretiveEra} ${commander.robustnessCategory} ${commanderTierLabel(commander)} ${confidenceText} ${roleText} ${auditText}`
          .toLowerCase();
        if (!haystack.includes(state.searchTerm.toLowerCase())) return false;
      }
      return true;
    });
  }

  function commandersWithCurrentMetric() {
    return filteredCommanders().filter((commander) => commanderMetricValue(commander, state.modelKey, state.metricKey) != null);
  }

  function topCommanders(limit) {
    return commandersWithCurrentMetric().sort(compareForCurrentMetric).slice(0, limit);
  }

  function selectedCommandersOrFallback(limit = 3) {
    if (state.selectedIds.length > 0) {
      return state.selectedIds
        .map((id) => commanderById.get(id))
        .filter(Boolean);
    }
    return topCommanders(limit);
  }

  function selectionBorder(id) {
    return state.selectedIds.includes(id) ? "#111111" : "rgba(0,0,0,0.18)";
  }

  function bubbleSize(commander) {
    const value = Math.max(1, commander.engagementCount || 1);
    return Math.min(30, 8 + Math.sqrt(value) * 3.2);
  }

  function addSelection(id) {
    if (!id) return;
    if (state.selectedIds.includes(id)) {
      state.selectedIds = state.selectedIds.filter((item) => item !== id);
    } else {
      state.selectedIds = [...state.selectedIds, id].slice(-4);
    }
    renderAll();
  }

  function findCommanderByName(name) {
    if (!name) return null;
    const exact = COMMANDERS.find((commander) => commander.name.toLowerCase() === name.toLowerCase());
    if (exact) return exact;
    return COMMANDERS.find((commander) => commander.name.toLowerCase().includes(name.toLowerCase())) || null;
  }

  function plotlyConfig() {
    return {
      displayModeBar: true,
      responsive: true,
      modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d", "toImage"],
      displaylogo: false,
    };
  }

  function attachPlotSelection(chartId) {
    const chart = document.getElementById(chartId);
    if (!chart || chart.dataset.selectionAttached === "1") return;
    chart.on("plotly_click", (event) => {
      const point = event.points && event.points[0];
      if (!point) return;
      const commanderId = Array.isArray(point.customdata) ? point.customdata[0] : point.customdata;
      if (commanderId) addSelection(commanderId);
    });
    chart.dataset.selectionAttached = "1";
  }

  function renderOverview() {
    document.getElementById("snapshot-label").textContent = DATA.metadata.snapshot;
    document.getElementById("commander-count").textContent = formatNumber(DATA.metadata.counts.commanderCount);

    const cohort = commandersWithCurrentMetric();
    const top = topCommanders(1)[0];
    const robustCount = cohort.filter((commander) => commander.robustnessCategory === "robust_elite_core").length;
    const cautionCount = cohort.filter((commander) => commander.robustnessCategory === "model_sensitive_band").length;
    const medianSpread = cohort.length
      ? cohort.map((commander) => commander.rankRange || 0).sort((a, b) => a - b)[Math.floor(cohort.length / 2)]
      : 0;

    const cardContainer = document.getElementById("overview-cards");
    cardContainer.innerHTML = [
      {
        label: "Filtered cohort",
        value: formatNumber(cohort.length),
        detail: `Current model: ${getModelLabel(state.modelKey)}`,
      },
      {
        label: "Headline leader",
        value: top ? top.name : "NA",
        detail: top ? `${formatRank(top.ranks[state.modelKey])} Â· ${top.trustConfidence || "NA"} confidence` : "No commander available",
      },
      {
        label: "Headline core in filter",
        value: formatNumber(robustCount),
        detail: `${formatNumber(cautionCount)} model-sensitive cases remain in the filtered cohort`,
      },
      {
        label: "Median rank spread",
        value: formatNumber(medianSpread),
        detail: "Lower is more stable across models",
      },
    ]
      .map(
        (card) => `
          <div class="metric-card">
            <span class="metric-label">${card.label}</span>
            <strong class="metric-value">${card.value}</strong>
            <div class="metric-detail">${card.detail}</div>
          </div>
        `,
      )
      .join("");

    const filtered = commandersWithCurrentMetric();
    const byGroup = [
      "robust_elite_core",
      "strong_upper_tier",
      "high_confidence_upper_band",
      "model_sensitive_band",
    ].map((group) => ({
      group,
      items: filtered
        .filter((commander) => commander.robustnessCategory === group)
        .sort(compareForCurrentMetric)
        .slice(0, 8),
    }));

    document.getElementById("top-tier-columns").innerHTML = byGroup
      .map((entry) => {
        const description =
          entry.group === "robust_elite_core"
            ? "Highest-confidence headline commanders under trust-first v2."
            : entry.group === "strong_upper_tier"
              ? "Upper-tier contenders with strong scale and evidence."
              : entry.group === "high_confidence_upper_band"
                ? "Strong commanders who remain outside the headline core."
                : "Visible upper-band cases whose placement is still materially model-sensitive.";
        return `
          <div class="tier-column ${entry.group === "robust_elite_core" ? "robust" : entry.group === "strong_upper_tier" ? "strong" : "caution"}">
            <h3>${GROUP_LABELS[entry.group]}</h3>
            <p>${description}</p>
            <div class="tier-list">
              ${entry.items
                .map(
                  (commander) => `
                    <button class="tier-pill" data-commander-id="${commander.id}">
                      ${commander.name}
                    </button>
                  `,
                )
                .join("") || '<span class="muted">No commanders in the current filter.</span>'}
            </div>
          </div>
        `;
      })
      .join("");

    document.querySelectorAll(".tier-pill").forEach((button) => {
      button.addEventListener("click", () => addSelection(button.dataset.commanderId));
    });
  }

  function renderSelectedChips() {
    const container = document.getElementById("selected-commander-chips");
    if (state.selectedIds.length === 0) {
      container.innerHTML = '<span class="muted">No commanders selected. Click bars, points, or table rows to build a comparison set.</span>';
      return;
    }
    container.innerHTML = state.selectedIds
      .map((id) => {
        const commander = commanderById.get(id);
        if (!commander) return "";
        return `
          <span class="chip">
            ${commander.name}
            <button type="button" data-remove-id="${id}" aria-label="Remove ${commander.name}">Ã—</button>
          </span>
        `;
      })
      .join("");
    container.querySelectorAll("button[data-remove-id]").forEach((button) => {
      button.addEventListener("click", () => addSelection(button.dataset.removeId));
    });
  }

  function renderLeaderboard() {
    const chart = document.getElementById("leaderboard-chart");
    const top = topCommanders(state.topN);
    const traces = [
      {
        type: "bar",
        orientation: "h",
        y: top.map((commander) => commander.name).reverse(),
        x: top.map((commander) => commanderMetricValue(commander, state.modelKey, state.metricKey)).reverse(),
        customdata: top.map((commander) => [commander.id]).reverse(),
        marker: {
          color: top.map((commander) => COLORS[commander.robustnessCategory] || COLORS.other_ranked).reverse(),
          line: {
            color: top.map((commander) => selectionBorder(commander.id)).reverse(),
            width: top.map((commander) => (state.selectedIds.includes(commander.id) ? 3 : 1)).reverse(),
          },
        },
        hovertemplate: top
          .map(
            (commander) => `
              <b>${commander.name}</b><br>
              Era: ${ERA_LABELS[commander.interpretiveEra] || titleCase(commander.interpretiveEra)}<br>
              ${state.metricKey === "rank" ? "Rank" : "Score"}: %{x}<br>
              Engagements: ${formatNumber(commander.engagementCount)}<br>
              Rank spread: ${formatNumber(commander.rankRange)}<br>
              Robustness: ${GROUP_LABELS[commander.robustnessCategory] || "Other ranked"}<extra></extra>
            `,
          )
          .reverse(),
      },
    ];

    Plotly.react(
      chart,
      traces,
      {
        margin: { l: 180, r: 30, t: 20, b: 40 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        xaxis: {
          title: state.metricKey === "rank" ? "Rank (lower is better)" : "Normalized score",
          autorange: state.metricKey === "rank" ? "reversed" : true,
          gridcolor: "rgba(0,0,0,0.08)",
        },
        yaxis: { automargin: true },
      },
      plotlyConfig(),
    );
    attachPlotSelection("leaderboard-chart");
  }

  function renderMovementChart() {
    const chart = document.getElementById("movement-chart");
    const set = selectedCommandersOrFallback(Math.min(state.topN, 18));
    const traces = set.map((commander) => ({
      type: "scatter",
      mode: "lines+markers",
      name: commander.name,
      x: MODELS.map((model) => model.label),
      y: MODEL_KEYS.map((modelKey) => commander.ranks[modelKey]),
      customdata: MODEL_KEYS.map(() => [commander.id]),
      line: {
        color: COLORS[commander.robustnessCategory] || COLORS.other_ranked,
        width: state.selectedIds.includes(commander.id) ? 4 : 2.2,
      },
      marker: {
        size: state.selectedIds.includes(commander.id) ? 10 : 7,
        color: COLORS[commander.robustnessCategory] || COLORS.other_ranked,
      },
      hovertemplate: `<b>${commander.name}</b><br>%{x}<br>Rank: %{y}<extra></extra>`,
      connectgaps: false,
    }));

    Plotly.react(
      chart,
      traces,
      {
        margin: { l: 48, r: 20, t: 20, b: 70 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        xaxis: { tickangle: -25 },
        yaxis: {
          title: "Rank",
          autorange: "reversed",
          gridcolor: "rgba(0,0,0,0.08)",
        },
        showlegend: false,
      },
      plotlyConfig(),
    );
    attachPlotSelection("movement-chart");
  }

  function renderSensitivityChart() {
    const chart = document.getElementById("sensitivity-chart");
    const cohort = filteredCommanders().filter((commander) => commander.ranks.baseline_conservative != null && commander.rankRange != null);
    const groups = ["robust_elite_core", "strong_upper_tier", "high_confidence_upper_band", "model_sensitive_band", "other_ranked"];
    const traces = groups
      .map((group) => {
        const items = cohort.filter((commander) => commander.robustnessCategory === group);
        if (!items.length) return null;
        return {
          type: "scatter",
          mode: "markers",
          name: GROUP_LABELS[group],
          x: items.map((commander) => commander.ranks.baseline_conservative),
          y: items.map((commander) => commander.rankRange),
          text: items.map((commander) => commander.name),
          customdata: items.map((commander) => [commander.id, commander.engagementCount]),
          marker: {
            size: items.map(bubbleSize),
            color: COLORS[group],
            opacity: 0.82,
            line: {
              color: items.map((commander) => selectionBorder(commander.id)),
              width: items.map((commander) => (state.selectedIds.includes(commander.id) ? 3 : 1)),
            },
          },
          hovertemplate:
            "<b>%{text}</b><br>" +
            "Baseline rank: %{x}<br>" +
            "Rank spread: %{y}<br>" +
            "Engagements: %{customdata[1]}<extra></extra>",
        };
      })
      .filter(Boolean);

    Plotly.react(
      chart,
      traces,
      {
        margin: { l: 55, r: 20, t: 20, b: 48 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        xaxis: { title: "Conservative baseline rank", autorange: "reversed", gridcolor: "rgba(0,0,0,0.08)" },
        yaxis: { title: "Rank spread across models", gridcolor: "rgba(0,0,0,0.08)" },
        legend: { orientation: "h", y: 1.12 },
      },
      plotlyConfig(),
    );
    attachPlotSelection("sensitivity-chart");
  }

  function renderPageDependenceChart() {
    const chart = document.getElementById("page-dependence-chart");
    const cohort = filteredCommanders().filter(
      (commander) =>
        commander.modelDependence.battleVsHierarchicalRankGap != null &&
        commander.pageTypes.higherLevelShare != null,
    );
    const groups = ["robust_elite_core", "strong_upper_tier", "high_confidence_upper_band", "model_sensitive_band", "other_ranked"];
    const traces = groups
      .map((group) => {
        const items = cohort.filter((commander) => commander.robustnessCategory === group);
        if (!items.length) return null;
        return {
          type: "scatter",
          mode: "markers",
          name: GROUP_LABELS[group],
          x: items.map((commander) => commander.pageTypes.higherLevelShare * 100),
          y: items.map((commander) => commander.modelDependence.battleVsHierarchicalRankGap),
          text: items.map((commander) => commander.name),
          customdata: items.map((commander) => [commander.id, commander.engagementCount]),
          marker: {
            size: items.map(bubbleSize),
            color: COLORS[group],
            opacity: 0.82,
            line: {
              color: items.map((commander) => selectionBorder(commander.id)),
              width: items.map((commander) => (state.selectedIds.includes(commander.id) ? 3 : 1)),
            },
          },
          hovertemplate:
            "<b>%{text}</b><br>" +
            "Higher-level page share: %{x:.1f}%<br>" +
            "Battle-only rank minus hierarchical rank: %{y}<br>" +
            "Engagements: %{customdata[1]}<br>" +
            "Positive values indicate hierarchical gain.<extra></extra>",
        };
      })
      .filter(Boolean);

    Plotly.react(
      chart,
      traces,
      {
        margin: { l: 55, r: 20, t: 20, b: 55 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        xaxis: {
          title: "Higher-level page share (%)",
          gridcolor: "rgba(0,0,0,0.08)",
        },
        yaxis: {
          title: "Battle-only rank minus hierarchical rank",
          zeroline: true,
          zerolinecolor: "rgba(0,0,0,0.32)",
          gridcolor: "rgba(0,0,0,0.08)",
        },
        legend: { orientation: "h", y: 1.12 },
      },
      plotlyConfig(),
    );
    attachPlotSelection("page-dependence-chart");
  }

  function renderPageCompositionChart() {
    const chart = document.getElementById("page-composition-chart");
    const set = selectedCommandersOrFallback(Math.min(state.topN, 6));
    const traces = [
      {
        type: "bar",
        name: "Battle",
        x: set.map((commander) => commander.name),
        y: set.map((commander) => commander.pageTypes.shares.battle * 100),
        marker: { color: COLORS.battle },
      },
      {
        type: "bar",
        name: "Operation",
        x: set.map((commander) => commander.name),
        y: set.map((commander) => commander.pageTypes.shares.operation * 100),
        marker: { color: COLORS.operation },
      },
      {
        type: "bar",
        name: "Campaign",
        x: set.map((commander) => commander.name),
        y: set.map((commander) => commander.pageTypes.shares.campaign * 100),
        marker: { color: COLORS.campaign },
      },
      {
        type: "bar",
        name: "War/conflict",
        x: set.map((commander) => commander.name),
        y: set.map((commander) => commander.pageTypes.shares.war * 100),
        marker: { color: COLORS.war },
      },
    ];

    Plotly.react(
      chart,
      traces,
      {
        barmode: "stack",
        margin: { l: 55, r: 20, t: 20, b: 85 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        xaxis: { tickangle: -28 },
        yaxis: { title: "Strict page-type share (%)", gridcolor: "rgba(0,0,0,0.08)", range: [0, 100] },
        legend: { orientation: "h", y: 1.14 },
      },
      plotlyConfig(),
    );
  }

  function renderEraChart() {
    const chart = document.getElementById("era-chart");
    const era = state.eraView;
    const cohort = filteredCommanders()
      .filter((commander) => commander.interpretiveEra === era && commanderMetricValue(commander, state.modelKey, state.metricKey) != null)
      .sort(compareForCurrentMetric)
      .slice(0, Math.min(state.topN, 15));

    Plotly.react(
      chart,
      [
        {
          type: "bar",
          orientation: "h",
          y: cohort.map((commander) => commander.name).reverse(),
          x: cohort.map((commander) => commanderMetricValue(commander, state.modelKey, state.metricKey)).reverse(),
          customdata: cohort.map((commander) => [commander.id]).reverse(),
          marker: {
            color: cohort.map((commander) => COLORS[commander.robustnessCategory] || COLORS.other_ranked).reverse(),
            line: {
              color: cohort.map((commander) => selectionBorder(commander.id)).reverse(),
              width: cohort.map((commander) => (state.selectedIds.includes(commander.id) ? 3 : 1)).reverse(),
            },
          },
          hovertemplate:
            "<b>%{y}</b><br>" +
            `${state.metricKey === "rank" ? "Rank" : "Score"}: %{x}<br>` +
            `<extra>${ERA_LABELS[era]}</extra>`,
        },
      ],
      {
        margin: { l: 180, r: 20, t: 20, b: 40 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        title: { text: `${ERA_LABELS[era]} leaderboard`, font: { size: 16 } },
        xaxis: {
          title: state.metricKey === "rank" ? "Rank (lower is better)" : "Normalized score",
          autorange: state.metricKey === "rank" ? "reversed" : true,
          gridcolor: "rgba(0,0,0,0.08)",
        },
        yaxis: { automargin: true },
      },
      plotlyConfig(),
    );
    attachPlotSelection("era-chart");
  }

  function renderOutcomeChart() {
    const chart = document.getElementById("outcome-chart");
    const set = selectedCommandersOrFallback(Math.min(state.topN, 8));
    const names = set.map((commander) => commander.name).reverse();
    const reversed = [...set].reverse();
    const traces = [
      {
        type: "bar",
        orientation: "h",
        name: "Victory family",
        y: names,
        x: reversed.map((commander) => commander.outcomes.grouped.victory_family.share * 100),
        marker: { color: COLORS.victory },
      },
      {
        type: "bar",
        orientation: "h",
        name: "Indecisive family",
        y: names,
        x: reversed.map((commander) => commander.outcomes.grouped.indecisive_family.share * 100),
        marker: { color: COLORS.indecisive },
      },
      {
        type: "bar",
        orientation: "h",
        name: "Defeat family",
        y: names,
        x: reversed.map((commander) => commander.outcomes.grouped.defeat_family.share * 100),
        marker: { color: COLORS.defeat },
      },
      {
        type: "bar",
        orientation: "h",
        name: "Unknown",
        y: names,
        x: reversed.map((commander) => commander.outcomes.grouped.unknown.share * 100),
        marker: { color: COLORS.unknown },
      },
    ];

    Plotly.react(
      chart,
      traces,
      {
        barmode: "stack",
        margin: { l: 180, r: 20, t: 20, b: 40 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        xaxis: { title: "Outcome share (%)", range: [0, 100], gridcolor: "rgba(0,0,0,0.08)" },
        yaxis: { automargin: true },
        legend: { orientation: "h", y: 1.12 },
      },
      plotlyConfig(),
    );
  }

  function renderComparisonCards() {
    const container = document.getElementById("comparison-cards");
    const set = selectedCommandersOrFallback(3);
    if (!set.length) {
      container.innerHTML = '<span class="muted">No commanders available for comparison.</span>';
      return;
    }

    container.innerHTML = set
      .map((commander) => {
        const auditFlags = (commander.auditFlags || []).slice(0, 5);
        const flags = [
          ...auditFlags.map((flag) => flag.flag),
          ...(commander.cautionFlags || []),
          ...(commander.featureQualityFlags || []),
        ].slice(0, 8);
        const topPageContributions = (commander.pageTypes.contributions || [])
          .slice(0, 3)
          .map((item) => `${titleCase(item.pageType || "unknown")}: ${formatPercent(item.shareOfTotalScore)}`)
          .join(" | ");
        return `
          <article class="comparison-card">
            <h3>${commander.name}</h3>
            <div class="comparison-meta">
              ${ERA_LABELS[commander.interpretiveEra] || titleCase(commander.interpretiveEra)} ·
              ${GROUP_LABELS[commander.robustnessCategory] || "Other ranked"} ·
              ${PAGE_CLASS_LABELS[commander.pageTypeProfileClass] || titleCase(commander.pageTypeProfileClass || "mixed")} ·
              ${commander.trustConfidence || "NA"} confidence
            </div>
            <div class="tier-line">
              <strong>${commanderTierLabel(commander)}</strong>
              <span>${commander.tier && commander.tier.reason ? commander.tier.reason : "No tier reason available."}</span>
            </div>
            ${commander.confidenceAdjustedTier && commander.confidenceAdjustedTier.label ? `
              <div class="tier-line confidence-line">
                <strong>${commander.confidenceAdjustedTier.label}</strong>
                <span>${commander.confidenceAdjustedTier.reason || "No confidence-adjusted tier reason available."}</span>
              </div>
            ` : ""}
            <div class="comparison-grid">
              <div><span>Engagements</span><strong>${formatNumber(commander.engagementCount)}</strong></div>
              <div><span>Known outcomes</span><strong>${formatNumber(commander.knownOutcomeCount)}</strong></div>
              <div><span>Rank spread</span><strong>${formatNumber(commander.rankRange)}</strong></div>
              <div><span>Conflicts</span><strong>${formatNumber(commander.distinctConflicts)}</strong></div>
              <div><span>Battle share</span><strong>${formatPercent(commander.pageTypes.shares.battle)}</strong></div>
              <div><span>Higher-level share</span><strong>${formatPercent(commander.pageTypes.higherLevelShare)}</strong></div>
              <div><span>Stability</span><strong>${commanderStabilityLabel(commander)}</strong></div>
              <div><span>Rank CI</span><strong>${commanderConfidenceLabel(commander)}</strong></div>
              <div><span>Bootstrap presence</span><strong>${formatPercent(commander.rankConfidence && commander.rankConfidence.bootstrapPresenceRate)}</strong></div>
              <div><span>Dominant role</span><strong>${commanderRoleLabel(commander)}</strong></div>
              <div><span>Role-weighted rank</span><strong>${formatNumber(commander.roleSensitivity && commander.roleSensitivity.rankRoleWeighted)}</strong></div>
              <div><span>Direct command share</span><strong>${formatPercent(commander.roleSensitivity && commander.roleSensitivity.shareDirectFieldCommand)}</strong></div>
              <div><span>Audit flags</span><strong>${formatNumber((commander.auditFlags || []).length)}</strong></div>
            </div>
            <div class="muted">${commander.trustHeadlineReason || commander.interpretiveReason || "No interpretive note available for this commander in the current classification layer."}</div>
            ${commander.synthesis && commander.synthesis.recommendedInterpretation ? `<div class="muted">${commander.synthesis.recommendedInterpretation}</div>` : ""}
            ${commander.rankConfidence && commander.rankConfidence.recommendedInterpretation ? `<div class="muted">${commander.rankConfidence.recommendedInterpretation}</div>` : ""}
            ${topPageContributions ? `<div class="muted">Main page contribution mix: ${topPageContributions}</div>` : ""}
            <table class="model-rank-list">
              <thead>
                <tr><th>Model</th><th>Rank</th><th>Score</th></tr>
              </thead>
              <tbody>
                ${MODELS.map(
                  (model) => `
                    <tr>
                      <td>${model.label}</td>
                      <td>${formatRank(commander.ranks[model.key])}</td>
                      <td>${formatScore(commander.scores[model.key])}</td>
                    </tr>
                  `,
                ).join("")}
              </tbody>
            </table>
            <div class="flag-list">
              ${flags.length ? flags.map((flag) => `<span class="flag">${flag}</span>`).join("") : '<span class="flag">no special flags</span>'}
            </div>
          </article>
        `;
      })
      .join("");
  }

  function renderTrustExplainer() {
    const container = document.getElementById("trust-explainer");
    if (!container) return;

    const leader = topCommanders(1)[0];
    container.innerHTML = `
      <article class="footer-card">
        <h3>Why trust-first v2 leads</h3>
        <p>The headline model balances normalized outcomes with sustained scale, conflict breadth, opponent breadth, and conservative guardrails against thin records.</p>
      </article>
      <article class="footer-card">
        <h3>Napoleon vs Suvorov</h3>
        <p>Trust-first v2 does not compare raw losses. It compares rate-based performance and then asks how much scale, breadth, and stability support that record.</p>
      </article>
      <article class="footer-card">
        <h3>Why baseline can mislead</h3>
        <p>Battle-purity models can reward very clean smaller records. The trust tiers treat exact adjacent order as secondary to confidence, with ${leader ? `<strong>${leader.name}</strong>` : "the current leader"} shown inside that broader context.</p>
      </article>
    `;
  }

  function renderExplorerTable() {
    const table = document.getElementById("explorer-table");
    const thead = table.querySelector("thead");
    const tbody = table.querySelector("tbody");
    const rows = commandersWithCurrentMetric().sort(compareTableRows).slice(0, 120);

    thead.innerHTML = `
      <tr>
        ${sortableHeader("name", "Commander")}
        ${sortableHeader("era", "Era")}
        ${sortableHeader("category", "Category")}
        ${sortableHeader("tier", "Tier")}
        ${sortableHeader("metric", state.metricKey === "rank" ? "Rank" : "Score")}
        ${sortableHeader("engagements", "Engagements")}
        ${sortableHeader("stability", "Stability")}
        ${sortableHeader("confidence", "Confidence")}
        ${sortableHeader("role", "Role")}
        ${sortableHeader("spread", "Spread")}
        ${sortableHeader("audit", "Audit")}
        ${sortableHeader("profile", "Profile")}
      </tr>
    `;

    tbody.innerHTML = rows
      .map(
        (commander) => `
          <tr data-commander-id="${commander.id}" class="${state.selectedIds.includes(commander.id) ? "selected-row" : ""}">
            <td>${commander.name}</td>
            <td>${ERA_LABELS[commander.interpretiveEra] || titleCase(commander.interpretiveEra)}</td>
            <td>${GROUP_LABELS[commander.robustnessCategory] || "Other ranked"}</td>
            <td>${commanderTierLabel(commander)}</td>
            <td>${state.metricKey === "rank" ? formatRank(commander.ranks[state.modelKey]) : formatScore(commander.scores[state.modelKey])}</td>
            <td>${formatNumber(commander.engagementCount)}</td>
            <td>${commanderStabilityLabel(commander)}</td>
            <td>${commanderConfidenceLabel(commander)}</td>
            <td>${commanderRoleLabel(commander)}</td>
            <td>${formatNumber(commander.rankRange)}</td>
            <td>${formatNumber((commander.auditFlags || []).length)}</td>
            <td>${PAGE_CLASS_LABELS[commander.pageTypeProfileClass] || titleCase(commander.pageTypeProfileClass || "mixed")}</td>
          </tr>
        `,
      )
      .join("");

    tbody.querySelectorAll("tr[data-commander-id]").forEach((row) => {
      row.addEventListener("click", () => addSelection(row.dataset.commanderId));
    });
    thead.querySelectorAll("th[data-sort-key]").forEach((cell) => {
      cell.addEventListener("click", () => handleTableSort(cell.dataset.sortKey));
    });
  }

  function renderAuditAndShortlist() {
    const auditList = document.getElementById("audit-list");
    const shortlistList = document.getElementById("era-shortlist-list");

    auditList.innerHTML = DATA.sensitivityAudit
      .slice(0, 10)
      .map(
        (row) => `
          <li>
            <strong>${row.displayName}</strong>
            <span class="muted">(${titleCase(row.primaryEraBucket || "unknown")})</span><br>
            best ${formatRank(row.bestRank)}, worst ${formatRank(row.worstRank)}, spread ${formatNumber(row.rankRange)}.<br>
            ${row.auditNote}
          </li>
        `,
      )
      .join("");

    shortlistList.innerHTML = DATA.eraShortlist
      .filter((row) => row.requestedEra === state.eraView)
      .slice(0, 8)
      .map(
        (row) => `
          <li>
            <strong>${row.displayName}</strong>
            <span class="muted">(${row.supportBand.replace(/_/g, " ")})</span><br>
            ${row.recommendationNote}<br>
            ${row.caveatNote}
          </li>
        `,
      )
      .join("");
  }

  function renderAll() {
    renderSelectedChips();
    renderOverview();
    renderLeaderboard();
    renderMovementChart();
    renderSensitivityChart();
    renderPageDependenceChart();
    renderPageCompositionChart();
    renderEraChart();
    renderOutcomeChart();
    renderComparisonCards();
    renderExplorerTable();
    renderAuditAndShortlist();
    renderTrustExplainer();
  }

  function populateControls() {
    const modelSelect = document.getElementById("model-select");
    modelSelect.innerHTML = MODELS.map((model) => `<option value="${model.key}">${model.label}</option>`).join("");
    modelSelect.value = state.modelKey;

    const datalist = document.getElementById("commander-search-list");
    datalist.innerHTML = COMMANDERS
      .map((commander) => `<option value="${commander.name}"></option>`)
      .join("");
  }

  function bindControls() {
    document.getElementById("model-select").addEventListener("change", (event) => {
      state.modelKey = event.target.value;
      renderAll();
    });
    document.getElementById("metric-select").addEventListener("change", (event) => {
      state.metricKey = event.target.value;
      renderAll();
    });
    document.getElementById("era-filter").addEventListener("change", (event) => {
      state.eraFilter = event.target.value;
      renderAll();
    });
    document.getElementById("page-type-filter").addEventListener("change", (event) => {
      state.pageTypeFilter = event.target.value;
      renderAll();
    });
    document.getElementById("robustness-filter").addEventListener("change", (event) => {
      state.robustnessFilter = event.target.value;
      renderAll();
    });
    document.getElementById("min-engagements-input").addEventListener("input", (event) => {
      state.minEngagements = Number(event.target.value || 0);
      renderAll();
    });
    searchInput.addEventListener("input", (event) => {
      state.searchTerm = event.target.value.trim();
      renderAll();
    });
    document.getElementById("top-n-select").addEventListener("change", (event) => {
      state.topN = Number(event.target.value);
      renderAll();
    });
    document.getElementById("era-view-select").addEventListener("change", (event) => {
      state.eraView = event.target.value;
      renderAll();
    });
    document.getElementById("add-commander-button").addEventListener("click", () => {
      const match = findCommanderByName(searchInput.value.trim());
      if (match) {
        addSelection(match.id);
      }
    });
    document.getElementById("clear-selection-button").addEventListener("click", () => {
      state.selectedIds = [];
      renderAll();
    });
  }

  populateControls();
  bindControls();
  renderAll();
})();
