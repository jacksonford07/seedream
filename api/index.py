"""
SeedDream API - Vercel Serverless Functions
Applies multiple outfits to multiple poses using ByteDance SeedDream 4.5 via Fal.ai
"""

import os
import json
import tempfile
import base64
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

try:
    import fal_client
except ImportError:
    fal_client = None

# Configuration
FAL_API_KEY = os.getenv("FAL_API_KEY")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Set FAL_KEY for fal_client
if FAL_API_KEY:
    os.environ["FAL_KEY"] = FAL_API_KEY


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {
            "message": "SeedDream API is running",
            "endpoints": {
                "health": "/api/health",
                "edit": "/api/edit (POST)",
                "batch": "/api/batch (POST)"
            }
        }
        self.wfile.write(json.dumps(response).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
