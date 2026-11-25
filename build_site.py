import json
import re
import time
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

    /* Dropdown Filters & Search Toolbar */
    .dropdown-filter-bar {
      max-width: 960px;
      margin: 0 auto 0.85rem;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.75rem;
      background: #1e293b;
      padding: 0.95rem 1rem;
      border: 1px solid var(--border);
      border-radius: 12px;
      align-items: flex-end;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .toolbar-top-row {
      grid-column: 1 / -1;
      display: flex;
      gap: 0.6rem;
      align-items: center;
      flex-wrap: wrap;
    }
    .search-input-wrap {
      flex: 1 1 260px;
      position: relative;
      display: flex;
      align-items: center;
    }
    .search-input {
      width: 100%;
      background: #0f172a;
      color: var(--text);
      border: 1px solid #334155;
      padding: 0.6rem 0.9rem;
      border-radius: 8px;
      font-size: 0.92rem;
      outline: none;
      font-family: inherit;
      transition: all 0.15s ease;
    }
    .search-input::placeholder {
      color: #64748b;
    }
    .search-input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
    }
    .results-summary {
      max-width: 960px;
      margin: 0 auto 1rem;
      padding: 0 0.25rem;
      font-size: 0.84rem;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.5rem;
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
      flex-direction: row;
      gap: 0.5rem;
      align-items: center;
    }
    .btn-sort-date, .btn-hide-suburbs {
      background: #0f172a;
      color: var(--text);
      border: 1px solid #334155;
      padding: 0.6rem 0.85rem;
      border-radius: 8px;
      font-size: 0.86rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      font-family: inherit;
    }
    .btn-sort-date:hover, .btn-hide-suburbs:hover {
      border-color: #64748b;
    }
    .btn-sort-date.active, .btn-hide-suburbs.active {
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent);
      border-color: var(--accent);
      font-weight: 600;
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

    .meta-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      padding: 0.18rem 0.55rem;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
    }
    .meta-salary {
      background: rgba(16, 185, 129, 0.14);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .meta-shift {
      background: rgba(56, 189, 248, 0.12);
      color: #7dd3fc;
      border: 1px solid rgba(56, 189, 248, 0.28);
    }
    .meta-shift-night {
      background: rgba(139, 92, 246, 0.15);
      color: #c4b5fd;
      border: 1px solid rgba(139, 92, 246, 0.35);
    }

    @media (max-width: 820px) {
      .dropdown-filter-bar {
        grid-template-columns: 1fr;
        gap: 0.75rem;
        padding: 0.85rem;
      }
      .filter-group-actions {
        width: 100%;
      }
      .btn-sort-date, .btn-hide-suburbs, .btn-reset-filters {
        flex: 1;
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
      gap: 1.05rem;
      color: var(--text-muted);
      font-size: 0.86rem;
      flex-wrap: wrap;
      align-items: center;
    }
    .meta-resume-ny {
      background: rgba(244, 63, 94, 0.14);
      color: #fda4af;
      border: 1px solid rgba(244, 63, 94, 0.35);
    }
    .meta-resume-md {
      background: rgba(129, 140, 248, 0.14);
      color: #a5b4fc;
      border: 1px solid rgba(129, 140, 248, 0.35);
    }
    .req-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.38rem;
      align-items: center;
    }
    .req-row-label {
      font-size: 0.74rem;
      font-weight: 700;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-right: 0.15rem;
    }
    .req-chip {
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.18rem 0.52rem;
      border-radius: 5px;
      background: rgba(148, 163, 184, 0.11);
      color: #e2e8f0;
      border: 1px solid rgba(148, 163, 184, 0.25);
    }
    .req-chip-cert {
      background: rgba(245, 158, 11, 0.14);
      color: #fde68a;
      border: 1px solid rgba(245, 158, 11, 0.35);
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
    .btn-prep {
      background: rgba(168, 85, 247, 0.14);
      color: #d8b4fe;
      border: 1px solid rgba(168, 85, 247, 0.4);
    }
    .btn-prep:hover {
      background: rgba(168, 85, 247, 0.24);
      border-color: #c084fc;
      color: #f3e8ff;
    }

    /* Floating Fast-Fill Clipboard Button & Slide-Out Drawer */
    .fab-fastfill {
      position: fixed;
      bottom: 1.5rem;
      left: 1.5rem;
      background: #1e293b;
      color: var(--accent);
      border: 1px solid rgba(56, 189, 248, 0.55);
      padding: 0.72rem 1.15rem;
      border-radius: 9999px;
      font-size: 0.9rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      z-index: 900;
      transition: transform 0.15s, background 0.15s, box-shadow 0.15s;
      font-family: inherit;
    }
    .fab-fastfill:hover {
      background: #0f172a;
      transform: translateY(-2px);
      box-shadow: 0 10px 28px rgba(56, 189, 248, 0.25);
    }
    .overlay-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(2, 6, 23, 0.75);
      backdrop-filter: blur(3px);
      z-index: 950;
      display: none;
    }
    .overlay-backdrop.open {
      display: block;
    }
    .fastfill-drawer {
      position: fixed;
      top: 0;
      right: 0;
      height: 100vh;
      width: min(440px, 100vw);
      background: #0f172a;
      border-left: 1px solid var(--border);
      box-shadow: -10px 0 35px rgba(0, 0, 0, 0.6);
      z-index: 980;
      transform: translateX(105%);
      transition: transform 0.22s ease;
      display: flex;
      flex-direction: column;
    }
    .fastfill-drawer.open {
      transform: translateX(0);
    }
    .drawer-header, .modal-header {
      padding: 1rem 1.2rem;
      background: #1e293b;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
    }
    .drawer-title, .modal-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--text);
      margin: 0;
    }
    .btn-close-x {
      background: transparent;
      border: 1px solid #475569;
      color: var(--text-muted);
      border-radius: 7px;
      padding: 0.35rem 0.65rem;
      cursor: pointer;
      font-size: 0.88rem;
      font-weight: 600;
    }
    .btn-close-x:hover {
      color: var(--text);
      border-color: #94a3b8;
    }
    .drawer-body, .modal-body {
      padding: 1rem 1.2rem;
      overflow-y: auto;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }
    .privacy-note {
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #a7f3d0;
      font-size: 0.78rem;
      padding: 0.55rem 0.75rem;
      border-radius: 8px;
      line-height: 1.4;
    }
    .ff-card {
      background: #1e293b;
      border: 1px solid var(--border);
      border-radius: 9px;
      padding: 0.7rem 0.85rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
    }
    .ff-card-text {
      min-width: 0;
      flex: 1;
    }
    .ff-label {
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #94a3b8;
      margin-bottom: 0.2rem;
    }
    .ff-val {
      font-size: 0.86rem;
      color: var(--text);
      word-break: break-word;
      white-space: pre-wrap;
    }
    .ff-empty {
      color: #64748b;
      font-style: italic;
      font-size: 0.82rem;
    }
    .ff-input, .ff-textarea, .prep-textarea {
      width: 100%;
      background: #0f172a;
      color: var(--text);
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 0.55rem 0.75rem;
      font-size: 0.88rem;
      font-family: inherit;
      outline: none;
    }
    .ff-textarea {
      min-height: 76px;
      resize: vertical;
    }
    .ff-input:focus, .ff-textarea:focus, .prep-textarea:focus {
      border-color: var(--accent);
    }

    /* Application Prep / Cover Letter Modal */
    .prep-modal {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: min(680px, 94vw);
      max-height: 90vh;
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 14px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7);
      z-index: 990;
      display: none;
      flex-direction: column;
      overflow: hidden;
    }
    .prep-modal.open {
      display: flex;
    }
    .kw-list {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
    }
    .kw-chip {
      background: rgba(168, 85, 247, 0.14);
      color: #d8b4fe;
      border: 1px solid rgba(168, 85, 247, 0.35);
      border-radius: 6px;
      padding: 0.25rem 0.6rem;
      font-size: 0.78rem;
      font-weight: 600;
    }
    .prep-tabs {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .prep-tab-btn {
      background: #1e293b;
      color: var(--text-muted);
      border: 1px solid var(--border);
      padding: 0.42rem 0.8rem;
      border-radius: 7px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
    }
    .prep-tab-btn.active {
      background: rgba(56, 189, 248, 0.18);
      color: var(--accent);
      border-color: var(--accent);
    }
    .prep-textarea {
      min-height: 230px;
      line-height: 1.5;
      resize: vertical;
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

  <!-- Search + Quick Actions + 3 Clean Dropdown Filters -->
  <div class="dropdown-filter-bar">
    <div class="toolbar-top-row">
      <div class="search-input-wrap">
        <input
          type="search"
          id="search-input"
          class="search-input"
          placeholder="🔍 Search title, hospital, shift, or keyword (e.g. Bellevue, ENT, night)..."
          oninput="onSearchInput()"
          aria-label="Search jobs"
        />
      </div>
      <div class="filter-group-actions">
        <button class="btn-hide-suburbs" id="btn-hide-suburbs" onclick="toggleHideSuburbs()" title="Remember preference to hide Long Island and Westchester suburb roles">
          🗽 Hide NYC Suburbs
        </button>
        <button class="btn-sort-date" id="btn-sort-date" onclick="toggleDateSort()" title="Cycle sort order by posting date">
          📅 Sort by Date
        </button>
        <button class="btn-reset-filters" id="btn-reset-filters" onclick="resetDropdownFilters()">
          ↺ Reset
        </button>
      </div>
    </div>

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
  </div>

  <div class="results-summary" id="results-summary"></div>

  <div class="jobs-grid" id="jobs-container">
    <!-- Rendered via JavaScript -->
  </div>

  <!-- Floating Fast-Fill Button -->
  <button class="fab-fastfill" onclick="openFastFillDrawer()" title="Quick-copy your license, certs, and rotation info for portal applications">
    📋 Fast-Fill Info
  </button>

  <!-- Backdrop -->
  <div class="overlay-backdrop" id="overlay-backdrop" onclick="closeAllOverlays()"></div>

  <!-- Fast-Fill Slide-Out Drawer -->
  <aside class="fastfill-drawer" id="fastfill-drawer" aria-label="Application Fast-Fill Clipboard">
    <div class="drawer-header">
      <h2 class="drawer-title">📋 Application Fast-Fill</h2>
      <div class="action-group">
        <button class="btn-outline" id="btn-ff-mode" onclick="toggleFastFillEdit()">✏️ Edit</button>
        <button class="btn-close-x" onclick="closeAllOverlays()">✕</button>
      </div>
    </div>
    <div class="drawer-body" id="fastfill-body"></div>
  </aside>

  <!-- Cover Letter & ATS Keywords Modal -->
  <div class="prep-modal" id="prep-modal" role="dialog" aria-modal="true" aria-label="Application Cover Letter and ATS Keywords">
    <div class="modal-header">
      <div>
        <h2 class="modal-title" id="prep-modal-title">✉️ Cover Letter & Resume Keywords</h2>
        <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem;" id="prep-modal-subtitle"></div>
      </div>
      <button class="btn-close-x" onclick="closeAllOverlays()">✕</button>
    </div>
    <div class="modal-body">
      <div>
        <div id="prep-real-reqs-wrap" style="display:none; margin-bottom:0.75rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem; gap:0.5rem;">
            <span class="ff-label" style="margin:0;">📋 Real Terms Found in This Hospital Posting</span>
            <button class="btn-outline" style="padding:0.25rem 0.6rem; font-size:0.76rem;" onclick="copyRealReqs()">📋 Copy Posting Terms</button>
          </div>
          <div class="kw-list" id="prep-real-reqs"></div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.45rem; gap:0.5rem;">
          <span class="ff-label" style="margin:0;">💡 Suggested Specialty ATS Keywords</span>
          <button class="btn-outline" style="padding:0.28rem 0.65rem; font-size:0.78rem;" onclick="copyPrepKeywords()">📋 Copy Suggested</button>
        </div>
        <div class="kw-list" id="prep-keywords"></div>
      </div>

      <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem; gap:0.5rem; flex-wrap:wrap;">
          <div class="prep-tabs">
            <button class="prep-tab-btn active" id="prep-mode-short" onclick="setCoverLetterMode('short')">⚡ Portal Note ("Why Us")</button>
            <button class="prep-tab-btn" id="prep-mode-full" onclick="setCoverLetterMode('full')">📄 Full Cover Letter</button>
          </div>
          <button class="btn-primary" style="padding:0.42rem 0.9rem; font-size:0.84rem;" onclick="copyPrepCoverLetter()">📋 Copy Text</button>
        </div>
        <textarea id="prep-cover-text" class="prep-textarea"></textarea>
        <div style="font-size:0.76rem; color:#64748b; margin-top:0.35rem;">
          💡 Tip: Fill in your name, PA program, and rotations once in <strong>📋 Fast-Fill Info</strong> (bottom-left) and they auto-populate here.
        </div>
      </div>

      <div style="display:flex; justify-content:space-between; align-items:center; gap:0.75rem; flex-wrap:wrap; padding-top:0.35rem; border-top:1px solid #1e293b;">
        <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;">
          <a id="prep-apply-link" class="btn-primary" href="#" target="_blank" rel="noopener noreferrer">Open Hospital Portal ↗</a>
          <span id="prep-resume-hint"></span>
        </div>
        <button class="btn-outline" onclick="openFastFillFromPrep()">📋 Open Fast-Fill Clipboard</button>
      </div>
    </div>
  </div>

  <div class="toast" id="toast">Status updated!</div>

  <script>
    const JOBS = __JOBS_JSON__;
    const GENERATED_AT_MS = __GENERATED_AT_MS__;
    const STORAGE_KEY = 'ridplier_job_status_v1';
    const HIDE_SUBURBS_KEY = 'ridplier_hide_outside_nyc_v1';
    const FASTFILL_KEY = 'ridplier_fastfill_profile_v1';
    
    // Supabase Cloud Sync Configuration
    const SUPABASE_URL = "https://lmfjzjkkaytnrmiqadut.supabase.co";
    const SUPABASE_KEY = "sb_publishable__2yNARQiGOBhIIariC0t-Q_LSfzaIcc";

    let currentStatusTab = 'to_apply'; // 'to_apply' | 'applied' | 'dismissed'
    let selectedNetwork = 'all';
    let selectedLocation = 'all';
    let selectedSpecialty = 'all';
    let searchQuery = '';
    let hideOutsideNYC = localStorage.getItem(HIDE_SUBURBS_KEY) === 'true';
    let dateSortMode = 'none';         // 'none' | 'desc' | 'asc'
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

    function updateFilterActionButtons() {
      const resetBtn = document.getElementById('btn-reset-filters');
      if (selectedNetwork !== 'all' || selectedLocation !== 'all' || selectedSpecialty !== 'all' || searchQuery !== '' || dateSortMode !== 'none') {
        resetBtn.classList.add('visible');
      } else {
        resetBtn.classList.remove('visible');
      }

      const hideBtn = document.getElementById('btn-hide-suburbs');
      if (hideOutsideNYC) {
        hideBtn.classList.add('active');
        hideBtn.textContent = '🗽 Hiding Suburbs';
      } else {
        hideBtn.classList.remove('active');
        hideBtn.textContent = '🗽 Hide NYC Suburbs';
      }

      const sortBtn = document.getElementById('btn-sort-date');
      if (dateSortMode === 'desc') {
        sortBtn.classList.add('active');
        sortBtn.textContent = '📅 Newest First ↓';
      } else if (dateSortMode === 'asc') {
        sortBtn.classList.add('active');
        sortBtn.textContent = '📅 Oldest First ↑';
      } else {
        sortBtn.classList.remove('active');
        sortBtn.textContent = '📅 Sort by Date';
      }
    }

    function onSearchInput() {
      searchQuery = document.getElementById('search-input').value.trim().toLowerCase();
      updateFilterActionButtons();
      renderJobs();
    }

    function toggleHideSuburbs() {
      hideOutsideNYC = !hideOutsideNYC;
      try {
        localStorage.setItem(HIDE_SUBURBS_KEY, hideOutsideNYC ? 'true' : 'false');
      } catch (e) {}
      if (hideOutsideNYC && selectedLocation === 'NYC_outside') {
        selectedLocation = 'all';
        document.getElementById('filter-location').value = 'all';
      }
      updateFilterActionButtons();
      renderJobs();
    }

    function onDropdownFilterChange() {
      selectedNetwork = document.getElementById('filter-network').value;
      selectedLocation = document.getElementById('filter-location').value;
      selectedSpecialty = document.getElementById('filter-specialty').value;
      if (selectedLocation === 'NYC_outside' && hideOutsideNYC) {
        hideOutsideNYC = false;
        try { localStorage.setItem(HIDE_SUBURBS_KEY, 'false'); } catch (e) {}
      }
      updateFilterActionButtons();
      renderJobs();
    }

    function toggleDateSort() {
      if (dateSortMode === 'none') {
        dateSortMode = 'desc';
      } else if (dateSortMode === 'desc') {
        dateSortMode = 'asc';
      } else {
        dateSortMode = 'none';
      }
      updateFilterActionButtons();
      renderJobs();
    }

    function resetDropdownFilters() {
      document.getElementById('filter-network').value = 'all';
      document.getElementById('filter-location').value = 'all';
      document.getElementById('filter-specialty').value = 'all';
      document.getElementById('search-input').value = '';
      selectedNetwork = 'all';
      selectedLocation = 'all';
      selectedSpecialty = 'all';
      searchQuery = '';
      dateSortMode = 'none';
      updateFilterActionButtons();
      renderJobs();
    }

    function getShiftMetaBadge(shift) {
      if (!shift) return '';
      if (shift === 'Nights') return `<span class="meta-pill meta-shift-night">🌙 ${shift}</span>`;
      if (shift === 'Days') return `<span class="meta-pill meta-shift">☀️ ${shift}</span>`;
      if (shift === 'Evenings / Swing') return `<span class="meta-pill meta-shift">🌆 ${shift}</span>`;
      if (shift === 'Weekends') return `<span class="meta-pill meta-shift">🗓️ ${shift}</span>`;
      return `<span class="meta-pill meta-shift">🔄 ${shift}</span>`;
    }

    function getRecommendedResume(job) {
      return job && job.hub === 'NYC' ? 'Resume_NY.pdf' : 'Resume_MD.pdf';
    }

    function getResumeMetaBadge(job) {
      const fname = getRecommendedResume(job);
      const cls = job && job.hub === 'NYC' ? 'meta-resume-ny' : 'meta-resume-md';
      return `<span class="meta-pill ${cls}">📄 Use: ${fname}</span>`;
    }

    const CERT_REQ_NAMES = new Set(['ACLS', 'PALS', 'ATLS', 'BLS', 'DEA', 'NYS Infection Control']);

    function renderCardRequirements(reqs) {
      if (!Array.isArray(reqs) || reqs.length === 0) return '';
      const chips = reqs.map(r => {
        const cls = CERT_REQ_NAMES.has(r) ? 'req-chip req-chip-cert' : 'req-chip';
        return `<span class="${cls}">${escapeHtml(r)}</span>`;
      }).join('');
      return `<div class="req-row"><span class="req-row-label">📋 Posting Mentions:</span>${chips}</div>`;
    }

    const MONTH_INDEX = {
      jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5,
      jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11
    };

    function parsePostedDateMs(dateStr) {
      if (!dateStr) return null;
      const s = String(dateStr).trim();
      const lower = s.toLowerCase();

      // 1. ISO date: YYYY-MM-DD
      const isoMatch = s.match(/^(\\d{4})-(\\d{2})-(\\d{2})/);
      if (isoMatch) {
        return new Date(Number(isoMatch[1]), Number(isoMatch[2]) - 1, Number(isoMatch[3])).getTime();
      }

      // 2. "Mon DD, YYYY" (e.g. "Nov 23, 2026")
      const monMatch = s.match(/^([A-Za-z]{3})\\s+(\\d{1,2}),\\s*(\\d{4})$/);
      if (monMatch) {
        const mIdx = MONTH_INDEX[monMatch[1].toLowerCase()];
        if (mIdx !== undefined) {
          return new Date(Number(monMatch[3]), mIdx, Number(monMatch[2])).getTime();
        }
      }

      // 3. Workday relative strings anchored to dashboard generation timestamp
      const DAY_MS = 86400000;
      if (lower.includes('today')) return GENERATED_AT_MS;
      if (lower.includes('yesterday')) return GENERATED_AT_MS - DAY_MS;
      const daysMatch = lower.match(/(\\d+)\\+?\\s*days?\\s*ago/);
      if (daysMatch) {
        const days = Number(daysMatch[1]) + (lower.includes('+') ? 1 : 0);
        return GENERATED_AT_MS - days * DAY_MS;
      }

      return null;
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

      // 4b. Apply remembered Hide Outside NYC Suburbs preference
      let hiddenSuburbCount = 0;
      if (hideOutsideNYC && selectedLocation !== 'NYC_outside') {
        hiddenSuburbCount = list.filter(j => j.is_outside_nyc === true).length;
        list = list.filter(j => !j.is_outside_nyc);
      }

      // 4c. Apply free-text keyword search
      if (searchQuery) {
        list = list.filter(j => {
          const hay = [
            j.title, j.hospital, j.location, j.borough_tag,
            j.specialty, j.shift, j.salary_range, j.match_reason,
            Array.isArray(j.requirements) ? j.requirements.join(' ') : '',
            getRecommendedResume(j)
          ].filter(Boolean).join(' ').toLowerCase();
          return hay.includes(searchQuery);
        });
      }

      // 5. Sort by posting date if active
      if (dateSortMode !== 'none') {
        list = [...list].sort((a, b) => {
          const ta = parsePostedDateMs(a.posted_date);
          const tb = parsePostedDateMs(b.posted_date);
          if (ta === null && tb === null) return 0;
          if (ta === null) return 1;
          if (tb === null) return -1;
          return dateSortMode === 'desc' ? tb - ta : ta - tb;
        });
      }

      const summaryEl = document.getElementById('results-summary');
      if (summaryEl) {
        const suburbNote = hiddenSuburbCount > 0 ? ` · ${hiddenSuburbCount} outside-NYC suburb role(s) hidden` : '';
        summaryEl.textContent = `Showing ${list.length} listing${list.length === 1 ? '' : 's'}${suburbNote}`;
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
              <div class="action-group">
                <a class="btn-primary" href="${j.url}" target="_blank" rel="noopener noreferrer">
                  Apply on Hospital Site ↗
                </a>
                <button class="btn-outline btn-prep" onclick="openPrepModal('${j.id}')">
                  ✉️ Cover Letter & Keywords
                </button>
              </div>
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
                <button class="btn-outline btn-prep" onclick="openPrepModal('${j.id}')">
                  ✉️ Cover Letter & Keywords
                </button>
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
              ${getShiftMetaBadge(j.shift)}
              ${j.salary_range ? `<span class="meta-pill meta-salary">💵 ${j.salary_range}</span>` : ''}
              ${getResumeMetaBadge(j)}
            </div>
            ${renderCardRequirements(j.requirements)}
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

    // --- Fast-Fill Clipboard & Cover Letter Generator ---
    const FASTFILL_FIELDS = [
      { key: 'full_name', label: 'Full Name & Credentials', placeholder: 'e.g. Jane Doe, MS, PA-C' },
      { key: 'email', label: 'Email Address', placeholder: 'e.g. name@email.com' },
      { key: 'phone', label: 'Phone Number', placeholder: 'e.g. (555) 123-4567' },
      { key: 'location', label: 'Target City / Address', placeholder: 'e.g. New York, NY or Germantown, MD' },
      { key: 'pa_school', label: 'PA Program, Degree & Grad Date', placeholder: 'e.g. MS in Physician Assistant Studies, Aug 2026' },
      { key: 'nccpa', label: 'NCCPA Certification / PANCE Status', placeholder: 'e.g. NCCPA Certified (PA-C), Passed Aug 2026 | ID: #' },
      { key: 'ny_license', label: 'NY State PA License Status', placeholder: 'e.g. NYS Application Submitted / Pending Issuance' },
      { key: 'md_va_license', label: 'MD / VA PA License Status', placeholder: 'e.g. MD Application in Progress / Eligible' },
      { key: 'certs', label: 'BLS / ACLS / PALS & NYS Courses', placeholder: 'e.g. AHA BLS, ACLS (Date); NYS Infection Control & Child Abuse' },
      { key: 'rotations', label: 'Clinical Rotations Summary (Paste Block)', placeholder: 'Emergency Medicine, ENT/Facial Plastics, General Surgery, Urgent Care, Internal Medicine...', multiline: true },
      { key: 'references', label: 'Preceptor / Physician References', placeholder: 'Name, Title, Hospital, Email/Phone...', multiline: true },
    ];

    const SPECIALTY_KEYWORDS = {
      'ENT / Head & Neck': ['Otolaryngology', 'Flexible Fiberoptic Laryngoscopy', 'Nasal Endoscopy', 'Cerumen Disimpaction', 'Epistaxis Management', 'Head & Neck Pre-/Post-Op', 'Facial Plastics & Reconstructive', 'Audiogram Review'],
      'Dermatology': ['Dermatologic Assessment', 'Skin Lesion Evaluation', 'Punch & Shave Biopsy Assist', 'Cryotherapy', 'Wound Closure & Suturing', 'Abscess Incision & Drainage', 'Cellulitis Management', 'Sterile Technique'],
      'Emergency Medicine (ER)': ['ESI Triage & Stabilization', 'High-Acuity Adult & Pediatric ED', 'Multi-Layer Laceration Repair', 'Abscess I&D', 'Fracture & Joint Splinting', 'Basic Airway Management', 'EKG Interpretation', 'Fast-Track Workflows'],
      'Surgery': ['Surgical First- & Second-Assist', 'Sterile Field & Operating Room', 'Laparoscopic & General Surgery', 'Subcuticular & Staple Closure', 'Surgical Knot Tying', 'Pre-Op H&Ps', 'Post-Op Daily Rounding', 'Wound Checks & Drain Care'],
      'Urgent Care': ['Walk-In Acute Care', 'Undifferentiated Complaints', 'Point-of-Care Testing (Strep/Flu/COVID/UA)', 'Minor Procedures & I&D', 'Laceration Repair & Splinting', 'Foreign Body Removal', 'Pediatric & Adult Visits'],
      'Critical Care / ICU': ['ICU Daily Rounding', 'Critical Care Assessment', 'Basic Airway & Ventilator Exposure', 'ABG / Lab Interpretation', 'Multidisciplinary ICU Team', 'Procedure Readiness', 'Epic EMR'],
      'Cardiology': ['EKG & Rhythm Interpretation', 'Inpatient Cardiology Rounding', 'Chest Pain / ACS Workup', 'Medication Reconciliation', 'Pre-/Post-Procedure Assessment', 'Patient Counseling'],
      'Internal Medicine': ['Inpatient Hospitalist Rounding', 'Complex Differential Diagnosis', 'Order Entry & Discharge Planning', 'Medication Reconciliation', 'Multidisciplinary Care Coordination', 'SOAP Documentation'],
      'Primary Care': ['Outpatient Chronic Disease Management', 'Preventive Screenings & Wellness', 'Patient Education & Counseling', 'Point-of-Care Testing', 'Athena / Epic / eClinicalWorks EHR'],
      'Obstetrics & Gynecology': ['Pelvic Examinations', 'Prenatal & Postpartum Visits', 'Gyn Office Procedures', 'Preventive Screenings', 'Patient Counseling'],
      'General / Inpatient': ['History & Physical Exams', 'Differential Diagnosis', 'Clinical Documentation & SOAP Notes', 'Order Entry & Labs', 'Sterile Technique & Procedures', 'Epic EMR'],
    };

    let fastFillEditMode = false;
    let activePrepJobId = null;
    let coverLetterMode = 'short';

    function getFastFillProfile() {
      try {
        const raw = localStorage.getItem(FASTFILL_KEY);
        return raw ? JSON.parse(raw) : {};
      } catch (e) {
        return {};
      }
    }

    function saveFastFillProfile() {
      const next = {};
      FASTFILL_FIELDS.forEach(f => {
        const el = document.getElementById('ff-input-' + f.key);
        if (el) next[f.key] = el.value.trim();
      });
      try {
        localStorage.setItem(FASTFILL_KEY, JSON.stringify(next));
      } catch (e) {}
      fastFillEditMode = false;
      renderFastFillDrawer();
      showToast('Fast-Fill profile saved locally 🔒');
    }

    async function copyText(text, label = 'Text') {
      if (!text) {
        showToast('Nothing to copy yet — tap Edit to fill in');
        return;
      }
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(text);
        } else {
          const ta = document.createElement('textarea');
          ta.value = text;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
        }
        showToast(`Copied ${label} 📋`);
      } catch (e) {
        showToast('Copy failed — select text manually');
      }
    }

    function escapeHtml(str) {
      return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function renderFastFillDrawer() {
      const profile = getFastFillProfile();
      const body = document.getElementById('fastfill-body');
      const modeBtn = document.getElementById('btn-ff-mode');
      modeBtn.textContent = fastFillEditMode ? '👁️ Copy View' : '✏️ Edit';

      const privacyBanner = `<div class="privacy-note">🔒 <strong>Private to your browser:</strong> Info saved here stays strictly in this device's <code>localStorage</code> and is never committed to GitHub or sent to external servers.</div>`;

      if (fastFillEditMode) {
        const inputsHtml = FASTFILL_FIELDS.map(f => {
          const val = escapeHtml(profile[f.key] || '');
          const fieldMarkup = f.multiline
            ? `<textarea id="ff-input-${f.key}" class="ff-textarea" placeholder="${escapeHtml(f.placeholder)}">${val}</textarea>`
            : `<input type="text" id="ff-input-${f.key}" class="ff-input" value="${val}" placeholder="${escapeHtml(f.placeholder)}" />`;
          return `<div><div class="ff-label">${f.label}</div>${fieldMarkup}</div>`;
        }).join('');
        body.innerHTML = `${privacyBanner}${inputsHtml}<button class="btn-primary" style="justify-content:center; padding:0.75rem;" onclick="saveFastFillProfile()">💾 Save Fast-Fill Profile Locally</button>`;
        return;
      }

      const cardsHtml = FASTFILL_FIELDS.map(f => {
        const val = (profile[f.key] || '').trim();
        return `
          <div class="ff-card">
            <div class="ff-card-text">
              <div class="ff-label">${f.label}</div>
              ${val ? `<div class="ff-val">${escapeHtml(val)}</div>` : `<div class="ff-empty">Tap ✏️ Edit to save (${escapeHtml(f.placeholder)})</div>`}
            </div>
            ${val ? `<button class="btn-outline" style="padding:0.4rem 0.75rem; font-size:0.8rem;" onclick="copyFastFillField('${f.key}')">📋 Copy</button>` : ''}
          </div>
        `;
      }).join('');
      body.innerHTML = `${privacyBanner}${cardsHtml}`;
    }

    function copyFastFillField(key) {
      const profile = getFastFillProfile();
      const field = FASTFILL_FIELDS.find(f => f.key === key);
      copyText(profile[key] || '', field ? field.label : 'Field');
    }

    function openFastFillDrawer() {
      const profile = getFastFillProfile();
      if (Object.values(profile).every(v => !v)) {
        fastFillEditMode = true;
      }
      renderFastFillDrawer();
      document.getElementById('overlay-backdrop').classList.add('open');
      document.getElementById('fastfill-drawer').classList.add('open');
      document.getElementById('prep-modal').classList.remove('open');
    }

    function toggleFastFillEdit() {
      fastFillEditMode = !fastFillEditMode;
      renderFastFillDrawer();
    }

    function closeAllOverlays() {
      document.getElementById('overlay-backdrop').classList.remove('open');
      document.getElementById('fastfill-drawer').classList.remove('open');
      document.getElementById('prep-modal').classList.remove('open');
    }

    function openFastFillFromPrep() {
      closeAllOverlays();
      openFastFillDrawer();
    }

    function getMatchedKeywords(job) {
      const base = [...(SPECIALTY_KEYWORDS[job.specialty] || SPECIALTY_KEYWORDS['General / Inpatient'])];
      const t = (job.title || '').toLowerCase();
      if (t.includes('trauma') && !base.includes('Trauma Assessment')) base.unshift('Trauma Assessment');
      if (t.includes('robotic') && !base.includes('Robotic / Minimally Invasive Surgery')) base.unshift('Robotic / Minimally Invasive Surgery');
      if (t.includes('ortho') && !base.includes('Orthopedic Casting & Splinting')) base.unshift('Orthopedic Casting & Splinting');
      if (t.includes('plastic') && !base.includes('Facial Plastics & Reconstructive Care')) base.unshift('Facial Plastics & Reconstructive Care');
      return base.slice(0, 8);
    }

    function buildCoverLetterText(job, mode) {
      const p = getFastFillProfile();
      const name = p.full_name || '[Your Name, MS, PA-C]';
      const school = p.pa_school || 'my Master of Science in Physician Assistant Studies';
      const spec = job.specialty || 'Clinical Practice';
      const hospitalClean = (job.hospital || 'your organization').replace(/\\s*\\(Suburbs\\)/i, '');

      const rotationHighlightMap = {
        'ENT / Head & Neck': 'during my ENT & Facial Plastic Reconstructive Surgery clinical rotation, where I assisted with office-based otolaryngology procedures (flexible laryngoscopy, cerumen removal, ear irrigation) as well as pre-, intra-, and post-operative head and neck surgical evaluations',
        'Dermatology': 'across my Facial Plastic Reconstructive Surgery, Urgent Care, and General Surgery rotations, where I gained hands-on experience with skin lesion assessments, wound closures, suturing, incision and drainage procedures, and sterile technique',
        'Emergency Medicine (ER)': 'during my high-volume Emergency Medicine and Urgent Care rotations, evaluating acute adult and pediatric patients and performing laceration repairs, wound closures, splinting, abscess I&D, and airway management',
        'Surgery': 'during my General Surgery and ENT & Facial Plastic Surgery rotations, where I first- and second-assisted in the operating room, maintained sterile technique, tied surgical knots, and managed pre-operative workups and post-operative rounding',
        'Urgent Care': 'across my Urgent Care, Emergency Medicine, and prior urgent-care Medical Assistant experience, managing high-volume acute walk-in patients, point-of-care diagnostics, laceration repairs, and minor outpatient procedures',
      };
      const highlight = p.rotations
        ? `across my clinical training (${p.rotations})`
        : (rotationHighlightMap[spec] || 'across my inpatient and outpatient clinical rotations, including Emergency Medicine, General Surgery, Internal Medicine, and ENT');

      if (mode === 'short') {
        return `Hello ${hospitalClean} Hiring Team,\\n\\nI am an NCCPA board-certified Physician Assistant (PA-C) and recent ${school} graduate eager to apply for the ${job.title} role in ${job.location}. I developed strong procedural and collaborative clinical skills ${highlight}.\\n\\nI would welcome the opportunity to bring my adaptability, Epic/EMR readiness, and dedication to patient care to ${hospitalClean}.`;
      }

      const contactLine = [p.email, p.phone, p.location].filter(Boolean).join(' | ');
      const header = contactLine ? `${name}\\n${contactLine}\\n\\n` : '';
      const credsNote = [p.nccpa, p.ny_license, p.md_va_license].filter(Boolean).join(' · ');
      const credsSentence = credsNote ? ` Credential status: ${credsNote}.` : '';

      return `${header}Dear Hiring Team at ${hospitalClean},\\n\\nI am writing to express my enthusiastic interest in the ${job.title} position located in ${job.location}. As an NCCPA-certified Physician Assistant (PA-C) trained through ${school}, I am excited to begin my PA career contributing to ${hospitalClean}'s ${spec} team.\\n\\nIn clinical training, I built a strong procedural and diagnostic foundation ${highlight}. Combined with hands-on clinical support experience across primary and urgent care settings, I am comfortable thriving in fast-paced clinical teams, writing thorough SOAP documentation, and partnering closely with supervising physicians and nursing staff.${credsSentence}\\n\\nThank you for your time and consideration. I look forward to the opportunity to discuss how I can support your patients and care team.\\n\\nSincerely,\\n${name}`;
    }

    function openPrepModal(jobId) {
      const job = getAllKnownJobs().find(j => j.id === jobId);
      if (!job) return;
      activePrepJobId = jobId;
      coverLetterMode = 'short';

      document.getElementById('prep-modal-title').textContent = `✉️ ${job.title}`;
      document.getElementById('prep-modal-subtitle').textContent = `${job.hospital} · ${job.location} · ${job.specialty}`;
      document.getElementById('prep-apply-link').href = job.url;
      document.getElementById('prep-resume-hint').innerHTML = getResumeMetaBadge(job);

      const realWrap = document.getElementById('prep-real-reqs-wrap');
      const realReqs = Array.isArray(job.requirements) ? job.requirements : [];
      if (realReqs.length > 0) {
        realWrap.style.display = 'block';
        document.getElementById('prep-real-reqs').innerHTML = realReqs.map(r => {
          const cls = CERT_REQ_NAMES.has(r) ? 'req-chip req-chip-cert' : 'req-chip';
          return `<span class="${cls}">${escapeHtml(r)}</span>`;
        }).join('');
      } else {
        realWrap.style.display = 'none';
      }

      const kws = getMatchedKeywords(job);
      document.getElementById('prep-keywords').innerHTML = kws.map(k => `<span class="kw-chip">${escapeHtml(k)}</span>`).join('');

      document.getElementById('prep-mode-short').classList.add('active');
      document.getElementById('prep-mode-full').classList.remove('active');
      document.getElementById('prep-cover-text').value = buildCoverLetterText(job, 'short');

      document.getElementById('overlay-backdrop').classList.add('open');
      document.getElementById('prep-modal').classList.add('open');
      document.getElementById('fastfill-drawer').classList.remove('open');
    }

    function setCoverLetterMode(mode) {
      coverLetterMode = mode;
      document.getElementById('prep-mode-short').classList.toggle('active', mode === 'short');
      document.getElementById('prep-mode-full').classList.toggle('active', mode === 'full');
      const job = getAllKnownJobs().find(j => j.id === activePrepJobId);
      if (job) {
        document.getElementById('prep-cover-text').value = buildCoverLetterText(job, mode);
      }
    }

    function copyPrepCoverLetter() {
      const txt = document.getElementById('prep-cover-text').value;
      copyText(txt, coverLetterMode === 'short' ? 'Portal Note' : 'Cover Letter');
    }

    function copyPrepKeywords() {
      const job = getAllKnownJobs().find(j => j.id === activePrepJobId);
      if (!job) return;
      copyText(getMatchedKeywords(job).join(', '), 'Suggested Keywords');
    }

    function copyRealReqs() {
      const job = getAllKnownJobs().find(j => j.id === activePrepJobId);
      if (!job || !Array.isArray(job.requirements) || job.requirements.length === 0) return;
      copyText(job.requirements.join(', '), 'Posting Requirements');
    }

    // 1. Initial instant render from local storage
    updateFilterActionButtons();
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
        
    html = (
        HTML_TEMPLATE.replace("__JOBS_JSON__", json.dumps(jobs_data))
        .replace("__GENERATED_AT_MS__", str(int(time.time() * 1000)))
    )
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
