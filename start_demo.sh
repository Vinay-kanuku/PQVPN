 

 
echo "🧹 Cleaning up old demo environment..."
sudo pkill arnika
sudo pkill kms
sudo ip link delete dev wg0 2>/dev/null
sudo ip link delete dev wg1 2>/dev/null
sleep 1

# 2. START KMS (The Quantum Source)
echo "Starting KMS Simulator..."
./tools/kms > kms.log 2>&1 &
KMS_PID=$!
sleep 1

# 3. SETUP NETWORK (The Roads)
echo "Rx Building WireGuard Interfaces..."
# Alice (wg0)
sudo ip link add dev wg0 type wireguard
sudo ip address add 10.0.0.1/24 dev wg0
sudo wg set wg0 listen-port 51820 private-key ci/node-a/node-a.key peer yfJp6iGwLECj1Ni+XgTR2jUPpLNt+HyWhafefISxMgg= allowed-ips 10.0.0.2/32 endpoint 127.0.0.1:51821
sudo ip link set up dev wg0

# Bob (wg1)
sudo ip link add dev wg1 type wireguard
sudo ip address add 10.0.0.2/24 dev wg1
sudo wg set wg1 listen-port 51821 private-key ci/node-b/node-b.key peer 9KOGnoloZDb1k5Tx8yXTqahK/v05FloIYu5mWdLwpRQ= allowed-ips 10.0.0.1/32 endpoint 127.0.0.1:51820
sudo ip link set up dev wg1

# 4. START ARNIKA (The Security Agents)
echo "Starting Arnika Agents (Alice & Bob)..."

# Start Alice
sudo nohup env LISTEN_ADDRESS=127.0.0.1:9999 \
SERVER_ADDRESS=127.0.0.1:9998 \
INTERVAL=10s \
KMS_URL="http://localhost:8080/api/v1/keys/CONSA" \
WIREGUARD_INTERFACE=wg0 \
WIREGUARD_PEER_PUBLIC_KEY="yfJp6iGwLECj1Ni+XgTR2jUPpLNt+HyWhafefISxMgg=" \
./build/arnika > alice.log 2>&1 &

# Start Bob
sudo nohup env LISTEN_ADDRESS=127.0.0.1:9998 \
SERVER_ADDRESS=127.0.0.1:9999 \
INTERVAL=10s \
KMS_URL="http://localhost:8080/api/v1/keys/CONSB" \
WIREGUARD_INTERFACE=wg1 \
WIREGUARD_PEER_PUBLIC_KEY="9KOGnoloZDb1k5Tx8yXTqahK/v05FloIYu5mWdLwpRQ=" \
./build/arnika > bob.log 2>&1 &

# 5. VERIFICATION
echo "Waiting for Quantum Handshake (5 seconds)..."
sleep 5


echo "ENVIRONMENT READY!"
echo "Check below: You should see 'preshared key: (hidden)'"
sudo wg show

