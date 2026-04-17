import socket
import json
import threading
import time

DISCOVERY_PORT = 9999
BROADCAST_INTERVAL = 3


class PeerDiscovery:
    def __init__(self, name="Device", port=9000):
        self.name = name
        self.port = port
        self.peers = {}
        self.running = False
        self._setup_socket()

    def _setup_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(1)

    def start(self):
        self.running = True
        threading.Thread(target=self._broadcast_loop, daemon=True).start()
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def stop(self):
        self.running = False
        self.sock.close()

    def _broadcast_loop(self):
        while self.running:
            try:
                msg = json.dumps(
                    {
                        "type": "announce",
                        "name": self.name,
                        "port": self.port,
                        "time": time.time(),
                    }
                )
                self.sock.sendto(msg.encode(), ("<broadcast>", DISCOVERY_PORT))
            except:
                pass
            time.sleep(BROADCAST_INTERVAL)

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                msg = json.loads(data.decode())
                if msg["type"] == "announce" and msg.get("port"):
                    self.peers[addr[0]] = {
                        "name": msg["name"],
                        "port": msg["port"],
                        "ip": addr[0],
                        "last_seen": time.time(),
                    }
            except socket.timeout:
                pass
            except:
                pass

    def get_peers(self):
        current_time = time.time()
        return {
            ip: peer
            for ip, peer in self.peers.items()
            if current_time - peer["last_seen"] < 10
        }


def discover_peers(timeout=5):
    """Quick discovery function to find peers"""
    found = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)

    msg = json.dumps({"type": "announce", "name": "scanner", "port": 0})
    sock.sendto(msg.encode(), ("<broadcast>", DISCOVERY_PORT))

    try:
        while True:
            data, addr = sock.recvfrom(4096)
            msg = json.loads(data.decode())
            if msg["type"] == "announce" and msg.get("port", 0) > 0:
                found.append({"ip": addr[0], "name": msg["name"], "port": msg["port"]})
    except socket.timeout:
        pass

    return found


if __name__ == "__main__":
    print("Testing peer discovery...")
    peers = discover_peers(timeout=3)
    for p in peers:
        print(f"Found: {p['name']} at {p['ip']}:{p['port']}")
