const STORAGE_KEY = "ridplier_extension_profile_v1";

const PROFILE_FIELDS = [
  { key: "first_name", label: "First Name", placeholder: "e.g. Jane" },
  { key: "last_name", label: "Last Name", placeholder: "e.g. Doe" },
  { key: "email", label: "Email", placeholder: "e.g. name@email.com" },
  { key: "phone", label: "Phone Number", placeholder: "e.g. 555-123-4567" },
  { key: "address1", label: "Street Address", placeholder: "e.g. 123 Main St" },
  { key: "city", label: "City", placeholder: "e.g. New York" },
  { key: "state", label: "State (2-letter or Full)", placeholder: "e.g. NY or MD" },
  { key: "zip", label: "ZIP / Postal Code", placeholder: "e.g. 10001" },
  { key: "linkedin", label: "LinkedIn URL (Optional)", placeholder: "https://linkedin.com/in/..." },
  { key: "pa_school", label: "PA Program / University", placeholder: "e.g. DeSales University" },
  { key: "degree", label: "Degree", placeholder: "e.g. Master of Science in Physician Assistant Studies" },
  { key: "gpa", label: "GPA (Optional)", placeholder: "e.g. 3.82" },
  { key: "license_summary", label: "NCCPA / State PA License Status", placeholder: "e.g. NCCPA Certified (PA-C); NYS License Pending" },
  { key: "certs_summary", label: "BLS / ACLS / PALS & Courses (Copy Block)", placeholder: "e.g. AHA BLS, ACLS; NYS Infection Control", type: "textarea" },
  { key: "rotations_summary", label: "Clinical Rotations Block (Copy Block)", placeholder: "Emergency Medicine, ENT/Facial Plastics, General Surgery, Urgent Care...", type: "textarea" },
  { key: "referral_source", label: "How Did You Hear About Us?", placeholder: "e.g. Hospital Career Website", default: "Company Website" },
  { key: "salary_expectation", label: "Desired Salary Response", placeholder: "e.g. Open / Negotiable based on range" },
  { key: "work_authorized", label: "Authorized to Work in US?", type: "select", options: ["Yes", "No"], default: "Yes" },
  { key: "require_sponsorship", label: "Require Visa Sponsorship?", type: "select", options: ["No", "Yes"], default: "No" },
  { key: "worked_before", label: "Previously Employed at Hospital?", type: "select", options: ["No", "Yes"], default: "No" },
  { key: "nccpa_certified", label: "NCCPA Certified?", type: "select", options: ["Yes", "No"], default: "Yes" },
  { key: "cover_note", label: "Default Cover Note / Why Us", placeholder: "Short new-grad PA summary...", type: "textarea" },
];

let currentProfile = {};

function setStatus(message, type = "ok") {
  const el = document.getElementById("fill-status");
  el.textContent = message;
  el.className = "status-box" + (type === "warn" ? " warn" : type === "error" ? " error" : "");
}

function getDefaults() {
  const d = {};
  PROFILE_FIELDS.forEach((f) => {
    if (f.default !== undefined) d[f.key] = f.default;
  });
  return d;
}

async function loadProfile() {
  return new Promise((resolve) => {
    chrome.storage.local.get([STORAGE_KEY], (res) => {
      currentProfile = { ...getDefaults(), ...(res[STORAGE_KEY] || {}) };
      resolve(currentProfile);
    });
  });
}

async function saveProfileObj(obj) {
  currentProfile = { ...getDefaults(), ...obj };
  return new Promise((resolve) => {
    chrome.storage.local.set({ [STORAGE_KEY]: currentProfile }, () => resolve());
  });
}

function renderForm() {
  const form = document.getElementById("profile-form");
  form.innerHTML = "";
  PROFILE_FIELDS.forEach((f) => {
    const wrap = document.createElement("div");
    wrap.className = "field-wrap";
    const lbl = document.createElement("label");
    lbl.setAttribute("for", "inp-" + f.key);
    lbl.textContent = f.label;
    wrap.appendChild(lbl);

    let input;
    if (f.type === "select") {
      input = document.createElement("select");
      f.options.forEach((opt) => {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = opt;
        input.appendChild(o);
      });
    } else if (f.type === "textarea") {
      input = document.createElement("textarea");
      input.rows = 2;
      input.placeholder = f.placeholder || "";
    } else {
      input = document.createElement("input");
      input.type = "text";
      input.placeholder = f.placeholder || "";
    }
    input.id = "inp-" + f.key;
    input.value = currentProfile[f.key] || f.default || "";
    wrap.appendChild(input);
    form.appendChild(wrap);
  });
}

function renderQuickCopy() {
  const list = document.getElementById("quick-list");
  list.innerHTML = "";
  const populated = PROFILE_FIELDS.filter((f) => (currentProfile[f.key] || "").trim().length > 0);
  if (populated.length === 0) {
    list.innerHTML = `<div class="privacy-banner">👋 Tap <strong>✏️ Edit Profile</strong> above to save your details once, then use <strong>⚡ Auto-Fill This Page</strong> on any hospital portal!</div>`;
    return;
  }

  PROFILE_FIELDS.forEach((f) => {
    const val = (currentProfile[f.key] || "").trim();
    if (!val) return;
    const item = document.createElement("div");
    item.className = "quick-item";

    const meta = document.createElement("div");
    meta.className = "quick-meta";
    const lbl = document.createElement("div");
    lbl.className = "quick-label";
    lbl.textContent = f.label;
    const valDiv = document.createElement("div");
    valDiv.className = "quick-val";
    valDiv.textContent = val;
    meta.appendChild(lbl);
    meta.appendChild(valDiv);

    const btn = document.createElement("button");
    btn.className = "btn-copy-mini";
    btn.textContent = "Copy";
    btn.addEventListener("click", async () => {
      await navigator.clipboard.writeText(val);
      btn.textContent = "Copied!";
      setTimeout(() => (btn.textContent = "Copy"), 1200);
    });

    item.appendChild(meta);
    item.appendChild(btn);
    list.appendChild(item);
  });
}

function switchTab(tabName) {
  document.querySelectorAll(".tab-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.tab === tabName);
  });
  document.querySelectorAll(".tab-pane").forEach((p) => {
    p.classList.toggle("active", p.id === "tab-" + tabName);
  });
}

async function runAutoFill() {
  const hasAny = Object.entries(currentProfile).some(
    ([k, v]) => !["work_authorized", "require_sponsorship", "worked_before", "nccpa_certified", "referral_source"].includes(k) && String(v || "").trim()
  );
  if (!hasAny) {
    setStatus("Please save your name/email/info under ✏️ Edit Profile first!", "warn");
    switchTab("profile");
    return;
  }

  const overwrite = document.getElementById("chk-overwrite").checked;
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.id) {
      setStatus("No active browser tab found.", "error");
      return;
    }

    await chrome.scripting.executeScript({
      target: { tabId: tab.id, allFrames: true },
      files: ["autofill.js"],
    });

    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id, allFrames: true },
      func: (prof, opts) => {
        if (typeof ridplierAutoFillFrame === "function") {
          return ridplierAutoFillFrame(prof, opts);
        }
        return { filledCount: 0, filledFields: [] };
      },
      args: [currentProfile, { overwrite }],
    });

    const allFilled = [];
    for (const r of results || []) {
      if (r.result && Array.isArray(r.result.filledFields)) {
        allFilled.push(...r.result.filledFields);
      }
    }

    if (allFilled.length === 0) {
      setStatus(
        "No empty matching fields found on this step (or fields already filled). Use Quick Copy for custom dropdowns.",
        "warn"
      );
    } else {
      const uniqueNames = [...new Set(allFilled)];
      setStatus(`✅ Filled ${allFilled.length} field(s): ${uniqueNames.join(", ")}`);
    }
  } catch (err) {
    setStatus("Cannot auto-fill this page (restricted Chrome page or reload tab and try again).", "error");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadProfile();
  renderForm();
  renderQuickCopy();

  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  document.getElementById("btn-autofill").addEventListener("click", runAutoFill);

  document.getElementById("btn-save-profile").addEventListener("click", async () => {
    const next = {};
    PROFILE_FIELDS.forEach((f) => {
      const el = document.getElementById("inp-" + f.key);
      if (el) next[f.key] = el.value.trim();
    });
    await saveProfileObj(next);
    renderQuickCopy();
    setStatus("✅ Profile saved locally! Ready to auto-fill.");
    switchTab("quick");
  });

  document.getElementById("btn-export-json").addEventListener("click", () => {
    document.getElementById("json-box").value = JSON.stringify(currentProfile, null, 2);
  });

  document.getElementById("btn-import-json").addEventListener("click", async () => {
    try {
      const parsed = JSON.parse(document.getElementById("json-box").value);
      if (!parsed || typeof parsed !== "object") throw new Error("Invalid object");
      await saveProfileObj(parsed);
      renderForm();
      renderQuickCopy();
      setStatus("✅ Imported profile JSON locally!");
      switchTab("quick");
    } catch (e) {
      setStatus("Invalid JSON — please check formatting.", "error");
    }
  });
});
