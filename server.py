#!/usr/bin/env python3
# KEY GENERATOR SERVER

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

# ======================= NOTES.IO COOKIES =======================
NOTES_COOKIES = {
    "PHPSESSID": "213e26f012cb61d3b5cd41473c176801",
    "_ga": "GA1.1.552170096.1777705231",
    "_ga_H0XVNMGVTV": "GS2.1.s1778167246$o7$g0$t1778167246$j60$l0$h0"
}

# ======================= EZ4SHORT LOGIN =======================
EZ4_USER = "Banna123"
EZ4_PASS = "Jitendar"
EZ4_SESSION = None  # Cached session
EZ4_SESSION_TIME = 0

# ======================= YOUR SHORTENER =======================
YOUR_SHORTENER = "https://url-shortner-3jy6.onrender.com"

# ======================= HELPERS =======================
def random_key(length=8):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def create_notes_url(text):
    """Create notes.io short URL"""
    headers = {
        "Host": "notes.io",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 Chrome/146.0 Mobile Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://notes.io",
        "Referer": "https://notes.io/",
        "Accept": "*/*",
    }
    resp = requests.post(
        "https://notes.io/short.php",
        data=f"txt={quote(text)}",
        headers=headers,
        cookies=NOTES_COOKIES,
        timeout=30
    )
    match = re.search(r'href="(https://notes\.io/[^"]+)"', resp.text)
    return match.group(1) if match else None

def get_ez4_session():
    """Get or refresh EZ4 session"""
    global EZ4_SESSION, EZ4_SESSION_TIME
    
    # Use cached if valid (under 30 min)
    if EZ4_SESSION and (time.time() - EZ4_SESSION_TIME) < 1800:
        return EZ4_SESSION
    
    # Fresh login
    session = requests.Session()
    headers = {"Host": "ez4short.com", "User-Agent": "Mozilla/5.0", "Accept": "text/html"}
    
    # Get login page
    resp = session.get("https://ez4short.com/auth/signin", headers=headers)
    html = resp.text
    
    csrf = re.search(r'name="_csrfToken"[^>]*value="([^"]+)"', html).group(1)
    tf = re.search(r'name="_Token\[fields\]"[^>]*value="([^"]+)"', html).group(1)
    tu = re.search(r'name="_Token\[unlocked\]"[^>]*value="([^"]+)"', html).group(1)
    
    # Login
    data = f"_method=POST&_csrfToken={csrf}&username={EZ4_USER}&password={EZ4_PASS}&remember_me=0&_Token%5Bfields%5D={quote(tf, safe='')}&_Token%5Bunlocked%5D={quote(tu, safe='')}"
    headers_post = {"Host": "ez4short.com", "Origin": "https://ez4short.com", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0", "Referer": "https://ez4short.com/auth/signin"}
    session.post("https://ez4short.com/auth/signin", data=data, headers=headers_post)
    
    EZ4_SESSION = session
    EZ4_SESSION_TIME = time.time()
    return session

def shorten_ez4(long_url):
    """Shorten using EZ4"""
    session = get_ez4_session()
    
    # Get dashboard
    resp = session.get("https://ez4short.com/member/dashboard", headers={"Host": "ez4short.com", "User-Agent": "Mozilla/5.0"})
    html = resp.text
    
    csrf = re.search(r'name="_csrfToken"[^>]*value="([^"]+)"', html).group(1)
    tf = re.search(r'name="_Token\[fields\]"[^>]*value="([^"]+)"', html).group(1)
    tu = re.search(r'name="_Token\[unlocked\]"[^>]*value="([^"]+)"', html).group(1)
    
    # Shorten
    headers = {"Host": "ez4short.com", "X-Requested-With": "XMLHttpRequest", "User-Agent": "Mozilla/5.0", "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Origin": "https://ez4short.com", "Referer": "https://ez4short.com/member/dashboard"}
    data = f"_method=POST&_csrfToken={csrf}&url={quote(long_url)}&alias=&ad_type=2&_Token%5Bfields%5D={quote(tf, safe='')}&_Token%5Bunlocked%5D={quote(tu, safe='')}"
    
    resp = session.post("https://ez4short.com/links/shorten", data=data, headers=headers)
    result = resp.json()
    return result.get("url") if result.get("status") == "success" else None

def final_shorten(long_url):
    """Final shorten via your shortener"""
    resp = requests.post(
        f"{YOUR_SHORTENER}/shorten",
        json={"url": long_url},
        timeout=30
    )
    data = resp.json()
    return data.get("short_url")

# ======================= API =======================
@app.route('/get-key', methods=['GET'])
def get_key():
    """Generate key + return URL"""
    try:
        # 1. Random key
        key = random_key(8)
        
        # 2. Notes.io note
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
        
        return jsonify({
            "status": "success",
            "key": key,
            "url": final_url
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Key Generator Server Running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
