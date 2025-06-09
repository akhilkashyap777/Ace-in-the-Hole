import os
import threading
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserIconView
from kivy.clock import Clock
from kivy.metrics import dp

# Try to import Android-specific modules
try:
    from android.permissions import request_permissions, Permission
    from plyer import filechooser
    from android.storage import primary_external_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False
    import tkinter as tk
    from tkinter import filedialog

from audio_vault_core import AudioVaultCore

class AudioVaultWidget(BoxLayout):
    """
    Audio Vault UI Widget - Complete audio file management interface with fallback mechanism
    """
    
    def __init__(self, audio_vault_core, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.audio_vault = audio_vault_core
        self.selected_audio = None
        self.current_sort = 'added_date'
        
        # Create UI components
        self.create_header()
        self.create_controls()
        self.create_stats_section()
        self.create_audio_grid()
        self.create_bottom_buttons()
        
        # Load initial data
        Clock.schedule_once(lambda dt: self.refresh_audio_vault(), 0.1)
    
    def create_header(self):
        """Create header with title and quick actions"""
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=10)
        
        title = Label(
            text='🎵 Audio Files',
            font_size=24,
            size_hint_x=0.6
        )
        header.add_widget(title)
        
        # Quick action buttons
        actions_layout = BoxLayout(orientation='horizontal', size_hint_x=0.4, spacing=5)
        
        self.add_btn = Button(
            text='➕ Add Audio',
            font_size=14,
            size_hint_x=0.5,
            background_color=(0.2, 0.7, 0.2, 1)
        )
        self.add_btn.bind(on_press=self.show_add_audio_dialog)
        actions_layout.add_widget(self.add_btn)
        
        self.stats_btn = Button(
            text='📊 Stats',
            font_size=14,
            size_hint_x=0.5
        )
        self.stats_btn.bind(on_press=self.show_detailed_stats)
        actions_layout.add_widget(self.stats_btn)
        
        header.add_widget(actions_layout)
        self.add_widget(header)
    
    def create_controls(self):
        """Create search and sort controls"""
        controls_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), padding=10, spacing=10)
        
        # Search box
        search_layout = BoxLayout(orientation='horizontal', size_hint_x=0.6)
        
        search_label = Label(
            text='🔍',
            size_hint_x=0.1,
            font_size=20
        )
        search_layout.add_widget(search_label)
        
        self.search_input = TextInput(
            hint_text='Search audio files, artists, albums...',
            size_hint_x=0.9,
            multiline=False,
            font_size=16
        )
        self.search_input.bind(text=self.on_search_text_change)
        search_layout.add_widget(self.search_input)
        
        controls_layout.add_widget(search_layout)
        
        # Sort options
        sort_layout = BoxLayout(orientation='horizontal', size_hint_x=0.4)
        
        sort_label = Label(
            text='Sort:',
            size_hint_x=0.3,
            font_size=16
        )
        sort_layout.add_widget(sort_label)
        
        self.sort_spinner = Spinner(
            text='Recent First',
            values=['Recent First', 'Name A-Z', 'Largest First', 'Longest First'],
            size_hint_x=0.7,
            font_size=14
        )
        self.sort_spinner.bind(text=self.on_sort_changed)
        sort_layout.add_widget(self.sort_spinner)
        
        controls_layout.add_widget(sort_layout)
        self.add_widget(controls_layout)
    
    def create_stats_section(self):
        """Create statistics display section"""
        self.stats_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(60), padding=10)
        
        self.stats_label = Label(
            text='Loading audio vault statistics...',
            font_size=14,
            color=(0.7, 0.7, 0.7, 1)
        )
        self.stats_layout.add_widget(self.stats_label)
        
        self.add_widget(self.stats_layout)
    
    def create_audio_grid(self):
        """Create scrollable audio file grid"""
        scroll = ScrollView()
        
        self.audio_grid = GridLayout(
            cols=1,
            spacing=5,
            padding=10,
            size_hint_y=None
        )
        self.audio_grid.bind(minimum_height=self.audio_grid.setter('height'))
        
        scroll.add_widget(self.audio_grid)
        self.add_widget(scroll)
    
    def create_bottom_buttons(self):
        """Create bottom navigation and action buttons"""
        bottom_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=10)
        
        self.refresh_btn = Button(
            text='🔄 Refresh',
            font_size=16,
            size_hint_x=0.2
        )
        self.refresh_btn.bind(on_press=self.refresh_audio_vault)
        bottom_layout.add_widget(self.refresh_btn)
        
        self.play_btn = Button(
            text='▶️ Play',
            font_size=16,
            size_hint_x=0.2,
            background_color=(0.2, 0.6, 0.8, 1)
        )
        self.play_btn.bind(on_press=self.play_selected_audio)
        bottom_layout.add_widget(self.play_btn)
        
        self.export_btn = Button(
            text='📤 Export',
            font_size=16,
            size_hint_x=0.2,
            background_color=(0.6, 0.4, 0.8, 1)
        )
        self.export_btn.bind(on_press=self.export_selected_audio)
        bottom_layout.add_widget(self.export_btn)
        
        self.delete_btn = Button(
            text='🗑️ Delete',
            font_size=16,
            size_hint_x=0.2,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        self.delete_btn.bind(on_press=self.delete_selected_audio)
        bottom_layout.add_widget(self.delete_btn)
        
        self.back_btn = Button(
            text='🔙 Back',
            font_size=16,
            size_hint_x=0.2
        )
        self.back_btn.bind(on_press=self.back_to_vault)
        bottom_layout.add_widget(self.back_btn)
        
        self.add_widget(bottom_layout)
    
    def show_add_audio_dialog(self, instance):
        """Show file picker to add audio files - WITH FALLBACK MECHANISM"""
        if ANDROID:
            try:
                def on_selection(selection):
                    Clock.schedule_once(lambda dt: self.handle_selection_async(selection), 0)
                
                filechooser.open_file(
                    on_selection=on_selection,
                    multiple=True,
                    filters=['*.mp3', '*.wav', '*.flac', '*.aac', '*.m4a', '*.ogg', '*.wma', '*.opus']
                )
            except Exception as e:
                print(f"Error opening Android file chooser: {e}")
                self.fallback_file_picker()
        else:
            self.desktop_file_picker()
    
    def desktop_file_picker(self):
        """Desktop file picker using tkinter"""
        def pick_files():
            try:
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                
                file_paths = filedialog.askopenfilenames(
                    title="Select Audio Files",
                    filetypes=[
                        ("Audio files", "*.mp3 *.wav *.flac *.aac *.m4a *.ogg *.wma *.opus"),
                        ("All files", "*.*")
                    ]
                )
                
                root.destroy()
                
                # Schedule callback on main thread
                Clock.schedule_once(lambda dt: self.handle_selection_async(file_paths), 0)
                
            except Exception as e:
                print(f"Desktop file picker error: {e}")
                Clock.schedule_once(lambda dt: self.fallback_file_picker(), 0)
        
        # Run in separate thread to avoid blocking
        thread = threading.Thread(target=pick_files)
        thread.daemon = True
        thread.start()
    
    def fallback_file_picker(self):
        """Fallback file picker using Kivy's FileChooser"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Instructions
        instruction_label = Label(
            text='📁 Select audio files to add to your vault:\n\nSupported formats: MP3, WAV, FLAC, AAC, M4A, OGG, and many more',
            font_size=16,
            halign='center',
            size_hint_y=None,
            height=dp(80)
        )
        instruction_label.bind(size=instruction_label.setter('text_size'))
        content.add_widget(instruction_label)
        
        # File chooser
        if ANDROID:
            try:
                start_path = primary_external_storage_path()
            except:
                start_path = '/sdcard'
        else:
            start_path = os.path.expanduser('~')
        
        file_chooser = FileChooserIconView(
            path=start_path,
            filters=['*.mp3', '*.wav', '*.flac', '*.aac', '*.m4a', '*.ogg', '*.wma', '*.opus'],
            multiselect=True
        )
        content.add_widget(file_chooser)
        
        # Buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=10)
        
        add_btn = Button(
            text='➕ Add Selected Files',
            background_color=(0.2, 0.7, 0.2, 1),
            font_size=16
        )
        
        cancel_btn = Button(
            text='❌ Cancel',
            background_color=(0.5, 0.5, 0.5, 1),
            font_size=16
        )
        
        button_layout.add_widget(add_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title='➕ Add Audio Files',
            content=content,
            size_hint=(0.95, 0.9),
            auto_dismiss=False
        )
        
        def add_selected_files(instance):
            selected_files = file_chooser.selection
            if selected_files:
                popup.dismiss()
                self.handle_selection_async(selected_files)
            else:
                # Show no selection popup
                no_selection_popup = Popup(
                    title='No Files Selected',
                    content=Label(text='Please select at least one audio file to add.'),
                    size_hint=(0.6, 0.3),
                    auto_dismiss=True
                )
                no_selection_popup.open()
                Clock.schedule_once(lambda dt: no_selection_popup.dismiss(), 2)
        
        add_btn.bind(on_press=add_selected_files)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def handle_selection_async(self, file_paths):
        """Handle selected audio files asynchronously"""
        if not file_paths:
            return
        
        print(f"✅ Selected files: {file_paths}")
        # Handle both single file and multiple files
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        elif isinstance(file_paths, list) and len(file_paths) == 1 and isinstance(file_paths[0], list):
            file_paths = file_paths[0]  # Flatten nested list
        
        # Filter valid audio files
        valid_files = []
        for file_path in file_paths:
            if self.audio_vault.is_audio_file(file_path):
                valid_files.append(file_path)
            else:
                print(f"⚠️ Skipping non-audio file: {file_path}")
        
        if valid_files:
            self.add_audio_files(valid_files)
        else:
            # Show no valid files popup
            no_files_popup = Popup(
                title='❌ No Audio Files',
                content=Label(text='No valid audio files were selected.\n\nPlease select MP3, WAV, FLAC, or other supported audio formats.'),
                size_hint=(0.7, 0.4),
                auto_dismiss=True
            )
            no_files_popup.open()
            Clock.schedule_once(lambda dt: no_files_popup.dismiss(), 4)
    
    # [Continue with remaining methods - let me know if you want me to continue with the rest]
    
    def on_search_text_change(self, instance, text):
        """Handle search text changes with debounce"""
        # Cancel previous search timer
        if hasattr(self, '_search_timer'):
            self._search_timer.cancel()
        
        # Schedule new search after 0.5 seconds
        self._search_timer = Clock.schedule_once(lambda dt: self.refresh_audio_grid(), 0.5)
    
    def on_sort_changed(self, spinner, text):
        """Handle sort option change"""
        sort_mapping = {
            'Recent First': 'added_date',
            'Name A-Z': 'filename',
            'Largest First': 'size',
            'Longest First': 'duration'
        }
        
        self.current_sort = sort_mapping.get(text, 'added_date')
        self.refresh_audio_grid()
    
    def refresh_audio_vault(self, instance=None):
        """Refresh entire audio vault view"""
        self.update_stats()
        self.refresh_audio_grid()
    
    def update_stats(self):
        """Update statistics display"""
        try:
            stats = self.audio_vault.get_vault_statistics()
            
            # Format duration
            hours = int(stats['total_duration_minutes'] // 60)
            minutes = int(stats['total_duration_minutes'] % 60)
            
            if hours > 0:
                duration_str = f"{hours}h {minutes}m"
            else:
                duration_str = f"{minutes}m"
            
            stats_text = f"📊 {stats['total_files']} files • {stats['total_size_mb']} MB • {duration_str} total"
            
            if stats['recent_files'] > 0:
                stats_text += f" • {stats['recent_files']} new this week"
            
            self.stats_label.text = stats_text
            
        except Exception as e:
            print(f"Error updating stats: {e}")
            self.stats_label.text = "❌ Error loading statistics"
    
    def refresh_audio_grid(self):
        """Refresh the audio file grid"""
        try:
            # Clear existing widgets
            self.audio_grid.clear_widgets()
            self.selected_audio = None
            
            # Get search query
            search_query = self.search_input.text.strip() if self.search_input.text else None
            
            # Get audio files
            audio_files = self.audio_vault.get_audio_files(
                search_query=search_query,
                sort_by=self.current_sort
            )
            
            if not audio_files:
                # Show empty state
                empty_widget = self.create_empty_state_widget()
                self.audio_grid.add_widget(empty_widget)
                return
            
            # Create audio file widgets
            for audio_file in audio_files:
                audio_widget = self.create_audio_widget(audio_file)
                self.audio_grid.add_widget(audio_widget)
                
        except Exception as e:
            print(f"Error refreshing audio grid: {e}")
            error_label = Label(
                text=f"❌ Error loading audio files: {str(e)}",
                size_hint_y=None,
                height=dp(50)
            )
            self.audio_grid.add_widget(error_label)
    
    def create_empty_state_widget(self):
        """Create widget for empty audio vault state"""
        empty_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(200),
            spacing=10,
            padding=20
        )
        
        search_text = f"matching '{self.search_input.text}'" if self.search_input.text else ""
        
        empty_label = Label(
            text=f'🎵 No audio files found {search_text}\n\nTap "Add Audio" to import your music,\npodcasts, recordings, and other audio files.',
            font_size=16,
            halign='center',
            color=(0.6, 0.6, 0.6, 1)
        )
        empty_label.bind(size=empty_label.setter('text_size'))
        empty_layout.add_widget(empty_label)
        
        return empty_layout
    
    def add_audio_files(self, file_paths):
        """Add multiple audio files with progress tracking"""
        total_files = len(file_paths)
        completed_files = 0
        failed_files = []
        
        # Create progress popup
        progress_content = BoxLayout(orientation='vertical', spacing=15, padding=15)
        
        self.progress_label = Label(
            text=f'📁 Adding audio files...\n0 of {total_files} completed',
            font_size=16,
            halign='center'
        )
        self.progress_label.bind(size=self.progress_label.setter('text_size'))
        progress_content.add_widget(self.progress_label)
        
        self.current_file_label = Label(
            text='Preparing...',
            font_size=14,
            halign='center',
            color=(0.7, 0.7, 0.7, 1)
        )
        self.current_file_label.bind(size=self.current_file_label.setter('text_size'))
        progress_content.add_widget(self.current_file_label)
        
        progress_popup = Popup(
            title='➕ Adding Audio Files',
            content=progress_content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )
        progress_popup.open()
        
        def process_next_file(file_index=0):
            if file_index >= total_files:
                # All files processed
                progress_popup.dismiss()
                self.refresh_audio_vault()
                self.show_add_results(total_files, len(failed_files), failed_files)
                return
            
            file_path = file_paths[file_index]
            filename = os.path.basename(file_path)
            
            # Update progress
            self.progress_label.text = f'📁 Adding audio files...\n{completed_files} of {total_files} completed'
            self.current_file_label.text = f'Processing: {filename}'
            
            def on_file_added(result):
                nonlocal completed_files
                completed_files += 1
                
                if not result['success']:
                    failed_files.append({'file': filename, 'error': result['error']})
                
                # Process next file
                Clock.schedule_once(lambda dt: process_next_file(file_index + 1), 0.1)
            
            # Add file asynchronously
            self.audio_vault.add_audio_file(file_path, on_file_added)
        
        # Start processing
        Clock.schedule_once(lambda dt: process_next_file(), 0.1)
    
    def show_add_results(self, total, failed_count, failed_files):
        """Show results of adding audio files"""
        success_count = total - failed_count
        
        if failed_count == 0:
            # All successful
            popup = Popup(
                title='✅ Files Added Successfully',
                content=Label(text=f'All {success_count} audio files were added to your vault!'),
                size_hint=(0.7, 0.4),
                auto_dismiss=True
            )
            popup.open()
            Clock.schedule_once(lambda dt: popup.dismiss(), 3)
        else:
            # Some failures - show summary
            content = BoxLayout(orientation='vertical', spacing=10, padding=15)
            
            summary_text = f'📊 Results:\n✅ {success_count} files added successfully\n❌ {failed_count} files failed'
            
            summary_label = Label(
                text=summary_text,
                font_size=16,
                halign='center'
            )
            summary_label.bind(size=summary_label.setter('text_size'))
            content.add_widget(summary_label)
            
            close_btn = Button(
                text='❌ Close',
                size_hint_y=None,
                height=dp(50)
            )
            content.add_widget(close_btn)
            
            popup = Popup(
                title='📊 Add Audio Results',
                content=content,
                size_hint=(0.7, 0.5),
                auto_dismiss=False
            )
            
            close_btn.bind(on_press=popup.dismiss)
            popup.open()
    
    def create_audio_widget(self, audio_file):
        """Create widget for individual audio file"""
        # Main container
        audio_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(100),
            padding=5,
            spacing=10
        )
        
        # Thumbnail/album art section
        thumbnail_layout = BoxLayout(orientation='vertical', size_hint_x=0.15)
        
        if audio_file.get('thumbnail_path') and os.path.exists(audio_file['thumbnail_path']):
            try:
                thumbnail = Image(
                    source=audio_file['thumbnail_path'],
                    size_hint=(1, 1)
                )
            except:
                thumbnail = Label(text='🎵', font_size=32)
        else:
            thumbnail = Label(text='🎵', font_size=32)
        
        thumbnail_layout.add_widget(thumbnail)
        audio_layout.add_widget(thumbnail_layout)
        
        # Info section
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.55)
        
        # Title/filename row
        title_row = BoxLayout(orientation='horizontal', size_hint_y=0.4)
        
        filename = audio_file['display_name']
        if len(filename) > 35:
            filename = filename[:32] + "..."
        
        title_label = Label(
            text=filename,
            font_size=16,
            halign='left',
            color=(1, 1, 1, 1),
            bold=True
        )
        title_label.bind(size=title_label.setter('text_size'))
        title_row.add_widget(title_label)
        
        info_layout.add_widget(title_row)
        
        # Metadata row (artist, album)
        metadata_row = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        
        metadata_text = ""
        extracted_fields = audio_file.get('metadata', {}).get('extracted_fields', {})
        
        # Try to get artist and album from extracted metadata
        artist = extracted_fields.get('artist', extracted_fields.get('ARTIST', ''))
        album = extracted_fields.get('album', extracted_fields.get('ALBUM', ''))
        
        if artist:
            metadata_text += f"👤 {artist}"
        if album:
            if metadata_text:
                metadata_text += f" • 💿 {album}"
            else:
                metadata_text += f"💿 {album}"
        
        if not metadata_text:
            metadata_text = f"📁 {audio_file['format_info']}"
        
        metadata_label = Label(
            text=metadata_text,
            font_size=13,
            halign='left',
            color=(0.8, 0.8, 0.8, 1)
        )
        metadata_label.bind(size=metadata_label.setter('text_size'))
        metadata_row.add_widget(metadata_label)
        
        info_layout.add_widget(metadata_row)
        
        # Technical info row
        tech_row = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        
        tech_info = f"⏱️ {audio_file['duration_str']} • 📊 {audio_file['size_mb']:.1f} MB"
        
        # Add bitrate if available
        bitrate = audio_file.get('metadata', {}).get('bitrate')
        if bitrate:
            tech_info += f" • 🎚️ {bitrate} kbps"
        
        tech_label = Label(
            text=tech_info,
            font_size=11,
            halign='left',
            color=(0.6, 0.6, 0.6, 1)
        )
        tech_label.bind(size=tech_label.setter('text_size'))
        tech_row.add_widget(tech_label)
        
        info_layout.add_widget(tech_row)
        
        audio_layout.add_widget(info_layout)
        
        # Action buttons section
        button_layout = BoxLayout(orientation='vertical', size_hint_x=0.3, spacing=3)
        
        # Top button row
        top_buttons = BoxLayout(orientation='horizontal', size_hint_y=0.5, spacing=3)
        
        select_btn = Button(
            text='📋 Select',
            font_size=12,
            size_hint_x=0.5
        )
        select_btn.bind(on_press=lambda x: self.select_audio_file(audio_file))
        top_buttons.add_widget(select_btn)
        
        info_btn = Button(
            text='ℹ️ Info',
            font_size=12,
            size_hint_x=0.5
        )
        info_btn.bind(on_press=lambda x: self.show_audio_info(audio_file))
        top_buttons.add_widget(info_btn)
        
        button_layout.add_widget(top_buttons)
        
        # Bottom button row
        bottom_buttons = BoxLayout(orientation='horizontal', size_hint_y=0.5, spacing=3)
        
        play_btn = Button(
            text='▶️ Play',
            font_size=12,
            size_hint_x=0.5,
            background_color=(0.2, 0.6, 0.8, 1)
        )
        play_btn.bind(on_press=lambda x: self.play_audio_file(audio_file))
        bottom_buttons.add_widget(play_btn)
        
        options_btn = Button(
            text='⚙️ Menu',
            font_size=12,
            size_hint_x=0.5
        )
        options_btn.bind(on_press=lambda x: self.show_audio_options(audio_file))
        bottom_buttons.add_widget(options_btn)
        
        button_layout.add_widget(bottom_buttons)
        
        audio_layout.add_widget(button_layout)
        
        # Add selection indicator
        if self.selected_audio and self.selected_audio['id'] == audio_file['id']:
            audio_layout.canvas.before.clear()
            from kivy.graphics import Color, Rectangle
            with audio_layout.canvas.before:
                Color(0.2, 0.6, 0.8, 0.3)  # Light blue highlight
                Rectangle(pos=audio_layout.pos, size=audio_layout.size)
        
        return audio_layout
    
    def select_audio_file(self, audio_file):
        """Select an audio file"""
        self.selected_audio = audio_file
        print(f"✅ Audio file selected: {audio_file['display_name']}")
        self.refresh_audio_grid()  # Refresh to show selection highlight
    
    def play_audio_file(self, audio_file):
        """Play audio file using device's native audio player"""
        try:
            import subprocess
            import platform
            
            audio_path = audio_file['vault_path']
            
            if not os.path.exists(audio_path):
                popup = Popup(
                    title='❌ File Not Found',
                    content=Label(text='Audio file not found on disk.'),
                    size_hint=(0.6, 0.3),
                    auto_dismiss=True
                )
                popup.open()
                Clock.schedule_once(lambda dt: popup.dismiss(), 2)
                return
            
            # Use device's native audio player
            system = platform.system()
            try:
                if system == "Windows":
                    os.startfile(audio_path)
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", audio_path])
                else:  # Linux and Android
                    subprocess.run(["xdg-open", audio_path])
                
                # Show confirmation
                popup = Popup(
                    title='🎵 Opening Audio',
                    content=Label(text=f'Opening in device audio player:\n{audio_file["display_name"]}'),
                    size_hint=(0.7, 0.4),
                    auto_dismiss=True
                )
                popup.open()
                Clock.schedule_once(lambda dt: popup.dismiss(), 2)
                
            except Exception as e:
                # Fallback: show file location
                popup = Popup(
                    title='🎵 Audio File',
                    content=Label(text=f'Audio File: {audio_file["display_name"]}\n\nLocation: {audio_path}\n\nPlease open with your preferred audio player.'),
                    size_hint=(0.8, 0.5),
                    auto_dismiss=True
                )
                popup.open()
                Clock.schedule_once(lambda dt: popup.dismiss(), 4)
                
        except Exception as e:
            print(f"Error opening audio file: {e}")
            popup = Popup(
                title='❌ Error',
                content=Label(text=f'Could not open audio file:\n{str(e)}'),
                size_hint=(0.7, 0.4),
                auto_dismiss=True
            )
            popup.open()
            Clock.schedule_once(lambda dt: popup.dismiss(), 3)
    
    def show_audio_info(self, audio_file):
        """Show detailed audio file information"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        
        # Basic info
        basic_info = f"""📁 {audio_file['display_name']}
📊 {audio_file['format_info']} • {audio_file['size_mb']:.1f} MB
⏱️ Duration: {audio_file['duration_str']}
📅 Added: {datetime.fromisoformat(audio_file['added_date']).strftime("%Y-%m-%d %H:%M")}"""
        
        basic_label = Label(
            text=basic_info,
            font_size=14,
            halign='left'
        )
        basic_label.bind(size=basic_label.setter('text_size'))
        content.add_widget(basic_label)
        
        # Close button
        close_btn = Button(
            text='❌ Close',
            size_hint_y=None,
            height=dp(50)
        )
        content.add_widget(close_btn)
        
        popup = Popup(
            title=f'ℹ️ Audio Information',
            content=content,
            size_hint=(0.8, 0.6),
            auto_dismiss=False
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def show_audio_options(self, audio_file):
        """Show audio file options menu"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        
        # File info
        info_text = f"🎵 {audio_file['display_name']}\n📊 {audio_file['format_info']} • {audio_file['size_mb']:.1f} MB"
        
        info_label = Label(
            text=info_text,
            font_size=14,
            halign='center'
        )
        info_label.bind(size=info_label.setter('text_size'))
        content.add_widget(info_label)
        
        # Action buttons
        button_layout = BoxLayout(orientation='vertical', spacing=8)
        
        play_btn = Button(
            text='▶️ Play Audio',
            background_color=(0.2, 0.6, 0.8, 1),
            size_hint_y=None,
            height=dp(50)
        )
        
        export_btn = Button(
            text='📤 Export File',
            background_color=(0.6, 0.4, 0.8, 1),
            size_hint_y=None,
            height=dp(50)
        )
        
        delete_btn = Button(
            text='🗑️ Delete',
            background_color=(0.8, 0.2, 0.2, 1),
            size_hint_y=None,
            height=dp(50)
        )
        
        cancel_btn = Button(
            text='❌ Cancel',
            background_color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=dp(50)
        )
        
        button_layout.add_widget(play_btn)
        button_layout.add_widget(export_btn)
        button_layout.add_widget(delete_btn)
        button_layout.add_widget(cancel_btn)
        
        content.add_widget(button_layout)
        
        popup = Popup(
            title='🎵 Audio Options',
            content=content,
            size_hint=(0.7, 0.7),
            auto_dismiss=False
        )
        
        def handle_play(instance):
            popup.dismiss()
            self.play_audio_file(audio_file)
        
        def handle_export(instance):
            popup.dismiss()
            self.export_audio_file(audio_file)
        
        def handle_delete(instance):
            popup.dismiss()
            self.confirm_delete_audio(audio_file)
        
        play_btn.bind(on_press=handle_play)
        export_btn.bind(on_press=handle_export)
        delete_btn.bind(on_press=handle_delete)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def export_audio_file(self, audio_file):
        """Export audio file using fallback mechanism"""
        if ANDROID:
            try:
                def folder_selected(folder_path):
                    """Callback when folder is selected"""
                    if folder_path:
                        if isinstance(folder_path, list):
                            folder_path = folder_path[0]
                        
                        destination_path = os.path.join(folder_path, audio_file['original_filename'])
                        self.export_audio_file_with_progress(audio_file, destination_path)
                    else:
                        print("ℹ️ No folder selected for export")
                
                # Open native folder picker
                filechooser.choose_dir(
                    title="Select Export Destination",
                    on_selection=folder_selected
                )
            except Exception as e:
                print(f"Error opening folder picker: {e}")
                self.export_with_fallback_picker(audio_file)
        else:
            self.export_with_desktop_picker(audio_file)
    
    def export_with_desktop_picker(self, audio_file):
        """Export using desktop folder picker"""
        def pick_folder():
            try:
                root = tk.Tk()
                root.withdraw()
                
                folder_path = filedialog.askdirectory(title="Select Export Destination")
                root.destroy()
                
                if folder_path:
                    destination_path = os.path.join(folder_path, audio_file['original_filename'])
                    Clock.schedule_once(lambda dt: self.export_audio_file_with_progress(audio_file, destination_path), 0)
                
            except Exception as e:
                print(f"Desktop export picker error: {e}")
                Clock.schedule_once(lambda dt: self.export_with_fallback_picker(audio_file), 0)
        
        thread = threading.Thread(target=pick_folder)
        thread.daemon = True
        thread.start()
    
    def export_with_fallback_picker(self, audio_file):
        """Fallback export dialog using Kivy file chooser"""
        content = BoxLayout(orientation='vertical', spacing=15, padding=15)
        
        info_text = f'📤 Export Audio File:\n{audio_file["display_name"]}\n{audio_file["format_info"]} • {audio_file["size_mb"]:.1f} MB'
        
        info_label = Label(
            text=info_text,
            font_size=16,
            halign='center',
            size_hint_y=None,
            height=dp(100)
        )
        info_label.bind(size=info_label.setter('text_size'))
        content.add_widget(info_label)
        
        # File chooser for destination
        file_chooser = FileChooserIconView(
            dirselect=True,
            size_hint_y=0.6
        )
        content.add_widget(file_chooser)
        
        # Filename input
        filename_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        
        filename_label = Label(
            text='Filename:',
            size_hint_x=0.3,
            font_size=14
        )
        filename_layout.add_widget(filename_label)
        
        filename_input = TextInput(
            text=audio_file['original_filename'],
            size_hint_x=0.7,
            multiline=False,
            font_size=14
        )
        filename_layout.add_widget(filename_input)
        
        content.add_widget(filename_layout)
        
        # Buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=10)
        
        export_btn = Button(
            text='📤 Export Here',
            background_color=(0.6, 0.4, 0.8, 1),
            font_size=16
        )
        
        cancel_btn = Button(
            text='❌ Cancel',
            background_color=(0.5, 0.5, 0.5, 1),
            font_size=16
        )
        
        button_layout.add_widget(export_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title='📤 Export Audio File',
            content=content,
            size_hint=(0.9, 0.9),
            auto_dismiss=False
        )
        
        def do_export(instance):
            destination_dir = file_chooser.path
            filename = filename_input.text.strip()
            
            if not filename:
                filename = audio_file['original_filename']
            
            destination_path = os.path.join(destination_dir, filename)
            
            popup.dismiss()
            self.export_audio_file_with_progress(audio_file, destination_path)
        
        export_btn.bind(on_press=do_export)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def export_audio_file_with_progress(self, audio_file, destination_path):
        """Export audio file with progress indication"""
        # Show progress popup
        progress_content = Label(
            text=f'📤 Exporting audio file...\n{audio_file["display_name"]}\n\nPlease wait...',
            halign='center',
            font_size=16
        )
        
        progress_popup = Popup(
            title='Exporting Audio',
            content=progress_content,
            size_hint=(0.7, 0.4),
            auto_dismiss=False
        )
        progress_popup.open()
        
        def do_export():
            result = self.audio_vault.export_audio_file(audio_file['id'], destination_path)
            Clock.schedule_once(lambda dt: finish_export(result), 0)
        
        def finish_export(result):
            progress_popup.dismiss()
            
            if result['success']:
                success_popup = Popup(
                    title='✅ Export Successful',
                    content=Label(text=f'Audio file exported to:\n{result["exported_path"]}'),
                    size_hint=(0.8, 0.4),
                    auto_dismiss=True
                )
                success_popup.open()
                Clock.schedule_once(lambda dt: success_popup.dismiss(), 4)
            else:
                error_popup = Popup(
                    title='❌ Export Failed',
                    content=Label(text=f'Could not export audio file:\n{result["error"]}'),
                    size_hint=(0.8, 0.4),
                    auto_dismiss=True
                )
                error_popup.open()
                Clock.schedule_once(lambda dt: error_popup.dismiss(), 4)
        
        # Start export in background
        thread = threading.Thread(target=do_export)
        thread.daemon = True
        thread.start()
    
    def confirm_delete_audio(self, audio_file):
        """Confirm deletion of audio file"""
        content = BoxLayout(orientation='vertical', spacing=15, padding=15)
        
        warning_text = f"""⚠️ DELETE AUDIO FILE ⚠️

File: {audio_file['display_name']}
Format: {audio_file['format_info']}
Size: {audio_file['size_mb']:.1f} MB

This will move the file to the recycle bin.
You can restore it later if needed.

Are you sure you want to delete this audio file?"""
        
        warning_label = Label(
            text=warning_text,
            halign='center',
            font_size=14,
            color=(1, 0.8, 0, 1)
        )
        warning_label.bind(size=warning_label.setter('text_size'))
        content.add_widget(warning_label)
        
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=10)
        
        delete_btn = Button(
            text='🗑️ DELETE',
            background_color=(0.8, 0.2, 0.2, 1),
            font_size=16
        )
        
        cancel_btn = Button(
            text='❌ CANCEL',
            background_color=(0.5, 0.5, 0.5, 1),
            font_size=16
        )
        
        button_layout.add_widget(delete_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title='🗑️ Confirm Delete',
            content=content,
            size_hint=(0.8, 0.6),
            auto_dismiss=False
        )
        
        def delete_confirmed(instance):
            popup.dismiss()
            self.delete_audio_file_with_progress(audio_file)
        
        delete_btn.bind(on_press=delete_confirmed)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def delete_audio_file_with_progress(self, audio_file):
        """Delete audio file with progress indication"""
        # Show progress popup
        progress_content = Label(
            text=f'🗑️ Deleting audio file...\n{audio_file["display_name"]}\n\nPlease wait...',
            halign='center',
            font_size=16
        )
        
        progress_popup = Popup(
            title='Deleting Audio',
            content=progress_content,
            size_hint=(0.7, 0.4),
            auto_dismiss=False
        )
        progress_popup.open()
        
        def do_delete():
            result = self.audio_vault.delete_audio_file(audio_file['id'])
            Clock.schedule_once(lambda dt: finish_delete(result), 0)
        
        def finish_delete(result):
            progress_popup.dismiss()
            
            if result['success']:
                self.selected_audio = None
                self.refresh_audio_vault()
                
                message = 'Audio file moved to recycle bin successfully!\nYou can restore it later if needed.' if result.get('recycled') else 'Audio file deleted successfully!'
                
                success_popup = Popup(
                    title='✅ File Deleted',
                    content=Label(text=message),
                    size_hint=(0.7, 0.4),
                    auto_dismiss=True
                )
                success_popup.open()
                Clock.schedule_once(lambda dt: success_popup.dismiss(), 3)
            else:
                error_popup = Popup(
                    title='❌ Delete Failed',
                    content=Label(text=f'Could not delete audio file:\n{result["error"]}'),
                    size_hint=(0.8, 0.4),
                    auto_dismiss=True
                )
                error_popup.open()
                Clock.schedule_once(lambda dt: error_popup.dismiss(), 4)
        
        # Start deletion in background
        thread = threading.Thread(target=do_delete)
        thread.daemon = True
        thread.start()
    
    def play_selected_audio(self, instance):
        """Play the selected audio file"""
        if not self.selected_audio:
            self.show_no_selection_popup("play")
            return
        
        self.play_audio_file(self.selected_audio)
    
    def export_selected_audio(self, instance):
        """Export the selected audio file"""
        if not self.selected_audio:
            self.show_no_selection_popup("export")
            return
        
        self.export_audio_file(self.selected_audio)
    
    def delete_selected_audio(self, instance):
        """Delete the selected audio file"""
        if not self.selected_audio:
            self.show_no_selection_popup("delete")
            return
        
        self.confirm_delete_audio(self.selected_audio)
    
    def show_detailed_stats(self, instance):
        """Show detailed audio vault statistics"""
        from audio_vault_stats import AudioVaultStatsWidget
        
        stats_widget = AudioVaultStatsWidget(self.audio_vault)
        
        popup = Popup(
            title='📊 Audio Vault Statistics',
            content=stats_widget,
            size_hint=(0.9, 0.9),
            auto_dismiss=True
        )
        popup.open()
    
    def show_no_selection_popup(self, action):
        """Show popup when no audio file is selected"""
        popup = Popup(
            title='No Audio Selected',
            content=Label(text=f'Please select an audio file first to {action} it.'),
            size_hint=(0.7, 0.3),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def back_to_vault(self, instance):
        """Go back to main vault screen"""
        print("Going back to main vault screen from audio vault...")
        
        # Navigate back to main vault
        if hasattr(self.audio_vault.app, 'show_vault_main'):
            self.audio_vault.app.show_vault_main()


# Integration helper function
def integrate_audio_vault(vault_app):
    """Helper function to integrate audio vault into the main app"""
    # Check if already initialized to prevent circular reference
    if hasattr(vault_app, 'audio_vault'):
        print("⚠️ Audio vault already initialized")
        return vault_app.audio_vault
    
    # Initialize audio vault core
    vault_app.audio_vault = AudioVaultCore(vault_app)
    
    def show_audio_vault():
        """Show the audio vault interface"""
        print("Showing audio vault...")
        vault_app.main_layout.clear_widgets()
        
        # Create audio vault widget
        audio_vault_widget = AudioVaultWidget(vault_app.audio_vault)
        vault_app.main_layout.add_widget(audio_vault_widget)
        
        # Store reference for navigation
        vault_app.current_screen = 'audio_vault'
    
    # Add method to vault app
    vault_app.show_audio_vault = show_audio_vault
    
    return vault_app.audio_vault

print("✅ Audio Vault UI module loaded successfully (WITH FALLBACK)")
print("🎵 Complete audio file management interface")
print("🔧 Multi-platform file picker support:")
print("   📱 Android: Plyer native picker")
print("   🖥️ Desktop: Tkinter file dialog")  
print("   🔄 Fallback: Kivy FileChooser")
print("♻️ Full integration with secure storage and recycle bin")