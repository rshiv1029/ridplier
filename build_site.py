import json
import re
from pathlib import Path
from typing import List, Dict, Any
from scrapers.models import JobPosting
from scrapers.evaluator import detect_specialty

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
      --top-spec: #c084fc;
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
    .sync-status {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.8rem;
      color: #38bdf8;
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
    .filter-btn-top {
      border-color: rgba(168, 85, 247, 0.45);
      color: #c084fc;
    }
    .filter-btn-top:hover, .filter-btn-top.active {
      background: #a855f7 !important;
      color: #ffffff !important;
      border-color: #a855f7 !important;
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
    .badge-closed {
      background: rgba(148, 163, 184, 0.15);
      color: #94a3b8;
      border: 1px solid rgba(148, 163, 184, 0.3);
    }

    .badge-top-spec {
      background: rgba(168, 85, 247, 0.18);
      color: #c084fc;
      border: 1px solid rgba(168, 85, 247, 0.45);
      font-weight: 700;
    }
    .badge-spec {
      background: rgba(148, 163, 184, 0.12);
      color: #cbd5e1;
      border: 1px solid rgba(148, 163, 184, 0.28);
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
      <div class="stat-pill sync-status" id="cloud-sync-status">☁️ Connecting Cloud...</div>
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
    <button class="filter-btn active" data-filter="all" onclick="filterJobs('all')">All Jobs</button>
    <button class="filter-btn filter-btn-top" data-filter="top_5" onclick="filterJobs('top_5')">⭐ Top 5 Specialties</button>
    <button class="filter-btn" data-filter="Surgery" onclick="filterJobs('Surgery')">🔪 Surgery</button>
    <button class="filter-btn" data-filter="Emergency Medicine (ER)" onclick="filterJobs('Emergency Medicine (ER)')">🚨 Emergency (ER)</button>
    <button class="filter-btn" data-filter="ENT / Head & Neck" onclick="filterJobs('ENT / Head & Neck')">🩺 ENT</button>
    <button class="filter-btn" data-filter="Dermatology" onclick="filterJobs('Dermatology')">✨ Derm</button>
    <button class="filter-btn" data-filter="Urgent Care" onclick="filterJobs('Urgent Care')">⚡ Urgent Care</button>
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
    
    // Supabase Cloud Sync Configuration
    const SUPABASE_URL = "https://lmfjzjkkaytnrmiqadut.supabase.co";
    const SUPABASE_KEY = "sb_publishable__2yNARQiGOBhIIariC0t-Q_LSfzaIcc";

    let currentStatusTab = 'to_apply'; // 'to_apply' | 'applied' | 'dismissed'
    let currentFilter = 'all';         // 'all' | 'top_5' | 'Surgery' | 'MD' | etc.
    let archivedJobs = [];             // Past applied/dismissed jobs preserved even if removed by hospital

    // Local Storage helpers (Immediate 0ms UI reactivity)
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

    function showToast(msg) {
      const toast = document.getElementById('toast');
      toast.textContent = msg;
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2200);
    }

    // --- Supabase Cloud REST API Helpers ---
    async function supabaseUpsert(jobId, status, date) {
      const job = getAllKnownJobs().find(j => j.id === jobId) || {};
      try {
        const res = await fetch(`${SUPABASE_URL}/rest/v1/job_statuses`, {
          method: 'POST',
          headers: {
            'apikey': SUPABASE_KEY,
            'Authorization': `Bearer ${SUPABASE_KEY}`,
            'Content-Type': 'application/json',
            'Prefer': 'resolution=merge-duplicates'
          },
          body: JSON.stringify({
            job_id: jobId,
            status: status,
            date: date,
            hospital: job.hospital || '',
            title: job.title || '',
            url: job.url || ''
          })
        });
        if (res.ok) {
          document.getElementById('cloud-sync-status').innerHTML = '☁️ Cloud Synced';
        }
      } catch (e) {
        console.warn("Supabase upsert failed:", e);
      }
    }

    async function supabaseDelete(jobId) {
      try {
        const res = await fetch(`${SUPABASE_URL}/rest/v1/job_statuses?job_id=eq.${encodeURIComponent(jobId)}`, {
          method: 'DELETE',
          headers: {
            'apikey': SUPABASE_KEY,
            'Authorization': `Bearer ${SUPABASE_KEY}`
          }
        });
        if (res.ok) {
          document.getElementById('cloud-sync-status').innerHTML = '☁️ Cloud Synced';
        }
      } catch (e) {
        console.warn("Supabase delete failed:", e);
      }
    }

    async function syncFromCloud() {
      const syncEl = document.getElementById('cloud-sync-status');
      try {
        const res = await fetch(`${SUPABASE_URL}/rest/v1/job_statuses?select=*`, {
          headers: {
            'apikey': SUPABASE_KEY,
            'Authorization': `Bearer ${SUPABASE_KEY}`
          }
        });
        if (res.ok) {
          const cloudRows = await res.json();
          const localStatuses = getStoredStatuses();
          
          archivedJobs = [];
          cloudRows.forEach(row => {
            localStatuses[row.job_id] = { status: row.status, date: row.date, hospital: row.hospital, title: row.title, url: row.url };
            
            // If job is no longer on hospital site, keep it accessible for Applied / Dismissed
            if (!JOBS.some(j => j.id === row.job_id)) {
              archivedJobs.push({
                id: row.job_id,
                hospital: row.hospital || 'Hospital Portal',
                title: row.title || 'Physician Assistant',
                location: 'Archived Listing',
                posted_date: 'Expired / Closed by Hospital',
                match_reason: 'Archived Application History',
                hub: 'Other',
                probability: 'moderate',
                specialty: 'Archived',
                is_top_specialty: false,
                url: row.url || '#',
                is_closed: true
              });
            }
          });
          
          saveStoredStatuses(localStatuses);
          updateUI();
          syncEl.innerHTML = '☁️ Cloud Synced';
        } else {
          syncEl.innerHTML = '💾 Local Storage';
        }
      } catch (e) {
        syncEl.innerHTML = '💾 Local Storage';
      }
    }

    function getAllKnownJobs() {
      return [...JOBS, ...archivedJobs];
    }

    // --- User Actions ---
    function markAsApplied(jobId) {
      const statuses = getStoredStatuses();
      const today = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      statuses[jobId] = { status: 'applied', date: today };
      saveStoredStatuses(statuses);
      showToast('Moved to Applied! 🎉');
      updateUI();
      supabaseUpsert(jobId, 'applied', today);
    }

    // Dismiss job (from To Apply OR from Applied when rejected/passed)
    function dismissJob(jobId, fromApplied = false) {
      const statuses = getStoredStatuses();
      const today = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      statuses[jobId] = { status: 'dismissed', date: today };
      saveStoredStatuses(statuses);
      showToast(fromApplied ? 'Moved to Dismissed / Archived' : 'Job dismissed');
      updateUI();
      supabaseUpsert(jobId, 'dismissed', today);
    }

    // Move back to To Apply
    function restoreToApply(jobId) {
      const statuses = getStoredStatuses();
      delete statuses[jobId];
      saveStoredStatuses(statuses);
      showToast('Restored to "To Apply"');
      updateUI();
      supabaseDelete(jobId);
    }

    // --- Tab & Filter Switching ---
    function switchStatusTab(status) {
      currentStatusTab = status;
      document.querySelectorAll('.status-tab').forEach(t => t.classList.remove('active'));
      const activeBtn = document.getElementById(`tab-${status}`);
      if (activeBtn) activeBtn.classList.add('active');
      renderJobs();
    }

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

    function getSpecialtyBadge(specialty, isTop) {
      if (!specialty) return '';
      if (isTop) {
        return `<span class="badge badge-top-spec">⭐ ${specialty}</span>`;
      }
      return `<span class="badge badge-spec">${specialty}</span>`;
    }

    function getProbBadge(p, isClosed) {
      if (isClosed) return '<span class="badge badge-closed">🔒 Closed Requisition</span>';
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
      const allJobs = getAllKnownJobs();

      // 1. Filter by current active status tab
      let list = allJobs.filter(j => {
        const s = statuses[j.id] ? statuses[j.id].status : 'to_apply';
        return s === currentStatusTab;
      });

      // 2. Filter by sub-category
      if (currentFilter === 'MD' || currentFilter === 'NYC') {
        list = list.filter(j => j.hub === currentFilter);
      } else if (currentFilter === 'high' || currentFilter === 'moderate' || currentFilter === 'lower') {
        list = list.filter(j => j.probability === currentFilter);
      } else if (currentFilter === 'top_5') {
        list = list.filter(j => j.is_top_specialty);
      } else if (['Surgery', 'Emergency Medicine (ER)', 'ENT / Head & Neck', 'Dermatology', 'Urgent Care'].includes(currentFilter)) {
        list = list.filter(j => j.specialty === currentFilter);
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
          emptyTitle = "No active applications here";
          emptyDesc = "When you apply to a role, click '[✅ Mark as Applied]' on the job card to track it here.";
        } else if (currentStatusTab === 'dismissed') {
          emptyIcon = "📁";
          emptyTitle = "No dismissed jobs";
          emptyDesc = "Rejected or dismissed jobs will appear here.";
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
                <button class="btn-outline btn-dismiss" onclick="dismissJob('${j.id}', false)">
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
                <button class="btn-outline btn-dismiss" title="Move to Dismissed (e.g. if rejected or passing)" onclick="dismissJob('${j.id}', true)">
                  ✕ Move to Dismissed
                </button>
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
                <button class="btn-outline btn-mark-applied" onclick="markAsApplied('${j.id}')">
                  ✅ Move to Applied
                </button>
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
                ${getSpecialtyBadge(j.specialty, j.is_top_specialty)}
                ${j.hub !== 'Other' ? `<span class="badge ${j.hub === 'MD' ? 'badge-md' : 'badge-nyc'}">${j.hub}</span>` : ''}
                ${getProbBadge(j.probability, j.is_closed)}
              </div>
            </div>
            <div class="job-meta">
              <span>📍 ${j.location}</span>
              <span>📅 ${j.posted_date}</span>
              <span>💼 Full-Time</span>
            </div>
            <div class="${getReasonClass(j.probability)}">
              💡 <strong>Match Signal:</strong> ${j.is_top_specialty ? '⭐ <strong>Top 5 Specialty Pick</strong> · ' : ''}${j.match_reason}
            </div>
            ${actionMarkup}
          </div>
        `;
      }).join('');
    }

    function updateCounts() {
      const statuses = getStoredStatuses();
      const allJobs = getAllKnownJobs();
      let counts = { to_apply: 0, applied: 0, dismissed: 0 };
      
      allJobs.forEach(j => {
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

    // 1. Initial instant render from local storage
    updateUI();

    // 2. Background sync from Supabase cloud
    syncFromCloud();
  </script>
</body>
</html>
"""

def generate_dashboard(jobs: List[JobPosting], output_dir: Path):
    """Generate static HTML dashboard in output_dir (e.g. docs/index.html)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    jobs_data = []
    for j in jobs:
        d = j.to_dict() if isinstance(j, JobPosting) else dict(j)
        if "specialty" not in d or not d.get("specialty"):
            spec, is_top = detect_specialty(d.get("title", ""), d.get("description", ""))
            d["specialty"] = spec
            d["is_top_specialty"] = is_top
        jobs_data.append(d)
        
    html = HTML_TEMPLATE.replace("__JOBS_JSON__", json.dumps(jobs_data))
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    (output_dir / "jobs.json").write_text(json.dumps(jobs_data, indent=2), encoding="utf-8")
    print(f"[Dashboard] Generated docs/index.html with {len(jobs)} jobs and specialty tagging.")

if __name__ == "__main__":
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
        # Enforce specialty detection on existing jobs
        for j in jobs:
            spec, is_top = detect_specialty(j.get("title", ""), j.get("description", ""))
            j["specialty"] = spec
            j["is_top_specialty"] = is_top
            
        generate_dashboard(jobs, docs_dir)
        print("[Standalone] Successfully rebuilt docs/index.html with Top 5 clinical specialties.")
    else:
        print("[Standalone] No existing jobs found to rebuild from.")
