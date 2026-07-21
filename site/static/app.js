/* global L, SITE_BASE */

(function () {
  "use strict";

  const base = typeof SITE_BASE === "string" ? SITE_BASE : "/";

  /** @type {Array<any>} */
  let streets = [];
  /** @type {any} */
  let meta = {};
  /** @type {Array<any>} */
  let filtered = [];

  /** @type {L.Map | null} */
  let map = null;
  /** @type {L.LayerGroup | null} */
  let layerGroup = null;
  /** @type {L.Map | null} */
  let detailMap = null;
  /** @type {L.Layer | null} */
  let detailLine = null;

  const els = {
    search: document.getElementById("search"),
    category: document.getElementById("category"),
    tag: document.getElementById("tag"),
    district: document.getElementById("district"),
    districtField: document.querySelector(".district-field"),
    matchCount: document.getElementById("match-count"),
    streetCount: document.getElementById("street-count"),
    list: document.getElementById("list"),
    legend: document.getElementById("map-legend"),
    viewMap: document.getElementById("view-map"),
    viewList: document.getElementById("view-list"),
    tabs: Array.from(document.querySelectorAll(".tab")),
    detail: document.getElementById("detail"),
    detailBody: document.getElementById("detail-body"),
    detailMap: document.getElementById("detail-map"),
    detailClose: document.getElementById("detail-close"),
    detailBackdrop: document.getElementById("detail-backdrop"),
  };

  function dataUrl(path) {
    return base.replace(/\/?$/, "/") + path.replace(/^\//, "");
  }

  // Google encoded polyline decoder (precision 5).
  // Multiple independent paths for one street are joined with ';'
  // (semicolon is outside the Google polyline character set).
  function decodePolyline(str) {
    if (!str) return [];
    let index = 0;
    const len = str.length;
    let lat = 0;
    let lng = 0;
    const coordinates = [];

    while (index < len) {
      let result = 0;
      let shift = 0;
      let b;
      do {
        b = str.charCodeAt(index++) - 63;
        result |= (b & 0x1f) << shift;
        shift += 5;
      } while (b >= 0x20);
      const dlat = result & 1 ? ~(result >> 1) : result >> 1;
      lat += dlat;

      result = 0;
      shift = 0;
      do {
        b = str.charCodeAt(index++) - 63;
        result |= (b & 0x1f) << shift;
        shift += 5;
      } while (b >= 0x20);
      const dlng = result & 1 ? ~(result >> 1) : result >> 1;
      lng += dlng;

      coordinates.push([lat / 1e5, lng / 1e5]);
    }
    return coordinates;
  }

  /** @returns {Array<Array<[number, number]>>} */
  function decodeStreetPolylines(str) {
    if (!str) return [];
    return str
      .split(";")
      .map(decodePolyline)
      .filter((coords) => coords.length >= 2);
  }

  function colorFor(category) {
    return (meta.category_colors && meta.category_colors[category]) || "#666666";
  }

  function fillSelect(select, values, allLabel) {
    const current = select.value;
    select.innerHTML = "";
    const all = document.createElement("option");
    all.value = "";
    all.textContent = allLabel;
    select.appendChild(all);
    for (const value of values) {
      const opt = document.createElement("option");
      opt.value = value;
      opt.textContent = value;
      select.appendChild(opt);
    }
    if ([...select.options].some((o) => o.value === current)) {
      select.value = current;
    }
  }

  function applyFilters() {
    const q = (els.search.value || "").trim().toLowerCase();
    const category = els.category.value;
    const tag = els.tag.value;
    const district = els.district.value;

    filtered = streets.filter((street) => {
      if (category && street.category !== category) return false;
      if (tag && !(street.tags || []).includes(tag)) return false;
      if (district && street.district !== district) return false;
      if (q) {
        const hay = [
          street.name,
          street.category,
          ...(street.tags || []),
          ...(street.aliases || []),
          street.district || "",
        ]
          .join(" ")
          .toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    els.matchCount.textContent = String(filtered.length);
    renderList();
    renderMapLayers();
  }

  function renderLegend() {
    const categories = meta.categories || [];
    const items = categories
      .map(
        (c) =>
          `<div class="legend-item"><span class="swatch" style="background:${colorFor(c)}"></span>${escapeHtml(c)}</div>`
      )
      .join("");
    els.legend.innerHTML = `<h3>Categories</h3>${items}`;
  }

  function renderList() {
    if (!filtered.length) {
      els.list.innerHTML = `<p class="empty-state">No streets match these filters.</p>`;
      return;
    }

    const maxCards = 500;
    const slice = filtered.slice(0, maxCards);
    const cards = slice
      .map((street) => {
        const tags = (street.tags || [])
          .slice(0, 3)
          .map((t) => `<span class="pill tag">${escapeHtml(t)}</span>`)
          .join("");
        return `<button type="button" class="street-card" data-name="${escapeAttr(street.name)}">
          <span class="name">${escapeHtml(street.name)}</span>
          <span class="meta">
            <span class="pill" style="background:${colorFor(street.category)}22;color:${colorFor(street.category)}">${escapeHtml(street.category)}</span>
            ${tags}
          </span>
        </button>`;
      })
      .join("");

    const more =
      filtered.length > maxCards
        ? `<p class="empty-state">Showing first ${maxCards} of ${filtered.length}. Narrow filters to see more.</p>`
        : "";
    els.list.innerHTML = cards + more;
  }

  function renderMapLayers() {
    if (!map || !layerGroup) return;
    layerGroup.clearLayers();

    const bounds = [];
    // Cap drawn polylines for responsiveness when unfiltered.
    const maxDraw = 2500;
    const toDraw = filtered.length > maxDraw ? filtered.slice(0, maxDraw) : filtered;

    for (const street of toDraw) {
      const paths = decodeStreetPolylines(street.polyline);
      if (!paths.length) continue;
      const style = {
        color: colorFor(street.category),
        weight: 3,
        opacity: 0.75,
      };
      for (const coords of paths) {
        const line = L.polyline(coords, style);
        line.bindTooltip(street.name);
        line.on("click", () => openDetail(street.name));
        layerGroup.addLayer(line);
        for (const c of coords) bounds.push(c);
      }
    }

    if (bounds.length) {
      map.fitBounds(bounds, { padding: [24, 24], maxZoom: 15 });
    }
  }

  function ensureMap() {
    if (map) {
      setTimeout(() => map.invalidateSize(), 50);
      return;
    }
    map = L.map("map", {
      zoomControl: true,
      preferCanvas: true,
    }).setView([1.3521, 103.8198], 12);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap",
    }).addTo(map);

    layerGroup = L.layerGroup().addTo(map);
    renderMapLayers();
  }

  function setView(name) {
    const isMap = name === "map";
    els.viewMap.classList.toggle("hidden", !isMap);
    els.viewList.classList.toggle("hidden", isMap);
    for (const tab of els.tabs) {
      const active = tab.dataset.view === name;
      tab.classList.toggle("active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    }
    if (isMap) ensureMap();
    const url = new URL(window.location.href);
    if (isMap) url.searchParams.delete("view");
    else url.searchParams.set("view", "list");
    history.replaceState(null, "", url);
  }

  function findStreet(name) {
    return streets.find((s) => s.name === name) || null;
  }

  function openDetail(name) {
    const street = findStreet(name);
    if (!street) return;

    const tags = (street.tags || [])
      .map((t) => `<span class="pill tag">${escapeHtml(t)}</span>`)
      .join(" ");
    const aliases = (street.aliases || []).map(escapeHtml).join(", ");

    const rows = [
      ["Category", escapeHtml(street.category)],
      tags ? ["Tags", tags] : null,
      aliases ? ["Aliases", aliases] : null,
      street.district ? ["District", escapeHtml(street.district)] : null,
      street.etymology ? ["Etymology", escapeHtml(street.etymology)] : null,
      street.memory_note ? ["Memory", escapeHtml(street.memory_note)] : null,
    ].filter(Boolean);

    const dl = rows
      .map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`)
      .join("");

    els.detailBody.innerHTML = `
      <h2>${escapeHtml(street.name)}</h2>
      <div class="detail-meta">
        <span class="pill" style="background:${colorFor(street.category)}22;color:${colorFor(street.category)}">${escapeHtml(street.category)}</span>
        ${tags}
      </div>
      <dl>${dl}</dl>
    `;

    els.detail.classList.remove("hidden");
    els.detailBackdrop.classList.remove("hidden");

    const paths = decodeStreetPolylines(street.polyline);
    if (paths.length) {
      els.detailMap.classList.remove("hidden");
      if (!detailMap) {
        detailMap = L.map(els.detailMap, {
          zoomControl: false,
          attributionControl: false,
          preferCanvas: true,
        });
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          maxZoom: 19,
        }).addTo(detailMap);
      }
      if (detailLine) detailMap.removeLayer(detailLine);
      const style = {
        color: colorFor(street.category),
        weight: 5,
        opacity: 0.9,
      };
      detailLine = L.featureGroup(
        paths.map((coords) => L.polyline(coords, style))
      ).addTo(detailMap);
      setTimeout(() => {
        detailMap.invalidateSize();
        detailMap.fitBounds(detailLine.getBounds(), { padding: [16, 16], maxZoom: 17 });
      }, 50);
    } else {
      els.detailMap.classList.add("hidden");
    }

    const url = new URL(window.location.href);
    url.searchParams.set("street", street.name);
    history.replaceState(null, "", url);
  }

  function closeDetail() {
    els.detail.classList.add("hidden");
    els.detailBackdrop.classList.add("hidden");
    const url = new URL(window.location.href);
    url.searchParams.delete("street");
    history.replaceState(null, "", url);
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replace(/'/g, "&#39;");
  }

  function wireEvents() {
    for (const input of [els.search, els.category, els.tag, els.district]) {
      input.addEventListener("input", applyFilters);
      input.addEventListener("change", applyFilters);
    }

    for (const tab of els.tabs) {
      tab.addEventListener("click", () => setView(tab.dataset.view));
    }

    els.list.addEventListener("click", (event) => {
      const btn = event.target.closest(".street-card");
      if (!btn) return;
      openDetail(btn.dataset.name);
    });

    els.detailClose.addEventListener("click", closeDetail);
    els.detailBackdrop.addEventListener("click", closeDetail);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeDetail();
    });
  }

  async function loadGzipJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to load ${url}: ${response.status}`);
    }
    if (!window.DecompressionStream) {
      throw new Error("Browser does not support DecompressionStream (gzip)");
    }
    const stream = response.body.pipeThrough(new DecompressionStream("gzip"));
    const text = await new Response(stream).text();
    return JSON.parse(text);
  }

  async function init() {
    let metaRes;
    try {
      const [loadedStreets, loadedMetaRes] = await Promise.all([
        loadGzipJson(dataUrl("data/streets.json.gz")),
        fetch(dataUrl("data/meta.json")),
      ]);
      streets = loadedStreets;
      metaRes = loadedMetaRes;
    } catch (err) {
      document.body.insertAdjacentHTML(
        "afterbegin",
        `<p class="empty-state">Failed to load catalog data.</p>`
      );
      console.error(err);
      return;
    }
    if (!metaRes.ok) {
      document.body.insertAdjacentHTML(
        "afterbegin",
        `<p class="empty-state">Failed to load catalog data.</p>`
      );
      return;
    }
    meta = await metaRes.json();

    if (els.streetCount) {
      els.streetCount.textContent = Number(meta.count || streets.length).toLocaleString();
    }

    fillSelect(els.category, meta.categories || [], "All categories");
    fillSelect(els.tag, meta.tags || [], "All tags");

    if (meta.has_district) {
      els.districtField.classList.remove("hidden");
      const districts = [
        ...new Set(streets.map((s) => s.district).filter(Boolean)),
      ].sort((a, b) => a.localeCompare(b));
      fillSelect(els.district, districts, "All districts");
    }

    renderLegend();
    wireEvents();
    applyFilters();

    const params = new URLSearchParams(window.location.search);
    setView(params.get("view") === "list" ? "list" : "map");
    const street = params.get("street");
    if (street) openDetail(street);
  }

  init();
})();
