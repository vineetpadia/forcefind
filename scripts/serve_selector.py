#!/usr/bin/env python3
"""
Lightweight HTTP static server for ForceFind Selector UI.
Serves index.html, selector-data.json, datasheets, and ocr_results.
"""

import http.server
import socketserver
import sys
import webbrowser
from pathlib import Path

PORT = 8080

class ForceFindHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

def main():
    port = PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    # Ensure selector-data.json exists
    if not Path("selector-data.json").exists() and not Path("public/selector-data.json").exists():
        print("selector-data.json not found! Generating...")
        import subprocess
        subprocess.run(["python3", "scripts/build_selector_data.py"])

    handler = ForceFindHandler
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"\n=======================================================")
        print(f"  ForceFind Selector UI is live!")
        print(f"  URL: http://localhost:{port}/")
        print(f"  Spreadsheet Selector: http://localhost:{port}/index.html")
        print(f"=======================================================\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()
