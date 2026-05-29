"""
Servidor HTTP mínimo para manter o bot vivo em plataformas como Railway e Render.
Plataformas free tier matam processos que ficam sem tráfego HTTP.
Este servidor responde /health e / para os health checks automáticos.
"""

import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

KEEP_ALIVE_PORT = 8080

HTML_RESPONSE = b"""<!DOCTYPE html>
<html>
<head><title>Companion Tibia</title></head>
<body>
  <h1>Companion Tibia Online</h1>
  <p>Bot Discord para Rubinot Open PvP</p>
  <p>Por Soneca &amp; Shawnks</p>
</body>
</html>"""

JSON_HEALTH = b'{"status":"online","bot":"Companion Tibia","server":"Rubinot"}'


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/health", "/ping", "/healthz"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(JSON_HEALTH)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_RESPONSE)

    def log_message(self, format, *args):
        # Silencia os logs HTTP para não poluir o console
        pass


def start_keep_alive(port: int = KEEP_ALIVE_PORT):
    """Inicia o servidor HTTP em thread separada (não bloqueia o bot)."""
    def run():
        try:
            server = HTTPServer(("0.0.0.0", port), HealthHandler)
            logger.info("Keep-alive server rodando na porta %d", port)
            server.serve_forever()
        except OSError as e:
            logger.warning("Keep-alive server não pôde iniciar na porta %d: %s", port, e)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread
