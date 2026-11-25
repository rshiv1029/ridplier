/**
 * Ridplier Auto-Fill Content Function (injected per-frame via chrome.scripting.executeScript)
 * Designed for Workday, iCIMS (inside iframes), Oracle Cloud HCM, Radancy/m-cloud, and PAGNY.
 * Runs only on explicit user click; zero network calls, zero telemetry.
 */
function ridplierAutoFillFrame(profile, options = {}) {
  const overwrite = Boolean(options.overwrite);
  const STATE_NAMES = {
    NY: "New York",
    MD: "Maryland",
    VA: "Virginia",
    DC: "District of Columbia",
    NJ: "New Jersey",
    PA: "Pennsylvania",
    CT: "Connecticut",
  };

  function norm(s) {
    return String(s || "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function isVisible(el) {
    if (!el || el.disabled || el.readOnly) return false;
    const type = (el.getAttribute("type") || "").toLowerCase();
    if (["hidden", "file", "password", "submit", "button", "reset", "image"].includes(type)) {
      return false;
    }
    const style = window.getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden" || parseFloat(style.opacity) === 0) {
      return false;
    }
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function setNativeValue(el, value) {
    const strVal = String(value);
    const proto =
      el.tagName === "TEXTAREA"
        ? HTMLTextAreaElement.prototype
        : el.tagName === "SELECT"
          ? HTMLSelectElement.prototype
          : HTMLInputElement.prototype;
    const descriptor = Object.getOwnPropertyDescriptor(proto, "value");
    if (descriptor && descriptor.set) {
      descriptor.set.call(el, strVal);
    } else {
      el.value = strVal;
    }
    el.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
    el.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
    el.dispatchEvent(new Event("blur", { bubbles: true, composed: true }));
  }

  function flashHighlight(el) {
    try {
      const prev = el.style.boxShadow;
      el.style.boxShadow = "0 0 0 2px #38bdf8";
      setTimeout(() => {
        el.style.boxShadow = prev;
      }, 1600);
    } catch (_) {}
  }

  function getAccessibleLabel(el) {
    const parts = [];
    if (el.id) {
      try {
        const lbl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
        if (lbl) parts.push(lbl.innerText || lbl.textContent);
      } catch (_) {}
    }
    const parentLabel = el.closest("label");
    if (parentLabel) parts.push(parentLabel.innerText || parentLabel.textContent);

    const ariaLabel = el.getAttribute("aria-label");
    if (ariaLabel) parts.push(ariaLabel);

    const labelledBy = el.getAttribute("aria-labelledby");
    if (labelledBy) {
      labelledBy.split(/\s+/).forEach((id) => {
        const node = document.getElementById(id);
        if (node) parts.push(node.innerText || node.textContent);
      });
    }

    // Workday / Oracle form wrapper lookup
    const wrapper = el.closest(
      '[data-automation-id], .form-group, .field, .oj-form-control, tr, li, div[role="group"]'
    );
    if (wrapper) {
      const lblNode = wrapper.querySelector("label, .label, legend, th, dt, span[id*='label']");
      if (lblNode && !lblNode.contains(el)) {
        parts.push(lblNode.innerText || lblNode.textContent);
      }
    }

    parts.push(
      el.getAttribute("placeholder") || "",
      el.getAttribute("data-automation-id") || "",
      el.getAttribute("name") || "",
      el.id || ""
    );
    return norm(parts.join(" | "));
  }

  function matchSelectOption(selectEl, targetValue) {
    const want = norm(targetValue);
    if (!want) return null;
    const upper = String(targetValue).trim().toUpperCase();
    const expanded = norm(STATE_NAMES[upper] || "");
    const opts = Array.from(selectEl.options || []).filter((o) => !o.disabled && o.value !== "");

    // 1. Exact value or text match
    for (const o of opts) {
      if (norm(o.value) === want || norm(o.text) === want) return o;
      if (expanded && (norm(o.value) === expanded || norm(o.text) === expanded)) return o;
    }
    // 2. Partial contains match (e.g. "Master" -> "Master's Degree")
    for (const o of opts) {
      const ot = norm(o.text);
      const ov = norm(o.value);
      if (want.length >= 3 && (ot.includes(want) || ov.includes(want))) return o;
      if (expanded && (ot.includes(expanded) || ov.includes(expanded))) return o;
    }
    return null;
  }

  // Ordered, specific field matchers (avoid overly generic substrings that hit search bars/captchas)
  const FULL_NAME = [profile.first_name, profile.last_name].filter(Boolean).join(" ").trim();
  const FIELD_RULES = [
    {
      label: "First Name",
      value: profile.first_name,
      automationIds: ["legalNameSection_firstName", "firstName"],
      match: (l) =>
        /\b(first\s*name|given\s*name|fname|legalname.*firstname)\b/.test(l) &&
        !/\b(middle|last|preferred|emergency|reference)\b/.test(l),
    },
    {
      label: "Last Name",
      value: profile.last_name,
      automationIds: ["legalNameSection_lastName", "lastName"],
      match: (l) =>
        /\b(last\s*name|family\s*name|surname|lname|legalname.*lastname)\b/.test(l) &&
        !/\b(first|middle|emergency|reference)\b/.test(l),
    },
    {
      label: "Full Name",
      value: FULL_NAME,
      automationIds: ["fullName"],
      match: (l) =>
        /\b(full\s*name|applicant\s*name|your\s*name)\b/.test(l) &&
        !/\b(first|last|school|hospital|reference|emergency|supervisor)\b/.test(l),
    },
    {
      label: "Email",
      value: profile.email,
      automationIds: ["email"],
      match: (l, el) =>
        el.type === "email" ||
        (/\b(e-?mail(?:\s*address)?)\b/.test(l) && !/\b(confirm|re-?enter|verify|reference|supervisor)\b/.test(l)),
    },
    {
      label: "Phone",
      value: profile.phone,
      automationIds: ["phone-number", "phoneNumber"],
      match: (l, el) =>
        el.type === "tel" ||
        (/\b(phone(?:\s*number)?|mobile|cell|telephone)\b/.test(l) &&
          !/\b(extension|ext|country\s*code|fax|emergency|reference)\b/.test(l)),
    },
    {
      label: "Address Line 1",
      value: profile.address1,
      automationIds: ["addressSection_addressLine1", "addressLine1"],
      match: (l) =>
        /\b(address\s*line\s*1|street\s*address|mailing\s*address|home\s*address)\b/.test(l) &&
        !/\b(line\s*2|email|city|zip|postal)\b/.test(l),
    },
    {
      label: "City",
      value: profile.city,
      automationIds: ["addressSection_city", "city"],
      match: (l) => /\b(city|town)\b/.test(l) && !/\b(school|facility|birth)\b/.test(l),
    },
    {
      label: "State",
      value: profile.state,
      automationIds: ["addressSection_countryRegion", "state"],
      match: (l) =>
        /\b(state|province|region)\b/.test(l) &&
        !/\b(country|united\s*states|license\s*state|statement)\b/.test(l),
    },
    {
      label: "ZIP Code",
      value: profile.zip,
      automationIds: ["addressSection_postalCode", "postalCode"],
      match: (l) => /\b(zip(?:\s*code)?|postal\s*code)\b/.test(l),
    },
    {
      label: "LinkedIn",
      value: profile.linkedin,
      automationIds: ["linkedin"],
      match: (l) => /\blinkedin\b/.test(l),
    },
    {
      label: "PA School",
      value: profile.pa_school,
      automationIds: ["schoolName", "school"],
      match: (l) => /\b(school(?:\s*name)?|university|college|institution|alma\s*mater)\b/.test(l),
    },
    {
      label: "Degree",
      value: profile.degree,
      automationIds: ["degree"],
      match: (l) => /\b(degree|education\s*level|highest\s*level\s*of\s*education)\b/.test(l),
    },
    {
      label: "GPA",
      value: profile.gpa,
      automationIds: ["gpa"],
      match: (l) => /\b(gpa|grade\s*point)\b/.test(l),
    },
    {
      label: "License / NCCPA Status",
      value: profile.license_summary,
      automationIds: [],
      match: (l) =>
        /\b(license\s*(?:number|status|#)|nccpa|certification\s*(?:number|status|#))\b/.test(l),
    },
    {
      label: "How Did You Hear",
      value: profile.referral_source,
      automationIds: ["sourceDropdown"],
      match: (l) => /\b(how\s+did\s+you\s+hear|referral\s*source|source)\b/.test(l) && !/\bopen\s*source\b/.test(l),
    },
    {
      label: "Salary Expectation",
      value: profile.salary_expectation,
      automationIds: [],
      match: (l) => /\b(desired\s*(?:salary|pay|compensation)|salary\s*expectation)\b/.test(l),
    },
    {
      label: "Cover Note / Summary",
      value: profile.cover_note,
      automationIds: [],
      match: (l, el) =>
        el.tagName === "TEXTAREA" &&
        /\b(cover\s*letter|summary|additional\s*information|why\s*(?:do\s*you\s*want|are\s*you\s*interested)|message\s*to\s*hiring)\b/.test(l),
    },
  ];

  const filledFields = [];
  const inputs = Array.from(document.querySelectorAll("input, select, textarea")).filter(isVisible);

  for (const el of inputs) {
    if (el.type === "radio" || el.type === "checkbox") continue;
    const currentVal = (el.value || "").trim();
    if (!overwrite && el.tagName !== "SELECT" && currentVal.length > 0) {
      continue;
    }

    const labelText = getAccessibleLabel(el);
    // Skip search boxes, OTP codes, captcha inputs
    if (/\b(search|keyword|captcha|verification\s*code|otp)\b/.test(labelText)) {
      continue;
    }

    const autoId = el.getAttribute("data-automation-id") || "";

    for (const rule of FIELD_RULES) {
      if (!rule.value) continue;
      const byAutoId = rule.automationIds.some((id) => autoId === id || autoId.endsWith("_" + id));
      const matched = byAutoId || rule.match(labelText, el);
      if (!matched) continue;

      if (el.tagName === "SELECT") {
        const opt = matchSelectOption(el, rule.value);
        if (opt && (overwrite || !el.value || el.selectedIndex <= 0)) {
          setNativeValue(el, opt.value);
          flashHighlight(el);
          filledFields.push(rule.label);
        }
      } else {
        setNativeValue(el, rule.value);
        flashHighlight(el);
        filledFields.push(rule.label);
      }
      break;
    }
  }

  // Handle common Yes/No radio groups in Workday / iCIMS / PAGNY screening questions
  const RADIO_RULES = [
    {
      label: "US Work Authorization",
      answer: profile.work_authorized || "Yes",
      match: (q) => /\b(legally\s*authorized\s*to\s*work|authorized\s*to\s*work\s*in\s*the\s*(?:u\.?s\.?|united\s*states))\b/.test(q),
    },
    {
      label: "Visa Sponsorship",
      answer: profile.require_sponsorship || "No",
      match: (q) => /\b(require\s*(?:visa\s*)?sponsorship|now\s*or\s*in\s*the\s*future\s*require\s*sponsorship)\b/.test(q),
    },
    {
      label: "Previously Employed",
      answer: profile.worked_before || "No",
      match: (q) => /\b(previously\s*(?:worked|employed)|ever\s*been\s*employed\s*(?:by|at))\b/.test(q),
    },
    {
      label: "Age 18+",
      answer: "Yes",
      match: (q) => /\b(at\s*least\s*18\s*years|18\s*years\s*of\s*age\s*or\s*older)\b/.test(q),
    },
    {
      label: "NCCPA Certified",
      answer: profile.nccpa_certified || "Yes",
      match: (q) => /\b(nccpa\s*certif|board\s*certif(?:ied)?\s*(?:physician\s*assistant|pa))\b/.test(q),
    },
  ];

  const radios = Array.from(document.querySelectorAll('input[type="radio"]')).filter((r) => !r.disabled);
  const grouped = new Map();
  for (const r of radios) {
    const key = r.name || r.closest("fieldset, [role='radiogroup']")?.id || "";
    if (!key) continue;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key).push(r);
  }

  for (const [, group] of grouped) {
    if (!overwrite && group.some((r) => r.checked)) continue;
    const container = group[0].closest("fieldset, [role='radiogroup'], .form-group, tr, div[data-automation-id]");
    const qText = norm(container ? container.innerText || container.textContent : "");
    if (!qText) continue;

    for (const rr of RADIO_RULES) {
      if (!rr.match(qText)) continue;
      const targetAns = norm(rr.answer);
      const targetRadio = group.find((r) => {
        const rLbl = getAccessibleLabel(r);
        return rLbl.includes(targetAns) || norm(r.value) === targetAns;
      });
      if (targetRadio) {
        targetRadio.click();
        flashHighlight(targetRadio);
        filledFields.push(rr.label);
      }
      break;
    }
  }

  return {
    filledCount: filledFields.length,
    filledFields,
    url: location.hostname,
  };
}
