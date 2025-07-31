import os
import re
import threading
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.clock import Clock
from kivy.metrics import dp

# SIMPLIFIED: Desktop-only platform detection
ANDROID = False  # Always False for desktop-only version

def show_import_results_dialog(imported_files, moved_files):
    """Show import results popup with BlueGray theme"""
    content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
    
    if imported_files:
        count = len(imported_files)
        action = "moved" if moved_files else "copied"
        success_text = f'✅ Successfully {action} {count} video(s) to vault!'
        
        success_label = MDLabel(
            text=success_text,
            halign='center',
            text_color=[0.4, 0.8, 0.4, 1],  # Green
            font_style="Body1"
        )
        content.add_widget(success_label)
    else:
        no_files_label = MDLabel(
            text="No videos were selected or imported.",
            text_color=[0.7, 0.7, 0.7, 1],
            halign='center'
        )
        content.add_widget(no_files_label)
    
    # Close button
    close_btn = MDRaisedButton(
        text='OK',
        size_hint_y=None,
        height=dp(50),
        md_bg_color=[0.46, 0.53, 0.6, 1],
        text_color="white",
        elevation=2
    )
    content.add_widget(close_btn)
    
    popup = Popup(
        title='Videos Added',
        content=content,
        size_hint=(0.7, 0.4),
        auto_dismiss=False
    )
    
    close_btn.bind(on_press=popup.dismiss)
    popup.open()
    
    if imported_files:
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)

def show_file_movement_confirmation(file_paths, callback):
    """Confirm that user wants to move files (not copy)"""
    content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
    
    warning_text = f"""⚠️ IMPORTANT SECURITY NOTICE ⚠️

{len(file_paths)} video(s) will be MOVED to secure vault.

This means:
• Files will DISAPPEAR from current location
• Files will only exist in the secure vault
• This is more secure than copying

Continue?"""
    
    label = MDLabel(
        text=warning_text,
        text_color=[1, 0.8, 0, 1],  # Orange warning
        halign='center',
        font_style="Body1"
    )
    label.bind(size=label.setter('text_size'))
    content.add_widget(label)
    
    btn_layout = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(120), spacing=10)
    
    # First row
    row1 = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=10)
    
    move_btn = MDRaisedButton(
        text='✅ Yes, Move to Vault',
        md_bg_color=[0.2, 0.7, 0.2, 1],
        text_color="white",
        elevation=3
    )
    
    copy_btn = MDRaisedButton(
        text='📋 Copy Instead (Less Secure)',
        md_bg_color=[0.8, 0.6, 0.2, 1],
        text_color="white",
        elevation=3
    )
    
    row1.add_widget(move_btn)
    row1.add_widget(copy_btn)
    btn_layout.add_widget(row1)
    
    # Second row
    cancel_btn = MDRaisedButton(
        text='❌ Cancel',
        md_bg_color=[0.5, 0.5, 0.5, 1],
        text_color="white",
        size_hint_y=None,
        height=dp(50),
        elevation=2
    )
    btn_layout.add_widget(cancel_btn)
    
    content.add_widget(btn_layout)
    
    popup = Popup(
        title='Move Files to Vault?',
        content=content,
        size_hint=(0.8, 0.7),
        auto_dismiss=False
    )
    
    def move_files(instance):
        popup.dismiss()
        callback(file_paths, move_files=True)
    
    def copy_files(instance):
        popup.dismiss()
        callback(file_paths, move_files=False)
    
    def cancel_action(instance):
        popup.dismiss()
    
    move_btn.bind(on_press=move_files)
    copy_btn.bind(on_press=copy_files)
    cancel_btn.bind(on_press=cancel_action)
    
    popup.open()

def show_fallback_file_picker(callback):
    """Fallback file picker using Kivy's FileChooser - Desktop optimized"""
    content = MDBoxLayout(orientation='vertical', spacing=10, padding=10)
    
    # SIMPLIFIED: Desktop-only start path
    start_path = os.path.expanduser('~')  # User home directory
    
    filechooser = FileChooserIconView(
        path=start_path,
        filters=['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.webm', '*.3gp', '*.ogg', '*.ogv'],
        multiselect=True
    )
    content.add_widget(filechooser)
    
    # Buttons
    button_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=10)
    
    select_btn = MDRaisedButton(
        text='Select Videos',
        md_bg_color=[0.2, 0.6, 0.8, 1],
        text_color="white",
        size_hint_x=0.5,
        elevation=3
    )
    
    cancel_btn = MDRaisedButton(
        text='Cancel',
        md_bg_color=[0.5, 0.5, 0.5, 1],
        text_color="white",
        size_hint_x=0.5,
        elevation=2
    )
    
    button_layout.add_widget(select_btn)
    button_layout.add_widget(cancel_btn)
    content.add_widget(button_layout)
    
    popup = Popup(
        title='Select Videos from Computer',  # UPDATED: More desktop-appropriate
        content=content,
        size_hint=(0.9, 0.9),
        auto_dismiss=False
    )
    
    def on_select(instance):
        if filechooser.selection:
            popup.dismiss()
            callback(filechooser.selection)
        else:
            popup.dismiss()
    
    def on_cancel(instance):
        popup.dismiss()
    
    select_btn.bind(on_press=on_select)
    cancel_btn.bind(on_press=on_cancel)
    
    popup.open()

def show_video_options_dialog(video_path, video_vault, refresh_callback, export_callback, delete_callback):
    """Show detailed options for a specific video"""
    content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
    
    # Video info
    filename = os.path.basename(video_path)
    video_info = video_vault.get_video_info_safe(video_path)
    
    info_text = f"""📁 File: {filename}
📊 Size: {video_info['size']}
⏱️ Duration: {video_info['duration']}
📍 Location: {video_path}"""
    
    info_label = MDLabel(
        text=info_text,
        halign='left',
        font_style="Body1",
        text_color="white"
    )
    info_label.bind(size=info_label.setter('text_size'))
    content.add_widget(info_label)
    
    # Action buttons
    btn_layout = MDBoxLayout(orientation='vertical', spacing=12, size_hint_y=None, height=dp(180))
    
    # First row - Play and Export
    row1 = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=10)
    
    play_btn = MDRaisedButton(
        text='▶️ Play Video',
        md_bg_color=[0.2, 0.7, 0.2, 1],  # Green
        text_color="white",
        elevation=3
    )
    
    export_btn = MDRaisedButton(
        text='📤 Export Video',
        md_bg_color=[0.2, 0.4, 0.8, 1],  # Blue
        text_color="white",
        elevation=3
    )
    
    row1.add_widget(play_btn)
    row1.add_widget(export_btn)
    btn_layout.add_widget(row1)
    
    # Second row - Delete
    delete_btn = MDRaisedButton(
        text='🗑️ Move to Recycle Bin',
        md_bg_color=[0.8, 0.6, 0.2, 1],  # Orange
        text_color="white",
        size_hint_y=None,
        height=dp(50),
        elevation=3
    )
    btn_layout.add_widget(delete_btn)
    
    # Third row - Cancel
    cancel_btn = MDRaisedButton(
        text='❌ Cancel',
        size_hint_y=None,
        height=dp(50),
        md_bg_color=[0.5, 0.5, 0.5, 1],  # Gray
        text_color="white",
        elevation=2
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
        if not video_vault.open_video_externally(video_path):
            show_error_popup('Could not open video with external player\n\nTry installing a video player like VLC')
    
    def export_video(instance):
        popup.dismiss()
        export_callback()
    
    def delete_video(instance):
        popup.dismiss()
        delete_callback(video_path)
    
    play_btn.bind(on_press=play_external)
    export_btn.bind(on_press=export_video)
    delete_btn.bind(on_press=delete_video)
    cancel_btn.bind(on_press=popup.dismiss)
    
    popup.open()

def show_delete_confirmation_dialog(video_path, video_vault, refresh_callback):
    """Enhanced delete with recycle bin confirmation"""
    content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
    
    # Get retention days from recycle bin config
    retention_days = 7  # Default for videos
    if hasattr(video_vault.app, 'recycle_bin'):
        retention_days = video_vault.app.recycle_bin.FILE_TYPE_CONFIG['videos']['retention_days']
    
    warning_text = f"""🗑️ MOVE TO RECYCLE BIN

File: {os.path.basename(video_path)}

This will move the video to the recycle bin where:
♻️ It will be stored safely for {retention_days} days
🔄 You can restore it anytime from the recycle bin
🕒 It will be automatically deleted after {retention_days} days
🛡️ This is much safer than permanent deletion!

The video file and its thumbnail will be moved together.

Continue?"""
    
    label = MDLabel(
        text=warning_text,
        halign='center',
        font_style="Body1",
        text_color=[0.4, 0.8, 0.4, 1]  # Green instead of red warning
    )
    label.bind(size=label.setter('text_size'))
    content.add_widget(label)
    
    btn_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=10)
    
    delete_btn = MDRaisedButton(
        text='🗑️ YES, MOVE TO RECYCLE BIN',
        md_bg_color=[0.2, 0.7, 0.2, 1],  # Green instead of red
        text_color="white",
        elevation=3
    )
    
    cancel_btn = MDRaisedButton(
        text='❌ CANCEL',
        md_bg_color=[0.5, 0.5, 0.5, 1],  # Gray
        text_color="white",
        elevation=2
    )
    
    btn_layout.add_widget(delete_btn)
    btn_layout.add_widget(cancel_btn)
    content.add_widget(btn_layout)
    
    popup = Popup(
        title='🗑️ Move to Recycle Bin',
        content=content,
        size_hint=(0.85, 0.8),
        auto_dismiss=False
    )
    
    def delete_confirmed(instance):
        popup.dismiss()
        
        # Show progress popup
        progress_content = MDLabel(
            text='🗑️ Moving video to recycle bin...\n\nThis is much faster and safer than permanent deletion!\n\nPlease wait...',
            halign='center',
            font_style="Body1",
            text_color="white"
        )
        
        progress_popup = Popup(
            title='Moving to Recycle Bin',
            content=progress_content,
            size_hint=(0.7, 0.4),
            auto_dismiss=False
        )
        progress_popup.open()
        
        def do_deletion():
            success = video_vault.delete_video(video_path)
            Clock.schedule_once(lambda dt: finish_deletion(success), 0)
        
        def finish_deletion(success):
            progress_popup.dismiss()
            
            if success:
                refresh_callback()
                
                success_popup = Popup(
                    title='✅ Moved to Recycle Bin',
                    content=MDLabel(
                        text=f'Video moved to recycle bin successfully!\n\n♻️ You can restore it anytime from the vault menu\n🕒 It will be kept for {retention_days} days\n🗑️ Check the recycle bin to manage deleted files',
                        halign='center',
                        text_color=[0.4, 0.8, 0.4, 1]
                    ),
                    size_hint=(0.8, 0.6),
                    auto_dismiss=True
                )
                success_popup.open()
                Clock.schedule_once(lambda dt: success_popup.dismiss(), 4)
            else:
                show_error_popup('Could not move video to recycle bin.\nFile may be in use by another program.\n\nTry closing video players and try again.\n\nNote: If this keeps failing, the app will attempt permanent deletion as a last resort.')
        
        # Start deletion in background
        thread = threading.Thread(target=do_deletion)
        thread.daemon = True
        thread.start()
    
    delete_btn.bind(on_press=delete_confirmed)
    cancel_btn.bind(on_press=popup.dismiss)
    
    popup.open()

def show_export_dialog(video_path, export_callback):
    """Show initial export dialog"""
    # Get original filename for display
    vault_filename = os.path.basename(video_path)
    match = re.match(r'vault_\d{8}_\d{6}_\d+_(.+)', vault_filename)
    if match:
        original_name = match.group(1)
    else:
        original_name = vault_filename
    
    content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
    
    info_label = MDLabel(
        text=f"Export '{original_name}' to your computer?\n\nYou will be asked to choose the destination folder.",
        text_color="white",
        halign='center',
        font_style="Body1"
    )
    content.add_widget(info_label)
    
    button_layout = MDBoxLayout(orientation='horizontal', spacing=10)
    
    choose_btn = MDRaisedButton(
        text='📁 Choose Folder & Export',
        md_bg_color=[0.6, 0.4, 0.8, 1],
        text_color="white",
        elevation=3
    )
    
    cancel_btn = MDRaisedButton(
        text='❌ Cancel',
        md_bg_color=[0.5, 0.5, 0.5, 1],
        text_color="white",
        elevation=2
    )
    
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
        export_callback()
    
    choose_btn.bind(on_press=start_export)
    cancel_btn.bind(on_press=popup.dismiss)
    
    popup.open()

def show_export_result_dialog(message, title, is_success, retry_callback=None):
    """Show export result with optional retry"""
    content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
    
    result_label = MDLabel(
        text=message,
        text_color=[0.4, 0.8, 0.4, 1] if is_success else [1, 0.6, 0.6, 1],
        halign='center',
        font_style="Body1"
    )
    content.add_widget(result_label)
    
    button_layout = MDBoxLayout(orientation='horizontal', spacing=10)
    
    if retry_callback and not is_success:
        # Add retry button for failures
        retry_btn = MDRaisedButton(
            text='🔄 Try Different Folder',
            md_bg_color=[0.6, 0.4, 0.8, 1],
            text_color="white",
            elevation=3
        )
        button_layout.add_widget(retry_btn)
        retry_btn.bind(on_press=lambda x: (popup.dismiss(), retry_callback()))
    
    ok_btn = MDRaisedButton(
        text='OK',
        md_bg_color=[0.46, 0.53, 0.6, 1],
        text_color="white",
        elevation=2
    )
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

def show_no_selection_popup(action):
    """Show popup when no video is selected"""
    popup = Popup(
        title='No Video Selected',
        content=MDLabel(
            text=f'Please select a video first by tapping on any video',
            text_color="white",
            halign='center'
        ),
        size_hint=(0.7, 0.3),
        auto_dismiss=True
    )
    popup.open()
    Clock.schedule_once(lambda dt: popup.dismiss(), 2)

def show_error_popup(message):
    """Show error popup with BlueGray theme"""
    popup = Popup(
        title='❌ Error',
        content=MDLabel(
            text=message,
            halign='center',
            text_color=[1, 0.4, 0.4, 1]  # Red error
        ),
        size_hint=(0.8, 0.5),
        auto_dismiss=True
    )
    popup.open()
    Clock.schedule_once(lambda dt: popup.dismiss(), 4)