import os
import shutil
import threading
import gc
from datetime import datetime
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivymd.uix.card import MDCard
import gc

# Import the core video vault functionality
from video_vault_core import VideoVaultCore

# REMOVED: Android imports and detection
# Desktop-only imports
import tkinter as tk
from tkinter import filedialog

# SIMPLIFIED: Desktop-only platform detection
ANDROID = False  # Always False for desktop-only version

# Import dialog components
from video_vault_dialogs import (
    show_import_results_dialog,
    show_file_movement_confirmation,
    show_fallback_file_picker,
    show_video_options_dialog,
    show_delete_confirmation_dialog,
    show_export_dialog,
    show_export_result_dialog,
    show_no_selection_popup,
    show_error_popup
)

class VideoVault(VideoVaultCore):
    """Main Video Vault class that combines core functionality with UI methods"""

    def cleanup_video_players(self):
        """Clean up video players to prevent memory leaks"""
        try:
            cleaned = 0
            # Clean up resource manager if available (optimized version)
            if hasattr(self, 'resource_manager'):
                cleaned = self.resource_manager.cleanup_video_players()
            else:
                # Fallback cleanup for basic version
                if hasattr(self, 'active_video_players'):
                    for player in self.active_video_players[:]:
                        try:
                            if player:
                                if hasattr(player, 'state'):
                                    player.state = 'stop'
                                if hasattr(player, 'unload'):
                                    player.unload()
                                if hasattr(player, 'texture'):
                                    player.texture = None
                                cleaned += 1
                        except Exception as e:
                            print(f"Error cleaning video player: {e}")
                    self.active_video_players.clear()
            
            print(f"✅ Cleaned up {cleaned} video players")
            return cleaned
        except Exception as e:
            print(f"Error in cleanup_video_players: {e}")
            return 0

    def cleanup_all_imageio_readers(self):
        """Clean up ImageIO readers to prevent memory leaks"""
        try:
            cleaned = 0
            # Clean up resource manager if available (optimized version)
            if hasattr(self, 'resource_manager'):
                cleaned = self.resource_manager.cleanup_imageio_readers()
            else:
                # Fallback cleanup for basic version
                if hasattr(self, 'imageio_readers'):
                    for reader in self.imageio_readers[:]:
                        try:
                            if reader and hasattr(reader, 'close'):
                                reader.close()
                                cleaned += 1
                        except Exception as e:
                            print(f"Error closing ImageIO reader: {e}")
                    self.imageio_readers.clear()
            
            print(f"✅ Cleaned up {cleaned} ImageIO readers")
            return cleaned
        except Exception as e:
            print(f"Error in cleanup_all_imageio_readers: {e}")
            return 0
    
    def select_videos_from_gallery(self, callback):
        """Open file picker to select videos - Desktop only"""
        if self.processing:
            print("Already processing, ignoring request")
            return
            
        self.processing = True
        print("Starting video selection from computer...")
        
        # SIMPLIFIED: Desktop-only file selection
        self.desktop_file_picker(callback)
    
    def desktop_file_picker(self, callback):
        """Desktop file picker using tkinter"""
        def pick_files():
            try:
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                
                file_paths = filedialog.askopenfilenames(
                    title="Select Videos from Computer",  # UPDATED: More desktop-appropriate
                    filetypes=[
                        ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.3gp *.ogg *.ogv"),
                        ("All files", "*.*")
                    ]
                )
                
                root.destroy()
                
                # Schedule callback on main thread
                Clock.schedule_once(lambda dt: self.handle_selection_async(file_paths, callback), 0)
                
            except Exception as e:
                print(f"Desktop file picker error: {e}")
                self.processing = False
                # Fallback to Kivy file chooser
                self.fallback_file_picker(callback)
        
        # Run in separate thread to avoid blocking
        thread = threading.Thread(target=pick_files)
        thread.daemon = True
        thread.start()
    
    def fallback_file_picker(self, callback):
        """Fallback file picker using Kivy's FileChooser - Desktop optimized"""
        def on_selection_callback(file_paths):
            self.handle_selection_async(file_paths, callback)
        
        show_fallback_file_picker(on_selection_callback)
    
    def handle_selection_async(self, file_paths, callback):
        """Handle selected video files asynchronously"""
        if not file_paths:
            self.processing = False
            return
        
        print(f"Selected {len(file_paths)} files for processing")
        # Show confirmation dialog for file movement
        show_file_movement_confirmation(file_paths, lambda fps, move_files: self.process_files(fps, callback, move_files))
    
    def process_files(self, file_paths, callback, move_files=True):
        """Process selected video files"""
        def process_files_worker():
            try:
                imported_files = []
                
                for file_path in file_paths:
                    try:
                        print(f"Processing file: {file_path}")
                        
                        # Check if it's a valid video file
                        if not self.is_valid_video(file_path):
                            print(f"Skipping invalid video file: {file_path}")
                            continue
                        
                        # Generate unique filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        filename = f"vault_{timestamp}_{os.path.basename(file_path)}"
                        destination = os.path.join(self.vault_dir, filename)
                        
                        # Move or copy file to vault directory
                        if move_files:
                            print(f"Moving file to: {destination}")
                            shutil.move(file_path, destination)  # MOVE instead of copy
                        else:
                            print(f"Copying file to: {destination}")
                            shutil.copy2(file_path, destination)  # COPY for less secure option
                        
                        # Generate thumbnail with proper cleanup
                        self.generate_thumbnail_safe(destination)
                        
                        imported_files.append(destination)
                        print(f"Successfully processed: {destination}")
                        
                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")
                
                print(f"File processing complete. {len(imported_files)} files imported.")
                # Schedule callback on main thread
                Clock.schedule_once(lambda dt: self.finish_import(imported_files, callback, move_files), 0)
                
            except Exception as e:
                print(f"Error processing files: {e}")
                Clock.schedule_once(lambda dt: self.finish_import([], callback, move_files), 0)
        
        # Run file operations in background thread
        thread = threading.Thread(target=process_files_worker)
        thread.daemon = True
        thread.start()
    
    def finish_import(self, imported_files, callback, moved_files):
        """Finish import process on main thread"""
        self.processing = False
        if imported_files:
            callback(imported_files, moved_files)
    
    def create_video_gallery_widget(self):
        """Create the main video gallery widget"""
        return VideoGalleryWidget(self)

class VideoGalleryWidget(MDBoxLayout):
    """UI Widget for managing video gallery with BlueGray theme"""
    
    def __init__(self, video_vault, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.video_vault = video_vault
        self.vault_core = video_vault  # Add this line for compatibility
        self.selected_video = None
        self.video_widgets = []  # Keep track of video widgets for cleanup
        
        # Set BlueGray background
        self.md_bg_color = [0.37, 0.49, 0.55, 1]
        
        self.build_ui()
        
        # Load initial videos
        Clock.schedule_once(lambda dt: self.refresh_gallery(None), 0.1)
    
    def build_ui(self):
        """Build the main UI layout"""
        # Header with title and add button
        self.build_header()
        
        # Video grid in scroll view
        self.build_video_grid()
        
        # Bottom action buttons
        self.build_bottom_buttons()
    
    def build_header(self):
        """Build header with title and add button"""
        header = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),  # Compact header for desktop
            padding=[20, 20, 20, 10],
            spacing=10
        )
        
        # Large title
        title = MDLabel(
            text='VIDEO GALLERY',
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
            text='🎬 Add Videos',
            md_bg_color=[0.2, 0.7, 0.3, 1],
            text_color="white",
            size_hint_x=1,
            elevation=3
        )
        self.add_btn.bind(on_press=self.add_videos)
        actions_row.add_widget(self.add_btn)
        
        header.add_widget(actions_row)
        
        self.add_widget(header)
    
    def build_video_grid(self):
        """Build scrollable video grid"""
        scroll = MDScrollView(
            bar_width=dp(4),
            bar_color=[0.46, 0.53, 0.6, 0.7],
            bar_inactive_color=[0.7, 0.7, 0.7, 0.3],
            effect_cls="ScrollEffect"
        )
        
        self.video_grid = MDGridLayout(
            cols=2,
            spacing=15,
            padding=[20, 10, 20, 10],
            size_hint_y=None,
            adaptive_height=True
        )
        
        scroll.add_widget(self.video_grid)
        self.add_widget(scroll)
    
    def build_bottom_buttons(self):
        """Build bottom action buttons"""
        bottom_bar = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(70),
            padding=15,
            spacing=12,
            elevation=8,
            md_bg_color=[0.25, 0.29, 0.31, 1]  # BlueGray dark
        )
        
        self.refresh_btn = MDFlatButton(
            text='🔄 Refresh',
            text_color="white",
            size_hint_x=0.25
        )
        self.refresh_btn.bind(on_press=self.refresh_gallery)
        bottom_bar.add_widget(self.refresh_btn)
        
        self.export_btn = MDFlatButton(
            text='📤 Export',
            text_color=[0.6, 0.4, 0.9, 1],
            size_hint_x=0.25
        )
        self.export_btn.bind(on_press=self.export_selected_video)
        bottom_bar.add_widget(self.export_btn)
        
        self.add_more_btn = MDFlatButton(
            text='➕ Add More',
            text_color=[0.4, 0.8, 0.4, 1],
            size_hint_x=0.25
        )
        self.add_more_btn.bind(on_press=self.add_videos)
        bottom_bar.add_widget(self.add_more_btn)
        
        self.back_btn = MDFlatButton(
            text='← Back',
            text_color=[0.7, 0.7, 0.7, 1],
            size_hint_x=0.25
        )
        self.back_btn.bind(on_press=self.back_to_vault)
        bottom_bar.add_widget(self.back_btn)
        
        self.add_widget(bottom_bar)
    
    def add_videos(self, instance):
        """Handle add videos button press"""
        # Disable button during processing
        if self.video_vault.processing:
            print("Video vault is already processing, ignoring add request")
            return
            
        self.add_btn.disabled = True
        self.add_btn.text = 'Processing...'
        
        def on_videos_added(imported_files, moved_files):
            # Re-enable button
            self.add_btn.disabled = False
            self.add_btn.text = '🎬 Add Videos'
            
            if imported_files:
                # Refresh gallery
                self.refresh_gallery(None)
                
                # Show success message using dialog
                show_import_results_dialog(imported_files, moved_files)
        
        self.video_vault.select_videos_from_gallery(on_videos_added)
    
    def refresh_gallery(self, instance):
        """Refresh the video gallery"""
        print("Refreshing video gallery...")
        
        # Clean up resources first
        self.video_vault.cleanup_video_players()
        self.video_vault.cleanup_all_imageio_readers()
        
        # Clear existing widgets
        self.cleanup_video_widgets()
        self.video_grid.clear_widgets()
        
        # Force garbage collection
        gc.collect()
        
        videos = self.video_vault.get_vault_videos()
        print(f"Found {len(videos)} videos in vault")
        
        if not videos:
            # Show empty state
            empty_widget = self.create_empty_state_widget()
            self.video_grid.add_widget(empty_widget)
            return
        
        # Load videos in batches to avoid memory issues
        self.load_videos_batch(videos, 0)
    
    def create_empty_state_widget(self):
        """Create empty state widget"""
        empty_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height=dp(200),
            padding=30,
            spacing=20,
            md_bg_color=[0.31, 0.35, 0.39, 0.8],  # BlueGray light
            elevation=2
        )
        
        empty_label = MDLabel(
            text='🎬 No videos in vault\n\nTap "Add Videos" to import your videos\nfrom your computer and keep them secure',  # UPDATED: Desktop-appropriate text
            font_style="Body1",
            halign='center',
            text_color=[0.7, 0.7, 0.7, 1]
        )
        empty_label.bind(size=empty_label.setter('text_size'))
        empty_card.add_widget(empty_label)
        
        return empty_card
    
    def load_videos_batch(self, videos, start_index, batch_size=4):
        """Load videos in batches to prevent memory issues"""
        end_index = min(start_index + batch_size, len(videos))
        
        print(f"Loading videos batch {start_index} to {end_index}")
        
        for i in range(start_index, end_index):
            video_path = videos[i]
            video_widget = self.create_video_widget(video_path)
            self.video_grid.add_widget(video_widget)
            self.video_widgets.append(video_widget)
        
        # Load next batch if there are more videos
        if end_index < len(videos):
            Clock.schedule_once(lambda dt: self.load_videos_batch(videos, end_index), 0.1)
    
    def cleanup_video_widgets(self):
        """Enhanced cleanup with proper event unbinding"""
        if hasattr(self, '_widget_bindings'):
            for widget, event, callback in self._widget_bindings:
                try:
                    if widget:
                        widget.unbind(**{event: callback})
                except:
                    pass
            self._widget_bindings.clear()
        
        for widget in self.video_widgets:
            try:
                if hasattr(widget, 'children'):
                    for child in widget.children:
                        if hasattr(child, 'children'):
                            for grandchild in child.children:
                                if hasattr(grandchild, 'texture'):
                                    grandchild.texture = None
                                if hasattr(grandchild, 'source'):
                                    grandchild.source = ''
                
                if hasattr(widget, 'clear_widgets'):
                    widget.clear_widgets()
            except:
                pass
        
        self.video_widgets.clear()
        gc.collect()
    
    def create_video_widget(self, video_path):
        
        is_selected = self.selected_video == video_path
        
        video_card = MDCard(
            size_hint_y=None,
            height=dp(280),
            md_bg_color=[0.46, 0.53, 0.6, 1] if is_selected else [0.31, 0.35, 0.39, 0.9],
            elevation=4 if is_selected else 2,
            ripple_behavior=True
        )
        
        main_layout = BoxLayout(
            orientation='vertical',
            padding=10,
            spacing=8
        )
        
        thumb_path = self.video_vault.get_thumbnail_path(video_path)
        
        if thumb_path and os.path.exists(thumb_path):
            img = Image(
                source=thumb_path,
                size_hint_y=0.7
            )
            main_layout.add_widget(img)
        else:
            fallback_label = Label(
                text='🎬\nTap to Select',
                size_hint_y=0.7,
                color=[0.8, 0.8, 0.8, 1],
                halign='center'
            )
            main_layout.add_widget(fallback_label)
        
        filename = os.path.basename(video_path)
        display_name = filename[:20] + '...' if len(filename) > 20 else filename
        
        video_info = self.video_vault.get_video_info_safe(video_path)
        
        info_text = f"{display_name}\n{video_info['size']} | {video_info['duration']}"
        if is_selected:
            info_text += "\n🔴 SELECTED"
        
        info_label = Label(
            text=info_text,
            size_hint_y=0.3,
            color=[0.9, 0.9, 0.9, 1] if is_selected else [0.7, 0.7, 0.7, 1],
            halign='center'
        )
        main_layout.add_widget(info_label)
        
        video_card.add_widget(main_layout)
        
        def create_select_callback(path):
            def callback(instance):
                self.select_video(path)
            return callback
        
        select_callback = create_select_callback(video_path)
        video_card.bind(on_release=select_callback)
        
        if not hasattr(self, '_widget_bindings'):
            self._widget_bindings = []
        self._widget_bindings.append((video_card, 'on_release', select_callback))
        
        return video_card

        gc.collect()

    
    def select_video(self, video_path):
        """Select a video and show enhanced options dialog"""
        self.selected_video = video_path
        print(f"Selected video: {video_path}")
        
        # Refresh the gallery to show selection indicator
        self.refresh_gallery(None)
        
        # Show video options dialog
        show_video_options_dialog(
            video_path,
            self.video_vault,
            lambda: self.refresh_gallery(None),
            lambda: self.export_selected_video(None),
            self.enhanced_delete_video
        )
    
    def enhanced_delete_video(self, video_path):
        """Enhanced delete with recycle bin"""
        def refresh_and_clear():
            self.selected_video = None
            self.refresh_gallery(None)
        
        show_delete_confirmation_dialog(video_path, self.video_vault, refresh_and_clear)
    
    def export_selected_video(self, instance):
        """Export the selected video with folder selection"""
        if not self.selected_video:
            show_no_selection_popup("export")
            return
        
        show_export_dialog(self.selected_video, self.choose_folder_and_export)
    
    def choose_folder_and_export(self):
        """Choose folder and perform export"""
        def on_folder_selected(result):
            if result['success']:
                folder_path = result['folder_path']
                is_fallback = result.get('is_fallback', False)
                
                # Perform export
                export_result = self.video_vault.export_video(self.selected_video, folder_path)
                
                if export_result['success']:
                    # Success message with location
                    success_text = f"✅ Video exported successfully!\n\n"
                    success_text += f"🎬 File: {export_result['original_name']}\n"
                    success_text += f"📁 Location: {export_result['export_path']}\n\n"
                    
                    if is_fallback:
                        success_text += "⚠️ Used app storage as destination\n"
                    
                    success_text += "You can now play it in your video player."
                    
                    show_export_result_dialog(success_text, "Export Successful", True)
                else:
                    self.handle_export_error(export_result)
            else:
                # Folder selection failed
                error_text = f"❌ Folder selection failed!\n\nError: {result['error']}\n\nPlease try again."
                show_export_result_dialog(error_text, "Folder Selection Failed", False, self.choose_folder_and_export)
        
        # Start folder selection
        self.video_vault.select_export_folder(on_folder_selected)

    def handle_export_error(self, export_result):
        """Handle export errors with retry option"""
        if export_result.get('needs_folder_selection'):
            error_text = f"❌ Export failed!\n\nError: {export_result['error']}\n\nWould you like to try with a different folder?"
            show_export_result_dialog(error_text, "Export Failed", False, self.choose_folder_and_export)
        else:
            error_text = f"❌ Export failed!\n\nError: {export_result['error']}"
            show_export_result_dialog(error_text, "Export Failed", False, None)
    
    def back_to_vault(self, instance):
        """Go back to main vault screen"""
        print("Going back to main vault screen...")
        
        # Clean up before leaving
        self.video_vault.cleanup_video_players()
        self.video_vault.cleanup_all_imageio_readers()
        self.cleanup_video_widgets()
        
        # Navigate back
        if hasattr(self.video_vault.app, 'show_vault_main'):
            self.video_vault.app.show_vault_main()

# Integration helper function
def integrate_video_vault(vault_app):
    """Helper function to integrate video vault into the main app"""
    vault_app.video_vault = VideoVault(vault_app)
    
    def show_video_gallery():
        """Show the video gallery"""
        print("Showing video gallery...")
        vault_app.main_layout.clear_widgets()
        
        # Create video gallery widget
        video_gallery = vault_app.video_vault.create_video_gallery_widget()
        vault_app.main_layout.add_widget(video_gallery)
        
        # Store reference for navigation
        vault_app.current_screen = 'video_gallery'
    
    # Add method to vault app
    vault_app.show_video_gallery = show_video_gallery
    
    return vault_app.video_vault

# Additional helper functions for debugging
def cleanup_temp_files():
    """Clean up any temporary files marked for deletion"""
    import tempfile
    temp_dir = tempfile.gettempdir()
    
    try:
        for filename in os.listdir(temp_dir):
            if filename.startswith('delete_me_') or filename.endswith('.DELETE_ME'):
                file_path = os.path.join(temp_dir, filename)
                try:
                    os.remove(file_path)
                    print(f"Cleaned up temp file: {filename}")
                except:
                    pass
    except Exception as e:
        print(f"Error cleaning temp files: {e}")

def get_vault_statistics(vault_instance):
    """Get statistics about the video vault"""
    try:
        videos = vault_instance.get_vault_videos()
        total_size = 0
        
        for video_path in videos:
            try:
                total_size += os.path.getsize(video_path)
            except:
                pass
        
        total_size_mb = round(total_size / (1024 * 1024), 1)
        
        return {
            'video_count': len(videos),
            'total_size_mb': total_size_mb,
            'vault_directory': vault_instance.vault_dir
        }
    except Exception as e:
        print(f"Error getting vault statistics: {e}")
        return {'video_count': 0, 'total_size_mb': 0, 'vault_directory': 'Unknown'}