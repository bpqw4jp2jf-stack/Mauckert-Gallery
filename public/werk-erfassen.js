// Client-Logik für das Werk-Erfassen-Tool (siehe src/pages/werk-erfassen.astro).
(() => {
  const cfg = JSON.parse(document.getElementById("erfassung-config").textContent);
  const felder = cfg.felder;
  const pflicht = cfg.pflicht;
  const listEl = document.getElementById("list");
  const progressEl = document.getElementById("progress");
  const savedEl = document.getElementById("savedState");
  const saveBtn = document.getElementById("saveBtn");
  const nextBtn = document.getElementById("nextBtn");
  const resortBtn = document.getElementById("resortBtn");
  const onlyIncomplete = document.getElementById("onlyIncomplete");

  const statusOptionen = ["verfügbar", "verkauft", "reserviert", "nicht verkäuflich"];
  let records = [];
  let order = [];
  let dirty = false;
  let saveTimer = null;

  const isMissing = (rec, key) => pflicht.includes(key) && !String(rec[key] ?? "").trim();
  const fehlt = (rec) => pflicht.filter((k) => !String(rec[k] ?? "").trim());
  const complete = (rec) => fehlt(rec).length === 0;

  function esc(s) {
    return String(s ?? "").replace(/[&<>"]/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c],
    );
  }

  function numberFor(id) {
    const o = order.find((x) => x.record.id === id);
    return o ? o.nummer : null;
  }

  function cardHtml(rec) {
    const nr = numberFor(rec.id);
    const miss = fehlt(rec);
    const ok = miss.length === 0;
    const fieldsHtml = felder
      .map((f) => {
        const missing = isMissing(rec, f.key);
        const cls = "field" + (f.type === "textarea" ? " full" : "") + (missing ? " missing" : "");
        let control;
        if (f.type === "textarea") {
          control = `<textarea data-id="${rec.id}" data-key="${f.key}">${esc(rec[f.key])}</textarea>`;
        } else if (f.type === "status") {
          const opts = statusOptionen
            .map((o) => `<option value="${o}"${o === rec[f.key] ? " selected" : ""}>${o}</option>`)
            .join("");
          const cur = rec[f.key] && !statusOptionen.includes(rec[f.key])
            ? `<option value="${esc(rec[f.key])}" selected>${esc(rec[f.key])}</option>`
            : "";
          control = `<select data-id="${rec.id}" data-key="${f.key}"><option value=""></option>${cur}${opts}</select>`;
        } else {
          control = `<input type="text" data-id="${rec.id}" data-key="${f.key}" value="${esc(rec[f.key])}" />`;
        }
        return `<div class="${cls}"><label>${f.label}</label>${control}</div>`;
      })
      .join("");

    return `
      <div class="card ${ok ? "" : "incomplete"}" id="card-${rec.id}" data-id="${rec.id}">
        <div class="photo">
          <span class="nr">${nr ? "Nr. " + nr : "—"}</span>
          ${rec.bild ? `<img src="${esc(rec.bild)}" alt="${esc(rec.titel)}" loading="lazy" />` : ""}
          <span class="badge ${ok ? "ok" : "miss"}">${ok ? "✓ vollständig" : miss.length + " fehlt"}</span>
          <span class="quelle">${rec.quelle}</span>
        </div>
        <div class="fields">${fieldsHtml}</div>
      </div>`;
  }

  function render() {
    const ordered = order.map((o) => records.find((r) => r.id === o.record.id)).filter(Boolean);
    const showOnly = onlyIncomplete.checked;
    listEl.innerHTML = ordered
      .filter((r) => !showOnly || !complete(r))
      .map(cardHtml)
      .join("");
    updateProgress();
  }

  function updateProgress() {
    const total = records.length;
    const done = records.filter(complete).length;
    progressEl.textContent = `${done} von ${total} vollständig`;
  }

  function refreshCard(id) {
    const rec = records.find((r) => r.id === id);
    const card = document.getElementById("card-" + id);
    if (!rec || !card) return;
    const miss = fehlt(rec);
    const ok = miss.length === 0;
    card.classList.toggle("incomplete", !ok);
    const badge = card.querySelector(".badge");
    badge.className = "badge " + (ok ? "ok" : "miss");
    badge.textContent = ok ? "✓ vollständig" : miss.length + " fehlt";
    card.querySelectorAll("[data-key]").forEach((el) => {
      const key = el.dataset.key;
      el.parentElement.classList.toggle("missing", isMissing(rec, key));
    });
    updateProgress();
  }

  function onEdit(e) {
    const el = e.target;
    if (!el.dataset || !el.dataset.id) return;
    const rec = records.find((r) => r.id === el.dataset.id);
    if (!rec) return;
    rec[el.dataset.key] = el.value;
    refreshCard(rec.id);
    scheduleSave();
  }

  function scheduleSave() {
    dirty = true;
    savedEl.textContent = "ungespeichert …";
    clearTimeout(saveTimer);
    saveTimer = setTimeout(save, 900);
  }

  async function save() {
    clearTimeout(saveTimer);
    if (!dirty) return;
    savedEl.textContent = "speichert …";
    saveBtn.disabled = true;
    try {
      const res = await fetch("/api/erfassung", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ records }),
      });
      const data = await res.json();
      order = data.order;
      dirty = false;
      // Nummern aktualisieren, ohne DOM neu zu ordnen
      document.querySelectorAll(".card").forEach((card) => {
        const nr = numberFor(card.dataset.id);
        card.querySelector(".nr").textContent = nr ? "Nr. " + nr : "—";
      });
      savedEl.textContent = "gespeichert ✓";
    } catch (err) {
      savedEl.textContent = "Fehler beim Speichern";
      console.error(err);
    } finally {
      saveBtn.disabled = false;
    }
  }

  function nextIncomplete() {
    const cards = [...document.querySelectorAll(".card.incomplete")];
    const y = window.scrollY + 80;
    const next = cards.find((c) => c.getBoundingClientRect().top + window.scrollY > y) || cards[0];
    if (next) {
      next.scrollIntoView({ behavior: "smooth", block: "start" });
      const input = next.querySelector(".field.missing input, .field.missing select");
      if (input) setTimeout(() => input.focus(), 350);
    }
  }

  listEl.addEventListener("input", onEdit);
  listEl.addEventListener("change", onEdit);
  saveBtn.addEventListener("click", save);
  nextBtn.addEventListener("click", nextIncomplete);
  resortBtn.addEventListener("click", render);
  onlyIncomplete.addEventListener("change", render);

  (async () => {
    const res = await fetch("/api/erfassung");
    const data = await res.json();
    records = data.records;
    order = data.order;
    render();
  })();
})();
