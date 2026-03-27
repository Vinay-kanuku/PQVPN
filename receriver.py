import http.server
import socketserver
import os

# Configuration
PORT = 9000
BIND_IP = "10.0.0.2" 
STORAGE_DIR = "bob_secure_storage"

# Ensure storage directory exists
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

class SecureHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read the file size
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Get filename from custom header
            filename = self.headers.get('X-Filename', 'received_data.txt')
            
            # Save the file
            # We are NOT changing directory, so this path is now correct
            file_path = os.path.join(STORAGE_DIR, filename)
            
            with open(file_path, 'wb') as f:
                f.write(post_data)
                
            print(f"Received secure file: {filename} ({content_length} bytes)")
            
            # Send confirmation
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"File received successfully")
        except Exception as e:
            print(f"Error handling request: {e}")
            self.send_error(500, f"Server Error: {e}")

# Start the server
# REMOVED: os.chdir(STORAGE_DIR) - This was causing the path error!

# Allow address reuse so you don't get "Address already in use" errors if you restart quickly
socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer((BIND_IP, PORT), SecureHandler) as httpd:
    print(f"🔒 Bob is listening on Secure VPN IP {BIND_IP}:{PORT}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()