from flask import Flask, request, redirect, render_template_string
import random
import string
import json
import os

app = Flask(__name__)
DB_FILE = "notes.json"

# ======================= HTML TEMPLATE =======================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>N0tes - Share Text</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0a0a1a, #111133);
            color: #fff;
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 30px 0;
            width: 100%;
            max-width: 800px;
        }
        .header h1 { font-size: 36px; color: #00ff9d; margin-bottom: 10px; }
        .header p { color: #888; font-size: 14px; }
        
        .container {
            background: #111133;
            border-radius: 15px;
            padding: 30px;
            max-width: 800px;
            width: 100%;
            border: 1px solid #00ff9d33;
            margin-bottom: 20px;
        }
        
        textarea {
            width: 100%;
            height: 200px;
            background: #0a0a1a;
            border: 1px solid #00ff9d44;
            border-radius: 10px;
            color: #fff;
            padding: 15px;
            font-size: 16px;
            font-family: 'Courier New', monospace;
            resize: vertical;
        }
        textarea:focus { outline: none; border-color: #00ff9d; }
        
        .btn {
            background: linear-gradient(135deg, #00ff9d, #00bfff);
            color: #000;
            border: none;
            padding: 12px 30px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 50px;
            cursor: pointer;
            margin-top: 15px;
            transition: 0.3s;
        }
        .btn:hover { transform: scale(1.05); }
        
        .result {
            background: #000;
            border: 2px dashed #00ff9d;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            word-break: break-all;
            font-size: 18px;
            color: #00ff9d;
            display: {{ 'block' if show_result else 'none' }};
        }
        
        .copy-btn {
            background: #00ff9d22;
            color: #00ff9d;
            border: 1px solid #00ff9d44;
            padding: 8px 20px;
            border-radius: 20px;
            cursor: pointer;
            margin-top: 10px;
            font-size: 14px;
            display: {{ 'inline-block' if show_result else 'none' }};
        }
        
        .ad-banner {
            background: #ffffff10;
            border: 1px solid #ffffff22;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            color: #666;
            margin: 15px 0;
            max-width: 800px;
            width: 100%;
        }
        
        .footer { color: #555; font-size: 12px; margin-top: 30px; text-align: center; }
        .footer a { color: #00bfff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📝 N0tes</h1>
        <p>Share text instantly. Free & Anonymous.</p>
    </div>
    
    <!-- Ad Banner -->
    <div class="ad-banner">
        <script src="https://cdn.adpushup.com/ad.js"></script>
    </div>
    
    <div class="container">
        <h2 style="margin-bottom:15px;">✍️ Create New Note</h2>
        <form method="POST" action="/">
            <textarea name="text" placeholder="Type your text here...">{{ saved_text }}</textarea>
            <button type="submit" class="btn">🚀 Create Note</button>
        </form>
        
        {% if show_result %}
        <div class="result" id="resultBox">
            <strong>🔗 Share Link:</strong><br>
            <span id="shareLink">{{ share_url }}</span>
        </div>
        <button class="copy-btn" onclick="copyLink('{{ share_url }}')">📋 Copy Link</button>
        {% endif %}
    </div>
    
    <!-- Ad Banner -->
    <div class="ad-banner">
        <script src="https://cdn.adpushup.com/ad.js"></script>
    </div>
    
    <div class="footer">
        Powered by <a href="https://t.me/eaglescrip">@eaglescrip</a>
    </div>
    
    <script>
        function copyLink(url) {
            navigator.clipboard.writeText(url);
            alert('✅ Link copied!');
        }
        
        // Popup ad
        setTimeout(function() {
            window.open('https://google.com', '_blank', 'width=400,height=300');
        }, 3000);
    </script>
</body>
</html>
"""

VIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Note {{ code }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0a0a1a, #111133);
            color: #fff;
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: #111133;
            border-radius: 15px;
            padding: 30px;
            max-width: 800px;
            width: 100%;
            border: 1px solid #00ff9d33;
            margin-top: 50px;
        }
        .note-content {
            background: #000;
            border: 1px solid #00ff9d44;
            border-radius: 10px;
            padding: 20px;
            font-size: 18px;
            white-space: pre-wrap;
            word-break: break-word;
            color: #fff;
            min-height: 150px;
        }
        .ad-banner {
            background: #ffffff10;
            border: 1px solid #ffffff22;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            color: #666;
            margin: 15px 0;
            max-width: 800px;
            width: 100%;
        }
        .footer { color: #555; font-size: 12px; margin-top: 30px; text-align: center; }
        .footer a { color: #00bfff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="ad-banner">
        <script src="https://cdn.adpushup.com/ad.js"></script>
    </div>
    
    <div class="container">
        <h2 style="color:#00ff9d;margin-bottom:15px;">📄 Note: {{ code }}</h2>
        <div class="note-content">{{ text }}</div>
    </div>
    
    <div class="ad-banner">
        <script src="https://cdn.adpushup.com/ad.js"></script>
    </div>
    
    <p><a href="/" style="color:#00bfff;">✍️ Create your own note</a></p>
    
    <div class="footer">
        Powered by <a href="https://t.me/eaglescrip">@eaglescrip</a>
    </div>
    
    <script>
        setTimeout(function() {
            window.open('https://google.com', '_blank', 'width=400,height=300');
        }, 2000);
    </script>
</body>
</html>
"""

# ======================= HELPERS =======================
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, 'w') as f: json.dump(db, f)

def gen_code(length=6):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

# ======================= ROUTES =======================
@app.route('/', methods=['GET', 'POST'])
def home():
    share_url = ""
    show_result = False
    saved_text = ""
    
    if request.method == 'POST':
        text = request.form.get('text', '')
        if text:
            db = load_db()
            code = gen_code()
            db[code] = text
            save_db(db)
            base = request.host_url.rstrip('/')
            share_url = f"{base}/{code}"
            show_result = True
            saved_text = text
    
    return render_template_string(HTML_TEMPLATE, 
                                   share_url=share_url, 
                                   show_result=show_result,
                                   saved_text=saved_text)

@app.route('/<code>')
def view(code):
    db = load_db()
    text = db.get(code, "Note not found!")
    return render_template_string(VIEW_TEMPLATE, code=code, text=text)

@app.route('/api/create', methods=['POST'])
def api_create():
    """API endpoint for scripts"""
    text = request.json.get('text', '')
    if not text:
        return {"error": "Text required"}, 400
    
    db = load_db()
    code = gen_code()
    db[code] = text
    save_db(db)
    
    base = request.host_url.rstrip('/')
    return {"url": f"{base}/{code}", "code": code}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
