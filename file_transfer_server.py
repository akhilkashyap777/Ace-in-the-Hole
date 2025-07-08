"""
File Transfer Server Module
Backend HTTP server that handles file uploads/downloads with 5GB support
FIXED: Real-time file deletion detection and cache invalidation
"""

import os
import socket
import threading
import json
import qrcode
import io
import base64
import time
import logging
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Configure logging for file transfer operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [VAULT_TRANSFER] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('vault_transfer.log')
    ]
)
logger = logging.getLogger('VaultTransfer')

# Optional Cython optimization for large file transfers
try:
    from cython_file_transfer import chunk_file_fast, calculate_transfer_metrics
    CYTHON_AVAILABLE = True
    logger.info("High-performance file transfer mode enabled")
except ImportError:
    CYTHON_AVAILABLE = False
    logger.info("Standard file transfer mode active")


class SecureFileTransferHandler(BaseHTTPRequestHandler):
    """HTTP handler for secure vault file transfers"""
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/':
            self.send_main_page()
        elif path == '/api/files':
            self.send_file_list()
        elif path.startswith('/download/'):
            self.send_file(path[10:])
        else:
            self.send_404()
    
    def do_POST(self):
        if self.path == '/upload':
            self.receive_file()
        else:
            self.send_404()
    
    def send_main_page(self):
        """Serve the beautiful web interface"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            html_file_path = os.path.join(current_dir, 'file_transfer_ui.html')
            
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            
        except FileNotFoundError:
            logger.error("Web interface file missing - please ensure file_transfer_ui.html exists")
            self._send_fallback_page()
        except Exception as e:
            logger.error(f"Failed to load web interface: {e}")
            self.send_error(500, "Interface loading failed")
    
    def _send_fallback_page(self):
        """Emergency fallback if HTML file is missing"""
        fallback_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Vault Transfer - Setup Required</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #1a1a1a; color: white; }
                .error { background: #ff4444; padding: 20px; border-radius: 10px; margin: 20px auto; max-width: 500px; }
            </style>
        </head>
        <body>
            <h1>⚠️ Setup Required</h1>
            <div class="error">
                <h3>Web Interface Missing</h3>
                <p>The file 'file_transfer_ui.html' is required but not found.</p>
                <p>Please ensure both Python and HTML files are in the same folder.</p>
            </div>
        </body>
        </html>
        """
        self.send_response(500)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(fallback_html.encode('utf-8'))
    
    def send_file_list(self):
        """Send list of available vault files"""
        try:
            transfer_server = self.server.transfer_server
            files = transfer_server.get_realtime_file_list()  # 🔥 FIXED: Use real-time instead of cached
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(json.dumps(files, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Failed to retrieve file list: {e}")
            self.send_error(500, "File list unavailable")
    
    def send_file(self, file_path):
        """Securely send file for download"""
        try:
            transfer_server = self.server.transfer_server
            full_path = transfer_server.resolve_file_path(file_path)
            
            if not full_path or not os.path.exists(full_path):
                logger.warning(f"Download attempt for non-existent file: {file_path}")
                self.send_404()
                return
            
            file_size = os.path.getsize(full_path)
            filename = os.path.basename(full_path)
            
            logger.info(f"Serving download: {filename} ({self._format_bytes(file_size)})")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(file_size))
            self.send_header('Cache-Control', 'no-cache')
            # Extended timeout for large files
            self.send_header('Keep-Alive', 'timeout=3600')
            self.end_headers()
            
            # Use optimized transfer for large files
            if CYTHON_AVAILABLE and file_size > 10 * 1024 * 1024:  # Use for files > 10MB
                chunk_file_fast(full_path, self.wfile)
            else:
                self._stream_file_chunks(full_path)
                
        except Exception as e:
            logger.error(f"Download failed for {file_path}: {e}")
            self.send_error(500, "Download failed")
    
    def _stream_file_chunks(self, file_path):
        """Stream file in optimized chunks"""
        try:
            # Use larger chunks for better performance with big files
            chunk_size = 1024 * 1024  # 1MB chunks for large files
            
            with open(file_path, 'rb') as file:
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            logger.info("Client disconnected during transfer")
        except Exception as e:
            logger.error(f"Streaming error: {e}")
    
    def receive_file(self):
        """Securely receive uploaded file with 5GB support"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            content_type = self.headers.get('Content-Type', '')
            
            # Validate upload
            if content_length == 0:
                raise ValueError("No file data received")
            
            # 🚀 INCREASED TO 5GB LIMIT
            max_size = 5 * 1024 * 1024 * 1024  # 5GB limit
            if content_length > max_size:
                raise ValueError(f"File too large ({self._format_bytes(content_length)}). Maximum: 5GB")
            
            logger.info(f"Receiving file upload: {self._format_bytes(content_length)}")
            
            # For large files, use streaming approach instead of loading all into memory
            if content_length > 100 * 1024 * 1024:  # 100MB threshold
                self._receive_large_file_streaming(content_length, content_type)
            else:
                self._receive_small_file_memory(content_length, content_type)
                
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            self._send_error_response(str(e))
    
    def _receive_small_file_memory(self, content_length, content_type):
        """Handle smaller files (< 100MB) in memory"""
        post_data = self.rfile.read(content_length)
        
        if 'multipart/form-data' not in content_type:
            raise ValueError("Invalid upload format")
        
        filename, file_data = self._parse_multipart_upload(content_type, post_data)
        
        if not filename or not file_data:
            raise ValueError("No valid file found in upload")
        
        self._save_uploaded_file(filename, file_data)
    
    def _receive_large_file_streaming(self, content_length, content_type):
        """Handle large files (>= 100MB) with streaming to avoid memory issues"""
        if 'multipart/form-data' not in content_type:
            raise ValueError("Invalid upload format")
        
        # Extract boundary
        boundary = self._extract_boundary(content_type)
        if not boundary:
            raise ValueError("Upload boundary not found")
        
        # Stream and parse multipart data
        filename, temp_file_path = self._stream_parse_multipart(content_length, boundary)
        
        if not filename or not temp_file_path:
            raise ValueError("No valid file found in upload")
        
        # Move temp file to vault
        with open(temp_file_path, 'rb') as temp_file:
            file_data = temp_file.read()
        
        os.unlink(temp_file_path)  # Clean up temp file
        self._save_uploaded_file(filename, file_data)
    
    def _stream_parse_multipart(self, content_length, boundary):
        """Stream parse multipart data for large files"""
        boundary_bytes = f'--{boundary}'.encode()
        filename = None
        temp_file_path = None
        
        # Create temporary file for streaming
        temp_fd, temp_file_path = tempfile.mkstemp()
        
        try:
            bytes_read = 0
            in_file_data = False
            
            # Read in chunks and parse
            buffer = b''
            chunk_size = 64 * 1024  # 64KB chunks
            
            with os.fdopen(temp_fd, 'wb') as temp_file:
                while bytes_read < content_length:
                    remaining = min(chunk_size, content_length - bytes_read)
                    chunk = self.rfile.read(remaining)
                    if not chunk:
                        break
                    
                    bytes_read += len(chunk)
                    buffer += chunk
                    
                    # Simple parsing - look for filename in headers
                    if not filename and b'filename=' in buffer:
                        filename = self._extract_filename_from_buffer(buffer)
                    
                    # Start writing file data after headers
                    if not in_file_data and b'\r\n\r\n' in buffer:
                        header_end = buffer.find(b'\r\n\r\n') + 4
                        file_start = buffer[header_end:]
                        buffer = b''
                        in_file_data = True
                        if file_start:
                            temp_file.write(file_start)
                    elif in_file_data:
                        # Write chunk to temp file
                        temp_file.write(buffer)
                        buffer = b''
            
            return filename, temp_file_path
            
        except Exception as e:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise e
    
    def _extract_boundary(self, content_type):
        """Extract boundary from content type"""
        for part in content_type.split(';'):
            part = part.strip()
            if part.startswith('boundary='):
                return part.split('=', 1)[1].strip('"')
        return None
    
    def _extract_filename_from_buffer(self, buffer):
        """Extract filename from buffer containing headers"""
        try:
            buffer_str = buffer.decode('utf-8', errors='ignore')
            for line in buffer_str.split('\r\n'):
                if 'filename=' in line:
                    start = line.find('filename="')
                    if start != -1:
                        start += len('filename="')
                        end = line.find('"', start)
                        if end != -1:
                            return line[start:end]
        except:
            pass
        return None
    
    def _parse_multipart_upload(self, content_type, post_data):
        """Extract file from multipart form data (for smaller files)"""
        boundary = self._extract_boundary(content_type)
        
        if not boundary:
            raise ValueError("Upload boundary not found")
        
        boundary_bytes = f'--{boundary}'.encode()
        parts = post_data.split(boundary_bytes)
        
        for part in parts:
            if b'filename=' in part and b'Content-Disposition: form-data' in part:
                if b'\r\n\r\n' not in part:
                    continue
                
                headers_part, content_part = part.split(b'\r\n\r\n', 1)
                headers_str = headers_part.decode('utf-8', errors='ignore')
                
                filename = None
                for line in headers_str.split('\r\n'):
                    if 'filename=' in line:
                        start = line.find('filename="')
                        if start != -1:
                            start += len('filename="')
                            end = line.find('"', start)
                            if end != -1:
                                filename = line[start:end]
                                break
                
                file_data = content_part
                if file_data.endswith(b'\r\n'):
                    file_data = file_data[:-2]
                
                return filename, file_data
        
        return None, None
    
    def _save_uploaded_file(self, filename, file_data):
        """Save uploaded file to vault"""
        transfer_server = self.server.transfer_server
        saved_path = transfer_server.save_to_vault(filename, file_data)
        
        if saved_path:
            # 🔥 FIXED: Force immediate file system update
            transfer_server.invalidate_cache()
            logger.info(f"Upload successful: {filename} ({self._format_bytes(len(file_data))})")
            
            self._send_success_response({
                'status': 'success',
                'message': f'Successfully saved {filename}',
                'filename': filename,
                'size': len(file_data),
                'location': os.path.basename(saved_path)
            })
        else:
            raise ValueError("Failed to save file to vault")
    
    def _send_success_response(self, data):
        """Send formatted success response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def _send_error_response(self, error_message):
        """Send formatted error response"""
        try:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            error_data = {
                'status': 'error',
                'error': error_message,
                'timestamp': time.time()
            }
            self.wfile.write(json.dumps(error_data).encode('utf-8'))
        except:
            pass
    
    def _format_bytes(self, bytes_count):
        """Human-readable file size formatting"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
    
    def send_404(self):
        self.send_error(404, "Resource not found")
    
    def log_message(self, format, *args):
        pass


class VaultFileTransferServer:
    """Secure file transfer server for vault contents with 5GB support and real-time file detection"""
    
    def __init__(self, vault_app):
        self.vault_app = vault_app
        self.secure_storage = vault_app.secure_storage
        self.http_server = None
        self.server_thread = None
        self.is_running = False
        self.server_ip = None
        self.server_port = None
        
        # 🔥 FIXED: Enhanced file tracking system
        self._cached_files = None
        self._file_timestamps = {}  # Track individual file modification times
        self._directory_timestamps = {}  # Track directory modification times
        self._cache_lock = threading.Lock()
        
        # 🔥 NEW: Real-time monitoring thread
        self._monitor_thread = None
        self._should_monitor = False
    
    def detect_local_ip(self):
        """Detect the local network IP address"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                local_ip = sock.getsockname()[0]
            return local_ip
        except Exception as e:
            logger.warning(f"IP detection failed, using localhost: {e}")
            return "127.0.0.1"
    
    def find_available_port(self):
        """Find an available port for the server"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('', 0))
            return sock.getsockname()[1]
    
    def start_server(self):
        """Start the secure file transfer server"""
        if self.is_running:
            return False, "Server is already running"
        
        try:
            self.server_ip = self.detect_local_ip()
            self.server_port = self.find_available_port()
            
            # Create HTTP server with extended timeout for large files
            self.http_server = HTTPServer((self.server_ip, self.server_port), SecureFileTransferHandler)
            self.http_server.timeout = 3600  # 1 hour timeout for large transfers
            self.http_server.transfer_server = self
            
            # Start in background thread
            self.server_thread = threading.Thread(
                target=self.http_server.serve_forever,
                daemon=True,
                name="VaultTransferServer"
            )
            self.server_thread.start()
            
            # 🔥 NEW: Start file monitoring
            self._start_file_monitoring()
            
            self.is_running = True
            server_url = f"http://{self.server_ip}:{self.server_port}"
            
            logger.info(f"Vault transfer server started: {server_url} (5GB max file size)")
            return True, server_url
            
        except Exception as e:
            logger.error(f"Server startup failed: {e}")
            return False, f"Failed to start server: {e}"
    
    def stop_server(self):
        """Safely stop the file transfer server"""
        if not self.is_running:
            return
        
        try:
            # 🔥 NEW: Stop file monitoring first
            self._stop_file_monitoring()
            
            if self.http_server:
                self.http_server.shutdown()
                self.http_server.server_close()
            
            with self._cache_lock:
                self._cached_files = None
                self._file_timestamps.clear()
                self._directory_timestamps.clear()
            
            self.is_running = False
            logger.info("Vault transfer server stopped")
            
        except Exception as e:
            logger.error(f"Server shutdown error: {e}")
    
    def _start_file_monitoring(self):
        """🔥 NEW: Start background file monitoring thread"""
        self._should_monitor = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_file_changes,
            daemon=True,
            name="VaultFileMonitor"
        )
        self._monitor_thread.start()
        logger.info("Real-time file monitoring started")
    
    def _stop_file_monitoring(self):
        """🔥 NEW: Stop background file monitoring"""
        self._should_monitor = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        logger.info("File monitoring stopped")
    
    def _monitor_file_changes(self):
        """🔥 NEW: Background thread to monitor file system changes"""
        while self._should_monitor and self.is_running:
            try:
                if self._has_files_changed():
                    logger.info("File changes detected, invalidating cache")
                    self.invalidate_cache()
                
                # Check every 2 seconds (much faster than old 30-second cache)
                time.sleep(2.0)
                
            except Exception as e:
                logger.error(f"File monitoring error: {e}")
                time.sleep(5.0)  # Wait longer on error
    
    def _has_files_changed(self):
        """🔥 NEW: Check if any files or directories have changed"""
        try:
            vault_categories = {
                'photos': self.secure_storage.get_vault_directory('photos'),
                'videos': self.secure_storage.get_vault_directory('videos'),
                'audio': self.secure_storage.get_vault_directory('audio'),
                'documents': self.secure_storage.get_vault_directory('documents')
            }
            
            # Check directory modification times first (faster)
            for category, directory in vault_categories.items():
                if directory and os.path.exists(directory):
                    try:
                        current_mtime = os.path.getmtime(directory)
                        if category not in self._directory_timestamps:
                            self._directory_timestamps[category] = current_mtime
                            continue
                        
                        if current_mtime != self._directory_timestamps[category]:
                            self._directory_timestamps[category] = current_mtime
                            return True
                            
                    except OSError:
                        continue
            
            return False
            
        except Exception as e:
            logger.error(f"Change detection error: {e}")
            return True  # Assume changed on error for safety
    
    def invalidate_cache(self):
        """🔥 NEW: Force immediate cache invalidation"""
        with self._cache_lock:
            self._cached_files = None
            self._file_timestamps.clear()
            logger.debug("File cache invalidated")
    
    def get_realtime_file_list(self):
        """🔥 NEW: Get real-time file list (replaces cached version)"""
        # Always scan fresh to ensure accuracy
        return self._scan_vault_files()
    
    def get_cached_file_list(self):
        """🔥 DEPRECATED: Keep for backward compatibility but use real-time"""
        return self.get_realtime_file_list()
    
    def refresh_file_cache(self):
        """🔥 UPDATED: Force refresh (now just invalidates since we use real-time)"""
        self.invalidate_cache()
    
    def _scan_vault_files(self):
        """Scan all vault categories for files"""
        files = []
        
        vault_categories = {
            'photos': self.secure_storage.get_vault_directory('photos'),
            'videos': self.secure_storage.get_vault_directory('videos'),
            'audio': self.secure_storage.get_vault_directory('audio'),
            'documents': self.secure_storage.get_vault_directory('documents')
        }
        
        for category, directory in vault_categories.items():
            if directory and os.path.exists(directory):
                try:
                    with os.scandir(directory) as entries:
                        for entry in entries:
                            if entry.is_file():
                                try:
                                    stat_info = entry.stat()
                                    files.append({
                                        'name': entry.name,
                                        'category': category,
                                        'size': stat_info.st_size,
                                        'path': f"{category}/{entry.name}",
                                        'modified': stat_info.st_mtime
                                    })
                                except (OSError, IOError):
                                    continue
                except (OSError, IOError):
                    continue
        
        files.sort(key=lambda x: x.get('modified', 0), reverse=True)
        return files
    
    def resolve_file_path(self, relative_path):
        """Safely resolve relative path to absolute vault path"""
        try:
            path_parts = relative_path.split('/', 1)
            if len(path_parts) != 2:
                return None
            
            category, filename = path_parts
            vault_directory = self.secure_storage.get_vault_directory(category)
            
            if not vault_directory:
                return None
            
            safe_filename = os.path.basename(filename)
            full_path = os.path.join(vault_directory, safe_filename)
            
            if not full_path.startswith(vault_directory):
                logger.warning(f"Path traversal attempt blocked: {relative_path}")
                return None
            
            return full_path
            
        except Exception as e:
            logger.error(f"Path resolution failed for {relative_path}: {e}")
            return None
    
    def save_to_vault(self, filename, file_data):
        """Save uploaded file to appropriate vault category"""
        try:
            category = self._categorize_file(filename)
            vault_directory = self.secure_storage.get_vault_directory(category)
            
            if not vault_directory:
                logger.error(f"Vault directory unavailable for category: {category}")
                return None
            
            os.makedirs(vault_directory, exist_ok=True)
            
            safe_filename = self._ensure_safe_filename(filename)
            file_path = os.path.join(vault_directory, safe_filename)
            file_path = self._resolve_filename_conflict(file_path)
            
            # Write file securely (handle large files efficiently)
            if isinstance(file_data, bytes) and len(file_data) > 100 * 1024 * 1024:  # > 100MB
                # Write in chunks for very large files
                with open(file_path, 'wb') as f:
                    chunk_size = 1024 * 1024  # 1MB chunks
                    for i in range(0, len(file_data), chunk_size):
                        f.write(file_data[i:i + chunk_size])
            else:
                with open(file_path, 'wb') as f:
                    f.write(file_data)
            
            if hasattr(self.secure_storage, '_set_secure_permissions_if_needed'):
                self.secure_storage._set_secure_permissions_if_needed(file_path)
            
            logger.info(f"File saved to vault: {os.path.basename(file_path)} in {category}")
            return file_path
            
        except Exception as e:
            logger.error(f"Vault save failed for {filename}: {e}")
            return None
    
    def _categorize_file(self, filename):
        """Determine vault category based on file extension"""
        extension = os.path.splitext(filename)[1].lower()
        
        categories = {
            'photos': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg', '.heic', '.raw'],
            'videos': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus']
        }
        
        for category, extensions in categories.items():
            if extension in extensions:
                return category
        
        return 'documents'
    
    def _ensure_safe_filename(self, filename):
        """Sanitize filename for security"""
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-() "
        safe_filename = ''.join(c for c in filename if c in safe_chars)
        
        if not safe_filename.strip():
            safe_filename = f"uploaded_file_{int(time.time())}"
        
        return safe_filename[:255]
    
    def _resolve_filename_conflict(self, file_path):
        """Generate unique filename if conflict exists"""
        if not os.path.exists(file_path):
            return file_path
        
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        name, extension = os.path.splitext(filename)
        
        counter = 1
        while True:
            new_filename = f"{name}_{counter}{extension}"
            new_path = os.path.join(directory, new_filename)
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    
    def generate_qr_code(self, url):
        """Generate QR code for easy mobile access"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            qr_image.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return qr_base64
        except Exception as e:
            logger.warning(f"QR code generation failed: {e}")
            return None