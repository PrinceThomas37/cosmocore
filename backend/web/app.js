(function () {
  const GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search";

  const form = document.getElementById("chart-form");
  const loading = document.getElementById("loading");
  const errorPanel = document.getElementById("error-panel");
  const errorText = document.getElementById("error-text");
  const results = document.getElementById("results");
  const submitBtn = document.getElementById("submit-btn");
  const retryBtn = document.getElementById("retry-btn");
  const statusHint = document.getElementById("status-hint");

  const birthPlace = document.getElementById("birth_place");
  const placeSuggestions = document.getElementById("place-suggestions");
  const placeStatus = document.getElementById("place-status");
  const coordsPanel = document.getElementById("coords-panel");
  const latInput = document.getElementById("latitude");
  const lonInput = document.getElementById("longitude");
  const tzInput = document.getElementById("timezone_id");

  let engineMode = "WESTERN";
  let lastPayload = null;
  let selectedPlace = null;
  let searchTimer = null;

  const tabs = document.querySelectorAll(".tab");
  const panelWestern = document.getElementById("panel-western");
  const panelVedic = document.getElementById("panel-vedic");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      engineMode = tab.dataset.mode;
      tabs.forEach((t) => {
        const active = t.dataset.mode === engineMode;
        t.classList.toggle("active", active);
        t.setAttribute("aria-selected", active ? "true" : "false");
      });
      panelWestern.hidden = engineMode !== "WESTERN";
      panelVedic.hidden = engineMode !== "VEDIC";
    });
  });

  function formatPlaceLabel(item) {
    const parts = [item.name];
    if (item.admin1) parts.push(item.admin1);
    if (item.country) parts.push(item.country);
    return parts.join(", ");
  }

  function applyPlace(item) {
    selectedPlace = item;
    birthPlace.value = formatPlaceLabel(item);
    latInput.value = Number(item.latitude).toFixed(5);
    lonInput.value = Number(item.longitude).toFixed(5);
    tzInput.value = item.timezone || "";
    coordsPanel.hidden = false;
    placeSuggestions.hidden = true;
    placeSuggestions.replaceChildren();
    placeStatus.textContent = `Using ${formatPlaceLabel(item)} • ${item.timezone}`;
    placeStatus.classList.remove("error");
    updateSubmitState();
  }

  function clearPlace() {
    selectedPlace = null;
    latInput.value = "";
    lonInput.value = "";
    tzInput.value = "";
    coordsPanel.hidden = true;
    updateSubmitState();
  }

  function updateSubmitState() {
    const hasPlace =
      selectedPlace &&
      latInput.value &&
      lonInput.value &&
      tzInput.value;
    submitBtn.disabled = !hasPlace;
  }

  async function searchPlaces(query) {
    const url = `${GEOCODE_URL}?name=${encodeURIComponent(query)}&count=6&language=en`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Place search failed");
    const data = await res.json();
    return data.results || [];
  }

  function showSuggestions(items) {
    placeSuggestions.replaceChildren();
    if (!items.length) {
      placeSuggestions.hidden = true;
      placeStatus.textContent = "No places found — try a nearby city name.";
      placeStatus.classList.add("error");
      return;
    }
    items.forEach((item) => {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = formatPlaceLabel(item);
      btn.addEventListener("click", () => applyPlace(item));
      li.appendChild(btn);
      placeSuggestions.appendChild(li);
    });
    placeSuggestions.hidden = false;
    placeStatus.textContent = "Pick your birth place from the list.";
    placeStatus.classList.remove("error");
  }

  birthPlace.addEventListener("input", () => {
    clearPlace();
    const q = birthPlace.value.trim();
    if (searchTimer) clearTimeout(searchTimer);
    if (q.length < 2) {
      placeSuggestions.hidden = true;
      placeStatus.textContent = "Type at least 2 letters, then choose from the list.";
      placeStatus.classList.remove("error");
      return;
    }
    placeStatus.textContent = "Searching…";
    searchTimer = setTimeout(async () => {
      try {
        const items = await searchPlaces(q);
        showSuggestions(items);
      } catch {
        placeStatus.textContent = "Could not search places. Check your connection.";
        placeStatus.classList.add("error");
      }
    }, 350);
  });

  function ageFromBirthDate(birthDateStr) {
    const birth = new Date(birthDateStr + "T12:00:00");
    const now = new Date();
    const ms = now - birth;
    return Math.max(0, ms / (365.25 * 24 * 60 * 60 * 1000));
  }

  function buildPayload() {
    return {
      display_name: document.getElementById("display_name").value.trim(),
      birth_date: document.getElementById("birth_date").value,
      birth_time: document.getElementById("birth_time").value.slice(0, 5),
      latitude: parseFloat(latInput.value, 10),
      longitude: parseFloat(lonInput.value, 10),
      timezone_id: tzInput.value.trim(),
      current_age: Math.round(ageFromBirthDate(document.getElementById("birth_date").value) * 10) / 10,
      is_nocturnal: document.getElementById("is_nocturnal").checked,
      persist: false,
    };
  }

  function showLoading(on) {
    loading.hidden = !on;
    submitBtn.disabled = on || !selectedPlace;
  }

  function showError(msg) {
    errorPanel.hidden = false;
    results.hidden = true;
    errorText.textContent = msg || "Unknown error";
  }

  function hideError() {
    errorPanel.hidden = true;
  }

  function row(label, value) {
    const div = document.createElement("div");
    div.className = "row";
    div.innerHTML = `<span class="lbl">${label}</span><span class="val">${value}</span>`;
    return div;
  }

  function renderChart(data) {
    const planets = data.western?.planets || {};
    const aspects = data.western?.aspects || [];
    const angles = data.western?.houses?.angles || {};
    const vedicD1 = data.vedic?.d1 || {};
    const vedicD9 = data.vedic?.d9 || {};

    const westernPlanets = document.getElementById("western-planets");
    westernPlanets.replaceChildren();
    ["Sun", "Moon", "Mercury", "Venus", "Mars"].forEach((p) => {
      if (planets[p]) {
        const retro = planets[p].is_retrograde ? " ℞" : "";
        westernPlanets.appendChild(
          row(`${p}:`, `${planets[p].sign} ${planets[p].degree}°${retro}`)
        );
      }
    });

    const westernAngles = document.getElementById("western-angles");
    westernAngles.replaceChildren();
    if (angles.ASC) {
      westernAngles.appendChild(
        row("ASC:", `${angles.ASC.sign} ${angles.ASC.degree}°`)
      );
    }

    const westernAspects = document.getElementById("western-aspects");
    westernAspects.replaceChildren();
    aspects.slice(0, 8).forEach((asp) => {
      const p = document.createElement("p");
      p.className = "aspect-text";
      p.textContent = `${asp.p1} ${asp.aspect} ${asp.p2} (orb ${asp.orb}°)`;
      westernAspects.appendChild(p);
    });

    document.getElementById("vedic-header").textContent =
      `Jyotish • Lahiri ${data.vedic?.ayanamsa ?? "—"}°`;

    const vedicBody = document.getElementById("vedic-body");
    vedicBody.replaceChildren();
    if (vedicD1.Sun) {
      const nk = vedicD1.Sun.nakshatra;
      vedicBody.appendChild(
        row(
          "Sun D-1:",
          `${vedicD1.Sun.sign} • ${nk?.name || "—"} pada ${nk?.pada ?? "—"}`
        )
      );
      vedicBody.appendChild(row("Sun D-9:", vedicD9.Sun?.sign || "—"));
    }
    if (data.vedic?.dashas?.current_mahadasha) {
      vedicBody.appendChild(
        row("Mahadasha:", data.vedic.dashas.current_mahadasha)
      );
    }

    const f = data.firdaria || {};
    document.getElementById("firdaria-text").textContent =
      `Major: ${f.major || "—"} • Sub: ${f.sub || "—"}`;
    document.getElementById("firdaria-progress").style.width =
      `${f.progress || 0}%`;

    const acg = document.getElementById("acg-lines");
    acg.replaceChildren();
    const vectors = data.astrocartography?.Sun?.vectors || [];
    vectors.slice(0, 4).forEach((vec) => {
      const p = document.createElement("p");
      p.className = "aspect-text";
      p.textContent = `• h${vec.hour_meridian}: lat ${vec.lat}, lon ${vec.lon}`;
      acg.appendChild(p);
    });

    hideError();
    results.hidden = false;
    statusHint.hidden = false;
    statusHint.textContent = `Chart for ${data.display_name} • UTC ${data.utc_time || ""}`;
  }

  async function fetchChart(payload) {
    if (!payload.timezone_id || !Number.isFinite(payload.latitude)) {
      showError("Please select your place of birth from the search list first.");
      return;
    }

    lastPayload = payload;
    hideError();
    showLoading(true);

    try {
      const res = await fetch("/api/v1/chart/compute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = json.detail;
        throw new Error(
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
              ? detail.map((d) => d.msg || JSON.stringify(d)).join("; ")
              : res.statusText
        );
      }
      renderChart(json);
    } catch (err) {
      showError(String(err.message || err));
    } finally {
      showLoading(false);
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    fetchChart(buildPayload());
  });

  retryBtn.addEventListener("click", () => {
    if (lastPayload) fetchChart(lastPayload);
    else form.requestSubmit();
  });

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".field-place")) {
      placeSuggestions.hidden = true;
    }
  });

  updateSubmitState();
})();
