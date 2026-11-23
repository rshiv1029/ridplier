# 🩺 Ridplier: PA New Grad Job Discovery & SMS Alert Engine

Ridplier is an automated, zero-install job discovery engine designed specifically for new-grad Physician Assistants targeting **Montgomery County, MD** (Germantown / Silver Spring) and **NYC Metro**.

---

## ⚡ How It Works (Zero Installs for Her)

1. **Automated Cloud Scraping:** Runs automatically 4 times a day via GitHub Actions (8 AM, 12 PM, 5 PM, 9 PM EST).
2. **Direct-to-Source Portals:** Queries hospital career APIs directly (Holy Cross Health / Trinity Health & NewYork-Presbyterian), avoiding stale third-party job boards.
3. **New Grad Intelligence:** Filters out "Senior", "Chief", "Manager", and "Per Diem" roles, surfacing positions that welcome entry-level PAs.
4. **T-Mobile Direct SMS:** Texts her phone immediately via `[her-number]@tmomail.net` whenever a new eligible job is detected.
5. **Mobile Dashboard:** Automatically publishes to **GitHub Pages**, providing a clean Safari-ready link to browse all active jobs.

---

## 🚀 One-Time Setup (5 Minutes)

### 1. Push to GitHub
Create a private (or public) repository on GitHub and push this code:
```bash
git remote add origin https://github.com/<your-username>/ridplier.git
git branch -M main
git push -u origin main
```

### 2. Configure GitHub Secrets
In your GitHub repo, go to **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions** and add:
* `TMOBILE_NUMBER`: Her 10-digit phone number (digits only, e.g. `2401234567`).
* `GMAIL_USER`: Your Gmail address used to send the SMS email (e.g. `you@gmail.com`).
* `GMAIL_APP_PASSWORD`: A 16-character [Google App Password](https://myaccount.google.com/apppasswords) (generated in your Google Account under 2-Step Verification).

### 3. Enable Free GitHub Pages Dashboard
1. Go to **Settings** $\rightarrow$ **Pages**.
2. Under **Build and deployment** $\rightarrow$ **Source**, choose **Deploy from a branch**.
3. Select branch: `main` and folder: `/docs`.
4. Click **Save**.
5. Give her the link (e.g. `https://<your-username>.github.io/ridplier/`) to bookmark on her iPhone / Mac!

---

## 💻 Local Testing

Run the scraper locally at any time:
```bash
python run_scraper.py
```
*(If credentials are not set in your environment, it safely prints an exact SMS preview to your terminal without failing).*
