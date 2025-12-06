from flask import Flask, jsonify, request, Response, send_from_directory, redirect
import os
from service import api as api_mod

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "log")
OUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

app = Flask(__name__)
app.register_blueprint(api_mod.bp, url_prefix="/api")


@app.get("/")
def index():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "index.html")


@app.get("/progress")
def progress_ui():
    # simple static page shipped with the app
    return send_from_directory(os.path.join(BASE_DIR, "static"), "progress.html")

@app.get("/visualisasi.html")
def visualisasi_ui():
    # serve visualization dashboard static page
    return send_from_directory(os.path.join(BASE_DIR, "static"), "visualisasi.html")

@app.get("/visualisasi/<product_id>")
def visualisasi_redirect(product_id):
    return redirect(f"/visualisasi.html?product={product_id}")


def run():
    app.run(host="0.0.0.0", port=5001, debug=True)


if __name__ == "__main__":
    run()
