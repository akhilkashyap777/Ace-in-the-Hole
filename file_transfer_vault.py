import os
import socket
import threading
import json
import qrcode
import io
import base64
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivy.clock import Clock

# Optional: Try to import Cython optimized functions
try:
    from cython_file_transfer import chunk_file_fast, calculate_transfer_metrics
    CYTHON_AVAILABLE = True
    print("🚀 Cython optimization available for file transfer")
except ImportError:
    CYTHON_AVAILABLE = False
    print("⚡ Using pure Python for file transfer (still fast!)")

class FileTransferHandler(BaseHTTPRequestHandler):
    """HTTP handler for file transfer requests"""
    
    def do_GET(self):
        """Handle GET requests - file listing and download"""
        path = urlparse(self.path).path
        
        if path == '/':
            self.send_main_page()
        elif path == '/api/files':
            self.send_file_list()
        elif path.startswith('/download/'):
            self.send_file(path[10:])  # Remove '/download/'
        else:
            self.send_404()
    
    def do_POST(self):
        """Handle POST requests - file upload"""
        if self.path == '/upload':
            self.receive_file()
        else:
            self.send_404()
    
    def send_main_page(self):
        """Send main transfer interface"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Secret Vault - File Transfer</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: white; }
                .container { max-width: 600px; margin: 0 auto; }
                .file-list { background: #2a2a2a; padding: 15px; border-radius: 8px; margin: 10px 0; }
                .upload-area { background: #333; padding: 20px; border-radius: 8px; text-align: center; }
                button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #45a049; }
                .progress { width: 100%; background: #ddd; border-radius: 4px; }
                .progress-bar { width: 0%; height: 20px; background: #4CAF50; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔒 Secret Vault File Transfer</h1>
                
                <div class="upload-area">
                    <h3>📤 Upload Files</h3>
                    <input type="file" id="fileInput" multiple>
                    <button onclick="uploadFiles()">Upload Selected Files</button>
                    <div class="progress" id="uploadProgress" style="display:none;">
                        <div class="progress-bar" id="uploadBar"></div>
                    </div>
                </div>
                
                <div class="file-list">
                    <h3>📁 Available Files</h3>
                    <div id="fileList">Loading...</div>
                </div>
            </div>
            
            <script>
                function loadFiles() {
                    fetch('/api/files')
                        .then(response => response.json())
                        .then(files => {
                            const list = document.getElementById('fileList');
                            list.innerHTML = files.map(file => 
                                `<div style="margin: 5px 0; padding: 10px; background: #444; border-radius: 4px;">
                                    <strong>${file.name}</strong> (${file.size} bytes)
                                    <a href="/download/${file.path}" download style="float: right; color: #4CAF50;">📥 Download</a>
                                </div>`
                            ).join('');
                        });
                }
                
                function uploadFiles() {
                    const input = document.getElementById('fileInput');
                    const progress = document.getElementById('uploadProgress');
                    const bar = document.getElementById('uploadBar');
                    
                    if (input.files.length === 0) return;
                    
                    progress.style.display = 'block';
                    
                    for (let file of input.files) {
                        const formData = new FormData();
                        formData.append('file', file);
                        
                        fetch('/upload', {
                            method: 'POST',
                            body: formData
                        }).then(() => {
                            loadFiles();
                            bar.style.width = '100%';
                            setTimeout(() => progress.style.display = 'none', 2000);
                        });
                    }
                }
                
                loadFiles();
                setInterval(loadFiles, 5000); // Refresh every 5 seconds
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_file_list(self):
        """✅ OPTIMIZED: Send cached list of available files"""
        try:
            transfer_server = self.server.transfer_server
            files = transfer_server.get_available_files_cached()  # ✅ Use cached version
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(files).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def send_file(self, file_path):
        """Send a file for download"""
        try:
            transfer_server = self.server.transfer_server
            full_path = transfer_server.get_file_path(file_path)
            
            if not os.path.exists(full_path):
                self.send_404()
                return
            
            file_size = os.path.getsize(full_path)
            filename = os.path.basename(full_path)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(file_size))
            self.end_headers()
            
            # Use Cython for fast file streaming if available
            if CYTHON_AVAILABLE:
                chunk_file_fast(full_path, self.wfile)
            else:
                self.stream_file_python(full_path)
                
        except Exception as e:
            self.send_error(500, str(e))
    
    def stream_file_python(self, file_path):
        """✅ OPTIMIZED: Pure Python file streaming with larger chunks"""
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(65536)  # ✅ Increased from 8192 to 64KB chunks
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            # ✅ Handle client disconnection gracefully
            pass
    
    def receive_file(self):
        """Receive uploaded file"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse multipart form data (simplified)
            boundary = self.headers['Content-Type'].split('boundary=')[1]
            parts = post_data.split(f'--{boundary}'.encode())
            
            for part in parts:
                if b'filename=' in part:
                    # Extract filename and file data
                    lines = part.split(b'\r\n')
                    filename = None
                    file_data = b''
                    
                    for i, line in enumerate(lines):
                        if b'filename=' in line:
                            filename = line.split(b'filename="')[1].split(b'"')[0].decode()
                        elif line == b'' and i < len(lines) - 2:
                            file_data = b'\r\n'.join(lines[i+1:-1])
                            break
                    
                    if filename and file_data:
                        transfer_server = self.server.transfer_server
                        transfer_server.save_uploaded_file(filename, file_data)
                        # ✅ Invalidate cache after new file upload
                        transfer_server.invalidate_file_cache()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "success"}')
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def send_404(self):
        self.send_error(404, "File not found")
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass

class SecureFileTransferServer:
    """Main file transfer server class"""
    
    def __init__(self, vault_app):
        self.app = vault_app
        self.secure_storage = vault_app.secure_storage
        self.server = None
        self.server_thread = None
        self.running = False
        self.port = None
        self.local_ip = None
        
        # ✅ OPTIMIZATION: File list caching to prevent expensive directory scans
        self._file_cache = None
        self._cache_timestamp = 0
        self._cache_ttl = 30  # Cache for 30 seconds
        self._cache_lock = threading.Lock()
        
    def get_local_ip(self):
        """Get local IP address"""
        try:
            # Connect to remote address to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def find_free_port(self):
        """Find a free port to use"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]
    
    def start_server(self):
        """Start the file transfer server"""
        if self.running:
            return False, "Server already running"
        
        try:
            self.local_ip = self.get_local_ip()
            self.port = self.find_free_port()
            
            # Create HTTP server
            self.server = HTTPServer((self.local_ip, self.port), FileTransferHandler)
            self.server.transfer_server = self  # Reference for handlers
            
            # Start server in background thread
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            self.running = True
            
            print(f"🌐 File transfer server started")
            print(f"📡 URL: http://{self.local_ip}:{self.port}")
            
            return True, f"http://{self.local_ip}:{self.port}"
            
        except Exception as e:
            return False, f"Failed to start server: {e}"
    
    def stop_server(self):
        """✅ OPTIMIZED: Stop the file transfer server with proper cleanup"""
        if not self.running:
            return
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        # ✅ Clear cache on server stop
        with self._cache_lock:
            self._file_cache = None
            self._cache_timestamp = 0
        
        self.running = False
        print("🛑 File transfer server stopped")
    
    def invalidate_file_cache(self):
        """✅ OPTIMIZATION: Invalidate file cache when files change"""
        with self._cache_lock:
            self._file_cache = None
            self._cache_timestamp = 0
    
    def get_available_files_cached(self):
        """✅ OPTIMIZATION: Get cached list of files to avoid expensive directory scans"""
        current_time = time.time()
        
        with self._cache_lock:
            # Check if cache is valid
            if (self._file_cache is not None and 
                current_time - self._cache_timestamp < self._cache_ttl):
                return self._file_cache.copy()
        
        # Cache miss or expired, rebuild cache
        files = self._scan_files()
        
        with self._cache_lock:
            self._file_cache = files.copy()
            self._cache_timestamp = current_time
        
        return files
    
    def get_available_files(self):
        """Get list of files available for download (original method for compatibility)"""
        return self._scan_files()
    
    def _scan_files(self):
        """✅ OPTIMIZATION: Internal method to scan files with error handling"""
        files = []
        
        # Get files from all vault directories
        vault_dirs = {
            'photos': self.secure_storage.get_vault_directory('photos'),
            'videos': self.secure_storage.get_vault_directory('videos'),
            'audio': self.secure_storage.get_vault_directory('audio'),
            'documents': self.secure_storage.get_vault_directory('documents')
        }
        
        for category, directory in vault_dirs.items():
            if os.path.exists(directory):
                try:
                    # ✅ Use os.scandir for better performance
                    with os.scandir(directory) as entries:
                        for entry in entries:
                            if entry.is_file():
                                try:
                                    stat_result = entry.stat()
                                    files.append({
                                        'name': entry.name,
                                        'category': category,
                                        'size': stat_result.st_size,
                                        'path': f"{category}/{entry.name}"
                                    })
                                except (OSError, IOError):
                                    # ✅ Skip files that can't be accessed
                                    continue
                except (OSError, IOError) as e:
                    print(f"⚠️ Error scanning directory {directory}: {e}")
                    continue
        
        return files
    
    def get_file_path(self, relative_path):
        """Get full file path from relative path"""
        parts = relative_path.split('/', 1)
        if len(parts) != 2:
            return None
        
        category, filename = parts
        directory = self.secure_storage.get_vault_directory(category)
        return os.path.join(directory, filename)
    
    def save_uploaded_file(self, filename, file_data):
        """Save uploaded file to appropriate vault directory"""
        # Determine file type and save to appropriate directory
        category = self.determine_file_category(filename)
        directory = self.secure_storage.get_vault_directory(category)
        
        # Handle filename conflicts
        file_path = os.path.join(directory, filename)
        counter = 1
        original_path = file_path
        while os.path.exists(file_path):
            name, ext = os.path.splitext(original_path)
            file_path = f"{name}_{counter}{ext}"
            counter += 1
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Set secure permissions
        if hasattr(self.secure_storage, 'set_secure_permissions'):
            self.secure_storage.set_secure_permissions(file_path)
        elif hasattr(self.secure_storage, '_set_secure_permissions_if_needed'):
            self.secure_storage._set_secure_permissions_if_needed(file_path)
        
        print(f"📥 File received: {filename} -> {file_path}")
        return file_path
    
    def determine_file_category(self, filename):
        """Determine which vault category a file belongs to"""
        ext = os.path.splitext(filename)[1].lower()
        
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg', '.heic']
        video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
        audio_exts = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
        
        if ext in image_exts:
            return 'photos'
        elif ext in video_exts:
            return 'videos'
        elif ext in audio_exts:
            return 'audio'
        else:
            return 'documents'
    
    def generate_qr_code(self, url):
        """Generate QR code for easy sharing"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 for display
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
        except:
            return None

class FileTransferUI(MDBoxLayout):
    """File Transfer UI Widget"""
    
    def __init__(self, vault_app):
        super().__init__(orientation='vertical', spacing=20, padding=20)
        self.app = vault_app
        self.transfer_server = SecureFileTransferServer(vault_app)
        
        self.create_ui()
    
    def create_ui(self):
        """Create the file transfer interface"""
        # Title
        title = MDLabel(
            text='📡 WiFi File Transfer',
            font_style="H4",
            halign="center",
            size_hint_y=None,
            height="60dp"
        )
        self.add_widget(title)
        
        # Server controls
        server_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height="200dp",
            padding="20dp",
            spacing="15dp"
        )
        
        self.status_label = MDLabel(
            text='Server Status: Stopped',
            font_style="Body1",
            halign="center"
        )
        server_card.add_widget(self.status_label)
        
        self.url_label = MDLabel(
            text='',
            font_style="Body2",
            halign="center"
        )
        server_card.add_widget(self.url_label)
        
        # Control buttons
        button_layout = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height="50dp")
        
        self.start_btn = MDRaisedButton(text='Start Server', size_hint_x=0.5)
        self.start_btn.bind(on_press=self.start_server)
        button_layout.add_widget(self.start_btn)
        
        self.stop_btn = MDRaisedButton(text='Stop Server', size_hint_x=0.5, disabled=True)
        self.stop_btn.bind(on_press=self.stop_server)
        button_layout.add_widget(self.stop_btn)
        
        server_card.add_widget(button_layout)
        self.add_widget(server_card)
        
        # Instructions
        instructions = MDLabel(
            text='Instructions:\n1. Start the server\n2. Connect other devices to the same WiFi\n3. Open the URL on other devices\n4. Transfer files!',
            font_style="Body2",
            size_hint_y=None,
            height="120dp"
        )
        self.add_widget(instructions)
        
        # Back button
        back_btn = MDRaisedButton(
            text='← Back to Vault',
            size_hint_y=None,
            height="50dp"
        )
        back_btn.bind(on_press=self.back_to_vault)
        self.add_widget(back_btn)
    
    def start_server(self, instance):
        """Start the file transfer server"""
        success, result = self.transfer_server.start_server()
        
        if success:
            self.status_label.text = 'Server Status: Running ✅'
            self.url_label.text = f'URL: {result}'
            self.start_btn.disabled = True
            self.stop_btn.disabled = False
        else:
            self.status_label.text = f'Error: {result}'
    
    def stop_server(self, instance):
        """Stop the file transfer server"""
        self.transfer_server.stop_server()
        self.status_label.text = 'Server Status: Stopped'
        self.url_label.text = ''
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
    
    def back_to_vault(self, instance):
        """Return to main vault"""
        self.transfer_server.stop_server()  # ✅ Ensure proper cleanup
        self.app.show_vault_main()

# Integration function
def integrate_file_transfer(vault_app):
    """Integrate file transfer with the main vault app"""
    
    def show_file_transfer():
        """Show file transfer interface"""
        vault_app.main_layout.clear_widgets()
        
        # Create file transfer widget
        transfer_ui = FileTransferUI(vault_app)
        vault_app.main_layout.add_widget(transfer_ui)
        
        vault_app.current_screen = 'file_transfer'
    
    # Add method to vault app
    vault_app.show_file_transfer = show_file_transfer
    
    print("📡 File Transfer integrated successfully")
    print("🔒 Uses your existing secure storage system")
    print("🌐 WiFi-based transfer with web interface")

if __name__ == "__main__":
    print("📡 File Transfer module ready for integration")
    print("🔧 Add integrate_file_transfer(self) to your main.py")
    print("🌐 WiFi-based transfer with secure storage integration")