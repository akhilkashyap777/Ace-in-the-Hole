import os
import shutil
import threading
import gc
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.clock import Clock
from kivy.metrics import dp

# Import the core video vault functionality
from video_vault_core import VideoVaultCore, ANDROID
import re

# Import Android/Desktop specific modules for file selection
if not ANDROID:
    import tkinter as tk
    from tkinter import filedialog
else:
    try:
        from plyer import filechooser
        from android.storage import primary_external_storage_path
    except ImportError:
        pass

class VideoVault(VideoVaultCore):
    """Main Video Vault class that combines core functionality with UI methods"""
    
    def select_videos_from_gallery(self, callback):
        """Open gallery/file picker to select videos"""
        if self.processing:
            print("Already processing, ignoring request")
            return
            
        self.processing = True
        print("Starting video selection from gallery...")
        
        if ANDROID:
            try:
                def on_selection(selection):
                    Clock.schedule_once(lambda dt: self.handle_selection_async(selection, callback), 0)
                
                filechooser.open_file(
                    on_selection=on_selection,
                    multiple=True,
                    filters=['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.webm', '*.3gp', '*.ogg', '*.ogv']
                )
            except Exception as e:
                print(f"Error opening Android file chooser: {e}")
                self.processing = False
                self.fallback_file_picker(callback)
        else:
            self.desktop_file_picker(callback)
    
    def desktop_file_picker(self, callback):
        """Desktop file picker using tkinter"""
        def pick_files():
            try:
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                
                file_paths = filedialog.askopenfilenames(
                    title="Select Videos",
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
        
        # Run in separate thread to avoid blocking
        thread = threading.Thread(target=pick_files)
        thread.daemon = True
        thread.start()
    
    def fallback_file_picker(self, callback):
        """Fallback file picker using Kivy's FileChooser"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # File chooser
        if ANDROID:
            try:
                start_path = primary_external_storage_path()
            except:
                start_path = '/sdcard'
        else:
            start_path = os.path.expanduser('~')
        
        filechooser = FileChooserIconView(
            path=start_path,
            filters=['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.webm', '*.3gp', '*.ogg', '*.ogv'],
            multiselect=True
        )
        content.add_widget(filechooser)
        
        # Buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        
        select_btn = Button(text='Select Videos', size_hint_x=0.5)
        cancel_btn = Button(text='Cancel', size_hint_x=0.5)
        
        button_layout.add_widget(select_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title='Select Videos from Gallery',
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
        """Handle selected video files asynchronously"""
        if not file_paths:
            self.processing = False
            return
        
        print(f"Selected {len(file_paths)} files for processing")
        # Show confirmation dialog for file movement
        self.confirm_file_movement(file_paths, callback)
    
    def confirm_file_movement(self, file_paths, callback):
        """Confirm that user wants to move files (not copy)"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        warning_text = f"""⚠️ IMPORTANT SECURITY NOTICE ⚠️

{len(file_paths)} video(s) will be MOVED to secure vault.

This means:
• Files will DISAPPEAR from current location
• Files will only exist in the secure vault
• This is more secure than copying

Continue?"""
        
        label = Label(
            text=warning_text,
            text_size=(400, None),
            halign='center'
        )
        content.add_widget(label)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        
        move_btn = Button(text='✅ Yes, Move to Vault')
        copy_btn = Button(text='📋 Copy Instead (Less Secure)')
        cancel_btn = Button(text='❌ Cancel')
        
        btn_layout.add_widget(move_btn)
        btn_layout.add_widget(copy_btn) 
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title='Move Files to Vault?',
            content=content,
            size_hint=(0.8, 0.6),
            auto_dismiss=False
        )
        
        def move_files(instance):
            popup.dismiss()
            self.process_files(file_paths, callback, move_files=True)
        
        def copy_files(instance):
            popup.dismiss()
            self.process_files(file_paths, callback, move_files=False)
        
        def cancel_action(instance):
            popup.dismiss()
            self.processing = False
        
        move_btn.bind(on_press=move_files)
        copy_btn.bind(on_press=copy_files)
        cancel_btn.bind(on_press=cancel_action)
        
        popup.open()
    
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

class VideoGalleryWidget(BoxLayout):
    """UI Widget for managing video gallery - FIXED VERSION"""
    
    def __init__(self, video_vault, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.video_vault = video_vault
        self.selected_video = None
        self.video_widgets = []  # Keep track of video widgets for cleanup
        
        # Header with title and add button
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=10)
        
        title = Label(text='🎬 Secret Videos', font_size=24, size_hint_x=0.7)
        header.add_widget(title)
        
        self.add_btn = Button(text='+ Add Videos', font_size=16, size_hint_x=0.3)
        self.add_btn.bind(on_press=self.add_videos)
        header.add_widget(self.add_btn)
        
        self.add_widget(header)
        
        # Video grid in scroll view
        scroll = ScrollView()
        self.video_grid = GridLayout(cols=2, spacing=10, padding=10, size_hint_y=None)
        self.video_grid.bind(minimum_height=self.video_grid.setter('height'))
        
        scroll.add_widget(self.video_grid)
        self.add_widget(scroll)
        
        # FIXED: Bottom buttons - only 3 buttons, no duplicate delete
        bottom_layout = self.create_bottom_buttons_fixed()
        self.add_widget(bottom_layout)
        
        # Load initial videos
        Clock.schedule_once(lambda dt: self.refresh_gallery(None), 0.1)
    
    def create_bottom_buttons_fixed(self):
        """FIXED: Create bottom buttons with export functionality"""
        bottom_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), padding=10)
        
        # 4 buttons: Refresh, Export, Add More, Back
        self.refresh_btn = Button(text='🔄 Refresh', size_hint_x=0.25)
        self.refresh_btn.bind(on_press=self.refresh_gallery)
        bottom_layout.add_widget(self.refresh_btn)
        
        self.export_btn = Button(text='📤 Export', size_hint_x=0.25)
        self.export_btn.bind(on_press=self.export_selected_video)
        bottom_layout.add_widget(self.export_btn)
        
        self.add_more_btn = Button(text='➕ Add More', size_hint_x=0.25)
        self.add_more_btn.bind(on_press=self.add_videos)
        bottom_layout.add_widget(self.add_more_btn)
        
        self.back_btn = Button(text='🔙 Back to Vault', size_hint_x=0.25)
        self.back_btn.bind(on_press=self.back_to_vault)
        bottom_layout.add_widget(self.back_btn)
        
        return bottom_layout
    
    def add_videos(self, instance):
        """Handle add videos button press"""
        # Disable button during processing
        if self.video_vault.processing:
            print("Video vault is already processing, ignoring add request")
            return
            
        self.add_btn.disabled = True
        self.add_btn.text = 'Processing...'
        
        self.video_vault.request_permissions()
        
        def on_videos_added(imported_files, moved_files):
            # Re-enable button
            self.add_btn.disabled = False
            self.add_btn.text = '+ Add Videos'
            
            if imported_files:
                # Refresh gallery
                self.refresh_gallery(None)
                
                # Show success message
                count = len(imported_files)
                action = "moved" if moved_files else "copied"
                content = Label(text=f'Successfully {action} {count} video(s) to vault!')
                popup = Popup(
                    title='Videos Added',
                    content=content,
                    size_hint=(0.7, 0.3),
                    auto_dismiss=True
                )
                popup.open()
                Clock.schedule_once(lambda dt: popup.dismiss(), 2)
        
        self.video_vault.select_videos_from_gallery(on_videos_added)
    
    def refresh_gallery(self, instance):
        """Refresh the video gallery"""
        print("Refreshing video gallery...")
        
        # Clean up resources first
        self.video_vault.cleanup_video_players()
        self.video_vault.cleanup_all_cv2_captures()
        
        # Clear existing widgets
        self.cleanup_video_widgets()
        self.video_grid.clear_widgets()
        # Don't reset selected_video here so selection indicator works
        
        # Force garbage collection
        gc.collect()
        
        videos = self.video_vault.get_vault_videos()
        print(f"Found {len(videos)} videos in vault")
        
        if not videos:
            # Show empty state
            empty_label = Label(
                text='No videos in vault\nTap "Add Videos" to get started',
                font_size=18,
                halign='center'
            )
            self.video_grid.add_widget(empty_label)
            return
        
        # Load videos in batches to avoid memory issues
        self.load_videos_batch(videos, 0)
    
    def load_videos_batch(self, videos, start_index, batch_size=4):
        """Load videos in batches to prevent memory issues"""
        end_index = min(start_index + batch_size, len(videos))
        
        print(f"Loading videos batch {start_index} to {end_index}")
        
        for i in range(start_index, end_index):
            video_path = videos[i]
            video_widget = self.create_video_widget_fixed(video_path)
            self.video_grid.add_widget(video_widget)
            self.video_widgets.append(video_widget)
        
        # Load next batch if there are more videos
        if end_index < len(videos):
            Clock.schedule_once(lambda dt: self.load_videos_batch(videos, end_index), 0.1)
    
    def cleanup_video_widgets(self):
        """Clean up video widgets to prevent memory leaks"""
        print(f"Cleaning up {len(self.video_widgets)} video widgets")
        for widget in self.video_widgets:
            try:
                if hasattr(widget, 'children'):
                    for child in widget.children:
                        if hasattr(child, 'texture'):
                            child.texture = None
            except:
                pass
        self.video_widgets.clear()
        
        # Force garbage collection
        gc.collect()
    
    def create_video_widget_fixed(self, video_path):
        """FIXED: Create a widget for displaying a video thumbnail with proper display"""
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(250), spacing=5)
        
        # Create clickable thumbnail area
        thumbnail_area = BoxLayout(size_hint_y=0.7)
        
        try:
            # Try to use thumbnail if available
            thumb_path = self.video_vault.get_thumbnail_path(video_path)
            
            if thumb_path and os.path.exists(thumb_path):
                print(f"Loading thumbnail: {thumb_path}")
                # Create image widget
                img = Image(
                    source=thumb_path,
                    fit_mode="contain",
                    size_hint=(1, 1)
                )
                
                # Create transparent button overlay for clicking
                click_btn = Button(
                    background_color=(0, 0, 0, 0),  # Transparent
                    text='',
                    size_hint=(1, 1)
                )
                click_btn.bind(on_press=lambda x: self.select_video_fixed(video_path))
                
                # Add both to the thumbnail area
                thumbnail_area.add_widget(img)
                thumbnail_area.add_widget(click_btn)
                
            else:
                # Fallback: create a visible button with video icon
                fallback_btn = Button(
                    text='🎬\nTap to Select',
                    font_size=16,
                    background_color=(0.2, 0.2, 0.2, 1),  # Dark gray
                    color=(1, 1, 1, 1),  # White text
                    size_hint=(1, 1)
                )
                fallback_btn.bind(on_press=lambda x: self.select_video_fixed(video_path))
                thumbnail_area.add_widget(fallback_btn)
                
        except Exception as e:
            print(f"Error loading thumbnail for {video_path}: {e}")
            # Error fallback
            error_btn = Button(
                text='🎬\nVideo\n(Tap to Select)',
                font_size=14,
                background_color=(0.3, 0.1, 0.1, 1),  # Dark red
                color=(1, 1, 1, 1),  # White text
                size_hint=(1, 1)
            )
            error_btn.bind(on_press=lambda x: self.select_video_fixed(video_path))
            thumbnail_area.add_widget(error_btn)
        
        layout.add_widget(thumbnail_area)
        
        # Video info with selection indicator
        filename = os.path.basename(video_path)
        display_name = filename[:25] + '...' if len(filename) > 25 else filename
        
        # Get video info safely
        video_info = self.video_vault.get_video_info_safe(video_path)
        
        # Add selection indicator
        selection_indicator = "🔴 SELECTED" if self.selected_video == video_path else ""
        
        info_text = f"{display_name}\n{video_info['size']} | {video_info['duration']}\n{selection_indicator}"
        info_label = Label(
            text=info_text,
            size_hint_y=0.3,
            font_size=11,
            halign='center',
            color=(1, 1, 1, 1)  # White text
        )
        info_label.bind(size=info_label.setter('text_size'))
        layout.add_widget(info_label)
        
        return layout
    
    def select_video_fixed(self, video_path):
        """FIXED: Select a video and show enhanced options dialog"""
        self.selected_video = video_path
        print(f"Selected video: {video_path}")
        
        # Refresh the gallery to show selection indicator
        self.refresh_gallery(None)
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Video info
        filename = os.path.basename(video_path)
        video_info = self.video_vault.get_video_info_safe(video_path)
        
        info_text = f"""📁 File: {filename}
    📊 Size: {video_info['size']}
    ⏱️ Duration: {video_info['duration']}
    📍 Location: {video_path}"""
        
        info_label = Label(
            text=info_text,
            halign='left',
            font_size=14
        )
        info_label.bind(size=info_label.setter('text_size'))
        content.add_widget(info_label)
        
        # Buttons
        btn_layout = BoxLayout(orientation='vertical', spacing=8, size_hint_y=None, height=dp(170))
        
        # First row - Play and Export
        row1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        
        play_btn = Button(
            text='▶️ Play Video',
            background_color=(0, 0.6, 0, 1),  # Green
            font_size=16
        )
        
        export_btn = Button(
            text='📤 Export Video',
            background_color=(0, 0, 0.8, 1),  # Blue
            font_size=16
        )
        
        row1.add_widget(play_btn)
        row1.add_widget(export_btn)
        btn_layout.add_widget(row1)
        
        # Second row - Delete
        delete_btn = Button(
            text='🗑️ Move to Recycle Bin',
            background_color=(0.8, 0, 0, 1),  # Red
            font_size=16,
            size_hint_y=None,
            height=dp(50)
        )
        btn_layout.add_widget(delete_btn)
        
        # Third row - Cancel
        cancel_btn = Button(
            text='❌ Cancel',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.3, 0.3, 0.3, 1),  # Gray
            font_size=16
        )
        btn_layout.add_widget(cancel_btn)
        
        content.add_widget(btn_layout)
        
        popup = Popup(
            title=f'🎬 Video Options - {filename[:30]}...',
            content=content,
            size_hint=(0.85, 0.8),
            auto_dismiss=False
        )
        
        def play_external(instance):
            popup.dismiss()
            if not self.video_vault.open_video_externally(video_path):
                error_popup = Popup(
                    title='❌ Error',
                    content=Label(text='Could not open video with external player\n\nTry installing a video player like VLC'),
                    size_hint=(0.7, 0.4),
                    auto_dismiss=True
                )
                error_popup.open()
                Clock.schedule_once(lambda dt: error_popup.dismiss(), 3)
        
        def export_video(instance):
            popup.dismiss()
            self.export_selected_video(None)
        
        def delete_video(instance):
            popup.dismiss()
            self.enhanced_delete_video(video_path)
        
        play_btn.bind(on_press=play_external)
        export_btn.bind(on_press=export_video)
        delete_btn.bind(on_press=delete_video)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def enhanced_delete_video(self, video_path):
        """Enhanced delete with recycle bin - UPDATED VERSION"""
        content = BoxLayout(orientation='vertical', spacing=15, padding=15)
        
        # Get retention days from recycle bin config
        retention_days = 7  # Default for videos
        if hasattr(self.video_vault.app, 'recycle_bin'):
            retention_days = self.video_vault.app.recycle_bin.FILE_TYPE_CONFIG['videos']['retention_days']
        
        # NEW: Updated warning message for recycle bin
        warning_text = f"""🗑️ MOVE TO RECYCLE BIN

    File: {os.path.basename(video_path)}

    This will move the video to the recycle bin where:
    ♻️ It will be stored safely for {retention_days} days
    🔄 You can restore it anytime from the recycle bin
    🕒 It will be automatically deleted after {retention_days} days
    🛡️ This is much safer than permanent deletion!

    The video file and its thumbnail will be moved together.

    Continue?"""
        
        label = Label(
            text=warning_text,
            halign='center',
            font_size=14,
            color=(0.2, 0.8, 0.2, 1)  # Green instead of red warning
        )
        label.bind(size=label.setter('text_size'))
        content.add_widget(label)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=10)
        
        # NEW: Updated button colors and text
        delete_btn = Button(
            text='🗑️ YES, MOVE TO RECYCLE BIN',
            background_color=(0.2, 0.7, 0.2, 1),  # Green instead of red
            font_size=16
        )
        
        cancel_btn = Button(
            text='❌ CANCEL',
            background_color=(0.5, 0.5, 0.5, 1),  # Gray
            font_size=16
        )
        
        btn_layout.add_widget(delete_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title='🗑️ Move to Recycle Bin',  # Updated title
            content=content,
            size_hint=(0.85, 0.8),  # Made slightly larger for new text
            auto_dismiss=False
        )
        
        def delete_confirmed(instance):
            popup.dismiss()
            
            # NEW: Updated progress popup
            progress_content = Label(
                text='🗑️ Moving video to recycle bin...\n\nThis is much faster and safer than permanent deletion!\n\nPlease wait...',
                halign='center',
                font_size=16
            )
            
            progress_popup = Popup(
                title='Moving to Recycle Bin',  # Updated title
                content=progress_content,
                size_hint=(0.7, 0.4),
                auto_dismiss=False
            )
            progress_popup.open()
            
            def do_deletion():
                # Use the updated delete function (now moves to recycle bin)
                success = self.video_vault.delete_video(video_path)
                Clock.schedule_once(lambda dt: finish_deletion(success), 0)
            
            def finish_deletion(success):
                progress_popup.dismiss()
                
                if success:
                    self.selected_video = None
                    self.refresh_gallery(None)
                    
                    # NEW: Updated success message
                    success_popup = Popup(
                        title='✅ Moved to Recycle Bin',
                        content=Label(
                            text=f'Video moved to recycle bin successfully!\n\n♻️ You can restore it anytime from the vault menu\n🕒 It will be kept for {retention_days} days\n🗑️ Check the recycle bin to manage deleted files',
                            halign='center'
                        ),
                        size_hint=(0.8, 0.6),
                        auto_dismiss=True
                    )
                    success_popup.open()
                    Clock.schedule_once(lambda dt: success_popup.dismiss(), 4)
                else:
                    error_popup = Popup(
                        title='❌ Error',
                        content=Label(
                            text='Could not move video to recycle bin.\nFile may be in use by another program.\n\nTry closing video players and try again.\n\nNote: If this keeps failing, the app will attempt permanent deletion as a last resort.',
                            halign='center'
                        ),
                        size_hint=(0.8, 0.7),
                        auto_dismiss=True
                    )
                    error_popup.open()
                    Clock.schedule_once(lambda dt: error_popup.dismiss(), 5)
            
            # Start deletion in background
            import threading
            thread = threading.Thread(target=do_deletion)
            thread.daemon = True
            thread.start()
        
        delete_btn.bind(on_press=delete_confirmed)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    # Legacy methods for backwards compatibility
    def select_video(self, video_path):
        """Legacy method - redirects to fixed version"""
        return self.select_video_fixed(video_path)
    
    def create_video_widget(self, video_path):
        """Legacy method - redirects to fixed version"""
        return self.create_video_widget_fixed(video_path)
    
    def confirm_delete_video(self, video_path):
        """Legacy method - redirects to enhanced version"""
        return self.enhanced_delete_video(video_path)
    
    def delete_selected(self, instance):
        """Delete the selected video - KEPT for backwards compatibility"""
        if not self.selected_video:
            content = Label(text='Please select a video first by tapping on it')
            popup = Popup(
                title='No Video Selected',
                content=content,
                size_hint=(0.7, 0.3),
                auto_dismiss=True
            )
            popup.open()
            Clock.schedule_once(lambda dt: popup.dismiss(), 2)
            return
        
        self.enhanced_delete_video(self.selected_video)
    
    def back_to_vault(self, instance):
        """Go back to main vault screen"""
        print("Going back to main vault screen...")
        
        # Clean up before leaving
        self.video_vault.cleanup_video_players()
        self.video_vault.cleanup_all_cv2_captures()
        self.cleanup_video_widgets()
        
        # Navigate back
        if hasattr(self.video_vault.app, 'show_vault_main'):
            self.video_vault.app.show_vault_main()

    def export_selected_video(self, instance):
        """Export the selected video with folder selection"""
        if not self.selected_video:
            self.show_no_selection_message("export")
            return
        
        # Get original filename for display
        vault_filename = os.path.basename(self.selected_video)
        match = re.match(r'vault_\d{8}_\d{6}_\d+_(.+)', vault_filename)
        if match:
            original_name = match.group(1)
        else:
            original_name = vault_filename
        
        # Show initial export dialog
        content = BoxLayout(orientation='vertical', spacing=10)
        
        info_label = Label(
            text=f"Export '{original_name}' to device storage?\n\nYou will be asked to choose the destination folder."
        )
        content.add_widget(info_label)
        
        button_layout = BoxLayout(orientation='horizontal')
        
        choose_btn = Button(text='📁 Choose Folder & Export')
        cancel_btn = Button(text='❌ Cancel')
        
        button_layout.add_widget(choose_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title='Export Video',
            content=content,
            size_hint=(0.8, 0.5),
            auto_dismiss=False
        )
        
        def start_export(instance):
            popup.dismiss()
            self.choose_folder_and_export()
        
        choose_btn.bind(on_press=start_export)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()

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
                    
                    self.show_export_result(success_text, "Export Successful", True)
                else:
                    self.handle_export_error(export_result)
            else:
                # Folder selection failed
                error_text = f"❌ Folder selection failed!\n\nError: {result['error']}\n\nPlease try again."
                self.show_export_result(error_text, "Folder Selection Failed", False, retry_video=self.selected_video)
        
        # Start folder selection
        self.video_vault.select_export_folder(on_folder_selected)

    def handle_export_error(self, export_result):
        """Handle export errors with retry option"""
        if export_result.get('needs_folder_selection'):
            error_text = f"❌ Export failed!\n\nError: {export_result['error']}\n\nWould you like to try with a different folder?"
            self.show_export_result(error_text, "Export Failed", False, retry_video=self.selected_video)
        else:
            error_text = f"❌ Export failed!\n\nError: {export_result['error']}"
            self.show_export_result(error_text, "Export Failed", False, None)

    def show_export_result(self, message, title, is_success, retry_video=None):
        """Show export result with optional retry"""
        content = BoxLayout(orientation='vertical', spacing=10)
        
        result_label = Label(text=message)
        content.add_widget(result_label)
        
        button_layout = BoxLayout(orientation='horizontal')
        
        if retry_video and not is_success:
            # Add retry button for failures
            retry_btn = Button(text='🔄 Try Different Folder')
            button_layout.add_widget(retry_btn)
            
            def retry_export(instance):
                popup.dismiss()
                self.selected_video = retry_video
                self.choose_folder_and_export()
            
            retry_btn.bind(on_press=retry_export)
        
        ok_btn = Button(text='OK')
        button_layout.add_widget(ok_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.6),
            auto_dismiss=False
        )
        
        ok_btn.bind(on_press=popup.dismiss)
        popup.open()
        
        # Auto-dismiss success messages after 5 seconds
        if is_success:
            Clock.schedule_once(lambda dt: popup.dismiss(), 5)

    def show_no_selection_message(self, action):
        """Show message when no video is selected"""
        content = Label(text=f'Please select a video first by tapping on any video')
        popup = Popup(
            title=f'No Video Selected',
            content=content,
            size_hint=(0.7, 0.3),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)

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

print("✅ Video Vault UI module loaded successfully (FIXED VERSION)")