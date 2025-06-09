import os
import re
import io
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture
from PIL import Image as PILImage

class PhotoGalleryWidget(BoxLayout):
    """
    Photo Gallery UI Widget
    
    Features:
    - Grid-based photo display
    - Photo selection and viewing
    - Export functionality with folder selection
    - Recycle bin integration
    - Memory-efficient batch loading
    """
    
    def __init__(self, photo_vault_core, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.vault_core = photo_vault_core
        self.selected_photo = None
        self.photo_widgets = []  # Keep track of photo widgets for cleanup
        
        self.build_ui()
        
        # Load initial photos
        Clock.schedule_once(lambda dt: self.refresh_gallery(None), 0.1)
    
    def build_ui(self):
        """Build the main UI layout"""
        # Header with title and add button
        self.build_header()
        
        # Photo grid in scroll view
        self.build_photo_grid()
        
        # Bottom action buttons
        self.build_bottom_buttons()
    
    def build_header(self):
        """Build header with title and add button"""
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=10)
        
        title = Label(text='🖼️ Secret Photos', font_size=24, size_hint_x=0.7)
        header.add_widget(title)
        
        self.add_btn = Button(text='+ Add Photos', font_size=16, size_hint_x=0.3)
        self.add_btn.bind(on_press=self.add_photos)
        header.add_widget(self.add_btn)
        
        self.add_widget(header)
    
    def build_photo_grid(self):
        """Build scrollable photo grid"""
        scroll = ScrollView()
        self.photo_grid = GridLayout(cols=2, spacing=10, padding=10, size_hint_y=None)
        self.photo_grid.bind(minimum_height=self.photo_grid.setter('height'))
        
        scroll.add_widget(self.photo_grid)
        self.add_widget(scroll)
    
    def build_bottom_buttons(self):
        """Build bottom action buttons"""
        bottom_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), padding=10)
        
        self.refresh_btn = Button(text='🔄 Refresh', size_hint_x=0.2)
        self.refresh_btn.bind(on_press=self.refresh_gallery)
        bottom_layout.add_widget(self.refresh_btn)
        
        self.export_btn = Button(text='📤 Export', size_hint_x=0.2)
        self.export_btn.bind(on_press=self.export_selected_photo)
        bottom_layout.add_widget(self.export_btn)
        
        self.delete_btn = Button(text='🗑️ Delete', size_hint_x=0.2)
        self.delete_btn.bind(on_press=self.delete_selected)
        bottom_layout.add_widget(self.delete_btn)
        
        self.view_btn = Button(text='👁️ View', size_hint_x=0.2)
        self.view_btn.bind(on_press=self.view_selected_photo)
        bottom_layout.add_widget(self.view_btn)
        
        self.back_btn = Button(text='⬅️ Back', size_hint_x=0.2)
        self.back_btn.bind(on_press=self.back_to_vault)
        bottom_layout.add_widget(self.back_btn)
        
        self.add_widget(bottom_layout)
    
    def add_photos(self, instance):
        """Handle add photos button press"""
        # Disable button during processing
        if self.vault_core.processing:
            return
            
        self.add_btn.disabled = True
        self.add_btn.text = 'Processing...'
        
        self.vault_core.request_permissions()
        
        def on_photos_added(imported_files, skipped_files):
            # Re-enable button
            self.add_btn.disabled = False
            self.add_btn.text = '+ Add Photos'
            
            # Show results
            self.show_import_results(imported_files, skipped_files)
            
            # Refresh gallery if files were imported
            if imported_files:
                self.refresh_gallery(None)
        
        self.vault_core.select_photos_from_gallery(on_photos_added)
    
    def show_import_results(self, imported_files, skipped_files):
        """Show import results popup"""
        content = BoxLayout(orientation='vertical', spacing=10)
        
        # Success message
        if imported_files:
            success_text = f"✅ Successfully imported {len(imported_files)} photo(s) to vault!"
            success_label = Label(text=success_text, halign='center')
            content.add_widget(success_label)
        
        # Skipped files message
        if skipped_files:
            skipped_text = f"\n⚠️ Skipped {len(skipped_files)} file(s):\n"
            for skipped in skipped_files[:3]:  # Show first 3
                skipped_text += f"• {skipped}\n"
            
            if len(skipped_files) > 3:
                skipped_text += f"... and {len(skipped_files) - 3} more"
            
            skipped_label = Label(text=skipped_text, halign='center')
            content.add_widget(skipped_label)
        
        # If no files imported
        if not imported_files and not skipped_files:
            no_files_label = Label(text="No files were selected or imported.")
            content.add_widget(no_files_label)
        
        # Close button
        close_btn = Button(text='OK', size_hint_y=None, height=dp(40))
        content.add_widget(close_btn)
        
        popup = Popup(
            title='Import Results',
            content=content,
            size_hint=(0.8, 0.6),
            auto_dismiss=False
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
        
        # Auto-dismiss after 5 seconds if successful and no skipped files
        if imported_files and not skipped_files:
            Clock.schedule_once(lambda dt: popup.dismiss(), 3)
    
    def refresh_gallery(self, instance):
        """Refresh the photo gallery"""
        # Clear existing widgets
        self.cleanup_photo_widgets()
        self.photo_grid.clear_widgets()
        self.selected_photo = None
        
        photos = self.vault_core.get_vault_photos()
        
        if not photos:
            # Show empty state
            empty_label = Label(
                text='No photos in vault\nTap "Add Photos" to get started',
                font_size=18,
                halign='center'
            )
            self.photo_grid.add_widget(empty_label)
            return
        
        # Load photos in batches to avoid memory issues
        self.load_photos_batch(photos, 0)
    
    def load_photos_batch(self, photos, start_index, batch_size=6):
        """Load photos in batches to prevent memory issues"""
        end_index = min(start_index + batch_size, len(photos))
        
        for i in range(start_index, end_index):
            photo_path = photos[i]
            photo_widget = self.create_photo_widget(photo_path)
            self.photo_grid.add_widget(photo_widget)
            self.photo_widgets.append(photo_widget)
        
        # Load next batch if there are more photos
        if end_index < len(photos):
            Clock.schedule_once(lambda dt: self.load_photos_batch(photos, end_index), 0.1)
    
    def cleanup_photo_widgets(self):
        """Clean up photo widgets to prevent memory leaks"""
        for widget in self.photo_widgets:
            try:
                if hasattr(widget, 'children'):
                    for child in widget.children:
                        if hasattr(child, 'texture') and child.texture:
                            child.texture = None
            except:
                pass
        self.photo_widgets.clear()
    
    def create_photo_widget(self, photo_path):
        """Create a widget for displaying a photo thumbnail"""
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(200))
        
        # Create image button with error handling
        try:
            img = Image(
                source=photo_path,
                size_hint_y=0.8,
                fit_mode="contain"
            )
            
            # Make it clickable with overlay button
            btn_layout = BoxLayout()
            btn_layout.add_widget(img)
            
            btn = Button(
                size_hint_y=0.8,
                background_color=(0, 0, 0, 0),  # Transparent
                text=''
            )
            btn.bind(on_press=lambda x: self.select_photo(photo_path))
            btn_layout.add_widget(btn)
            
            layout.add_widget(btn_layout)
            
        except Exception as e:
            print(f"Error loading image {photo_path}: {e}")
            # Fallback if image can't be loaded
            error_btn = Button(
                text='📷\nImage Error',
                size_hint_y=0.8
            )
            error_btn.bind(on_press=lambda x: self.select_photo(photo_path))
            layout.add_widget(error_btn)
        
        # Photo info
        filename = os.path.basename(photo_path)
        display_name = filename[:20] + '...' if len(filename) > 20 else filename
        info_label = Label(
            text=display_name,
            size_hint_y=0.2,
            font_size=12
        )
        layout.add_widget(info_label)
        
        return layout
    
    def select_photo(self, photo_path):
        """Select a photo for operations"""
        self.selected_photo = photo_path
        
        # Get original filename for display
        vault_filename = os.path.basename(photo_path)
        match = re.match(r'vault_\d{8}_\d{6}_\d+_(.+)', vault_filename)
        if match:
            original_name = match.group(1)
        else:
            original_name = vault_filename
        
        # Show selection feedback
        content = Label(
            text=f"Selected: {original_name}\n\nUse the buttons below to view, export, or delete this photo."
        )
        
        popup = Popup(
            title='Photo Selected',
            content=content,
            size_hint=(0.7, 0.4),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def view_selected_photo(self, instance):
        """View the selected photo in full screen"""
        if not self.selected_photo:
            self.show_no_selection_message("view")
            return
        
        self.view_photo(self.selected_photo)
    
    def view_photo(self, photo_path):
        """View a photo in full screen"""
        content = BoxLayout(orientation='vertical')
        
        # Full size image
        try:
            img = Image(
                source=photo_path,
                fit_mode="contain"
            )
            content.add_widget(img)
        except Exception as e:
            print(f"Error loading full image: {e}")
            error_label = Label(text='Error loading image')
            content.add_widget(error_label)
        
        # Button layout
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=10
        )
        
        export_btn = Button(text='📤 Export Photo')
        close_btn = Button(text='❌ Close')
        
        button_layout.add_widget(export_btn)
        button_layout.add_widget(close_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title=os.path.basename(photo_path),
            content=content,
            size_hint=(0.95, 0.95),
            auto_dismiss=False
        )
        
        def export_from_view(instance):
            popup.dismiss()
            self.selected_photo = photo_path
            self.export_selected_photo(None)
        
        def close_popup(instance):
            popup.dismiss()
            # Clean up the image texture
            try:
                if hasattr(img, 'texture') and img.texture:
                    img.texture = None
            except:
                pass
        
        export_btn.bind(on_press=export_from_view)
        close_btn.bind(on_press=close_popup)
        popup.open()
    
    def export_selected_photo(self, instance):
        """Export the selected photo with folder selection"""
        if not self.selected_photo:
            self.show_no_selection_message("export")
            return
        
        # Get original filename for display
        vault_filename = os.path.basename(self.selected_photo)
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
            title='Export Photo',
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
                export_result = self.vault_core.export_photo(self.selected_photo, folder_path)
                
                if export_result['success']:
                    # Success message with location
                    success_text = f"✅ Photo exported successfully!\n\n"
                    success_text += f"📷 File: {export_result['original_name']}\n"
                    success_text += f"📁 Location: {export_result['export_path']}\n\n"
                    
                    if is_fallback:
                        success_text += "⚠️ Used app storage as destination\n"
                    
                    success_text += "You can now view it in your gallery app."
                    
                    self.show_export_result(success_text, "Export Successful", True)
                else:
                    self.handle_export_error(export_result)
            else:
                # Folder selection failed
                error_text = f"❌ Folder selection failed!\n\nError: {result['error']}\n\nPlease try again."
                self.show_export_result(error_text, "Folder Selection Failed", False, retry_photo=self.selected_photo)
        
        # Start folder selection
        self.vault_core.select_export_folder(on_folder_selected)

    def handle_export_error(self, export_result):
        """Handle export errors with retry option"""
        if export_result.get('needs_folder_selection'):
            error_text = f"❌ Export failed!\n\nError: {export_result['error']}\n\nWould you like to try with a different folder?"
            self.show_export_result(error_text, "Export Failed", False, retry_photo=self.selected_photo)
        else:
            error_text = f"❌ Export failed!\n\nError: {export_result['error']}"
            self.show_export_result(error_text, "Export Failed", False, None)

    def show_export_result(self, message, title, is_success, retry_photo=None):
        """Show export result with optional retry"""
        content = BoxLayout(orientation='vertical', spacing=10)
        
        result_label = Label(text=message)
        content.add_widget(result_label)
        
        button_layout = BoxLayout(orientation='horizontal')
        
        if retry_photo and not is_success:
            # Add retry button for failures
            retry_btn = Button(text='🔄 Try Different Folder')
            button_layout.add_widget(retry_btn)
            
            def retry_export(instance):
                popup.dismiss()
                self.selected_photo = retry_photo
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
        """Show message when no photo is selected"""
        content = Label(text=f'Please select a photo first by tapping on any image')
        popup = Popup(
            title=f'No Photo Selected',
            content=content,
            size_hint=(0.7, 0.3),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def delete_selected(self, instance):
        """Delete the selected photo"""
        if not self.selected_photo:
            self.show_no_selection_message("delete")
            return
        
        content = BoxLayout(orientation='vertical', spacing=10)
        
        # Get retention days from recycle bin config
        retention_days = 30  # Default
        if hasattr(self.vault_core.app, 'recycle_bin'):
            retention_days = self.vault_core.app.recycle_bin.FILE_TYPE_CONFIG['photos']['retention_days']
        
        label = Label(
            text=f'Move this photo to recycle bin?\n\n📁 {os.path.basename(self.selected_photo)}\n\n♻️ You can restore it within {retention_days} days\n🗑️ It will be auto-deleted after {retention_days} days\n\nThis is much safer than permanent deletion!'
        )
        content.add_widget(label)
        
        btn_layout = BoxLayout(orientation='horizontal')
        
        yes_btn = Button(text='🗑️ Move to Recycle Bin')
        no_btn = Button(text='❌ Cancel')
        
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title='Move to Recycle Bin',
            content=content,
            size_hint=(0.8, 0.6),
            auto_dismiss=False
        )
        
        def delete_confirmed(instance):
            if self.vault_core.delete_photo(self.selected_photo):
                self.refresh_gallery(None)
                popup.dismiss()
                
                success_content = Label(
                    text=f'Photo moved to recycle bin successfully!\n\n♻️ You can restore it anytime from the vault menu.\n🕒 It will be kept for {retention_days} days.'
                )
                success_popup = Popup(
                    title='✅ Moved to Recycle Bin',
                    content=success_content,
                    size_hint=(0.8, 0.5),
                    auto_dismiss=True
                )
                success_popup.open()
                Clock.schedule_once(lambda dt: success_popup.dismiss(), 3)
            else:
                popup.dismiss()
                error_content = Label(
                    text='Could not move photo to recycle bin.\nPlease try again.'
                )
                error_popup = Popup(
                    title='❌ Error',
                    content=error_content,
                    size_hint=(0.7, 0.4),
                    auto_dismiss=True
                )
                error_popup.open()
                Clock.schedule_once(lambda dt: error_popup.dismiss(), 3)
        
        yes_btn.bind(on_press=delete_confirmed)
        no_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def back_to_vault(self, instance):
        """Go back to main vault screen"""
        # Clean up before leaving
        self.cleanup_photo_widgets()
        
        # Navigate back
        if hasattr(self.vault_core.app, 'show_vault_main'):
            self.vault_core.app.show_vault_main()

# Thumbnail creation utility function
def create_thumbnail(image_path, size=(150, 150)):
    """Create thumbnail for image using PIL"""
    try:
        with PILImage.open(image_path) as img:
            img.thumbnail(size, PILImage.Resampling.LANCZOS)
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Create Kivy texture
            texture = Texture.create(size=img.size)
            texture.blit_buffer(img_bytes.getvalue(), colorfmt='rgba', bufferfmt='ubyte')
            return texture
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return None

print("✅ Photo Vault UI loaded successfully")
print("🎨 Features: Grid view, selection, export, recycle bin integration")
print("💾 Memory-efficient batch loading for large photo collections")
print("📤 Complete export functionality with folder selection")
print("♻️ Safe deletion with recycle bin integration")