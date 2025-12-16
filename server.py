#!/usr/bin/env python3
"""
SLIS - Simple Development Server
Serves the Sign Language Interpretation System

Usage:
    python server.py [port]
    
Example:
    python server.py 8080
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

PORT = 8080
DIRECTORY = Path(__file__).parent


class CORSHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with CORS support."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def guess_type(self, path):
        ext = Path(path).suffix.lower()
        types = {
            '.js': 'application/javascript',
            '.mjs': 'application/javascript', 
            '.css': 'text/css',
            '.html': 'text/html',
            '.json': 'application/json',
            '.task': 'application/octet-stream',
            '.wasm': 'application/wasm',
        }
        return types.get(ext, super().guess_type(path))
    
    def log_message(self, format, *args):
        status = args[1] if len(args) > 1 else ''
        color = '\033[92m' if status.startswith('2') else '\033[93m' if status.startswith('3') else '\033[91m'
        print(f"{color}[{self.log_date_time_string()}]\033[0m {args[0]}")


def main():
    global PORT
    
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)
    
    os.chdir(DIRECTORY)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ◈ SLIS - Sign Language Interpretation System               ║
║                                                              ║
║   Server running at: http://localhost:{PORT:<5}                 ║
║                                                              ║
║   Press Ctrl+C to stop                                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    try:
        with socketserver.TCPServer(("", PORT), CORSHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except OSError as e:
        if e.errno == 98:
            print(f"\nError: Port {PORT} is already in use.")
            print(f"Try: python server.py {PORT + 1}")
        else:
            raise


if __name__ == '__main__':
    main()