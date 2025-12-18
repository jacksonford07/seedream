"""
Upload endpoint - Upload images directly to Fal storage
Returns URLs that can be used with other endpoints
"""

import os
import json
import tempfile
import base64
from http.server import BaseHTTPRequestHandler

try:
    import fal_client
except ImportError:
    fal_client = None

FAL_API_KEY = os.getenv("FAL_API_KEY")

if FAL_API_KEY:
    os.environ["FAL_KEY"] = FAL_API_KEY


class handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if not FAL_API_KEY:
            return self.send_json({"error": "FAL_API_KEY not configured"}, 500)

        if not fal_client:
            return self.send_json({"error": "fal_client not installed"}, 500)

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            data = json.loads(body.decode())
            image_base64 = data.get('image', '')

            if not image_base64:
                return self.send_json({"error": "No image provided"}, 400)

            # Handle data URL format
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]

            img_bytes = base64.b64decode(image_base64)

            # Write to temp file and upload to Fal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name

            try:
                url = fal_client.upload_file(tmp_path)
            finally:
                os.unlink(tmp_path)

            return self.send_json({
                "success": True,
                "url": url
            })

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in upload endpoint: {error_details}")
            return self.send_json({"error": str(e)}, 500)
