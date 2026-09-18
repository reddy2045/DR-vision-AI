"""HTTP bridge from the Node API to the real MATLAB Engine inference path."""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phc_screening.settings')

import django

django.setup()

from ai_engine.matlab_engine import MATLABConfigurationError, MATLABEngineUnavailable
from ai_engine.predictor import predict_fundus
from ai_engine.quality import check_image_quality


logger = logging.getLogger('ai_bridge')
inference_lock = Lock()


class BridgeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.respond(200, {'status': 'ok', 'engine': 'MATLAB Engine for Python'})
            return
        self.respond(404, {'error': 'Not found.'})

    def do_POST(self):
        try:
            payload = self.read_json()
            image_path = Path(payload.get('image_path', '')).resolve()
            if not image_path.is_file():
                self.respond(400, {'error': 'The uploaded image is unavailable to the AI bridge.'})
                return
            if self.path == '/quality':
                self.respond(200, check_image_quality(image_path))
                return
            if self.path == '/predict':
                with inference_lock:
                    result = predict_fundus(image_path)
                self.respond(200, result)
                return
            self.respond(404, {'error': 'Not found.'})
        except (MATLABConfigurationError, MATLABEngineUnavailable) as error:
            logger.exception('MATLAB bridge unavailable')
            self.respond(503, {'error': getattr(error, 'public_message', str(error))})
        except Exception:
            logger.exception('AI bridge request failed')
            self.respond(500, {'error': 'The AI bridge could not complete this request.'})

    def read_json(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length > 4096:
            raise ValueError('Request body is too large.')
        return json.loads(self.rfile.read(length))

    def respond(self, status, payload):
        encoded = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format_string, *args):
        logger.info('%s - %s', self.address_string(), format_string % args)


def main():
    logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'))
    host = os.environ.get('AI_BRIDGE_HOST', '127.0.0.1')
    port = int(os.environ.get('AI_BRIDGE_PORT', '5050'))
    server = ThreadingHTTPServer((host, port), BridgeHandler)
    logger.info('MATLAB AI bridge listening on http://%s:%s', host, port)
    server.serve_forever()


if __name__ == '__main__':
    main()