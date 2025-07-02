import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp

# Try to import audio libraries
try:
    import pygame
    PYGAME_AVAILABLE = True
    print("🎵 Pygame audio support available")
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️ Pygame not available - basic audio player only")

try:
    from kivy.core.audio import SoundLoader
    KIVY_AUDIO_AVAILABLE = True
    print("🎵 Kivy audio support available")
except ImportError:
    KIVY_AUDIO_AVAILABLE = False
    print("⚠️ Kivy audio not available")

class AudioPlayerWidget(BoxLayout):
    """
    Audio Player Widget - Simple audio playback for the vault
    Supports multiple audio backends (Pygame, Kivy Audio, system default)
    """
    
    def __init__(self, audio_file_info, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.audio_file = audio_file_info
        self.audio_path = audio_file_info.get('vault_path', '')
        self.sound = None
        self.is_playing = False
        self.is_paused = False
        self.duration = audio_file_info.get('metadata', {}).get('duration', 0)
        self.position = 0
        
        # Initialize audio backend
        self.audio_backend = self.initialize_audio_backend()
        
        # Create player UI
        self.create_player_interface()
        
        # Start position update timer
        self.update_timer = None
    
    def initialize_audio_backend(self):
        """Initialize the best available audio backend - prioritize system player"""
        # Prioritize system player (device's default audio player)
        return 'system'
        
        # Custom players available as fallback if needed
        # if PYGAME_AVAILABLE:
        #     try:
        #         pygame.mixer.init()
        #         return 'pygame'
        #     except:
        #         pass
        # 
        # if KIVY_AUDIO_AVAILABLE:
        #     return 'kivy'
    
    def create_player_interface(self):
        """Create the audio player interface"""
        # File info header
        info_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), padding=10)
        
        title_label = Label(
            text=f"🎵 {self.audio_file['display_name']}",
            font_size=16,
            bold=True,
            size_hint_y=0.6
        )
        info_layout.add_widget(title_label)
        
        # Get metadata for subtitle
        extracted_fields = self.audio_file.get('metadata', {}).get('extracted_fields', {})
        artist = extracted_fields.get('artist', extracted_fields.get('ARTIST', ''))
        album = extracted_fields.get('album', extracted_fields.get('ALBUM', ''))
        
        subtitle_text = ""
        if artist:
            subtitle_text += f"👤 {artist}"
        if album:
            if subtitle_text:
                subtitle_text += f" • 💿 {album}"
            else:
                subtitle_text += f"💿 {album}"
        
        if not subtitle_text:
            subtitle_text = f"📁 {self.audio_file['format_info']}"
        
        subtitle_label = Label(
            text=subtitle_text,
            font_size=14,
            size_hint_y=0.4,
            color=(0.8, 0.8, 0.8, 1)
        )
        info_layout.add_widget(subtitle_label)
        
        self.add_widget(info_layout)
        
        # Progress bar
        progress_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), padding=10)
        
        self.time_label = Label(
            text="0:00",
            size_hint_x=0.15,
            font_size=12
        )
        progress_layout.add_widget(self.time_label)
        
        self.progress_slider = Slider(
            min=0,
            max=max(1, self.duration),  # Avoid division by zero
            value=0,
            size_hint_x=0.7
        )
        self.progress_slider.bind(on_touch_up=self.on_progress_change)
        progress_layout.add_widget(self.progress_slider)
        
        duration_minutes = int(self.duration // 60)
        duration_seconds = int(self.duration % 60)
        self.duration_label = Label(
            text=f"{duration_minutes}:{duration_seconds:02d}",
            size_hint_x=0.15,
            font_size=12
        )
        progress_layout.add_widget(self.duration_label)
        
        self.add_widget(progress_layout)
        
        # Control buttons
        controls_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=10, spacing=10)
        
        self.play_pause_btn = Button(
            text="▶️ Play",
            size_hint_x=0.3,
            font_size=16,
            background_color=(0.2, 0.6, 0.8, 1)
        )
        self.play_pause_btn.bind(on_press=self.toggle_play_pause)
        controls_layout.add_widget(self.play_pause_btn)
        
        self.stop_btn = Button(
            text="⏹️ Stop",
            size_hint_x=0.2,
            font_size=16
        )
        self.stop_btn.bind(on_press=self.stop_audio)
        controls_layout.add_widget(self.stop_btn)
        
        volume_layout = BoxLayout(orientation='horizontal', size_hint_x=0.5)
        
        volume_label = Label(
            text="🔊",
            size_hint_x=0.2,
            font_size=16
        )
        volume_layout.add_widget(volume_label)
        
        self.volume_slider = Slider(
            min=0,
            max=1,
            value=0.7,
            size_hint_x=0.8
        )
        self.volume_slider.bind(value=self.on_volume_change)
        volume_layout.add_widget(self.volume_slider)
        
        controls_layout.add_widget(volume_layout)
        
        self.add_widget(controls_layout)
        
        # Status and backend info
        status_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(50), padding=10)
        
        self.status_label = Label(
            text=f"🎵 Ready to play • Backend: {self.audio_backend.title()}",
            font_size=12,
            color=(0.7, 0.7, 0.7, 1)
        )
        status_layout.add_widget(self.status_label)
        
        self.add_widget(status_layout)
        
        # Close button
        close_btn = Button(
            text="❌ Close Player",
            size_hint_y=None,
            height=dp(50),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        close_btn.bind(on_press=self.close_player)
        self.add_widget(close_btn)
    
    def toggle_play_pause(self, instance):
        """Toggle between play and pause"""
        if not os.path.exists(self.audio_path):
            self.status_label.text = "❌ Audio file not found"
            return
        
        if self.is_playing:
            self.pause_audio()
        else:
            self.play_audio()
    
    def play_audio(self):
        """Start playing audio"""
        try:
            if self.is_paused:
                # Resume from pause
                self.resume_audio()
                return
            
            # Load and play audio based on backend
            if self.audio_backend == 'pygame':
                self.play_with_pygame()
            elif self.audio_backend == 'kivy':
                self.play_with_kivy()
            else:
                self.play_with_system()
            
        except Exception as e:
            self.status_label.text = f"❌ Playback error: {str(e)}"
            print(f"Audio playback error: {e}")
    
    def play_with_pygame(self):
        """Play audio using Pygame"""
        try:
            pygame.mixer.music.load(self.audio_path)
            pygame.mixer.music.play(start=self.position)
            
            self.is_playing = True
            self.is_paused = False
            self.play_pause_btn.text = "⏸️ Pause"
            self.status_label.text = "🎵 Playing with Pygame"
            
            # Start position update timer
            self.start_position_timer()
            
        except Exception as e:
            raise Exception(f"Pygame error: {str(e)}")
    
    def play_with_kivy(self):
        """Play audio using Kivy SoundLoader"""
        try:
            if not self.sound:
                self.sound = SoundLoader.load(self.audio_path)
            
            if self.sound:
                self.sound.volume = self.volume_slider.value
                self.sound.play()
                
                self.is_playing = True
                self.is_paused = False
                self.play_pause_btn.text = "⏸️ Pause"
                self.status_label.text = "🎵 Playing with Kivy Audio"
                
                # Start position update timer
                self.start_position_timer()
            else:
                raise Exception("Could not load audio file")
                
        except Exception as e:
            raise Exception(f"Kivy Audio error: {str(e)}")
    
    def play_with_system(self):
        """Play audio using system default player"""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                os.startfile(self.audio_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", self.audio_path])
            else:  # Linux and others
                subprocess.run(["xdg-open", self.audio_path])
            
            self.status_label.text = "🎵 Opened with system player"
            
        except Exception as e:
            raise Exception(f"System player error: {str(e)}")
    
    def pause_audio(self):
        """Pause audio playback"""
        try:
            if self.audio_backend == 'pygame':
                pygame.mixer.music.pause()
            elif self.audio_backend == 'kivy' and self.sound:
                self.sound.stop()  # Kivy doesn't have pause, so we stop
            
            self.is_playing = False
            self.is_paused = True
            self.play_pause_btn.text = "▶️ Resume"
            self.status_label.text = "⏸️ Paused"
            
            # Stop position timer
            self.stop_position_timer()
            
        except Exception as e:
            self.status_label.text = f"❌ Pause error: {str(e)}"
    
    def resume_audio(self):
        """Resume audio playback"""
        try:
            if self.audio_backend == 'pygame':
                pygame.mixer.music.unpause()
            elif self.audio_backend == 'kivy':
                # Kivy doesn't have resume, so restart from position
                self.play_with_kivy()
                return
            
            self.is_playing = True
            self.is_paused = False
            self.play_pause_btn.text = "⏸️ Pause"
            self.status_label.text = "🎵 Resumed"
            
            # Restart position timer
            self.start_position_timer()
            
        except Exception as e:
            self.status_label.text = f"❌ Resume error: {str(e)}"
    
    def stop_audio(self, instance):
        """Stop audio playback"""
        try:
            if self.audio_backend == 'pygame':
                pygame.mixer.music.stop()
            elif self.audio_backend == 'kivy' and self.sound:
                self.sound.stop()
            
            self.is_playing = False
            self.is_paused = False
            self.position = 0
            self.progress_slider.value = 0
            self.play_pause_btn.text = "▶️ Play"
            self.time_label.text = "0:00"
            self.status_label.text = "⏹️ Stopped"
            
            # Stop position timer
            self.stop_position_timer()
            
        except Exception as e:
            self.status_label.text = f"❌ Stop error: {str(e)}"
    
    def on_progress_change(self, instance, touch):
        """Handle progress bar changes"""
        if instance.collide_point(*touch.pos):
            # Calculate new position
            new_position = self.progress_slider.value
            self.position = new_position
            
            # If playing, seek to new position
            if self.is_playing and self.audio_backend == 'pygame':
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.play(start=new_position)
                except:
                    pass  # Seeking might not be supported
            
            # Update time display
            minutes = int(new_position // 60)
            seconds = int(new_position % 60)
            self.time_label.text = f"{minutes}:{seconds:02d}"
    
    def on_volume_change(self, instance, value):
        """Handle volume changes"""
        try:
            if self.audio_backend == 'pygame':
                pygame.mixer.music.set_volume(value)
            elif self.audio_backend == 'kivy' and self.sound:
                self.sound.volume = value
            
        except Exception as e:
            print(f"Volume change error: {e}")
    
    def start_position_timer(self):
        """Start timer to update playback position"""
        if self.update_timer:
            self.update_timer.cancel()
        
        self.update_timer = Clock.schedule_interval(self.update_position, 1.0)
    
    def stop_position_timer(self):
        """Stop position update timer"""
        if self.update_timer:
            self.update_timer.cancel()
            self.update_timer = None
    
    def update_position(self, dt):
        """Update playback position and UI"""
        if not self.is_playing:
            return False  # Stop the timer
        
        try:
            # Estimate position (this is approximate)
            self.position += 1
            
            # Check if playback finished
            if self.position >= self.duration:
                self.stop_audio(None)
                return False
            
            # Update UI
            self.progress_slider.value = self.position
            minutes = int(self.position // 60)
            seconds = int(self.position % 60)
            self.time_label.text = f"{minutes}:{seconds:02d}"
            
            return True  # Continue the timer
            
        except Exception as e:
            print(f"Position update error: {e}")
            return False
    
    def close_player(self, instance):
        """Close the audio player"""
        # Stop any playing audio
        self.stop_audio(None)
        
        # Clean up resources
        if self.audio_backend == 'pygame':
            try:
                pygame.mixer.quit()
            except:
                pass
        
        # Find parent popup and dismiss it
        parent = self.parent
        while parent:
            if isinstance(parent, Popup):
                parent.dismiss()
                break
            parent = parent.parent


def show_audio_player(audio_file_info):
    """
    Show audio player popup for a given audio file
    
    Args:
        audio_file_info: Dictionary containing audio file information
    """
    player_widget = AudioPlayerWidget(audio_file_info)
    
    popup = Popup(
        title=f'🎵 Audio Player',
        content=player_widget,
        size_hint=(0.9, 0.8),
        auto_dismiss=False
    )
    
    popup.open()
    return popup


def create_simple_audio_info_popup(audio_file_info):
    """
    Create a simple popup showing audio file info when player is not available
    """
    content = BoxLayout(orientation='vertical', spacing=15, padding=15)
    
    # File info
    extracted_fields = audio_file_info.get('metadata', {}).get('extracted_fields', {})
    artist = extracted_fields.get('artist', extracted_fields.get('ARTIST', ''))
    album = extracted_fields.get('album', extracted_fields.get('ALBUM', ''))
    
    info_text = f"""🎵 {audio_file_info['display_name']}
    
📁 Format: {audio_file_info['format_info']}
📊 Size: {audio_file_info['size_mb']:.1f} MB
⏱️ Duration: {audio_file_info['duration_str']}"""
    
    if artist:
        info_text += f"\n👤 Artist: {artist}"
    if album:
        info_text += f"\n💿 Album: {album}"
    
    info_text += f"\n\n📍 File Location:\n{audio_file_info['vault_path']}"
    
    info_label = Label(
        text=info_text,
        font_size=14,
        halign='left'
    )
    info_label.bind(size=info_label.setter('text_size'))
    content.add_widget(info_label)
    
    # Note about audio playback
    note_label = Label(
        text="💡 Audio playback requires pygame or kivy audio libraries.\nFile location shown above for external player use.",
        font_size=12,
        halign='center',
        color=(0.7, 0.7, 0.7, 1),
        size_hint_y=None,
        height=dp(60)
    )
    note_label.bind(size=note_label.setter('text_size'))
    content.add_widget(note_label)
    
    # Close button
    close_btn = Button(
        text="❌ Close",
        size_hint_y=None,
        height=dp(50)
    )
    content.add_widget(close_btn)
    
    popup = Popup(
        title='🎵 Audio File Info',
        content=content,
        size_hint=(0.8, 0.7),
        auto_dismiss=False
    )
    
    close_btn.bind(on_press=popup.dismiss)
    popup.open()
    
    return popup