import os
import threading
from datetime import datetime
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp

def show_file_options_dialog(file_info, recycle_bin_core, refresh_callback):
    """Show detailed options for a specific file"""
    content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
    
    # File details
    file_type = file_info['file_type']
    icon = recycle_bin_core.FILE_TYPE_CONFIG[file_type]['icon']
    type_name = recycle_bin_core.FILE_TYPE_CONFIG[file_type]['display_name']
    
    details_text = f"""{icon} {file_info['display_name']}

📁 Type: {type_name}
📊 Size: {file_info['size'] / (1024 * 1024):.1f} MB
🕒 Deleted: {datetime.fromisoformat(file_info['deleted_at']).strftime("%Y-%m-%d %H:%M")}
⏰ Days Remaining: {file_info['days_remaining']}
📍 Original Location: {file_info['original_location']}"""
    
    details_label = MDLabel(
        text=details_text,
        font_style="Body1",
        text_color="white",
        halign='left'
    )
    details_label.bind(size=details_label.setter('text_size'))
    content.add_widget(details_label)
    
    # Action buttons
    button_layout = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=dp(140))
    
    # First row
    row1 = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=10)
    
    restore_btn = MDRaisedButton(
        text='♻️ Restore File',
        md_bg_color=[0.2, 0.7, 0.2, 1],
        text_color="white",
        elevation=3
    )
    
    delete_btn = MDRaisedButton(
        text='💀 Delete Forever',
        md_bg_color=[0.8, 0.2, 0.2, 1],
        text_color="white",
        elevation=3
    )
    
    row1.add_widget(restore_btn)
    row1.add_widget(delete_btn)
    button_layout.add_widget(row1)
    
    # Second row
    cancel_btn = MDRaisedButton(
        text='❌ Cancel',
        md_bg_color=[0.5, 0.5, 0.5, 1],
        text_color="white",
        size_hint_y=None,
        height=dp(50),
        elevation=2
    )
    button_layout.add_widget(cancel_btn)
    
    content.add_widget(button_layout)
    
    popup = Popup(
        title=f'{icon} File Options',
        content=content,
        size_hint=(0.9, 0.8),
        auto_dismiss=False
    )
    
    def restore_file(instance):
        popup.dismiss()
        restore_file_with_progress(file_info, recycle_bin_core, refresh_callback)
    
    def delete_file(instance):
        popup.dismiss()
        confirm_permanent_delete(file_info, recycle_bin_core, refresh_callback)
    
    restore_btn.bind(on_press=restore_file)
    delete_btn.bind(on_press=delete_file)
    cancel_btn.bind(on_press=popup.dismiss)
    
    popup.open()

def restore_file_with_progress(file_info, recycle_bin_core, refresh_callback):
    """Restore file with progress indication"""
    # Show progress popup
    progress_content = MDLabel(
        text=f'♻️ Restoring file...\n{file_info["display_name"]}\n\nPlease wait...',
        halign='center',
        font_style="Body1",
        text_color="white"
    )
    
    progress_popup = Popup(
        title='Restoring File',
        content=progress_content,
        size_hint=(0.7, 0.4),
        auto_dismiss=False
    )
    progress_popup.open()
    
    def do_restore():
        result = recycle_bin_core.restore_from_recycle(file_info['recycled_id'])
        Clock.schedule_once(lambda dt: finish_restore(result), 0)
    
    def finish_restore(result):
        progress_popup.dismiss()
        
        if result['success']:
            refresh_callback()
            
            success_popup = Popup(
                title='✅ File Restored',
                content=MDLabel(
                    text=f'File restored successfully to:\n{result["restored_path"]}',
                    text_color="white",
                    halign='center'
                ),
                size_hint=(0.8, 0.4),
                auto_dismiss=True
            )
            success_popup.open()
            Clock.schedule_once(lambda dt: success_popup.dismiss(), 3)
        else:
            error_popup = Popup(
                title='❌ Restore Failed',
                content=MDLabel(
                    text=f'Could not restore file:\n{result["error"]}',
                    text_color="white",
                    halign='center'
                ),
                size_hint=(0.8, 0.4),
                auto_dismiss=True
            )
            error_popup.open()
            Clock.schedule_once(lambda dt: error_popup.dismiss(), 4)
    
    # Start restoration in background
    thread = threading.Thread(target=do_restore)
    thread.daemon = True
    thread.start()

def confirm_permanent_delete(file_info, recycle_bin_core, refresh_callback):
    """Confirm permanent deletion of a file"""
    content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
    
    warning_text = f"""⚠️ PERMANENT DELETION WARNING ⚠️

File: {file_info['display_name']}
Type: {recycle_bin_core.FILE_TYPE_CONFIG[file_info['file_type']]['display_name']}
Size: {file_info['size'] / (1024 * 1024):.1f} MB

This will PERMANENTLY delete the file.
This action CANNOT be undone!

Are you absolutely sure?"""
    
    warning_label = MDLabel(
        text=warning_text,
        halign='center',
        font_style="Body1",
        text_color=[1, 0.8, 0, 1]  # Yellow warning
    )
    warning_label.bind(size=warning_label.setter('text_size'))
    content.add_widget(warning_label)
    
    button_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=10)
    
    delete_btn = MDRaisedButton(
        text='💀 YES, DELETE FOREVER',
        md_bg_color=[0.9, 0, 0, 1],
        text_color="white",
        elevation=3
    )
    
    cancel_btn = MDRaisedButton(
        text='❌ CANCEL',
        md_bg_color=[0.5, 0.5, 0.5, 1],
        text_color="white",
        elevation=2
    )
    
    button_layout.add_widget(delete_btn)
    button_layout.add_widget(cancel_btn)
    content.add_widget(button_layout)
    
    popup = Popup(
        title='💀 Confirm Permanent Deletion',
        content=content,
        size_hint=(0.8, 0.7),
        auto_dismiss=False
    )
    
    def delete_confirmed(instance):
        popup.dismiss()
        delete_file_permanently(file_info, recycle_bin_core, refresh_callback)
    
    delete_btn.bind(on_press=delete_confirmed)
    cancel_btn.bind(on_press=popup.dismiss)
    
    popup.open()

def delete_file_permanently(file_info, recycle_bin_core, refresh_callback):
    """Permanently delete a file"""
    # Show progress popup
    progress_content = MDLabel(
        text=f'💀 Permanently deleting...\n{file_info["display_name"]}\n\nPlease wait...',
        halign='center',
        font_style="Body1",
        text_color="white"
    )
    
    progress_popup = Popup(
        title='Deleting File',
        content=progress_content,
        size_hint=(0.7, 0.4),
        auto_dismiss=False
    )
    progress_popup.open()
    
    def do_delete():
        result = recycle_bin_core.delete_permanently(file_info['recycled_id'])
        Clock.schedule_once(lambda dt: finish_delete(result), 0)
    
    def finish_delete(result):
        progress_popup.dismiss()
        
        if result['success']:
            refresh_callback()
            
            success_popup = Popup(
                title='✅ File Deleted',
                content=MDLabel(
                    text='File permanently deleted successfully!',
                    text_color="white",
                    halign='center'
                ),
                size_hint=(0.6, 0.3),
                auto_dismiss=True
            )
            success_popup.open()
            Clock.schedule_once(lambda dt: success_popup.dismiss(), 2)
        else:
            error_popup = Popup(
                title='❌ Delete Failed',
                content=MDLabel(
                    text=f'Could not delete file:\n{result["error"]}',
                    text_color="white",
                    halign='center'
                ),
                size_hint=(0.8, 0.4),
                auto_dismiss=True
            )
            error_popup.open()
            Clock.schedule_once(lambda dt: error_popup.dismiss(), 4)
    
    # Start deletion in background
    thread = threading.Thread(target=do_delete)
    thread.daemon = True
    thread.start()

def manual_cleanup_dialog(recycle_bin_core, refresh_callback):
    """Manually trigger cleanup of expired files"""
    # Show progress popup
    progress_content = MDLabel(
        text='🧹 Cleaning up expired files...\n\nPlease wait...',
        halign='center',
        font_style="Body1",
        text_color="white"
    )
    
    progress_popup = Popup(
        title='Cleanup in Progress',
        content=progress_content,
        size_hint=(0.6, 0.3),
        auto_dismiss=False
    )
    progress_popup.open()
    
    def do_cleanup():
        expired_count = recycle_bin_core.cleanup_expired_files()
        Clock.schedule_once(lambda dt: finish_cleanup(expired_count), 0)
    
    def finish_cleanup(expired_count):
        progress_popup.dismiss()
        refresh_callback()
        
        if expired_count > 0:
            message = f'Cleanup completed!\n{expired_count} expired files were deleted.'
        else:
            message = 'Cleanup completed!\nNo expired files found.'
        
        cleanup_popup = Popup(
            title='🧹 Cleanup Complete',
            content=MDLabel(
                text=message,
                text_color="white",
                halign='center'
            ),
            size_hint=(0.7, 0.4),
            auto_dismiss=True
        )
        cleanup_popup.open()
        Clock.schedule_once(lambda dt: cleanup_popup.dismiss(), 3)
    
    # Start cleanup in background
    thread = threading.Thread(target=do_cleanup)
    thread.daemon = True
    thread.start()

def confirm_empty_all_dialog(recycle_bin_core, refresh_callback):
    """Confirm emptying entire recycle bin"""
    content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
    
    stats = recycle_bin_core.get_recycle_bin_stats()
    
    warning_text = f"""🔥 EMPTY RECYCLE BIN WARNING 🔥

This will PERMANENTLY DELETE ALL files in the recycle bin:

📊 Total Files: {stats['total_files']}
💾 Total Size: {stats['total_size_mb']} MB

This action CANNOT be undone!
All files will be lost forever!

Are you absolutely sure?"""
    
    warning_label = MDLabel(
        text=warning_text,
        halign='center',
        font_style="Body1",
        text_color=[1, 0.2, 0.2, 1]  # Red warning
    )
    warning_label.bind(size=warning_label.setter('text_size'))
    content.add_widget(warning_label)
    
    button_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=10)
    
    empty_btn = MDRaisedButton(
        text='🔥 YES, EMPTY RECYCLE BIN',
        md_bg_color=[0.9, 0, 0, 1],
        text_color="white",
        elevation=3
    )
    
    cancel_btn = MDRaisedButton(
        text='❌ CANCEL',
        md_bg_color=[0.5, 0.5, 0.5, 1],
        text_color="white",
        elevation=2
    )
    
    button_layout.add_widget(empty_btn)
    button_layout.add_widget(cancel_btn)
    content.add_widget(button_layout)
    
    popup = Popup(
        title='🔥 Empty Recycle Bin',
        content=content,
        size_hint=(0.85, 0.8),
        auto_dismiss=False
    )
    
    def empty_confirmed(instance):
        popup.dismiss()
        empty_recycle_bin_with_progress(recycle_bin_core, refresh_callback)
    
    empty_btn.bind(on_press=empty_confirmed)
    cancel_btn.bind(on_press=popup.dismiss)
    
    popup.open()

def empty_recycle_bin_with_progress(recycle_bin_core, refresh_callback):
    """Empty the entire recycle bin"""
    # Show progress popup
    progress_content = MDLabel(
        text='🔥 Emptying recycle bin...\n\nThis may take a moment...',
        halign='center',
        font_style="Body1",
        text_color="white"
    )
    
    progress_popup = Popup(
        title='Emptying Recycle Bin',
        content=progress_content,
        size_hint=(0.7, 0.4),
        auto_dismiss=False
    )
    progress_popup.open()
    
    def do_empty():
        result = recycle_bin_core.empty_recycle_bin()
        Clock.schedule_once(lambda dt: finish_empty(result), 0)
    
    def finish_empty(result):
        progress_popup.dismiss()
        refresh_callback()
        
        if result['success']:
            message = f'Recycle bin emptied successfully!\n{result["deleted_count"]} files were permanently deleted.'
            title = '✅ Recycle Bin Emptied'
        else:
            message = f'Error emptying recycle bin:\n{result["error"]}\n\n{result["deleted_count"]} files were deleted.'
            title = '❌ Empty Failed'
        
        result_popup = Popup(
            title=title,
            content=MDLabel(
                text=message,
                text_color="white",
                halign='center'
            ),
            size_hint=(0.8, 0.5),
            auto_dismiss=True
        )
        result_popup.open()
        Clock.schedule_once(lambda dt: result_popup.dismiss(), 4)
    
    # Start emptying in background
    thread = threading.Thread(target=do_empty)
    thread.daemon = True
    thread.start()

def show_no_selection_popup(action):
    """Show popup when no file is selected"""
    popup = Popup(
        title='No File Selected',
        content=MDLabel(
            text=f'Please select a file first by tapping "Select" to {action} it.',
            text_color="white",
            halign='center'
        ),
        size_hint=(0.7, 0.3),
        auto_dismiss=True
    )
    popup.open()
    Clock.schedule_once(lambda dt: popup.dismiss(), 2)