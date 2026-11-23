import json
from pathlib import Path
from typing import List
from scrapers.models import JobPosting

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ridplier | PA New Grad Job Board</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-hover: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --badge-new: #10b981;
      --badge-md: #818cf8;
      --badge-nyc: #f43f5e;
      --border: #334155;
    }
    body {
      margin: 0;
      padding: 1.5rem;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }
    .header {
      max-width: 900px;
      margin: 0 auto 2rem;
      text-align: center;
    }
    .header h1 {
      font-size: 2rem;
      margin: 0 0 0.5rem;
      color: var(--accent);
    }
    .header p {
      color: var(--text-muted);
      margin: 0;
    }
    .stats {
      margin-top: 1rem;
      display: flex;
      justify-content: center;
      gap: 1rem;
      font-size: 0.9rem;
    }
    .stat-pill {
      background: var(--card-bg);
      padding: 0.35rem 0.8rem;
      border-radius: 9999px;
      border: 1px solid var(--border);
    }
    .filter-bar {
      max-width: 900px;
      margin: 0 auto 1.5rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      justify-content: center;
    }
    .filter-btn {
      background: var(--card-bg);
      color: var(--text);
      border: 1px solid var(--border);
      padding: 0.5rem 1rem;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 500;
      transition: all 0.2s;
    }
    .filter-btn:hover, .filter-btn.active {
      background: var(--accent);
      color: var(--bg);
      border-color: var(--accent);
    }
    .jobs-grid {
      max-width: 900px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .job-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      transition: transform 0.15s, border-color 0.15s;
    }
    .job-card:hover {
      border-color: var(--accent);
    }
    .job-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
    }
    .job-title {
      font-size: 1.2rem;
      font-weight: 600;
      color: var(--text);
      margin: 0;
    }
    .job-hospital {
      font-size: 0.95rem;
      color: var(--accent);
      font-weight: 500;
    }
    .badges {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .badge {
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.2rem 0.6rem;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .badge-md { background: rgba(129, 140, 248, 0.2); color: var(--badge-md); }
    .badge-nyc { background: rgba(244, 63, 94, 0.2); color: var(--badge-nyc); }
    .badge-newgrad { background: rgba(16, 185, 129, 0.2); color: var(--badge-new); }
    .job-meta {
      display: flex;
      gap: 1.5rem;
      color: var(--text-muted);
      font-size: 0.85rem;
      flex-wrap: wrap;
    }
    .job-reason {
      font-size: 0.85rem;
      color: #cbd5e1;
      background: rgba(0,0,0,0.2);
      padding: 0.5rem 0.75rem;
      border-radius: 6px;
      border-left: 3px solid var(--badge-new);
    }
    .apply-btn {
      align-self: flex-start;
      background: var(--accent);
      color: var(--bg);
      text-decoration: none;
      padding: 0.5rem 1.2rem;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.9rem;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      transition: opacity 0.15s;
    }
    .apply-btn:hover {
      opacity: 0.9;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🩺 Ridplier</h1>
    <p>Curated PA New Grad Job Tracker & Discovery Engine</p>
    <div class="stats">
      <div class="stat-pill">📍 Montgomery County, MD + NYC Metro</div>
      <div class="stat-pill">⚡ Auto-Updated Daily</div>
      <div class="stat-pill">Total Active: <strong id="total-count">0</strong></div>
    </div>
  </div>

  <div class="filter-bar">
    <button class="filter-btn active" onclick="filterJobs('all')">All Jobs</button>
    <button class="filter-btn" onclick="filterJobs('MD')">Holy Cross / MD</button>
    <button class="filter-btn" onclick="filterJobs('NYC')">NYP / NYC</button>
    <button class="filter-btn" onclick="filterJobs('newgrad')">⭐ Verified New Grad</button>
  </div>

  <div class="jobs-grid" id="jobs-container">
    <!-- Rendered via JS -->
  </div>

  <script>
    const JOBS = __JOBS_JSON__;
    document.getElementById('total-count').textContent = JOBS.length;

    function renderJobs(list) {
      const c = document.getElementById('jobs-container');
      c.innerHTML = list.map(j => `
        <div class="job-card" data-hub="${j.hub}" data-newgrad="${j.is_new_grad_friendly}">
          <div class="job-top">
            <div>
              <div class="job-hospital">${j.hospital}</div>
              <h2 class="job-title">${j.title}</h2>
            </div>
            <div class="badges">
              <span class="badge ${j.hub === 'MD' ? 'badge-md' : 'badge-nyc'}">${j.hub}</span>
              ${j.is_new_grad_friendly ? '<span class="badge badge-newgrad">New Grad Friendly</span>' : ''}
            </div>
          </div>
          <div class="job-meta">
            <span>📍 ${j.location}</span>
            <span>📅 ${j.posted_date}</span>
          </div>
          <div class="job-reason">💡 ${j.match_reason}</div>
          <a class="apply-btn" href="${j.url}" target="_blank" rel="noopener noreferrer">Apply on Hospital Site ↗</a>
        </div>
      `).join('');
    }

    function filterJobs(type) {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      event.target.classList.add('active');

      if (type === 'all') renderJobs(JOBS);
      else if (type === 'MD' || type === 'NYC') renderJobs(JOBS.filter(j => j.hub === type));
      else if (type === 'newgrad') renderJobs(JOBS.filter(j => j.is_new_grad_friendly));
    }

    renderJobs(JOBS);
  </script>
</body>
</html>
"""

def generate_dashboard(jobs: List[JobPosting], output_dir: Path):
    """Generate static HTML dashboard in output_dir (e.g. docs/index.html)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    jobs_data = [j.to_dict() for j in jobs]
    html = HTML_TEMPLATE.replace("__JOBS_JSON__", json.dumps(jobs_data))
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"[Dashboard] Generated docs/index.html with {len(jobs)} jobs.")
