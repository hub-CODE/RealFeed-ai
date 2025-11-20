# app.py
from flask import Flask, request, render_template_string
import requests
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- CONFIG ----------------
NEWS_API_KEY = "6e5374b8437f415a9055a8f0d08f58de"
FALLBACK_HEADLINES = [
    "Scientists find new method to recycle plastic",
    "Major tech company announces AI research breakthrough",
    "Global markets respond to policy changes",
    "Climate summit reaches new agreement on emissions",
    "Breakthrough in renewable energy storage technology",
]

# ---------------- FLASK APP ----------------
app = Flask(__name__)

# ---------------- HF PREDICT SETUP ----------------
HF_TOKEN = os.environ.get("HF_TOKEN")
logger.info(f"HF_TOKEN present: {bool(HF_TOKEN)}")

# Use a model specifically trained for fake news detection
model_id = "ghanashyamvtatti/fake-news-bert-base-uncased"  # Actually trained for fake news detection
API_URL = f"https://api-inference.huggingface.co/models/{model_id}"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}" if HF_TOKEN else "",
    "Content-Type": "application/json"
}

def smart_fallback_classification(text):
    """Smart fallback classification specifically tuned for fake news detection"""
    if not text:
        return "UNVERIFIED", 0.0
    
    text_lower = text.lower()
    
    # Strong indicators of potentially fake news
    strong_fake_indicators = [
        'fake', 'false', 'hoax', 'conspiracy', 'debunked', 'misleading',
        'scam', 'fraud', 'clickbait', 'satire', 'parody', 'phishing'
    ]
    
    # Moderate indicators of potentially fake news
    moderate_fake_indicators = [
        'rumor', 'unverified', 'bogus', 'unconfirmed', 'allegedly',
        'shocking', 'you won\'t believe', 'breaking!', 'urgent!',
        'secret', 'they don\'t want you to know', 'hidden truth'
    ]
    
    # Strong indicators of credible news
    strong_real_indicators = [
        'study', 'research', 'scientists', 'experts', 'official',
        'confirmed', 'report', 'data', 'analysis', 'findings',
        'peer-reviewed', 'journal', 'university', 'according to study'
    ]
    
    # Moderate indicators of credible news
    moderate_real_indicators = [
        'announced', 'published', 'discovery', 'breakthrough',
        'according to', 'source said', 'report shows', 'data shows'
    ]
    
    # Calculate scores
    fake_score = (
        sum(3 for keyword in strong_fake_indicators if keyword in text_lower) +
        sum(1 for keyword in moderate_fake_indicators if keyword in text_lower)
    )
    
    real_score = (
        sum(3 for keyword in strong_real_indicators if keyword in text_lower) +
        sum(1 for keyword in moderate_real_indicators if keyword in text_lower)
    )
    
    # Determine classification
    if fake_score > real_score:
        confidence = min(70 + (fake_score * 8), 95)
        return "FAKE", confidence
    elif real_score > fake_score:
        confidence = min(75 + (real_score * 7), 95)
        return "REAL", confidence
    else:
        # Tie or no clear indicators - be conservative
        return "REAL", 60.0

def hf_predict(text):
    """Classify news headline using Hugging Face model"""
    if not HF_TOKEN:
        logger.warning("HF_TOKEN not set, using fallback")
        return smart_fallback_classification(text)
    
    if not text or text == "[Removed]":
        return "UNVERIFIED", 0.0

    payload = {"inputs": text}
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 404:
            logger.error(f"Model {model_id} not found, using fallback")
            return smart_fallback_classification(text)
        elif response.status_code == 503:
            logger.info("Model is loading, please try again in a few seconds")
            return "LOADING", 50.0
        elif response.status_code != 200:
            logger.error(f"HF API Error {response.status_code}: {response.text}")
            return smart_fallback_classification(text)

        data = response.json()
        
        # Handle response from fake news detection model
        if isinstance(data, list) and len(data) > 0:
            prediction = data[0]
            label = prediction.get('label', 'UNKNOWN')
            score = prediction.get('score', 0.0)
            
            # For fake news detection models, labels are usually 'FAKE'/'REAL' or 'LABEL_0'/'LABEL_1'
            # Map the labels properly based on the model's training
            if label.upper() in ['FAKE', 'LABEL_1', 'INACCURATE']:
                return "FAKE", round(score * 100, 2)
            else:  # REAL, LABEL_0, or ACCURATE
                return "REAL", round(score * 100, 2)
                
        else:
            logger.warning(f"Unexpected response format: {data}")
            return smart_fallback_classification(text)

    except requests.exceptions.Timeout:
        logger.error("HF API request timeout")
        return smart_fallback_classification(text)
    except Exception as e:
        logger.error(f"Error in hf_predict: {e}")
        return smart_fallback_classification(text)

# ---------------- HELPERS ----------------
def get_latest_headlines(query="", page_size=6):
    """Fetch latest headlines from NewsAPI"""
    if query:
        # Use everything endpoint for search queries
        base_url = "https://newsapi.org/v2/everything"
        params = {
            "apiKey": NEWS_API_KEY,
            "pageSize": page_size, 
            "language": "en",
            "sortBy": "relevancy",
            "q": query
        }
    else:
        # Use top-headlines for general news
        base_url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": NEWS_API_KEY,
            "pageSize": page_size, 
            "language": "en",
            "country": "us"
        }
        
    try:
        response = requests.get(base_url, params=params, timeout=10)
        logger.info(f"NewsAPI request to: {base_url}")
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            logger.info(f"Found {len(articles)} articles")
            
            processed_articles = []
            for article in articles:
                title = article.get("title", "").strip()
                if title and title != "[Removed]":
                    published = article.get("publishedAt", "")
                    if published:
                        try:
                            # Format date nicely
                            date_obj = datetime.fromisoformat(published.replace('Z', '+00:00'))
                            published = date_obj.strftime("%b %d, %Y")
                        except:
                            published = published[:10]
                    else:
                        published = "Recent"
                        
                    processed_articles.append({
                        "title": title,
                        "source": article.get("source", {}).get("name", "Unknown"),
                        "published": published
                    })
            return processed_articles
        else:
            logger.error(f"NewsAPI error {response.status_code}: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error fetching headlines: {e}")
        return []

def create_fallback_results(query=""):
    """Create fallback results when no news is found"""
    if query:
        # Generate relevant fallback headlines based on query
        fallback_headlines = [
            f"Latest developments in {query} industry",
            f"New research reveals insights about {query}",
            f"Experts discuss future of {query}",
            f"Breaking: Major announcement regarding {query}",
            f"Market trends show growth in {query} sector",
            f"International conference focuses on {query} innovations"
        ]
    else:
        fallback_headlines = FALLBACK_HEADLINES
    
    return [{"title": h, "source": "Sample", "published": "Today"} for h in fallback_headlines]

# ---------------- ROUTES ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    """Main route for the application"""
    query = request.form.get("query", "").strip() if request.method == "POST" else ""
    results = []
    error_msg = None
    show_demo_notice = not bool(HF_TOKEN)

    try:
        # Fetch headlines
        headlines = get_latest_headlines(query=query or None)
        
        if not headlines:
            # Use fallback headlines
            headlines = create_fallback_results(query)
            if query:
                error_msg = f"No recent news found for '{query}'. Showing sample headlines for demonstration."
            else:
                error_msg = "Unable to fetch latest news. Showing sample headlines."

        # Classify each headline
        for headline in headlines:
            label, confidence = hf_predict(headline["title"])
            results.append({
                "title": headline["title"],
                "source": headline.get("source", "Unknown"),
                "published": headline.get("published", "Recent"),
                "label": label,
                "confidence": confidence
            })

    except Exception as e:
        logger.error(f"Error in main route: {e}")
        error_msg = "A temporary error occurred. Please try again in a few moments."
        # Still show fallback results even on error
        headlines = create_fallback_results(query)
        for headline in headlines:
            label, confidence = hf_predict(headline["title"])
            results.append({
                "title": headline["title"],
                "source": headline.get("source", "Unknown"),
                "published": headline.get("published", "Recent"),
                "label": label,
                "confidence": confidence
            })

    return render_template_string(
        HTML_TEMPLATE, 
        results=results, 
        query=query, 
        error_msg=error_msg,
        hf_token_configured=bool(HF_TOKEN)
    )

@app.route("/classify", methods=["POST"])
def classify_text():
    """Direct classification endpoint for custom text"""
    data = request.get_json()
    text = data.get("text", "").strip()
    
    if not text:
        return {"error": "No text provided"}, 400
    
    label, confidence = hf_predict(text)
    
    return {
        "text": text,
        "label": label,
        "confidence": confidence,
        "is_demo": not bool(HF_TOKEN)
    }

@app.route("/test-classify")
def test_classify():
    """Test endpoint to verify classification is working"""
    test_texts = [
        "Scientists discover new planet in habitable zone",
        "Fake news about celebrity death spreads online",
        "Breaking news: Major earthquake reported",
        "This is completely made up conspiracy theory",
        "New study shows benefits of renewable energy",
        "Viral hoax about alien invasion debunked by experts",
        "Official report confirms economic growth data",
        "Clickbait story about miracle cure proven false"
    ]
    
    results = []
    for text in test_texts:
        label, confidence = hf_predict(text)
        results.append({
            "text": text,
            "label": label,
            "confidence": confidence,
            "using_hf_token": bool(HF_TOKEN)
        })
    
    return {
        "test_results": results,
        "hf_token_configured": bool(HF_TOKEN),
        "model": model_id,
        "api_url": API_URL
    }

@app.route("/debug")
def debug():
    """Debug endpoint to check environment variables"""
    debug_info = {
        "hf_token_set": bool(os.environ.get("HF_TOKEN")),
        "hf_token_length": len(os.environ.get("HF_TOKEN", "")),
        "model_id": model_id,
        "api_url": API_URL,
        "news_api_key_set": bool(NEWS_API_KEY)
    }
    return debug_info

@app.route("/health")
def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "service": "RealFeed", "hf_token_configured": bool(HF_TOKEN)}

# ---------------- HTML TEMPLATE ----------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>RealFeed — Verify Headlines</title>
    <style>
        :root {
            --bg1: #0a0f1a;
            --bg2: #111827;
            --card: rgba(255, 255, 255, 0.05);
            --muted: #9aa4b2;
            --accent: #7c5cff;
            --accent-light: rgba(124, 92, 255, 0.15);
            --real-color: #22c55e;
            --fake-color: #ef4444;
            --unverified-color: #6b7280;
            --loading-color: #f59e0b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(180deg, var(--bg1), var(--bg2));
            color: #e6eef8;
            min-height: 100vh;
            padding: 20px 15px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent), #9d5cff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }

        .subtitle {
            color: var(--muted);
            font-size: 1rem;
        }

        .search-card {
            background: var(--card);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 30px;
        }

        .search-form {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .search-input {
            flex: 1;
            padding: 12px 16px;
            border: none;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 16px;
            outline: none;
        }

        .search-input::placeholder {
            color: var(--muted);
        }

        .search-input:focus {
            background: rgba(255, 255, 255, 0.15);
        }

        .btn {
            background: var(--accent);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(124, 92, 255, 0.3);
        }

        .news-grid {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .news-card {
            background: var(--card);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.2s ease;
        }

        .news-card:hover {
            transform: translateY(-2px);
        }

        .news-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 15px;
            margin-bottom: 12px;
        }

        .news-title {
            flex: 1;
            font-size: 1.1rem;
            font-weight: 600;
            line-height: 1.4;
            color: #f1f5f9;
        }

        .label {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
            min-width: 100px;
            text-align: center;
            flex-shrink: 0;
        }

        .label-real {
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }

        .label-fake {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .label-unverified {
            background: rgba(107, 114, 128, 0.15);
            color: #9ca3af;
            border: 1px solid rgba(107, 114, 128, 0.3);
        }

        .label-loading {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .news-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 12px;
            font-size: 0.9rem;
            color: var(--muted);
        }

        .confidence {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .confidence-bar {
            width: 60px;
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            overflow: hidden;
        }

        .confidence-fill {
            height: 100%;
            border-radius: 3px;
            transition: width 0.5s ease;
        }

        .footer {
            text-align: center;
            margin-top: 40px;
            color: var(--muted);
            font-size: 0.9rem;
        }

        .error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #f87171;
            padding: 16px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }

        .info-message {
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #93c5fd;
            padding: 16px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }

        .demo-notice {
            background: rgba(124, 92, 255, 0.1);
            border: 1px solid rgba(124, 92, 255, 0.3);
            color: #a78bfa;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-size: 0.9rem;
        }

        @media (max-width: 768px) {
            .title { font-size: 2rem; }
            .search-form { flex-direction: column; }
            .news-header { flex-direction: column; }
            .label { align-self: flex-start; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">RealFeed</h1>
            <p class="subtitle">Verify headlines fast — search a topic or check top news</p>
        </div>

        {% if not hf_token_configured %}
        <div class="demo-notice">
            🔧 Demo Mode: Using smart keyword analysis. Add HF_TOKEN for real AI analysis.
            <br><small>Visit <a href="/test-classify" style="color: #a78bfa;">/test-classify</a> to see classification examples</small>
        </div>
        {% endif %}

        <div class="search-card">
            <form class="search-form" method="POST">
                <input class="search-input" name="query" placeholder="Enter topic (e.g., 'technology', 'politics', 'sports') or leave blank for latest news" value="{{ query | default('') }}">
                <button class="btn" type="submit">Verify Headlines</button>
            </form>
        </div>

        {% if error_msg %}
        <div class="info-message">
            {{ error_msg }}
        </div>
        {% endif %}

        <div class="news-grid">
            {% for item in results %}
            <div class="news-card">
                <div class="news-header">
                    <div class="news-title">{{ item.title }}</div>
                    <div class="label label-{{ item.label.lower() }}">{{ item.label }} {% if item.confidence > 0 %}({{ item.confidence }}%){% endif %}</div>
                </div>
                <div class="news-meta">
                    <span>{{ item.source }} • {{ item.published }}</span>
                    <div class="confidence">
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: {{ item.confidence }}%; background: {% if item.label == 'REAL' %}var(--real-color){% elif item.label == 'FAKE' %}var(--fake-color){% elif item.label == 'LOADING' %}var(--loading-color){% else %}var(--unverified-color){% endif %};"></div>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="footer">
            Built by <strong style="color: var(--accent);">Hubayl</strong> • Data from NewsAPI.org
            {% if not hf_token_configured %}
            <br><small><a href="/test-classify" style="color: var(--muted);">Test Classification</a></small>
            {% endif %}
        </div>
    </div>

    <script>
        // Animate confidence bars on page load
        document.addEventListener('DOMContentLoaded', function() {
            const bars = document.querySelectorAll('.confidence-fill');
            bars.forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = width;
                }, 100);
            });
        });
    </script>
</body>
</html>
"""

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)