import json, os, socket, signal, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

GRACEFUL = os.environ.get("GRACEFUL", "1") == "1"
START = time.time()
VERSION = "2"
state = {"ready": False, "in_flight": 0}
lock = threading.Lock()

def log(msg):
    print(f"{time.time() - START:5.1f}s  {msg}", flush=True)

def load_model():
    log("loading model weights... (8 s)")
    time.sleep(8)
    state["ready"] = True
    log("model loaded: READY")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/version":
            if not state["ready"]:
                return self.reply(503, {"error": "not ready", "pod": socket.gethostname()})
            return self.reply(200, {"version": VERSION, "pod": socket.gethostname()})
        if self.path == "/healthz":
            return self.reply(200, {"alive": True})
        if self.path == "/readyz":
            return self.reply(200 if state["ready"] else 503, {"ready": state["ready"]})
        if self.path == "/predict":
            if not state["ready"]:
                return self.reply(503, {"error": "not ready"})
            with lock:
                state["in_flight"] += 1
            try:
                time.sleep(3)                        # the "model" thinking
                self.reply(200, {"answer": 42})
            finally:
                with lock:
                    state["in_flight"] -= 1
            return
        self.reply(404, {"error": "no route"})

    def reply(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass

server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)

def drain_and_exit():
    while True:
        with lock:
            n = state["in_flight"]
        if n == 0:
            break
        log(f"draining: waiting for {n} request(s) to finish")
        time.sleep(0.5)
    log("drained: exiting cleanly")
    server.shutdown()

def on_sigterm(signum, frame):
    log("SIGTERM received: marking NOT ready, finishing in-flight work")
    state["ready"] = False
    threading.Thread(target=drain_and_exit).start()

if GRACEFUL:
    signal.signal(signal.SIGTERM, on_sigterm)

threading.Thread(target=load_model, daemon=True).start()
log(f"listening on 8000 (graceful shutdown {'ON' if GRACEFUL else 'OFF'})")
server.serve_forever()
log("server stopped")
