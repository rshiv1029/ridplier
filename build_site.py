import json
import re
from pathlib import Path
from typing import List, Dict, Any
from scrapers.models import JobPosting
from scrapers.evaluator import detect_specialty, classify_nyc_location

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
      --badge-va: #60a5fa;
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

    /* Dropdown Filters Toolbar */
    .dropdown-filter-bar {
      max-width: 960px;
      margin: 0 auto 1.5rem;
      display: grid;
      grid-template-columns: repeat(3, 1fr) auto;
      gap: 0.75rem;
      background: #1e293b;
      padding: 0.85rem 1rem;
      border: 1px solid var(--border);
      border-radius: 12px;
      align-items: flex-end;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .filter-group {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      min-width: 0;
    }
    .filter-label {
      font-size: 0.75rem;
      font-weight: 700;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      display: flex;
      align-items: center;
      gap: 0.3rem;
    }
    .filter-select {
      background: #0f172a;
      color: var(--text);
      border: 1px solid #334155;
      padding: 0.6rem 0.8rem;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 500;
      outline: none;
      cursor: pointer;
      width: 100%;
      text-overflow: ellipsis;
      white-space: nowrap;
      transition: all 0.15s ease;
      font-family: inherit;
    }
    .filter-select:hover {
      border-color: #64748b;
    }
    .filter-select:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
    }
    .filter-select optgroup {
      background: #0f172a;
      color: #94a3b8;
      font-weight: 700;
      font-size: 0.82rem;
    }
    .filter-select option {
      background: #1e293b;
      color: var(--text);
      font-weight: 400;
      padding: 0.4rem;
    }
    .filter-group-actions {
      display: flex;
      align-items: flex-end;
    }
    .btn-reset-filters {
      background: transparent;
      color: #94a3b8;
      border: 1px dashed #475569;
      padding: 0.58rem 0.9rem;
      border-radius: 8px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
      display: none;
    }
    .btn-reset-filters.visible {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
    }
    .btn-reset-filters:hover {
      color: #f87171;
      border-color: #ef4444;
      background: rgba(239, 68, 68, 0.1);
    }

    @media (max-width: 820px) {
      .dropdown-filter-bar {
        grid-template-columns: 1fr;
        gap: 0.75rem;
        padding: 0.85rem;
      }
      .filter-group-actions {
        align-items: stretch;
      }
      .btn-reset-filters {
        justify-content: center;
      }
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
    .badge-va { background: rgba(59, 130, 246, 0.18); color: var(--badge-va); border: 1px solid rgba(59, 130, 246, 0.3); }
    
    .badge-outside-nyc {
      background: rgba(239, 68, 68, 0.16);
      color: #f87171;
      border: 1px solid rgba(239, 68, 68, 0.4);
      font-weight: 700;
    }

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

    .location-warning {
      background: rgba(239, 68, 68, 0.12);
      color: #fca5a5;
      border-left: 3px solid #ef4444;
      padding: 0.5rem 0.85rem;
      border-radius: 6px;
      font-size: 0.84rem;
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
      <div class="stat-pill">📍 Montgomery County, MD + DC + Northern VA + NYC Metro</div>
      <div class="stat-pill">⚡ Auto-Updated Every 6 Hours</div>
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

  <!-- 3 Clean Dropdown Filters: Network, Location, Specialty -->
  <div class="dropdown-filter-bar">
    <div class="filter-group">
      <label for="filter-network" class="filter-label">🏥 Hospital Network</label>
      <select id="filter-network" class="filter-select" onchange="onDropdownFilterChange()">
        <option value="all">All Networks (All Hospitals)</option>
        <option value="NYP">NewYork-Presbyterian (NYC)</option>
        <option value="Mount Sinai">Mount Sinai Health System (NYC)</option>
        <option value="NYU Langone">NYU Langone Health (NYC)</option>
        <option value="NYC Health + Hospitals">NYC Health + Hospitals / PAGNY (NYC)</option>
        <option value="Johns Hopkins">Johns Hopkins / Suburban & Sibley (MD/DC)</option>
        <option value="MedStar">MedStar Health (MD & DC)</option>
        <option value="Adventist">Adventist HealthCare (MD)</option>
        <option value="Holy Cross">Holy Cross Health (MD)</option>
        <option value="Inova">Inova Health System (VA)</option>
      </select>
    </div>

    <div class="filter-group">
      <label for="filter-location" class="filter-label">📍 Location & Borough</label>
      <select id="filter-location" class="filter-select" onchange="onDropdownFilterChange()">
        <option value="all">All Locations</option>
        <optgroup label="🗽 New York City (Strict In-City)">
          <option value="NYC_proper">🗽 All NYC (5 Boroughs Only)</option>
          <option value="Manhattan">Manhattan</option>
          <option value="Brooklyn">Brooklyn</option>
          <option value="Queens">Queens</option>
          <option value="Bronx">Bronx</option>
        </optgroup>
        <optgroup label="⚠️ Outside NYC (Suburbs)">
          <option value="NYC_outside">⚠️ Outside NYC (Long Island / Westchester)</option>
        </optgroup>
        <optgroup label="📍 Maryland, DC & Virginia">
          <option value="MD">📍 Montgomery County & DC Border (MD)</option>
          <option value="VA">🏛️ Northern Virginia (Inova)</option>
        </optgroup>
      </select>
    </div>

    <div class="filter-group">
      <label for="filter-specialty" class="filter-label">🩺 Clinical Specialty</label>
      <select id="filter-specialty" class="filter-select" onchange="onDropdownFilterChange()">
        <option value="all">All Specialties</option>
        <optgroup label="⭐ Her Top 5 Specialties">
          <option value="top_5">⭐ Any Top 5 Specialty Pick</option>
          <option value="ENT / Head & Neck">🩺 1. ENT / Head & Neck</option>
          <option value="Dermatology">✨ 2. Dermatology</option>
          <option value="Emergency Medicine (ER)">🚨 3. Emergency Medicine (ER)</option>
          <option value="Surgery">🔪 4. Surgery (General, Trauma, Ortho, OR)</option>
          <option value="Urgent Care">⚡ 5. Urgent Care</option>
        </optgroup>
        <optgroup label="🏥 Other Specialties">
          <option value="Critical Care / ICU">🫁 Critical Care / ICU</option>
          <option value="Cardiology">❤️ Cardiology & Cath Lab</option>
          <option value="Internal Medicine">🏥 Internal Medicine / Hospitalist</option>
          <option value="Primary Care">🩺 Primary Care & Outpatient</option>
          <option value="Obstetrics & Gynecology">👶 OB / GYN</option>
          <option value="General / Inpatient">📋 General / Inpatient</option>
        </optgroup>
      </select>
    </div>

    <div class="filter-group filter-group-actions">
      <button class="btn-reset-filters" id="btn-reset-filters" onclick="resetDropdownFilters()">
        ↺ Reset Filters
      </button>
    </div>
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
    let selectedNetwork = 'all';
    let selectedLocation = 'all';
    let selectedSpecialty = 'all';
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

    function dismissJob(jobId, fromApplied = false) {
      const statuses = getStoredStatuses();
      const today = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      statuses[jobId] = { status: 'dismissed', date: today };
      saveStoredStatuses(statuses);
      showToast(fromApplied ? 'Moved to Dismissed / Archived' : 'Job dismissed');
      updateUI();
      supabaseUpsert(jobId, 'dismissed', today);
    }

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

    function onDropdownFilterChange() {
      selectedNetwork = document.getElementById('filter-network').value;
      selectedLocation = document.getElementById('filter-location').value;
      selectedSpecialty = document.getElementById('filter-specialty').value;

      const resetBtn = document.getElementById('btn-reset-filters');
      if (selectedNetwork !== 'all' || selectedLocation !== 'all' || selectedSpecialty !== 'all') {
        resetBtn.classList.add('visible');
      } else {
        resetBtn.classList.remove('visible');
      }

      renderJobs();
    }

    function resetDropdownFilters() {
      document.getElementById('filter-network').value = 'all';
      document.getElementById('filter-location').value = 'all';
      document.getElementById('filter-specialty').value = 'all';
      selectedNetwork = 'all';
      selectedLocation = 'all';
      selectedSpecialty = 'all';
      document.getElementById('btn-reset-filters').classList.remove('visible');
      renderJobs();
    }

    function getSpecialtyBadge(specialty, isTop) {
      if (!specialty) return '';
      if (isTop) {
        return `<span class="badge badge-top-spec">⭐ ${specialty}</span>`;
      }
      return `<span class="badge badge-spec">${specialty}</span>`;
    }

    function getLocationBadge(j) {
      if (j.hub === 'NYC') {
        if (j.is_outside_nyc) {
          return `<span class="badge badge-outside-nyc">⚠️ Outside NYC (${j.borough_tag || 'Suburbs'})</span>`;
        }
        return `<span class="badge badge-nyc">🗽 NYC (${j.borough_tag || 'City'})</span>`;
      }
      if (j.hub === 'VA') {
        return `<span class="badge badge-va">🏛️ Northern VA</span>`;
      }
      return `<span class="badge badge-md">📍 MD / DC</span>`;
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

      // 2. Filter by Network dropdown
      if (selectedNetwork !== 'all') {
        list = list.filter(j => {
          const hosp = (j.hospital || '').toLowerCase();
          const idStr = (j.id || '').toLowerCase();
          if (selectedNetwork === 'NYP') return hosp.includes('presbyterian') || idStr.includes('nyp');
          if (selectedNetwork === 'Mount Sinai') return hosp.includes('mount sinai') || idStr.includes('mountsinai');
          if (selectedNetwork === 'NYU Langone') return hosp.includes('nyu') || idStr.includes('nyulangone');
          if (selectedNetwork === 'NYC Health + Hospitals') return hosp.includes('nyc health') || idStr.includes('nychhc') || idStr.includes('pagny');
          if (selectedNetwork === 'Johns Hopkins') return hosp.includes('hopkins') || hosp.includes('sibley') || hosp.includes('suburban') || idStr.includes('hopkins');
          if (selectedNetwork === 'MedStar') return hosp.includes('medstar') || idStr.includes('medstar');
          if (selectedNetwork === 'Adventist') return hosp.includes('adventist') || idStr.includes('adventist');
          if (selectedNetwork === 'Holy Cross') return hosp.includes('holy cross') || idStr.includes('holycross');
          if (selectedNetwork === 'Inova') return hosp.includes('inova') || idStr.includes('inova');
          return true;
        });
      }

      // 3. Filter by Location dropdown
      if (selectedLocation !== 'all') {
        list = list.filter(j => {
          if (selectedLocation === 'NYC_proper') {
            return j.hub === 'NYC' && !j.is_outside_nyc;
          }
          if (selectedLocation === 'NYC_outside') {
            return j.hub === 'NYC' && j.is_outside_nyc;
          }
          if (['Manhattan', 'Brooklyn', 'Queens', 'Bronx'].includes(selectedLocation)) {
            const bTag = (j.borough_tag || '').toLowerCase();
            const loc = (j.location || '').toLowerCase();
            const title = (j.title || '').toLowerCase();
            const hosp = (j.hospital || '').toLowerCase();
            const target = selectedLocation.toLowerCase();
            return bTag.includes(target) || loc.includes(target) || title.includes(target) || hosp.includes(target);
          }
          if (selectedLocation === 'MD') {
            return j.hub === 'MD';
          }
          if (selectedLocation === 'VA') {
            return j.hub === 'VA';
          }
          return true;
        });
      }

      // 4. Filter by Specialty dropdown
      if (selectedSpecialty !== 'all') {
        list = list.filter(j => {
          if (selectedSpecialty === 'top_5') {
            return j.is_top_specialty === true;
          }
          return j.specialty === selectedSpecialty;
        });
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

        let warningNotice = '';
        if (j.is_outside_nyc) {
          warningNotice = `
            <div class="location-warning">
              ⚠️ <strong>Location Notice:</strong> Located in ${j.borough_tag || 'the suburbs'} (outside NYC 5 boroughs).
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
                ${getLocationBadge(j)}
                ${getProbBadge(j.probability, j.is_closed)}
              </div>
            </div>
            <div class="job-meta">
              <span>📍 ${j.location}</span>
              <span>📅 ${j.posted_date}</span>
              <span>💼 Full-Time</span>
            </div>
            ${warningNotice}
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
        if d.get("hub") == "NYC" and "is_outside_nyc" not in d:
            is_outside, borough = classify_nyc_location(d.get("location", ""), d.get("title", ""))
            d["is_outside_nyc"] = is_outside
            d["borough_tag"] = borough
        jobs_data.append(d)
        
    html = HTML_TEMPLATE.replace("__JOBS_JSON__", json.dumps(jobs_data))
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    (output_dir / "jobs.json").write_text(json.dumps(jobs_data, indent=2), encoding="utf-8")
    print(f"[Dashboard] Generated docs/index.html with {len(jobs)} jobs.")

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
        for j in jobs:
            spec, is_top = detect_specialty(j.get("title", ""), j.get("description", ""))
            j["specialty"] = spec
            j["is_top_specialty"] = is_top
            if j.get("hub") == "NYC":
                is_outside, borough = classify_nyc_location(j.get("location", ""), j.get("title", ""))
                j["is_outside_nyc"] = is_outside
                j["borough_tag"] = borough
            
        generate_dashboard(jobs, docs_dir)
        print("[Standalone] Successfully rebuilt docs/index.html with outside-NYC alerts and new hubs.")
    else:
        print("[Standalone] No existing jobs found to rebuild from.")
