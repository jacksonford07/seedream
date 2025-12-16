"""
SeedDream Edit Endpoint - Single image editing
"""

import os
import json
import tempfile
import base64
from http.server import BaseHTTPRequestHandler
import cgi
from io import BytesIO

try:
    import fal_client
except ImportError:
    fal_client = None

FAL_API_KEY = os.getenv("FAL_API_KEY")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

if FAL_API_KEY:
    os.environ["FAL_KEY"] = FAL_API_KEY


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_multipart(handler):
    """Parse multipart form data"""
    content_type = handler.headers.get('Content-Type', '')

    if 'multipart/form-data' not in content_type:
        return None, None

    content_length = int(handler.headers.get('Content-Length', 0))
    body = handler.rfile.read(content_length)

    # Parse the boundary
    boundary = content_type.split('boundary=')[1] if 'boundary=' in content_type else None
    if not boundary:
        return None, None

    environ = {
        'REQUEST_METHOD': 'POST',
        'CONTENT_TYPE': content_type,
        'CONTENT_LENGTH': content_length,
    }

    fp = BytesIO(body)
    form = cgi.FieldStorage(fp=fp, environ=environ, keep_blank_values=True)

    return form, body


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
            content_type = self.headers.get('Content-Type', '')
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            # Handle JSON requests (with base64 images or URLs)
            if 'application/json' in content_type:
                data = json.loads(body.decode())
                prompt = data.get('prompt', '')
                image_urls = data.get('image_urls', [])
                images_base64 = data.get('images', [])
                seed = data.get('seed')
                num_images = data.get('num_images', 1)

                if not prompt:
                    return self.send_json({"error": "No prompt provided"}, 400)

                # Upload base64 images if provided
                if images_base64 and not image_urls:
                    image_urls = []
                    for img_data in images_base64:
                        # Handle data URL format
                        if ',' in img_data:
                            img_data = img_data.split(',')[1]

                        img_bytes = base64.b64decode(img_data)
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                            tmp.write(img_bytes)
                            tmp_path = tmp.name

                        try:
                            url = fal_client.upload_file(tmp_path)
                            image_urls.append(url)
                        finally:
                            os.unlink(tmp_path)

                if not image_urls:
                    return self.send_json({"error": "No images provided"}, 400)

                # Build API arguments
                arguments = {
                    "prompt": prompt,
                    "image_urls": image_urls,
                    "num_images": num_images,
                    "image_size": "auto_4K",
                    "enable_safety_checker": False,
                }

                if seed:
                    arguments["seed"] = int(seed)

                # Call Fal API
                result = fal_client.subscribe(
                    "fal-ai/bytedance/seedream/v4.5/edit",
                    arguments=arguments,
                    with_logs=True
                )

                return self.send_json({
                    "success": True,
                    "images": result.get("images", []),
                    "request_id": result.get("request_id", "")
                })

            else:
                return self.send_json({"error": "Content-Type must be application/json"}, 400)

        except Exception as e:
            return self.send_json({"error": str(e)}, 500)
