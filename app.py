# app.py
from flask import Flask, request, render_template_string
import requests


# ---------------- CONFIG ----------------
NEWS_API_KEY = "6e5374b8437f415a9055a8f0d08f58de"  # NewsAPI key
LABELS_MAP = {0: "FAKE", 1: "REAL"}
FALLBACK_HEADLINES = [
    "Scientists find new method to recycle plastic",
    "Major tech company announces AI research breakthrough",
    "Global markets respond to policy changes",
]

# ---------------- FLASK APP ----------------
app = Flask(__name__)

# ---------------- HTML TEMPLATE ----------------
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RealFeed — Verify Headlines</title>
<style>
:root {
  --bg1: #0a0f1a; /* dark navy background */
  --bg2: #111827; 
  --card: rgba(255, 255, 255, 0.05); /* semi-transparent glass card */
  --muted: #9aa4b2;
  --accent: #7c5cff; /* purple accent */
  --accent-light: rgba(124, 92, 255, 0.15);
  --glass-blur: 10px;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: Inter, "Segoe UI", Roboto, system-ui, -apple-system, "Helvetica Neue", Arial;
  background: linear-gradient(180deg, var(--bg1), var(--bg2));
  color: #e6eef8;
  display: flex;
  justify-content: center;
  padding: 36px 18px;
}

.container {
  width: 100%;
  max-width: 920px;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 20px;
}
.title {
  font-size: 36px;
  color: var(--accent);
  font-weight: 700;
  text-shadow: 0 6px 18px rgba(124, 92, 255, 0.1);
}
.subtitle {
  margin-top: 4px;
  color: var(--muted);
  font-size: 14px;
}

/* Search box */
.search-wrap {
  margin: 20px 0;
  display: flex;
  justify-content: center;
}
.search-card {
  backdrop-filter: blur(var(--glass-blur));
  background: var(--card);
  border-radius: 999px;
  display: flex;
  gap: 10px;
  align-items: center;
  width: 100%;
  max-width: 820px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 16px;
  transition: all 0.3s ease;
}
.search-card:focus-within {
  border-color: var(--accent);
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  color: #e6eef8;
  font-size: 16px;
  padding: 10px 14px;
}
.search-input::placeholder { color: #7b8695; }

.topic-select {
  background: rgba(255,255,255,0.08);
  color: #d7e2f2;
  border: none;
  padding: 8px 10px;
  border-radius: 10px;
  font-size: 14px;
  outline: none;
}

.btn {
  background: var(--accent);
  color: white;
  padding: 8px 14px;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}
.btn:hover { filter: brightness(1.1); transform: translateY(-2px); }

/* Cards */
.main {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  margin-top: 30px;
}

.card {
  background: var(--card);
  backdrop-filter: blur(var(--glass-blur));
  border-radius: 18px;
  padding: 18px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255,255,255,0.08);
  transition: transform 0.3s ease;
}
.card:hover {
  transform: translateY(-5px);
}

.headline-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.headline {
  font-size: 17px;
  font-weight: 600;
  color: #eaf1ff;
  margin: 0 0 8px 0;
}
.meta {
  font-size: 13px;
  color: var(--muted);
}
.summary {
  margin-top: 8px;
  font-size: 14px;
  color: #cfe0ff;
  opacity: 0.95;
}

/* Label + progress */
.label {
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 13px;
  min-width: 90px;
  text-align: center;
}
.label-real {
  background: rgba(34,197,94,0.15);
  color: #9ff7bf;
  border: 1px solid rgba(34,197,94,0.3);
}
.label-fake {
  background: rgba(235,87,87,0.15);
  color: #ffb3b3;
  border: 1px solid rgba(235,87,87,0.3);
}

.progress-container {
  background: rgba(255,255,255,0.1);
  border-radius: 10px;
  overflow: hidden;
  height: 8px;
  margin-top: 6px;
}
.progress-bar {
  height: 100%;
  border-radius: 10px;
  background: var(--accent);
  width: 0%;
  transition: width 1s ease;
}

/* Footer */
.footer {
  margin-top: 24px;
  text-align: center;
  color: var(--muted);
  font-size: 13px;
  opacity: 0.9;
}
.footer .name {
  color: var(--accent);
  font-weight: 700;
}

/* Responsive */
@media (max-width: 600px){
  .title { font-size: 24px; }
  .search-card { padding: 10px; }
  .search-input { font-size: 14px; }
}
</style>

</head>
<body>
<div class="container">
  <div class="header">
    <div class="title">RealFeed</div>
    <div class="subtitle">Verify headlines fast — search a topic or check top news</div>
  </div>

  <div class="search-wrap">
    <form class="search-card" method="POST">
      <input class="search-input" name="query" placeholder="Enter topic or leave blank for latest news" value="{{ query | default('') }}">
      <button class="btn" type="submit">Check</button>
      {% if loading %}<span class="loader"></span>{% endif %}
    </form>
  </div>

  <div class="main">
    {% if error_msg %}<div class="card">{{ error_msg }}</div>{% endif %}

    {% for item in results %}
      <div class="card">
        <div class="headline">{{ item.title }}</div>
        <div class="meta">{{ item.source }} • {{ item.published }}</div>
        <div class="summary">{{ item.summary }}</div>
        <div style="width:120px; text-align:right;">
            <div class="label {{ 'label-real' if item.label=='REAL' else 'label-fake' }}">
                {{ item.label }}
            </div>
            <div class="confidence-bar">
                <div class="bar-fill" style="width: {{ item.confidence }}%"></div>
            </div>
            <div class="conf-text">{{ item.confidence }}%</div>
        </div>

      </div>
    {% endfor %}
  </div>

  <div class="footer">Built by <span style="color:var(--accent);font-weight:700;">Hubayl</span> • Data from NewsAPI.org</div>
</div>
<script>
document.addEventListener("DOMContentLoaded", function(){
  document.querySelectorAll(".bar-fill").forEach((bar, i) => {
    const val = parseFloat(bar.dataset.confidence) || 0;
    bar.style.width = "0%";
    // staggered animation for nicer effect
    setTimeout(() => { bar.style.width = val + "%"; }, 100 + i*80);
  });
});
</script>
</body>
</html>
"""

# ---------------- HELPERS ----------------
def get_latest_headlines(query="", page_size=5):
    base = "https://newsapi.org/v2/top-headlines"
    params = {"apiKey": NEWS_API_KEY, "pageSize": page_size, "language": "en"}
    if query: params["q"] = query
    try:
        resp = requests.get(base, params=params, timeout=8)
        if resp.status_code==200:
            articles = resp.json().get("articles", [])
            return [{"title":a.get("title") or "", "source":a.get("source",{}).get("name",""), "published":a.get("publishedAt","")[:10]} for a in articles]
        else: return []
    except: return []

def summarize(text, max_len=40):
    return text if len(text.split())<6 else (text[:max_len]+"..." if len(text)>max_len else text)

import json
from flask import jsonify

# ---------------- HF PREDICT ----------------
import requests
import os

HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/mrm8488/bert-base-cased-finetuned-fake-news"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

import requests
import os

HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/mrm8488/bert-base-cased-finetuned-fake-news"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def hf_predict(text):
    if not HF_TOKEN:
        print("ERROR: HF_TOKEN missing.")
        return "UNKNOWN", 0.0

    payload = {"inputs": text}

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        data = response.json()

        # If API is loading or error
        if isinstance(data, dict) and "error" in data:
            print("HF API Error:", data["error"])
            return "UNKNOWN", 0.0

        # Sometimes HF returns a dict with estimated time
        if isinstance(data, dict) and "estimated_time" in data:
            print("Model warming up...")
            return "UNKNOWN", 0.0

        # Normal expected format
        output = data[0][0]

        raw_label = output.get("label", "")
        confidence = round(float(output.get("score", 0.0)) * 100, 2)

        # Fix label mapping based on model docs
        if raw_label in ["LABEL_0", "0"]:
            label = "FAKE"
        else:
            label = "REAL"

        return label, confidence

    except Exception as e:
        print("Error in hf_predict:", e)
        return "UNKNOWN", 0.0


# ---------------- ROUTE ----------------
@app.route("/", methods=["GET","POST"])
def home():
    query = (request.form.get("query") or "").strip() if request.method=="POST" else ""
    results = []
    loading = False
    error_msg = None

    headlines = get_latest_headlines(query=query, page_size=6)
    if not headlines:
        if query=="": headlines = [{"title":h,"source":"Local","published":""} for h in FALLBACK_HEADLINES]
        else: error_msg="No results found or NewsAPI returned nothing."

    for h in headlines:
        title = h["title"]
        label, conf = hf_predict(title)
        results.append({
           "title": title,
           "source": h.get("source", ""),
           "published": h.get("published", ""),
           "label": label,
           "confidence": conf,
           "summary": summarize(title)
    })


    return render_template_string(html_template, results=results, query=query, error_msg=error_msg, loading=loading)

@app.route("/debug-classifier")
def debug_classifier():
    if classifier is None:
        return {"error": "classifier is None (model not loaded)"}, 500

    sample = "NASA discovers new exoplanet"
    try:
        raw = classifier(sample, top_k=3)
        print("DEBUG /debug-classifier raw:", raw)
        return {"sample": sample, "raw_output": raw}
    except Exception as e:
        print("debug error:", e)
        return {"error": str(e)}, 500


# ---------------- RUN ----------------
if __name__=="__main__":
    app.run(debug=True, port=5000)
