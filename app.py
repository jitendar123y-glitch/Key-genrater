from flask import Flask, request, render_template_string
import random
import string
import json
import os

app = Flask(__name__)
DB_FILE = "notes.json"

# ======================= HOME TEMPLATE (NO ADS) =======================
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
        .header h1 { font-size: 36px; color: #00ff9
