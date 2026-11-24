# 🩺 Ridplier: The PA New Grad Job Hunter That Doesn't Ghost You

> *"Entry level position: Requires Master's degree, active state license, DEA registration, 3–5 years of prior inpatient clinical experience, and the blessing of an ancient deity."*
>
> — Literally every hospital job board ever.

Sound familiar? Welcome to the post-PA school job hunt. 

You just survived 2+ years of didactic hell, 2,000 clinical rotation hours, and the PANCE, only to find yourself manually refreshing 14 different hospital Workday portals every morning while competing with 300 other applicants.

**Ridplier** automates the entire discovery and evaluation grind so you can stop playing recruiter detective and actually land interviews.

---

## ⚡ What It Does

* **Direct-to-Source Scraping:** Bypasses stale reposts on Indeed, LinkedIn, and sketchy travel staffing recruiters. It pulls live requisitions directly from **9 primary hospital career portals**:
  * **NYC Metro:** NewYork-Presbyterian, Mount Sinai, NYU Langone, and NYC Health + Hospitals (PAGNY).
  * **Maryland & DC Border:** Adventist HealthCare (Rockville/Silver Spring), Suburban & Sibley Memorial (Johns Hopkins), Holy Cross Health (Germantown/Silver Spring), and MedStar Health.
  * **Northern Virginia:** Inova Health System (Fairfax, Alexandria, Loudoun).
* **Strict B.S. Filter:** Automatically filters out "Chief", "Senior", "Lead", "Director", "Per Diem", "PRN", "Part-Time", and explicit "Experience Required" postings.
* **New Grad Intelligence:** Scans job descriptions for genuine entry-level signals (*"New grads welcome"*, *"Will consider new graduates"*, *"PA I"*).
* **Clean 3-Dropdown Mobile Dashboard:** Deployed 100% free on GitHub Pages. Filter by:
  1. **🏥 Hospital Network:** Switch between any of the 9 hospital systems.
  2. **📍 Location & Borough:** Strict `🗽 NYC In-City (5 Boroughs Only)` filtering to immediately separate city jobs from suburban Long Island/Westchester postings.
  3. **🩺 Clinical Specialty:** Instant filter for her **Top 5 Specialties** (ENT, Derm, ER, Surgery, Urgent Care) + inpatient specialties.
* **Pipeline Tracking & Cloud Sync:** Separate tabs for **`To Apply`**, **`Applied`**, and **`Dismissed`** with instant real-time synchronization to Supabase across iPhone and Mac Safari.
* **Zero-Install Alerts:** Optional SMS or email alerts whenever a fresh listing drops, so she can apply within hours of posting.

---

## 🏥 Live Hospital Coverage (130 Active Roles)

| Health System | Region | Facilities Monitored | ATS Platform |
| :--- | :--- | :--- | :--- |
| **NewYork-Presbyterian (NYP)** | NYC | Manhattan, Brooklyn, Queens, Westchester | Workday CXS REST |
| **Mount Sinai Health System** | NYC | Manhattan, Queens, Brooklyn | Jibe / iCIMS REST |
| **NYU Langone Health** | NYC | Tisch, Kimmel, Orthopedic, Brooklyn, Bellevue | Radancy / m-cloud API |
| **NYC Health + Hospitals / PAGNY** | NYC | Jacobi, Lincoln, Kings County, Harlem, Metropolitan, South Brooklyn Health | Custom PAGNY Portal |
| **Johns Hopkins Medicine** | MD / DC | Suburban Hospital (Bethesda) & Sibley Memorial (DC) | Hopkins Schema.org Parser |
| **MedStar Health** | MD / DC | MedStar Montgomery (Olney), Gaithersburg, DC | Jibe REST API |
| **Adventist HealthCare** | MD | Shady Grove (Rockville) & White Oak (Silver Spring) | Workday CXS REST |
| **Holy Cross Health** | MD | Germantown & Silver Spring | Trinity Phenom API |
| **Inova Health System** | VA | Fairfax, Alexandria, Loudoun, Reston | Oracle Cloud HCM REST |

---

## 📱 Mobile Dashboard (Zero Installs)

Open the link in Safari on an iPhone or Mac:
👉 **[https://rshiv1029.github.io/ridplier/](https://rshiv1029.github.io/ridplier/)**

* **Status Tabs:** Move jobs seamlessly between **`To Apply`**, **`Applied`**, and **`Dismissed`**.
* **Direct Application Deep-Links:** Clicking **`Apply on Hospital Site ↗`** opens the exact hospital requisition in a new tab without altering state.
* **Closed Job Protection:** Applied positions remain saved in the "Applied" tab even if the hospital later closes or removes the requisition.
* **Supabase Cloud Sync:** Zero-latency optimistic UI updates with cloud backup to Supabase PostgreSQL.

---

## 🚀 5-Minute Setup & Scheduled Automation

Ridplier runs entirely in the cloud via GitHub Actions every 6 hours (`cron: '0 */6 * * *'`).

### 1. Repository Setup
```powershell
git remote add origin https://github.com/rshiv1029/ridplier.git
git branch -M main
git push -u origin main
```

### 2. Optional: Add Notification Secrets
To enable automated text/email notifications when new jobs drop, add the following in GitHub under **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions**:
* `ALERT_EMAIL`: Email address to receive alerts (e.g. `your-email@gmail.com`).
* `TMOBILE_NUMBER`: 10-digit mobile number for free SMS via T-Mobile's gateway (e.g. `2401234567`).
* `GMAIL_USER`: The sender Gmail address (e.g. `you@gmail.com`).
* `GMAIL_APP_PASSWORD`: A 16-character [Google App Password](https://myaccount.google.com/apppasswords).

### 3. GitHub Pages
1. Go to repository **Settings** $\rightarrow$ **Pages**.
2. Under **Build and deployment** $\rightarrow$ **Source**, choose **Deploy from a branch**.
3. Select branch: `main` and folder: `/docs`.
4. Click **Save**.

---

## 💻 Local Manual Run

To execute the scrapers locally and rebuild the dashboard:
```powershell
python run_scraper.py
```
To open the static dashboard locally:
```powershell
start docs/index.html
```

---

*Made with ❤️ to help new PAs secure the bag.*
