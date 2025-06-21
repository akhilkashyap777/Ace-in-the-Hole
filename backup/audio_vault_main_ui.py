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
from kivy.clock import Clock
from kivy.metrics import dp

# Import dialog functions
from audio_vault_dialogs import (
    show_add_audio_dialog,
    show_audio_options,
    show_audio_info_dialog,
    show_detailed_stats_dialog,
    show_no_selection_popup
)

class AudioVaultWidget(BoxLayout):
    """
    Audio Vault Main UI Widget - Core interface and audio file display
    Focused on layout, navigation, and basic interactions
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
        self.add_btn.bind(on_press=self.handle_add_audio)
        actions_layout.add_widget(self.add_btn)
        
        self.stats_btn = Button(
            text='📊 Stats',
            font_size=14,
            size_hint_x=0.5
        )
        self.stats_btn.bind(on_press=self.handle_show_stats)
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
    
    # Event Handlers
    def handle_add_audio(self, instance):
        """Handle add audio button press - delegates to dialog"""
        show_add_audio_dialog(self.audio_vault, self.refresh_audio_vault)
    
    def handle_show_stats(self, instance):
        """Handle show stats button press - delegates to dialog"""
        show_detailed_stats_dialog(self.audio_vault)
    
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
    
    # Core UI Functions
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
        info_btn.bind(on_press=lambda x: show_audio_info_dialog(audio_file))
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
        options_btn.bind(on_press=lambda x: show_audio_options(audio_file, self.audio_vault, self.refresh_audio_vault))
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
    
    # Bottom Button Handlers
    def play_selected_audio(self, instance):
        """Play the selected audio file"""
        if not self.selected_audio:
            show_no_selection_popup("play")
            return
        
        self.play_audio_file(self.selected_audio)
    
    def export_selected_audio(self, instance):
        """Export the selected audio file"""
        if not self.selected_audio:
            show_no_selection_popup("export")
            return
        
        # Import here to avoid circular imports
        from audio_vault_dialogs import export_audio_file
        export_audio_file(self.selected_audio, self.audio_vault)
    
    def delete_selected_audio(self, instance):
        """Delete the selected audio file"""
        if not self.selected_audio:
            show_no_selection_popup("delete")
            return
        
        # Import here to avoid circular imports
        from audio_vault_dialogs import confirm_delete_audio
        confirm_delete_audio(self.selected_audio, self.audio_vault, self.refresh_audio_vault, self.clear_selection)
    
    def clear_selection(self):
        """Clear the current audio selection"""
        self.selected_audio = None
    
    def back_to_vault(self, instance):
        """Go back to main vault screen"""
        print("Going back to main vault screen from audio vault...")
        
        # Navigate back to main vault
        if hasattr(self.audio_vault.app, 'show_vault_main'):
            self.audio_vault.app.show_vault_main()


# Integration helper function - OUTSIDE THE CLASS
def integrate_audio_vault(vault_app):
    """Helper function to integrate audio vault into the main app"""
    # Check if already initialized to prevent circular reference
    if hasattr(vault_app, 'audio_vault'):
        print("⚠️ Audio vault already initialized")
        return vault_app.audio_vault
    
    # Import here to avoid circular imports
    try:
        from audio_vault_core import AudioVaultCore
        # Initialize audio vault core
        vault_app.audio_vault = AudioVaultCore(vault_app)
    except ImportError as e:
        print(f"❌ Error importing AudioVaultCore: {e}")
        return None
    
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


print("✅ Audio Vault Main UI loaded successfully")
print("🎵 Focused main interface with clean separation of concerns")
print("🔧 Delegates complex dialogs to separate module")