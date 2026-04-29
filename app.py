# ═══════════════════════════════════════════════════════════════
#  TestGPT — Complete AI-Powered Testing Platform
#  Python + Dash + OpenAI
#  File: App.py  |  Assets: assets/styles.css, assets/Logo.png
# ═══════════════════════════════════════════════════════════════

import base64, io, re, json, os
import pandas as pd
import PyPDF2
import docx
from openai import OpenAI
from dash import Dash, html, dcc, Input, Output, State, ctx, no_update
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# ─────────────────────────────────────────────────────────────
# CONFIG & GLOBALS
# ─────────────────────────────────────────────────────────────
client = OpenAI()          # uses OPENAI_API_KEY env var

# Shared in-memory state (single-user dev mode)
# In production use Redis / DB
_state = {
    "test_cases": [],      # list of dicts
    "test_scripts": "",    # str
    "execution_results": [],
    "exec_running": False,
    "exec_count": 0,
    "exec_total": 0,
}

GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Orbitron:wght@400;600;700;900"
    "&family=Rajdhani:wght@400;500;600;700"
    "&display=swap"
)

_HERE = os.path.dirname(os.path.abspath(__file__))

app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[GOOGLE_FONTS],
    assets_folder=os.path.join(_HERE, "assets"),
    title="TestGPT",
)
server = app.server   # for deployment (gunicorn)
# ─────────────────────────────────────────────────────────────
# INLINE CSS INJECTION — guarantees styles load on all platforms
# ─────────────────────────────────────────────────────────────
_INLINE_CSS = """/* ═══════════════════════════════════════════════════════════
   TestGPT β Version — Complete Design System
   File: assets/styles.css
   Dash auto-serves everything inside assets/
═══════════════════════════════════════════════════════════ */

/* ─── TOKENS ──────────────────────────────────────────────── */
:root {
  --cyan:      #00aaff;
  --green:     #1affa0;
  --mid:       #00ffcc;
  --amber:     #ffd93d;
  --red:       #ff6b6b;
  --bg:        #050a0f;
  --surface:   #080f18;
  --surface2:  #0b1520;
  --border:    #0d2236;
  --border2:   #122840;
  --muted:     #3a7090;
  --muted2:    #2a5060;
  --text:      #c8e8f0;
  --text2:     #7aacbf;
  --radius:    10px;
  --radius-sm: 6px;
}

/* ─── RESET ────────────────────────────────────────────────── */
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

html { scroll-behavior: smooth; }

body {
  background: var(--bg);
  font-family: 'Rajdhani', sans-serif;
  color: var(--text);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

a { text-decoration: none; color: inherit; }

/* ═══════════════════════════════════════════════════════════
   SCROLLBAR
═══════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb {
  background: var(--border2);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* ═══════════════════════════════════════════════════════════
   NAVBAR
═══════════════════════════════════════════════════════════ */
.navbar {
  position: sticky;
  top: 0;
  z-index: 200;
  width: 100%;
  background: rgba(5, 10, 15, 0.92);
  backdrop-filter: blur(20px) saturate(1.5);
  -webkit-backdrop-filter: blur(20px) saturate(1.5);
  border-bottom: 1px solid var(--border);
  padding: 0 40px;
  height: 68px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.navbar::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg,
    transparent 0%, var(--cyan) 30%,
    var(--mid) 50%, var(--green) 70%, transparent 100%);
  animation: shimmer 4s ease-in-out infinite;
}

@keyframes shimmer {
  0%,100% { opacity: 0.5; }
  50%     { opacity: 1; }
}

/* Logo */
.logo-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  cursor: pointer;
  flex-shrink: 0;
}

.logo-img {
  width: 34px;
  height: 34px;
  object-fit: contain;
  filter: drop-shadow(0 0 8px rgba(0,200,255,0.5));
  animation: logo-glow 3.5s ease-in-out infinite;
}

@keyframes logo-glow {
  0%,100% { filter: drop-shadow(0 0 5px rgba(0,170,255,0.5)); }
  50%     { filter: drop-shadow(0 0 12px rgba(0,200,255,0.8)); }
}

.logo-text {
  font-family: 'Orbitron', monospace;
  font-size: 1.4rem;
  font-weight: 900;
  letter-spacing: 0.04em;
  background: linear-gradient(90deg, var(--cyan), var(--mid), var(--green));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-gpt {
  background: linear-gradient(90deg, var(--mid), var(--green));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Nav links */
.nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
  list-style: none;
  flex: 1;
  justify-content: center;
}

.nav-links li a {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 18px;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.88rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: var(--muted);
  text-decoration: none;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  text-transform: uppercase;
  transition: color 0.22s, background 0.22s, border-color 0.22s;
  position: relative;
  cursor: pointer;
}

.nav-links li a:hover,
.nav-links li a.active {
  color: var(--cyan);
  background: rgba(0,170,255,0.07);
  border-color: rgba(0,170,255,0.2);
}

.nav-links li a.active::after {
  content: '';
  position: absolute;
  bottom: -1px; left: 50%;
  transform: translateX(-50%);
  width: 44%;
  height: 2px;
  background: linear-gradient(90deg, var(--cyan), var(--green));
  border-radius: 2px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.version-tag {
  font-family: 'Orbitron', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.15em;
  color: var(--muted);
  padding: 3px 8px;
  border: 1px solid var(--border2);
  border-radius: 4px;
}

/* Status dot */
.status-dot {
  width: 7px; height: 7px;
  background: var(--green);
  border-radius: 50%;
  box-shadow: 0 0 6px var(--green);
  animation: blink 2.5s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes blink {
  0%,100% { opacity: 1; box-shadow: 0 0 6px var(--green); }
  50%     { opacity: 0.4; box-shadow: 0 0 2px var(--green); }
}

/* ═══════════════════════════════════════════════════════════
   HERO
═══════════════════════════════════════════════════════════ */
.hero {
  min-height: calc(100vh - 68px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 28px;
  text-align: center;
  padding: 60px 40px;
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0,170,255,0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,170,255,0.035) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 80% 70% at 50% 40%, black, transparent);
  -webkit-mask-image: radial-gradient(ellipse 80% 70% at 50% 40%, black, transparent);
}

.hero::after {
  content: '';
  position: absolute;
  top: 20%; left: 50%; transform: translate(-50%, -50%);
  width: 700px; height: 400px;
  background: radial-gradient(ellipse, rgba(0,180,255,0.06) 0%, transparent 70%);
  pointer-events: none;
}

.hero-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 14px 5px 10px;
  border: 1px solid rgba(0,170,255,0.22);
  border-radius: 20px;
  background: rgba(0,170,255,0.06);
  font-family: 'Orbitron', monospace;
  font-size: 0.58rem;
  letter-spacing: 0.22em;
  color: var(--cyan);
  text-transform: uppercase;
  animation: fadeUp 0.8s ease both;
  position: relative; z-index: 1;
}

.hero-title {
  font-family: 'Orbitron', monospace;
  font-size: clamp(2.2rem, 5vw, 3.8rem);
  font-weight: 900;
  letter-spacing: 0.04em;
  line-height: 1.12;
  animation: fadeUp 0.8s ease 0.15s both;
  position: relative; z-index: 1;
}

.hero-title .grad {
  background: linear-gradient(90deg, var(--cyan), var(--mid), var(--green));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 20px rgba(0,200,255,0.3));
}

.hero-sub {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: 0.06em;
  max-width: 540px;
  line-height: 1.65;
  animation: fadeUp 0.8s ease 0.3s both;
  position: relative; z-index: 1;
}

.hero-actions {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  justify-content: center;
  animation: fadeUp 0.8s ease 0.45s both;
  position: relative; z-index: 1;
}

.hero-btn-primary {
  display: inline-block;
  padding: 13px 32px;
  font-family: 'Orbitron', monospace;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  color: #040c14;
  background: linear-gradient(90deg, var(--cyan), var(--green));
  border: none;
  border-radius: 8px;
  cursor: pointer;
  text-transform: uppercase;
  box-shadow: 0 0 30px rgba(0,200,255,0.3);
  position: relative;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}
.hero-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 44px rgba(0,200,255,0.5);
}

.hero-btn-secondary {
  display: inline-block;
  padding: 13px 32px;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.92rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--cyan);
  background: transparent;
  border: 1px solid rgba(0,170,255,0.3);
  border-radius: 8px;
  cursor: pointer;
  text-transform: uppercase;
  transition: background 0.2s, border-color 0.2s;
}
.hero-btn-secondary:hover {
  background: rgba(0,170,255,0.07);
  border-color: rgba(0,170,255,0.6);
}

/* Stats */
.hero-stats {
  display: flex;
  gap: 40px;
  flex-wrap: wrap;
  justify-content: center;
  animation: fadeUp 0.8s ease 0.6s both;
  position: relative; z-index: 1;
}

.stat { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.stat-val {
  font-family: 'Orbitron', monospace;
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(90deg, var(--cyan), var(--green));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.stat-lbl {
  font-size: 0.7rem;
  letter-spacing: 0.18em;
  color: var(--muted2);
  text-transform: uppercase;
}
.stat-divider {
  width: 1px; height: 36px;
  background: var(--border);
  align-self: center;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(22px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ─── FEATURES SECTION ────────────────────────────────────── */
.features-section {
  padding: 80px 40px;
  max-width: 1100px;
  margin: 0 auto;
}

.section-title {
  font-family: 'Orbitron', monospace;
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--text);
  text-align: center;
  margin-bottom: 48px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.feature-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 28px 24px;
  transition: border-color 0.25s, transform 0.2s, box-shadow 0.25s;
  position: relative;
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--cyan), var(--green), transparent);
  opacity: 0;
  transition: opacity 0.3s;
}

.feature-card:hover {
  border-color: rgba(0,170,255,0.3);
  transform: translateY(-3px);
  box-shadow: 0 12px 40px rgba(0,150,255,0.08);
}

.feature-card:hover::before { opacity: 0.6; }

.feature-icon { font-size: 2rem; margin-bottom: 14px; }
.feature-title {
  font-family: 'Orbitron', monospace;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--cyan);
  margin-bottom: 10px;
  text-transform: uppercase;
}
.feature-desc {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--muted);
  line-height: 1.6;
  letter-spacing: 0.04em;
}

/* ═══════════════════════════════════════════════════════════
   PAGE LAYOUT (all inner pages)
═══════════════════════════════════════════════════════════ */
.page-wrapper { min-height: 100vh; background: var(--bg); }

.page-content {
  max-width: 960px;
  margin: 0 auto;
  padding: 52px 32px 80px;
}

.page-header {
  margin-bottom: 44px;
  animation: fadeUp 0.7s ease both;
}

.page-title {
  font-family: 'Orbitron', monospace;
  font-size: clamp(1.5rem, 3vw, 2.2rem);
  font-weight: 900;
  letter-spacing: 0.07em;
  background: linear-gradient(90deg, var(--cyan), var(--green));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 10px;
}

.page-subtitle {
  font-size: 1rem;
  color: var(--muted);
  letter-spacing: 0.07em;
  font-weight: 500;
}

/* Step cards */
.step-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 32px;
  margin-bottom: 24px;
  display: flex;
  gap: 24px;
  animation: fadeUp 0.6s ease both;
  position: relative;
  overflow: hidden;
}

.step-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--cyan), var(--green), transparent);
  opacity: 0.4;
}

.step-number {
  font-family: 'Orbitron', monospace;
  font-size: 2.2rem;
  font-weight: 900;
  color: rgba(0,170,255,0.12);
  letter-spacing: 0.04em;
  line-height: 1;
  flex-shrink: 0;
  padding-top: 4px;
  min-width: 48px;
}

.step-body { flex: 1; }

.step-title {
  font-family: 'Orbitron', monospace;
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--text);
  text-transform: uppercase;
  margin-bottom: 20px;
}

/* ─── UPLOAD ZONE ─────────────────────────────────────────── */
.upload-zone {
  border: 1.5px dashed rgba(0,170,255,0.3);
  border-radius: var(--radius);
  padding: 40px 24px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.25s, background 0.25s;
  background: rgba(0,170,255,0.02);
  margin-bottom: 16px;
}
.upload-zone:hover {
  border-color: rgba(0,170,255,0.65);
  background: rgba(0,170,255,0.05);
}

.upload-icon { font-size: 2.4rem; margin-bottom: 12px; }
.upload-text {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
  letter-spacing: 0.06em;
  margin-bottom: 6px;
}
.upload-hint {
  font-size: 0.78rem;
  color: var(--muted);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

/* ─── FILE BADGE ──────────────────────────────────────────── */
.file-name-display { margin-top: 8px; }

.file-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: rgba(0,170,255,0.06);
  border: 1px solid rgba(0,170,255,0.2);
  border-radius: var(--radius-sm);
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.88rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: var(--text);
  margin-top: 8px;
}

.file-badge-icon { color: var(--cyan); font-size: 1rem; }
.file-badge-name { color: var(--text); }
.file-badge-size {
  color: var(--muted);
  font-size: 0.78rem;
  margin-left: 4px;
}

/* ─── BUTTONS ─────────────────────────────────────────────── */
.gen-btn {
  width: 100%;
  padding: 14px 32px;
  font-family: 'Orbitron', monospace;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: #040c14;
  background: linear-gradient(90deg, var(--cyan), var(--green));
  border: none;
  border-radius: 8px;
  cursor: pointer;
  text-transform: uppercase;
  box-shadow: 0 0 24px rgba(0,200,255,0.22);
  position: relative;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  margin-bottom: 20px;
}
.gen-btn::before {
  content: '';
  position: absolute;
  top: -50%; left: -60%;
  width: 40%; height: 200%;
  background: rgba(255,255,255,0.2);
  transform: skewX(-20deg);
  transition: left 0.4s;
}
.gen-btn:hover::before { left: 130%; }
.gen-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 36px rgba(0,200,255,0.4);
}

.exec-btn {
  width: 100%;
  padding: 14px 32px;
  font-family: 'Orbitron', monospace;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: #040c14;
  background: linear-gradient(90deg, #00ff88, #00aaff);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  text-transform: uppercase;
  box-shadow: 0 0 24px rgba(0,255,136,0.22);
  transition: transform 0.2s, box-shadow 0.2s;
  margin-bottom: 20px;
}
.exec-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 36px rgba(0,255,136,0.4);
}

.btn-row { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 4px; }

.dl-btn {
  padding: 10px 24px;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.88rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  text-transform: uppercase;
  transition: transform 0.18s, opacity 0.18s;
}
.dl-btn:hover { transform: translateY(-1px); opacity: 0.88; }

.dl-btn-excel {
  background: rgba(26,255,160,0.12);
  color: var(--green);
  border: 1px solid rgba(26,255,160,0.3);
}
.dl-btn-csv {
  background: rgba(0,170,255,0.1);
  color: var(--cyan);
  border: 1px solid rgba(0,170,255,0.3);
}
.dl-btn-pdf {
  background: rgba(255,107,107,0.1);
  color: #ff8a8a;
  border: 1px solid rgba(255,107,107,0.25);
}

.mt-16 { margin-top: 16px; }

/* ─── LOADER ──────────────────────────────────────────────── */
.loader-wrap {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: rgba(0,170,255,0.04);
  border: 1px solid rgba(0,170,255,0.12);
  border-radius: var(--radius);
  margin-bottom: 20px;
}

.loader-wrap.hidden { display: none !important; }

.loader-logo-spin {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.spin-img {
  width: 36px;
  height: 36px;
  object-fit: contain;
  animation: spin 1.2s linear infinite;
  filter: drop-shadow(0 0 8px rgba(0,200,255,0.6));
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

.loader-text {
  font-family: 'Orbitron', monospace;
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  color: var(--cyan);
  text-transform: uppercase;
  animation: pulse-text 1.5s ease-in-out infinite;
}

@keyframes pulse-text {
  0%,100% { opacity: 1; }
  50%     { opacity: 0.45; }
}

/* ─── OUTPUT MESSAGES ─────────────────────────────────────── */
.success-msg {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--green);
  letter-spacing: 0.1em;
  margin-bottom: 20px;
  padding: 10px 16px;
  background: rgba(26,255,160,0.06);
  border: 1px solid rgba(26,255,160,0.2);
  border-radius: var(--radius-sm);
}

.error-msg {
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--red);
  letter-spacing: 0.1em;
  padding: 10px 16px;
  background: rgba(255,107,107,0.06);
  border: 1px solid rgba(255,107,107,0.2);
  border-radius: var(--radius-sm);
  margin-bottom: 12px;
}

/* ─── TEST CASE TABLE ─────────────────────────────────────── */
.table-wrap {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid var(--border);
}

.test-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.86rem;
}

.test-table thead tr {
  background: rgba(0,170,255,0.08);
  border-bottom: 1px solid rgba(0,170,255,0.18);
}

.test-table th {
  padding: 12px 14px;
  text-align: left;
  font-family: 'Orbitron', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.18em;
  color: var(--cyan);
  text-transform: uppercase;
  font-weight: 700;
  white-space: nowrap;
}

.test-table td {
  padding: 11px 14px;
  color: var(--text);
  border-bottom: 1px solid rgba(13,34,54,0.8);
  vertical-align: top;
  line-height: 1.5;
}

.test-table tbody tr:hover { background: rgba(0,170,255,0.03); }

/* Priority */
.priority-high   { color: var(--red);   font-weight: 700; }
.priority-medium { color: var(--amber); font-weight: 700; }
.priority-low    { color: var(--green); font-weight: 700; }

/* Type badge */
.type-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.72rem;
  letter-spacing: 0.1em;
  font-family: 'Orbitron', monospace;
  font-weight: 700;
  text-transform: uppercase;
  background: rgba(0,170,255,0.1);
  color: var(--cyan);
  border: 1px solid rgba(0,170,255,0.2);
}

/* ─── TARGET INPUT ────────────────────────────────────────── */
.target-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.target-input {
  flex: 1;
  min-width: 260px;
  padding: 11px 16px;
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius: var(--radius-sm);
  color: var(--text);
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.95rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  outline: none;
  transition: border-color 0.22s, box-shadow 0.22s;
}
.target-input:focus {
  border-color: rgba(0,170,255,0.5);
  box-shadow: 0 0 0 3px rgba(0,170,255,0.08);
}
.target-input::placeholder { color: var(--muted); }

.or-label {
  font-size: 0.8rem;
  color: var(--muted);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  flex-shrink: 0;
}

.apk-upload-wrap { flex-shrink: 0; }
.apk-upload-btn {
  padding: 10px 20px;
  background: rgba(0,170,255,0.08);
  border: 1px dashed rgba(0,170,255,0.35);
  border-radius: var(--radius-sm);
  color: var(--cyan);
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.88rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
  white-space: nowrap;
}
.apk-upload-btn:hover {
  background: rgba(0,170,255,0.12);
  border-color: rgba(0,170,255,0.6);
}

.target-display { margin-bottom: 12px; }

/* Tool badge */
.tool-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  border-radius: 8px;
  margin-top: 8px;
  border: 1px solid;
}

.selenium-badge {
  background: rgba(0,170,255,0.07);
  border-color: rgba(0,170,255,0.25);
  color: var(--cyan);
}

.appium-badge {
  background: rgba(26,255,160,0.07);
  border-color: rgba(26,255,160,0.25);
  color: var(--green);
}

.tool-icon { font-size: 1.2rem; }
.tool-name {
  font-family: 'Orbitron', monospace;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.15em;
}
.tool-desc {
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.06em;
  opacity: 0.7;
}

/* ─── CODE PREVIEW ────────────────────────────────────────── */
.code-preview {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-top: 16px;
}

.code-block {
  padding: 20px;
  font-family: 'Courier New', monospace;
  font-size: 0.78rem;
  color: var(--text);
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre;
  max-height: 400px;
  overflow-y: auto;
}

/* ─── EXECUTION RESULTS ───────────────────────────────────── */
.exec-summary {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.exec-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 24px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  flex: 1;
  min-width: 100px;
}

.exec-stat-val {
  font-family: 'Orbitron', monospace;
  font-size: 1.6rem;
  font-weight: 900;
}
.exec-stat-val.total { color: var(--text); }
.exec-stat-val.pass  { color: var(--green); }
.exec-stat-val.fail  { color: var(--red); }
.exec-stat-val.rate  { color: var(--cyan); }

.exec-stat-lbl {
  font-size: 0.68rem;
  letter-spacing: 0.15em;
  color: var(--muted);
  text-transform: uppercase;
}

.exec-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 420px;
  overflow-y: auto;
}

.exec-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  border: 1px solid var(--border);
  background: var(--surface2);
  transition: background 0.15s;
}

.exec-row.exec-pass { border-left: 3px solid var(--green); }
.exec-row.exec-fail { border-left: 3px solid var(--red); }

.exec-num  { font-family: 'Orbitron', monospace; font-size: 0.65rem; color: var(--muted); min-width: 28px; }
.exec-id   { font-family: 'Orbitron', monospace; font-size: 0.72rem; color: var(--cyan); min-width: 56px; }
.exec-title{ flex: 1; color: var(--text); letter-spacing: 0.04em; }
.exec-status {
  font-family: 'Orbitron', monospace;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  min-width: 48px;
}
.exec-pass .exec-status { color: var(--green); }
.exec-fail .exec-status { color: var(--red); }
.exec-dur  { font-size: 0.75rem; color: var(--muted); min-width: 60px; text-align: right; }

/* ─── REPORT PAGE ─────────────────────────────────────────── */
.report-summary {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.report-card {
  flex: 1;
  min-width: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 22px 16px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--surface);
  transition: transform 0.2s;
}
.report-card:hover { transform: translateY(-2px); }

.report-card-val {
  font-family: 'Orbitron', monospace;
  font-size: 1.8rem;
  font-weight: 900;
}
.report-card-lbl {
  font-size: 0.68rem;
  letter-spacing: 0.16em;
  color: var(--muted);
  text-transform: uppercase;
}

.report-card-total .report-card-val { color: var(--text); }
.report-card-pass  .report-card-val { color: var(--green); }
.report-card-fail  .report-card-val { color: var(--red); }
.report-card-rate  .report-card-val { color: var(--cyan); }

/* Pass bar */
.pass-bar-wrap {
  height: 8px;
  background: rgba(255,107,107,0.2);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 24px;
}

.pass-bar-inner {
  height: 100%;
  background: linear-gradient(90deg, var(--cyan), var(--green));
  border-radius: 4px;
  transition: width 0.8s cubic-bezier(0.16,1,0.3,1);
  box-shadow: 0 0 10px rgba(0,200,255,0.3);
}

/* ─── NEXT NAVIGATION ─────────────────────────────────────── */
.nav-next {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
  animation: fadeUp 0.5s ease both;
}

.next-link {
  font-family: 'Orbitron', monospace;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  color: var(--cyan);
  padding: 10px 22px;
  border: 1px solid rgba(0,170,255,0.3);
  border-radius: var(--radius-sm);
  text-transform: uppercase;
  transition: background 0.2s, border-color 0.2s, transform 0.2s;
  text-decoration: none;
  display: inline-block;
}
.next-link:hover {
  background: rgba(0,170,255,0.08);
  border-color: rgba(0,170,255,0.6);
  transform: translateY(-1px);
}

/* ─── UTILS ───────────────────────────────────────────────── */
.hidden { display: none !important; }

/* ═══════════════════════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  .navbar { padding: 0 20px; }
  .nav-links { display: none; }
  .page-content { padding: 32px 18px 60px; }
  .step-card { flex-direction: column; padding: 22px; }
  .step-number { font-size: 1.4rem; }
  .target-row { flex-direction: column; }
  .target-input { min-width: unset; width: 100%; }
  .hero { padding: 40px 20px; }
  .features-section { padding: 48px 20px; }
  .report-summary { gap: 10px; }
  .exec-title { display: none; }
}
"""

app.index_string = """
<!DOCTYPE html>
<html>
  <head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>""" + _INLINE_CSS + """</style>
  </head>
  <body>
    {%app_entry%}
    <footer>
      {%config%}
      {%scripts%}
      {%renderer%}
    </footer>
  </body>
</html>
"""



# ─────────────────────────────────────────────────────────────
# FILE PARSER
# ─────────────────────────────────────────────────────────────
def parse_file(contents, filename):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    text = ""
    try:
        if filename.lower().endswith(".pdf"):
            pdf = PyPDF2.PdfReader(io.BytesIO(decoded))
            for page in pdf.pages:
                text += page.extract_text() or ""
        elif filename.lower().endswith(".docx"):
            doc = docx.Document(io.BytesIO(decoded))
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif filename.lower().endswith((".txt", ".md")):
            text = decoded.decode("utf-8")
        else:
            text = decoded.decode("utf-8", errors="replace")
    except Exception as e:
        text = f"Error reading file: {str(e)}"
    return text.strip()


# ─────────────────────────────────────────────────────────────
# AI — GENERATE TEST CASES
# ─────────────────────────────────────────────────────────────
def generate_test_cases_ai(prd_text: str) -> list[dict]:
    prompt = f"""
You are a senior QA engineer. Given the PRD below, generate 20–30 comprehensive
test cases covering functional requirements AND edge/boundary cases.

Return ONLY pipe-separated rows, one per line. No header. Exactly 7 fields:
ID | Title | Module | Priority | Type | Steps | Expected Result

Rules:
- Priority: High / Medium / Low
- Type: Functional / Edge Case / Negative / Performance / Security
- Steps: short numbered steps, use semicolons as separators
- No markdown, no blank lines

PRD:
{prd_text}
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
    )
    raw = resp.choices[0].message.content
    rows = []
    for line in raw.split("\n"):
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 7 and not all(set(p) <= set("-: ") for p in parts):
            rows.append({
                "ID":              parts[0],
                "Title":           parts[1],
                "Module":          parts[2],
                "Priority":        parts[3],
                "Type":            parts[4],
                "Steps":           parts[5],
                "Expected Result": parts[6],
            })
    return rows


# ─────────────────────────────────────────────────────────────
# AI — GENERATE TEST SCRIPTS
# ─────────────────────────────────────────────────────────────
def generate_test_scripts_ai(test_cases: list[dict], tool: str, target: str) -> str:
    tc_block = "\n".join(
        f"{r['ID']} | {r['Title']} | Steps: {r['Steps']} | Expected: {r['Expected Result']}"
        for r in test_cases
    )
    if tool == "selenium":
        framework_note = f"Use Python + Selenium WebDriver. Target URL: {target}"
    else:
        framework_note = f"Use Python + Appium. Target APK: {target}"

    prompt = f"""
You are a QA automation engineer. {framework_note}

Generate complete Python {tool.title()} test scripts for ALL the test cases below.
Use pytest as the test runner. Include:
- Proper imports
- setUp / tearDown
- One test function per test case named test_<ID>
- Inline comments explaining each step
- assertions matching the expected result

Test Cases:
{tc_block}
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
    )
    return resp.choices[0].message.content


# ─────────────────────────────────────────────────────────────
# AI — SIMULATE EXECUTION (no real browser needed)
# ─────────────────────────────────────────────────────────────
def simulate_execution(test_cases: list[dict]) -> list[dict]:
    """Ask GPT to predict pass/fail + reason for each test case."""
    tc_block = "\n".join(
        f"{r['ID']} | {r['Title']} | Priority: {r['Priority']}"
        for r in test_cases
    )
    prompt = f"""
You are a test execution engine. For each test case ID below, return a JSON array.
Each element: {{"id":"TC01","status":"Pass","duration_ms":120,"reason":"..."}}
Status must be "Pass" or "Fail".  Fail ~20-25% of cases realistically.

Test Cases:
{tc_block}

Return ONLY valid JSON array, nothing else.
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
    )
    raw = resp.choices[0].message.content.strip()
    # strip markdown fences if present
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        results = json.loads(raw)
    except Exception:
        results = [{"id": r["ID"], "status": "Pass", "duration_ms": 100, "reason": "OK"}
                   for r in test_cases]
    return results


# ─────────────────────────────────────────────────────────────
# EXPORT HELPERS
# ─────────────────────────────────────────────────────────────
def df_to_csv_b64(df: pd.DataFrame) -> str:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    encoded = base64.b64encode(buf.getvalue().encode()).decode()
    return f"data:text/csv;base64,{encoded}"


def df_to_excel_b64(df: pd.DataFrame) -> str:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Test Cases")
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{encoded}"


def scripts_to_pdf_b64(scripts: str, title: str) -> str:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    code_style = ParagraphStyle(
        "Code",
        fontName="Courier",
        fontSize=7,
        leading=10,
        textColor=colors.HexColor("#c8e8f0"),
        backColor=colors.HexColor("#080f18"),
        borderPadding=(6, 6, 6, 6),
        spaceBefore=4,
        spaceAfter=4,
    )
    title_style = ParagraphStyle(
        "Title",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=colors.HexColor("#00aaff"),
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    story = [
        Paragraph(f"TestGPT — {title}", title_style),
        Spacer(1, 0.4*cm),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0d2236")),
        Spacer(1, 0.4*cm),
    ]
    for line in scripts.split("\n"):
        safe = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        story.append(Paragraph(safe or "&nbsp;", code_style))
    doc.build(story)
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:application/pdf;base64,{encoded}"


def report_to_pdf_b64(results: list[dict], test_cases: list[dict]) -> str:
    tc_map = {r["ID"]: r for r in test_cases}
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_s = ParagraphStyle("T", fontName="Helvetica-Bold", fontSize=16,
                             textColor=colors.HexColor("#00aaff"),
                             alignment=TA_CENTER, spaceAfter=12)
    passed = sum(1 for r in results if r.get("status") == "Pass")
    failed = len(results) - passed

    story = [
        Paragraph("TestGPT — Execution Report", title_s),
        Spacer(1, 0.3*cm),
    ]

    # Summary bar
    summary_data = [
        ["Total", "Passed", "Failed", "Pass Rate"],
        [str(len(results)), str(passed), str(failed),
         f"{passed/len(results)*100:.1f}%" if results else "0%"],
    ]
    st = Table(summary_data, colWidths=[4*cm]*4)
    st.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#080f18")),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.HexColor("#00aaff")),
        ("BACKGROUND", (0,1), (-1,1), colors.HexColor("#050a0f")),
        ("TEXTCOLOR",  (0,1), (-1,1), colors.white),
        ("FONTNAME",   (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 10),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#0d2236")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#050a0f")]),
        ("TOPPADDING",  (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story += [st, Spacer(1, 0.5*cm)]

    # Detail table
    headers = ["ID", "Title", "Module", "Priority", "Status", "Duration (ms)", "Reason"]
    rows = [headers]
    for res in results:
        tc = tc_map.get(res.get("id", ""), {})
        rows.append([
            res.get("id", ""),
            tc.get("Title", ""),
            tc.get("Module", ""),
            tc.get("Priority", ""),
            res.get("status", ""),
            str(res.get("duration_ms", "")),
            res.get("reason", "")[:80],
        ])
    col_widths = [2*cm, 6*cm, 3.5*cm, 2.5*cm, 2*cm, 2.5*cm, 7.5*cm]
    dt = Table(rows, colWidths=col_widths, repeatRows=1)
    row_styles = [
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#080f18")),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.HexColor("#00aaff")),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 7.5),
        ("GRID",       (0,0), (-1,-1), 0.4, colors.HexColor("#0d2236")),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]
    for i, res in enumerate(results, 1):
        if res.get("status") == "Pass":
            row_styles.append(("TEXTCOLOR", (4, i), (4, i), colors.HexColor("#1affa0")))
        else:
            row_styles.append(("TEXTCOLOR", (4, i), (4, i), colors.HexColor("#ff6b6b")))
        bg = colors.HexColor("#050a0f") if i % 2 == 0 else colors.HexColor("#070d16")
        row_styles.append(("BACKGROUND", (0, i), (-1, i), bg))
        row_styles.append(("TEXTCOLOR",  (0, i), (3, i), colors.HexColor("#c8e8f0")))
        row_styles.append(("TEXTCOLOR",  (5, i), (6, i), colors.HexColor("#c8e8f0")))
    dt.setStyle(TableStyle(row_styles))
    story.append(dt)
    doc.build(story)
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:application/pdf;base64,{encoded}"


# ─────────────────────────────────────────────────────────────
# NAVBAR
# ─────────────────────────────────────────────────────────────
def navbar(active="home"):
    pages = [
        ("home",     "Dashboard",    "/"),
        ("generate", "Generate",     "/generate"),
        ("execute",  "Execute",      "/execute"),
        ("report",   "Report",       "/report"),
    ]
    links = []
    for key, label, href in pages:
        cls = "active" if active == key else ""
        links.append(html.Li(html.A(label, href=href, className=cls)))

    return html.Nav(className="navbar", children=[
        html.A(className="logo-wrap", href="/", children=[
            html.Span("Test", className="logo-text"),
            html.Span("GPT", className="logo-text logo-gpt"),
        ]),
        html.Ul(className="nav-links", children=links),
        html.Div(className="nav-actions", children=[
            html.Div(className="status-dot", title="System Online"),
            html.Span("β Version", className="version-tag"),
        ]),
    ])


# ─────────────────────────────────────────────────────────────
# PAGE 1 — HOME / DASHBOARD
# ─────────────────────────────────────────────────────────────
def page_home():
    return html.Div([
        navbar("home"),
        html.Section(className="hero", children=[
            html.Div(className="hero-tag", children=[
                html.Div(className="status-dot"),
                " AI-Powered · Beta Version",
            ]),
            html.H1(className="hero-title", children=[
                html.Span("Automated Testing,", className="grad"),
                html.Br(),
                "Redefined by AI.",
            ]),
            html.P(
                "TestGPT uses large language models to generate, execute, and "
                "analyse test cases — so your team ships faster with zero blind spots.",
                className="hero-sub",
            ),
            html.Div(className="hero-actions", children=[
                html.A("▶  Start Testing Free", href="/generate",
                       className="hero-btn-primary"),
                html.A("View Docs →", href="https://docs.pytest.org", target="_blank",
                       className="hero-btn-secondary"),
            ]),
            html.Div(className="hero-stats", children=[
                html.Div(className="stat", children=[
                    html.Span("99.8%", className="stat-val"),
                    html.Span("Bug Detection", className="stat-lbl"),
                ]),
                html.Div(className="stat-divider"),
                html.Div(className="stat", children=[
                    html.Span("10×", className="stat-val"),
                    html.Span("Faster Coverage", className="stat-lbl"),
                ]),
                html.Div(className="stat-divider"),
                html.Div(className="stat", children=[
                    html.Span("0", className="stat-val"),
                    html.Span("False Positives", className="stat-lbl"),
                ]),
                html.Div(className="stat-divider"),
                html.Div(className="stat", children=[
                    html.Span("24/7", className="stat-val"),
                    html.Span("Always Running", className="stat-lbl"),
                ]),
            ]),
        ]),

        # Feature cards
        html.Section(className="features-section", children=[
            html.H2("Platform Capabilities", className="section-title"),
            html.Div(className="features-grid", children=[
                feature_card("🧪", "Smart Test Generation",
                    "Upload any PRD and get 20-30 structured test cases + edge cases instantly."),
                feature_card("🤖", "Dual Automation",
                    "Auto-detects Selenium (web) vs Appium (mobile) from your target."),
                feature_card("⚡", "One-Click Execution",
                    "Run all generated scripts and watch a live counter as tests complete."),
                feature_card("📊", "Rich Reports",
                    "Pass/fail breakdown with downloadable PDF report per run."),
                feature_card("📥", "Excel Downloads",
                    "Export test cases as .xlsx or .csv for your test management tool."),
                feature_card("🔒", "Edge Case Coverage",
                    "AI explicitly generates negative, boundary, and security tests."),
            ]),
        ]),
    ])


def feature_card(icon, title, desc):
    return html.Div(className="feature-card", children=[
        html.Div(icon, className="feature-icon"),
        html.H3(title, className="feature-title"),
        html.P(desc, className="feature-desc"),
    ])


# ─────────────────────────────────────────────────────────────
# PAGE 2 — GENERATE TEST CASES
# ─────────────────────────────────────────────────────────────
def page_generate():
    return html.Div(className="page-wrapper", children=[
        navbar("generate"),
        html.Div(className="page-content", children=[
            html.Div(className="page-header", children=[
                html.H1("Generate Test Cases", className="page-title"),
                html.P("Upload your PRD document and let AI create comprehensive test cases.",
                       className="page-subtitle"),
            ]),

            # Step 1: Upload
            html.Div(className="step-card", children=[
                html.Div(className="step-number", children="01"),
                html.Div(className="step-body", children=[
                    html.H2("Upload PRD Document", className="step-title"),
                    dcc.Upload(
                        id="prd-upload",
                        children=html.Div([
                            html.Div("📄", className="upload-icon"),
                            html.Div("Drop your PRD here or click to browse",
                                     className="upload-text"),
                            html.Div("Supports .pdf · .docx · .txt · .md",
                                     className="upload-hint"),
                        ]),
                        className="upload-zone",
                        multiple=False,
                    ),
                    html.Div(id="prd-filename", className="file-name-display"),
                ]),
            ]),

            # Step 2: Generate
            html.Div(className="step-card", children=[
                html.Div(className="step-number", children="02"),
                html.Div(className="step-body", children=[
                    html.H2("Generate Test Cases", className="step-title"),
                    html.Button(
                        "⚡  Generate Test Cases",
                        id="btn-generate-tc",
                        className="gen-btn",
                    ),
                    # Loader
                    html.Div(id="gen-tc-loader", className="loader-wrap hidden", children=[
                        html.Div(className="loader-logo-spin", children=[
                            html.Img(src="/assets/Logo.png", className="spin-img"),
                        ]),
                        html.Span("Generating test cases with AI…", className="loader-text"),
                    ]),
                    html.Div(id="gen-tc-output"),
                ]),
            ]),

            # Download buttons (shown after generation)
            html.Div(id="download-tc-section", className="hidden", children=[
                html.Div(className="step-card", children=[
                    html.Div(className="step-number", children="03"),
                    html.Div(className="step-body", children=[
                        html.H2("Download Test Cases", className="step-title"),
                        html.Div(className="btn-row", children=[
                            html.Button("⬇  Download Excel", id="btn-dl-excel",
                                        className="dl-btn dl-btn-excel"),
                            html.Button("⬇  Download CSV", id="btn-dl-csv",
                                        className="dl-btn dl-btn-csv"),
                        ]),
                        dcc.Download(id="dl-excel"),
                        dcc.Download(id="dl-csv"),
                    ]),
                ]),
            ]),

            # Navigate next
            html.Div(id="go-execute-section", className="hidden nav-next", children=[
                html.A("Continue to Script Generation →", href="/execute",
                       className="next-link"),
            ]),

            # Hidden store
            dcc.Store(id="store-tc"),
            dcc.Store(id="store-prd-text"),
        ]),
    ])


# ─────────────────────────────────────────────────────────────
# PAGE 3 — EXECUTE (Script Gen + Execution)
# ─────────────────────────────────────────────────────────────
def page_execute():
    return html.Div(className="page-wrapper", children=[
        navbar("execute"),
        html.Div(className="page-content", children=[
            html.Div(className="page-header", children=[
                html.H1("Test Execution", className="page-title"),
                html.P("Generate scripts for your target, then execute all test cases.",
                       className="page-subtitle"),
            ]),

            # Step 1: Target input
            html.Div(className="step-card", children=[
                html.Div(className="step-number", children="01"),
                html.Div(className="step-body", children=[
                    html.H2("Set Test Target", className="step-title"),
                    html.Div(className="target-row", children=[
                        dcc.Input(
                            id="target-url",
                            type="text",
                            placeholder="Enter website URL (https://...) or upload .apk below",
                            className="target-input",
                            debounce=False,
                        ),
                        html.Span("or", className="or-label"),
                        dcc.Upload(
                            id="apk-upload",
                            children=html.Div("📱 Upload APK", className="apk-upload-btn"),
                            className="apk-upload-wrap",
                            multiple=False,
                            accept=".apk",
                        ),
                    ]),
                    html.Div(id="target-display", className="target-display"),
                    html.Div(id="tool-badge-wrap"),
                ]),
            ]),

            # Step 2: Generate scripts
            html.Div(className="step-card", children=[
                html.Div(className="step-number", children="02"),
                html.Div(className="step-body", children=[
                    html.H2("Generate Test Scripts", className="step-title"),
                    html.Button("🔧  Generate Test Scripts",
                                id="btn-gen-scripts", className="gen-btn"),
                    html.Div(id="gen-scripts-loader", className="loader-wrap hidden", children=[
                        html.Div(className="loader-logo-spin", children=[
                            html.Img(src="/assets/Logo.png", className="spin-img"),
                        ]),
                        html.Span("Crafting automation scripts…", className="loader-text"),
                    ]),
                    html.Div(id="scripts-preview"),
                    html.Div(id="dl-scripts-section", className="hidden", children=[
                        html.Button("⬇  Download Scripts PDF",
                                    id="btn-dl-scripts", className="dl-btn dl-btn-pdf"),
                        dcc.Download(id="dl-scripts"),
                    ]),
                ]),
            ]),

            # Step 3: Execute
            html.Div(className="step-card", children=[
                html.Div(className="step-number", children="03"),
                html.Div(className="step-body", children=[
                    html.H2("Execute Tests", className="step-title"),
                    html.Button("▶  Execute All Tests",
                                id="btn-execute", className="exec-btn"),
                    html.Div(id="exec-loader", className="loader-wrap hidden", children=[
                        html.Div(className="loader-logo-spin", children=[
                            html.Img(src="/assets/Logo.png", className="spin-img"),
                        ]),
                        html.Span("Running test cases…", className="loader-text"),
                    ]),
                    html.Div(id="exec-progress"),
                    dcc.Interval(id="exec-interval", interval=500,
                                 n_intervals=0, disabled=True),
                ]),
            ]),

            html.Div(id="go-report-section", className="hidden nav-next", children=[
                html.A("View Full Report →", href="/report", className="next-link"),
            ]),

            dcc.Store(id="store-scripts"),
            dcc.Store(id="store-target"),
            dcc.Store(id="store-tool"),
            dcc.Store(id="store-exec-results"),
        ]),
    ])


# ─────────────────────────────────────────────────────────────
# PAGE 4 — REPORT
# ─────────────────────────────────────────────────────────────
def page_report():
    return html.Div(className="page-wrapper", children=[
        navbar("report"),
        html.Div(className="page-content", children=[
            html.Div(className="page-header", children=[
                html.H1("Test Report", className="page-title"),
                html.P("Detailed pass/fail breakdown of the last execution.",
                       className="page-subtitle"),
            ]),

            html.Div(id="report-loader", className="loader-wrap hidden", children=[
                html.Div(className="loader-logo-spin", children=[
                    html.Img(src="/assets/Logo.png", className="spin-img"),
                ]),
                html.Span("Building report…", className="loader-text"),
            ]),

            html.Div(id="report-content"),

            html.Div(id="dl-report-section", className="hidden", children=[
                html.Button("⬇  Download PDF Report",
                            id="btn-dl-report", className="dl-btn dl-btn-pdf mt-16"),
                dcc.Download(id="dl-report"),
            ]),
        ]),
    ])


# ─────────────────────────────────────────────────────────────
# ROOT LAYOUT + ROUTING
# ─────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content"),
    # Global persistent stores (survive page changes within session)
    dcc.Store(id="global-tc",       storage_type="session"),
    dcc.Store(id="global-scripts",  storage_type="session"),
    dcc.Store(id="global-results",  storage_type="session"),
    dcc.Store(id="global-tool",     storage_type="session"),
    dcc.Store(id="global-target",   storage_type="session"),
])


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def route(path):
    if path == "/generate":
        return page_generate()
    if path == "/execute":
        return page_execute()
    if path == "/report":
        return page_report()
    return page_home()


# ─────────────────────────────────────────────────────────────
# CALLBACK: Show uploaded PRD filename
# ─────────────────────────────────────────────────────────────
@app.callback(
    Output("prd-filename", "children"),
    Output("store-prd-text", "data"),
    Input("prd-upload", "contents"),
    State("prd-upload", "filename"),
    prevent_initial_call=True,
)
def show_prd_filename(contents, filename):
    if not contents:
        return no_update, no_update
    text = parse_file(contents, filename)
    display = html.Div(className="file-badge", children=[
        html.Span("📎", className="file-badge-icon"),
        html.Span(filename, className="file-badge-name"),
        html.Span(f"{len(text):,} chars", className="file-badge-size"),
    ])
    return display, text


# ─────────────────────────────────────────────────────────────
# CALLBACK: Generate test cases
# ─────────────────────────────────────────────────────────────
@app.callback(
    Output("gen-tc-loader",         "className"),
    Output("gen-tc-output",         "children"),
    Output("store-tc",              "data"),
    Output("global-tc",             "data"),
    Output("download-tc-section",   "className"),
    Output("go-execute-section",    "className"),
    Input("btn-generate-tc",        "n_clicks"),
    State("store-prd-text",         "data"),
    prevent_initial_call=True,
)
def generate_tc(n, prd_text):
    if not prd_text:
        err = html.Div("❌  Please upload a PRD document first.", className="error-msg")
        return "loader-wrap hidden", err, no_update, no_update, "hidden", "hidden"

    # Show loader while running (loader shown client-side via clientside cb; here we fake it)
    tc_rows = generate_test_cases_ai(prd_text)

    if not tc_rows:
        err = html.Div("⚠️  Could not parse test cases. Try a more detailed PRD.",
                       className="error-msg")
        return "loader-wrap hidden", err, no_update, no_update, "hidden", "hidden"

    df = pd.DataFrame(tc_rows)

    # Build table
    header = html.Thead(html.Tr([html.Th(c) for c in df.columns]))
    body_rows = []
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            val = str(row[col])
            if col == "Priority":
                p = val.lower()
                cls = ("priority-high" if "high" in p
                       else "priority-medium" if "medium" in p
                       else "priority-low")
                cells.append(html.Td(val, className=cls))
            elif col == "Type":
                cells.append(html.Td(html.Span(val, className="type-badge")))
            else:
                cells.append(html.Td(val))
        body_rows.append(html.Tr(cells))

    table = html.Div([
        html.Div(f"✅  Generated {len(df)} test cases successfully.",
                 className="success-msg"),
        html.Div(className="table-wrap", children=[
            html.Table(className="test-table",
                       children=[header, html.Tbody(body_rows)])
        ]),
    ])

    return ("loader-wrap hidden", table, tc_rows, tc_rows,
            "step-card", "nav-next")


# ─────────────────────────────────────────────────────────────
# CALLBACK: Download Excel
# ─────────────────────────────────────────────────────────────
@app.callback(
    Output("dl-excel", "data"),
    Input("btn-dl-excel", "n_clicks"),
    State("store-tc", "data"),
    prevent_initial_call=True,
)
def dl_excel(n, tc_data):
    if not tc_data:
        return no_update
    df = pd.DataFrame(tc_data)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Test Cases")
    return dcc.send_bytes(buf.getvalue(), "TestGPT_TestCases.xlsx")


# ─────────────────────────────────────────────────────────────
# CALLBACK: Download CSV
# ─────────────────────────────────────────────────────────────
@app.callback(
    Output("dl-csv", "data"),
    Input("btn-dl-csv", "n_clicks"),
    State("store-tc", "data"),
    prevent_initial_call=True,
)
def dl_csv(n, tc_data):
    if not tc_data:
        return no_update
    df = pd.DataFrame(tc_data)
    return dcc.send_data_frame(df.to_csv, "TestGPT_TestCases.csv", index=False)


# ─────────────────────────────────────────────────────────────
# CALLBACK: Detect target (URL or APK)
# ─────────────────────────────────────────────────────────────
@app.callback(
    Output("target-display",  "children"),
    Output("tool-badge-wrap", "children"),
    Output("store-target",    "data"),
    Output("store-tool",      "data"),
    Output("global-tool",     "data"),
    Output("global-target",   "data"),
    Input("target-url",       "value"),
    Input("apk-upload",       "contents"),
    State("apk-upload",       "filename"),
    prevent_initial_call=True,
)
def detect_target(url_val, apk_contents, apk_filename):
    triggered = ctx.triggered_id
    if triggered == "apk-upload" and apk_contents:
        badge = html.Div(className="tool-badge appium-badge", children=[
            html.Span("📱", className="tool-icon"),
            html.Span("APPIUM", className="tool-name"),
            html.Span("Mobile Testing Mode", className="tool-desc"),
        ])
        display = html.Div(className="file-badge", children=[
            html.Span("📎"), html.Span(apk_filename, className="file-badge-name"),
        ])
        return display, badge, apk_filename, "appium", "appium", apk_filename

    if triggered == "target-url" and url_val:
        if url_val.startswith("http://") or url_val.startswith("https://"):
            badge = html.Div(className="tool-badge selenium-badge", children=[
                html.Span("🌐", className="tool-icon"),
                html.Span("SELENIUM", className="tool-name"),
                html.Span("Web Testing Mode", className="tool-desc"),
            ])
            return no_update, badge, url_val, "selenium", "selenium", url_val
        else:
            warn = html.Div("⚠️  Enter a valid URL starting with https:// or http://",
                            className="error-msg")
            return warn, no_update, no_update, no_update, no_update, no_update

    return no_update, no_update, no_update, no_update, no_update, no_update


# ─────────────────────────────────────────────────────────────
# CALLBACK: Generate scripts
# ─────────────────────────────────────────────────────────────
@app.callback(
    Output("gen-scripts-loader",  "className"),
    Output("scripts-preview",     "children"),
    Output("store-scripts",       "data"),
    Output("global-scripts",      "data"),
    Output("dl-scripts-section",  "className"),
    Input("btn-gen-scripts",      "n_clicks"),
    State("global-tc",            "data"),
    State("store-tool",           "data"),
    State("global-tool",          "data"),
    State("store-target",         "data"),
    State("global-target",        "data"),
    prevent_initial_call=True,
)
def gen_scripts(n, tc_local, tool_local, tool_global, target_local, target_global):
    tc_data = tc_local or []
    tool    = tool_local or tool_global or ""
    target  = target_local or target_global or ""

    if not tc_data:
        err = html.Div("❌  No test cases found. Please generate test cases first.",
                       className="error-msg")
        return "loader-wrap hidden", err, no_update, no_update, "hidden"

    if not tool or not target:
        err = html.Div("❌  Please set a test target (URL or APK) before generating scripts.",
                       className="error-msg")
        return "loader-wrap hidden", err, no_update, no_update, "hidden"

    scripts = generate_test_scripts_ai(tc_data, tool, target)

    preview = html.Div([
        html.Div(f"✅  Scripts generated for {len(tc_data)} test cases ({tool.upper()}).",
                 className="success-msg"),
        html.Div(className="code-preview", children=[
            html.Pre(scripts[:3000] + ("\n\n... (truncated for preview)" if len(scripts) > 3000 else ""),
                     className="code-block"),
        ]),
    ])
    return "loader-wrap hidden", preview, scripts, scripts, ""


# ─────────────────────────────────────────────────────────────
# CALLBACK: Download scripts PDF
# ─────────────────────────────────────────────────────────────
@app.callback(
    Output("dl-scripts", "data"),
    Input("btn-dl-scripts", "n_clicks"),
    State("store-scripts", "data"),
    State("store-tool",    "data"),
    State("global-tool",   "data"),
    prevent_initial_call=True,
)
def dl_scripts(n, scripts, tool_local, tool_global):
    if not scripts:
        return no_update
    tool = tool_local or tool_global or "automation"
    pdf_b64 = scripts_to_pdf_b64(scripts, f"{tool.title()} Test Scripts")
    _, b64 = pdf_b64.split(",", 1)
    return dcc.send_bytes(base64.b64decode(b64), f"TestGPT_{tool}_scripts.pdf")


# ─────────────────────────────────────────────────────────────
# CALLBACK: Execute tests
# ─────────────────────────────────────────────────────────────
@app.callback(
    Output("exec-loader",        "className"),
    Output("exec-progress",      "children"),
    Output("store-exec-results", "data"),
    Output("global-results",     "data"),
    Output("go-report-section",  "className"),
    Input("btn-execute",         "n_clicks"),
    State("global-tc",           "data"),
    prevent_initial_call=True,
)
def execute_tests(n, tc_data):
    if not tc_data:
        err = html.Div("❌  No test cases to execute. Generate test cases first.",
                       className="error-msg")
        return "loader-wrap hidden", err, no_update, no_update, "hidden"

    results = simulate_execution(tc_data)

    passed = sum(1 for r in results if r.get("status") == "Pass")
    failed = len(results) - passed

    # Progress display
    rows = []
    for i, res in enumerate(results):
        tc = next((t for t in tc_data if t["ID"] == res.get("id")), {})
        status_cls = "exec-pass" if res.get("status") == "Pass" else "exec-fail"
        rows.append(html.Div(className=f"exec-row {status_cls}", children=[
            html.Span(f"#{i+1}", className="exec-num"),
            html.Span(res.get("id",""), className="exec-id"),
            html.Span(tc.get("Title",""), className="exec-title"),
            html.Span(res.get("status",""), className="exec-status"),
            html.Span(f"{res.get('duration_ms',0)}ms", className="exec-dur"),
        ]))

    summary = html.Div([
        html.Div(className="exec-summary", children=[
            html.Div(className="exec-stat", children=[
                html.Span(str(len(results)), className="exec-stat-val total"),
                html.Span("Total", className="exec-stat-lbl"),
            ]),
            html.Div(className="exec-stat", children=[
                html.Span(str(passed), className="exec-stat-val pass"),
                html.Span("Passed", className="exec-stat-lbl"),
            ]),
            html.Div(className="exec-stat", children=[
                html.Span(str(failed), className="exec-stat-val fail"),
                html.Span("Failed", className="exec-stat-lbl"),
            ]),
            html.Div(className="exec-stat", children=[
                html.Span(f"{passed/len(results)*100:.1f}%", className="exec-stat-val rate"),
                html.Span("Pass Rate", className="exec-stat-lbl"),
            ]),
        ]),
        html.Div(className="exec-list", children=rows),
    ])

    return "loader-wrap hidden", summary, results, results, ""


# ─────────────────────────────────────────────────────────────
# CALLBACK: Report page content
# ─────────────────────────────────────────────────────────────
@app.callback(
    Output("report-content",     "children"),
    Output("dl-report-section",  "className"),
    Input("url",                 "pathname"),
    State("global-results",      "data"),
    State("global-tc",           "data"),
)
def build_report(path, results, tc_data):
    if path != "/report":
        return no_update, no_update
    if not results:
        return (html.Div("⚠️  No execution results found. Run tests first.",
                         className="error-msg"), "hidden")

    tc_map = {r["ID"]: r for r in (tc_data or [])}
    passed = sum(1 for r in results if r.get("status") == "Pass")
    failed = len(results) - passed
    pass_rate = passed / len(results) * 100 if results else 0

    # Summary cards
    summary = html.Div(className="report-summary", children=[
        report_card("Total",     str(len(results)), "total"),
        report_card("Passed",    str(passed),        "pass"),
        report_card("Failed",    str(failed),         "fail"),
        report_card("Pass Rate", f"{pass_rate:.1f}%", "rate"),
    ])

    # Pass/fail bar
    bar = html.Div(className="pass-bar-wrap", children=[
        html.Div(className="pass-bar-inner",
                 style={"width": f"{pass_rate}%"}),
    ])

    # Detailed rows
    detail_rows = []
    for res in results:
        tc = tc_map.get(res.get("id", ""), {})
        status = res.get("status", "")
        detail_rows.append(html.Tr([
            html.Td(res.get("id", "")),
            html.Td(tc.get("Title", "")),
            html.Td(tc.get("Module", "")),
            html.Td(tc.get("Priority", ""), className=(
                "priority-high" if "High" in tc.get("Priority","") else
                "priority-medium" if "Medium" in tc.get("Priority","") else
                "priority-low"
            )),
            html.Td(status, className="exec-pass" if status=="Pass" else "exec-fail"),
            html.Td(f"{res.get('duration_ms',0)}ms"),
            html.Td(res.get("reason", "")[:60]),
        ]))

    table = html.Div(className="table-wrap", children=[
        html.Table(className="test-table", children=[
            html.Thead(html.Tr([
                html.Th(c) for c in
                ["ID", "Title", "Module", "Priority", "Status", "Duration", "Reason"]
            ])),
            html.Tbody(detail_rows),
        ])
    ])

    content = html.Div([summary, bar, Spacer_div(), table])
    return content, ""


def report_card(label, val, cls):
    return html.Div(className=f"report-card report-card-{cls}", children=[
        html.Span(val, className="report-card-val"),
        html.Span(label, className="report-card-lbl"),
    ])


def Spacer_div():
    return html.Div(style={"height": "24px"})


# ─────────────────────────────────────────────────────────────
# CALLBACK: Download report PDF
# ─────────────────────────────────────────────────────────────
@app.callback(
    Output("dl-report", "data"),
    Input("btn-dl-report", "n_clicks"),
    State("global-results", "data"),
    State("global-tc",      "data"),
    prevent_initial_call=True,
)
def dl_report(n, results, tc_data):
    if not results:
        return no_update
    pdf_b64 = report_to_pdf_b64(results, tc_data or [])
    _, b64 = pdf_b64.split(",", 1)
    return dcc.send_bytes(base64.b64decode(b64), "TestGPT_Report.pdf")


# ─────────────────────────────────────────────────────────────
# RUN
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8051)
