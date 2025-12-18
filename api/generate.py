"""
SeedDream Text-to-Image Endpoint - Generate images from text prompts
"""

import os
import json
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
            content_type = self.headers.get('Content-Type', '')
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            if 'application/json' not in content_type:
                return self.send_json({"error": "Content-Type must be application/json"}, 400)

            data = json.loads(body.decode())
            prompt = data.get('prompt', '')
            image_size = data.get('image_size', 'square_hd')
            num_images = data.get('num_images', 1)
            seed = data.get('seed')

            if not prompt:
                return self.send_json({"error": "No prompt provided"}, 400)

            # Map size options - default to 4K
            size_map = {
                "square_hd": "square_hd",
                "square": "square",
                "portrait_4_3": "portrait_4_3",
                "portrait_16_9": "portrait_16_9",
                "landscape_4_3": "landscape_4_3",
                "landscape_16_9": "landscape_16_9",
                "auto_4K": "auto_4K",
                "auto_2K": "auto_2K",
            }

            # Build API arguments
            arguments = {
                "prompt": prompt,
                "image_size": size_map.get(image_size, "auto_4K"),
                "num_images": num_images,
                "enable_safety_checker": False,
            }

            if seed:
                arguments["seed"] = int(seed)

            # Call Fal API for text-to-image
            result = fal_client.subscribe(
                "fal-ai/bytedance/seedream/v4.5/text-to-image",
                arguments=arguments,
                with_logs=True
            )

            return self.send_json({
                "success": True,
                "images": result.get("images", []),
                "request_id": result.get("request_id", "")
            })

        except Exception as e:
            return self.send_json({"error": str(e)}, 500)
