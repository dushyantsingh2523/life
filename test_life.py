import json, subprocess, sys, time, unittest, urllib.error, urllib.request

URL = "http://127.0.0.1:8000"

def get(path):
    try:
        with urllib.request.urlopen(URL + path, timeout=2) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:          # 4xx/5xx still have a JSON body
        return e.code, json.loads(e.read())

class LifeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc = subprocess.Popen([sys.executable, "life.py"])
        for _ in range(50):                      # wait up to 5 s for it to listen
            try:
                get("/healthz")
                return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("server never started listening")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()                     # SIGTERM [D9]
        cls.proc.wait(timeout=10)

    def test_1_alive_but_not_ready_while_loading(self):
        self.assertEqual(get("/healthz")[0], 200)
        self.assertEqual(get("/readyz")[0], 503, "must NOT be ready while the model loads")

    def test_2_ready_and_answers_after_loading(self):
        for _ in range(30):                      # wait up to 15 s
            if get("/readyz")[0] == 200:
                break
            time.sleep(0.5)
        status, body = get("/version")
        self.assertEqual(status, 200)
        self.assertEqual(body["version"], "2")

if __name__ == "__main__":
    unittest.main(verbosity=2)
