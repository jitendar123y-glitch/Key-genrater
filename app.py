from flask import Flask, request, render_template_string
import random
import string
import json
import os

app = Flask(__name__)
DB_FILE = "notes.json"

# ======================= HTML TEMPLATES =======================
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>N0tes - Share Text</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a1a;
            color: #fff;
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        .header { text-align: center; padding: 30px 0; }
        .header h1 { font-size: 36px; color: #00ff9d; }
        .container {
            background: #111133;
            border-radius: 15px;
            padding: 30px;
            max-width: 600px;
            width: 100%;
            border: 1px solid #00ff9d33;
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
        }
        .result {
            background: #000;
            border: 2px dashed #00ff9d;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            word-break: break-all;
            font-size: 18px;
            color: #00ff9d;
            display: {{ 'block' if show else 'none' }};
        }
        .copy-btn {
            background: #00ff9d22;
            color: #00ff9d;
            border: 1px solid #00ff9d44;
            padding: 8px 20px;
            border-radius: 20px;
            cursor: pointer;
            margin-top: 10px;
            display: {{ 'inline-block' if show else 'none' }};
        }
        .footer { color: #555; font-size: 12px; margin-top: 30px; }
        .footer a { color: #00bfff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📝 N0tes</h1>
        <p style="color:#888;">Share text instantly</p>
    </div>
    
    <div class="container">
        <form method="POST" action="/">
            <textarea name="text" placeholder="Type your text here...">{{ saved }}</textarea>
            <button type="submit" class="btn">🚀 Create Note</button>
        </form>
        
        {% if show %}
        <div class="result" id="resultBox">
            <strong>🔗 Link:</strong> {{ url }}
        </div>
        <button class="copy-btn" onclick="copyLink('{{ url }}')">📋 Copy Link</button>
        {% endif %}
    </div>
    
    <div class="footer">
        Powered by <a href="https://t.me/eaglescrip">@eaglescrip</a>
    </div>
    
    <script>
        function copyLink(url) {
            navigator.clipboard.writeText(url);
            alert('✅ Link copied!');
        }
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
    <title>Your Key - EAGLE SCRIPT</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a1a;
            color: #fff;
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 10px;
        }
        .container { max-width: 500px; width: 100%; }
        .header {
            background: #111133;
            text-align: center;
            padding: 15px;
            border-radius: 15px 15px 0 0;
            border: 1px solid #00ff9d33;
        }
        .header h2 { color: #00ff9d; font-size: 20px; }
        
        .ad-box {
            background: #ffffff05;
            border: 1px solid #ffffff10;
            border-radius: 10px;
            text-align: center;
            padding: 5px;
            margin: 5px 0;
            min-height: 250px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .key-section {
            background: #111133;
            padding: 20px;
            text-align: center;
            border: 1px solid #00ff9d33;
        }
        .key-box {
            background: #000;
            border: 2px dashed #00ff9d;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
        }
        .key-text {
            font-size: 32px;
            font-weight: bold;
            color: #00ff9d;
            letter-spacing: 3px;
            user-select: all;
            word-break: break-all;
        }
        .copy-btn {
            background: linear-gradient(135deg, #00ff9d, #00bfff);
            color: #000;
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 50px;
            cursor: pointer;
            margin: 10px 0;
        }
        .copy-btn:hover { transform: scale(1.05); }
        .copied {
            color: #00ff9d;
            display: none;
            margin-top: 5px;
        }
        .instructions { color: #888; font-size: 14px; margin: 10px 0; }
        .footer {
            background: #111133;
            text-align: center;
            padding: 10px;
            border-radius: 0 0 15px 15px;
            border: 1px solid #00ff9d33;
            font-size: 12px;
            color: #666;
        }
        .footer a { color: #00bfff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        
        <!-- HEADER -->
        <div class="header">
            <h2>🦅 EAGLE SCRIPT KEY</h2>
        </div>
        
        <!-- AD 1: 300x250 -->
        <div class="ad-box">
            <script>
              atOptions = {
                'key' : 'e2ca8421d3063469d5d96a332a4b7013',
                'format' : 'iframe',
                'height' : 250,
                'width' : 300,
                'params' : {}
              };
            </script>
            <script src="https://www.highperformanceformat.com/e2ca8421d3063469d5d96a332a4b7013/invoke.js"></script>
        </div>
        
        <!-- KEY SECTION -->
        <div class="key-section">
            <p class="instructions">👇 Copy this key and paste in script:</p>
            <div class="key-box">
                <div class="key-text">{{ key }}</div>
            </div>
            <button class="copy-btn" onclick="copyKey()">📋 Copy Key</button>
            <div class="copied" id="copiedMsg">✅ Copied!</div>
        </div>
        
        <!-- AD 2: 160x300 -->
        <div class="ad-box" style="min-height:300px;">
            <script>
              atOptions = {
                'key' : 'fa9ec17e17f6ab6999d105123e4520c0',
                'format' : 'iframe',
                'height' : 300,
                'width' : 160,
                'params' : {}
              };
            </script>
            <script src="https://www.highperformanceformat.com/fa9ec17e17f6ab6999d105123e4520c0/invoke.js"></script>
        </div>
        
        <!-- AD 3: Native -->
        <div class="ad-box" style="min-height:100px;">
            <script async="async" data-cfasync="false" src="https://pl29374836.profitablecpmratenetwork.com/9c852a112e271c7b2bb904d720b767ec/invoke.js"></script>
            <div id="container-9c852a112e271c7b2bb904d720b767ec"></div>
        </div>
        
        <!-- FOOTER -->
        <div class="footer">
            Join: <a href="https://t.me/eaglescrip">@eaglescrip</a>
        </div>
        
    </div>
    
    <script>
        function copyKey() {
            const key = "{{ key }}";
            navigator.clipboard.writeText(key).then(() => {
                const msg = document.getElementById('copiedMsg');
                msg.style.display = 'block';
                setTimeout(() => msg.style.display = 'none', 2000);
            });
        }
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
    url = ""
    show = False
    saved = ""
    
    if request.method == 'POST':
        text = request.form.get('text', '')
        if text:
            db = load_db()
            code = gen_code()
            db[code] = text
            save_db(db)
            base = request.host_url.rstrip('/')
            url = f"{base}/{code}"
            show = True
            saved = text
    
    return render_template_string(HOME_TEMPLATE, url=url, show=show, saved=saved)

@app.route('/<code>')
def view(code):
    db = load_db()
    key = db.get(code, "KEY_NOT_FOUND")
    return render_template_string(VIEW_TEMPLATE, key=key)

@app.route('/api/create', methods=['POST'])
def api_create():
    text = request.json.get('text', '')
    if not text: return {"error": "Text required"}, 400
    db = load_db()
    code = gen_code()
    db[code] = text
    save_db(db)
    return {"url": f"{request.host_url.rstrip('/')}/{code}", "code": code}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
