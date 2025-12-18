"""
Fal Proxy - Proxies requests to Fal API with credentials
This allows the browser fal client to work without exposing API keys
"""

import os
import json
from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.error

FAL_API_KEY = os.getenv("FAL_API_KEY")


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
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Fal-Target-Url')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def proxy_request(self, method):
        if not FAL_API_KEY:
            return self.send_json({"error": "FAL_API_KEY not configured"}, 500)

        try:
            # Get target URL from header
            target_url = self.headers.get('X-Fal-Target-Url', '')
            if not target_url:
                return self.send_json({"error": "Missing X-Fal-Target-Url header"}, 400)

            # Read body if present
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            # Create request to Fal
            req = urllib.request.Request(target_url, data=body, method=method)
            req.add_header('Authorization', f'Key {FAL_API_KEY}')

            # Forward content type
            content_type = self.headers.get('Content-Type')
            if content_type:
                req.add_header('Content-Type', content_type)

            # Make request
            with urllib.request.urlopen(req, timeout=300) as response:
                response_body = response.read()

                self.send_response(response.status)
                self.send_header('Access-Control-Allow-Origin', '*')
                for header, value in response.headers.items():
                    if header.lower() not in ['transfer-encoding', 'content-encoding']:
                        self.send_header(header, value)
                self.end_headers()
                self.wfile.write(response_body)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            self.send_response(e.code)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": error_body}).encode())
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def do_GET(self):
        self.proxy_request('GET')

    def do_POST(self):
        self.proxy_request('POST')

    def do_PUT(self):
        self.proxy_request('PUT')
