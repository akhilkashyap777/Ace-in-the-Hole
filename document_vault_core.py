import os
import shutil
import threading
import mimetypes
from datetime import datetime
from kivy.clock import Clock
import re
import tkinter as tk
from tkinter import filedialog

# Desktop-only version - All Android code removed
ANDROID = False

class DocumentVaultCore:
    """
    Universal Document Vault - Handles ANY non-media file type
    
    Desktop compatible: Windows, macOS, Linux
    Future-ready: Extensible for contacts, passwords, bookmarks, etc.
    """
    
    # EXTENSIBLE FILE TYPE CATEGORIES
    FILE_CATEGORIES = {
        'documents': {
            'extensions': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages', 
                          '.md', '.tex', '.epub', '.mobi', '.azw', '.azw3'],
            'icon': '📄',
            'display_name': 'Documents',
            'description': 'PDFs, Word docs, text files, e-books'
        },
        'spreadsheets': {
            'extensions': ['.xls', '.xlsx', '.csv', '.ods', '.numbers', '.tsv'],
            'icon': '📊',
            'display_name': 'Spreadsheets', 
            'description': 'Excel, CSV, data files'
        },
        'presentations': {
            'extensions': ['.ppt', '.pptx', '.odp', '.key'],
            'icon': '📽️',
            'display_name': 'Presentations',
            'description': 'PowerPoint, Keynote slides'
        },
        'code': {
            'extensions': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h',
                          '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.ts', '.jsx',
                          '.vue', '.sql', '.json', '.xml', '.yaml', '.yml', '.toml',
                          '.ini', '.cfg', '.conf', '.sh', '.bat', '.ps1'],
            'icon': '💻',
            'display_name': 'Code & Scripts',
            'description': 'Programming files, config files'
        },
        'archives': {
            'extensions': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', 
                          '.tar.gz', '.tar.bz2', '.tar.xz'],
            'icon': '📦',
            'display_name': 'Archives',
            'description': 'Compressed files, backups'
        },
        'executables': {
            'extensions': ['.apk', '.exe', '.msi', '.deb', '.rpm', '.dmg', '.pkg',
                          '.app', '.appimage', '.flatpak', '.snap'],
            'icon': '⚙️',
            'display_name': 'Applications',
            'description': 'Executable files, installers'
        },
        'data': {
            'extensions': ['.db', '.sqlite', '.sqlite3', '.sql', '.log', '.backup',
                          '.bak', '.tmp', '.cache', '.dat', '.bin'],
            'icon': '💾',
            'display_name': 'Data Files',
            'description': 'Databases, logs, backups'
        },
        # FUTURE CATEGORIES - Ready for implementation
        'contacts': {
            'extensions': ['.vcf', '.contact', '.abbu', '.ldif'],
            'icon': '👥',
            'display_name': 'Contacts',
            'description': 'Contact files, address books'
        },
        'certificates': {
            'extensions': ['.crt', '.pem', '.p12', '.pfx', '.key', '.cer'],
            'icon': '🔐',
            'display_name': 'Certificates',
            'description': 'Security certificates, keys'
        },
        'fonts': {
            'extensions': ['.ttf', '.otf', '.woff', '.woff2', '.eot'],
            'icon': '🔤',
            'display_name': 'Fonts',
            'description': 'Font files'
        },
        'other': {
            'extensions': [],  # Catch-all for unknown types
            'icon': '📁',
            'display_name': 'Other Files',
            'description': 'Unknown or miscellaneous files'
        }
    }
    
    # EXCLUDED MEDIA TYPES (handled by other vaults)
    EXCLUDED_EXTENSIONS = {
        # Images (handled by photo vault)
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif', '.ico', '.svg',
        # Videos (handled by video vault) 
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.3gp', '.m4v', '.mpg', '.mpeg',
        # Audio (handled by audio vault)
        '.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma', '.opus'
    }
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.vault_dir = self.get_vault_directory()
        self.ensure_vault_directory()
        self.processing = False
        
        # Initialize MIME types for better file detection
        mimetypes.init()
    
    def get_vault_directory(self):
        """Get secure directory for document vault - Desktop"""
        if hasattr(self.app, 'secure_storage'):
            return self.app.secure_storage.get_vault_directory('documents')
        
        # Desktop fallback
        return os.path.join(os.getcwd(), 'vault_documents')
    
    def ensure_vault_directory(self):
        """Create vault directory structure"""
        try:
            if not os.path.exists(self.vault_dir):
                os.makedirs(self.vault_dir)
                
            # Create category subdirectories for organization
            for category in self.FILE_CATEGORIES.keys():
                category_dir = os.path.join(self.vault_dir, category)
                if not os.path.exists(category_dir):
                    os.makedirs(category_dir)
                    
        except Exception as e:
            print(f"Error creating vault directory: {e}")
    
    def detect_file_category(self, filename):
        """Detect file category based on extension and MIME type"""
        if not filename:
            return 'other'
        
        # Get file extension
        file_ext = os.path.splitext(filename.lower())[1]
        
        # Check if it's an excluded media type
        if file_ext in self.EXCLUDED_EXTENSIONS:
            return None  # Not supported in document vault
        
        # Find matching category
        for category, config in self.FILE_CATEGORIES.items():
            if category == 'other':  # Skip other category for now
                continue
            if file_ext in config['extensions']:
                return category
        
        # Unknown file type - goes to 'other'
        return 'other'
    
    def is_file_supported(self, filename):
        """Check if file is supported (not a media file)"""
        file_ext = os.path.splitext(filename.lower())[1]
        return file_ext not in self.EXCLUDED_EXTENSIONS
    
    def request_permissions(self):
        """No permissions needed on desktop"""
        pass
    
    def select_documents_from_storage(self, callback):
        """Open file picker to select documents - Desktop only"""
        if self.processing:
            return
            
        self.processing = True
        self.desktop_file_picker(callback)
    
    def desktop_file_picker(self, callback):
        """Desktop file picker - Windows, macOS, Linux"""
        def pick_files():
            try:
                root = tk.Tk()
                root.withdraw()
                
                file_paths = filedialog.askopenfilenames(
                    title="Select Documents",
                    filetypes=[
                        ("Document files", "*.pdf *.doc *.docx *.txt *.rtf"),
                        ("Spreadsheets", "*.xls *.xlsx *.csv"),
                        ("Code files", "*.py *.js *.html *.css *.json"),
                        ("Archives", "*.zip *.rar *.7z"),
                        ("Contact files", "*.vcf *.contact"),
                        ("All files", "*.*")
                    ]
                )
                
                root.destroy()
                Clock.schedule_once(lambda dt: self.handle_selection_async(file_paths, callback), 0)
                
            except Exception as e:
                print(f"Desktop file picker error: {e}")
                self.processing = False
        
        thread = threading.Thread(target=pick_files)
        thread.daemon = True
        thread.start()
    
    def fallback_file_picker(self, callback):
        """Fallback Kivy file picker"""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.popup import Popup
        from kivy.uix.filechooser import FileChooserIconView
        from kivy.metrics import dp
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Use home directory as starting path
        start_path = os.path.expanduser('~')
        
        filechooser = FileChooserIconView(
            path=start_path,
            filters=['*.*'],  # Accept all files
            multiselect=True
        )
        content.add_widget(filechooser)
        
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        
        select_btn = Button(text='Select Files', size_hint_x=0.5)
        cancel_btn = Button(text='Cancel', size_hint_x=0.5)
        
        button_layout.add_widget(select_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title='Select Documents',
            content=content,
            size_hint=(0.9, 0.9),
            auto_dismiss=False
        )
        
        def on_select(instance):
            if filechooser.selection:
                popup.dismiss()
                Clock.schedule_once(lambda dt: self.handle_selection_async(filechooser.selection, callback), 0.1)
            else:
                popup.dismiss()
                self.processing = False
        
        def on_cancel(instance):
            popup.dismiss()
            self.processing = False
        
        select_btn.bind(on_press=on_select)
        cancel_btn.bind(on_press=on_cancel)
        
        popup.open()
    
    def handle_selection_async(self, file_paths, callback):
        """Handle selected files asynchronously"""
        if not file_paths:
            self.processing = False
            return
        
        def process_files():
            try:
                imported_files = []
                skipped_files = []
                
                for file_path in file_paths:
                    try:
                        filename = os.path.basename(file_path)
                        
                        # Check if file is supported (not media)
                        if not self.is_file_supported(filename):
                            skipped_files.append(f"{filename} (media file)")
                            continue
                        
                        # Detect category
                        category = self.detect_file_category(filename)
                        if category is None:
                            skipped_files.append(f"{filename} (not supported)")
                            continue
                        
                        # Generate unique filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        safe_filename = f"vault_{timestamp}_{filename}"
                        
                        # Determine destination based on category
                        destination_dir = os.path.join(self.vault_dir, category)
                        destination = os.path.join(destination_dir, safe_filename)
                        
                        # Copy file to vault
                        shutil.move(file_path, destination)
                        
                        imported_files.append({
                            'path': destination,
                            'original_name': filename,
                            'category': category,
                            'size': os.path.getsize(destination)
                        })
                        
                    except Exception as e:
                        print(f"Error importing file {file_path}: {e}")
                        skipped_files.append(f"{os.path.basename(file_path)} (error)")
                
                # Schedule callback on main thread
                Clock.schedule_once(lambda dt: self.finish_import(imported_files, skipped_files, callback), 0)
                
            except Exception as e:
                print(f"Error processing files: {e}")
                Clock.schedule_once(lambda dt: self.finish_import([], [], callback), 0)
        
        thread = threading.Thread(target=process_files)
        thread.daemon = True
        thread.start()
    
    def finish_import(self, imported_files, skipped_files, callback):
        """Finish import process on main thread"""
        self.processing = False
        callback(imported_files, skipped_files)
    
    def get_vault_documents(self, category_filter=None):
        """Get list of documents in vault, optionally filtered by category"""
        documents = []
        
        try:
            categories_to_check = [category_filter] if category_filter else self.FILE_CATEGORIES.keys()
            
            for category in categories_to_check:
                category_dir = os.path.join(self.vault_dir, category)
                
                if os.path.exists(category_dir):
                    for filename in os.listdir(category_dir):
                        file_path = os.path.join(category_dir, filename)
                        
                        if os.path.isfile(file_path):
                            try:
                                # Extract original filename using regex
                                match = re.match(r'vault_\d{8}_\d{6}_\d+_(.+)', filename)
                                if match:
                                    original_name = match.group(1)
                                else:
                                    original_name = filename
                                
                                # Get file info
                                stat = os.stat(file_path)
                                
                                documents.append({
                                    'path': file_path,
                                    'filename': filename,
                                    'original_name': original_name,
                                    'category': category,
                                    'size': stat.st_size,
                                    'modified': datetime.fromtimestamp(stat.st_mtime),
                                    'category_info': self.FILE_CATEGORIES[category]
                                })
                                
                            except Exception as e:
                                print(f"Error processing file {file_path}: {e}")
            
            # Sort by modification time (newest first)
            documents.sort(key=lambda x: x['modified'], reverse=True)
            return documents
            
        except Exception as e:
            print(f"Error getting vault documents: {e}")
            return []
    
    def delete_document(self, document_path):
        """Move document to recycle bin"""
        try:
            if hasattr(self.app, 'recycle_bin'):
                print(f"Moving document to recycle bin: {document_path}")
                result = self.app.recycle_bin.move_to_recycle(
                    file_path=document_path,
                    original_location=os.path.dirname(document_path),
                    metadata={
                        'vault_type': 'documents',
                        'original_name': os.path.basename(document_path)
                    }
                )
                
                if result['success']:
                    print(f"✅ Document moved to recycle bin successfully")
                    return True
                else:
                    print(f"❌ Failed to move document to recycle bin: {result.get('error', 'Unknown error')}")
                    return False
            else:
                # Fallback to permanent deletion
                print("⚠️ Recycle bin not available, using permanent deletion")
                if os.path.exists(document_path):
                    os.remove(document_path)
                    return True
                return False
                
        except Exception as e:
            print(f"❌ Error moving document to recycle bin: {e}")
            return False
    
    def get_category_stats(self):
        """Get statistics for each file category"""
        stats = {}
        
        for category, config in self.FILE_CATEGORIES.items():
            stats[category] = {
                'count': 0,
                'size_mb': 0,
                'icon': config['icon'],
                'display_name': config['display_name'],
                'description': config['description']
            }
        
        try:
            documents = self.get_vault_documents()
            
            for doc in documents:
                category = doc['category']
                if category in stats:
                    stats[category]['count'] += 1
                    stats[category]['size_mb'] += doc['size'] / (1024 * 1024)
            
            # Round sizes
            for category in stats:
                stats[category]['size_mb'] = round(stats[category]['size_mb'], 1)
            
        except Exception as e:
            print(f"Error calculating category stats: {e}")
        
        return stats
    
    def export_document(self, document_path, user_selected_folder=None):
        """Export document to user-selected location"""
        try:
            if not os.path.exists(document_path):
                return {'success': False, 'error': 'Document not found'}
            
            # Get original filename using regex
            vault_filename = os.path.basename(document_path)
            match = re.match(r'vault_\d{8}_\d{6}_\d+_(.+)', vault_filename)
            if match:
                original_name = match.group(1)
            else:
                original_name = vault_filename
            
            if not user_selected_folder:
                return {'success': False, 'error': 'No export folder selected', 'needs_folder_selection': True}
            
            # Check if selected folder exists and is writable
            if not os.path.exists(user_selected_folder):
                return {'success': False, 'error': 'Selected folder does not exist', 'needs_folder_selection': True}
            
            if not os.access(user_selected_folder, os.W_OK):
                return {'success': False, 'error': 'No write permission for selected folder', 'needs_folder_selection': True}
            
            export_path = os.path.join(user_selected_folder, original_name)
            
            # Handle filename conflicts
            counter = 1
            base_path = export_path
            while os.path.exists(export_path):
                name_part, ext_part = os.path.splitext(base_path)
                export_path = f"{name_part} ({counter}){ext_part}"
                counter += 1
            
            # Copy file
            shutil.copy2(document_path, export_path)
            
            return {
                'success': True,
                'export_path': export_path,
                'original_name': original_name,
                'export_folder': user_selected_folder
            }
            
        except Exception as e:
            print(f"Error exporting document: {e}")
            return {'success': False, 'error': str(e), 'needs_folder_selection': True}
    
    def get_document_preview(self, document_path, max_lines=20):
        """Get preview of document content (text files only)"""
        try:
            # Only preview text-based files
            text_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', 
                             '.xml', '.yaml', '.yml', '.sql', '.log', '.ini', '.cfg', '.conf'}
            
            file_ext = os.path.splitext(document_path.lower())[1]
            
            if file_ext not in text_extensions:
                return {
                    'success': False,
                    'error': 'Preview not available for this file type',
                    'preview_available': False
                }
            
            # Try to read file content
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(document_path, 'r', encoding=encoding) as f:
                        lines = []
                        for i, line in enumerate(f):
                            if i >= max_lines:
                                break
                            lines.append(line.rstrip())
                        
                        content = '\n'.join(lines)
                        file_stats = os.stat(document_path)
                        
                        return {
                            'success': True,
                            'content': content,
                            'preview_available': True,
                            'total_lines': i + 1,
                            'truncated': i >= max_lines,
                            'encoding': encoding,
                            'size': file_stats.st_size
                        }
                        
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail
            return {
                'success': False,
                'error': 'Could not decode file content',
                'preview_available': False
            }
            
        except Exception as e:
            print(f"Error getting document preview: {e}")
            return {
                'success': False,
                'error': str(e),
                'preview_available': False
            }
        
    def select_export_folder(self, callback):
        """Select folder for export - Desktop only"""
        self.desktop_folder_picker(callback)

    def desktop_folder_picker(self, callback):
        """Desktop folder picker"""
        def pick_folder():
            try:
                root = tk.Tk()
                root.withdraw()
                
                folder_path = filedialog.askdirectory(
                    title="Select Export Destination Folder"
                )
                
                root.destroy()
                
                if folder_path:
                    Clock.schedule_once(lambda dt: callback({'success': True, 'folder_path': folder_path}), 0)
                else:
                    Clock.schedule_once(lambda dt: callback({'success': False, 'error': 'No folder selected'}), 0)
                    
            except Exception as e:
                print(f"Desktop folder picker error: {e}")
                Clock.schedule_once(lambda dt: callback({'success': False, 'error': str(e)}), 0)
        
        thread = threading.Thread(target=pick_folder)
        thread.daemon = True
        thread.start()