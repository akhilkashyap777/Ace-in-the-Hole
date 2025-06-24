import os
import re
import io
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture
from PIL import Image as PILImage
from photo_camera_module import PhotoCameraModule

class PhotoGalleryWidget(MDBoxLayout):
    
    def __init__(self, photo_vault_core, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.vault_core = photo_vault_core
        self.selected_photo = None
        self.photo_widgets = []
        
        self.camera_module = PhotoCameraModule(self)
        
        self.md_bg_color = [0.37, 0.49, 0.55, 1]
        
        self.build_ui()
        
        Clock.schedule_once(lambda dt: self.refresh_gallery(None), 0.1)
    
    def build_ui(self):
        self.build_header()
        self.build_photo_grid()
        self.build_bottom_buttons()
    
    def build_header(self):
        header = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(120),
            padding=[20, 20, 20, 10],
            spacing=10
        )
        
        title = MDLabel(
            text='PHOTO GALLERY',
            font_style="H3",
            text_color="white",
            halign="center",
            bold=True
        )
        header.add_widget(title)
        
        actions_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=15
        )
        
        self.add_btn = MDRaisedButton(
            text='📷 Add Photos',
            md_bg_color=[0.2, 0.7, 0.3, 1],
            text_color="white",
            size_hint_x=1,
            elevation=3
        )
        self.add_btn.bind(on_press=self.add_photos)
        actions_row.add_widget(self.add_btn)
        
        header.add_widget(actions_row)
        
        camera_buttons = self.camera_module.build_camera_buttons()
        header.add_widget(camera_buttons)
        
        self.add_widget(header)
    
    def build_photo_grid(self):
        scroll = MDScrollView(
            bar_width=dp(4),
            bar_color=[0.46, 0.53, 0.6, 0.7],
            bar_inactive_color=[0.7, 0.7, 0.7, 0.3],
            effect_cls="ScrollEffect"
        )
        
        self.photo_grid = MDGridLayout(
            cols=2, 
            spacing=15, 
            padding=[20, 10, 20, 10],
            size_hint_y=None,
            adaptive_height=True
        )
        
        scroll.add_widget(self.photo_grid)
        self.add_widget(scroll)
    
    def build_bottom_buttons(self):
        bottom_bar = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(70),
            padding=15,
            spacing=12,
            elevation=8,
            md_bg_color=[0.25, 0.29, 0.31, 1]
        )
        
        self.refresh_btn = MDFlatButton(
            text='🔄 Refresh',
            text_color="white",
            size_hint_x=0.2
        )
        self.refresh_btn.bind(on_press=self.refresh_gallery)
        bottom_bar.add_widget(self.refresh_btn)
        
        self.view_btn = MDFlatButton(
            text='👁️ View',
            text_color=[0.4, 0.8, 0.9, 1],
            size_hint_x=0.2
        )
        self.view_btn.bind(on_press=self.view_selected_photo)
        bottom_bar.add_widget(self.view_btn)
        
        self.export_btn = MDFlatButton(
            text='📤 Export',
            text_color=[0.6, 0.6, 0.9, 1],
            size_hint_x=0.2
        )
        self.export_btn.bind(on_press=self.export_selected_photo)
        bottom_bar.add_widget(self.export_btn)
        
        self.delete_btn = MDFlatButton(
            text='🗑️ Delete',
            text_color=[0.9, 0.4, 0.4, 1],
            size_hint_x=0.2
        )
        self.delete_btn.bind(on_press=self.delete_selected)
        bottom_bar.add_widget(self.delete_btn)
        
        self.back_btn = MDFlatButton(
            text='← Back',
            text_color=[0.7, 0.7, 0.7, 1],
            size_hint_x=0.2
        )
        self.back_btn.bind(on_press=self.back_to_vault)
        bottom_bar.add_widget(self.back_btn)
        
        self.add_widget(bottom_bar)
    
    def add_photos(self, instance):
        if self.vault_core.processing:
            return
            
        self.add_btn.disabled = True
        self.add_btn.text = 'Processing...'
        
        self.vault_core.request_permissions()
        
        def on_photos_added(imported_files, skipped_files):
            self.add_btn.disabled = False
            self.add_btn.text = '📷 Add Photos'
            
            self.show_import_results(imported_files, skipped_files)
            
            if imported_files:
                self.refresh_gallery(None)
        
        self.vault_core.select_photos_from_gallery(on_photos_added)
    
    def show_import_results(self, imported_files, skipped_files):
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
        
        if imported_files:
            success_text = f"✅ Successfully imported {len(imported_files)} photo(s) to vault!"
            success_label = MDLabel(
                text=success_text, 
                halign='center',
                text_color="white",
                font_style="Body1"
            )
            content.add_widget(success_label)
        
        if skipped_files:
            skipped_text = f"\n⚠️ Skipped {len(skipped_files)} file(s):\n"
            for skipped in skipped_files[:3]:
                skipped_text += f"• {skipped}\n"
            
            if len(skipped_files) > 3:
                skipped_text += f"... and {len(skipped_files) - 3} more"
            
            skipped_label = MDLabel(
                text=skipped_text, 
                halign='center',
                text_color=[1, 0.8, 0, 1],
                font_style="Body2"
            )
            content.add_widget(skipped_label)
        
        if not imported_files and not skipped_files:
            no_files_label = MDLabel(
                text="No files were selected or imported.",
                text_color=[0.7, 0.7, 0.7, 1],
                halign='center'
            )
            content.add_widget(no_files_label)
        
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
            title='Import Results',
            content=content,
            size_hint=(0.8, 0.6),
            auto_dismiss=False
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
        
        if imported_files and not skipped_files:
            Clock.schedule_once(lambda dt: popup.dismiss(), 3)
    
    def refresh_gallery(self, instance):
        self.cleanup_photo_widgets()
        self.photo_grid.clear_widgets()
        self.selected_photo = None
        
        photos = self.vault_core.get_vault_photos()
        
        if not photos:
            empty_widget = self.create_empty_state_widget()
            self.photo_grid.add_widget(empty_widget)
            return
        
        self.load_photos_batch(photos, 0)
    
    def create_empty_state_widget(self):
        empty_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height=dp(200),
            padding=30,
            spacing=20,
            md_bg_color=[0.31, 0.35, 0.39, 0.8],
            elevation=2
        )
        
        empty_label = MDLabel(
            text='📷 No photos in vault\n\nTap "Add Photos" to import your images\nfrom gallery and keep them secure',
            font_style="Body1",
            halign='center',
            text_color=[0.7, 0.7, 0.7, 1]
        )
        empty_label.bind(size=empty_label.setter('text_size'))
        empty_card.add_widget(empty_label)
        
        return empty_card
    
    def load_photos_batch(self, photos, start_index, batch_size=6):
        end_index = min(start_index + batch_size, len(photos))
        
        for i in range(start_index, end_index):
            photo_path = photos[i]
            photo_widget = self.create_photo_widget(photo_path)
            if photo_widget:
                self.photo_grid.add_widget(photo_widget)
                self.photo_widgets.append(photo_widget)
        
        if end_index < len(photos):
            Clock.schedule_once(lambda dt: self.load_photos_batch(photos, end_index), 0.1)
    
    def cleanup_photo_widgets(self):
        for widget in self.photo_widgets:
            try:
                for child in widget.walk():
                    if hasattr(child, 'texture') and child.texture:
                        child.texture = None
                    if hasattr(child, 'source'):
                        child.source = ''
            except:
                pass
        self.photo_widgets.clear()
    
    def create_photo_widget(self, photo_path):
        try:
            photo_card = MDCard(
                orientation='vertical',
                size_hint_y=None,
                height=dp(220),
                padding=10,
                spacing=8,
                elevation=3,
                md_bg_color=[0.31, 0.35, 0.39, 0.9],
                ripple_behavior=True
            )
            
            img_container = MDBoxLayout(size_hint_y=0.8)
            
            if os.path.exists(photo_path):
                img = Image(
                    source=photo_path,
                    fit_mode="cover"
                )
                img_container.add_widget(img)
            else:
                error_label = MDLabel(
                    text='📷\nImage Error',
                    halign='center',
                    text_color=[0.7, 0.7, 0.7, 1],
                    font_style="Body2"
                )
                img_container.add_widget(error_label)
            
            photo_card.add_widget(img_container)
            
            info_layout = MDBoxLayout(
                orientation='horizontal',
                size_hint_y=0.2,
                spacing=5
            )
            
            filename = os.path.basename(photo_path)
            display_name = filename[:15] + '...' if len(filename) > 15 else filename
            
            info_label = MDLabel(
                text=display_name,
                font_style="Caption",
                text_color="white",
                size_hint_x=0.7
            )
            info_layout.add_widget(info_label)
            
            select_btn = MDRaisedButton(
                text='📋',
                size_hint_x=0.3,
                md_bg_color=[0.2, 0.6, 0.8, 1],
                text_color="white",
                elevation=2
            )
            select_btn.bind(on_press=lambda x: self.select_photo(photo_path))
            info_layout.add_widget(select_btn)
            
            photo_card.add_widget(info_layout)
            
            photo_card.bind(on_release=lambda x: self.select_photo(photo_path))
            
            return photo_card
            
        except Exception as e:
            return None
    
    def select_photo(self, photo_path):
        self.selected_photo = photo_path
        
        vault_filename = os.path.basename(photo_path)
        match = re.match(r'vault_\d{8}_\d{6}_\d+_(.+)', vault_filename)
        if match:
            original_name = match.group(1)
        else:
            original_name = vault_filename
        
        content = MDLabel(
            text=f"Selected: {original_name}\n\nUse the buttons below to view, export, or delete this photo.",
            text_color="white",
            halign='center'
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
        if not self.selected_photo:
            self.show_no_selection_message("view")
            return
        
        self.view_photo(self.selected_photo)
    
    def view_photo(self, photo_path):
        content = MDBoxLayout(orientation='vertical', spacing=10)
        
        try:
            img = Image(
                source=photo_path,
                fit_mode="contain"
            )
            content.add_widget(img)
        except Exception as e:
            error_label = MDLabel(
                text='Error loading image',
                text_color="white",
                halign='center'
            )
            content.add_widget(error_label)
        
        button_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=15
        )
        
        export_btn = MDRaisedButton(
            text='📤 Export Photo',
            md_bg_color=[0.6, 0.4, 0.8, 1],
            text_color="white",
            elevation=3
        )
        
        close_btn = MDRaisedButton(
            text='❌ Close',
            md_bg_color=[0.5, 0.5, 0.5, 1],
            text_color="white",
            elevation=2
        )
        
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
            try:
                if hasattr(img, 'texture') and img.texture:
                    img.texture = None
            except:
                pass
        
        export_btn.bind(on_press=export_from_view)
        close_btn.bind(on_press=close_popup)
        popup.open()
    
    def export_selected_photo(self, instance):
        if not self.selected_photo:
            self.show_no_selection_message("export")
            return
        
        vault_filename = os.path.basename(self.selected_photo)
        match = re.match(r'vault_\d{8}_\d{6}_\d+_(.+)', vault_filename)
        if match:
            original_name = match.group(1)
        else:
            original_name = vault_filename
        
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
        
        info_label = MDLabel(
            text=f"Export '{original_name}' to device storage?\n\nYou will be asked to choose the destination folder.",
            text_color="white",
            halign='center'
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
        def on_folder_selected(result):
            if result['success']:
                folder_path = result['folder_path']
                is_fallback = result.get('is_fallback', False)
                
                export_result = self.vault_core.export_photo(self.selected_photo, folder_path)
                
                if export_result['success']:
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
                error_text = f"❌ Folder selection failed!\n\nError: {result['error']}\n\nPlease try again."
                self.show_export_result(error_text, "Folder Selection Failed", False, retry_photo=self.selected_photo)
        
        self.vault_core.select_export_folder(on_folder_selected)

    def handle_export_error(self, export_result):
        if export_result.get('needs_folder_selection'):
            error_text = f"❌ Export failed!\n\nError: {export_result['error']}\n\nWould you like to try with a different folder?"
            self.show_export_result(error_text, "Export Failed", False, retry_photo=self.selected_photo)
        else:
            error_text = f"❌ Export failed!\n\nError: {export_result['error']}"
            self.show_export_result(error_text, "Export Failed", False, None)

    def show_export_result(self, message, title, is_success, retry_photo=None):
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
        
        result_label = MDLabel(
            text=message,
            text_color="white" if is_success else [1, 0.6, 0.6, 1],
            halign='center'
        )
        content.add_widget(result_label)
        
        button_layout = MDBoxLayout(orientation='horizontal', spacing=10)
        
        if retry_photo and not is_success:
            retry_btn = MDRaisedButton(
                text='🔄 Try Different Folder',
                md_bg_color=[0.6, 0.4, 0.8, 1],
                text_color="white",
                elevation=3
            )
            button_layout.add_widget(retry_btn)
            
            def retry_export(instance):
                popup.dismiss()
                self.selected_photo = retry_photo
                self.choose_folder_and_export()
            
            retry_btn.bind(on_press=retry_export)
        
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
        
        if is_success:
            Clock.schedule_once(lambda dt: popup.dismiss(), 5)
    
    def show_no_selection_message(self, action):
        content = MDLabel(
            text=f'Please select a photo first by tapping on any image',
            text_color="white",
            halign='center'
        )
        popup = Popup(
            title=f'No Photo Selected',
            content=content,
            size_hint=(0.7, 0.3),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def delete_selected(self, instance):
        if not self.selected_photo:
            self.show_no_selection_message("delete")
            return
        
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
        
        retention_days = 30
        if hasattr(self.vault_core.app, 'recycle_bin'):
            retention_days = self.vault_core.app.recycle_bin.FILE_TYPE_CONFIG['photos']['retention_days']
        
        label = MDLabel(
            text=f'Move this photo to recycle bin?\n\n📁 {os.path.basename(self.selected_photo)}\n\n♻️ You can restore it within {retention_days} days\n🗑️ It will be auto-deleted after {retention_days} days\n\nThis is much safer than permanent deletion!',
            text_color="white",
            halign='center'
        )
        content.add_widget(label)
        
        btn_layout = MDBoxLayout(orientation='horizontal', spacing=10)
        
        yes_btn = MDRaisedButton(
            text='🗑️ Move to Recycle Bin',
            md_bg_color=[0.8, 0.6, 0.2, 1],
            text_color="white",
            elevation=3
        )
        
        no_btn = MDRaisedButton(
            text='❌ Cancel',
            md_bg_color=[0.5, 0.5, 0.5, 1],
            text_color="white",
            elevation=2
        )
        
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
                
                success_content = MDLabel(
                    text=f'Photo moved to recycle bin successfully!\n\n♻️ You can restore it anytime from the vault menu.\n🕒 It will be kept for {retention_days} days.',
                    text_color=[0.4, 0.8, 0.4, 1],
                    halign='center'
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
                error_content = MDLabel(
                    text='Could not move photo to recycle bin.\nPlease try again.',
                    text_color=[1, 0.4, 0.4, 1],
                    halign='center'
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
        self.cleanup_photo_widgets()
        
        if hasattr(self.vault_core.app, 'show_vault_main'):
            self.vault_core.app.show_vault_main()

def create_thumbnail(image_path, size=(150, 150)):
    try:
        with PILImage.open(image_path) as img:
            img.thumbnail(size, PILImage.Resampling.LANCZOS)
            
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            texture = Texture.create(size=img.size)
            texture.blit_buffer(img_bytes.getvalue(), colorfmt='rgba', bufferfmt='ubyte')
            return texture
    except Exception as e:
        return None