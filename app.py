#!/usr/bin/env python3
"""
Yvette Stock Host — public dashboard + open API for your tools
No keys. Domain shows cool live stock / generated counts only.
"""

from __future__ import annotations

import os
import json
import random
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

DATA_DIR = Path(os.getenv("DATA_DIR", "/data" if Path("/data").exists() else "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
STOCK_FILE = DATA_DIR / "stock.json"
USED_FILE = DATA_DIR / "used.json"

def _load(path: Path) -> list:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []

def _save(path: Path, data: list):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    tmp.replace(path)

def get_stock() -> list:
    return _load(STOCK_FILE)

def get_used() -> set:
    return set(str(x).lower() for x in _load(USED_FILE))

def save_stock(names: list):
    _save(STOCK_FILE, names)

def save_used(used: set):
    _save(USED_FILE, sorted(used))

# ── PUBLIC DASHBOARD ONLY ─────────────────────────────────────────────────
PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Yvette Upass — Live Stock</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
  :root {
    --bg: #000000;
    --green: #00ff41;
    --green-dim: #00cc33;
    --red: #ff0033;
    --yellow: #ffcc00;
    --muted: #3a3a3a;
    --card: #070707;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    min-height: 100vh;
    background: var(--bg);
    color: #c8ffc8;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    display: flex;
    align-items: center;
    justify-content: center;
    background-image:
      linear-gradient(rgba(0,255,65,0.035) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,255,65,0.035) 1px, transparent 1px);
    background-size: 28px 28px;
  }
  .shell {
    width: min(520px, 94vw);
    border: 1px solid #0a5c1a;
    background: rgba(0,0,0,0.94);
    box-shadow:
      0 0 0 1px rgba(0,255,65,0.08),
      0 0 60px rgba(0,255,65,0.08),
      inset 0 0 80px rgba(0,255,65,0.03);
  }
  .banner {
    background: linear-gradient(90deg, #cc0022, #ff0033 40%, #cc0022);
    color: #fff;
    text-align: center;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 3px;
    padding: 10px 12px;
    text-transform: uppercase;
  }
  .logo {
    text-align: center;
    padding: 32px 16px 4px;
    font-size: 28px;
    font-weight: 700;
    color: var(--green);
    letter-spacing: 6px;
    text-shadow: 0 0 18px rgba(0,255,65,0.55);
  }
  .sub {
    text-align: center;
    color: #4a4a4a;
    font-size: 11px;
    letter-spacing: 2px;
    padding-bottom: 22px;
  }
  .status {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 11px;
    color: var(--green-dim);
    margin-bottom: 18px;
  }
  .dot {
    width: 9px; height: 9px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 10px var(--green);
    animation: pulse 1.5s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.45; transform: scale(0.85); }
  }
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: #0a5c1a;
    margin: 0 18px 18px;
  }
  .card {
    background: var(--card);
    padding: 26px 12px 22px;
    text-align: center;
  }
  .label {
    font-size: 10px;
    color: #555;
    letter-spacing: 2.5px;
    margin-bottom: 12px;
  }
  .value {
    font-size: 30px;
    font-weight: 700;
    color: var(--green);
    text-shadow: 0 0 14px rgba(0,255,65,0.4);
    font-variant-numeric: tabular-nums;
  }
  .card.used .value {
    color: var(--yellow);
    text-shadow: 0 0 14px rgba(255,204,0,0.35);
  }
  .footer {
    border-top: 1px solid #111;
    text-align: center;
    padding: 14px;
    font-size: 10px;
    color: #333;
    letter-spacing: 1px;
  }
</style>
</head>
<body>
  <div class="shell">
    <div class="banner">Yvette Upass Gen — Live Stock Monitor</div>
    <div class="logo">YVETTE</div>
    <div class="sub">STOCK DASHBOARD</div>
    <div class="status"><span class="dot"></span> SYSTEM ONLINE</div>
    <div class="grid">
      <div class="card">
        <div class="label">NAME STOCKS</div>
        <div class="value" id="stock">{{ stock }}</div>
      </div>
      <div class="card used">
        <div class="label">GENERATED</div>
        <div class="value" id="used">{{ used }}</div>
      </div>
    </div>
    <div class="footer">AUTO REFRESH · 10s</div>
  </div>
  <script>
    async function tick() {
      try {
        const j = await (await fetch('/api/stats')).json();
        document.getElementById('stock').textContent = Number(j.stock || 0).toLocaleString();
        document.getElementById('used').textContent = Number(j.used || 0).toLocaleString();
      } catch (e) {}
    }
    setInterval(tick, 10000);
  </script>
</body>
</html>
"""

@app.get("/")
def index():
    return render_template_string(
        PAGE,
        stock=f"{len(get_stock()):,}",
        used=f"{len(get_used()):,}",
    )

@app.get("/api/stats")
def api_stats():
    return jsonify({"stock": len(get_stock()), "used": len(get_used())})

@app.get("/health")
def health():
    return "ok", 200

# ── OPEN API for your generator / admin (no key) ──────────────────────────
@app.get("/api/stock")
def api_stock():
    names = get_stock()
    return jsonify({"names": names, "count": len(names)})

@app.post("/api/stock/add")
def api_stock_add():
    existing = {n.lower() for n in get_stock()}
    incoming = []
    if request.is_json:
        incoming = request.json.get("names") or []
    else:
        text = request.get_data(as_text=True) or ""
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "," in line:
                incoming.extend(p.strip() for p in line.split(",") if p.strip())
            else:
                incoming.append(line)

    clean = []
    for raw in incoming:
        cleaned = "".join(c for c in str(raw) if c.isalpha() or c in " -'")
        cleaned = cleaned.replace(" ", "").replace("'", "").replace("-", "")
        if not cleaned.isalpha() or len(cleaned) < 2 or len(cleaned) > 24:
            continue
        title = cleaned[0].upper() + cleaned[1:].lower()
        if title.lower() in existing:
            continue
        existing.add(title.lower())
        clean.append(title)

    if clean:
        stock = get_stock()
        stock.extend(clean)
        save_stock(stock)

    return jsonify({
        "added": len(clean),
        "skipped": max(0, len(incoming) - len(clean)),
        "total": len(get_stock()),
    })

@app.get("/api/used")
def api_used():
    used = list(get_used())
    return jsonify({"used": used, "count": len(used)})

@app.post("/api/used/add")
def api_used_add():
    body = request.get_json(silent=True) or {}
    users = body.get("users") or body.get("combos") or []
    used = get_used()
    before = len(used)
    for u in users:
        if not u:
            continue
        name = str(u).split(":", 1)[0].strip().lower()
        if name:
            used.add(name)
    save_used(used)
    return jsonify({"added": len(used) - before, "total": len(used)})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
