#!/usr/bin/env python3
# KEY GENERATOR SERVER - CUSTOM VALIDITY + KEY MANAGEMENT

from flask import Flask, request, jsonify
import requests
import re
import random
import string
import json
import os
import time
from urllib.parse import quote

app = Flask(__name__)

# ======================= EZ4SHORT LOGIN =======================
EZ4_USER = "Banna123"
EZ4_PASS = "Jitendar"
EZ4_SESSION = None
EZ4_SESSION_TIME = 0

# ======================= YOUR SHORTENER =======================
YOUR_SHORTENER = "https://url-shortner-3jy6.onrender.com"

# ======================= KEY DATABASE =======================
KEYS_DB = {}  # {key: {"created": timestamp, "url": "...", "validity_hours": 6, "used_ips": []}}

# ======================= HELPERS =======================
def random_key(length=8):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def clean_expired_keys():
    """Remove expired keys"""
    now = time.time()
    expired = []
    for k, v in KEYS_DB.items():
        validity_sec = v.get("validity_hours", 6) * 3600
        if now - v["created"] > validity_sec:
            expired.append(k)
    for k in expired:
        del KEYS_DB[k]

def create_notes_url(text):
    """Create notes.io URL with FRESH session every time"""
    session = requests.Session()
    session.get("https://notes.io/", timeout=30)
    
    headers = {
        "Host": "notes.io",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 Chrome/146.0 Mobile Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://notes.io",
        "Referer": "https://notes.io/",
        "Accept": "*/*",
    }
    
    resp = session.post(
        "https://notes.io/short.php",
        data=f"txt={quote(text)}",
        headers=headers,
        timeout=30
    )
    
    if resp.status_code != 200:
        return None
    
    match = re.search(r'href="(https://notes\.io/[^"]+)"', resp.text)
    return match.group(1) if match else None

def get_ez4_session():
    """Get or refresh EZ4 session"""
    global EZ4_SESSION, EZ4_SESSION_TIME
    
    if EZ4_SESSION and (time.time() - EZ4_SESSION_TIME) < 1800:
        return EZ4_SESSION
    
    session = requests.Session()
    headers = {
        "Host": "ez4short.com",
        "User-Agent": "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml"
    }
    
    resp = session.get("https://ez4short.com/auth/signin", headers=headers)
    html = resp.text
    
    csrf = re.search(r'name="_csrfToken"[^>]*value="([^"]+)"', html)
    tf = re.search(r'name="_Token\[fields\]"[^>]*value="([^"]+)"', html)
    tu = re.search(r'name="_Token\[unlocked\]"[^>]*value="([^"]+)"', html)
    
    if not csrf or not tf or not tu:
        return None
    
    login_data = (
        f"_method=POST"
        f"&_csrfToken={csrf.group(1)}"
        f"&username={EZ4_USER}"
        f"&password={EZ4_PASS}"
        f"&remember_me=0"
        f"&_Token%5Bfields%5D={quote(tf.group(1), safe='')}"
        f"&_Token%5Bunlocked%5D={quote(tu.group(1), safe='')}"
    )
    
    headers_post = {
        "Host": "ez4short.com",
        "Origin": "https://ez4short.com",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://ez4short.com/auth/signin"
    }
    
    session.post("https://ez4short.com/auth/signin", data=login_data, headers=headers_post)
    
    EZ4_SESSION = session
    EZ4_SESSION_TIME = time.time()
    return session

def shorten_ez4(long_url):
    """Shorten using EZ4"""
    session = get_ez4_session()
    if not session:
        return None
    
    headers = {
        "Host": "ez4short.com",
        "User-Agent": "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36",
        "Accept": "text/html"
    }
    resp = session.get("https://ez4short.com/member/dashboard", headers=headers)
    html = resp.text
    
    csrf = re.search(r'name="_csrfToken"[^>]*value="([^"]+)"', html)
    tf = re.search(r'name="_Token\[fields\]"[^>]*value="([^"]+)"', html)
    tu = re.search(r'name="_Token\[unlocked\]"[^>]*value="([^"]+)"', html)
    
    if not csrf or not tf or not tu:
        return None
    
    headers_post = {
        "Host": "ez4short.com",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://ez4short.com",
        "Referer": "https://ez4short.com/member/dashboard"
    }
    
    data = (
        f"_method=POST"
        f"&_csrfToken={csrf.group(1)}"
        f"&url={quote(long_url)}"
        f"&alias="
        f"&ad_type=2"
        f"&_Token%5Bfields%5D={quote(tf.group(1), safe='')}"
        f"&_Token%5Bunlocked%5D={quote(tu.group(1), safe='')}"
    )
    
    resp = session.post("https://ez4short.com/links/shorten", data=data, headers=headers_post)
    
    try:
        result = resp.json()
        if result.get("status") == "success":
            return result.get("url")
    except:
        pass
    
    return None

def final_shorten(long_url):
    """Final shorten via your shortener"""
    try:
        resp = requests.post(
            f"{YOUR_SHORTENER}/shorten",
            json={"url": long_url},
            timeout=30
        )
        data = resp.json()
        return data.get("short_url")
    except:
        return None

# ======================= API =======================
@app.route('/get-key', methods=['GET'])
def get_key():
    """Generate key + return URL (CUSTOM VALIDITY)"""
    try:
        clean_expired_keys()
        
        # 🔥 User se validity lo (query param: ?hours=6)
        validity_hours = request.args.get('hours', '6')
        try:
            validity_hours = float(validity_hours)
            if validity_hours < 1:
                validity_hours = 1
            if validity_hours > 24:
                validity_hours = 24
        except:
            validity_hours = 6
        
        user_ip = request.remote_addr
        
        # Check if same IP already has valid key
        for k, v in KEYS_DB.items():
            if user_ip in v.get("used_ips", []):
                validity_sec = v.get("validity_hours", 6) * 3600
                if time.time() - v["created"] < validity_sec:
                    return jsonify({
                        "status": "success",
                        "key": k,
                        "url": v["url"],
                        "validity_hours": v.get("validity_hours", 6),
                        "expires_in": round((validity_sec - (time.time() - v["created"])) / 3600, 1),
                        "message": "Your existing key is still valid!"
                    })
        
        # 1. Random key
        key = random_key(8)
        
        # 2. Notes.io (fresh session)
        notes_url = create_notes_url(key)
        if not notes_url:
            return jsonify({"error": "Notes.io failed"}), 500
        
        # 3. EZ4Short
        ez4_url = shorten_ez4(notes_url)
        if not ez4_url:
            return jsonify({"error": "EZ4 failed"}), 500
        
        # 4. Your shortener
        final_url = final_shorten(ez4_url)
        if not final_url:
            return jsonify({"error": "Final shorten failed"}), 500
        
        # Save to DB
        KEYS_DB[key] = {
            "created": time.time(),
            "url": final_url,
            "validity_hours": validity_hours,
            "used_ips": [user_ip]
        }
        
        return jsonify({
            "status": "success",
            "key": key,
            "url": final_url,
            "validity_hours": validity_hours,
            "expires_in": validity_hours
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/verify-key', methods=['POST'])
def verify_key():
    """Verify if key is valid"""
    clean_expired_keys()
    
    data = request.json
    key = data.get('key', '')
    
    if key in KEYS_DB:
        v = KEYS_DB[key]
        validity_sec = v.get("validity_hours", 6) * 3600
        
        if time.time() - v["created"] < validity_sec:
            return jsonify({
                "status": "success",
                "valid": True,
                "expires_in": round((validity_sec - (time.time() - v["created"])) / 3600, 1)
            })
    
    return jsonify({"status": "error", "valid": False, "message": "Key expired or invalid!"})

@app.route('/keys', methods=['GET'])
def list_keys():
    """Show all active keys (admin)"""
    clean_expired_keys()
    active_keys = {}
    for k, v in KEYS_DB.items():
        validity_sec = v.get("validity_hours", 6) * 3600
        active_keys[k] = {
            "url": v["url"],
            "created": v["created"],
            "validity_hours": v.get("validity_hours", 6),
            "expires_in": round((validity_sec - (time.time() - v["created"])) / 3600, 1)
        }
    return jsonify({"total": len(active_keys), "keys": active_keys})

@app.route('/')
def home():
    return "Key Generator Server Running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
