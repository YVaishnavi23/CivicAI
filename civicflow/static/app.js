// CivicFlow AI frontend: three views (report, track, authority) over the JSON API.
(function () {
  "use strict";

  const MAX_PHOTO = 3 * 1024 * 1024;
  const STATUSES = ["Received", "Under Review", "In Progress", "Resolved"];
  const PRIORITIES = ["High", "Medium", "Low"];
  const FACTOR_COLORS = { base: "#9aa5a0", category: "#5b7f9e", severity: "#12467e", safety: "#a62f1e", duration: "#b8860b", related: "#3f6249" };

  const $ = (sel, root) => (root || document).querySelector(sel);
  let lang = localStorage.getItem("cf-lang");
  if (!I18N[lang]) lang = "en";
  const state = { view: "report", submitted: null, tracked: null, queue: null, open: new Set(), toast: null };

  const t = (key, vars) => {
    let s = I18N[lang][key] ?? I18N.en[key] ?? key;
    for (const k in vars || {}) s = s.replace("{" + k + "}", vars[k]);
    return s;
  };
  const tr = (group, value) => (I18N[lang][group] && I18N[lang][group][value]) || value;

  // DOM builder: text always goes through textContent, so report content can never inject markup.
  function h(tag, attrs, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? "" : v);
    }
    for (const kid of kids.flat()) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : document.createTextNode(kid));
    return el;
  }
  const show = (el, msg) => { el.textContent = msg || ""; el.hidden = !msg; };
  const fmtDate = (iso) => new Date(iso).toLocaleString(lang === "en" ? "en-IN" : lang + "-IN", { dateStyle: "medium", timeStyle: "short" });

  async function api(path, opts) {
    let res;
    try { res = await fetch(path, opts); } catch (e) { throw new Error(t("errNetwork")); }
    let data = null;
    try { data = await res.json(); } catch (e) { /* no body */ }
    if (!res.ok) {
      let msg = data && data.detail;
      if (Array.isArray(msg)) msg = msg.map((m) => m.msg).join(" ");
      const err = new Error(msg || res.statusText);
      err.status = res.status;
      throw err;
    }
    return data;
  }

  // ---------- language ----------
  function applyStaticText() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach((el) => (el.textContent = t(el.dataset.i18n)));
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => el.setAttribute("placeholder", t(el.dataset.i18nPlaceholder)));
    $("#lang").value = lang;
    fillFilterOptions();
  }

  function setLang(next) {
    lang = next;
    localStorage.setItem("cf-lang", lang);
    applyStaticText();
    renderConfirmation();
    renderTrack();
    renderQueue();
    renderKpis();
  }

  // ---------- routing ----------
  function route() {
    const [view, arg] = location.hash.replace("#", "").split("/");
    state.view = ["report", "track", "authority"].includes(view) ? view : "report";
    document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== "view-" + state.view));
    document.querySelectorAll(".tab").forEach((b) => {
      if (b.dataset.view === state.view) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
    });
    if (state.view === "authority") loadQueue();
    if (state.view === "track" && arg) { $("#t-id").value = arg; lookup(arg); }
    window.scrollTo(0, 0);
  }
  const go = (view, arg) => { const target = "#" + (arg ? view + "/" + arg : view); if (location.hash === target) route(); else location.hash = target; };

  // ---------- report ----------
  function renderConfirmation() {
    const box = $("#confirmation");
    const r = state.submitted;
    box.hidden = !r;
    $("#report-form").hidden = !!r;
    if (!r) return;
    box.replaceChildren(
      h("h2", {}, t("confTitle")),
      h("p", { class: "small" }, t("confRef")),
      h("div", { class: "plate" }, h("span", {}, r.ticket_id)),
      h("p", {}, t("confNext")),
      h("dl", { class: "facts" },
        h("dt", {}, t("fCategory")), h("dd", {}, tr("category", r.category)),
        h("dt", {}, t("fPriority")), h("dd", {}, h("span", { class: "prio " + r.priority }, tr("priority", r.priority))),
        h("dt", {}, t("fAssess")), h("dd", {}, h("span", { class: "mode " + r.ai_mode }, r.ai_mode === "llm" ? t("modeLlm") : t("modeRules")))),
      h("div", { class: "row-actions" },
        h("button", { type: "button", class: "btn primary", onclick: () => go("track", r.ticket_id) }, t("trackThis")),
        h("button", { type: "button", class: "btn", onclick: (e) => copyId(e.currentTarget, r.ticket_id) }, t("copyId")),
        h("button", { type: "button", class: "btn quiet", onclick: () => { state.submitted = null; $("#report-form").reset(); renderConfirmation(); } }, t("another"))));
  }

  async function copyId(btn, id) {
    try { await navigator.clipboard.writeText(id); btn.textContent = t("copied"); setTimeout(() => (btn.textContent = t("copyId")), 1500); }
    catch (e) { /* clipboard unavailable: the ID is selectable on screen */ }
  }

  async function submitReport(ev) {
    ev.preventDefault();
    const err = $("#report-error");
    const location_ = $("#f-location").value.trim();
    const description = $("#f-description").value.trim();
    const photo = $("#f-photo").files[0];
    show(err, "");
    if (location_.length < 3) return show(err, t("errLocation"));
    if (description.length < 10) return show(err, t("errDescription"));
    if (photo && !["image/jpeg", "image/png", "image/webp"].includes(photo.type)) return show(err, t("errPhotoType"));
    if (photo && photo.size > MAX_PHOTO) return show(err, t("errPhotoSize"));

    const fd = new FormData();
    fd.append("location", location_);
    fd.append("description", description);
    fd.append("language", lang);
    if (photo) fd.append("photo", photo);
    const btn = $("#report-submit");
    btn.disabled = true; btn.textContent = t("submitting");
    try {
      state.submitted = await api("/api/complaints", { method: "POST", body: fd });
      renderConfirmation();
      $("#confirmation").scrollIntoView({ block: "start" });
    } catch (e) {
      show(err, e.message);
    } finally {
      btn.disabled = false; btn.textContent = t("submit");
    }
  }

  // ---------- track ----------
  function statusProgress(status) {
    const idx = STATUSES.indexOf(status);
    return h("ol", { class: "progress", "aria-label": t("fStatus") },
      STATUSES.map((s, i) => h("li", { class: (i <= idx ? "done " : "") + (i === idx ? "current" : ""), "aria-current": i === idx ? "step" : null }, tr("status", s))));
  }

  function renderTrack() {
    const box = $("#track-result");
    const r = state.tracked;
    if (!r) return box.replaceChildren();
    box.replaceChildren(h("div", { class: "panel" },
      h("div", { class: "plate compact" }, h("span", {}, r.ticket_id)),
      r.is_demo ? h("span", { class: "chip demo", style: "margin-left:.6rem" }, "DEMO") : null,
      statusProgress(r.status),
      h("dl", { class: "facts" },
        h("dt", {}, t("fCategory")), h("dd", {}, tr("category", r.category)),
        h("dt", {}, t("fPriority")), h("dd", {}, h("span", { class: "prio " + r.priority }, tr("priority", r.priority))),
        h("dt", {}, t("fDepartment")), h("dd", {}, r.department),
        h("dt", {}, t("fRelated")), h("dd", {}, r.related_count ? t("relatedCount", { n: r.related_count }) : t("relatedNone")),
        h("dt", {}, t("fRecommend")), h("dd", {}, r.recommendation),
        h("dt", {}, t("fAssess")), h("dd", {}, h("span", { class: "mode " + r.ai_mode }, r.ai_mode === "llm" ? t("modeLlm") : t("modeRules"))),
        h("dt", {}, t("fLocation")), h("dd", {}, r.location),
        h("dt", {}, t("fDescription")), h("dd", { class: "desc" }, r.description),
        r.image_url ? h("dt", {}, t("fPhoto")) : null, r.image_url ? h("dd", {}, h("img", { src: r.image_url, alt: t("fPhoto") })) : null,
        h("dt", {}, t("fUpdated")), h("dd", {}, fmtDate(r.updated_at))),
      h("p", { class: "small", style: "margin-top:.9rem" }, t("dynNote"))));
  }

  async function lookup(id) {
    const err = $("#track-error");
    show(err, "");
    id = (id || "").trim();
    state.tracked = null; renderTrack();
    if (!id) return show(err, t("enterId"));
    try {
      state.tracked = await api("/api/complaints/" + encodeURIComponent(id));
      renderTrack();
    } catch (e) {
      show(err, e.status === 404 ? t("notFound") : e.message);
    }
  }

  // ---------- authority ----------
  function fillFilterOptions() {
    const fp = $("#flt-priority"), fs = $("#flt-status");
    const pv = fp.value, sv = fs.value;
    fp.replaceChildren(h("option", { value: "" }, t("all")), ...PRIORITIES.map((p) => h("option", { value: p }, tr("priority", p))));
    fs.replaceChildren(h("option", { value: "" }, t("all")), ...STATUSES.map((s) => h("option", { value: s }, tr("status", s))));
    fp.value = pv; fs.value = sv;
  }

  function renderKpis() {
    const m = state.queue && state.queue.metrics;
    const box = $("#kpis");
    if (!m) return box.replaceChildren();
    const item = (label, n) => h("div", {}, h("dt", {}, label), h("dd", {}, String(n)));
    box.replaceChildren(item(t("kpiTotal"), m.total), item(t("kpiHigh"), m.high_priority), item(t("kpiClusters"), m.clusters), item(t("kpiResolved"), m.resolved));
  }

  function reasonBlock(c) {
    return h("div", {},
      h("h3", {}, t("reasoning")),
      h("div", { class: "meter", role: "img", "aria-label": t("score", { s: c.priority_score }) },
        c.priority_reasons.map((r) => h("i", { style: `width:${r.points}%;background:${FACTOR_COLORS[r.factor] || "#888"}`, title: tr("factor", r.factor) }))),
      h("p", { class: "small", style: "margin-top:.4rem" }, t("score", { s: c.priority_score }) + ". " + t("severityOf", { s: c.severity })),
      h("ul", { class: "reasons" },
        c.priority_reasons.map((r) => h("li", {},
          h("span", { class: "sw", style: `background:${FACTOR_COLORS[r.factor] || "#888"}` }),
          h("b", {}, "+" + r.points),
          h("span", {}, h("strong", {}, tr("factor", r.factor)), " ", h("span", { class: "small" }, r.detail))))),
      h("p", { class: "small", style: "margin-top:.5rem" }, t("disclaimer")));
  }

  function queueCard(c) {
    const select = h("select", { id: "st-" + c.ticket_id, onchange: (e) => changeStatus(c.ticket_id, e.target.value) },
      STATUSES.map((s) => h("option", { value: s, selected: s === c.status }, tr("status", s))));
    const details = h("details", { class: "more", open: state.open.has(c.ticket_id) || null, ontoggle: (e) => { e.target.open ? state.open.add(c.ticket_id) : state.open.delete(c.ticket_id); } },
      h("summary", {}, t("showDetails")),
      h("div", { class: "more-body" },
        reasonBlock(c),
        h("div", {}, h("h3", {}, t("fRecommend")), h("p", {}, c.recommendation), h("p", { class: "small" }, c.department)),
        h("div", {}, h("h3", {}, t("original")), h("p", { class: "desc" }, c.description),
          c.image_url ? h("img", { src: c.image_url, alt: t("fPhoto"), style: "max-width:100%;max-height:220px;margin-top:.5rem;border-radius:6px" }) : null),
        c.related_tickets.length ? h("div", {}, h("h3", {}, t("relatedTickets")), h("p", {}, c.related_tickets.join(", ")), h("p", { class: "small" }, t("relatedNote"))) : null));
    return h("article", { class: "card " + c.priority },
      h("div", { class: "card-top" },
        h("div", {},
          h("div", { class: "card-title" }, tr("category", c.category)),
          h("p", { class: "card-meta" }, c.location),
          h("p", { class: "card-meta" }, c.summary)),
        h("div", { class: "card-side" },
          h("span", { class: "prio " + c.priority }, tr("priority", c.priority) + " " + c.priority_score),
          h("label", { for: "st-" + c.ticket_id }, t("fStatus")), select)),
      h("div", { class: "chips" },
        h("span", { class: "chip" }, c.ticket_id),
        c.is_demo ? h("span", { class: "chip demo" }, "DEMO") : null,
        c.related_count ? h("span", { class: "chip" }, t("possiblyRelated", { n: c.related_count })) : null,
        h("span", { class: "chip" }, c.ai_mode === "llm" ? t("modeLlm") : t("modeRules"))),
      details);
  }

  function renderQueue() {
    const box = $("#queue");
    if (!state.queue) return box.replaceChildren();
    const list = state.queue.complaints;
    box.replaceChildren(...(list.length ? list.map(queueCard) : [h("div", { class: "empty" }, t("queueEmpty"))]));
    const toast = $("#toast");
    toast.hidden = !state.toast;
    toast.textContent = state.toast ? t(state.toast.key, state.toast.vars) : "";
  }

  async function loadQueue() {
    const q = new URLSearchParams();
    if ($("#flt-priority").value) q.set("priority", $("#flt-priority").value);
    if ($("#flt-status").value) q.set("status", $("#flt-status").value);
    show($("#queue-error"), "");
    try {
      state.queue = await api("/api/admin/complaints?" + q);
      renderKpis(); renderQueue();
    } catch (e) { show($("#queue-error"), e.message); }
  }

  async function changeStatus(ticket, status) {
    try {
      await api("/api/complaints/" + ticket + "/status", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }) });
      state.toast = { key: "toastUpdated", vars: { id: ticket, status: tr("status", status) } };
      await loadQueue();
    } catch (e) { show($("#queue-error"), e.message); loadQueue(); }
  }

  async function demo(action) {
    try {
      if (action === "seed") {
        const r = await api("/api/demo/seed", { method: "POST" });
        state.toast = { key: r.seeded ? "demoLoaded" : "demoExists" };
      } else {
        const r = await api("/api/demo/clear", { method: "DELETE" });
        state.toast = { key: "demoCleared", vars: { n: r.deleted } };
      }
      await loadQueue();
    } catch (e) { show($("#queue-error"), e.message); }
  }

  // ---------- init ----------
  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => go(b.dataset.view)));
  $("#lang").addEventListener("change", (e) => setLang(e.target.value));
  $("#report-form").addEventListener("submit", submitReport);
  $("#track-form").addEventListener("submit", (e) => { e.preventDefault(); const id = $("#t-id").value.trim(); if (id) history.replaceState(null, "", "#track/" + id.toUpperCase()); lookup(id); });
  $("#flt-priority").addEventListener("change", loadQueue);
  $("#flt-status").addEventListener("change", loadQueue);
  $("#demo-seed").addEventListener("click", () => demo("seed"));
  $("#demo-clear").addEventListener("click", () => demo("clear"));
  window.addEventListener("hashchange", route);
  applyStaticText();
  route();
})();
