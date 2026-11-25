# ⚡ Ridplier Auto-Fill Chrome Extension (`feature/true-autofill`)

Zero-install-backend, 100% private Chrome Manifest V3 extension designed for Mac/Windows Chrome to accelerate filling out hospital PA applications (**Workday**, **iCIMS iframes**, **Oracle Cloud HCM**, **Radancy / NYU Langone**, **PAGNY**, and **Trinity / Hopkins**).

---

## 🔒 Privacy & Security
* **Zero PII in Git:** No personal info is stored in this repository.
* **100% Local Storage:** Your profile is saved strictly inside `chrome.storage.local` on your own browser.
* **Minimal Permissions:** Uses `activeTab` + `scripting` + `storage` (no `<all_urls>` background access) — scripts run **only when you click `⚡ Auto-Fill This Page`**.

---

## 🚀 60-Second Install in Chrome (Mac)

1. Check out this branch locally (or download the `extension/` folder):
   ```bash
   git checkout feature/true-autofill
   ```
2. Open Chrome and navigate to:
   ```text
   chrome://extensions
   ```
3. Toggle **Developer mode** ON (top-right corner).
4. Click **Load unpacked** (top-left) and select the `ridplier/extension` folder.
5. Click the puzzle-piece icon in Chrome's toolbar and **📌 Pin** **Ridplier Auto-Fill** so it's always 1 click away!

---

## 🧪 How to Use on Any Hospital Portal

1. Click the pinned **Ridplier Auto-Fill** icon → open **✏️ Edit Profile** → fill in your details once and click **💾 Save Profile**.
2. Open any hospital application form (Workday for NYP/Adventist, iCIMS for MedStar/Mount Sinai, Oracle Cloud for Inova, Radancy for NYU Langone, or PAGNY).
3. On each application step/page, click the extension → **`⚡ Auto-Fill This Page`**:
   * Fills standard text fields, selects (`State`, `Degree`), and common Yes/No screening radios (`Work Authorization`, `Visa Sponsorship`, `Previously Employed`, `18+`, `NCCPA Certified`).
   * Uses React-compatible native setters (`HTMLInputElement.prototype` + `input`/`change`/`blur` events) so Workday and Oracle don't clear values when clicking **Next**.
   * Injects across **`allFrames: true`** so **iCIMS** iframe forms fill too.
4. For any portal-specific custom dropdown or text box that wasn't auto-matched, grab it in 1 click from the **📋 Quick Copy** tab right inside the popup.
