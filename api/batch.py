"""
SeedDream Batch Endpoint - Process multiple poses x outfits
"""

import os
import json
import tempfile
import base64
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path

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

            # Expected format:
            # {
            #   "poses": [{"name": "pose1.png", "data": "base64..."}, ...] or ["url1", "url2"]
            #   "outfits": [{"name": "outfit1.png", "data": "base64..."}, ...] or ["url1", "url2"]
            #   "prompt": "optional custom prompt",
            #   "seed": optional_seed
            # }

            poses_input = data.get('poses', [])
            outfits_input = data.get('outfits', [])
            prompt = data.get('prompt', 'Apply the outfit/clothing from Figure 2 onto the person in Figure 1. Keep the exact pose, face, and background from Figure 1. Only change the clothing to match Figure 2.')
            seed = data.get('seed')

            if not poses_input or not outfits_input:
                return self.send_json({"error": "Need both poses and outfits"}, 400)

            results = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Process poses - convert to URLs if base64
            pose_urls = []
            for idx, pose in enumerate(poses_input):
                if isinstance(pose, str) and pose.startswith('http'):
                    pose_urls.append({"url": pose, "name": f"pose_{idx+1}"})
                elif isinstance(pose, dict):
                    name = pose.get('name', f'pose_{idx+1}')
                    img_data = pose.get('data', '')

                    if img_data.startswith('http'):
                        pose_urls.append({"url": img_data, "name": name})
                    else:
                        # Base64 data
                        if ',' in img_data:
                            img_data = img_data.split(',')[1]

                        img_bytes = base64.b64decode(img_data)
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                            tmp.write(img_bytes)
                            tmp_path = tmp.name

                        try:
                            url = fal_client.upload_file(tmp_path)
                            pose_urls.append({"url": url, "name": name})
                        finally:
                            os.unlink(tmp_path)

            # Process outfits - convert to URLs if base64
            outfit_urls = []
            for idx, outfit in enumerate(outfits_input):
                if isinstance(outfit, str) and outfit.startswith('http'):
                    outfit_urls.append({"url": outfit, "name": f"outfit_{idx+1}"})
                elif isinstance(outfit, dict):
                    name = outfit.get('name', f'outfit_{idx+1}')
                    img_data = outfit.get('data', '')

                    if img_data.startswith('http'):
                        outfit_urls.append({"url": img_data, "name": name})
                    else:
                        # Base64 data
                        if ',' in img_data:
                            img_data = img_data.split(',')[1]

                        img_bytes = base64.b64decode(img_data)
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                            tmp.write(img_bytes)
                            tmp_path = tmp.name

                        try:
                            url = fal_client.upload_file(tmp_path)
                            outfit_urls.append({"url": url, "name": name})
                        finally:
                            os.unlink(tmp_path)

            # Process each combination
            for p_idx, pose_data in enumerate(pose_urls):
                for o_idx, outfit_data in enumerate(outfit_urls):
                    arguments = {
                        "prompt": prompt,
                        "image_urls": [pose_data["url"], outfit_data["url"]],
                        "num_images": 1,
                        "image_size": "auto_4K",
                        "enable_safety_checker": False,
                    }

                    if seed:
                        arguments["seed"] = int(seed)

                    try:
                        result = fal_client.subscribe(
                            "fal-ai/bytedance/seedream/v4.5/edit",
                            arguments=arguments,
                            with_logs=True
                        )

                        images = result.get("images", [])
                        if images:
                            pose_name = Path(pose_data["name"]).stem
                            outfit_name = Path(outfit_data["name"]).stem
                            results.append({
                                "pose_index": p_idx,
                                "outfit_index": o_idx,
                                "pose_name": pose_name,
                                "outfit_name": outfit_name,
                                "status": "completed",
                                "image_url": images[0].get("url", ""),
                                "filename": f"seedream_{timestamp}_p{p_idx + 1}_{pose_name}_o{o_idx + 1}_{outfit_name}.png"
                            })
                        else:
                            results.append({
                                "pose_index": p_idx,
                                "outfit_index": o_idx,
                                "status": "failed",
                                "error": "No image returned"
                            })

                    except Exception as e:
                        results.append({
                            "pose_index": p_idx,
                            "outfit_index": o_idx,
                            "status": "failed",
                            "error": str(e)
                        })

            return self.send_json({
                "success": True,
                "total": len(poses_input) * len(outfits_input),
                "completed": len([r for r in results if r.get("status") == "completed"]),
                "results": results
            })

        except json.JSONDecodeError:
            return self.send_json({"error": "Invalid JSON"}, 400)
        except Exception as e:
            return self.send_json({"error": str(e)}, 500)
