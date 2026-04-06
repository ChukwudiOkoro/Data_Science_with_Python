#!/usr/bin/env python3
import ast
import json
import math
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

ALLOWED_NAMES = {
    **{name: value for name, value in math.__dict__.items() if not name.startswith("__")},
    "abs": abs,
    "round": round,
    "pow": pow,
    "pi": math.pi,
    "e": math.e,
}

OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b,
    ast.Mod: lambda a, b: a % b,
    ast.USub: lambda a: -a,
    ast.UAdd: lambda a: +a,
}


class CalculatorError(Exception):
    pass


def eval_expr(node):
    if isinstance(node, ast.BinOp):
        left = eval_expr(node.left)
        right = eval_expr(node.right)
        op = OPS.get(type(node.op))
        if op is None:
            raise CalculatorError("Unsupported binary operator")
        return op(left, right)

    if isinstance(node, ast.UnaryOp):
        operand = eval_expr(node.operand)
        op = OPS.get(type(node.op))
        if op is None:
            raise CalculatorError("Unsupported unary operator")
        return op(operand)

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise CalculatorError("Invalid function call")
        func_name = node.func.id
        func = ALLOWED_NAMES.get(func_name)
        if func is None or not callable(func):
            raise CalculatorError(f"Unsupported function: {func_name}")
        args = [eval_expr(arg) for arg in node.args]
        return func(*args)

    if isinstance(node, ast.Name):
        if node.id not in ALLOWED_NAMES:
            raise CalculatorError(f"Unknown symbol: {node.id}")
        return ALLOWED_NAMES[node.id]

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise CalculatorError("Unsupported constant type")

    if isinstance(node, ast.Num):
        return node.n

    raise CalculatorError("Unsupported expression")


def calculate(expression: str):
    sanitized = expression.replace("^", "**")
    tree = ast.parse(sanitized, mode="eval")
    return eval_expr(tree.body)


def json_response(handler, status, payload):
    payload_bytes = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload_bytes)))
    handler.end_headers()
    handler.wfile.write(payload_bytes)


class CalcHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            return self.serve_static("index.html")
        if parsed.path.startswith("/static/"):
            return self.serve_static(parsed.path[len("/static/"):])
        if parsed.path == "/api/calc":
            params = parse_qs(parsed.query)
            expression = params.get("expr", [""])[0]
            return self.handle_calc(expression)
        self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path != "/api/calc":
            return self.send_error(404, "Not Found")

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length else ""
        try:
            data = json.loads(body or "{}")
        except json.JSONDecodeError:
            return json_response(self, 400, {"error": "Invalid JSON body"})

        expression = data.get("expression", "")
        return self.handle_calc(expression)

    def handle_calc(self, expression: str):
        if not isinstance(expression, str) or not expression.strip():
            return json_response(self, 400, {"error": "Expression is required"})

        try:
            result = calculate(expression)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return json_response(self, 200, {"result": result})
        except Exception as exc:
            return json_response(self, 400, {"error": str(exc)})

    def serve_static(self, path: str):
        safe_path = os.path.normpath(path).lstrip(os.sep)
        target = STATIC_DIR / safe_path
        if not target.exists() or not target.is_file() or (STATIC_DIR not in target.resolve().parents and target.resolve() != STATIC_DIR):
            return self.send_error(404, "File not found")

        content_type = self.guess_type(target.name)
        with open(target, "rb") as fh:
            content = fh.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        return

    def guess_type(self, path):
        if path.endswith(".html"):
            return "text/html; charset=utf-8"
        if path.endswith(".css"):
            return "text/css; charset=utf-8"
        if path.endswith(".js"):
            return "application/javascript; charset=utf-8"
        if path.endswith(".json"):
            return "application/json; charset=utf-8"
        return "application/octet-stream"


def main():
    host = "127.0.0.1"
    port = 8000
    server = HTTPServer((host, port), CalcHandler)
    print(f"fastAOI calculator running at http://{host}:{port}/")
    print("Open the browser to use the modern calculator UI.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server...")
        server.server_close()


if __name__ == "__main__":
    main()
