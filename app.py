#!/usr/bin/env python3
"""
Yvette Stock Dashboard — Railway / any host
Shows live stock + used counts. Minimal Flask app.
"""

import os
from flask import Flask, render_template_string, jsonify

try:
    import psycopg2
    HAS_PG = True
except ImportError:
    HAS_PG = False

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Yvette Upass — Stock Dashboard</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Share+Tech+Mono&display=swap');
  :root {
    --bg: #000000;
    --green: #00ff41;
    --green-dim: #00aa2a;
    --red: #ff0033;
    --gray: #1a1a1a;
    --text: #c0ffc0;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'JetBrains Mono', 'Share Tech Mono', monospace;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background-image:
      linear-gradient(rgba(0,255,65,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,255,65,0.03) 1px, transparent 1px);
    background-size: 24px 24px;
  }
  .wrap {
    width: min(520px, 94vw);
    border: 1px solid var(--green-dim);
    background: rgba(0,0,0,0.92);
    box-shadow: 0 0 40px rgba(0,255,65,0.12), inset 0 0 60px rgba(0,255,65,0.04);
  }
  .top {
    background: var(--red);
    color: #fff;
    text-align: center;
    padding: 8px 12px;
    font-weight: 700;
    letter-spacing: 2px;
    font-size: 13px;
  }
  .logo {
    text-align: center;
    padding: 28px 16px 8px;
    color: var(--green);
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 3px;
    text-shadow: 0 0 12px rgba(0,255,65,0.5);
  }
  .sub {
    text-align: center;
    color: #666;
    font-size: 11px;
    padding-bottom: 18px;
    letter-spacing: 1px;
  }
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: var(--green-dim);
    margin: 0 16px 16px;
  }
  .card {
    background: #050505;
    padding: 22px 12px;
    text-align: center;
  }
  .card .label {
    font-size: 11px;
    color: #666;
    letter-spacing: 2px;
    margin-bottom: 10px;
  }
  .card .val {
    font-size: 28px;
    font-weight: 700;
    color: var(--green);
    text-shadow: 0 0 10px rgba(0,255,65,0.4);
  }
  .card.used .val { color: #ffcc00; text-shadow: 0 0 10px rgba(255,200,0,0.3); }
  .footer {
    text-align: center;
    padding: 14px;
    font-size: 10px;
    color: #444;
    border-top: 1px solid #111;
  }
  .status {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 8px;
  }
  .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 8px var(--green);
    animation: pulse 1.6s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }
  .err { color: var(--red); text-align: center; padding: 20px; }
</style>
</head>
<body>
  <div class="wrap">
    <div class="top">YVETTE UPASS GEN — LIVE STOCK</div>
    <div class="logo">YVETTE</div>
    <div class="sub">STOCK DASHBOARD</div>
    {% if error %}
      <div class="err">{{ error }}</div>
    {% else %}
      <div style="text-align:center">
        <div class="status"><span class="dot"></span> CONNECTED</div>
      </div>
      <div class="grid">
        <div class="card">
          <div class="label">NAME STOCKS</div>
          <div class="val" id="stock">{{ stock }}</div>
        </div>
        <div class="card used">
          <div class="label">USED COMBOS</div>
          <div class="val" id="used">{{ used }}</div>
        </div>
      </div>
      <div class="footer">
        auto-refresh 15s · backend {{ backend }}
      </div>
    {% endif %}
  </div>
  <script>
    async function refresh() {
      try {
        const r = await fetch('/api/stats');
        const j = await r.json();
        if (j.stock !== undefined) document.getElementById('stock').textContent = Number(j.stock).toLocaleString();
        if (j.used !== undefined) document.getElementById('used').textContent = Number(j.used).toLocaleString();
      } catch (e) {}
    }
    setInterval(refresh, 15000);
  </script>
</body>
</html>
"""

def get_counts():
    if not DATABASE_URL or not HAS_PG:
        return None, None, "No DATABASE_URL or psycopg2 missing"
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=6)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM stock")
            stock = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM used")
            used = cur.fetchone()[0]
        conn.close()
        return stock, used, None
    except Exception as e:
        return None, None, str(e)

@app.route("/")
def index():
    stock, used, err = get_counts()
    return render_template_string(
        PAGE,
        stock=f"{stock:,}" if stock is not None else "—",
        used=f"{used:,}" if used is not None else "—",
        error=err,
        backend="postgres" if DATABASE_URL else "none",
    )

@app.route("/api/stats")
def api_stats():
    stock, used, err = get_counts()
    if err:
        return jsonify({"error": err}), 500
    return jsonify({"stock": stock, "used": used})

@app.route("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
