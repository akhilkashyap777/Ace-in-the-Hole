import os
import threading
from datetime import datetime
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle

from audio_vault_dialogs import (
    show_add_audio_dialog,
    show_audio_options,
    show_audio_info_dialog,
    show_detailed_stats_dialog,
    show_no_selection_popup
)

class AudioVaultWidget(MDBoxLayout):
    
    def __init__(self, audio_vault_core, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.audio_vault = audio_vault_core
        self.selected_audio = None
        self.current_sort = 'added_date'
        
        # Set dark gradient background
        self.md_bg_color = [0.37, 0.49, 0.55, 1]
        
        self.create_header()
        self.create_search_section()
        self.create_stats_section()
        self.create_audio_grid()
        self.create_bottom_bar()
        
        Clock.schedule_once(lambda dt: self.refresh_audio_vault(), 0.1)
    
    def create_header(self):
        """Create large title header"""
        header = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(120),
            padding=[20, 20, 20, 10],
            spacing=10
        )
        
        # Large title
        title = MDLabel(
            text='AUDIO FILES',
            font_style="H3",
            text_color="white",
            halign="center",
            bold=True
        )
        header.add_widget(title)
        
        # Action buttons row
        actions_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=15
        )
        
        self.add_btn = MDRaisedButton(
            text='➕ Add Audio',
            md_bg_color=[0.2, 0.7, 0.3, 1],
            text_color="white",
            size_hint_x=0.5,
            elevation=3
        )
        self.add_btn.bind(on_press=self.handle_add_audio)
        actions_row.add_widget(self.add_btn)
        
        self.stats_btn = MDRaisedButton(
            text='📊 Stats',
            md_bg_color=[0.38, 0.49, 0.55, 1],
            text_color="white", 
            size_hint_x=0.5,
            elevation=3
        )
        self.stats_btn.bind(on_press=self.handle_show_stats)
        actions_row.add_widget(self.stats_btn)
        
        header.add_widget(actions_row)
        self.add_widget(header)
    
    def create_search_section(self):
        """Create search bar and sort controls"""
        search_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(100),
            padding=[20, 10, 20, 10],
            spacing=15
        )
        
        # Search bar
        search_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=15
        )
        
        # Search input with rounded style
        self.search_input = MDTextField(
            hint_text='Search audio files...',
            size_hint_x=0.75,
            mode="round",
            fill_color_normal=[0.26, 0.32, 0.36, 0.8],
            text_color_normal="white",
            hint_text_color_normal=[0.7, 0.7, 0.7, 1],
            line_color_normal=[0.4, 0.6, 0.8, 0],
            line_color_focus=[0.4, 0.6, 0.8, 0]
        )
        self.search_input.bind(text=self.on_search_text_change)
        search_row.add_widget(self.search_input)
        
        # Sort button
        self.sort_btn = MDRaisedButton(
            text='Sort',
            size_hint_x=0.25,
            md_bg_color=[0.46, 0.53, 0.6, 1],
            text_color="white",
            elevation=2
        )
        self.sort_btn.bind(on_press=self.show_sort_menu)
        search_row.add_widget(self.sort_btn)
        
        # Create sort menu
        if not hasattr(self, 'sort_menu'):
            sort_menu_items = [
                {
                    "text": "Recent First",
                    "viewclass": "OneLineListItem",
                    "on_release": lambda x="Recent First": self.set_sort_option(x),
                },
                {
                    "text": "Name A-Z", 
                    "viewclass": "OneLineListItem",
                    "on_release": lambda x="Name A-Z": self.set_sort_option(x),
                },
                {
                    "text": "Largest First",
                    "viewclass": "OneLineListItem",
                    "on_release": lambda x="Largest First": self.set_sort_option(x),
                },
                {
                    "text": "Longest First",
                    "viewclass": "OneLineListItem", 
                    "on_release": lambda x="Longest First": self.set_sort_option(x),
                },
            ]
            
            self.sort_menu = MDDropdownMenu(
                caller=self.sort_btn,
                items=sort_menu_items,
                width_mult=3,
            )
        
        search_container.add_widget(search_row)
        self.add_widget(search_container)
    
    def show_sort_menu(self, instance):
        self.sort_menu.open()
    
    def set_sort_option(self, sort_text):
        self.sort_btn.text = sort_text
        self.sort_menu.dismiss()
        
        sort_mapping = {
            'Recent First': 'added_date',
            'Name A-Z': 'filename',
            'Largest First': 'size', 
            'Longest First': 'duration'
        }
        
        self.current_sort = sort_mapping.get(sort_text, 'added_date')
        self.refresh_audio_grid()
    
    def create_stats_section(self):
        """Create stats display"""
        self.stats_label = MDLabel(
            text='Loading audio vault statistics...',
            font_style="Body2",
            text_color=[0.8, 0.8, 0.8, 1],
            halign="center",
            size_hint_y=None,
            height=dp(30)
        )
        self.add_widget(self.stats_label)
    
    def create_audio_grid(self):
        """Create scrollable audio files grid"""
        scroll = MDScrollView(
            bar_width=dp(4),
            bar_color=[0.4, 0.6, 0.8, 0.7],
            bar_inactive_color=[0.7, 0.7, 0.7, 0.3],
            effect_cls="ScrollEffect"
        )
        
        self.audio_grid = MDGridLayout(
            cols=1,
            spacing=15,
            padding=[20, 10, 20, 10],
            size_hint_y=None,
            adaptive_height=True
        )
        
        scroll.add_widget(self.audio_grid)
        self.add_widget(scroll)
    
    def create_bottom_bar(self):
        """Create bottom action bar"""
        bottom_bar = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(70),
            padding=15,
            spacing=20,
            elevation=8,
            md_bg_color=[0.26, 0.32, 0.36, 1]
        )
        
        # Refresh
        refresh_btn = MDFlatButton(
            text='🔄 Refresh',
            text_color="white",
            size_hint_x=0.2
        )
        refresh_btn.bind(on_press=self.refresh_audio_vault)
        bottom_bar.add_widget(refresh_btn)
        
        # Play
        self.play_btn = MDFlatButton(
            text='▶️ Play',
            text_color=[0.4, 0.8, 0.4, 1],
            size_hint_x=0.2
        )
        self.play_btn.bind(on_press=self.play_selected_audio)
        bottom_bar.add_widget(self.play_btn)
        
        # Export
        self.export_btn = MDFlatButton(
            text='⬇ Export',
            text_color=[0.6, 0.6, 0.9, 1],
            size_hint_x=0.2
        )
        self.export_btn.bind(on_press=self.export_selected_audio)
        bottom_bar.add_widget(self.export_btn)
        
        # Delete
        self.delete_btn = MDFlatButton(
            text='🗑 Delete',
            text_color=[0.9, 0.4, 0.4, 1],
            size_hint_x=0.2
        )
        self.delete_btn.bind(on_press=self.delete_selected_audio)
        bottom_bar.add_widget(self.delete_btn)
        
        # Back
        self.back_btn = MDFlatButton(
            text='← Back',
            text_color=[0.7, 0.7, 0.7, 1],
            size_hint_x=0.2
        )
        self.back_btn.bind(on_press=self.back_to_vault)
        bottom_bar.add_widget(self.back_btn)
        
        self.add_widget(bottom_bar)
    
    def handle_add_audio(self, instance):
        show_add_audio_dialog(self.audio_vault, self.refresh_audio_vault)
    
    def handle_show_stats(self, instance):
        show_detailed_stats_dialog(self.audio_vault)
    
    def on_search_text_change(self, instance, text):
        if hasattr(self, '_search_timer'):
            self._search_timer.cancel()
        
        self._search_timer = Clock.schedule_once(lambda dt: self.refresh_audio_grid(), 0.5)
    
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
            
            stats_text = f"{stats['total_files']} files - {stats['total_size_mb']} MB - {duration_str} total"
            
            if stats['recent_files'] > 0:
                stats_text += f" - {stats['recent_files']} new this week"
            
            self.stats_label.text = stats_text
            
        except Exception as e:
            print(f"Error updating stats: {e}")
            self.stats_label.text = "Error loading statistics"
    
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
            error_card = MDCard(
                size_hint_y=None,
                height=dp(60),
                padding=15,
                md_bg_color=[0.8, 0.2, 0.2, 0.3]
            )
            error_label = MDLabel(
                text=f"❌ Error loading audio files: {str(e)}",
                text_color=[1, 0.4, 0.4, 1],
                halign="center"
            )
            error_card.add_widget(error_label)
            self.audio_grid.add_widget(error_card)
    
    def create_empty_state_widget(self):
        """Create empty state with modern styling"""
        empty_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height=dp(200),
            padding=30,
            spacing=20,
            md_bg_color=[0.37, 0.49, 0.55, 0.8],
            elevation=2
        )
        
        search_text = f"matching '{self.search_input.text}'" if self.search_input.text else ""
        
        empty_label = MDLabel(
            text=f'🎵 No audio files found {search_text}\n\nTap "Add Audio" to import your music,\npodcasts, recordings, and other audio files.',
            font_style="Body1",
            halign="center",
            text_color=[0.7, 0.7, 0.7, 1]
        )
        empty_card.add_widget(empty_label)
        
        return empty_card
    
    def create_audio_widget(self, audio_file):
        """Create modern audio file card"""
        is_selected = self.selected_audio and self.selected_audio['id'] == audio_file['id']
        
        # Main card with modern styling
        audio_card = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(90),
            padding=15,
            spacing=15,
            elevation=4 if is_selected else 2,
            md_bg_color=[0.46, 0.53, 0.6, 1] if is_selected else [0.37, 0.49, 0.55, 0.9],
            ripple_behavior=True
        )
        
        # Music note icon
        icon_container = MDBoxLayout(
            orientation='vertical',
            size_hint_x=None,
            width=dp(60),
            padding=[5, 5]
        )
        
        if audio_file.get('thumbnail_path') and os.path.exists(audio_file['thumbnail_path']):
            try:
                thumbnail = Image(
                    source=audio_file['thumbnail_path'],
                    size_hint=(1, 1)
                )
            except:
                thumbnail = MDLabel(
                    text='🎵',
                    font_style="H4",
                    halign="center",
                    text_color="white"
                )
        else:
            thumbnail = MDLabel(
                text='🎵',
                font_style="H4", 
                halign="center",
                text_color="white"
            )
        
        icon_container.add_widget(thumbnail)
        audio_card.add_widget(icon_container)
        
        # File info section
        info_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_x=0.6,
            spacing=5
        )
        
        # Filename
        filename = audio_file['display_name']
        if len(filename) > 40:
            filename = filename[:37] + "..."
        
        title_label = MDLabel(
            text=filename,
            font_style="Subtitle1",
            text_color="white",
            bold=True,
            size_hint_y=0.5
        )
        info_layout.add_widget(title_label)
        
        # File details
        size_mb = audio_file['size_mb']
        duration_str = audio_file.get('duration_str', 'Unknown')
        format_info = audio_file.get('format_info', 'Unknown')
        
        details_text = f"Size: {size_mb:.1f} MB - Duration: {duration_str}"
        
        details_label = MDLabel(
            text=details_text,
            font_style="Caption",
            text_color=[0.8, 0.8, 0.8, 1],
            size_hint_y=0.25
        )
        info_layout.add_widget(details_label)
        
        # Format
        format_label = MDLabel(
            text=format_info,
            font_style="Caption", 
            text_color=[0.7, 0.7, 0.7, 1],
            size_hint_y=0.25
        )
        info_layout.add_widget(format_label)
        
        audio_card.add_widget(info_layout)
        
        # Action buttons
        button_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            width=dp(160),
            spacing=10
        )
        
        # Play button
        play_btn = MDRaisedButton(
            text='▶️ Play',
            md_bg_color=[0.2, 0.6, 0.8, 1],
            text_color="white",
            size_hint_x=0.5,
            elevation=2
        )
        play_btn.bind(on_press=lambda x: self.play_audio_file(audio_file))
        button_layout.add_widget(play_btn)
        
        # Info button  
        info_btn = MDRaisedButton(
            text='ℹ️ Info',
            md_bg_color=[0.5, 0.5, 0.5, 1],
            text_color="white",
            size_hint_x=0.5,
            elevation=2
        )
        info_btn.bind(on_press=lambda x: show_audio_info_dialog(audio_file))
        button_layout.add_widget(info_btn)
        
        audio_card.add_widget(button_layout)
        
        # Add click to select functionality
        audio_card.bind(on_release=lambda x: self.select_audio_file(audio_file))
        
        return audio_card
    
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
                    content=MDLabel(text='Audio file not found on disk.'),
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
                    content=MDLabel(text=f'Opening in device audio player:\n{audio_file["display_name"]}'),
                    size_hint=(0.7, 0.4),
                    auto_dismiss=True
                )
                popup.open()
                Clock.schedule_once(lambda dt: popup.dismiss(), 2)
                
            except Exception as e:
                popup = Popup(
                    title='🎵 Audio File',
                    content=MDLabel(text=f'Audio File: {audio_file["display_name"]}\n\nLocation: {audio_path}\n\nPlease open with your preferred audio player.'),
                    size_hint=(0.8, 0.5),
                    auto_dismiss=True
                )
                popup.open()
                Clock.schedule_once(lambda dt: popup.dismiss(), 4)
                
        except Exception as e:
            print(f"Error opening audio file: {e}")
            popup = Popup(
                title='❌ Error',
                content=MDLabel(text=f'Could not open audio file:\n{str(e)}'),
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