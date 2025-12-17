"""
Seedance Video Endpoint - Image to Video generation
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

            # Required fields
            prompt = data.get('prompt', '')
            image_data = data.get('image')  # base64 or URL
            image_url = data.get('image_url')  # direct URL

            if not prompt:
                return self.send_json({"error": "No prompt provided"}, 400)

            # Handle image - either base64 or URL
            if image_data and not image_url:
                # Base64 image - upload to fal
                if ',' in image_data:
                    image_data = image_data.split(',')[1]

                img_bytes = base64.b64decode(image_data)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                    tmp.write(img_bytes)
                    tmp_path = tmp.name

                try:
                    image_url = fal_client.upload_file(tmp_path)
                finally:
                    os.unlink(tmp_path)

            if not image_url:
                return self.send_json({"error": "No image provided"}, 400)

            # Optional fields
            aspect_ratio = data.get('aspect_ratio', 'auto')
            resolution = data.get('resolution', '1080p')
            duration = data.get('duration', '5')
            seed = data.get('seed')

            # Build API arguments
            arguments = {
                "prompt": prompt,
                "image_url": image_url,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "duration": str(duration),
                "enable_safety_checker": False,
            }

            if seed:
                arguments["seed"] = int(seed)

            print(f"Calling Seedance API with: {arguments}")

            # Call Fal API
            result = fal_client.subscribe(
                "fal-ai/bytedance/seedance/v1/pro/image-to-video",
                arguments=arguments,
                with_logs=True
            )

            print(f"Seedance result: {result}")

            return self.send_json({
                "success": True,
                "video": result.get("video", {}),
                "request_id": result.get("request_id", "")
            })

        except json.JSONDecodeError:
            return self.send_json({"error": "Invalid JSON"}, 400)
        except Exception as e:
            print(f"Seedance error: {str(e)}")
            return self.send_json({"error": str(e)}, 500)
