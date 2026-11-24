# 🩺 Ridplier: The PA New Grad Job Hunter That Doesn't Ghost You

> *"Entry level position: Requires Master's degree, active state license, DEA registration, 3–5 years of prior inpatient clinical experience, and the blessing of an ancient deity."*
>
> — Literally every hospital job board ever.

Sound familiar? Welcome to the post-PA school job hunt. 

You just survived 2+ years of didactic hell, 2,000 clinical rotation hours, and the PANCE, only to find yourself manually refreshing 14 different hospital Workday portals every morning while competing with 300 other applicants.

**Ridplier** automates the entire discovery grind so you can stop playing recruiter detective and actually land interviews.

---

## ⚡ What It Does

* **Direct-to-Source Scraping:** Bypasses stale reposts on Indeed, LinkedIn, and sketchy travel staffing recruiters. It pulls live requisitions directly from primary hospital career portals (Holy Cross Health, NYP, and expanding across MD & NYC).
* **B.S. Filter:** Automatically filters out "Chief", "Senior", "Lead", "Director", and "Per Diem" listings.
* **New Grad Intelligence:** Scans job descriptions for genuine entry-level signals (*"New grads welcome"*, *"Will consider new graduates"*, *"PA I"*).
* **Zero-Install SMS Alerts:** When a fresh listing drops, your phone buzzes with a clean, concise text containing the hospital, specialty, and direct application link. You can be applicant #4 instead of applicant #150.
* **No-Fuss Mobile Dashboard:** Deployed 100% free on GitHub Pages. Bookmark it in Safari on your iPhone or Mac to browse all active openings with direct 1-click apply links.

---

## 📱 What You See on Your Phone

The second a matching job goes live, you get a clean text:

```text
🏥 Holy Cross Health (Trinity)
💼 Physician Assistant - Emergency Medicine
📍 Germantown, MD
⭐ New Grad: Yes
🔗 https://jobs.trinity-health.org/job/...
```

---

## 🚀 5-Minute Setup (100% Free Forever)

Ridplier runs entirely in the cloud via GitHub Actions. You don't need a server, you don't need to leave your computer on, and you don't need to install anything on your phone.

### 1. Push Code to GitHub
```powershell
git remote add origin https://github.com/<your-username>/ridplier.git
git branch -M main
git push -u origin main
```

### 2. Add Your Alert Secrets
In your GitHub repository, go to **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions** and add:
* `TMOBILE_NUMBER`: Your 10-digit mobile number (e.g. `2401234567`).
* `GMAIL_USER`: The Gmail address used to dispatch the SMS notifications (e.g. `you@gmail.com`).
* `GMAIL_APP_PASSWORD`: A 16-character [Google App Password](https://myaccount.google.com/apppasswords) (generated in your Google Account under *Security* $\rightarrow$ *2-Step Verification* $\rightarrow$ *App Passwords*).

### 3. Turn on the Web Dashboard
1. In your GitHub repo, go to **Settings** $\rightarrow$ **Pages**.
2. Under **Build and deployment** $\rightarrow$ **Source**, choose **Deploy from a branch**.
3. Select branch: `main` and folder: `/docs`.
4. Click **Save**.
5. Bookmark your URL (e.g., `https://<your-username>.github.io/ridplier/`) on your phone home screen!

---

## 💻 Local Quick Test

Want to run a manual scan right now from your terminal?
```powershell
python run_scraper.py
```
To view your local dashboard:
```powershell
start docs/index.html
```

---

*Made with ❤️ to help new PAs secure the bag.*
