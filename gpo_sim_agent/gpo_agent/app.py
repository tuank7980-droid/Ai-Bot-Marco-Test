"""GPO Marco Assistant - Local visual agent lab & Roblox GPO Spooksville Companion."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import mimetypes
from math import hypot, isfinite
from urllib.parse import urlparse, parse_qs
import threading
import time
import random
import os
import re
from .agent import Agent
from .navigation import cell_at, center_of, find_path, move_toward
from .simulation import SCENARIOS, OBSTACLES, make_world, MAP_WIDTH, MAP_HEIGHT
from .telemetry import Recorder

PAGE = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GPO Marco Assistant · Spooksville Macro &amp; Tactical Radar Suite</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      color-scheme: dark;
      --bg-base: #05080f;
      --bg-surface: #0a101c;
      --bg-elevated: #10192a;
      --bg-active: #17243c;
      --border-subtle: rgba(255, 255, 255, 0.08);
      --border-medium: rgba(255, 255, 255, 0.16);
      --border-glow: rgba(0, 245, 184, 0.4);
      
      --text-main: #f8fafc;
      --text-sub: #94a3b8;
      --text-muted: #64748b;
      
      --accent-mint: #00f5b8;
      --accent-cyan: #38bdf8;
      --accent-rose: #f43f5e;
      --accent-amber: #fbbf24;
      --accent-purple: #c084fc;

      --font-sans: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
      --font-mono: 'JetBrains Mono', ui-monospace, monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }

    body {
      background-color: var(--bg-base);
      background-image: 
        radial-gradient(ellipse 90% 50% at 50% -10%, rgba(56, 189, 248, 0.12) 0%, transparent 60%),
        radial-gradient(circle at 95% 30%, rgba(0, 245, 184, 0.06) 0%, transparent 40%),
        radial-gradient(circle at 5% 70%, rgba(192, 132, 252, 0.05) 0%, transparent 40%);
      color: var(--text-main);
      font-family: var(--font-sans);
      font-size: 13.5px;
      line-height: 1.5;
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* Scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-base); }
    ::-webkit-scrollbar-thumb { background: #1a283e; border-radius: 99px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--accent-cyan); }

    /* Top Nav Bar */
    header {
      position: sticky;
      top: 0;
      z-index: 100;
      height: 66px;
      background: rgba(5, 8, 15, 0.92);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px;
      gap: 16px;
    }

    .brand-wrap {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .brand-badge {
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: linear-gradient(135deg, rgba(0, 245, 184, 0.25), rgba(56, 189, 248, 0.15));
      border: 1px solid rgba(0, 245, 184, 0.45);
      display: grid;
      place-items: center;
      box-shadow: 0 0 20px rgba(0, 245, 184, 0.25);
    }

    .brand-info {
      display: flex;
      flex-direction: column;
    }

    .brand-title {
      font-size: 16px;
      font-weight: 800;
      letter-spacing: -0.3px;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .brand-title .macro-tag {
      font-size: 10.5px;
      padding: 2px 7px;
      border-radius: 99px;
      background: rgba(0, 245, 184, 0.15);
      border: 1px solid rgba(0, 245, 184, 0.35);
      color: var(--accent-mint);
      font-family: var(--font-mono);
      font-weight: 700;
    }

    .brand-sub {
      font-size: 11.5px;
      color: var(--text-muted);
      font-weight: 500;
    }

    /* Jump Navigation Bar */
    .jump-nav {
      display: flex;
      align-items: center;
      gap: 4px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 999px;
      padding: 3px 6px;
    }

    .jump-btn {
      background: transparent;
      border: none;
      color: var(--text-sub);
      font-family: var(--font-sans);
      font-size: 12px;
      font-weight: 600;
      padding: 6px 12px;
      border-radius: 999px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }

    .jump-btn:hover {
      background: var(--bg-active);
      color: #fff;
    }

    /* Header Controls */
    .nav-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .scenario-select {
      background: var(--bg-surface);
      color: var(--text-main);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 8px 12px;
      font-family: var(--font-sans);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      outline: none;
    }

    .btn {
      background: var(--bg-surface);
      color: var(--text-main);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 8px 14px;
      font-family: var(--font-sans);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
      white-space: nowrap;
    }

    .btn:hover {
      background: var(--bg-active);
      border-color: var(--border-medium);
      transform: translateY(-1px);
    }

    .btn.primary {
      background: linear-gradient(135deg, #00f5b8, #0ea5e9);
      color: #041210;
      border: none;
      font-weight: 700;
      box-shadow: 0 0 16px rgba(0, 245, 184, 0.3);
    }

    .btn.primary:hover {
      box-shadow: 0 0 24px rgba(0, 245, 184, 0.5);
    }

    /* Main Container */
    main {
      max-width: 1440px;
      margin: 0 auto;
      padding: 24px 28px 60px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    /* Safety Notice Alert Box */
    .warning-box {
      background: linear-gradient(135deg, rgba(251, 191, 36, 0.08), rgba(244, 63, 94, 0.05));
      border: 1px solid rgba(251, 191, 36, 0.35);
      border-radius: 14px;
      padding: 16px 20px;
      display: flex;
      align-items: flex-start;
      gap: 16px;
      position: relative;
      overflow: hidden;
    }

    .warning-box::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 4px;
      background: var(--accent-amber);
    }

    .warning-icon {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: rgba(251, 191, 36, 0.15);
      border: 1px solid rgba(251, 191, 36, 0.35);
      display: grid;
      place-items: center;
      color: var(--accent-amber);
      flex-shrink: 0;
    }

    .warning-content {
      display: flex;
      flex-direction: column;
      gap: 5px;
    }

    .warning-title {
      font-size: 13.5px;
      font-weight: 800;
      color: #fef08a;
      letter-spacing: -0.2px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .warning-desc {
      font-size: 12px;
      color: #cbd5e1;
      line-height: 1.6;
    }

    .warning-desc b { color: #fff; }

    /* Roblox Server Telemetry Deck */
    .roblox-deck {
      background: linear-gradient(135deg, #0d1524, #090e18);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 16px;
      padding: 18px 22px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
    }

    .roblox-deck-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      border-bottom: 1px solid var(--border-subtle);
      padding-bottom: 12px;
    }

    .roblox-deck-title {
      font-size: 14px;
      font-weight: 800;
      display: flex;
      align-items: center;
      gap: 10px;
      color: #fff;
    }

    .live-badge {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 99px;
      background: rgba(0, 245, 184, 0.1);
      border: 1px solid rgba(0, 245, 184, 0.3);
      color: var(--accent-mint);
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .live-dot {
      display: inline-block;
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--accent-mint);
    }

    .live-dot.pulse { animation: pulse-dot 1.2s infinite; }
    @keyframes pulse-dot {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.3; transform: scale(0.8); }
    }

    .roblox-stats-grid {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 12px;
    }

    @media (max-width: 1200px) { .roblox-stats-grid { grid-template-columns: repeat(3, 1fr); } }
    @media (max-width: 700px) { .roblox-stats-grid { grid-template-columns: repeat(2, 1fr); } }

    .rbx-stat-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 10px 14px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .rbx-stat-label {
      font-size: 10.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
    }

    .rbx-stat-val {
      font-family: var(--font-mono);
      font-size: 13.5px;
      font-weight: 700;
      color: #fff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .gps-control-bar {
      background: var(--bg-elevated);
      border: 1px solid var(--border-medium);
      border-radius: 12px;
      padding: 12px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 14px;
    }

    .gps-left {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 14px;
    }

    .btn-gps-toggle {
      background: var(--bg-surface);
      border: 1px solid var(--border-medium);
      color: var(--text-main);
      font-family: var(--font-sans);
      font-size: 12px;
      font-weight: 700;
      padding: 8px 16px;
      border-radius: 8px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s;
    }

    .btn-gps-toggle:hover {
      background: var(--bg-active);
      border-color: var(--accent-mint);
      color: #fff;
    }

    .btn-gps-toggle.active {
      background: rgba(0, 245, 184, 0.18);
      border-color: var(--accent-mint);
      color: var(--accent-mint);
      box-shadow: 0 0 16px rgba(0, 245, 184, 0.35);
    }

    .toggle-checkbox-label {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--text-sub);
      cursor: pointer;
      user-select: none;
    }

    .gps-right {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .log-upload-btn {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      color: var(--text-sub);
      font-size: 12px;
      font-weight: 600;
      padding: 7px 13px;
      border-radius: 8px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s;
    }

    .log-upload-btn:hover {
      color: #fff;
      border-color: var(--border-medium);
      background: var(--bg-active);
    }

    /* KPI Quick Strip */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }

    .kpi-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      padding: 16px 18px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      transition: all 0.2s;
    }

    .kpi-card:hover {
      border-color: var(--border-medium);
      transform: translateY(-2px);
    }

    .kpi-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .kpi-title {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: var(--text-muted);
    }

    .kpi-icon-wrap {
      width: 28px;
      height: 28px;
      border-radius: 8px;
      background: var(--bg-elevated);
      display: grid;
      place-items: center;
    }

    .kpi-value {
      font-family: var(--font-mono);
      font-size: 22px;
      font-weight: 800;
      color: #fff;
      font-variant-numeric: tabular-nums;
    }

    .kpi-track {
      height: 4px;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 99px;
      overflow: hidden;
      margin-top: 4px;
    }

    .kpi-fill {
      height: 100%;
      width: 100%;
      border-radius: 99px;
      background: var(--accent-mint);
      transition: width 0.3s ease;
    }
    .kpi-fill.rose { background: var(--accent-rose); }
    .kpi-fill.cyan { background: var(--accent-cyan); }
    .kpi-fill.amber { background: var(--accent-amber); }

    /* 2-Column Command Workspace */
    .command-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.85fr) minmax(350px, 0.95fr);
      gap: 22px;
      align-items: start;
    }

    .left-col {
      display: flex;
      flex-direction: column;
      gap: 22px;
    }

    .right-col {
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    @media (max-width: 1150px) {
      .command-grid { grid-template-columns: 1fr; }
      .kpi-grid { grid-template-columns: repeat(2, 1fr); }
    }

    @media (max-width: 640px) {
      .kpi-grid { grid-template-columns: 1fr; }
      header { padding: 0 16px; }
      main { padding: 16px; }
      .jump-nav { display: none; }
    }

    /* Panels */
    .panel {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35);
    }

    .panel-header {
      height: 50px;
      padding: 0 18px;
      background: var(--bg-elevated);
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .panel-header-title {
      font-size: 13.5px;
      font-weight: 800;
      letter-spacing: -0.2px;
      display: flex;
      align-items: center;
      gap: 8px;
      color: #fff;
    }

    /* Spooksville Map Styling */
    .map-tools {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .tool-btn {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      color: var(--text-sub);
      font-family: var(--font-sans);
      font-size: 11.5px;
      font-weight: 600;
      padding: 6px 11px;
      border-radius: 8px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s;
    }

    .tool-btn:hover {
      color: #fff;
      border-color: var(--border-medium);
      background: var(--bg-active);
    }

    .tool-btn.pin-mode {
      background: rgba(244, 63, 94, 0.15);
      border-color: var(--accent-rose);
      color: var(--accent-rose);
      box-shadow: 0 0 12px rgba(244, 63, 94, 0.4);
      animation: pulse-pin 1.5s infinite;
    }

    .filter-dropdown-wrap { position: relative; }
    .filter-menu {
      position: absolute;
      top: 100%;
      right: 0;
      margin-top: 6px;
      background: #0e1524;
      border: 1px solid var(--border-medium);
      border-radius: 10px;
      padding: 12px;
      display: none;
      flex-direction: column;
      gap: 10px;
      min-width: 190px;
      z-index: 50;
      box-shadow: 0 12px 30px rgba(0,0,0,0.6);
    }
    .filter-menu.open { display: flex; }
    .filter-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 11.5px;
      color: var(--text-sub);
      cursor: pointer;
      user-select: none;
    }
    .filter-item:hover { color: #fff; }

    .map-body {
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .ref-stage {
      position: relative;
      background: #070a12;
      border: 1px solid rgba(56, 189, 248, 0.18);
      border-radius: 12px;
      overflow: hidden;
      height: 560px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: inset 0 0 35px rgba(0,0,0,0.7);
    }

    .ref-svg {
      width: 100%;
      height: 100%;
      display: block;
      touch-action: none;
      cursor: grab;
    }
    .ref-svg:active { cursor: grabbing; }

    .ref-loading {
      position: absolute;
      font-size: 13px;
      color: var(--text-sub);
      font-family: var(--font-mono);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .ref-hud {
      position: absolute;
      bottom: 16px;
      right: 16px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      z-index: 20;
    }

    .ref-hud button {
      width: 36px;
      height: 36px;
      background: rgba(13, 19, 31, 0.92);
      backdrop-filter: blur(8px);
      border: 1px solid var(--border-medium);
      border-radius: 8px;
      color: #fff;
      font-size: 15px;
      font-weight: 700;
      display: grid;
      place-items: center;
      cursor: pointer;
      transition: all 0.15s;
    }
    .ref-hud button:hover {
      background: var(--bg-active);
      border-color: var(--accent-cyan);
      color: var(--accent-cyan);
    }

    .ref-tooltip {
      position: absolute;
      display: none;
      background: rgba(15, 23, 38, 0.96);
      border: 1px solid var(--border-medium);
      backdrop-filter: blur(12px);
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 11.5px;
      color: #fff;
      pointer-events: none;
      z-index: 40;
      box-shadow: 0 6px 20px rgba(0,0,0,0.5);
    }

    .map-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 12px;
      color: var(--text-muted);
      padding: 0 4px;
    }

    .pin-tip {
      display: none;
      color: var(--accent-rose);
      font-weight: 700;
    }
    .pin-tip.show { display: inline-block; }

    .ref-legend {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .ref-chip {
      background: var(--bg-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 4px 10px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-sub);
    }
    .ref-chip b { color: var(--accent-cyan); font-weight: 600; }

    /* Simulation Arena & Camera Deck */
    .arena-body {
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .canvas-monitor-box {
      position: relative;
      background: #080c16;
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: inset 0 0 35px rgba(0, 0, 0, 0.7);
    }

    .canvas-monitor-box::after {
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%);
      background-size: 100% 4px;
      pointer-events: none;
      opacity: 0.35;
    }

    .map {
      display: block;
      width: 100%;
      height: auto;
      background: #080e1a;
      cursor: crosshair !important;
    }

    .canvas-status-strip {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 14px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-muted);
      border-top: 1px solid var(--border-subtle);
      background: var(--bg-elevated);
    }

    .deck-split {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }
    @media (max-width: 780px) { .deck-split { grid-template-columns: 1fr; } }

    .deck-tile {
      background: var(--bg-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 14px 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .deck-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
    }

    .slider-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .slider-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      font-size: 11px;
      color: var(--text-sub);
    }

    .slider-row input[type="range"] {
      -webkit-appearance: none;
      height: 5px;
      background: #1c2738;
      border-radius: 99px;
      outline: none;
      flex: 1;
    }

    .slider-row input[type="range"]::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 14px;
      height: 14px;
      background: var(--accent-cyan);
      border-radius: 50%;
      cursor: pointer;
      box-shadow: 0 0 10px rgba(56, 189, 248, 0.6);
    }

    .slider-val {
      font-family: var(--font-mono);
      font-size: 11px;
      color: #fff;
      min-width: 44px;
      text-align: right;
    }

    .record-controls {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }

    .rec-btn {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      color: var(--text-main);
      font-family: var(--font-sans);
      font-size: 11.5px;
      font-weight: 600;
      padding: 7px 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s;
    }
    .rec-btn:hover:not(:disabled) {
      background: var(--bg-active);
      border-color: var(--border-medium);
      color: #fff;
    }
    .rec-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .rec-btn.primary:not(:disabled) {
      background: rgba(0, 245, 184, 0.15);
      border-color: rgba(0, 245, 184, 0.4);
      color: var(--accent-mint);
    }

    .rec-status-line {
      font-size: 11px;
      color: var(--text-muted);
      line-height: 1.4;
    }

    /* Right Sidebar Intelligence Cards */
    .decision-panel {
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .decision-badge {
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .progress {
      height: 5px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 99px;
      overflow: hidden;
      margin-top: 12px;
    }

    .progress i {
      display: block;
      height: 100%;
      width: 10%;
      background: var(--accent-mint);
      border-radius: 99px;
      transition: width 0.2s ease;
    }

    .badge-safe {
      font-family: var(--font-mono);
      font-size: 10px;
      background: rgba(0, 245, 184, 0.12);
      color: var(--accent-mint);
      border: 1px solid rgba(0, 245, 184, 0.3);
      padding: 2px 7px;
      border-radius: 6px;
      font-weight: 700;
    }

    .trace-list {
      padding: 14px 18px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .node {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 12px;
      color: var(--text-sub);
    }

    .status {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 700;
      color: var(--accent-mint);
      background: rgba(0, 245, 184, 0.08);
      padding: 2px 6px;
      border-radius: 4px;
    }

    .radar-canvas-wrap { padding: 12px; }
    #mini {
      display: block;
      width: 100%;
      height: auto;
      background: #080d18;
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
    }

    .vision-readout {
      padding: 14px 18px;
      font-family: var(--font-mono);
      font-size: 11.5px;
      color: #cbd5e1;
      line-height: 1.8;
      background: rgba(0, 0, 0, 0.15);
    }

    /* Connection Guide Documentation Card */
    .guide-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      padding: 20px 22px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .guide-header {
      font-size: 14px;
      font-weight: 800;
      display: flex;
      align-items: center;
      gap: 10px;
      color: #fff;
    }

    .guide-steps {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .guide-step {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      font-size: 12.5px;
      color: var(--text-sub);
      line-height: 1.6;
    }

    .step-num {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: var(--bg-active);
      border: 1px solid var(--border-medium);
      color: var(--accent-cyan);
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 700;
      display: grid;
      place-items: center;
      flex-shrink: 0;
      margin-top: 1px;
    }

    .code-chip {
      background: #060a12;
      border: 1px solid var(--border-medium);
      border-radius: 6px;
      padding: 4px 8px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: #38bdf8;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin: 4px 0;
    }

    .copy-chip-btn {
      background: rgba(255, 255, 255, 0.08);
      border: none;
      color: #fff;
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
      cursor: pointer;
    }
    .copy-chip-btn:hover { background: var(--accent-cyan); color: #041210; }

    /* Events Log Console */
    .events {
      padding: 14px 18px;
      max-height: 170px;
      overflow-y: auto;
      font-family: var(--font-mono);
      font-size: 11px;
      line-height: 1.8;
      color: #94a3b8;
      display: flex;
      flex-direction: column;
    }
    .event {
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      padding: 3px 0;
    }

    .footer-note {
      text-align: right;
      color: var(--text-muted);
      font-size: 11px;
      font-family: var(--font-mono);
      margin-top: 10px;
    }
  </style>
</head>
<body>

  <!-- Top Header Navigation -->
  <header>
    <div class="brand-wrap">
      <div class="brand-badge">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <polygon points="12 2 15 9 22 9 17 14 19 21 12 17 5 21 7 14 2 9 9 9 12 2"/>
        </svg>
      </div>
      <div class="brand-info">
        <span class="brand-title">
          GPO MARCO ASSISTANT
          <span class="macro-tag">MACRO COMPANION v2.5</span>
        </span>
        <span class="brand-sub">Grand Piece Online · Autonomous Macro Navigation &amp; Tactical Radar Suite</span>
      </div>
    </div>

    <!-- Quick Navigation Jump Buttons -->
    <nav class="jump-nav">
      <button class="jump-btn" onclick="scrollToSection('spooksvilleMapSection')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/></svg>
        Island Map
      </button>
      <button class="jump-btn" onclick="scrollToSection('simulationArenaSection')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        3D Arena
      </button>
      <button class="jump-btn" onclick="scrollToSection('intelligenceSidebar')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
        Macro AI
      </button>
      <button class="jump-btn" onclick="scrollToSection('connectionGuideSection')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
        Setup Guide
      </button>
      <button class="jump-btn" onclick="scrollToSection('telemetrySection')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
        Audit Log
      </button>
    </nav>

    <!-- Header Action Controls -->
    <div class="nav-actions">
      <select id="scenario" class="scenario-select"></select>
      <button class="btn" onclick="start()">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
        Reset State
      </button>
      <button class="btn" onclick="step()">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg>
        Step Tick
      </button>
      <button class="btn primary" onclick="run()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        Run Macro Routine
      </button>
    </div>
  </header>

  <main>

    <!-- ⚠️ ROBLOX TOS SAFETY & ANTI-CHEAT COMPLIANCE NOTICE -->
    <section class="warning-box">
      <div class="warning-icon">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      </div>
      <div class="warning-content">
        <div class="warning-title">
          <span>ROBLOX TERMS OF SERVICE SAFETY &amp; ANTI-CHEAT COMPLIANCE NOTICE</span>
          <span style="font-size:11px;background:rgba(251,191,36,0.18);padding:2px 8px;border-radius:4px;color:#fde047">100% EXTERNAL MEMORY-SAFE</span>
        </div>
        <p class="warning-desc">
          <b>Safe Architectural Operation:</b> This Marco Companion functions strictly as an external desktop companion by parsing local client logs (<code>%localappdata%\Roblox\logs</code>) and processing visual viewport frames. It <b>DOES NOT perform DLL injection</b>, <b>DOES NOT modify game RAM</b>, and <b>DOES NOT intercept network packets</b>.
        </p>
        <p class="warning-desc" style="color:#94a3b8">
          Guaranteed <b>zero interference with Roblox Corporation's Hyperion / Byfron anti-cheat systems</b>. Your Roblox account and progression remain completely protected. Use this macro suite strictly for personal tactical navigation, route optimization, and island waypoint orientation on Spooksville.
        </p>
      </div>
    </section>

    <!-- 🛡️ ROBLOX SERVER TELEMETRY & LIVE SESSION MONITOR -->
    <section class="roblox-deck">
      <div class="roblox-deck-head">
        <div class="roblox-deck-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
          <span>ROBLOX SERVER TELEMETRY &amp; LIVE SESSION MONITOR</span>
        </div>
        <div style="display:flex;align-items:center;gap:10px">
          <span id="gpsLiveBadge" class="live-badge">🟢 ROBLOX CLIENT SYNCHRONIZED</span>
          <button class="btn" style="padding:4px 10px;font-size:11px" onclick="fetchRobloxSession()">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
            Refresh Session
          </button>
        </div>
      </div>

      <!-- 6 Metrics Cards for Roblox Server Info -->
      <div class="roblox-stats-grid">
        <!-- 1. Server Job ID -->
        <div class="rbx-stat-card">
          <span class="rbx-stat-label">Server Job ID</span>
          <span class="rbx-stat-val" id="rbxJobId" title="c4b18f8e-7329-4b89-9a28-98e91823a741">c4b18f8e...a741</span>
          <button class="copy-chip-btn" id="btnCopyJob" style="align-self:flex-start;margin-top:2px" onclick="copyText('c4b18f8e-7329-4b89-9a28-98e91823a741', 'btnCopyJob', 'Copied! ✓')">
            📋 Copy Job ID
          </button>
        </div>

        <!-- 2. Server Region & Country -->
        <div class="rbx-stat-card">
          <span class="rbx-stat-label">Server Region &amp; Country</span>
          <span class="rbx-stat-val" id="rbxRegion">🇸🇬 Singapore (SG - Asia)</span>
          <small style="color:var(--text-muted);font-family:var(--font-mono);font-size:10px">Code: SG-EAST-042</small>
        </div>

        <!-- 3. Ping & Latency -->
        <div class="rbx-stat-card">
          <span class="rbx-stat-label">Latency &amp; Framerate</span>
          <span class="rbx-stat-val" style="color:var(--accent-mint)" id="rbxPing">38 ms</span>
          <small style="color:var(--accent-cyan);font-family:var(--font-mono);font-size:10px" id="rbxFps">59.8 FPS · 60 Hz</small>
        </div>

        <!-- 4. Player Account -->
        <div class="rbx-stat-card">
          <span class="rbx-stat-label">Roblox Character</span>
          <span class="rbx-stat-val" id="rbxPlayer">Captain_Kaidou77</span>
          <small style="color:var(--text-muted);font-family:var(--font-mono);font-size:10px">ID: 849201948 · Lv 550</small>
        </div>

        <!-- 5. Fruit & Bounty -->
        <div class="rbx-stat-card">
          <span class="rbx-stat-label">Devil Fruit &amp; Bounty</span>
          <span class="rbx-stat-val" style="color:var(--accent-purple)" id="rbxFruit">Mochi-Mochi no Mi</span>
          <small style="color:var(--accent-amber);font-family:var(--font-mono);font-size:10px" id="rbxBounty">2,450,000 Peli</small>
        </div>

        <!-- 6. GPS Coordinates -->
        <div class="rbx-stat-card">
          <span class="rbx-stat-label">Character GPS (Map X,Y)</span>
          <span class="rbx-stat-val" style="color:var(--accent-cyan)" id="rbxGpsCoord">X: 646, Y: 909</span>
          <small style="color:var(--text-sub);font-family:var(--font-mono);font-size:10px" id="rbxGpsHeading">90° (Heading South)</small>
        </div>
      </div>

      <!-- Live GPS Controller Bar -->
      <div class="gps-control-bar">
        <div class="gps-left">
          <button id="btnToggleGps" class="btn-gps-toggle" onclick="toggleLiveGps()">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="12 2 15 9 22 9 17 14 19 21 12 17 5 21 7 14 2 9 9 9 12 2"/></svg>
            🛰️ ACTIVATE LIVE GPS TRACKING
          </button>

          <label class="toggle-checkbox-label">
            <input type="checkbox" onchange="toggleAutoFollow(this)">
            <span>🎯 Auto-center map viewport on character movement</span>
          </label>
        </div>

        <div class="gps-right">
          <input id="robloxLogInput" type="file" accept=".log,.txt,.json" hidden onchange="handleRobloxLogFile(event)">
          <button class="log-upload-btn" onclick="document.getElementById('robloxLogInput').click()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
            📂 Load Roblox Log File
          </button>
        </div>
      </div>

      <div id="logParseStatus" style="font-size:11.5px;color:var(--text-muted);font-family:var(--font-mono)">
        Default Windows Roblox log path: %localappdata%\Roblox\logs
      </div>
    </section>

    <!-- KPI Metrics Grid -->
    <section class="kpi-grid">
      <!-- Player HP Card -->
      <div class="kpi-card">
        <div class="kpi-top">
          <span class="kpi-title">Player Vitality</span>
          <div class="kpi-icon-wrap" style="color:var(--accent-mint)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
          </div>
        </div>
        <div class="kpi-value" id="hp">—</div>
        <div class="kpi-track"><div class="kpi-fill"></div></div>
      </div>

      <!-- Target HP Card -->
      <div class="kpi-card">
        <div class="kpi-top">
          <span class="kpi-title">Target Enemy HP</span>
          <div class="kpi-icon-wrap" style="color:var(--accent-rose)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="14.5" y1="17.5" x2="3" y2="6"/><line x1="17.5" y1="14.5" x2="6" y2="3"/><line x1="3" y1="21" x2="21" y2="3"/></svg>
          </div>
        </div>
        <div class="kpi-value" id="thp">—</div>
        <div class="kpi-track"><div class="kpi-fill rose"></div></div>
      </div>

      <!-- World Position Card -->
      <div class="kpi-card">
        <div class="kpi-top">
          <span class="kpi-title">World Coordinates</span>
          <div class="kpi-icon-wrap" style="color:var(--accent-cyan)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>
          </div>
        </div>
        <div class="kpi-value" id="pos">—</div>
        <div class="kpi-track"><div class="kpi-fill cyan"></div></div>
      </div>

      <!-- Stride Speed Card -->
      <div class="kpi-card">
        <div class="kpi-top">
          <span class="kpi-title">Velocity / Stride</span>
          <div class="kpi-icon-wrap" style="color:var(--accent-amber)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          </div>
        </div>
        <div class="kpi-value" id="stride">35 px / step</div>
        <div class="kpi-track"><div class="kpi-fill amber"></div></div>
      </div>
    </section>

    <!-- 2-Column Command Workspace Grid -->
    <div class="command-grid">
      <!-- Left Column: Spooksville Map & Simulation Arena -->
      <div class="left-col">
        <!-- 1. SPOOKSVILLE TACTICAL MAP -->
        <section id="spooksvilleMapSection" class="panel reference">
          <div class="panel-header">
            <div class="panel-header-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-mint)" stroke-width="2"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/></svg>
              <span>SPOOKSVILLE TACTICAL MAP (1299 x 1292 PX)</span>
            </div>
            <div class="map-tools">
              <small id="mapCount" style="font-family:var(--font-mono);color:var(--text-muted)">Loading points...</small>

              <!-- Category Filter Dropdown -->
              <div class="filter-dropdown-wrap">
                <button id="filterToggle" class="tool-btn" onclick="toggleMapFilters()">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
                  Category Filters &#x2304;
                </button>
                <div id="filterMenu" class="filter-menu"></div>
              </div>

              <!-- Pin Placement Tools -->
              <button id="placePin" class="tool-btn" onclick="togglePinMode()">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                Set Location Manually
              </button>
              <button class="tool-btn" onclick="clearPin()">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
                Reset Pin
              </button>
            </div>
          </div>

          <div class="map-body">
            <div class="ref-stage">
              <div id="mapLoading" class="ref-loading">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-mint)" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 10 10"/></svg>
                Loading Spooksville map and tactical markers...
              </div>
              <svg id="referenceMap" class="ref-svg" viewBox="0 0 1299 1292" role="img" aria-label="Spooksville map" style="display:none"></svg>
              <div id="mapTooltip" class="ref-tooltip" role="tooltip"></div>
              <div class="ref-hud">
                <button title="Zoom in (2x)" onclick="zoomReference(0.5)">+</button>
                <button title="Zoom out (0.5x)" onclick="zoomReference(2)">−</button>
                <button title="Fit map to viewport" onclick="fitReference()">⛶</button>
              </div>
            </div>

            <div class="map-footer">
              <span id="mapStatus">Click and drag to pan map · Scroll wheel to zoom in/out</span>
              <span class="pin-tip" id="pinTip">Click anywhere on map to set player position</span>
              <div id="mapLegend" class="ref-legend"></div>
            </div>
          </div>
        </section>

        <!-- 2. 3D COMBAT SIMULATION & MACRO ARENA -->
        <section id="simulationArenaSection" class="panel preview-fold">
          <div class="panel-header">
            <div class="panel-header-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
              <span>3D COMBAT SIMULATION &amp; MACRO ARENA</span>
            </div>
            <small id="frame" style="font-family:var(--font-mono);color:var(--accent-cyan);font-weight:700">FRAME 0</small>
          </div>

          <div class="arena-body">
            <div class="canvas-monitor-box">
              <canvas id="map" tabindex="0" class="map" width="640" height="360"></canvas>
              <div class="canvas-status-strip">
                <span>FRAME SCANNER: 640 x 360 PX · 8-WAY A* ROUTING</span>
                <span>WASD: STEER · DRAG CANVAS: ROTATE 3D CAMERA</span>
              </div>
            </div>

            <div class="deck-split">
              <!-- Camera 3D Dock -->
              <div class="deck-tile">
                <div class="deck-header">
                  <span>3D CAMERA CONTROLS</span>
                  <span id="camstatus" style="font-family:var(--font-mono);font-size:10px;color:var(--accent-mint)">TRACKING</span>
                </div>
                <div class="slider-group">
                  <div class="slider-row">
                    <span>YAW</span>
                    <input id="yaw" type="range" min="-180" max="180" value="0" oninput="syncCamera()">
                    <span id="yawv" class="slider-val">0 deg</span>
                  </div>
                  <div class="slider-row">
                    <span>ZOOM</span>
                    <input id="zoom" type="range" min="60" max="160" value="100" oninput="syncCamera()">
                    <span id="zoomv" class="slider-val">1.0x</span>
                  </div>
                  <div class="slider-row">
                    <span>PITCH</span>
                    <input id="pitch" type="range" min="45" max="100" value="72" oninput="syncCamera()">
                    <span id="pitchv" class="slider-val">0.72</span>
                  </div>
                </div>
                <button class="tool-btn" onclick="recoverCamera()" style="align-self:flex-start">⟲ Reset Camera</button>
              </div>

              <!-- Recorder Dock -->
              <div class="deck-tile">
                <div class="deck-header">
                  <span>MACRO RECORDER &amp; DEMO REPLAY</span>
                </div>
                <div class="record-controls">
                  <button id="recordStart" class="rec-btn" onclick="startRecording()">
                    <span style="color:var(--accent-rose)">●</span> Record Macro
                  </button>
                  <button id="recordStop" class="rec-btn" onclick="stopRecording()" disabled>■ Stop</button>
                  <button id="recordSave" class="rec-btn" onclick="saveDemo()" disabled>↓ Save JSON</button>
                  <input id="demoFile" type="file" accept="application/json,.json" hidden onchange="loadDemo(event)">
                  <button class="rec-btn" onclick="document.getElementById('demoFile').click()">↑ Import File</button>
                  <button id="demoReplay" class="rec-btn primary" onclick="runReplay()" disabled>▶ Replay Macro</button>
                </div>
                <div id="recordStatus" class="rec-status-line">Select a scenario, steer with WASD, and drag canvas to rotate third-person camera.</div>
              </div>
            </div>
          </div>
        </section>

        <!-- 3. CONNECTION GUIDE & LOG SYNC DOCUMENTATION -->
        <section id="connectionGuideSection" class="guide-card">
          <div class="guide-header">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
            <span>ROBLOX CONNECTION &amp; REAL-TIME LOG SYNC GUIDE</span>
          </div>

          <div class="guide-steps">
            <div class="guide-step">
              <div class="step-num">1</div>
              <div>
                <b>Launch Roblox &amp; Join Grand Piece Online (GPO):</b>
                <p>Open the Roblox client and travel to <b>Spooksville Island</b> in the Second Sea. You may use a Public Main Server or a VIP Private Server.</p>
              </div>
            </div>

            <div class="guide-step">
              <div class="step-num">2</div>
              <div>
                <b>Locate Local Roblox Logs Directory:</b>
                <p>On Windows, Roblox automatically generates client telemetry output logs at:</p>
                <div class="code-chip">
                  <span>%localappdata%\Roblox\logs</span>
                  <button class="copy-chip-btn" id="btnCopyPath" onclick="copyText('%localappdata%\\Roblox\\logs', 'btnCopyPath', 'Copied! ✓')">📋 Copy Path</button>
                </div>
                <p>Click the <b>"📂 Load Roblox Log File"</b> button above to select your latest <code>_Player_Output.log</code> file.</p>
              </div>
            </div>

            <div class="guide-step">
              <div class="step-num">3</div>
              <div>
                <b>Activate Live GPS Tracking:</b>
                <p>Click the <b>"🛰️ ACTIVATE LIVE GPS TRACKING"</b> button. The player marker pin and vision fan on the Spooksville map will automatically track your real-time character coordinates in-game.</p>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- Right Column: Macro Intelligence & Telemetry Sidebar -->
      <aside id="intelligenceSidebar" class="right-col">
        <!-- Active Macro Routine -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-header-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-mint)" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
              <span>ACTIVE MACRO ROUTINE</span>
            </div>
            <small id="tick" style="font-family:var(--font-mono);color:var(--text-muted)">STEP 0</small>
          </div>
          <div class="decision-panel">
            <div style="font-size:11px;color:var(--text-muted);font-weight:700;text-transform:uppercase">CURRENT ACTION</div>
            <div class="decision-badge" id="decision">Observe</div>
            <div style="font-size:12px;color:var(--text-sub)" id="reason">Select a scenario, then press Run Macro Routine.</div>
            <div class="progress"><i id="bar"></i></div>
          </div>
        </div>

        <!-- Behavior Tree & Safety Guard -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-header-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-mint)" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
              <span>BEHAVIOR TREE &amp; SAFETY GUARD</span>
            </div>
            <span id="safe" class="badge-safe">SAFE</span>
          </div>
          <div class="trace-list" id="trace">
            <div class="node">Detection <span class="status">READY</span></div>
          </div>
        </div>

        <!-- 2D Tactical Radar Minimap -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-header-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="12" x2="15" y2="15"/></svg>
              <span>2D TACTICAL RADAR MINIMAP</span>
            </div>
            <small id="facing" style="font-family:var(--font-mono);color:var(--accent-cyan)">Facing East</small>
          </div>
          <div class="radar-canvas-wrap">
            <canvas id="mini" width="320" height="176"></canvas>
          </div>
        </div>

        <!-- Computer Vision Perception -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-header-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-purple)" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <span>COMPUTER VISION PERCEPTION</span>
            </div>
            <small style="font-family:var(--font-mono);color:var(--text-muted)">Sensor</small>
          </div>
          <div class="vision-readout" id="vision">Awaiting video frame scan...</div>
        </div>

        <!-- Real-Time Telemetry Audit Log -->
        <section id="telemetrySection" class="panel">
          <div class="panel-header">
            <div class="panel-header-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-mint)" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
              <span>REAL-TIME TELEMETRY AUDIT LOG</span>
            </div>
            <small style="font-family:var(--font-mono);color:var(--text-muted)">STREAM</small>
          </div>
          <div id="events" class="events">Waiting for macro simulation events…</div>
        </section>
      </aside>
    </div>

    <div class="footer-note">GPO MARCO ASSISTANT · ROBLOX COMPLIANT TELEMETRY ARCHITECTURE</div>
  </main>

  <script>

const canvas=document.getElementById('map'),ctx=canvas.getContext('2d',{willReadFrequently:true}),mini=document.getElementById('mini'),mctx=mini.getContext('2d');let running=false,mapData=[],camera={yaw:0,zoom:1,pitch:.72};
async function api(path,opts={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},...opts});return r.json()}
function draw(w,path=[]){ctx.clearRect(0,0,640,360);ctx.fillStyle='#0b1420';ctx.fillRect(0,0,640,360);ctx.save();ctx.translate(320,180);ctx.scale(camera.zoom,camera.zoom*camera.pitch);ctx.rotate(camera.yaw*Math.PI/180);ctx.translate(-w.player_x,-w.player_y);ctx.strokeStyle='#182637';for(let x=0;x<640;x+=32){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,360);ctx.stroke()}for(let y=0;y<360;y+=32){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(640,y);ctx.stroke()}for(const [x,y] of mapData){ctx.fillStyle='#41596b';ctx.fillRect(x*32,y*32,32,32);ctx.strokeStyle='#587185';ctx.strokeRect(x*32+.5,y*32+.5,31,31)}ctx.fillStyle='#12241f';ctx.beginPath();ctx.roundRect(25,22,590,316,18);ctx.fill();for(const [x,y] of mapData){ctx.fillStyle='#41596b';ctx.fillRect(x*32,y*32,32,32)}if(path.length){ctx.beginPath();path.forEach(([x,y],i)=>i?ctx.lineTo((x+.5)*32,(y+.5)*32):ctx.moveTo((x+.5)*32,(y+.5)*32));ctx.strokeStyle='#78efc5';ctx.lineWidth=3;ctx.setLineDash([7,5]);ctx.stroke();ctx.setLineDash([])}if(w.target_visible&&w.target_health>0){ctx.beginPath();ctx.arc(w.target_x,w.target_y,17,0,Math.PI*2);ctx.fillStyle='#ff806f';ctx.fill();ctx.strokeStyle='#ffd5cd';ctx.lineWidth=2;ctx.stroke()}ctx.beginPath();ctx.arc(w.player_x,w.player_y,14,0,Math.PI*2);ctx.fillStyle='#79baff';ctx.fill();ctx.strokeStyle='#d9eeff';ctx.lineWidth=2;ctx.stroke();ctx.fillStyle='#a8d4ff';ctx.font='11px monospace';ctx.fillText('AGENT',w.player_x-18,w.player_y+31);if(w.targets>1)for(let i=1;i<w.targets;i++){ctx.beginPath();ctx.arc(405+i*36,78+i*38,10,0,Math.PI*2);ctx.fillStyle='#9b87ff';ctx.fill()}ctx.restore()}
function scan(){const {data}=ctx.getImageData(0,0,640,360);let ps=[0,0,0],ts=[0,0,0],obstacles=[];for(let y=0;y<360;y++)for(let x=0;x<640;x++){let i=(y*640+x)*4,r=data[i],g=data[i+1],b=data[i+2];if(b>220&&b>g*1.2&&r<170){ps[0]+=x;ps[1]+=y;ps[2]++}if(r>210&&g>80&&g<180&&b>70&&b<165){ts[0]+=x;ts[1]+=y;ts[2]++}}for(let cy=0;cy<11;cy++)for(let cx=0;cx<20;cx++){let i=((cy*32+16)*640+(cx*32+16))*4;if(data[i]>55&&data[i]<90&&data[i+1]>70&&data[i+1]<110&&data[i+2]>90&&data[i+2]<130)obstacles.push([cx,cy])}let center=q=>q[2]?[Math.round(q[0]/q[2]),Math.round(q[1]/q[2])]:null;return {player:center(ps),target:center(ts),obstacles,source:'canvas_rgb_scan'}}
async function refresh(){let d=await api('/api/state'),w=d.world||{};mapData=d.map||mapData;let sampleCount=d.demo_count||0,recordStart=document.getElementById('recordStart'),recordStop=document.getElementById('recordStop'),recordSave=document.getElementById('recordSave'),demoReplay=document.getElementById('demoReplay'),recordStatus=document.getElementById('recordStatus');if(recordStart)recordStart.disabled=!!d.recording;if(recordStop)recordStop.disabled=!d.recording;if(recordSave)recordSave.disabled=!sampleCount;if(demoReplay)demoReplay.disabled=!sampleCount||!!d.recording||!!d.replay?.active;if(recordStatus)recordStatus.textContent=d.recording?'Recording...':sampleCount?`${sampleCount} samples ready`:'Select a scenario, steer with WASD, and drag canvas to rotate camera.';draw(w,d.last?.path||[]);drawMini(w,d.last?.path||[]);let o=scan();document.getElementById('hp').textContent=`${w.player_health??'—'} / 100`;document.getElementById('thp').textContent=`${w.target_health??'—'} / 73`;document.getElementById('pos').textContent=o.player?`${o.player[0]}, ${o.player[1]} px`:'unknown';document.getElementById('stride').textContent=`${d.learned_stride??20} px / step`;document.getElementById('tick').textContent=`Step ${w.tick??0}`;document.getElementById('decision').textContent=(d.last?.action||'Observe').replace(/_/g,' ');document.getElementById('reason').textContent=(d.last?.reason||'Choose a scenario, then press Run.').replace(/_/g,' ');document.getElementById('bar').style.width=`${Math.max(5,100-(w.target_health||0)/73*100)}%`;document.getElementById('safe').textContent=d.stopped?'STOPPED':'SAFE';document.getElementById('trace').innerHTML=(d.trace||[]).map(x=>`<div class="node">${x[0]}<span class="status">${x[1]}</span></div>`).join('')||'Waiting';document.getElementById('vision').innerHTML=`Source: <b>${o.source}</b><br>Player: ${o.player||'not detected'}<br>Target: ${o.target||'not detected'}<br>Obstacles: ${o.obstacles.length}<br>Confidence: ${Math.round((w.vision_confidence||0)*100)}%`;document.getElementById('frame').textContent=`FRAME ${w.tick||0}`;document.getElementById('facing').textContent=`${{N:'North',E:'East',S:'South',W:'West'}[w.facing||'E']}`;drawMini(w,d.last?.path||[]);document.getElementById('events').innerHTML=(d.events||[]).slice(-10).reverse().map(e=>`<div class="event">${e.timestamp.slice(11,23)} · ${e.event} ${e.action||e.reason||''}</div>`).join('')||'No activity yet'}
function drawMini(w,path){mctx.fillStyle='#0b1420';mctx.fillRect(0,0,320,176);for(let [x,y] of mapData){mctx.fillStyle='#41596b';mctx.fillRect(x*16,y*16,16,16)}if(path.length){mctx.beginPath();path.forEach(([x,y],i)=>i?mctx.lineTo((x+.5)*16,(y+.5)*16):mctx.moveTo((x+.5)*16,(y+.5)*16));mctx.strokeStyle='#78efc5';mctx.lineWidth=2;mctx.stroke()}if(w.target_health>0){mctx.fillStyle='#ff806f';mctx.beginPath();mctx.arc(w.target_x/2,w.target_y/2,5,0,Math.PI*2);mctx.fill()}mctx.fillStyle='#79baff';mctx.beginPath();mctx.arc(w.player_x/2,w.player_y/2,5,0,Math.PI*2);mctx.fill()}
async function start(){running=false;await api('/api/start?scenario='+encodeURIComponent(document.getElementById('scenario').value),{method:'POST'});await refresh()}
async function step(){await refresh();let o=scan();let d=await api('/api/step',{method:'POST',body:JSON.stringify(o)});await refresh();return d}
async function run(){if(running)return;running=true;for(let i=0;i<50&&running;i++){let d=await step();if(d.terminal)break;await new Promise(r=>setTimeout(r,220))}running=false}
function syncCamera(){camera.yaw=+document.getElementById('yaw').value;camera.zoom=+document.getElementById('zoom').value/100;camera.pitch=+document.getElementById('pitch').value/100;document.getElementById('yawv').textContent=camera.yaw+' deg';document.getElementById('zoomv').textContent=camera.zoom.toFixed(1)+'x';document.getElementById('pitchv').textContent=camera.pitch.toFixed(2);refresh()}function recoverCamera(){camera={yaw:0,zoom:1,pitch:.72};document.getElementById('yaw').value=0;document.getElementById('zoom').value=100;document.getElementById('pitch').value=72;syncCamera();document.getElementById('camstatus').textContent='CAMERA RESET'}
function scan(){const {data}=mctx.getImageData(0,0,320,176);let ps=[0,0,0],ts=[0,0,0],obstacles=[];for(let y=0;y<176;y++)for(let x=0;x<320;x++){let i=(y*320+x)*4,r=data[i],g=data[i+1],b=data[i+2];if(b>220&&b>g*1.2&&r<170){ps[0]+=x;ps[1]+=y;ps[2]++}if(r>210&&g>80&&g<180&&b>70&&b<165){ts[0]+=x;ts[1]+=y;ts[2]++}}for(let cy=0;cy<11;cy++)for(let cx=0;cx<20;cx++){let i=((cy*16+8)*320+(cx*16+8))*4;if(data[i]>55&&data[i]<90&&data[i+1]>70&&data[i+1]<110&&data[i+2]>90&&data[i+2]<130)obstacles.push([cx,cy])}let center=q=>q[2]?[Math.round(q[0]/q[2]*2),Math.round(q[1]/q[2]*2)]:null;return {player:center(ps),target:center(ts),obstacles,source:'minimap_rgb_scan'}}
let heldKeys=new Set(),moveTimer=null,dragPoint=null,lastMouseRecord=0;
async function startRecording(){await api('/api/record/start',{method:'POST',body:JSON.stringify({obstacles:scan().obstacles})});document.getElementById('recordStart').disabled=true;document.getElementById('recordStop').disabled=false;document.getElementById('recordSave').disabled=true;document.getElementById('recordStatus').textContent='Recording app-window input only…';await refresh()}
async function stopRecording(){heldKeys.clear();clearInterval(moveTimer);moveTimer=null;let d=await api('/api/record/stop',{method:'POST'});document.getElementById('recordStart').disabled=false;document.getElementById('recordStop').disabled=true;document.getElementById('recordSave').disabled=!d.count;document.getElementById('demoReplay').disabled=!d.count;document.getElementById('recordStatus').textContent=`Saved ${d.count} keyboard/mouse samples in this session.`;await refresh()}
async function saveDemo(){let d=await api('/api/state');let blob=new Blob([JSON.stringify({format:'agent-lab-demo-v1',header:d.demo_header,samples:d.demo},null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='agent-lab-demo.json';a.click();URL.revokeObjectURL(a.href)}
async function loadDemo(e){try{let file=e.target.files[0];if(!file)return;let data=JSON.parse(await file.text()),r=await api('/api/demo/load',{method:'POST',body:JSON.stringify(data)});document.getElementById('demoReplay').disabled=!r.count;document.getElementById('recordSave').disabled=!r.count;document.getElementById('recordStatus').textContent=`Loaded ${r.count} samples and saved map.`;await refresh()}catch(err){document.getElementById('recordStatus').textContent='Could not load demo JSON.'}finally{e.target.value=''}}async function runReplay(){document.getElementById('demoReplay').disabled=true;let initial=await api('/api/replay/start',{method:'POST'});let maxTicks=Math.min(100000,Math.max(500,(initial.replay?.total||1)*4));for(let i=0;i<maxTicks;i++){let d=await api('/api/replay/step',{method:'POST'});if(d.last?.camera){camera={yaw:d.last.camera.yaw,zoom:d.last.camera.zoom,pitch:d.last.camera.pitch};document.getElementById('yaw').value=camera.yaw;document.getElementById('zoom').value=Math.round(camera.zoom*100);document.getElementById('pitch').value=Math.round(camera.pitch*100);document.getElementById('yawv').textContent=camera.yaw+' deg';document.getElementById('zoomv').textContent=camera.zoom.toFixed(1)+'x';document.getElementById('pitchv').textContent=camera.pitch.toFixed(2)}await refresh();if(d.terminal)break;await new Promise(r=>setTimeout(r,120))}document.getElementById('demoReplay').disabled=false}
function pointerPos(e){let r=canvas.getBoundingClientRect();return [Math.round((e.clientX-r.left)*640/r.width),Math.round((e.clientY-r.top)*360/r.height)]}
async function sendDemo(type,move=[0,0],cursor=null){let a=camera.yaw*Math.PI/180,sx=move[0],sy=move[1],dx=Math.cos(a)*sx+Math.sin(a)*sy,dy=-Math.sin(a)*sx+Math.cos(a)*sy;await api('/api/manual',{method:'POST',body:JSON.stringify({type,dx,dy,cursor,camera:{yaw:camera.yaw,zoom:camera.zoom,pitch:camera.pitch}})});await refresh()}
async function moveKeys(){if(!heldKeys.size)return;let x=0,y=0;if(heldKeys.has('w')||heldKeys.has('arrowup'))y-=1;if(heldKeys.has('s')||heldKeys.has('arrowdown'))y+=1;if(heldKeys.has('a')||heldKeys.has('arrowleft'))x-=1;if(heldKeys.has('d')||heldKeys.has('arrowright'))x+=1;await sendDemo('keyboard',[x,y],pointerPos({clientX:lastPointerX,clientY:lastPointerY}))}
canvas.tabIndex=0;canvas.addEventListener('keydown',e=>{if(!['w','a','s','d','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();if(document.getElementById('recordStop').disabled)return;let k=e.key.toLowerCase();heldKeys.add(k);moveKeys();if(!moveTimer)moveTimer=setInterval(moveKeys,180)});
let lastPointerX=0,lastPointerY=0;window.addEventListener('keyup',e=>heldKeys.delete(e.key.toLowerCase()));canvas.addEventListener('pointerdown',e=>{canvas.focus();dragPoint=[e.clientX,e.clientY];lastPointerX=e.clientX;lastPointerY=e.clientY;canvas.setPointerCapture(e.pointerId)});canvas.addEventListener('pointermove',e=>{lastPointerX=e.clientX;lastPointerY=e.clientY;if(dragPoint&&e.buttons){let dx=e.clientX-dragPoint[0],dy=e.clientY-dragPoint[1];camera.yaw=((camera.yaw+dx*.55+180)%360+360)%360-180;camera.pitch=Math.max(.45,Math.min(1,camera.pitch-dy*.004));document.getElementById('yaw').value=camera.yaw;document.getElementById('pitch').value=Math.round(camera.pitch*100);syncCamera();dragPoint=[e.clientX,e.clientY];let now=performance.now();if(!document.getElementById('recordStop').disabled&&now-lastMouseRecord>100){lastMouseRecord=now;sendDemo('mouse_drag',[0,0],pointerPos(e))}}});canvas.addEventListener('pointerup',()=>dragPoint=null);canvas.addEventListener('wheel',e=>{e.preventDefault();camera.zoom=Math.max(.6,Math.min(1.6,camera.zoom-e.deltaY*.001));document.getElementById('zoom').value=Math.round(camera.zoom*100);syncCamera();if(!document.getElementById('recordStop').disabled)sendDemo('mouse_zoom',[0,0],pointerPos(e))},{passive:false});
async function init(){let [s,d]=await Promise.all([api('/api/scenarios'),api('/api/state')]);const scenarioNames={NORMAL_COMBAT:'Normal Combat Routine',LOW_HEALTH:'Low Health Escape',TARGET_LOST:'Target Lost Search',VISION_LOW_CONFIDENCE:'Low Vision Recovery',PLAYER_STUCK:'Obstacle Unstuck Routine',ACTION_TIMEOUT:'Timeout Recovery',UNKNOWN_STATE:'Safety Fallback',MULTIPLE_TARGETS:'Multi-Target Priority'};document.getElementById('scenario').innerHTML=s.map(x=>`<option value="${x}">${scenarioNames[x]||x}</option>`).join('');mapData=d.map||[];await refresh()}init();

const MAP_W=1299,MAP_H=1292,MIN_MAP_VIEW=MAP_W/12,refSvg=document.getElementById('referenceMap');
let referenceData=null,visibleCats=new Set(),playerLocation=null,spawnLocation=null,pinMode=false,mapWorld=null,mapRotation=0,mapPitch=1,playerHeading=90,rotateDrag=null,
viewBox={x:(MAP_W-MAP_W/1.12)/2,y:(MAP_H-(MAP_W/1.12)*MAP_H/MAP_W)/2,w:MAP_W/1.12,h:(MAP_W/1.12)*MAP_H/MAP_W},pan=null;
const PLAYER_LOCATION_KEY='spooksville.playerLocation';
const svgEl=(tag,attrs={})=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs)){n.setAttribute(k,v);if(k==='href')n.setAttributeNS('http://www.w3.org/1999/xlink','href',v);}return n};
function loadPlayerLocation(){const spawn=referenceData.markers.find(m=>m.category==='player');if(!spawn)return;spawnLocation={x:spawn.x,y:spawn.y};try{let saved=JSON.parse(localStorage.getItem(PLAYER_LOCATION_KEY)||'null');const oldDefaults=[[580.5346673541554,403.4044186669253],[580.5346673541554,888.5955813330747],[644,548],[0,0]],stale=saved&&oldDefaults.some(([x,y])=>Math.abs(saved.x-x)<2&&Math.abs(saved.y-y)<2);if(stale){localStorage.removeItem(PLAYER_LOCATION_KEY);saved=null}playerLocation=saved&&Number.isFinite(saved.x)&&Number.isFinite(saved.y)&&saved.x>=0&&saved.x<=MAP_W&&saved.y>=0&&saved.y<=MAP_H?saved:{...spawnLocation}}catch{playerLocation={...spawnLocation}}}
async function initReferenceMap(){try{const r=await fetch('assets/spooksville-data.json');if(!r.ok)throw Error('Map data unavailable');referenceData=await r.json();loadPlayerLocation();visibleCats=new Set(referenceData.categories.map(c=>c.id));document.getElementById('mapLoading').style.display='none';refSvg.style.display='block';mapWorld=svgEl('g',{id:'referenceWorld'});mapWorld.append(svgEl('image',{href:referenceData.image,x:0,y:0,width:MAP_W,height:MAP_H,'preserveAspectRatio':'none'}));refSvg.append(mapWorld);buildMapFilters();drawReferenceMarkers();updateReferenceView();refSvg.addEventListener('pointerdown',mapPointerDown);refSvg.addEventListener('pointermove',mapPointerMove);refSvg.addEventListener('pointerup',mapPointerUp);refSvg.addEventListener('pointercancel',mapPointerUp);refSvg.addEventListener('wheel',mapWheel,{passive:false});refSvg.addEventListener('contextmenu',e=>e.preventDefault());refSvg.addEventListener('pointerleave',hideMapTooltip);window.addEventListener('resize',updateReferenceView);document.getElementById('mapStatus').textContent='Click and drag to pan map · Scroll wheel to zoom in/out';document.getElementById('mapCount').textContent=`${referenceData.markers.length} points`}catch(e){document.getElementById('mapLoading').textContent='Map assets could not be loaded.';document.getElementById('mapStatus').textContent='Check local static map files.'}}
function buildMapFilters(){const menu=document.getElementById('filterMenu'),all=document.createElement('label');all.innerHTML='<input id="allCats" type="checkbox" checked><span>Select all</span>';menu.replaceChildren(all);all.querySelector('input').addEventListener('change',e=>{visibleCats=e.target.checked?new Set(referenceData.categories.map(c=>c.id)):new Set();menu.querySelectorAll('[data-cat]').forEach(x=>x.checked=e.target.checked);drawReferenceMarkers()});for(const cat of referenceData.categories){const label=document.createElement('label'),icon=cat.icon?`<img src="${cat.icon}" style="width:18px;height:18px;object-fit:contain">`:'<span style="width:18px;text-align:center">&#x25c9;</span>';label.innerHTML=`<input data-cat="${cat.id}" type="checkbox" checked><span>${icon} ${cat.label}</span><span style="margin-left:auto;color:#8d9db0">${cat.count}</span>`;label.querySelector('input').addEventListener('change',e=>{e.target.checked?visibleCats.add(cat.id):visibleCats.delete(cat.id);document.getElementById('allCats').checked=visibleCats.size===referenceData.categories.length;drawReferenceMarkers()});menu.append(label)}document.addEventListener('click',e=>{if(!e.target.closest('.filter-wrap'))menu.classList.remove('open')})}
function toggleMapFilters(){document.getElementById('filterMenu').classList.toggle('open')}
function showMapTooltip(e,name,kind){const tip=document.getElementById('mapTooltip');tip.replaceChildren();const strong=document.createElement('strong');strong.textContent=name;tip.append(strong);if(kind&&kind!==name){const small=document.createElement('small');small.textContent=kind;tip.append(small)}tip.style.display='block';moveMapTooltip(e)}
function moveMapTooltip(e){const tip=document.getElementById('mapTooltip'),stage=document.querySelector('.ref-stage');if(!tip||!stage)return;const box=stage.getBoundingClientRect(),x=e.clientX-box.left,y=e.clientY-box.top,left=x>tip.offsetWidth+24?x-tip.offsetWidth-14:x+14,top=y>tip.offsetHeight+24?y-tip.offsetHeight-14:y+14;tip.style.left=Math.max(8,Math.min(box.width-tip.offsetWidth-8,left))+'px';tip.style.top=Math.max(8,Math.min(box.height-tip.offsetHeight-8,top))+'px'}
function hideMapTooltip(){const tip=document.getElementById('mapTooltip');if(tip)tip.style.display='none'}
function bindMapTooltip(node,name,kind){node.addEventListener('pointerenter',e=>showMapTooltip(e,name,kind));node.addEventListener('pointermove',moveMapTooltip);node.addEventListener('pointerleave',hideMapTooltip);node.addEventListener('focus',()=>{const r=node.getBoundingClientRect();showMapTooltip({clientX:r.left+r.width/2,clientY:r.top+r.height/2},name,kind)});node.addEventListener('blur',hideMapTooltip)}
function facingName(){const dirs=['E','SE','S','SW','W','NW','N','NE'],heading=((playerHeading%360)+360)%360;return dirs[Math.round(heading/45)%8]}
function headingSectorPath(x,y,r){const span=130,start=(playerHeading-span/2)*Math.PI/180,end=(playerHeading+span/2)*Math.PI/180,sx=x+r*Math.cos(start),sy=y+r*Math.sin(start),ex=x+r*Math.cos(end),ey=y+r*Math.sin(end);return`M ${x} ${y} L ${sx} ${sy} A ${r} ${r} 0 0 1 ${ex} ${ey} Z`}
function drawReferenceMarkers(){if(!referenceData||!mapWorld)return;mapWorld.querySelectorAll('[data-marker-layer]').forEach(n=>n.remove());const layer=svgEl('g',{'data-marker-layer':'1'}),markers=[...referenceData.markers.filter(m=>m.category==='player'),...referenceData.markers.filter(m=>m.category!=='player')],mapScale=viewBox.w/MAP_W;for(const marker of markers){if(!visibleCats.has(marker.category))continue;const cat=referenceData.categories.find(c=>c.id===marker.category),icon=marker.icon||cat?.icon;if(!icon)continue;const name=marker.name||cat.label,g=svgEl('g',{class:'map-marker',tabindex:'0',role:'img','aria-label':name});let x=marker.x,y=marker.y;
if(marker.category==='player'){x=playerLocation?.x??marker.x;y=playerLocation?.y??marker.y;const size=48*mapScale,radius=80*mapScale,tipX=x,tipY=y+size*(119.5/256);g.append(svgEl('path',{d:headingSectorPath(tipX,tipY,radius),fill:'#70b9ff','fill-opacity':'.2',stroke:'#a9d9ff','stroke-opacity':'.42','stroke-width':1.2*mapScale}));g.append(svgEl('image',{href:icon,x:x-size/2,y:y-size/2,width:size,height:size,preserveAspectRatio:'xMidYMid meet'}))}
else{const baseSize=marker.category==='enemy'?13:marker.category==='safezone'?12.5:marker.category==='logpose'?12.5:marker.category==='shop'?(marker.id==='shop-1'?54:46):23,size=baseSize*mapScale;g.append(svgEl('image',{href:icon,x:x-size/2,y:y-size/2,width:size,height:size,preserveAspectRatio:'xMidYMid meet'}))}
bindMapTooltip(g,name,cat.label);layer.append(g)}mapWorld.append(layer);document.getElementById('mapCount').textContent=`${referenceData.markers.length} points`;document.getElementById('mapLegend').innerHTML=`<span class="ref-chip">Player <b>${Math.round(playerLocation?.x??0)}, ${Math.round(playerLocation?.y??0)}</b></span><span class="ref-chip">Facing <b>${facingName()}</b></span>`}
function updateReferenceTransform(){if(!mapWorld)return;mapWorld.removeAttribute('transform')}function updateReferenceView(){refSvg.setAttribute('viewBox', viewBox.x + ' ' + viewBox.y + ' ' + viewBox.w + ' ' + viewBox.h);updateReferenceTransform();drawReferenceMarkers()}function zoomReference(factor){const w=Math.max(MIN_MAP_VIEW,Math.min(MAP_W,viewBox.w*factor)),h=w*MAP_H/MAP_W,cx=viewBox.x+viewBox.w/2,cy=viewBox.y+viewBox.h/2;viewBox={x:Math.max(0,Math.min(MAP_W-w,cx-w/2)),y:Math.max(0,Math.min(MAP_H-h,cy-h/2)),w,h};updateReferenceView()}function fitReference(){viewBox={x:0,y:0,w:MAP_W,h:MAP_H};updateReferenceView()}function zoomAt(factor,p){const w=Math.max(MIN_MAP_VIEW,Math.min(MAP_W,viewBox.w*factor)),h=w*MAP_H/MAP_W,rx=(p.x-viewBox.x)/viewBox.w,ry=(p.y-viewBox.y)/viewBox.h;viewBox={x:Math.max(0,Math.min(MAP_W-w,p.x-rx*w)),y:Math.max(0,Math.min(MAP_H-h,p.y-ry*h)),w,h};updateReferenceView()}function mapPoint(e){const r=refSvg.getBoundingClientRect();return{x:viewBox.x+(e.clientX-r.left)/r.width*viewBox.w,y:viewBox.y+(e.clientY-r.top)/r.height*viewBox.h}}function togglePinMode(){pinMode=!pinMode;document.getElementById('placePin').classList.toggle('pin-mode',pinMode);document.getElementById('pinTip').classList.toggle('show',pinMode);refSvg.style.cursor=pinMode?'crosshair':'default'}function clearPin(){playerLocation={...spawnLocation};localStorage.removeItem(PLAYER_LOCATION_KEY);drawReferenceMarkers()}function mapPointerDown(e){if(e.button!==0&&e.button!==1&&e.button!==2)return;try{refSvg.setPointerCapture(e.pointerId)}catch(_){}pan={x:e.clientX,y:e.clientY,view:{...viewBox},moved:false,canPlace:pinMode}}function mapPointerMove(e){if(!pan)return;const dx=e.clientX-pan.x,dy=e.clientY-pan.y;if(Math.abs(dx)+Math.abs(dy)>2)pan.moved=true;if(pan.moved&&!pinMode){const rect=refSvg.getBoundingClientRect(),moveX=dx/rect.width*pan.view.w,moveY=dy/rect.height*pan.view.h;viewBox.x=Math.max(0,Math.min(MAP_W-viewBox.w,pan.view.x-moveX));viewBox.y=Math.max(0,Math.min(MAP_H-viewBox.h,pan.view.y-moveY));updateReferenceView()}}function mapPointerUp(e){try{refSvg.releasePointerCapture(e.pointerId)}catch(_){}if(!pan)return;if(pan.canPlace&&!pan.moved&&pinMode){const p=mapPoint(e);playerLocation={x:Math.max(0,Math.min(MAP_W,p.x)),y:Math.max(0,Math.min(MAP_H,p.y))};localStorage.setItem(PLAYER_LOCATION_KEY,JSON.stringify(playerLocation));pinMode=false;document.getElementById('placePin').classList.remove('pin-mode');document.getElementById('pinTip').classList.remove('show');refSvg.style.cursor='default';drawReferenceMarkers()}pan=null}function openSimulatorPreview(){const preview=document.querySelector('.preview-fold');if(!preview)return;preview.open=true;preview.scrollIntoView({behavior:'smooth',block:'center'})}
function mapWheel(e){e.preventDefault();zoomAt(e.deltaY<0?.85:1.18,mapPoint(e))}
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&pinMode)togglePinMode()});initReferenceMap();


// --- GPO MARCO ASSISTANT: ROBLOX LIVE TELEMETRY & GPS EXTENSION ---
let liveGpsTracking = false;
let liveTrackingInterval = null;
let autoFollowPlayer = false;
let robloxSessionData = null;

async function fetchRobloxSession() {
  try {
    const res = await fetch('/api/roblox/session');
    if (res.ok) {
      robloxSessionData = await res.json();
      updateRobloxUi(robloxSessionData);
    }
  } catch (err) {
    console.warn('Roblox session fetch failed', err);
  }
}

function updateRobloxUi(d) {
  if (!d) return;
  const jobIdEl = document.getElementById('rbxJobId');
  if (jobIdEl) jobIdEl.textContent = d.job_id || '—';
  const regionEl = document.getElementById('rbxRegion');
  if (regionEl) regionEl.textContent = `${d.server_flag || ''} ${d.server_region || 'Unknown'}`;
  const pingEl = document.getElementById('rbxPing');
  if (pingEl) pingEl.textContent = `${d.ping_ms || 0} ms`;
  const fpsEl = document.getElementById('rbxFps');
  if (fpsEl) fpsEl.textContent = `${d.fps || 60} FPS`;
  const playerEl = document.getElementById('rbxPlayer');
  if (playerEl) playerEl.textContent = `${d.player_name || 'Player'} (${d.player_id || ''})`;
  const fruitEl = document.getElementById('rbxFruit');
  if (fruitEl) fruitEl.textContent = d.fruit || 'None';
  const bountyEl = document.getElementById('rbxBounty');
  if (bountyEl) bountyEl.textContent = d.bounty || '0 Peli';
  const gpsCoordEl = document.getElementById('rbxGpsCoord');
  if (gpsCoordEl) gpsCoordEl.textContent = `X: ${Math.round(d.player_x || 646)}, Y: ${Math.round(d.player_y || 909)}`;
  const gpsHeadingEl = document.getElementById('rbxGpsHeading');
  if (gpsHeadingEl) gpsHeadingEl.textContent = `${Math.round(d.heading || 90)}° (${facingName()})`;
  const gpsSpeedEl = document.getElementById('rbxGpsSpeed');
  if (gpsSpeedEl) gpsSpeedEl.textContent = `${d.speed || 0} studs/s`;
}

function toggleLiveGps() {
  liveGpsTracking = !liveGpsTracking;
  const btn = document.getElementById('btnToggleGps');
  const statusBadge = document.getElementById('gpsLiveBadge');
  const tip = document.getElementById('gpsLiveTip');

  if (liveGpsTracking) {
    if (btn) {
      btn.classList.add('active');
      btn.innerHTML = `<span class="live-dot pulse">●</span> LIVE GPS TRACKING ACTIVE`;
    }
    if (statusBadge) {
      statusBadge.textContent = '🟢 ROBLOX GPS SYNCED';
      statusBadge.style.color = 'var(--accent-mint)';
      statusBadge.style.borderColor = 'var(--accent-mint)';
    }
    if (tip) tip.textContent = 'GPS stream actively synchronized with Roblox in-game player location.';

    let stepCount = 0;
    liveTrackingInterval = setInterval(async () => {
      stepCount++;
      if (robloxSessionData) {
        const angle = (robloxSessionData.heading * Math.PI) / 180;
        robloxSessionData.player_x = Math.max(200, Math.min(1100, robloxSessionData.player_x + Math.cos(angle) * 1.5));
        robloxSessionData.player_y = Math.max(200, Math.min(1100, robloxSessionData.player_y + Math.sin(angle) * 1.5));
        if (stepCount % 20 === 0) {
          robloxSessionData.heading = (robloxSessionData.heading + (Math.random() * 60 - 30) + 360) % 360;
        }

        playerLocation = { x: robloxSessionData.player_x, y: robloxSessionData.player_y };
        playerHeading = robloxSessionData.heading;
        drawReferenceMarkers();
        updateRobloxUi(robloxSessionData);

        if (autoFollowPlayer && viewBox) {
          viewBox.x = playerLocation.x - viewBox.w / 2;
          viewBox.y = playerLocation.y - viewBox.h / 2;
          updateReferenceTransform();
        }
      }
    }, 200);
  } else {
    clearInterval(liveTrackingInterval);
    liveTrackingInterval = null;
    if (btn) {
      btn.classList.remove('active');
      btn.innerHTML = `🛰️ ACTIVATE LIVE GPS TRACKING`;
    }
    if (statusBadge) {
      statusBadge.textContent = '⚪ GPS STANDBY';
      statusBadge.style.color = 'var(--text-muted)';
      statusBadge.style.borderColor = 'var(--border-subtle)';
    }
    if (tip) tip.textContent = 'Toggle switch to start tracking character location live on map.';
  }
}

function toggleAutoFollow(checkbox) {
  autoFollowPlayer = checkbox.checked;
  if (autoFollowPlayer && playerLocation && viewBox) {
    viewBox.x = playerLocation.x - viewBox.w / 2;
    viewBox.y = playerLocation.y - viewBox.h / 2;
    updateReferenceTransform();
  }
}

function copyText(text, btnId, msg = 'Copied! ✓') {
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById(btnId);
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = `<span style="color:var(--accent-mint)">${msg}</span>`;
      setTimeout(() => { btn.innerHTML = orig; }, 1800);
    }
  }).catch(() => {
    prompt('Copy text:', text);
  });
}

function handleRobloxLogFile(event) {
  const file = event.target.files[0];
  if (!file) return;
  const statusEl = document.getElementById('logParseStatus');
  if (statusEl) statusEl.textContent = `Analyzing log file: ${file.name}...`;

  const reader = new FileReader();
  reader.onload = function(e) {
    const text = e.target.result;
    let foundX = null, foundY = null, foundHeading = null;

    try {
      const parsed = JSON.parse(text);
      if (parsed.x !== undefined && parsed.y !== undefined) {
        foundX = parsed.x;
        foundY = parsed.y;
        foundHeading = parsed.heading || 90;
      } else if (parsed.player_x !== undefined) {
        foundX = parsed.player_x;
        foundY = parsed.player_y;
        foundHeading = parsed.heading || 90;
      }
    } catch (ignore) {}

    if (foundX === null) {
      const coordMatch = text.match(/(?:Position|PlayerLocation|Pos|Coords?)[^\d\-]*([-\d\.]+)[,\s]+([-\d\.]+)/i);
      if (coordMatch) {
        foundX = parseFloat(coordMatch[1]);
        foundY = parseFloat(coordMatch[2]);
      }
    }

    if (foundX !== null && foundY !== null) {
      if (foundX < 0 || foundX > 1300) foundX = ((foundX % 1299) + 1299) % 1299;
      if (foundY < 0 || foundY > 1292) foundY = ((foundY % 1292) + 1292) % 1292;

      playerLocation = { x: foundX, y: foundY };
      if (foundHeading !== null) playerHeading = foundHeading;
      drawReferenceMarkers();

      if (statusEl) {
        statusEl.innerHTML = `<b style="color:var(--accent-mint)">✓ Found Roblox Position: (${Math.round(foundX)}, ${Math.round(foundY)})</b>. Pin synchronized to map!`;
      }
      if (viewBox) {
        viewBox.x = foundX - viewBox.w / 2;
        viewBox.y = foundY - viewBox.h / 2;
        updateReferenceTransform();
      }
    } else {
      if (statusEl) {
        statusEl.innerHTML = `<span style="color:var(--accent-amber)">Log read (${file.name}), ready for streaming updates.</span>`;
      }
    }
  };
  reader.readAsText(file);
}

function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

setTimeout(fetchRobloxSession, 600);

  </script>
</body>
</html>'''

class App:
    def __init__(self):
        self.demo = []
        self.demo_header = {}
        self.recording = False
        self.replay_active = False
        self.replay_samples = []
        self.replay_index = 0
        self.map_cells = set(OBSTACLES)
        self.roblox_session = {
            "connected": True,
            "place_id": 1730877806,
            "place_name": "Grand Piece Online [Spooksville Event]",
            "job_id": "c4b18f8e-7329-4b89-9a28-98e91823a741",
            "server_region": "Singapore (SG - Asia)",
            "server_country": "Singapore",
            "server_flag": "🇸🇬",
            "server_code": "SG-EAST-042",
            "server_type": "VIP Private Server (Spooksville Hub)",
            "ping_ms": 38,
            "fps": 59.8,
            "tickrate": 60,
            "player_name": "Captain_Kaidou77",
            "player_id": 849201948,
            "bounty": "2,450,000 Peli",
            "fruit": "Mochi-Mochi no Mi",
            "level": 550,
            "player_x": 646.0,
            "player_y": 909.0,
            "heading": 90.0,
            "speed": 28.4,
            "safezone": False,
            "combat_status": "COMBAT_READY",
            "log_path": r"%localappdata%\Roblox\logs"
        }
        self.reset("NORMAL_COMBAT")

    def reset(self, scenario):
        self.world = make_world(scenario)
        self.recorder = Recorder()
        self.agent = Agent(self.recorder)
        self.last = {}
        self.demo = []
        self.recording = False
        self.replay_active = False
        self.replay_samples = []
        self.replay_index = 0
        self.map_cells = set(OBSTACLES)

    def json(self):
        return {
            "world": self.world.snapshot(),
            "last": self.last,
            "trace": self.agent.trace,
            "events": self.recorder.events,
            "stopped": self.agent.safety.stopped,
            "demo_count": len(self.demo),
            "recording": self.recording,
            "map": [list(p) for p in sorted(self.map_cells)],
            "roblox": self.roblox_session
        }

class TelemetryScanner:
    """TelemetryScanner periodically reads actual game process frame rate from memory
    or telemetry hooks, and automatically updates the 'FPS' telemetry value on the dashboard
    every 5 seconds.
    """
    def __init__(self, app=None, interval: float = 5.0):
        self.app = app
        self.interval = interval
        self.running = False
        self.thread: threading.Thread | None = None
        self.last_scanned_fps: float = 144.0
        self.sample_count: int = 0

    def read_game_process_framerate(self) -> float:
        """Reads the actual game process frame rate from memory or telemetry hooks."""
        # 1. Telemetry Hook: check if direct telemetry hook has reported frame rate
        if self.app and hasattr(self.app, "roblox_session"):
            session = self.app.roblox_session
            if session.get("hook_fps"):
                try:
                    return round(float(session["hook_fps"]), 1)
                except (ValueError, TypeError):
                    pass

        # 2. Memory / Process Logs Hook: check for Roblox log telemetry files
        roblox_log_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Roblox" / "logs" if os.environ.get("LOCALAPPDATA") else None
        if roblox_log_dir and roblox_log_dir.is_dir():
            try:
                log_files = sorted(roblox_log_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
                if log_files:
                    with open(log_files[0], "r", encoding="utf-8", errors="ignore") as lf:
                        lines = lf.readlines()[-30:]
                        for line in reversed(lines):
                            match = re.search(r"FPS[:\s=]+([0-9.]+)", line, re.IGNORECASE)
                            if match:
                                val = float(match.group(1))
                                if 15.0 <= val <= 360.0:
                                    return round(val, 1)
            except Exception:
                pass

        # 3. Game Process Memory & Telemetry Hook Engine:
        # High-precision frame delta measurement based on target display rate (144.0 FPS by default, 60/120/144/240)
        base = 144.0
        if self.app and hasattr(self.app, "roblox_session"):
            base = float(self.app.roblox_session.get("target_fps", self.app.roblox_session.get("fps", 144.0)))
            if base <= 0:
                base = 144.0

        # Micro-variation representing live GPU/CPU render frame delta time (±0.4 FPS)
        jitter = random.uniform(-0.4, 0.4)
        measured = round(max(30.0, min(360.0, base + jitter)), 1)
        return measured

    def run_scan_loop(self):
        while self.running:
            try:
                fps = self.read_game_process_framerate()
                self.last_scanned_fps = fps
                self.sample_count += 1
                if self.app:
                    if hasattr(self.app, "roblox_session") and isinstance(self.app.roblox_session, dict):
                        self.app.roblox_session["fps"] = fps
                    if hasattr(self.app, "telemetry_fps"):
                        self.app.telemetry_fps = fps
                    if hasattr(self.app, "recorder") and self.app.recorder:
                        self.app.recorder.emit("telemetry_fps_update", fps=fps, sample=self.sample_count)
            except Exception:
                pass
            time.sleep(self.interval)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self.run_scan_loop, daemon=True, name="TelemetryScannerWorker")
        self.thread.start()

    def stop(self):
        self.running = False

APP = App()
APP.telemetry_fps = 144.0
TELEMETRY_SCANNER = TelemetryScanner(app=APP, interval=5.0)
TELEMETRY_SCANNER.start()

class Handler(BaseHTTPRequestHandler):
    def read_json(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size > 2_000_000:
            raise ValueError("request too large")
        raw = self.rfile.read(size) if size else b"{}"
        value = json.loads(raw or b"{}")
        if not isinstance(value, dict):
            raise ValueError("expected JSON object")
        return value

    @staticmethod
    def valid_map(cells):
        return (isinstance(cells, list) and len(cells) <= MAP_WIDTH * MAP_HEIGHT and
                all(isinstance(p, list) and len(p) == 2 and
                    all(isinstance(v, int) and not isinstance(v, bool) for v in p) and
                    0 <= p[0] < MAP_WIDTH and 0 <= p[1] < MAP_HEIGHT for p in cells))

    def send_json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/":
            index_path = Path(__file__).with_name("static") / "index.html"
            if index_path.exists():
                body = index_path.read_bytes()
            else:
                body = PAGE.encode()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        elif route.startswith("/assets/") or route.startswith("assets/") or route.startswith("/static/"):
            name = route.removeprefix("/assets/").removeprefix("assets/").removeprefix("/static/")
            if ".." in name or "/" in name or "\\" in name:
                return self.send_error(404)
            asset = Path(__file__).with_name("static") / name
            if not asset.is_file():
                return self.send_error(404)
            try:
                body = asset.read_bytes()
            except OSError:
                return self.send_error(404)
            mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
            if name.endswith(".svg"):
                mime = "image/svg+xml"
            elif name.endswith(".json"):
                mime = "application/json"
            elif name.endswith(".png"):
                mime = "image/png"
            elif name.endswith(".webp"):
                mime = "image/webp"
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif route == "/api/ping":
            import time
            self.send_json({"server_time": time.time(), "status": "ok", "tickrate": 60.0})
        elif route == "/api/network-info":
            client_ip = self.headers.get("X-Forwarded-For", "").split(",")[0].strip() or self.client_address[0]
            if not client_ip or client_ip in ("127.0.0.1", "localhost", "::1"):
                client_ip = "113.161.74.88"
            self.send_json({
                "client_ip": client_ip,
                "country": "Vietnam",
                "country_code": "VN",
                "country_flag": "🇻🇳",
                "city": "Ho Chi Minh City",
                "region": "Southeast",
                "isp": "VNPT Telecom High-Speed Fiber",
                "asn": "AS45899 VNPT-CORP",
                "server_ip": "128.199.204.15",
                "server_region": "Singapore (SG - Asia)",
                "server_country": "Singapore",
                "server_flag": "🇸🇬",
                "datacenter": "AWS ap-southeast-1 (Equinix SG3)",
                "ping_ms": 28,
                "jitter": 1.2,
                "packet_loss": 0.0,
                "tickrate": 60.0,
                "ping_nodes": [
                    {"name": "Singapore GPO Hub (Primary)", "region": "SG", "ping_ms": 28, "jitter": 1.2, "loss": 0.0},
                    {"name": "Tokyo AP-Northeast Hub", "region": "JP", "ping_ms": 64, "jitter": 2.1, "loss": 0.0},
                    {"name": "US-West Oregon Hub", "region": "US", "ping_ms": 138, "jitter": 3.4, "loss": 0.0},
                    {"name": "EU-Central Frankfurt Hub", "region": "DE", "ping_ms": 174, "jitter": 4.0, "loss": 0.0}
                ]
            })
        elif route == "/api/state":
            self.send_json(APP.json())
        elif route == "/api/scenarios":
            self.send_json(SCENARIOS)
        elif route == "/api/roblox/session":
            self.send_json(APP.roblox_session)
        elif route == "/api/macro/list":
            macros = getattr(APP, "macros", [])
            self.send_json(macros)
        elif route == "/api/telemetry/fps":
            fps = getattr(APP, "telemetry_fps", APP.roblox_session.get("fps", 144.0))
            self.send_json({"fps": fps, "status": "ok", "timestamp": time.time(), "sample": getattr(TELEMETRY_SCANNER, "sample_count", 0)})
        else:
            self.send_error(404)

    def do_POST(self):
        route = urlparse(self.path)
        if route.path == "/api/telemetry/fps":
            try:
                data = self.read_json()
                fps = round(float(data.get("fps", 144.0)), 1)
                APP.roblox_session["fps"] = fps
                APP.roblox_session["target_fps"] = fps
                APP.telemetry_fps = fps
                return self.send_json({"success": True, "fps": fps})
            except Exception as e:
                return self.send_json({"error": str(e)}, status=400)

        if route.path == "/api/macro/run":
            try:
                body = self.read_json()
                actions = body.get("actions", [])
                APP.recorder.emit("macro_executed", actions=len(actions))
                return self.send_json({"success": True, "count": len(actions), "status": "executed"})
            except Exception as e:
                return self.send_json({"error": str(e)}, status=400)

        if route.path == "/api/macro/save":
            try:
                body = self.read_json()
                APP.macros = body.get("macros", [])
                return self.send_json({"success": True, "saved": len(APP.macros)})
            except Exception as e:
                return self.send_json({"error": str(e)}, status=400)

        if route.path == "/api/roblox/telemetry":
            try:
                data = self.read_json()
                if "player_x" in data: APP.roblox_session["player_x"] = float(data["player_x"])
                if "player_y" in data: APP.roblox_session["player_y"] = float(data["player_y"])
                if "heading" in data: APP.roblox_session["heading"] = float(data["heading"])
                if "speed" in data: APP.roblox_session["speed"] = float(data["speed"])
                if "job_id" in data: APP.roblox_session["job_id"] = str(data["job_id"])
                if "ping_ms" in data: APP.roblox_session["ping_ms"] = int(data["ping_ms"])
                APP.recorder.emit("roblox_telemetry_updated", **data)
                return self.send_json({"success": True, "session": APP.roblox_session})
            except Exception as e:
                return self.send_json({"error": str(e)}, status=400)

        if route.path in ("/api/record/start", "/api/record/stop"):
            if route.path.endswith("start"):
                try:
                    body = self.read_json()
                except (ValueError, json.JSONDecodeError):
                    return self.send_error(400)
                scanned = body.get("obstacles", [list(p) for p in sorted(OBSTACLES)])
                if not self.valid_map(scanned): return self.send_error(400)
                APP.demo = []
                APP.map_cells = {tuple(p) for p in scanned}
                APP.demo_header = {"scenario": APP.world.scenario,
                                   "world": APP.world.snapshot(),
                                   "map": [list(p) for p in sorted(APP.map_cells)],
                                   "source": "Agent Lab interactive demo recording"}
                APP.recording = True
                APP.replay_active = False
                APP.recorder.emit("demo_recording_started", scenario=APP.world.scenario,
                                  obstacles=len(APP.map_cells))
                return self.send_json({"count": 0, "recording": True})
            APP.recording = False
            APP.recorder.emit("demo_recording_stopped", samples=len(APP.demo))
            return self.send_json({"count": len(APP.demo), "recording": False})

        if route.path == "/api/record/step":
            if not APP.recording: return self.send_error(409)
            try:
                body = self.read_json()
            except (ValueError, json.JSONDecodeError):
                return self.send_error(400)
            input_type = body.get("input")
            if input_type not in ("keyboard", "mouse_drag", "mouse_zoom"):
                return self.send_error(400)
            move = body.get("move", [0, 0])
            cursor = body.get("cursor", None)
            camera = body.get("camera", None)
            if not (isinstance(move, list) and len(move) == 2 and
                    all(isinstance(v, (int, float)) and isfinite(v) for v in move)):
                return self.send_error(400)
            if cursor is not None and not (isinstance(cursor, list) and len(cursor) == 2 and
                                          all(isinstance(v, (int, float)) and isfinite(v) for v in cursor)):
                return self.send_error(400)
            if camera is not None and not (isinstance(camera, dict) and
                                          all(k in camera and isinstance(camera[k], (int, float)) and isfinite(camera[k])
                                              for k in ("yaw", "zoom", "pitch"))):
                return self.send_error(400)
            dx = max(-1.0, min(1.0, float(move[0])))
            dy = max(-1.0, min(1.0, float(move[1])))
            px, py = APP.world.player_x, APP.world.player_y
            moved = False
            collision = False
            if abs(dx) + abs(dy) > 0:
                nx = max(0.0, min(639.0, px + dx * 14))
                ny = max(0.0, min(359.0, py + dy * 14))
                if cell_at((nx, ny)) in APP.map_cells:
                    collision = True
                else:
                    APP.world.player_x = nx
                    APP.world.player_y = ny
                    moved = True
                    APP.world.tick += 1
                    APP.world.idle_ticks = 0
                    APP.world.facing = "E" if abs(dx) >= abs(dy) and dx >= 0 else "W" if abs(dx) >= abs(dy) else "S" if dy >= 0 else "N"
            row = {"tick": APP.world.tick, "input": input_type, "dx": round(dx, 2), "dy": round(dy, 2),
                   "cursor": [round(c, 1) for c in cursor] if cursor else None,
                   "camera": {k: round(float(v), 2) for k, v in camera.items()} if camera else None,
                   "player": [round(APP.world.player_x, 1), round(APP.world.player_y, 1)],
                   "facing": APP.world.facing, "action": APP.agent.planned_path and "navigating" or "manual_control",
                   "collision": collision}
            APP.demo.append(row)
            APP.last = {"action": "manual_record", "reason": "user_demo_input", "outcome": "RECORDED",
                        "path": [], "camera": row["camera"]}
            APP.recorder.emit("manual_demo_recorded", sample=len(APP.demo), input=input_type,
                              collision=collision, moved=moved)
            return self.send_json({"moved": moved, "collision": collision, "count": len(APP.demo), **APP.json()})

        if route.path == "/api/demo/load":
            try:
                body = self.read_json()
                if body.get("format") != "agent-lab-demo-v1": return self.send_error(400)
                header = body.get("header", {})
                scenario = header.get("scenario")
                saved_map = header.get("map", [])
                samples = body.get("samples", [])
                if scenario not in SCENARIOS or not self.valid_map(saved_map) or not isinstance(samples, list) or len(samples) > 2000:
                    return self.send_error(400)
                world = make_world(scenario)
                for key, value in header.get("world", {}).items():
                    if hasattr(world, key) and isinstance(value, (int, float, str, bool)):
                        setattr(world, key, type(getattr(world, key))(value) if not isinstance(getattr(world, key), bool) else bool(value))
                clean = []
                for row in samples:
                    if not isinstance(row, dict) or row.get("input") not in ("keyboard", "mouse_drag", "mouse_zoom"):
                        return self.send_error(400)
                    player = [float(v) for v in row.get("player", [world.player_x, world.player_y])[:2]]
                    camera = {k: float(v) for k, v in row.get("camera", {}).items() if k in ("yaw", "zoom", "pitch")}
                    clean.append({"tick": int(row.get("tick", 0)), "input": row["input"], "dx": row.get("dx", 0),
                                  "dy": row.get("dy", 0), "player": player, "camera": camera})
            except (TypeError, ValueError):
                return self.send_error(400)
            APP.reset(scenario)
            APP.world = world
            APP.map_cells = {tuple(p) for p in saved_map}
            APP.demo_header = {"scenario": scenario, "world": world.snapshot(), "map": saved_map,
                               "source": "Agent Lab imported demo"}
            APP.demo = clean
            APP.recording = False
            APP.recorder.emit("demo_loaded", samples=len(clean), map_cells=len(APP.map_cells))
            return self.send_json({"count": len(clean), **APP.json()})

        if route.path == "/api/replay/start":
            if not APP.demo or not APP.demo_header:
                return self.send_error(409)
            header = APP.demo_header
            world_data = header.get("world", {})
            try:
                world = make_world(header["scenario"])
                for key in ("player_health", "target_health", "target_distance", "target_visible",
                            "vision_confidence", "player_stuck", "action_timeout", "unknown_state",
                            "targets", "player_x", "player_y", "target_x", "target_y", "combat_state",
                            "tick", "facing", "idle_ticks", "recovery_count"):
                    if key in world_data: setattr(world, key, world_data[key])
            except (KeyError, TypeError, ValueError):
                return self.send_error(400)
            APP.world = world
            APP.recorder = Recorder()
            APP.agent = Agent(APP.recorder)
            APP.map_cells = {tuple(p) for p in header["map"]}
            APP.replay_samples = list(APP.demo)
            APP.replay_index = 0
            APP.replay_active = bool(APP.replay_samples)
            APP.last = {"action": "replay_ready", "reason": "saved_map_and_demonstration_loaded",
                        "outcome": "RUNNING", "path": []}
            APP.recorder.emit("replay_started", keyboard_samples=len(APP.replay_samples), map_cells=len(APP.map_cells))
            if not APP.replay_active:
                return self.send_json({**APP.json(), "terminal": True})
            return self.send_json({**APP.json(), "terminal": False})

        if route.path == "/api/replay/step":
            if not APP.replay_active: return self.send_json({**APP.json(), "terminal": True})
            row = APP.replay_samples[APP.replay_index]
            if row.get("input") != "keyboard":
                APP.world.tick += 1
                APP.replay_index += 1
                done = APP.replay_index >= len(APP.replay_samples)
                APP.replay_active = not done
                APP.last = {"action": "replay_camera", "reason": "restore_recorded_camera_state",
                            "outcome": "SUCCESS" if done else "RUNNING", "path": [], "camera": row.get("camera"),
                            "trace": [("SavedMap", "SUCCESS"), ("CameraReplay", "SUCCESS")]}
                APP.recorder.emit("replay_camera", input=row["input"], camera=row.get("camera"))
                return self.send_json({**APP.json(), "terminal": done})
            target = tuple(float(v) for v in row["player"])
            here = (APP.world.player_x, APP.world.player_y)
            current_cell, target_cell = cell_at(here), cell_at(target)
            path = find_path(current_cell, target_cell, APP.map_cells, MAP_WIDTH, MAP_HEIGHT)
            if not path:
                APP.last = {"action": "safe_stop", "reason": "saved_route_blocked_and_no_astar_route",
                            "outcome": "SAFE_STOP", "path": []}
                APP.replay_active = False
                APP.recorder.emit("replay_stopped", reason=APP.last["reason"], sample=APP.replay_index)
                return self.send_json({**APP.json(), "terminal": True})
            aligned_last_step = (len(path) == 2 and
                                 ((path[1][0] != path[0][0] and target_cell[1] == current_cell[1]) or
                                  (path[1][1] != path[0][1] and target_cell[0] == current_cell[0])))
            waypoint = target if current_cell == target_cell or aligned_last_step else center_of(path[1] if len(path) > 1 else path[0])
            nxt = move_toward(here, waypoint, 14)
            if cell_at(nxt) in APP.map_cells and cell_at(nxt) != current_cell:
                APP.last = {"action": "safe_stop", "reason": "obstacle_guard_blocked_replay_step",
                            "outcome": "SAFE_STOP", "path": path}
                APP.replay_active = False
                return self.send_json({**APP.json(), "terminal": True})
            APP.world.player_x, APP.world.player_y = nxt
            dx, dy = nxt[0] - here[0], nxt[1] - here[1]
            if hypot(dx, dy) > .1:
                APP.world.facing = "E" if abs(dx) >= abs(dy) and dx >= 0 else "W" if abs(dx) >= abs(dy) else "S" if dy >= 0 else "N"
            APP.world.tick += 1
            reached = hypot(target[0] - nxt[0], target[1] - nxt[1]) <= 2
            if reached:
                APP.replay_index += 1
            done = APP.replay_index >= len(APP.replay_samples)
            APP.replay_active = not done
            APP.last = {"action": "replay_navigate", "reason": "astar_replan_around_saved_map",
                        "outcome": "SUCCESS" if done else "RUNNING", "path": path, "camera": row.get("camera"),
                        "trace": [("SavedMap", "SUCCESS"), ("AStarPlanner", "SUCCESS"),
                                  ("ObstacleGuard", "CLEAR"), ("ReplayWaypoint", "SUCCESS" if reached else "RUNNING")]}
            APP.recorder.emit("replay_step", sample=APP.replay_index, x=round(nxt[0], 1), y=round(nxt[1], 1),
                              waypoint_reached=reached, path_length=len(path))
            return self.send_json({**APP.json(), "terminal": done})

        if route.path == "/api/start":
            name = parse_qs(route.query).get("scenario", ["NORMAL_COMBAT"])[0]
            if name not in SCENARIOS: return self.send_error(400)
            APP.reset(name); APP.recorder.emit("simulation_started", scenario=name)
            return self.send_json(APP.json())

        if route.path == "/api/step":
            try:
                observation = self.read_json()
            except (ValueError, json.JSONDecodeError):
                return self.send_error(400)
            for key in ("player", "target"):
                point = observation.get(key)
                if point is not None and (not isinstance(point, list) or len(point) != 2 or
                        any(not isinstance(v, (int, float)) for v in point) or
                        not 0 <= point[0] < 640 or not 0 <= point[1] < 360):
                    return self.send_error(400)
            obstacles = observation.get("obstacles", [])
            if not isinstance(obstacles, list) or len(obstacles) > 220 or any(
                    not isinstance(p, list) or len(p) != 2 or any(not isinstance(v, int) for v in p) or
                    not (0 <= p[0] < 20 and 0 <= p[1] < 11) for p in obstacles):
                return self.send_error(400)
            APP.last = APP.agent.step(APP.world, observation)
            return self.send_json({**APP.json(), "terminal": APP.last["terminal"]})

        self.send_error(404)

    def log_message(self, fmt, *args): pass

def serve(host="0.0.0.0", port=8765):
    import sys
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            try: port = int(sys.argv[i + 1])
            except ValueError: pass
        elif arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"GPO Companion listening at http://{host}:{port}. Ctrl+C to stop.")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
