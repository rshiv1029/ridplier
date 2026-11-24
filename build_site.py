import json
import re
from pathlib import Path
from typing import List, Dict, Any
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
      --card-hover: #273549;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-hover: #0284c7;
      --badge-md: #818cf8;
      --badge-nyc: #f43f5e;
      --prob-high: #10b981;
      --prob-mod: #f59e0b;
      --prob-lower: #f97316;
      --border: #334155;
      --success: #10b981;
    }
    * {
      box-sizing: border-box;
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
      max-width: 960px;
      margin: 0 auto 1.5rem;
      text-align: center;
    }
    .header h1 {
      font-size: 2.2rem;
      margin: 0 0 0.4rem;
      color: var(--accent);
      letter-spacing: -0.02em;
    }
    .header p {
      color: var(--text-muted);
      margin: 0;
      font-size: 1.05rem;
    }
    .stats {
      margin-top: 1rem;
      display: flex;
      justify-content: center;
      gap: 0.75rem;
      flex-wrap: wrap;
      font-size: 0.85rem;
    }
    .stat-pill {
      background: var(--card-bg);
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      border: 1px solid var(--border);
      color: var(--text-muted);
    }
    .stat-pill strong {
      color: var(--text);
    }

    /* Main Status Tabs */
    .status-tabs-container {
      max-width: 960px;
      margin: 0 auto 1rem;
      display: flex;
      background: #1e293b;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 0.35rem;
      gap: 0.35rem;
    }
    .status-tab {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      background: transparent;
      border: none;
      border-radius: 8px;
      color: var(--text-muted);
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .status-tab:hover {
      color: var(--text);
      background: rgba(255, 255, 255, 0.04);
    }
    .status-tab.active {
      background: var(--accent);
      color: #0f172a;
      box-shadow: 0 2px 8px rgba(56, 189, 248, 0.25);
    }
    .tab-badge {
      font-size: 0.8rem;
      padding: 0.15rem 0.55rem;
      border-radius: 9999px;
      background: rgba(0, 0, 0, 0.25);
      font-weight: 700;
    }
    .status-tab.active .tab-badge {
      background: rgba(15, 23, 42, 0.2);
      color: #0f172a;
    }

    /* Sub Filters */
    .filter-bar {
      max-width: 960px;
      margin: 0 auto 1.5rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      justify-content: center;
    }
    .filter-btn {
      background: var(--card-bg);
      color: var(--text-muted);
      border: 1px solid var(--border);
      padding: 0.45rem 0.9rem;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 500;
      font-size: 0.88rem;
      transition: all 0.2s;
    }
    .filter-btn:hover {
      color: var(--text);
      border-color: #475569;
    }
    .filter-btn.active {
      background: #334155;
      color: var(--accent);
      border-color: var(--accent);
    }

    /* Jobs Grid */
    .jobs-grid {
      max-width: 960px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .job-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.3rem;
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
      transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s;
    }
    .job-card:hover {
      border-color: #475569;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    }
    .job-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
    }
    .job-title {
      font-size: 1.25rem;
      font-weight: 600;
      color: var(--text);
      margin: 0.15rem 0 0;
      line-height: 1.35;
    }
    .job-hospital {
      font-size: 0.92rem;
      color: var(--accent);
      font-weight: 600;
      letter-spacing: 0.01em;
    }
    .badges {
      display: flex;
      gap: 0.45rem;
      flex-wrap: wrap;
      align-items: center;
      justify-content: flex-end;
    }
    .badge {
      font-size: 0.74rem;
      font-weight: 600;
      padding: 0.25rem 0.65rem;
      border-radius: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      white-space: nowrap;
    }
    .badge-md { background: rgba(129, 140, 248, 0.18); color: var(--badge-md); border: 1px solid rgba(129, 140, 248, 0.3); }
    .badge-nyc { background: rgba(244, 63, 94, 0.18); color: var(--badge-nyc); border: 1px solid rgba(244, 63, 94, 0.3); }
    
    .badge-high {
      background: rgba(16, 185, 129, 0.16);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .badge-moderate {
      background: rgba(245, 158, 11, 0.16);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.4);
    }
    .badge-lower {
      background: rgba(249, 115, 22, 0.16);
      color: #fb923c;
      border: 1px solid rgba(249, 115, 22, 0.4);
    }

    .job-meta {
      display: flex;
      gap: 1.25rem;
      color: var(--text-muted);
      font-size: 0.86rem;
      flex-wrap: wrap;
      align-items: center;
    }
    .job-reason {
      font-size: 0.86rem;
      padding: 0.65rem 0.95rem;
      border-radius: 6px;
      background: rgba(0, 0, 0, 0.28);
    }
    .job-reason-high {
      border-left: 3px solid var(--prob-high);
      color: #a7f3d0;
    }
    .job-reason-moderate {
      border-left: 3px solid var(--prob-mod);
      color: #fde68a;
    }
    .job-reason-lower {
      border-left: 3px solid var(--prob-lower);
      color: #fed7aa;
    }

    /* Actions Bar */
    .card-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      margin-top: 0.25rem;
      padding-top: 0.75rem;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      flex-wrap: wrap;
    }
    .action-group {
      display: flex;
      gap: 0.5rem;
      align-items: center;
      flex-wrap: wrap;
    }
    .btn-primary {
      background: var(--accent);
      color: #0f172a;
      text-decoration: none;
      padding: 0.55rem 1.15rem;
      border-radius: 7px;
      font-weight: 600;
      font-size: 0.88rem;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      border: none;
      cursor: pointer;
      transition: background 0.15s;
    }
    .btn-primary:hover {
      background: #7dd3fc;
    }
    .btn-outline {
      background: transparent;
      color: var(--text-muted);
      text-decoration: none;
      padding: 0.5rem 1rem;
      border-radius: 7px;
      font-weight: 500;
      font-size: 0.86rem;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      border: 1px solid var(--border);
      cursor: pointer;
      transition: all 0.15s;
    }
    .btn-outline:hover {
      color: var(--text);
      border-color: #64748b;
      background: rgba(255, 255, 255, 0.03);
    }
    .btn-mark-applied {
      background: rgba(16, 185, 129, 0.14);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .btn-mark-applied:hover {
      background: rgba(16, 185, 129, 0.25);
      border-color: #34d399;
      color: #6ee7b7;
    }
    .btn-dismiss {
      color: #94a3b8;
      border-color: #334155;
    }
    .btn-dismiss:hover {
      color: #f87171;
      border-color: rgba(248, 113, 113, 0.4);
      background: rgba(239, 68, 68, 0.08);
    }
    .btn-undo {
      color: #fbbf24;
      border-color: rgba(245, 158, 11, 0.4);
      background: rgba(245, 158, 11, 0.08);
    }
    .btn-undo:hover {
      background: rgba(245, 158, 11, 0.2);
    }
    .applied-tag {
      font-size: 0.85rem;
      font-weight: 600;
      color: #34d399;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      background: rgba(16, 185, 129, 0.1);
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      border: 1px solid rgba(16, 185, 129, 0.25);
    }

    /* Empty States */
    .empty-state {
      text-align: center;
      padding: 3.5rem 1.5rem;
      background: var(--card-bg);
      border: 1px dashed var(--border);
      border-radius: 12px;
      color: var(--text-muted);
    }
    .empty-icon {
      font-size: 2.5rem;
      margin-bottom: 0.5rem;
    }
    .empty-title {
      font-size: 1.15rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 0.3rem;
    }

    /* Toast Notification */
    .toast {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: #1e293b;
      color: var(--text);
      border: 1px solid var(--accent);
      padding: 0.8rem 1.4rem;
      border-radius: 8px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      font-size: 0.9rem;
      font-weight: 500;
      opacity: 0;
      pointer-events: none;
      transform: translateY(10px);
      transition: all 0.2s ease;
      z-index: 1000;
    }
    .toast.show {
      opacity: 1;
      transform: translateY(0);
    }

    @media (max-width: 640px) {
      body {
        padding: 1rem;
      }
      .job-top {
        flex-direction: column;
        align-items: flex-start;
      }
      .badges {
        justify-content: flex-start;
      }
      .card-actions {
        flex-direction: column;
        align-items: stretch;
      }
      .action-group {
        justify-content: space-between;
      }
      .btn-primary, .btn-outline {
        justify-content: center;
      }
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🩺 Ridplier</h1>
    <p>Curated PA New Grad Job Tracker & Application Hub</p>
    <div class="stats">
      <div class="stat-pill">📍 Montgomery County, MD + NYC Metro</div>
      <div class="stat-pill">⚡ Auto-Updated 4x Daily</div>
      <div class="stat-pill">Total Active: <strong id="total-count">0</strong></div>
    </div>
  </div>

  <!-- Primary Status Navigation Tabs -->
  <div class="status-tabs-container">
    <button class="status-tab active" id="tab-to_apply" onclick="switchStatusTab('to_apply')">
      <span>📥 To Apply</span>
      <span class="tab-badge" id="badge-count-to_apply">0</span>
    </button>
    <button class="status-tab" id="tab-applied" onclick="switchStatusTab('applied')">
      <span>✅ Applied</span>
      <span class="tab-badge" id="badge-count-applied">0</span>
    </button>
    <button class="status-tab" id="tab-dismissed" onclick="switchStatusTab('dismissed')">
      <span>📁 Dismissed</span>
      <span class="tab-badge" id="badge-count-dismissed">0</span>
    </button>
  </div>

  <!-- Sub-filters for current tab -->
  <div class="filter-bar">
    <button class="filter-btn active" data-filter="all" onclick="filterJobs('all')">All</button>
    <button class="filter-btn" data-filter="MD" onclick="filterJobs('MD')">📍 Maryland (MoCo)</button>
    <button class="filter-btn" data-filter="NYC" onclick="filterJobs('NYC')">🗽 NYP (NYC)</button>
    <button class="filter-btn" data-filter="high" onclick="filterJobs('high')">🟢 High Chance</button>
    <button class="filter-btn" data-filter="moderate" onclick="filterJobs('moderate')">🟡 Moderate Chance</button>
    <button class="filter-btn" data-filter="lower" onclick="filterJobs('lower')">🟠 Lower Chance (2+ Yrs)</button>
  </div>

  <div class="jobs-grid" id="jobs-container">
    <!-- Rendered via JavaScript -->
  </div>

  <div class="toast" id="toast">Status updated!</div>

  <script>
    const JOBS = __JOBS_JSON__;
    const STORAGE_KEY = 'ridplier_job_status_v1';

    let currentStatusTab = 'to_apply'; // 'to_apply' | 'applied' | 'dismissed'
    let currentFilter = 'all';         // 'all' | 'MD' | 'NYC' | 'high' | 'moderate' | 'lower'

    // Status persistence in localStorage
    function getStoredStatuses() {
      try {
        const data = localStorage.getItem(STORAGE_KEY);
        return data ? JSON.parse(data) : {};
      } catch (e) {
        return {};
      }
    }

    function saveStoredStatuses(statuses) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(statuses));
      } catch (e) {
        console.error("Failed to save to localStorage:", e);
      }
    }

    function getJobStatus(jobId) {
      const statuses = getStoredStatuses();
      if (statuses[jobId] && statuses[jobId].status) {
        return statuses[jobId];
      }
      return { status: 'to_apply', date: null };
    }

    function showToast(msg) {
      const toast = document.getElementById('toast');
      toast.textContent = msg;
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2200);
    }

    // User Action: Mark as Applied
    function markAsApplied(jobId) {
      const statuses = getStoredStatuses();
      const today = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      statuses[jobId] = { status: 'applied', date: today };
      saveStoredStatuses(statuses);
      showToast('Moved to Applied! 🎉');
      updateUI();
    }

    // User Action: Dismiss
    function dismissJob(jobId) {
      const statuses = getStoredStatuses();
      const today = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      statuses[jobId] = { status: 'dismissed', date: today };
      saveStoredStatuses(statuses);
      showToast('Job dismissed');
      updateUI();
    }

    // User Action: Move back to To Apply
    function restoreToApply(jobId) {
      const statuses = getStoredStatuses();
      delete statuses[jobId];
      saveStoredStatuses(statuses);
      showToast('Restored to "To Apply"');
      updateUI();
    }

    // Switching main status tabs
    function switchStatusTab(status) {
      currentStatusTab = status;
      document.querySelectorAll('.status-tab').forEach(t => t.classList.remove('active'));
      const activeBtn = document.getElementById(`tab-${status}`);
      if (activeBtn) activeBtn.classList.add('active');
      renderJobs();
    }

    // Sub-filtering
    function filterJobs(filterKey) {
      currentFilter = filterKey;
      document.querySelectorAll('.filter-btn').forEach(b => {
        if (b.getAttribute('data-filter') === filterKey) {
          b.classList.add('active');
        } else {
          b.classList.remove('active');
        }
      });
      renderJobs();
    }

    function getProbBadge(p) {
      if (p === 'high') return '<span class="badge badge-high">🟢 High Chance · New Grad Welcome</span>';
      if (p === 'lower') return '<span class="badge badge-lower">🟠 Lower Chance · 2+ Yrs Exp Needed</span>';
      return '<span class="badge badge-moderate">🟡 Moderate Chance · 1 Yr / Standard</span>';
    }

    function getReasonClass(p) {
      if (p === 'high') return 'job-reason job-reason-high';
      if (p === 'lower') return 'job-reason job-reason-lower';
      return 'job-reason job-reason-moderate';
    }

    function renderJobs() {
      const container = document.getElementById('jobs-container');
      const statuses = getStoredStatuses();

      // 1. Filter by current active status tab
      let list = JOBS.filter(j => {
        const s = statuses[j.id] ? statuses[j.id].status : 'to_apply';
        return s === currentStatusTab;
      });

      // 2. Filter by sub-category
      if (currentFilter === 'MD' || currentFilter === 'NYC') {
        list = list.filter(j => j.hub === currentFilter);
      } else if (currentFilter === 'high' || currentFilter === 'moderate' || currentFilter === 'lower') {
        list = list.filter(j => j.probability === currentFilter);
      }

      // Empty State handling
      if (list.length === 0) {
        let emptyIcon = "📭";
        let emptyTitle = "No jobs found";
        let emptyDesc = "Try switching filters to view other postings.";

        if (currentStatusTab === 'to_apply') {
          emptyIcon = "🎉";
          emptyTitle = "All caught up!";
          emptyDesc = "You have no unapplied jobs matching this filter. Check back after the next scan!";
        } else if (currentStatusTab === 'applied') {
          emptyIcon = "📋";
          emptyTitle = "No applications logged yet";
          emptyDesc = "When you apply to a role, press '[✅ Mark as Applied]' on the job card to track it here.";
        } else if (currentStatusTab === 'dismissed') {
          emptyIcon = "📁";
          emptyTitle = "No dismissed jobs";
          emptyDesc = "Jobs you dismiss from the 'To Apply' view will appear here.";
        }

        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">${emptyIcon}</div>
            <div class="empty-title">${emptyTitle}</div>
            <div>${emptyDesc}</div>
          </div>
        `;
        return;
      }

      container.innerHTML = list.map(j => {
        const itemStatus = statuses[j.id] || { status: 'to_apply' };
        
        let actionMarkup = '';
        if (currentStatusTab === 'to_apply') {
          actionMarkup = `
            <div class="card-actions">
              <a class="btn-primary" href="${j.url}" target="_blank" rel="noopener noreferrer">
                Apply on Hospital Site ↗
              </a>
              <div class="action-group">
                <button class="btn-outline btn-mark-applied" onclick="markAsApplied('${j.id}')">
                  ✅ Mark as Applied
                </button>
                <button class="btn-outline btn-dismiss" onclick="dismissJob('${j.id}')">
                  ✕ Dismiss
                </button>
              </div>
            </div>
          `;
        } else if (currentStatusTab === 'applied') {
          actionMarkup = `
            <div class="card-actions">
              <div class="action-group">
                <span class="applied-tag">✅ Applied on ${itemStatus.date || 'Recently'}</span>
                <a class="btn-outline" href="${j.url}" target="_blank" rel="noopener noreferrer">
                  View Listing ↗
                </a>
              </div>
              <div class="action-group">
                <button class="btn-outline btn-undo" onclick="restoreToApply('${j.id}')">
                  ↩ Move back to To Apply
                </button>
              </div>
            </div>
          `;
        } else if (currentStatusTab === 'dismissed') {
          actionMarkup = `
            <div class="card-actions">
              <div class="action-group">
                <span class="stat-pill">📁 Dismissed on ${itemStatus.date || 'Recently'}</span>
                <a class="btn-outline" href="${j.url}" target="_blank" rel="noopener noreferrer">
                  View Listing ↗
                </a>
              </div>
              <div class="action-group">
                <button class="btn-outline btn-undo" onclick="restoreToApply('${j.id}')">
                  ↩ Restore to To Apply
                </button>
              </div>
            </div>
          `;
        }

        return `
          <div class="job-card" data-id="${j.id}">
            <div class="job-top">
              <div>
                <div class="job-hospital">${j.hospital}</div>
                <h2 class="job-title">${j.title}</h2>
              </div>
              <div class="badges">
                <span class="badge ${j.hub === 'MD' ? 'badge-md' : 'badge-nyc'}">${j.hub}</span>
                ${getProbBadge(j.probability)}
              </div>
            </div>
            <div class="job-meta">
              <span>📍 ${j.location}</span>
              <span>📅 ${j.posted_date}</span>
              <span>💼 Full-Time</span>
            </div>
            <div class="${getReasonClass(j.probability)}">
              💡 <strong>Match Signal:</strong> ${j.match_reason}
            </div>
            ${actionMarkup}
          </div>
        `;
      }).join('');
    }

    function updateCounts() {
      const statuses = getStoredStatuses();
      let counts = { to_apply: 0, applied: 0, dismissed: 0 };
      
      JOBS.forEach(j => {
        const s = statuses[j.id] ? statuses[j.id].status : 'to_apply';
        if (counts[s] !== undefined) counts[s]++;
        else counts.to_apply++;
      });

      document.getElementById('badge-count-to_apply').textContent = counts.to_apply;
      document.getElementById('badge-count-applied').textContent = counts.applied;
      document.getElementById('badge-count-dismissed').textContent = counts.dismissed;
      document.getElementById('total-count').textContent = JOBS.length;
    }

    function updateUI() {
      updateCounts();
      renderJobs();
    }

    // Initial setup
    updateUI();
  </script>
</body>
</html>
"""

def generate_dashboard(jobs: List[JobPosting], output_dir: Path):
    """Generate static HTML dashboard in output_dir (e.g. docs/index.html)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    jobs_data = [j.to_dict() if isinstance(j, JobPosting) else j for j in jobs]
    html = HTML_TEMPLATE.replace("__JOBS_JSON__", json.dumps(jobs_data))
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    (output_dir / "jobs.json").write_text(json.dumps(jobs_data, indent=2), encoding="utf-8")
    print(f"[Dashboard] Generated docs/index.html with {len(jobs)} jobs.")

if __name__ == "__main__":
    # If run standalone, regenerate from existing docs/jobs.json or docs/index.html
    docs_dir = Path(__file__).parent / "docs"
    jobs_file = docs_dir / "jobs.json"
    index_file = docs_dir / "index.html"
    
    jobs = []
    if jobs_file.exists():
        jobs = json.loads(jobs_file.read_text(encoding="utf-8"))
    elif index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        match = re.search(r"const JOBS = (\[.*?\]);", content, re.DOTALL)
        if match:
            jobs = json.loads(match.group(1))
    
    if jobs:
        generate_dashboard(jobs, docs_dir)
        print("[Standalone] Successfully rebuilt docs/index.html from existing data.")
    else:
        print("[Standalone] No existing jobs found to rebuild from.")
