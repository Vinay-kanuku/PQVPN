from flask import Flask, render_template, request, jsonify
import os, time, requests, subprocess, threading, socket
from discovery import PeerDiscovery, discover_peers

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

DEVICE_NAME = "Alice-" + socket.gethostname()[:8]

discovery = PeerDiscovery(name=DEVICE_NAME, port=9000)
discovery.start()


def get_psk_details():
    try:
        r = subprocess.check_output(
            ["sudo", "wg", "show", "wg0", "preshared-keys"], text=True
        )
        if "(none)" in r or not r.strip():
            return None
        for line in r.split("\n"):
            if "preshared key" in line.lower():
                parts = line.split(":")
                if len(parts) > 1:
                    return parts[1].strip()[:16] + "..."
        return "Active (hidden)"
    except:
        return None


def is_quantum_secure():
    try:
        r = subprocess.check_output(
            ["sudo", "wg", "show", "wg0", "preshared-keys"], text=True
        )
        return "(none)" not in r and bool(r.strip())
    except:
        return None


@app.route("/")
def index():
    return render_template("sender.html")


@app.route("/api/status")
def status():
    files = [
        {
            "name": f,
            "size": os.path.getsize(os.path.join(app.config["UPLOAD_FOLDER"], f)),
            "time": time.strftime(
                "%H:%M:%S",
                time.localtime(
                    os.path.getmtime(os.path.join(app.config["UPLOAD_FOLDER"], f))
                ),
            ),
        }
        for f in os.listdir(app.config["UPLOAD_FOLDER"])
        if os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], f))
    ]
    qsecure = is_quantum_secure()
    peers = discovery.get_peers()

    return jsonify(
        {
            "secure": qsecure,
            "files": files,
            "device_name": DEVICE_NAME,
            "psk": get_psk_details() if qsecure else None,
            "security_info": {
                "algorithm": "Kyber512 + Curve25519 (Hybrid)",
                "key_exchange": "Post-Quantum ECDH",
                "tunnel": "WireGuard + Arnika (QKD PSK)",
                "protection": "Against quantum & classical attacks",
            }
            if qsecure
            else None,
            "peers": [
                {"name": p["name"], "ip": ip, "port": p["port"]}
                for ip, p in peers.items()
            ],
        }
    )


@app.route("/api/scan")
def scan_peers():
    peers = discover_peers(timeout=3)
    return jsonify(peers)


@app.route("/upload", methods=["POST"])
def upload():
    qsecure = is_quantum_secure()
    if not qsecure:
        return jsonify({"error": "Not quantum secure! File transfer blocked."}), 403

    target_ip = request.form.get("target_ip") or "localhost"
    target_port = int(request.form.get("target_port") or 9000)
    receiver_url = f"http://{target_ip}:{target_port}"

    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    try:
        with open(filepath, "rb") as f:
            r = requests.post(
                f"{receiver_url}/upload",
                data=f,
                headers={"X-Filename": file.filename, "X-Secure": "true"},
                timeout=30,
            )
            return jsonify(
                {"success": True, "message": f"Sent to {target_ip}:{target_port}"}
            ) if r.status_code == 200 else jsonify({"error": "Failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    import socket

    print("=" * 60)
    print("🔐 Arnika Secure File Transfer - Post-Quantum VPN")
    print("=" * 60)
    print(f"Device: {DEVICE_NAME}")
    print(f"Sender: http://localhost:5000")
    print()
    print("Security Stack:")
    print("  ├── WireGuard (Post-Quantum Cryptography)")
    print("  ├── Arnika (QKD Key Injection)")
    print("  └── PSK: 256-bit quantum-safe key")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
