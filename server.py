from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import json
import threading
import time
from urllib.parse import urlparse, parse_qs

HOST = '127.0.0.1'
PORT = 8000
TRACKING_UPDATE_INTERVAL = 4.0

TRACKING_VANS = [
    {
        'id': 'Van 01',
        'branch': 'Branch A',
        'color': '#2a6049',
        'status': 'On route',
        'route': [
            [12.9716, 77.5946],
            [12.9583, 77.6471],
            [12.9718, 77.6412],
            [12.9835, 77.6715],
        ],
        'step': 0,
    },
    {
        'id': 'Van 02',
        'branch': 'Branch B',
        'color': '#1a4a7a',
        'status': 'On route',
        'route': [
            [12.9352, 77.6245],
            [12.9192, 77.6129],
            [12.9081, 77.5266],
            [12.9231, 77.6206],
        ],
        'step': 0,
    },
    {
        'id': 'Van 03',
        'branch': 'Branch C',
        'color': '#6b3fa0',
        'status': 'On route',
        'route': [
            [12.9911, 77.5968],
            [12.9788, 77.7152],
            [12.9673, 77.7492],
            [12.9658, 77.6072],
        ],
        'step': 0,
    },
]

class TrackingHandler(SimpleHTTPRequestHandler):
    def _set_json_headers(self, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=UTF-8')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/tracking':
            self._set_json_headers()
            response = {
                'vans': [
                    {
                        'id': v['id'],
                        'branch': v['branch'],
                        'color': v['color'],
                        'status': v['status'],
                        'coords': v['route'][v['step']],
                    }
                    for v in TRACKING_VANS
                ],
                'updated_at': int(time.time()),
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return

        if parsed.path == '/api/maintenance':
            self._set_json_headers()
            response = {
                'status': 'ok',
                'message': 'Live tracking server is running',
                'van_count': len(TRACKING_VANS),
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/tracking':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            decode_text = body.decode('utf-8') if body else ''
            try:
                payload = json.loads(decode_text) if decode_text else {}
            except json.JSONDecodeError:
                self._set_json_headers(400)
                self.wfile.write(json.dumps({'error': 'Invalid JSON'}).encode('utf-8'))
                return

            updates = payload.get('updates', [])
            updated = []
            for item in updates:
                van_id = item.get('id')
                for van in TRACKING_VANS:
                    if van['id'] == van_id:
                        if 'status' in item:
                            van['status'] = item['status']
                        if 'coords' in item and isinstance(item['coords'], list) and len(item['coords']) == 2:
                            van['route'][van['step']] = item['coords']
                        updated.append(van_id)

            self._set_json_headers(200)
            self.wfile.write(json.dumps({'status': 'updated', 'updated': updated}).encode('utf-8'))
            return

        self.send_error(404, 'Endpoint not found')


def tracking_loop():
    while True:
        for van in TRACKING_VANS:
            van['step'] = (van['step'] + 1) % len(van['route'])
            van['status'] = 'Arriving soon' if van['step'] == len(van['route']) - 1 else 'On route'
        time.sleep(TRACKING_UPDATE_INTERVAL)


def run_server():
    server = ThreadingHTTPServer((HOST, PORT), TrackingHandler)
    print(f'Live tracking server running at http://{HOST}:{PORT}')
    server.serve_forever()


if __name__ == '__main__':
    thread = threading.Thread(target=tracking_loop, daemon=True)
    thread.start()
    run_server()
