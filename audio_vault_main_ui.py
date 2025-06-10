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

from audio_vault_dialogs import (
    show_add_audio_dialog,
    show_audio_options,
    show_audio_info_dialog,
    show_detailed_stats_dialog,
    show_no_selection_popup
)

class AudioVaultWidget(BoxLayout):
    
    def __init__(self, audio_vault_core, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.audio_vault = audio_vault_core
        self.selected_audio = None
        self.current_sort = 'added_date'
        
        self.create_header()
        self.create_controls()
        self.create_stats_section()
        self.create_audio_grid()
        self.create_bottom_buttons()
        
        Clock.schedule_once(lambda dt: self.refresh_audio_vault(), 0.1)
    
    def create_header(self):
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=10)
        
        title = Label(
            text='🎵 Audio Files',
            font_size=24,
            size_hint_x=0.6
        )
        header.add_widget(title)
        
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
        controls_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), padding=10, spacing=10)
        
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
        self.stats_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(60), padding=10)
        
        self.stats_label = Label(
            text='Loading audio vault statistics...',
            font_size=14,
            color=(0.7, 0.7, 0.7, 1)
        )
        self.stats_layout.add_widget(self.stats_label)
        
        self.add_widget(self.stats_layout)
    
    def create_audio_grid(self):
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
    
    def handle_add_audio(self, instance):
        show_add_audio_dialog(self.audio_vault, self.refresh_audio_vault)
    
    def handle_show_stats(self, instance):
        show_detailed_stats_dialog(self.audio_vault)
    
    def on_search_text_change(self, instance, text):
        if hasattr(self, '_search_timer'):
            self._search_timer.cancel()
        
        self._search_timer = Clock.schedule_once(lambda dt: self.refresh_audio_grid(), 0.5)
    
    def on_sort_changed(self, spinner, text):
        sort_mapping = {
            'Recent First': 'added_date',
            'Name A-Z': 'filename',
            'Largest First': 'size',
            'Longest First': 'duration'
        }
        
        self.current_sort = sort_mapping.get(text, 'added_date')
        self.refresh_audio_grid()
    
    def refresh_audio_vault(self, instance=None):
        self.update_stats()
        self.refresh_audio_grid()
    
    def update_stats(self):
        try:
            stats = self.audio_vault.get_vault_statistics()
            
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
        try:
            selected_audio_id = self.selected_audio['id'] if self.selected_audio else None
            
            self.audio_grid.clear_widgets()
            
            search_query = self.search_input.text.strip() if self.search_input.text else None
            
            audio_files = self.audio_vault.get_audio_files(
                search_query=search_query,
                sort_by=self.current_sort
            )
            
            if not audio_files:
                empty_widget = self.create_empty_state_widget()
                self.audio_grid.add_widget(empty_widget)
                return
            
            for audio_file in audio_files:
                audio_widget = self.create_audio_widget(audio_file)
                self.audio_grid.add_widget(audio_widget)
                
                if selected_audio_id and audio_file['id'] == selected_audio_id:
                    self.selected_audio = audio_file
                
        except Exception as e:
            print(f"Error refreshing audio grid: {e}")
            error_label = Label(
                text=f"❌ Error loading audio files: {str(e)}",
                size_hint_y=None,
                height=dp(50)
            )
            self.audio_grid.add_widget(error_label)
    
    def create_empty_state_widget(self):
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
        audio_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(100),
            padding=5,
            spacing=10
        )
        
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
        
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.55)
        
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
        
        metadata_row = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        
        metadata_text = ""
        extracted_fields = audio_file.get('metadata', {}).get('extracted_fields', {})
        
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
        
        tech_row = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        
        tech_info = f"⏱️ {audio_file['duration_str']} • 📊 {audio_file['size_mb']:.1f} MB"
        
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
        
        button_layout = BoxLayout(orientation='vertical', size_hint_x=0.3, spacing=3)
        
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
        
        if self.selected_audio and self.selected_audio['id'] == audio_file['id']:
            audio_layout.canvas.before.clear()
            from kivy.graphics import Color, Rectangle
            with audio_layout.canvas.before:
                Color(0.2, 0.6, 0.8, 0.3)
                Rectangle(pos=audio_layout.pos, size=audio_layout.size)
        
        return audio_layout
    
    def select_audio_file(self, audio_file):
        self.selected_audio = audio_file
        print(f"✅ Audio file selected: {audio_file['display_name']}")
        self.refresh_audio_grid()
    
    def play_audio_file(self, audio_file):
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
            
            system = platform.system()
            try:
                if system == "Windows":
                    os.startfile(audio_path)
                elif system == "Darwin":
                    subprocess.run(["open", audio_path])
                else:
                    subprocess.run(["xdg-open", audio_path])
                
                popup = Popup(
                    title='🎵 Opening Audio',
                    content=Label(text=f'Opening in device audio player:\n{audio_file["display_name"]}'),
                    size_hint=(0.7, 0.4),
                    auto_dismiss=True
                )
                popup.open()
                Clock.schedule_once(lambda dt: popup.dismiss(), 2)
                
            except Exception as e:
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
    
    def play_selected_audio(self, instance):
        if not self.selected_audio:
            show_no_selection_popup("play")
            return
        
        self.play_audio_file(self.selected_audio)
    
    def export_selected_audio(self, instance):
        if not self.selected_audio:
            show_no_selection_popup("export")
            return
        
        from audio_vault_dialogs import export_audio_file
        export_audio_file(self.selected_audio, self.audio_vault)
    
    def delete_selected_audio(self, instance):
        if not self.selected_audio:
            show_no_selection_popup("delete")
            return
        
        from audio_vault_dialogs import confirm_delete_audio
        confirm_delete_audio(self.selected_audio, self.audio_vault, self.refresh_audio_vault, self.clear_selection)
    
    def clear_selection(self):
        self.selected_audio = None
    
    def back_to_vault(self, instance):
        print("Going back to main vault screen from audio vault...")
        
        if hasattr(self.audio_vault.app, 'show_vault_main'):
            self.audio_vault.app.show_vault_main()


def integrate_audio_vault(vault_app):
    if hasattr(vault_app, 'audio_vault'):
        print("⚠️ Audio vault already initialized")
        return vault_app.audio_vault
    
    try:
        from audio_vault_core import AudioVaultCore
        vault_app.audio_vault = AudioVaultCore(vault_app)
    except ImportError as e:
        print(f"❌ Error importing AudioVaultCore: {e}")
        return None
    
    def show_audio_vault():
        print("Showing audio vault...")
        vault_app.main_layout.clear_widgets()
        
        audio_vault_widget = AudioVaultWidget(vault_app.audio_vault)
        vault_app.main_layout.add_widget(audio_vault_widget)
        
        vault_app.current_screen = 'audio_vault'
    
    vault_app.show_audio_vault = show_audio_vault
    
    return vault_app.audio_vault