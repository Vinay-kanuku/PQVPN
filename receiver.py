from flask import Flask, render_template, jsonify, request, send_from_directory
import os, datetime, socket, threading
import time
from discovery import PeerDiscovery

app = Flask(__name__)
app.config["STORAGE"] = "bob_secure_storage"
os.makedirs(app.config["STORAGE"], exist_ok=True)

DEVICE_NAME = "Bob-" + socket.gethostname()[:8]

discovery = PeerDiscovery(name=DEVICE_NAME, port=9000)
discovery.start()


@app.route("/")
def index():
    return render_template("receiver.html")


@app.route("/upload", methods=["POST"])
def upload():
    fname = request.headers.get("X-Filename", "file.dat")
    data = request.data
    with open(os.path.join(app.config["STORAGE"], fname), "wb") as f:
        f.write(data)
    return jsonify({"success": True, "message": f"Received {fname}"})


@app.route("/api/files")
def files():
    flist = [
        {
            "name": f,
            "size": os.path.getsize(os.path.join(app.config["STORAGE"], f)),
            "time": datetime.datetime.fromtimestamp(
                os.path.getmtime(os.path.join(app.config["STORAGE"], f))
            ).strftime("%H:%M:%S"),
        }
        for f in os.listdir(app.config["STORAGE"])
        if os.path.isfile(os.path.join(app.config["STORAGE"], f))
    ]
    return jsonify(flist)


@app.route("/api/status")
def status():
    return jsonify(
        {
            "device_name": DEVICE_NAME,
            "files_count": len(
                [
                    f
                    for f in os.listdir(app.config["STORAGE"])
                    if os.path.isfile(os.path.join(app.config["STORAGE"], f))
                ]
            ),
        }
    )


@app.route("/download/<path:filename>")
def download(filename):
    return send_from_directory(app.config["STORAGE"], filename, as_attachment=True)


@app.route("/view/<path:filename>")
def view_file(filename):
    return send_from_directory(app.config["STORAGE"], filename, as_attachment=False)


if __name__ == "__main__":
    print("=" * 60)
    print("🔐 Arnika Receiver - Post-Quantum Secure")
    print("=" * 60)
    print(f"Device: {DEVICE_NAME}")
    print(f"Receiver: http://localhost:9000")
    print(f"Status: Broadcasting on network (UDP port 9999)")
    print("=" * 60)
    app.run(host="0.0.0.0", port=9000, debug=True)
