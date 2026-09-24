"use strict";
function byId(id) {
    const element = document.getElementById(id);
    if (!element)
        throw new Error(`Missing Explorer element: ${id}`);
    return element;
}
const dataElement = byId("slean-data");
if (!dataElement.textContent)
    throw new Error("Missing Explorer timeline data");
const data = JSON.parse(dataElement.textContent);
const caseFile = data.case;
const events = caseFile.events;
const snapshots = data.snapshots;
const eventByRecord = new Map();
const journalButtons = [];
for (const [index, event] of events.entries()) {
    const recordId = event.payload?.identity?.id;
    if (recordId)
        eventByRecord.set(recordId, index + 1);
}
function node(tag, className = "", value) {
    const element = document.createElement(tag);
    if (className)
        element.className = className;
    if (value !== undefined && value !== null)
        element.textContent = String(value);
    return element;
}
function clear(element) { element.replaceChildren(); }
function label(value) { return String(value ?? "").replaceAll("_", " "); }
function recordId(record) { return record?.identity?.id ?? ""; }
function addFact(list, title, value) {
    const row = node("div");
    row.append(node("dt", "", title), node("dd", "", value));
    list.append(row);
}
function jumpLink(id, prefix) {
    const button = node("button", "record-link", id);
    button.type = "button";
    button.title = `Show the event that introduced ${id}`;
    button.addEventListener("click", () => setPrefix(prefix));
    return button;
}
function reference(id) {
    const prefix = eventByRecord.get(id);
    return prefix ? jumpLink(id, prefix) : node("span", "", id);
}
function addNodeFact(list, title, valueNode) {
    const row = node("div");
    const content = node("dd");
    content.append(valueNode);
    row.append(node("dt", "", title), content);
    list.append(row);
}
function thresholdText(protocol) {
    if (!protocol)
        return "No protocol in scope";
    const symbol = protocol.direction === "gte"
        ? (protocol.inclusive ? "≥" : ">")
        : protocol.direction === "lte"
            ? (protocol.inclusive ? "≤" : "<")
            : label(protocol.direction);
    return `${protocol.metric_id} ${symbol} ${protocol.threshold} ${protocol.unit}`;
}
function observationText(item) {
    const value = item.value === null ? "value unavailable" : `${item.value} ${item.unit}`;
    return `${item.metric_id}: ${value} · ${label(item.status)}`;
}
function gateText(item) {
    const operator = item.operator === "all_of" ? "AND · all members" : "OR · any member";
    const joiner = item.operator === "all_of" ? " + " : " / ";
    return `${operator} · ${label(item.kind)}: ${item.member_refs.join(joiner)} → ${item.target_ref} · recorded, not evaluated`;
}
function renderDecision(state) {
    const target = byId("decision-content");
    const status = byId("state-status");
    clear(target);
    const decision = state.decisions.at(-1);
    const assessment = state.assessments.at(-1);
    if (!decision) {
        status.className = "state-status";
        status.textContent = state.prefix === 0 ? "Start" : "Decision pending";
        target.append(node("p", "quiet-state", state.prefix === 0
            ? "The projected journal has no events at this prefix. Move forward to review the protocol, evidence, and decision as they are recorded."
            : "No decision has been recorded at this prefix. Evidence below shows only records available so far."));
        if (assessment) {
            const facts = node("dl", "fact-rows");
            addNodeFact(facts, "Latest assessment", reference(recordId(assessment)));
            addFact(facts, "Recorded verdict", label(assessment.verdict));
            target.append(facts);
        }
        return;
    }
    status.className = "state-status is-decision";
    status.textContent = "Decision recorded";
    const heading = node("div", "decision-result");
    heading.append(node("strong", "", label(decision.result)), node("span", "", `from ${recordId(decision)}`));
    target.append(heading, node("p", "decision-reason", decision.reason));
    const citedAssessment = state.assessments.find(item => recordId(item) === decision.assessment_ref);
    const protocol = state.protocols.find(item => recordId(item) === citedAssessment?.protocol_ref);
    const facts = node("dl", "fact-rows");
    addNodeFact(facts, "Assessment", reference(decision.assessment_ref));
    addFact(facts, "Assessment verdict", citedAssessment ? label(citedAssessment.verdict) : "Not in scope");
    addFact(facts, "Stated rule", citedAssessment?.rule_used ?? "Not in scope");
    addFact(facts, "Frozen threshold", thresholdText(protocol));
    target.append(facts);
}
function addGroup(target, title, records, renderRecord) {
    const group = node("div", "record-group");
    const heading = node("h3");
    heading.append(node("span", "", title), node("span", "", String(records.length)));
    group.append(heading);
    if (!records.length) {
        group.append(node("p", "record-empty", "No record at this prefix"));
    }
    else {
        const list = node("ul");
        for (const record of records) {
            const row = node("li");
            const primary = node("span", "record-primary");
            primary.append(reference(recordId(record)));
            row.append(primary, node("span", "record-secondary", renderRecord(record)));
            list.append(row);
        }
        group.append(list);
    }
    target.append(group);
}
function renderEvidence(state) {
    const target = byId("evidence-content");
    clear(target);
    addGroup(target, "Protocols", state.protocols, item => thresholdText(item));
    addGroup(target, "Observations", state.observations, item => observationText(item));
    addGroup(target, "Assessments", state.assessments, item => `${label(item.verdict)} · ${item.rule_used} · cites ${item.observation_refs.join(", ") || "no observations"}`);
    addGroup(target, "Costs", state.costs, item => `${item.amount} ${item.unit} · ${label(item.category)} · ${label(item.coverage)}`);
    addGroup(target, "Relations", state.relations, item => `${label(item.kind)}: ${item.source_ref} → ${item.target_ref}`);
    addGroup(target, "Dependency gates", state.dependency_gates ?? [], gateText);
    addGroup(target, "Runs and artifacts", [...state.runs, ...state.artifacts], item => "input_ref" in item
        ? `Input ${item.input_ref} · protocol ${item.protocol_ref}`
        : `${item.media_type} · ${item.digest}`);
}
function relationNode(state, id) {
    if (recordId(caseFile.claim) === id)
        return { kind: "Claim", summary: caseFile.claim.text };
    const gate = (state.dependency_gates ?? []).find(item => recordId(item) === id);
    if (gate)
        return {
            kind: gate.operator === "all_of" ? "AND · all members" : "OR · any member",
            summary: `${label(gate.kind)} · ${gate.member_refs.length} members · recorded, not evaluated`,
            isGate: true,
        };
    const protocol = state.protocols.find(item => recordId(item) === id);
    if (protocol)
        return { kind: "Protocol", summary: thresholdText(protocol) };
    const observation = state.observations.find(item => recordId(item) === id);
    if (observation)
        return { kind: "Observation", summary: observationText(observation) };
    const assessment = state.assessments.find(item => recordId(item) === id);
    if (assessment)
        return { kind: "Assessment", summary: `${label(assessment.verdict)} · ${assessment.rule_used}` };
    const decision = state.decisions.find(item => recordId(item) === id);
    if (decision)
        return { kind: "Decision", summary: `${label(decision.result)} · ${decision.reason}` };
    const cost = state.costs.find(item => recordId(item) === id);
    if (cost)
        return { kind: "Cost", summary: `${cost.amount} ${cost.unit} · ${label(cost.category)}` };
    const run = state.runs.find(item => recordId(item) === id);
    if (run)
        return { kind: "Run", summary: `Input ${run.input_ref} · protocol ${run.protocol_ref}` };
    const artifact = state.artifacts.find(item => recordId(item) === id);
    if (artifact)
        return { kind: "Artifact", summary: `${artifact.media_type} · ${artifact.digest}` };
    return { kind: "Record", summary: "No display details in this projection" };
}
function renderRelationMap(state) {
    const target = byId("relation-map-content");
    clear(target);
    const gateEdges = (state.dependency_gates ?? []).flatMap(gate => [
        ...gate.member_refs.map(member => ({ source_ref: member, target_ref: recordId(gate), kind: "member" })),
        { source_ref: recordId(gate), target_ref: gate.target_ref, kind: gate.kind },
    ]);
    const edges = [...state.relations, ...gateEdges];
    if (!edges.length) {
        target.append(node("p", "record-empty", "No recorded relation or dependency gate at this prefix."));
        return;
    }
    const ids = [...new Set(edges.flatMap(edge => [edge.source_ref, edge.target_ref]))];
    if (ids.length > 24 || edges.length > 40) {
        target.append(node("p", "record-empty", "This dependency set is too large for the local map. Use the complete Relations and Dependency gates lists above."));
        return;
    }
    const incoming = new Map(ids.map(id => [id, 0]));
    const outgoing = new Map(ids.map(id => [id, []]));
    const levels = new Map(ids.map(id => [id, 0]));
    for (const edge of edges) {
        incoming.set(edge.target_ref, (incoming.get(edge.target_ref) ?? 0) + 1);
        outgoing.get(edge.source_ref)?.push(edge.target_ref);
    }
    const queue = ids.filter(id => incoming.get(id) === 0);
    let visited = 0;
    for (let index = 0; index < queue.length; index += 1) {
        const source = queue[index];
        visited += 1;
        for (const destination of outgoing.get(source) ?? []) {
            levels.set(destination, Math.max(levels.get(destination) ?? 0, (levels.get(source) ?? 0) + 1));
            incoming.set(destination, (incoming.get(destination) ?? 0) - 1);
            if (incoming.get(destination) === 0)
                queue.push(destination);
        }
    }
    if (visited !== ids.length) {
        target.append(node("p", "record-empty", "The recorded dependencies form a cycle. Use the complete Relations and Dependency gates lists above."));
        return;
    }
    const columns = [];
    for (const id of ids) {
        const level = levels.get(id) ?? 0;
        if (!columns[level])
            columns[level] = [];
        columns[level].push(id);
    }
    const nodeWidth = 208;
    const nodeHeight = 108;
    const columnGap = 116;
    const rowGap = 26;
    const inset = 12;
    const width = inset * 2 + columns.length * nodeWidth + (columns.length - 1) * columnGap;
    const height = inset * 2 + Math.max(...columns.map(column => column.length)) * (nodeHeight + rowGap) - rowGap;
    const positions = new Map();
    columns.forEach((column, level) => column.forEach((id, row) => {
        positions.set(id, { x: inset + level * (nodeWidth + columnGap), y: inset + row * (nodeHeight + rowGap) });
    }));
    const stage = node("div", "relation-map-stage");
    stage.style.width = `${width}px`;
    stage.style.height = `${height}px`;
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("relation-map-lines");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    const defs = document.createElementNS(svg.namespaceURI, "defs");
    const marker = document.createElementNS(svg.namespaceURI, "marker");
    marker.setAttribute("id", "relation-map-arrow");
    marker.setAttribute("viewBox", "0 0 10 10");
    marker.setAttribute("refX", "8");
    marker.setAttribute("refY", "5");
    marker.setAttribute("markerWidth", "8");
    marker.setAttribute("markerHeight", "8");
    marker.setAttribute("orient", "auto-start-reverse");
    const arrow = document.createElementNS(svg.namespaceURI, "path");
    arrow.setAttribute("d", "M 0 1 L 9 5 L 0 9 z");
    marker.append(arrow);
    defs.append(marker);
    svg.append(defs);
    for (const edge of edges) {
        const from = positions.get(edge.source_ref);
        const to = positions.get(edge.target_ref);
        const x1 = from.x + nodeWidth + 4;
        const y1 = from.y + nodeHeight / 2;
        const x2 = to.x - 9;
        const y2 = to.y + nodeHeight / 2;
        const middle = (x1 + x2) / 2;
        const path = document.createElementNS(svg.namespaceURI, "path");
        path.classList.add("relation-map-edge");
        path.setAttribute("d", `M ${x1} ${y1} C ${middle} ${y1}, ${middle} ${y2}, ${x2} ${y2}`);
        path.setAttribute("marker-end", "url(#relation-map-arrow)");
        svg.append(path);
        const edgeLabel = document.createElementNS(svg.namespaceURI, "text");
        edgeLabel.classList.add("relation-map-edge-label");
        edgeLabel.setAttribute("x", String(middle));
        edgeLabel.setAttribute("y", String((y1 + y2) / 2 - 8));
        edgeLabel.textContent = edge.kind === "member" ? "" : label(edge.kind);
        svg.append(edgeLabel);
    }
    stage.append(svg);
    for (const id of ids) {
        const position = positions.get(id);
        const info = relationNode(state, id);
        const card = node("div", "relation-map-node");
        if (info.isGate)
            card.classList.add("is-gate");
        card.style.left = `${position.x}px`;
        card.style.top = `${position.y}px`;
        card.dataset.recordId = id;
        card.append(node("span", "relation-map-kind", info.kind), node("strong", "", id), node("span", "relation-map-summary", info.summary));
        stage.append(card);
    }
    target.append(stage);
}
function renderEvent(prefix) {
    const event = events[prefix - 1];
    const facts = byId("event-facts");
    const exact = byId("event-json");
    const disclosure = exact.closest("details");
    if (!disclosure)
        throw new Error("Missing Explorer event details");
    clear(facts);
    disclosure.open = false;
    disclosure.hidden = !event;
    if (!event) {
        byId("event-subtitle").textContent = "Start of the projected journal";
        addFact(facts, "Position", "Before the first event");
        addFact(facts, "Visible events", "0");
        exact.textContent = "";
        return;
    }
    byId("event-subtitle").textContent = `Event ${prefix} of ${events.length}`;
    addFact(facts, "Event", event.event_id);
    addFact(facts, "Type", label(event.kind));
    addFact(facts, "Recorded", event.recorded_at);
    addFact(facts, "Actor", event.actor);
    addFact(facts, "Audience", event.audience);
    addFact(facts, "Source", event.provenance);
    exact.textContent = JSON.stringify(event, null, 2);
}
function setPrefix(value) {
    const prefix = Math.max(0, Math.min(events.length, Number(value)));
    const state = snapshots[prefix];
    byId("prefix-slider").value = String(prefix);
    byId("mobile-event-select").value = String(prefix);
    byId("prefix-count").textContent = `After ${prefix} ${prefix === 1 ? "event" : "events"}`;
    byId("prefix-description").textContent = prefix === 0
        ? "Before the first projected event."
        : `State after ${events[prefix - 1].event_id}: ${label(events[prefix - 1].kind)}.`;
    byId("previous").disabled = prefix === 0;
    byId("next").disabled = prefix === events.length;
    byId("state-subtitle").textContent = `${prefix} of ${events.length} projected events applied`;
    journalButtons.forEach((button, index) => {
        button.classList.toggle("future", index + 1 > prefix);
        if (index + 1 === prefix)
            button.setAttribute("aria-current", "step");
        else
            button.removeAttribute("aria-current");
    });
    renderDecision(state);
    renderEvidence(state);
    renderRelationMap(state);
    renderEvent(prefix);
}
function initialize() {
    if (!Array.isArray(events) || !Array.isArray(snapshots) || snapshots.length !== events.length + 1) {
        throw new Error("Invalid Explorer timeline bundle");
    }
    document.title = `${caseFile.case_id} · Slean Explorer`;
    byId("audience-tag").textContent = `${label(data.audience)} projection`;
    byId("case-id").textContent = caseFile.case_id;
    byId("fixture-tag").hidden = !String(caseFile.provenance).startsWith("synthetic://");
    byId("case-title").textContent = caseFile.claim.text;
    byId("case-question").textContent = caseFile.question.text;
    byId("prefix-total").textContent = `/ ${events.length}`;
    const slider = byId("prefix-slider");
    slider.max = String(events.length);
    byId("journal-count").textContent = `${events.length} events`;
    byId("build-revision").textContent = `Base ${data.build.base_revision.slice(0, 8)}${data.build.source_tree_clean ? "" : " · source tree changed"}`;
    const journal = byId("journal-list");
    const mobileSelect = byId("mobile-event-select");
    mobileSelect.append(new Option("Before the first event", "0"));
    for (const [index, event] of events.entries()) {
        const button = node("button", "journal-item");
        button.type = "button";
        button.setAttribute("aria-label", `After event ${index + 1}: ${label(event.kind)}, ${event.event_id}`);
        const content = node("span");
        content.append(node("span", "journal-title", label(event.kind)), node("span", "journal-id", event.event_id));
        button.append(node("span", "journal-number", String(index + 1).padStart(2, "0")), content);
        button.addEventListener("click", () => setPrefix(index + 1));
        journalButtons.push(button);
        journal.append(button);
        mobileSelect.append(new Option(`${String(index + 1).padStart(2, "0")} · ${label(event.kind)}`, String(index + 1)));
    }
    mobileSelect.addEventListener("change", () => setPrefix(mobileSelect.value));
    slider.addEventListener("input", () => setPrefix(slider.value));
    byId("previous").addEventListener("click", () => setPrefix(Number(slider.value) - 1));
    byId("next").addEventListener("click", () => setPrefix(Number(slider.value) + 1));
    setPrefix(events.length);
}
initialize();
