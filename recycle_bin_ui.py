import os
from datetime import datetime
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle

from recycle_bin_core import RecycleBinCore
from recycle_bin_dialogs import (
    show_file_options_dialog,
    restore_file_with_progress,
    confirm_permanent_delete,
    manual_cleanup_dialog,
    confirm_empty_all_dialog,
    show_no_selection_popup
)

class RecycleBinWidget(MDBoxLayout):
    """
    Main Recycle Bin UI Widget - Flexible for all file types with BlueGray theme
    """
    
    def __init__(self, recycle_bin_core, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.recycle_bin = recycle_bin_core
        self.selected_file = None
        self.current_filter = 'all'  # Current file type filter
        
        # Set BlueGray background
        self.md_bg_color = [0.37, 0.49, 0.55, 1]
        
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
        header = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(120),
            padding=[20, 20, 20, 10],
            spacing=10
        )
        
        # Large title
        title = MDLabel(
            text='RECYCLE BIN',
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
        
        self.cleanup_btn = MDRaisedButton(
            text='🧹 Cleanup',
            md_bg_color=[0.46, 0.53, 0.6, 1],
            text_color="white",
            size_hint_x=0.5,
            elevation=3
        )
        self.cleanup_btn.bind(on_press=self.manual_cleanup)
        actions_row.add_widget(self.cleanup_btn)
        
        self.empty_btn = MDRaisedButton(
            text='🔥 Empty All',
            md_bg_color=[0.8, 0.2, 0.2, 1],  # Red warning color
            text_color="white",
            size_hint_x=0.5,
            elevation=3
        )
        self.empty_btn.bind(on_press=self.confirm_empty_all)
        actions_row.add_widget(self.empty_btn)
        
        header.add_widget(actions_row)
        self.add_widget(header)
    
    def create_filter_section(self):
        """Create file type filter section"""
        filter_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            padding=[20, 10, 20, 10],
            spacing=15
        )
        
        filter_label = MDLabel(
            text='Filter:',
            size_hint_x=0.2,
            font_style="Subtitle1",
            text_color="white"
        )
        filter_container.add_widget(filter_label)
        
        # Create filter options dynamically from FILE_TYPE_CONFIG
        filter_options = ['All Files']
        for file_type, config in self.recycle_bin.FILE_TYPE_CONFIG.items():
            display_name = f"{config['icon']} {config['display_name']}"
            filter_options.append(display_name)
        
        self.filter_spinner = Spinner(
            text='All Files',
            values=filter_options,
            size_hint_x=0.8,
            font_size=16,
            background_color=[0.31, 0.35, 0.39, 1]  # BlueGray
        )
        self.filter_spinner.bind(text=self.on_filter_changed)
        filter_container.add_widget(self.filter_spinner)
        
        self.add_widget(filter_container)
    
    def create_stats_section(self):
        """Create statistics section"""
        self.stats_label = MDLabel(
            text='Loading recycle bin statistics...',
            font_style="Body2",
            text_color=[0.8, 0.8, 0.8, 1],
            halign="center",
            size_hint_y=None,
            height=dp(30)
        )
        self.add_widget(self.stats_label)
    
    def create_file_grid(self):
        """Create scrollable file grid"""
        scroll = MDScrollView(
            bar_width=dp(4),
            bar_color=[0.46, 0.53, 0.6, 0.7],
            bar_inactive_color=[0.7, 0.7, 0.7, 0.3],
            effect_cls="ScrollEffect"
        )
        
        self.file_grid = MDGridLayout(
            cols=1,  # Single column for detailed view
            spacing=15,
            padding=[20, 10, 20, 10],
            size_hint_y=None,
            adaptive_height=True
        )
        
        scroll.add_widget(self.file_grid)
        self.add_widget(scroll)
    
    def create_bottom_buttons(self):
        """Create bottom action buttons"""
        bottom_bar = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(70),
            padding=15,
            spacing=15,
            elevation=8,
            md_bg_color=[0.25, 0.29, 0.31, 1]  # BlueGray dark
        )
        
        self.refresh_btn = MDFlatButton(
            text='🔄 Refresh',
            text_color="white",
            size_hint_x=0.25
        )
        self.refresh_btn.bind(on_press=self.refresh_recycle_bin)
        bottom_bar.add_widget(self.refresh_btn)
        
        self.restore_btn = MDFlatButton(
            text='♻️ Restore',
            text_color=[0.4, 0.8, 0.4, 1],  # Green
            size_hint_x=0.25
        )
        self.restore_btn.bind(on_press=self.restore_selected)
        bottom_bar.add_widget(self.restore_btn)
        
        self.delete_btn = MDFlatButton(
            text='💀 Delete',
            text_color=[0.9, 0.4, 0.4, 1],  # Red
            size_hint_x=0.25
        )
        self.delete_btn.bind(on_press=self.delete_selected_forever)
        bottom_bar.add_widget(self.delete_btn)
        
        self.back_btn = MDFlatButton(
            text='← Back',
            text_color=[0.7, 0.7, 0.7, 1],
            size_hint_x=0.25
        )
        self.back_btn.bind(on_press=self.back_to_vault)
        bottom_bar.add_widget(self.back_btn)
        
        self.add_widget(bottom_bar)
    
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
            stats_text = f"📊 Total: {stats['total_files']} files ({stats['total_size_mb']} MB)"
            
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
                stats_text += f"\n{' | '.join(type_breakdown)}"
            else:
                stats_text = "🎉 Recycle bin is empty!"
            
            self.stats_label.text = stats_text
            
        except Exception as e:
            print(f"Error updating stats: {e}")
            self.stats_label.text = "❌ Error loading statistics"
    
    def cleanup_file_grid_widgets(self):
        """Properly cleanup all widgets in file grid before clearing"""
        try:
            for widget in self.file_grid.children[:]:
                if hasattr(widget, 'children'):
                    self.cleanup_widget_tree(widget)
        except Exception as e:
            print(f"Warning during widget cleanup: {e}")

    def cleanup_widget_tree(self, widget):
        """Recursively cleanup a widget tree and unbind all events"""
        try:
            event_types = ['on_press', 'on_release', 'on_touch_down', 'on_touch_up']
            
            for event_type in event_types:
                if hasattr(widget, event_type):
                    if hasattr(widget, '_event_listeners') and event_type in widget._event_listeners:
                        if len(widget._event_listeners[event_type]) > 0:
                            widget.unbind(**{event_type: None})
            
            if hasattr(widget, 'children'):
                for child in widget.children[:]:
                    self.cleanup_widget_tree(child)
            
            if hasattr(widget, 'clear_widgets'):
                widget.clear_widgets()
                
        except Exception as e:
            print(f"Warning cleaning widget {type(widget).__name__}: {e}")
    
    def refresh_file_grid(self):
        """Refresh the file grid based on current filter"""
        try:
            selected_file_id = self.selected_file['recycled_id'] if self.selected_file else None
            
            self.cleanup_file_grid_widgets()
            self.file_grid.clear_widgets()
            
            if self.current_filter == 'all':
                files = self.recycle_bin.get_recycled_files()
            else:
                files = self.recycle_bin.get_recycled_files(self.current_filter)
            
            if not files:
                empty_widget = self.create_empty_state_widget()
                self.file_grid.add_widget(empty_widget)
                return
            
            for file_info in files:
                file_widget = self.create_file_widget(file_info)
                self.file_grid.add_widget(file_widget)
                
                if selected_file_id and file_info['recycled_id'] == selected_file_id:
                    self.selected_file = file_info
                
        except Exception as e:
            print(f"Error refreshing file grid: {e}")
            self.file_grid.clear_widgets()
            error_card = self.create_error_widget(str(e))
            self.file_grid.add_widget(error_card)

    def create_error_widget(self, error_message):
        """Create error display widget"""
        error_card = MDCard(
            size_hint_y=None,
            height=dp(80),
            padding=15,
            md_bg_color=[0.8, 0.2, 0.2, 0.3]
        )
        error_label = MDLabel(
            text=f"❌ Error loading files: {error_message}",
            text_color=[1, 0.4, 0.4, 1],
            halign="center",
            font_style="Body2"
        )
        error_card.add_widget(error_label)
        return error_card
    
    def create_empty_state_widget(self):
        """Create widget for empty recycle bin state"""
        empty_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height=dp(200),
            padding=30,
            spacing=20,
            md_bg_color=[0.31, 0.35, 0.39, 0.8],  # BlueGray light
            elevation=2
        )
        
        filter_text = "this category" if self.current_filter != 'all' else "the recycle bin"
        
        empty_label = MDLabel(
            text=f'🎉 No files in {filter_text}\n\nDeleted files will appear here and be\nautomatically cleaned up based on retention settings.',
            font_style="Body1",
            halign='center',
            text_color=[0.7, 0.7, 0.7, 1]
        )
        empty_label.bind(size=empty_label.setter('text_size'))
        empty_card.add_widget(empty_label)
        
        return empty_card
    
    def create_file_widget(self, file_info):
        """Create widget for individual recycled file"""
        is_selected = self.selected_file and self.selected_file['recycled_id'] == file_info['recycled_id']
        
        # Main card with modern styling
        file_card = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(100),
            padding=15,
            spacing=15,
            elevation=4 if is_selected else 2,
            md_bg_color=[0.46, 0.53, 0.6, 1] if is_selected else [0.31, 0.35, 0.39, 0.9],
            ripple_behavior=True
        )
        
        # File type icon container
        icon_container = MDBoxLayout(
            orientation='vertical',
            size_hint_x=None,
            width=dp(60),
            padding=[5, 5]
        )
        
        file_type = file_info['file_type']
        icon = self.recycle_bin.FILE_TYPE_CONFIG[file_type]['icon']
        
        icon_label = MDLabel(
            text=icon,
            font_style="H4",
            halign="center",
            text_color="white"
        )
        icon_container.add_widget(icon_label)
        file_card.add_widget(icon_container)
        
        # File info section
        info_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_x=0.6,
            spacing=5
        )
        
        # File name (truncated if too long)
        display_name = file_info['display_name']
        if len(display_name) > 35:
            display_name = display_name[:32] + "..."
        
        name_label = MDLabel(
            text=display_name,
            font_style="Subtitle1",
            text_color="white",
            bold=True,
            size_hint_y=0.4
        )
        info_layout.add_widget(name_label)
        
        # Size and type info
        size_mb = file_info['size'] / (1024 * 1024)
        type_display = self.recycle_bin.FILE_TYPE_CONFIG[file_type]['display_name']
        
        size_label = MDLabel(
            text=f"Size: {size_mb:.1f} MB • {type_display}",
            font_style="Caption",
            text_color=[0.8, 0.8, 0.8, 1],
            size_hint_y=0.3
        )
        info_layout.add_widget(size_label)
        
        # Deletion date and days remaining
        deleted_at = datetime.fromisoformat(file_info['deleted_at'])
        deleted_date = deleted_at.strftime("%Y-%m-%d %H:%M")
        days_remaining = file_info['days_remaining']
        
        if days_remaining > 0:
            remaining_text = f"🕒 Deleted: {deleted_date} • {days_remaining} days remaining"
            remaining_color = [0.7, 0.7, 0.7, 1]
        else:
            remaining_text = f"⚠️ Deleted: {deleted_date} • EXPIRES SOON!"
            remaining_color = [1, 0.6, 0, 1]  # Orange warning
        
        date_label = MDLabel(
            text=remaining_text,
            font_style="Caption",
            text_color=remaining_color,
            size_hint_y=0.3
        )
        info_layout.add_widget(date_label)
        
        file_card.add_widget(info_layout)
        
        # Action buttons
        button_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            width=dp(160),
            spacing=10
        )
        
        # Select button
        select_btn = MDRaisedButton(
            text='📋 Select',
            md_bg_color=[0.2, 0.6, 0.8, 1],
            text_color="white",
            size_hint_x=0.5,
            elevation=2
        )
        select_btn.bind(on_press=lambda x: self.select_file(file_info))
        button_layout.add_widget(select_btn)
        
        # Options button
        options_btn = MDRaisedButton(
            text='⚙️ Options',
            md_bg_color=[0.5, 0.5, 0.5, 1],
            text_color="white",
            size_hint_x=0.5,
            elevation=2
        )
        options_btn.bind(on_press=lambda x: self.show_file_options(file_info))
        button_layout.add_widget(options_btn)
        
        file_card.add_widget(button_layout)
        
        # Add click to select functionality
        file_card.bind(on_release=lambda x: self.select_file(file_info))
        
        return file_card
    
    def select_file(self, file_info):
        """Select a file and refresh to show selection"""
        self.selected_file = file_info
        print(f"✅ File selected: {file_info['display_name']}")
        self.refresh_file_grid()
    
    def show_file_options(self, file_info):
        """Show detailed options for a specific file"""
        show_file_options_dialog(file_info, self.recycle_bin, self.refresh_recycle_bin)
    
    def restore_selected(self, instance):
        """Restore the currently selected file"""
        if not self.selected_file:
            show_no_selection_popup("restore")
            return
        
        restore_file_with_progress(self.selected_file, self.recycle_bin, self.refresh_recycle_bin_and_clear_selection)
    
    def delete_selected_forever(self, instance):
        """Delete selected file permanently"""
        if not self.selected_file:
            show_no_selection_popup("delete")
            return
        
        confirm_permanent_delete(self.selected_file, self.recycle_bin, self.refresh_recycle_bin_and_clear_selection)
    
    def refresh_recycle_bin_and_clear_selection(self):
        """Refresh recycle bin and clear selection"""
        self.selected_file = None
        self.refresh_recycle_bin()
    
    def manual_cleanup(self, instance):
        """Manually trigger cleanup of expired files"""
        manual_cleanup_dialog(self.recycle_bin, self.refresh_recycle_bin)
    
    def confirm_empty_all(self, instance):
        """Confirm emptying entire recycle bin"""
        confirm_empty_all_dialog(self.recycle_bin, self.refresh_recycle_bin_and_clear_selection)
    
    def cleanup(self):
        """Cleanup method for the entire RecycleBinWidget"""
        self.cleanup_file_grid_widgets()
        self.file_grid.clear_widgets()
        self.selected_file = None
        self.current_filter = 'all'
    
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