import os
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.metrics import dp

from recycle_bin_core import RecycleBinCore

class RecycleBinWidget(BoxLayout):
    """
    Main Recycle Bin UI Widget - Flexible for all file types
    """
    
    def __init__(self, recycle_bin_core, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.recycle_bin = recycle_bin_core
        self.selected_file = None
        self.current_filter = 'all'  # Current file type filter
        
        # Create UI
        self.create_header()
        self.create_filter_section()
        self.create_stats_section()
        self.create_file_grid()
        self.create_bottom_buttons()
        
        # Load initial data
        Clock.schedule_once(lambda dt: self.refresh_recycle_bin(), 0.1)
    
    def create_header(self):
        """Create header with title and actions"""
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=10)
        
        title = Label(
            text='🗑️ Recycle Bin',
            font_size=24,
            size_hint_x=0.6
        )
        header.add_widget(title)
        
        # Quick actions
        actions_layout = BoxLayout(orientation='horizontal', size_hint_x=0.4, spacing=5)
        
        self.cleanup_btn = Button(
            text='🧹 Cleanup',
            font_size=14,
            size_hint_x=0.5
        )
        self.cleanup_btn.bind(on_press=self.manual_cleanup)
        actions_layout.add_widget(self.cleanup_btn)
        
        self.empty_btn = Button(
            text='🔥 Empty All',
            font_size=14,
            size_hint_x=0.5,
            background_color=(0.8, 0.2, 0.2, 1)  # Red warning color
        )
        self.empty_btn.bind(on_press=self.confirm_empty_all)
        actions_layout.add_widget(self.empty_btn)
        
        header.add_widget(actions_layout)
        self.add_widget(header)
    
    def create_filter_section(self):
        """Create file type filter section"""
        filter_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), padding=10)
        
        filter_label = Label(
            text='Filter:',
            size_hint_x=0.2,
            font_size=16
        )
        filter_layout.add_widget(filter_label)
        
        # Create filter options dynamically from FILE_TYPE_CONFIG
        filter_options = ['All Files']
        for file_type, config in self.recycle_bin.FILE_TYPE_CONFIG.items():
            display_name = f"{config['icon']} {config['display_name']}"
            filter_options.append(display_name)
        
        self.filter_spinner = Spinner(
            text='All Files',
            values=filter_options,
            size_hint_x=0.8,
            font_size=16
        )
        self.filter_spinner.bind(text=self.on_filter_changed)
        filter_layout.add_widget(self.filter_spinner)
        
        self.add_widget(filter_layout)
    
    def create_stats_section(self):
        """Create statistics section"""
        self.stats_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), padding=10)
        
        self.stats_label = Label(
            text='Loading statistics...',
            font_size=14,
            color=(0.7, 0.7, 0.7, 1)
        )
        self.stats_layout.add_widget(self.stats_label)
        
        self.add_widget(self.stats_layout)
    
    def create_file_grid(self):
        """Create scrollable file grid"""
        scroll = ScrollView()
        
        self.file_grid = GridLayout(
            cols=1,  # Single column for detailed view
            spacing=5,
            padding=10,
            size_hint_y=None
        )
        self.file_grid.bind(minimum_height=self.file_grid.setter('height'))
        
        scroll.add_widget(self.file_grid)
        self.add_widget(scroll)
    
    def create_bottom_buttons(self):
        """Create bottom action buttons"""
        bottom_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=10)
        
        self.refresh_btn = Button(
            text='🔄 Refresh',
            font_size=16,
            size_hint_x=0.25
        )
        self.refresh_btn.bind(on_press=self.refresh_recycle_bin)
        bottom_layout.add_widget(self.refresh_btn)
        
        self.restore_btn = Button(
            text='♻️ Restore Selected',
            font_size=16,
            size_hint_x=0.25,
            background_color=(0.2, 0.7, 0.2, 1)  # Green
        )
        self.restore_btn.bind(on_press=self.restore_selected)
        bottom_layout.add_widget(self.restore_btn)
        
        self.delete_btn = Button(
            text='💀 Delete Forever',
            font_size=16,
            size_hint_x=0.25,
            background_color=(0.8, 0.2, 0.2, 1)  # Red
        )
        self.delete_btn.bind(on_press=self.delete_selected_forever)
        bottom_layout.add_widget(self.delete_btn)
        
        self.back_btn = Button(
            text='🔙 Back to Vault',
            font_size=16,
            size_hint_x=0.25
        )
        self.back_btn.bind(on_press=self.back_to_vault)
        bottom_layout.add_widget(self.back_btn)
        
        self.add_widget(bottom_layout)
    
    def on_filter_changed(self, spinner, text):
        """Handle filter change"""
        if text == 'All Files':
            self.current_filter = 'all'
        else:
            # Extract file type from display text
            for file_type, config in self.recycle_bin.FILE_TYPE_CONFIG.items():
                display_name = f"{config['icon']} {config['display_name']}"
                if text == display_name:
                    self.current_filter = file_type
                    break
        
        self.refresh_file_grid()
    
    def refresh_recycle_bin(self, instance=None):
        """Refresh entire recycle bin view"""
        self.update_stats()
        self.refresh_file_grid()
    
    def update_stats(self):
        """Update statistics display"""
        try:
            stats = self.recycle_bin.get_recycle_bin_stats()
            
            # Create stats text
            stats_text = f"📊 Total: {stats['total_files']} files ({stats['total_size_mb']} MB)\n"
            
            # Add breakdown by type (only show non-zero counts)
            type_breakdown = []
            for file_type, type_stats in stats['by_type'].items():
                if type_stats['count'] > 0:
                    icon = type_stats['icon']
                    name = type_stats['display_name']
                    count = type_stats['count']
                    size = type_stats['size_mb']
                    type_breakdown.append(f"{icon} {name}: {count} ({size} MB)")
            
            if type_breakdown:
                stats_text += " | ".join(type_breakdown)
            else:
                stats_text += "🎉 Recycle bin is empty!"
            
            self.stats_label.text = stats_text
            
        except Exception as e:
            print(f"Error updating stats: {e}")
            self.stats_label.text = "❌ Error loading statistics"
    
    def refresh_file_grid(self):
        """Refresh the file grid based on current filter"""
        try:
            # Clear existing widgets
            self.file_grid.clear_widgets()
            self.selected_file = None
            
            # Get filtered files
            if self.current_filter == 'all':
                files = self.recycle_bin.get_recycled_files()
            else:
                files = self.recycle_bin.get_recycled_files(self.current_filter)
            
            if not files:
                # Show empty state
                empty_widget = self.create_empty_state_widget()
                self.file_grid.add_widget(empty_widget)
                return
            
            # Create file widgets
            for file_info in files:
                file_widget = self.create_file_widget(file_info)
                self.file_grid.add_widget(file_widget)
                
        except Exception as e:
            print(f"Error refreshing file grid: {e}")
            error_label = Label(
                text=f"❌ Error loading files: {str(e)}",
                size_hint_y=None,
                height=dp(50)
            )
            self.file_grid.add_widget(error_label)
    
    def create_empty_state_widget(self):
        """Create widget for empty recycle bin state"""
        empty_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(200),
            spacing=10,
            padding=20
        )
        
        filter_text = "this category" if self.current_filter != 'all' else "the recycle bin"
        
        empty_label = Label(
            text=f'🎉 No files in {filter_text}\n\nDeleted files will appear here and be\nautomatically cleaned up based on retention settings.',
            font_size=16,
            halign='center',
            color=(0.6, 0.6, 0.6, 1)
        )
        empty_label.bind(size=empty_label.setter('text_size'))
        empty_layout.add_widget(empty_label)
        
        return empty_layout
    
    def create_file_widget(self, file_info):
        """Create widget for individual recycled file"""
        # Main container
        file_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(80),
            padding=5,
            spacing=10
        )
        
        # File type icon and info
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.7)
        
        # Top row: Icon, name, size
        top_row = BoxLayout(orientation='horizontal', size_hint_y=0.6)
        
        file_type = file_info['file_type']
        icon = self.recycle_bin.FILE_TYPE_CONFIG[file_type]['icon']
        
        icon_label = Label(
            text=icon,
            font_size=24,
            size_hint_x=0.1
        )
        top_row.add_widget(icon_label)
        
        name_size_layout = BoxLayout(orientation='vertical', size_hint_x=0.9)
        
        # File name (truncated if too long)
        display_name = file_info['display_name']
        if len(display_name) > 40:
            display_name = display_name[:37] + "..."
        
        name_label = Label(
            text=display_name,
            font_size=14,
            halign='left',
            color=(1, 1, 1, 1)
        )
        name_label.bind(size=name_label.setter('text_size'))
        name_size_layout.add_widget(name_label)
        
        # Size and type info
        size_mb = file_info['size'] / (1024 * 1024)
        type_display = self.recycle_bin.FILE_TYPE_CONFIG[file_type]['display_name']
        
        size_label = Label(
            text=f"{size_mb:.1f} MB • {type_display}",
            font_size=12,
            halign='left',
            color=(0.7, 0.7, 0.7, 1)
        )
        size_label.bind(size=size_label.setter('text_size'))
        name_size_layout.add_widget(size_label)
        
        top_row.add_widget(name_size_layout)
        info_layout.add_widget(top_row)
        
        # Bottom row: Deletion date and days remaining
        bottom_row = BoxLayout(orientation='horizontal', size_hint_y=0.4)
        
        deleted_at = datetime.fromisoformat(file_info['deleted_at'])
        deleted_date = deleted_at.strftime("%Y-%m-%d %H:%M")
        days_remaining = file_info['days_remaining']
        
        if days_remaining > 0:
            remaining_text = f"🕒 Deleted: {deleted_date} • {days_remaining} days remaining"
            remaining_color = (0.7, 0.7, 0.7, 1)
        else:
            remaining_text = f"⚠️ Deleted: {deleted_date} • EXPIRES SOON!"
            remaining_color = (1, 0.6, 0, 1)  # Orange warning
        
        date_label = Label(
            text=remaining_text,
            font_size=11,
            halign='left',
            color=remaining_color
        )
        date_label.bind(size=date_label.setter('text_size'))
        bottom_row.add_widget(date_label)
        
        info_layout.add_widget(bottom_row)
        file_layout.add_widget(info_layout)
        
        # Action buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_x=0.3, spacing=5)
        
        select_btn = Button(
            text='📋\nSelect',
            font_size=12,
            size_hint_x=0.5
        )
        select_btn.bind(on_press=lambda x: self.select_file(file_info))
        button_layout.add_widget(select_btn)
        
        options_btn = Button(
            text='⚙️\nOptions',
            font_size=12,
            size_hint_x=0.5
        )
        options_btn.bind(on_press=lambda x: self.show_file_options(file_info))
        button_layout.add_widget(options_btn)
        
        file_layout.add_widget(button_layout)
        
        # Add selection indicator
        if self.selected_file and self.selected_file['recycled_id'] == file_info['recycled_id']:
            file_layout.canvas.before.clear()
            from kivy.graphics import Color, Rectangle
            with file_layout.canvas.before:
                Color(0.2, 0.6, 0.8, 0.3)  # Light blue highlight
                Rectangle(pos=file_layout.pos, size=file_layout.size)
        
        return file_layout
    
    def select_file(self, file_info):
        """Select a file and refresh to show selection"""
        self.selected_file = file_info
        print(f"Selected file: {file_info['display_name']}")
        # Don't refresh the entire grid - just print confirmation
        print(f"✅ File selected: {file_info['recycled_id']}")
    
    def show_file_options(self, file_info):
        """Show detailed options for a specific file"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        
        # File details
        file_type = file_info['file_type']
        icon = self.recycle_bin.FILE_TYPE_CONFIG[file_type]['icon']
        type_name = self.recycle_bin.FILE_TYPE_CONFIG[file_type]['display_name']
        
        details_text = f"""{icon} {file_info['display_name']}

📁 Type: {type_name}
📊 Size: {file_info['size'] / (1024 * 1024):.1f} MB
🕒 Deleted: {datetime.fromisoformat(file_info['deleted_at']).strftime("%Y-%m-%d %H:%M")}
⏰ Days Remaining: {file_info['days_remaining']}
📍 Original Location: {file_info['original_location']}"""
        
        details_label = Label(
            text=details_text,
            font_size=14,
            halign='left'
        )
        details_label.bind(size=details_label.setter('text_size'))
        content.add_widget(details_label)
        
        # Action buttons
        button_layout = BoxLayout(orientation='vertical', spacing=8, size_hint_y=None, height=dp(120))
        
        # First row
        row1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        
        restore_btn = Button(
            text='♻️ Restore File',
            background_color=(0.2, 0.7, 0.2, 1),
            font_size=16
        )
        
        delete_btn = Button(
            text='💀 Delete Forever',
            background_color=(0.8, 0.2, 0.2, 1),
            font_size=16
        )
        
        row1.add_widget(restore_btn)
        row1.add_widget(delete_btn)
        button_layout.add_widget(row1)
        
        # Second row
        cancel_btn = Button(
            text='❌ Cancel',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.5, 0.5, 0.5, 1)
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
            self.restore_file_with_progress(file_info)
        
        def delete_file(instance):
            popup.dismiss()
            self.confirm_permanent_delete(file_info)
        
        restore_btn.bind(on_press=restore_file)
        delete_btn.bind(on_press=delete_file)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def restore_selected(self, instance):
        """Restore the currently selected file"""
        if not self.selected_file:
            self.show_no_selection_popup("restore")
            return
        
        self.restore_file_with_progress(self.selected_file)
    
    def restore_file_with_progress(self, file_info):
        """Restore file with progress indication"""
        # Show progress popup
        progress_content = Label(
            text=f'♻️ Restoring file...\n{file_info["display_name"]}\n\nPlease wait...',
            halign='center',
            font_size=16
        )
        
        progress_popup = Popup(
            title='Restoring File',
            content=progress_content,
            size_hint=(0.7, 0.4),
            auto_dismiss=False
        )
        progress_popup.open()
        
        def do_restore():
            result = self.recycle_bin.restore_from_recycle(file_info['recycled_id'])
            Clock.schedule_once(lambda dt: finish_restore(result), 0)
        
        def finish_restore(result):
            progress_popup.dismiss()
            
            if result['success']:
                self.refresh_recycle_bin()
                
                success_popup = Popup(
                    title='✅ File Restored',
                    content=Label(text=f'File restored successfully to:\n{result["restored_path"]}'),
                    size_hint=(0.8, 0.4),
                    auto_dismiss=True
                )
                success_popup.open()
                Clock.schedule_once(lambda dt: success_popup.dismiss(), 3)
            else:
                error_popup = Popup(
                    title='❌ Restore Failed',
                    content=Label(text=f'Could not restore file:\n{result["error"]}'),
                    size_hint=(0.8, 0.4),
                    auto_dismiss=True
                )
                error_popup.open()
                Clock.schedule_once(lambda dt: error_popup.dismiss(), 4)
        
        # Start restoration in background
        import threading
        thread = threading.Thread(target=do_restore)
        thread.daemon = True
        thread.start()
    
    def delete_selected_forever(self, instance):
        """Delete selected file permanently"""
        if not self.selected_file:
            self.show_no_selection_popup("delete")
            return
        
        self.confirm_permanent_delete(self.selected_file)
    
    def confirm_permanent_delete(self, file_info):
        """Confirm permanent deletion of a file"""
        content = BoxLayout(orientation='vertical', spacing=15, padding=15)
        
        warning_text = f"""⚠️ PERMANENT DELETION WARNING ⚠️

File: {file_info['display_name']}
Type: {self.recycle_bin.FILE_TYPE_CONFIG[file_info['file_type']]['display_name']}
Size: {file_info['size'] / (1024 * 1024):.1f} MB

This will PERMANENTLY delete the file.
This action CANNOT be undone!

Are you absolutely sure?"""
        
        warning_label = Label(
            text=warning_text,
            halign='center',
            font_size=14,
            color=(1, 0.8, 0, 1)  # Yellow warning
        )
        warning_label.bind(size=warning_label.setter('text_size'))
        content.add_widget(warning_label)
        
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=10)
        
        delete_btn = Button(
            text='💀 YES, DELETE FOREVER',
            background_color=(0.9, 0, 0, 1),
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
            title='💀 Confirm Permanent Deletion',
            content=content,
            size_hint=(0.8, 0.7),
            auto_dismiss=False
        )
        
        def delete_confirmed(instance):
            popup.dismiss()
            self.delete_file_permanently(file_info)
        
        delete_btn.bind(on_press=delete_confirmed)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def delete_file_permanently(self, file_info):
        """Permanently delete a file"""
        # Show progress popup
        progress_content = Label(
            text=f'💀 Permanently deleting...\n{file_info["display_name"]}\n\nPlease wait...',
            halign='center',
            font_size=16
        )
        
        progress_popup = Popup(
            title='Deleting File',
            content=progress_content,
            size_hint=(0.7, 0.4),
            auto_dismiss=False
        )
        progress_popup.open()
        
        def do_delete():
            result = self.recycle_bin.delete_permanently(file_info['recycled_id'])
            Clock.schedule_once(lambda dt: finish_delete(result), 0)
        
        def finish_delete(result):
            progress_popup.dismiss()
            
            if result['success']:
                self.selected_file = None
                self.refresh_recycle_bin()
                
                success_popup = Popup(
                    title='✅ File Deleted',
                    content=Label(text='File permanently deleted successfully!'),
                    size_hint=(0.6, 0.3),
                    auto_dismiss=True
                )
                success_popup.open()
                Clock.schedule_once(lambda dt: success_popup.dismiss(), 2)
            else:
                error_popup = Popup(
                    title='❌ Delete Failed',
                    content=Label(text=f'Could not delete file:\n{result["error"]}'),
                    size_hint=(0.8, 0.4),
                    auto_dismiss=True
                )
                error_popup.open()
                Clock.schedule_once(lambda dt: error_popup.dismiss(), 4)
        
        # Start deletion in background
        import threading
        thread = threading.Thread(target=do_delete)
        thread.daemon = True
        thread.start()
    
    def manual_cleanup(self, instance):
        """Manually trigger cleanup of expired files"""
        # Show progress popup
        progress_content = Label(
            text='🧹 Cleaning up expired files...\n\nPlease wait...',
            halign='center',
            font_size=16
        )
        
        progress_popup = Popup(
            title='Cleanup in Progress',
            content=progress_content,
            size_hint=(0.6, 0.3),
            auto_dismiss=False
        )
        progress_popup.open()
        
        def do_cleanup():
            expired_count = self.recycle_bin.cleanup_expired_files()
            Clock.schedule_once(lambda dt: finish_cleanup(expired_count), 0)
        
        def finish_cleanup(expired_count):
            progress_popup.dismiss()
            self.refresh_recycle_bin()
            
            if expired_count > 0:
                message = f'Cleanup completed!\n{expired_count} expired files were deleted.'
            else:
                message = 'Cleanup completed!\nNo expired files found.'
            
            cleanup_popup = Popup(
                title='🧹 Cleanup Complete',
                content=Label(text=message),
                size_hint=(0.7, 0.4),
                auto_dismiss=True
            )
            cleanup_popup.open()
            Clock.schedule_once(lambda dt: cleanup_popup.dismiss(), 3)
        
        # Start cleanup in background
        import threading
        thread = threading.Thread(target=do_cleanup)
        thread.daemon = True
        thread.start()
    
    def confirm_empty_all(self, instance):
        """Confirm emptying entire recycle bin"""
        content = BoxLayout(orientation='vertical', spacing=15, padding=15)
        
        stats = self.recycle_bin.get_recycle_bin_stats()
        
        warning_text = f"""🔥 EMPTY RECYCLE BIN WARNING 🔥

This will PERMANENTLY DELETE ALL files in the recycle bin:

📊 Total Files: {stats['total_files']}
💾 Total Size: {stats['total_size_mb']} MB

This action CANNOT be undone!
All files will be lost forever!

Are you absolutely sure?"""
        
        warning_label = Label(
            text=warning_text,
            halign='center',
            font_size=14,
            color=(1, 0.2, 0.2, 1)  # Red warning
        )
        warning_label.bind(size=warning_label.setter('text_size'))
        content.add_widget(warning_label)
        
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=10)
        
        empty_btn = Button(
            text='🔥 YES, EMPTY RECYCLE BIN',
            background_color=(0.9, 0, 0, 1),
            font_size=16
        )
        
        cancel_btn = Button(
            text='❌ CANCEL',
            background_color=(0.5, 0.5, 0.5, 1),
            font_size=16
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
            self.empty_recycle_bin()
        
        empty_btn.bind(on_press=empty_confirmed)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def empty_recycle_bin(self):
        """Empty the entire recycle bin"""
        # Show progress popup
        progress_content = Label(
            text='🔥 Emptying recycle bin...\n\nThis may take a moment...',
            halign='center',
            font_size=16
        )
        
        progress_popup = Popup(
            title='Emptying Recycle Bin',
            content=progress_content,
            size_hint=(0.7, 0.4),
            auto_dismiss=False
        )
        progress_popup.open()
        
        def do_empty():
            result = self.recycle_bin.empty_recycle_bin()
            Clock.schedule_once(lambda dt: finish_empty(result), 0)
        
        def finish_empty(result):
            progress_popup.dismiss()
            self.selected_file = None
            self.refresh_recycle_bin()
            
            if result['success']:
                message = f'Recycle bin emptied successfully!\n{result["deleted_count"]} files were permanently deleted.'
                title = '✅ Recycle Bin Emptied'
            else:
                message = f'Error emptying recycle bin:\n{result["error"]}\n\n{result["deleted_count"]} files were deleted.'
                title = '❌ Empty Failed'
            
            result_popup = Popup(
                title=title,
                content=Label(text=message),
                size_hint=(0.8, 0.5),
                auto_dismiss=True
            )
            result_popup.open()
            Clock.schedule_once(lambda dt: result_popup.dismiss(), 4)
        
        # Start emptying in background
        import threading
        thread = threading.Thread(target=do_empty)
        thread.daemon = True
        thread.start()
    
    def show_no_selection_popup(self, action):
        """Show popup when no file is selected"""
        popup = Popup(
            title='No File Selected',
            content=Label(text=f'Please select a file first by tapping "Select" to {action} it.'),
            size_hint=(0.7, 0.3),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def back_to_vault(self, instance):
        """Go back to main vault screen"""
        print("Going back to main vault screen from recycle bin...")
        
        # Navigate back
        if hasattr(self.recycle_bin.app, 'show_vault_main'):
            self.recycle_bin.app.show_vault_main()

# Integration helper function
def integrate_recycle_bin(vault_app):
    """Helper function to integrate recycle bin into the main app"""
    # Initialize recycle bin core
    vault_app.recycle_bin = RecycleBinCore(vault_app)
    
    def show_recycle_bin():
        """Show the recycle bin interface"""
        print("Showing recycle bin...")
        vault_app.main_layout.clear_widgets()
        
        # Create recycle bin widget
        recycle_bin_widget = RecycleBinWidget(vault_app.recycle_bin)
        vault_app.main_layout.add_widget(recycle_bin_widget)
        
        # Store reference for navigation
        vault_app.current_screen = 'recycle_bin'
    
    # Add method to vault app
    vault_app.show_recycle_bin = show_recycle_bin
    
    return vault_app.recycle_bin

print("✅ Recycle Bin UI module loaded successfully")
print("🎯 Supports all file types with flexible filtering and management")
print("♻️ Complete restore and permanent deletion capabilities")