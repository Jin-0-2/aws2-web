import os
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))

# .env 파일이 있으면 읽어서 환경변수로 등록 (클라우드에서 직접 넣은 환경변수가 우선)
if os.path.exists(os.path.join(BASE, ".env")):
    with open(os.path.join(BASE, ".env"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

HOST = os.environ.get("WEB_HOST", "127.0.0.1")                      # 클라우드: 0.0.0.0
PORT = int(os.environ.get("WEB_PORT", "8080"))
WAS = os.environ.get("WAS_URL", "http://127.0.0.1:8000")            # /api/* 요청을 보낼 WAS 주소
WAS_TIMEOUT = float(os.environ.get("WAS_TIMEOUT", "30"))            # WAS 응답 대기 시간(초)
STATIC = os.path.join(BASE, "static")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.proxy()
        else:
            super().do_GET()                                         # 정적 파일 (HTML/JS)

    def do_POST(self):
        self.proxy()

    def do_PATCH(self):
        self.proxy()

    def do_DELETE(self):
        self.proxy()

    def proxy(self):
        # /api/desk/owner → WAS /desk/owner (본문, 쿠키 그대로 전달)
        if not self.path.startswith("/api/"):
            return self.send_error(404)
        length = int(self.headers.get("Content-Length") or 0)
        req = urllib.request.Request(WAS + self.path[4:], data=self.rfile.read(length) if length else None, method=self.command)
        for name in ("Content-Type", "Cookie"):
            if self.headers.get(name):
                req.add_header(name, self.headers[name])
        try:
            res = urllib.request.urlopen(req, timeout=WAS_TIMEOUT)
        except urllib.error.HTTPError as e:                          # 401, 404, 422 등도 그대로 전달
            res = e
        except urllib.error.URLError:
            return self.send_error(502, "WAS connection failed")
        with res:
            body = res.read()
            self.send_response(res.status)
            for name, value in res.headers.items():
                if name.lower() in ("content-type", "set-cookie"):
                    self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


if __name__ == "__main__":
    print(f"web server: http://{HOST}:{PORT}  (api → {WAS})")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
