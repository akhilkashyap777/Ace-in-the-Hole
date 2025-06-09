import os
import json
import shutil
import threading
from datetime import datetime
from kivy.clock import Clock

# Try to import Android-specific modules
try:
    from android.storage import app_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False

# Try to import audio metadata libraries
try:
    import mutagen
    from mutagen.id3 import ID3NoHeaderError
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("⚠️ Mutagen not available - audio metadata extraction disabled")

class AudioVaultCore:
    """
    Audio Vault Core - Handles all audio file operations
    Supports any audio format with dynamic metadata extraction
    """
    
    # Common audio extensions - easily extensible
    AUDIO_EXTENSIONS = {
        # Lossy formats
        '.mp3': 'MP3 Audio',
        '.aac': 'AAC Audio', 
        '.m4a': 'M4A Audio',
        '.ogg': 'OGG Audio',
        '.wma': 'WMA Audio',
        '.opus': 'Opus Audio',
        '.3gp': '3GP Audio',
        
        # Lossless formats
        '.flac': 'FLAC Audio',
        '.wav': 'WAV Audio',
        '.aiff': 'AIFF Audio',
        '.ape': 'APE Audio',
        '.alac': 'ALAC Audio',
        
        # Other formats
        '.mid': 'MIDI',
        '.midi': 'MIDI',
        '.ra': 'RealAudio',
        '.au': 'AU Audio',
        '.gsm': 'GSM Audio',
        '.dss': 'DSS Audio',
        '.msv': 'MSV Audio',
        '.dvf': 'DVF Audio',
        '.amr': 'AMR Audio',
        '.awb': 'AWB Audio'
    }
    
    # Popular formats for filtering (if you decide to add filters later)
    POPULAR_FORMATS = ['.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg']
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.vault_dir = self.get_vault_directory()
        self.metadata_file = os.path.join(self.vault_dir, 'audio_metadata.json')
        self.thumbnails_dir = os.path.join(self.vault_dir, 'thumbnails')
        
        self.ensure_directories()
        self.metadata = self.load_metadata()
        
        print("🎵 Audio Vault Core initialized")
        print(f"📁 Vault directory: {self.vault_dir}")
        print(f"🔧 Metadata extraction: {'✅ Available' if MUTAGEN_AVAILABLE else '❌ Disabled'}")
    
    def get_vault_directory(self):
        """Get the audio vault directory"""
        if hasattr(self.app, 'secure_storage'):
            # FIX: Use the correct attribute name - it's 'base_dir' NOT 'base_directory'
            try:
                base_dir = self.app.secure_storage.base_dir  # ✅ CORRECT
                return os.path.join(base_dir, 'vault_audio')
            except Exception as e:
                print(f"⚠️ Error accessing secure storage: {e}")
                # Fall through to fallback
        
        # Fallback for testing/development
        if ANDROID:
            try:
                return os.path.join(app_storage_path(), 'vault_audio')
            except:
                return os.path.join('/sdcard', 'vault_audio')
        else:
            return os.path.join(os.getcwd(), 'vault_audio')
    
    def ensure_directories(self):
        """Create necessary directories"""
        try:
            if not os.path.exists(self.vault_dir):
                os.makedirs(self.vault_dir)
            
            if not os.path.exists(self.thumbnails_dir):
                os.makedirs(self.thumbnails_dir)
                
        except Exception as e:
            print(f"❌ Error creating directories: {e}")
    
    def is_audio_file(self, file_path):
        """Check if file is an audio file"""
        if not os.path.exists(file_path):
            return False
        
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in self.AUDIO_EXTENSIONS
    
    def get_audio_format(self, file_path):
        """Get audio format description"""
        file_ext = os.path.splitext(file_path)[1].lower()
        return self.AUDIO_EXTENSIONS.get(file_ext, 'Unknown Audio')
    
    def extract_audio_metadata(self, file_path):
        """
        Extract metadata from audio file - DYNAMIC approach
        Returns all available metadata without hardcoding specific fields
        """
        metadata = {
            'format': self.get_audio_format(file_path),
            'file_size': 0,
            'duration': None,
            'bitrate': None,
            'sample_rate': None,
            'channels': None,
            'extracted_fields': {}  # Dynamic metadata fields
        }
        
        try:
            # Basic file info
            metadata['file_size'] = os.path.getsize(file_path)
            
            if not MUTAGEN_AVAILABLE:
                return metadata
            
            # Extract audio metadata using mutagen
            audio_file = mutagen.File(file_path)
            
            if audio_file is None:
                return metadata
            
            # Get technical info
            if hasattr(audio_file, 'info'):
                info = audio_file.info
                if hasattr(info, 'length'):
                    metadata['duration'] = info.length
                if hasattr(info, 'bitrate'):
                    metadata['bitrate'] = info.bitrate
                if hasattr(info, 'sample_rate'):
                    metadata['sample_rate'] = info.sample_rate
                if hasattr(info, 'channels'):
                    metadata['channels'] = info.channels
            
            # Extract ALL available tag fields dynamically
            if hasattr(audio_file, 'tags') and audio_file.tags:
                tags = audio_file.tags
                
                # Common tag mappings (but we'll store everything)
                common_mappings = {
                    'TIT2': 'title',           # ID3v2
                    'TPE1': 'artist',          # ID3v2
                    'TALB': 'album',           # ID3v2
                    'TYER': 'year',            # ID3v2
                    'TCON': 'genre',           # ID3v2
                    'TRCK': 'track',           # ID3v2
                    'TPE2': 'album_artist',    # ID3v2
                    'TPOS': 'disc',            # ID3v2
                    'TLEN': 'length',          # ID3v2
                    
                    # Vorbis/FLAC tags
                    'TITLE': 'title',
                    'ARTIST': 'artist', 
                    'ALBUM': 'album',
                    'DATE': 'date',
                    'GENRE': 'genre',
                    'TRACKNUMBER': 'track',
                    'ALBUMARTIST': 'album_artist',
                    'DISCNUMBER': 'disc',
                    
                    # MP4 tags
                    '©nam': 'title',
                    '©ART': 'artist',
                    '©alb': 'album',
                    '©day': 'date',
                    '©gen': 'genre',
                    'trkn': 'track',
                    'aART': 'album_artist',
                    'disk': 'disc',
                }
                
                # Extract all tags dynamically
                for key, value in tags.items():
                    try:
                        # Convert value to string
                        if isinstance(value, list) and len(value) > 0:
                            str_value = str(value[0])
                        else:
                            str_value = str(value)
                        
                        # Use common mapping if available, otherwise use raw key
                        field_name = common_mappings.get(key, key)
                        metadata['extracted_fields'][field_name] = str_value
                        
                        # Also store raw key for completeness
                        if field_name != key:
                            metadata['extracted_fields'][f'raw_{key}'] = str_value
                            
                    except Exception as e:
                        print(f"⚠️ Error processing tag {key}: {e}")
                        continue
            
        except Exception as e:
            print(f"⚠️ Error extracting metadata from {file_path}: {e}")
        
        return metadata
    
    def extract_album_art(self, file_path, audio_id):
        """Extract album art if available"""
        thumbnail_path = None
        
        try:
            if not MUTAGEN_AVAILABLE:
                return None
            
            audio_file = mutagen.File(file_path)
            if audio_file is None or not hasattr(audio_file, 'tags') or not audio_file.tags:
                return None
            
            artwork_data = None
            
            # Different formats store artwork differently
            tags = audio_file.tags
            
            # ID3 tags (MP3)
            if 'APIC:' in tags:
                artwork_data = tags['APIC:'].data
            elif hasattr(tags, 'getall'):
                apic_tags = tags.getall('APIC')
                if apic_tags:
                    artwork_data = apic_tags[0].data
            
            # MP4 tags (M4A, etc.)
            elif 'covr' in tags:
                artwork_data = tags['covr'][0]
            
            # FLAC tags  
            elif hasattr(tags, 'pictures') and tags.pictures:
                artwork_data = tags.pictures[0].data
            
            # Vorbis comment with embedded picture
            elif 'METADATA_BLOCK_PICTURE' in tags:
                import base64
                import struct
                try:
                    pic_data = base64.b64decode(tags['METADATA_BLOCK_PICTURE'][0])
                    # Skip FLAC picture block header (32 bytes)
                    artwork_data = pic_data[32:]
                except:
                    pass
            
            if artwork_data:
                # Save thumbnail
                thumbnail_filename = f"{audio_id}_albumart.jpg"
                thumbnail_path = os.path.join(self.thumbnails_dir, thumbnail_filename)
                
                with open(thumbnail_path, 'wb') as f:
                    f.write(artwork_data)
                
                print(f"🎨 Album art extracted: {thumbnail_filename}")
                
        except Exception as e:
            print(f"⚠️ Could not extract album art: {e}")
        
        return thumbnail_path
    
    def add_audio_file(self, source_path, callback=None):
        """
        Add audio file to vault with progress tracking
        """
        def process_file():
            try:
                if not self.is_audio_file(source_path):
                    result = {'success': False, 'error': 'Not a valid audio file'}
                    if callback:
                        Clock.schedule_once(lambda dt: callback(result), 0)
                    return
                
                # Generate unique ID and filename
                audio_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                original_filename = os.path.basename(source_path)
                file_extension = os.path.splitext(original_filename)[1]
                
                # Create secure filename
                vault_filename = f"audio_{audio_id}{file_extension}"
                vault_path = os.path.join(self.vault_dir, vault_filename)
                
                # Copy file to vault (preserving original)
                shutil.move(source_path, vault_path)
                
                # Extract metadata
                metadata = self.extract_audio_metadata(vault_path)
                
                # Extract album art
                thumbnail_path = self.extract_album_art(vault_path, audio_id)
                
                # Create file record
                file_record = {
                    'id': audio_id,
                    'original_filename': original_filename,
                    'vault_filename': vault_filename,
                    'vault_path': vault_path,
                    'added_date': datetime.now().isoformat(),
                    'metadata': metadata,
                    'thumbnail_path': thumbnail_path,
                    'tags': []  # User can add custom tags later
                }
                
                # Add to metadata
                self.metadata[audio_id] = file_record
                self.save_metadata()
                
                print(f"✅ Audio file added: {original_filename}")
                
                result = {
                    'success': True,
                    'audio_id': audio_id,
                    'file_record': file_record
                }
                
                if callback:
                    Clock.schedule_once(lambda dt: callback(result), 0)
                    
            except Exception as e:
                print(f"❌ Error adding audio file: {e}")
                result = {'success': False, 'error': str(e)}
                if callback:
                    Clock.schedule_once(lambda dt: callback(result), 0)
        
        # Process in background thread
        thread = threading.Thread(target=process_file)
        thread.daemon = True
        thread.start()
    
    def get_audio_files(self, search_query=None, sort_by='added_date'):
        """
        Get list of audio files with optional search and sorting
        """
        try:
            files = []
            
            for audio_id, record in self.metadata.items():
                # Search filter
                if search_query:
                    search_lower = search_query.lower()
                    searchable_text = f"{record['original_filename']} "
                    
                    # Add metadata fields to search
                    if record.get('metadata', {}).get('extracted_fields'):
                        for field, value in record['metadata']['extracted_fields'].items():
                            searchable_text += f"{field} {value} "
                    
                    if search_lower not in searchable_text.lower():
                        continue
                
                # Add display information
                display_record = record.copy()
                display_record['display_name'] = record['original_filename']
                display_record['format_info'] = record['metadata']['format']
                display_record['size_mb'] = record['metadata']['file_size'] / (1024 * 1024)
                
                # Duration formatting
                duration = record['metadata'].get('duration')
                if duration:
                    minutes = int(duration // 60)
                    seconds = int(duration % 60)
                    display_record['duration_str'] = f"{minutes}:{seconds:02d}"
                else:
                    display_record['duration_str'] = "Unknown"
                
                files.append(display_record)
            
            # Sort files
            if sort_by == 'added_date':
                files.sort(key=lambda x: x['added_date'], reverse=True)
            elif sort_by == 'filename':
                files.sort(key=lambda x: x['original_filename'].lower())
            elif sort_by == 'size':
                files.sort(key=lambda x: x['metadata']['file_size'], reverse=True)
            elif sort_by == 'duration':
                files.sort(key=lambda x: x['metadata'].get('duration', 0), reverse=True)
            
            return files
            
        except Exception as e:
            print(f"❌ Error getting audio files: {e}")
            return []
    
    def get_audio_file(self, audio_id):
        """Get specific audio file record"""
        return self.metadata.get(audio_id)
    
    def delete_audio_file(self, audio_id):
        """
        Delete audio file (move to recycle bin)
        """
        try:
            if audio_id not in self.metadata:
                return {'success': False, 'error': 'Audio file not found'}
            
            record = self.metadata[audio_id]
            vault_path = record['vault_path']
            
            if not os.path.exists(vault_path):
                return {'success': False, 'error': 'File not found on disk'}
            
            # Move to recycle bin using the app's recycle bin system
            if hasattr(self.app, 'recycle_bin'):
                recycle_result = self.app.recycle_bin.move_to_recycle(
                    vault_path,
                    original_location=self.vault_dir,
                    metadata={
                        'audio_id': audio_id,
                        'original_filename': record['original_filename'],
                        'audio_metadata': record['metadata']
                    }
                )
                
                if recycle_result['success']:
                    # Remove thumbnail if exists
                    if record.get('thumbnail_path') and os.path.exists(record['thumbnail_path']):
                        try:
                            os.remove(record['thumbnail_path'])
                        except:
                            pass  # Non-critical
                    
                    # Remove from metadata
                    del self.metadata[audio_id]
                    self.save_metadata()
                    
                    print(f"✅ Audio file moved to recycle bin: {record['original_filename']}")
                    return {'success': True, 'recycled': True}
                else:
                    return {'success': False, 'error': recycle_result['error']}
            else:
                # Fallback: direct deletion
                os.remove(vault_path)
                if record.get('thumbnail_path') and os.path.exists(record['thumbnail_path']):
                    os.remove(record['thumbnail_path'])
                
                del self.metadata[audio_id]
                self.save_metadata()
                
                return {'success': True, 'recycled': False}
                
        except Exception as e:
            print(f"❌ Error deleting audio file: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_audio_file(self, audio_id, destination_path):
        """Export audio file to external location"""
        try:
            if audio_id not in self.metadata:
                return {'success': False, 'error': 'Audio file not found'}
            
            record = self.metadata[audio_id]
            vault_path = record['vault_path']
            
            if not os.path.exists(vault_path):
                return {'success': False, 'error': 'File not found on disk'}
            
            # Copy file to destination
            shutil.copy2(vault_path, destination_path)
            
            print(f"✅ Audio file exported: {record['original_filename']} -> {destination_path}")
            return {'success': True, 'exported_path': destination_path}
            
        except Exception as e:
            print(f"❌ Error exporting audio file: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_audio_tags(self, audio_id, custom_tags):
        """Update custom tags for audio file"""
        try:
            if audio_id not in self.metadata:
                return {'success': False, 'error': 'Audio file not found'}
            
            self.metadata[audio_id]['tags'] = custom_tags
            self.save_metadata()
            
            return {'success': True}
            
        except Exception as e:
            print(f"❌ Error updating tags: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_vault_statistics(self):
        """Get audio vault statistics"""
        try:
            stats = {
                'total_files': len(self.metadata),
                'total_size_mb': 0,
                'total_duration_minutes': 0,
                'formats': {},
                'recent_files': 0
            }
            
            recent_threshold = datetime.now().timestamp() - (7 * 24 * 60 * 60)  # 7 days
            
            for record in self.metadata.values():
                # Size
                file_size = record['metadata']['file_size']
                stats['total_size_mb'] += file_size / (1024 * 1024)
                
                # Duration
                duration = record['metadata'].get('duration', 0)
                if duration:
                    stats['total_duration_minutes'] += duration / 60
                
                # Format
                format_name = record['metadata']['format']
                stats['formats'][format_name] = stats['formats'].get(format_name, 0) + 1
                
                # Recent files
                added_date = datetime.fromisoformat(record['added_date'])
                if added_date.timestamp() > recent_threshold:
                    stats['recent_files'] += 1
            
            # Round numbers
            stats['total_size_mb'] = round(stats['total_size_mb'], 1)
            stats['total_duration_minutes'] = round(stats['total_duration_minutes'], 1)
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting vault statistics: {e}")
            return {
                'total_files': 0,
                'total_size_mb': 0,
                'total_duration_minutes': 0,
                'formats': {},
                'recent_files': 0
            }
    
    def load_metadata(self):
        """Load metadata from JSON file"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"❌ Error loading metadata: {e}")
            return {}
    
    def save_metadata(self):
        """Save metadata to JSON file"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving metadata: {e}")

print("✅ Audio Vault Core loaded successfully")
print(f"🎵 Supports {len(AudioVaultCore.AUDIO_EXTENSIONS)} audio formats")
print("🔧 Dynamic metadata extraction with mutagen support")
print("🎨 Album art extraction capability")
print("♻️ Full recycle bin integration")