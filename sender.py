from flask import Flask, render_template, request, jsonify
import os, time, requests, subprocess

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["RECEIVER_URL"] = "http://localhost:9000"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


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
                    return parts[1].strip()[:16] + "..."  # Show first 16 chars
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
    psk = get_psk_details() if qsecure else None

    return jsonify(
        {
            "secure": qsecure,
            "files": files,
            "psk": psk,
            "security_info": {
                "algorithm": "Kyber512 + Curve25519 (Hybrid)",
                "key_exchange": "Post-Quantum ECDH",
                "tunnel": "WireGuard + Arnika (QKD PSK)",
                "protection": "Against quantum & classical attacks",
            }
            if qsecure
            else None,
        }
    )


@app.route("/upload", methods=["POST"])
def upload():
    qsecure = is_quantum_secure()
    if not qsecure:
        return jsonify(
            {"error": "Not quantum secure! File transfer blocked for safety."}
        ), 403

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
                f"{app.config['RECEIVER_URL']}/upload",
                data=f,
                headers={"X-Filename": file.filename, "X-Secure": "true"},
                timeout=30,
            )
            return jsonify(
                {"success": True, "message": "File sent via Quantum-Secure Tunnel!"}
            ) if r.status_code == 200 else jsonify({"error": "Failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("🔐 Arnika Secure File Transfer - Post-Quantum VPN")
    print("=" * 60)
    print("Sender: http://localhost:5000")
    print()
    print("Security Stack:")
    print("  ├── WireGuard (Post-Quantum Cryptography)")
    print("  ├── Arnika (QKD Key Injection)")
    print("  └── PSK: 256-bit quantum-safe key")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
