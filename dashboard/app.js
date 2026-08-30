const state = {
  runId: "",
  eventSource: null,
};

const elements = {
  connectionStatus: document.querySelector("#connectionStatus"),
  caseSelect: document.querySelector("#caseSelect"),
  activationCode: document.querySelector("#activationCode"),
  runIdInput: document.querySelector("#runIdInput"),
  startFixtureRun: document.querySelector("#startFixtureRun"),
  startLiveRun: document.querySelector("#startLiveRun"),
  inspectRun: document.querySelector("#inspectRun"),
  refreshRun: document.querySelector("#refreshRun"),
  runTitle: document.querySelector("#runTitle"),
  runState: document.querySelector("#runState"),
  runMode: document.querySelector("#runMode"),
  eventList: document.querySelector("#eventList"),
  evidencePanel: document.querySelector("#evidencePanel"),
  evidenceStatus: document.querySelector("#evidenceStatus"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${body}`);
  }
  return response.json();
}

async function boot() {
  bindEvents();
  await checkApi();
  await loadCases();
}

function bindEvents() {
  elements.startFixtureRun.addEventListener("click", startFixtureRun);
  elements.startLiveRun.addEventListener("click", startLiveRun);
  elements.inspectRun.addEventListener("click", () => inspectRun(elements.runIdInput.value.trim()));
  elements.refreshRun.addEventListener("click", refreshActiveRun);
}

async function checkApi() {
  try {
    await api("/v1/health");
    elements.connectionStatus.textContent = "API ready";
  } catch (error) {
    elements.connectionStatus.textContent = "API unavailable";
    elements.connectionStatus.classList.add("tag", "blocker");
  }
}

async function loadCases() {
  const payload = await api("/v1/cases");
  elements.caseSelect.innerHTML = "";
  for (const item of payload.cases) {
    const option = document.createElement("option");
    option.value = item.case_id;
    option.textContent = `${item.case_id} (${item.hazard_type})`;
    elements.caseSelect.append(option);
  }
}

async function startFixtureRun() {
  const caseId = elements.caseSelect.value || "nepal-emsr927-v1";
  const run = await api("/v1/agent/runs", {
    method: "POST",
    headers: {"Idempotency-Key": `dashboard-fixture-${caseId}-${newId()}`},
    body: JSON.stringify({case_id: caseId, mode: "agent", fixture_mode: true}),
  });
  inspectRun(run.run_id);
}

async function startLiveRun() {
  const activation = elements.activationCode.value.trim().toUpperCase();
  const caseId = activation.toLowerCase();
  const run = await api("/v1/agent/runs", {
    method: "POST",
    headers: {"Idempotency-Key": `dashboard-live-${caseId}-${newId()}`},
    body: JSON.stringify({case_id: caseId, mode: "agent", fixture_mode: false, activation}),
  });
  inspectRun(run.run_id);
}

async function inspectRun(runId) {
  if (!runId) {
    return;
  }
  state.runId = runId;
  elements.runIdInput.value = runId;
  elements.eventList.innerHTML = "";
  closeEventSource();
  await refreshActiveRun();
  connectEvents(runId);
}

async function refreshActiveRun() {
  if (!state.runId) {
    return;
  }
  const run = await api(`/v1/runs/${state.runId}`);
  renderRun(run);
  await renderEvents(state.runId);
  await renderEvidence(state.runId);
}

function connectEvents(runId) {
  state.eventSource = new EventSource(`/v1/runs/${runId}/events?follow=true`);
  state.eventSource.addEventListener("run_event", async () => {
    await refreshActiveRun();
  });
  state.eventSource.onerror = () => {
    closeEventSource();
  };
}

function closeEventSource() {
  if (state.eventSource) {
    state.eventSource.close();
    state.eventSource = null;
  }
}

function renderRun(run) {
  elements.runTitle.textContent = run.run_id;
  elements.runState.textContent = run.state;
  elements.runMode.textContent = `${run.mode} / ${run.case_id}`;
}

async function renderEvents(runId) {
  const response = await fetch(`/v1/runs/${runId}/events?follow=false`);
  const text = await response.text();
  const events = parseSse(text);
  elements.eventList.innerHTML = "";
  for (const event of events) {
    const item = document.createElement("li");
    item.className = "event";
    item.innerHTML = `
      <strong>${escapeHtml(event.event_type)} - ${escapeHtml(event.stage)}</strong>
      <span>${escapeHtml(event.message)}</span>
      <small>#${event.sequence} ${escapeHtml(event.created_at)}</small>
    `;
    elements.eventList.append(item);
  }
}

async function renderEvidence(runId) {
  const payload = await api(`/v1/runs/${runId}/evidence`);
  const evidence = payload.source_evidence_package;
  if (!evidence) {
    elements.evidenceStatus.textContent = "No package";
    elements.evidencePanel.className = "empty-state";
    elements.evidencePanel.textContent = "Source evidence has not been produced yet.";
    return;
  }
  elements.evidenceStatus.textContent = evidence.verification_status;
  elements.evidencePanel.className = "evidence-grid";
  const cems = evidence.cems_activation;
  elements.evidencePanel.innerHTML = `
    <section>
      <div class="tags">
        <span class="tag">${escapeHtml(evidence.activation_code)}</span>
        <span class="tag ${evidence.verification_status === "conflicting" ? "blocker" : evidence.verification_status === "preliminary" ? "warning" : ""}">${escapeHtml(evidence.verification_status)}</span>
        <span class="tag">${escapeHtml(evidence.hazard_type)}</span>
      </div>
    </section>
    ${cems ? renderCems(cems) : ""}
    ${renderFindings(evidence.findings || [])}
    ${renderDataGaps(evidence.data_gaps || [])}
    ${renderSnapshots(evidence.snapshots || [])}
  `;
}

function renderCems(cems) {
  const aois = cems.aois || [];
  return `
    <section>
      <h3>${escapeHtml(cems.name)}</h3>
      <p class="meta">${escapeHtml(cems.category)}${cems.sub_category ? ` / ${escapeHtml(cems.sub_category)}` : ""} - ${cems.closed ? "closed" : "open"}</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>AOI</th><th>Product</th><th>Status</th><th>Delivery</th></tr>
          </thead>
          <tbody>
            ${aois.map((aoi) => `
              <tr>
                <td>${aoi.aoi_number}. ${escapeHtml(aoi.aoi_name)}</td>
                <td>${escapeHtml(aoi.product_type)}</td>
                <td>${escapeHtml(aoi.status_label)}</td>
                <td>${escapeHtml(aoi.delivery_time || aoi.expected_delivery || "not available")}</td>
              </tr>
            `).join("") || `<tr><td colspan="4">No AOI product detail in this package.</td></tr>`}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function renderFindings(findings) {
  return `
    <section>
      <h3>Verification Findings</h3>
      ${findings.map((finding) => `
        <div class="finding ${escapeHtml(finding.severity)}">
          <strong>${escapeHtml(finding.finding_id)}</strong>
          <p>${escapeHtml(finding.message)}</p>
          <small>${escapeHtml(finding.status)}</small>
        </div>
      `).join("")}
    </section>
  `;
}

function renderDataGaps(gaps) {
  return `
    <section>
      <h3>Data Gaps</h3>
      ${gaps.length ? `<ul>${gaps.map((gap) => `<li>${escapeHtml(gap)}</li>`).join("")}</ul>` : `<p class="meta">No source-level data gaps recorded.</p>`}
    </section>
  `;
}

function renderSnapshots(snapshots) {
  return `
    <section>
      <h3>Snapshots</h3>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Source</th><th>Kind</th><th>SHA-256</th></tr></thead>
          <tbody>
            ${snapshots.map((snapshot) => `
              <tr>
                <td>${escapeHtml(snapshot.publisher)}</td>
                <td>${escapeHtml(snapshot.kind)}</td>
                <td><code>${escapeHtml(snapshot.content_sha256.slice(0, 16))}...</code></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function parseSse(text) {
  return text
    .split("\n\n")
    .map((chunk) => chunk.split("\n").find((line) => line.startsWith("data:")))
    .filter(Boolean)
    .map((line) => JSON.parse(line.slice(5).trim()));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function newId() {
  if (crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

boot().catch((error) => {
  elements.connectionStatus.textContent = "Dashboard error";
  elements.connectionStatus.classList.add("tag", "blocker");
  elements.evidencePanel.className = "empty-state";
  elements.evidencePanel.textContent = error.message;
});
