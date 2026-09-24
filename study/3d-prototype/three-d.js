"use strict";

// Study-only view. The existing Explorer still renders the checked timeline,
// text table, decision, and exact event. This replaces only its visual map.
const studyData = JSON.parse(document.getElementById("slean-data").textContent);
const studySection = document.querySelector(".relation-section");
const studyMap = document.getElementById("relation-map-content");
const studySlider3d = document.getElementById("prefix-slider");
const studyViewport = studySection.querySelector(".relation-map-viewport");
const studyWidth = 880;
const studyHeight = 600;
let studyGraph = null;
let studyLastPrefix = -1;

function studyElement(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (value !== undefined) element.textContent = value;
  return element;
}

const studyControls = studyElement("div", "study-view-controls");
const yawLabel = studyElement("label", "", "Rotate left or right");
const yawControl = document.createElement("input");
yawControl.type = "range";
yawControl.min = "-65";
yawControl.max = "65";
yawControl.value = "-28";
yawControl.setAttribute("aria-label", "Rotate spatial view left or right");
yawLabel.append(yawControl);
const pitchLabel = studyElement("label", "", "Tilt up or down");
const pitchControl = document.createElement("input");
pitchControl.type = "range";
pitchControl.min = "0";
pitchControl.max = "55";
pitchControl.value = "22";
pitchControl.setAttribute("aria-label", "Tilt spatial view up or down");
pitchLabel.append(pitchControl);
const resetControl = studyElement("button", "", "Reset view");
resetControl.type = "button";
studyControls.append(yawLabel, pitchLabel, resetControl);
const depthNote = studyElement(
  "p",
  "study-depth-note",
  "Depth separates recorded AND and OR groups. Rotating changes the view, never the records or the table."
);
studySection.insertBefore(studyControls, studyViewport);
studySection.insertBefore(depthNote, studyViewport);
studySection.querySelector(".map-scroll-hint").textContent = "Scroll the map sideways to follow a dependency.";

function studyEdges(state) {
  const edges = state.relations.map(item => ({from: item.source_ref, to: item.target_ref, kind: item.kind}));
  for (const gate of state.dependency_gates ?? []) {
    for (const member of gate.member_refs) {
      edges.push({from: member, to: gate.identity.id, kind: "member"});
    }
    edges.push({from: gate.identity.id, to: gate.target_ref, kind: gate.kind});
  }
  return edges;
}

function studyLevels(ids, edges) {
  const incoming = new Map(ids.map(id => [id, 0]));
  const outgoing = new Map(ids.map(id => [id, []]));
  const levels = new Map(ids.map(id => [id, 0]));
  for (const edge of edges) {
    incoming.set(edge.to, incoming.get(edge.to) + 1);
    outgoing.get(edge.from).push(edge.to);
  }
  const queue = ids.filter(id => incoming.get(id) === 0);
  for (let index = 0; index < queue.length; index += 1) {
    const id = queue[index];
    for (const child of outgoing.get(id)) {
      levels.set(child, Math.max(levels.get(child), levels.get(id) + 1));
      incoming.set(child, incoming.get(child) - 1);
      if (incoming.get(child) === 0) queue.push(child);
    }
  }
  return queue.length === ids.length ? levels : null;
}

function studyModel(state, cards) {
  const edges = studyEdges(state);
  const ids = [...new Set(edges.flatMap(edge => [edge.from, edge.to]))];
  const info = new Map(cards.map(card => [card.dataset.recordId, {
    kind: card.querySelector(".relation-map-kind")?.textContent ?? "Record",
    summary: card.querySelector(".relation-map-summary")?.textContent ?? "",
  }]));
  if (ids.length > 24 || edges.length > 40 || ids.some(id => !info.has(id))) return null;
  const levels = studyLevels(ids, edges);
  if (!levels) return null;
  const maxLevel = Math.max(...levels.values());
  const columns = new Map();
  for (const id of ids) {
    const level = levels.get(id);
    if (!columns.has(level)) columns.set(level, []);
    columns.get(level).push(id);
  }
  const operators = new Map((state.dependency_gates ?? []).map(gate => [gate.identity.id, gate.operator]));
  const points = new Map();
  for (const [level, members] of columns) {
    members.forEach((id, index) => {
      const operator = operators.get(id);
      points.set(id, {
        x: (level - maxLevel / 2) * 300,
        y: (index - (members.length - 1) / 2) * 118,
        z: operator === "all_of" ? 150 : operator === "any_of" ? -150 : 0,
      });
    });
  }
  return {ids, edges, info, operators, points};
}

function studyProject(point) {
  const yaw = Number(yawControl.value) * Math.PI / 180;
  const pitch = Number(pitchControl.value) * Math.PI / 180;
  const turnedX = point.x * Math.cos(yaw) + point.z * Math.sin(yaw);
  const turnedZ = -point.x * Math.sin(yaw) + point.z * Math.cos(yaw);
  const turnedY = point.y * Math.cos(pitch) - turnedZ * Math.sin(pitch);
  const depth = point.y * Math.sin(pitch) + turnedZ * Math.cos(pitch);
  const scale = Math.max(.77, Math.min(1.25, 1100 / (1100 + depth)));
  return {x: studyWidth / 2 + turnedX * scale, y: studyHeight / 2 + turnedY * scale, scale, depth};
}

function studySvg(tag) {
  return document.createElementNS("http://www.w3.org/2000/svg", tag);
}

function studyMarker(defs, id, color) {
  const marker = studySvg("marker");
  marker.id = id;
  marker.setAttribute("markerWidth", "7");
  marker.setAttribute("markerHeight", "7");
  marker.setAttribute("refX", "6");
  marker.setAttribute("refY", "3.5");
  marker.setAttribute("orient", "auto");
  const arrow = studySvg("path");
  arrow.setAttribute("d", "M 0 0 L 7 3.5 L 0 7 Z");
  arrow.setAttribute("fill", color);
  marker.append(arrow);
  defs.append(marker);
}

function studyDraw() {
  if (!studyGraph) return;
  const projected = new Map([...studyGraph.points].map(([id, point]) => [id, studyProject(point)]));
  const stage = studyElement("div", "study-stage");
  stage.style.height = `${studyHeight}px`;
  const svg = studySvg("svg");
  svg.classList.add("study-links");
  svg.setAttribute("viewBox", `0 0 ${studyWidth} ${studyHeight}`);
  const defs = studySvg("defs");
  studyMarker(defs, "study-arrow", "#8b3827");
  studyMarker(defs, "study-member-arrow", "#557264");
  svg.append(defs);
  for (const edge of studyGraph.edges) {
    const from = projected.get(edge.from);
    const to = projected.get(edge.to);
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const length = Math.hypot(dx, dy) || 1;
    const ux = dx / length;
    const uy = dy / length;
    const start = {x: from.x + ux * 74 * from.scale, y: from.y + uy * 48 * from.scale};
    const end = {x: to.x - ux * 88 * to.scale, y: to.y - uy * 52 * to.scale};
    const middle = (start.x + end.x) / 2;
    const path = studySvg("path");
    if (edge.kind === "member") path.classList.add("is-member");
    path.setAttribute("d", `M ${start.x} ${start.y} C ${middle} ${start.y}, ${middle} ${end.y}, ${end.x} ${end.y}`);
    path.setAttribute("marker-end", `url(#${edge.kind === "member" ? "study-member-arrow" : "study-arrow"})`);
    svg.append(path);
  }
  stage.append(svg);
  for (const id of studyGraph.ids) {
    const position = projected.get(id);
    const info = studyGraph.info.get(id);
    const card = studyElement("div", "study-node");
    if (studyGraph.operators.has(id)) card.classList.add("is-gate");
    card.dataset.recordId = id;
    card.style.left = `${position.x}px`;
    card.style.top = `${position.y}px`;
    card.style.transform = `translate(-50%, -50%) scale(${position.scale})`;
    card.style.zIndex = String(Math.round(1000 - position.depth));
    card.append(
      studyElement("span", "study-kind", info.kind),
      studyElement("strong", "", id),
      studyElement("span", "study-summary", info.summary),
    );
    stage.append(card);
  }
  studyMap.replaceChildren(stage);
}

function studySyncPrefix() {
  const prefix = Number(studySlider3d.value);
  if (prefix === studyLastPrefix) return;
  studyLastPrefix = prefix;
  const cards = [...studyMap.querySelectorAll(".relation-map-node")];
  studyGraph = cards.length ? studyModel(studyData.snapshots[prefix], cards) : null;
  if (studyGraph) studyDraw();
}

for (const input of [yawControl, pitchControl]) input.addEventListener("input", studyDraw);
resetControl.addEventListener("click", () => {
  yawControl.value = "-28";
  pitchControl.value = "22";
  studyDraw();
});
for (const eventName of ["click", "input", "change"]) {
  document.addEventListener(eventName, event => {
    if (event.target.closest?.(".study-view-controls")) return;
    studySyncPrefix();
  });
}
studySyncPrefix();
