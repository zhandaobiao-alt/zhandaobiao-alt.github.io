"use strict";
const data = JSON.parse(document.getElementById("research-data").textContent);
document.getElementById("updated").textContent = `资料更新 ${data.updated_on} · ${data.current_stage}`;
const list = document.getElementById("milestones");
const labels = {done: "已验收", active: "进行中", todo: "待验证"};
for (const task of data.milestones) {
  const row = document.createElement("article");
  row.className = "milestone";
  row.dataset.phase = task.phase;
  const number = document.createElement("span");
  number.className = "milestone-id";
  number.textContent = task.id;
  const body = document.createElement("div");
  const title = document.createElement("h3");
  title.textContent = task.title;
  const description = document.createElement("p");
  description.textContent = task.description;
  body.append(title, description);
  const badge = document.createElement("span");
  badge.className = `tag ${task.phase}`;
  badge.textContent = labels[task.phase];
  row.append(number, body, badge);
  list.append(row);
}
for (const button of document.querySelectorAll("[data-filter]")) {
  button.addEventListener("click", () => {
    const value = button.dataset.filter;
    let visible = 0;
    for (const row of list.children) {
      row.hidden = value !== "all" && row.dataset.phase !== value;
      if (!row.hidden) visible++;
    }
    for (const sibling of document.querySelectorAll("[data-filter]")) {
      const active = sibling === button;
      sibling.classList.toggle("active", active);
      sibling.setAttribute("aria-pressed", String(active));
    }
    document.getElementById("filter-status").textContent = `显示${visible}项研究任务`;
  });
}
document.getElementById("route-count").textContent = data.acceptance.routes.length;
document.getElementById("request-count").textContent = data.acceptance.requests;
document.getElementById("real-trials").textContent = data.acceptance.independent_vehicle_trials;
document.getElementById("trial-scope").textContent = data.acceptance.scope;
for (const route of data.acceptance.routes) {
  const row = document.createElement("tr");
  for (const value of [route.label, String(route.requests), route.status]) {
    const cell = document.createElement("td"); cell.textContent = value; row.append(cell);
  }
  document.getElementById("experiment-rows").append(row);
}
document.getElementById("source-note").textContent = `依据摘要 ${data.evidence_sha256.slice(0,16)}… · 完整实验记录保留于研究环境`;
