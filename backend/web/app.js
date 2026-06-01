(function () {
  const form = document.getElementById("chart-form");
  const formSection = document.getElementById("form-section");
  const loading = document.getElementById("loading");
  const errorPanel = document.getElementById("error-panel");
  const errorText = document.getElementById("error-text");
  const results = document.getElementById("results");
  const submitBtn = document.getElementById("submit-btn");
  const retryBtn = document.getElementById("retry-btn");
  const statusHint = document.getElementById("status-hint");

  let engineMode = "WESTERN";
  let lastPayload = null;

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

  function showLoading(on) {
    loading.hidden = !on;
    submitBtn.disabled = on;
  }

  function showError(msg) {
    errorPanel.hidden = false;
    results.hidden = true;
    errorText.textContent = msg || "Unknown error";
  }

  function hideError() {
    errorPanel.hidden = true;
  }

  function buildPayload() {
    const age = parseFloat(document.getElementById("current_age").value, 10);
    return {
      display_name: document.getElementById("display_name").value.trim(),
      birth_date: document.getElementById("birth_date").value,
      birth_time: document.getElementById("birth_time").value.slice(0, 5),
      latitude: parseFloat(document.getElementById("latitude").value, 10),
      longitude: parseFloat(document.getElementById("longitude").value, 10),
      timezone_id: document.getElementById("timezone_id").value.trim(),
      current_age: Number.isFinite(age) ? age : 25,
      is_nocturnal: document.getElementById("is_nocturnal").checked,
      persist: false,
    };
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
})();
