#!/
echo "Stopping all Demo Processes..."
sudo pkill arnika
sudo pkill kms
sudo ip link delete dev wg0
sudo ip link delete dev wg1
echo "Cleanup Complete."