from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.metrics import dp

class DocumentComponents:
    
    def __init__(self, parent_ui):
        self.parent = parent_ui
        self.vault_core = parent_ui.vault_core
    
    def create_empty_state_widget(self, current_filter):
        empty_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height=dp(200),
            padding=30,
            spacing=20,
            md_bg_color=[0.31, 0.35, 0.39, 0.8],
            elevation=2
        )
        
        if current_filter:
            category_name = self.vault_core.FILE_CATEGORIES[current_filter]['display_name']
            empty_text = f'No {category_name.lower()} in vault\n\nTap "Add Files" to get started'
        else:
            empty_text = 'No documents in vault\n\nTap "Add Files" to get started'
        
        empty_label = MDLabel(
            text=empty_text,
            font_style="Body1",
            halign='center',
            text_color=[0.7, 0.7, 0.7, 1]
        )
        empty_label.bind(size=empty_label.setter('text_size'))
        empty_card.add_widget(empty_label)
        
        return empty_card
    
    def show_import_results(self, imported_files, skipped_files):
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
        
        if imported_files:
            success_text = f"Successfully imported {len(imported_files)} file(s):\n\n"
            for file_info in imported_files[:5]:
                success_text += f"• {file_info['original_name']} ({file_info['category']})\n"
            
            if len(imported_files) > 5:
                success_text += f"... and {len(imported_files) - 5} more files"
            
            success_label = MDLabel(
                text=success_text,
                text_color="white",
                halign='left'
            )
            content.add_widget(success_label)
        
        if skipped_files:
            skipped_text = f"\nSkipped {len(skipped_files)} file(s):\n"
            for skipped in skipped_files[:3]:
                skipped_text += f"• {skipped}\n"
            
            if len(skipped_files) > 3:
                skipped_text += f"... and {len(skipped_files) - 3} more"
            
            skipped_label = MDLabel(
                text=skipped_text,
                text_color=[1, 0.8, 0, 1],
                halign='left'
            )
            content.add_widget(skipped_label)
        
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
            Clock.schedule_once(lambda dt: popup.dismiss(), 5)
    
    def show_no_selection_message(self, action):
        content = MDLabel(
            text=f'Please select a document first by tapping "Select" on any file',
            text_color="white",
            halign='center'
        )
        popup = Popup(
            title=f'No Document Selected',
            content=content,
            size_hint=(0.7, 0.3),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def show_document_view(self, doc):
        preview_result = self.vault_core.get_document_preview(doc['path'])
        
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=15)
        
        info_text = f"{doc['original_name']}\n"
        info_text += f"Category: {doc['category_info']['display_name']}\n"
        info_text += f"Size: {doc['size'] / (1024 * 1024):.1f} MB\n"
        info_text += f"Modified: {doc['modified'].strftime('%Y-%m-%d %H:%M:%S')}"
        
        info_label = MDLabel(
            text=info_text,
            font_style="Body1",
            size_hint_y=None,
            height=dp(100),
            halign='left',
            text_color="white"
        )
        info_label.bind(size=info_label.setter('text_size'))
        content.add_widget(info_label)
        
        if preview_result['preview_available'] and preview_result['success']:
            preview_scroll = MDScrollView(size_hint_y=0.7)
            
            preview_text = preview_result['content']
            if preview_result['truncated']:
                preview_text += f"\n\n... (showing first {preview_result.get('total_lines', 20)} lines)"
            
            preview_input = TextInput(
                text=preview_text,
                readonly=True,
                font_size=12,
                font_name='RobotoMono-Regular'
            )
            
            preview_scroll.add_widget(preview_input)
            content.add_widget(preview_scroll)
            
        else:
            no_preview_label = MDLabel(
                text=f"Preview not available for this file type\n\n{doc['category_info']['description']}\n\nTo view this file, export it and open with an appropriate application.",
                halign='center',
                size_hint_y=0.7,
                text_color=[0.8, 0.8, 0.8, 1]
            )
            no_preview_label.bind(size=no_preview_label.setter('text_size'))
            content.add_widget(no_preview_label)
        
        button_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=10
        )
        
        export_btn = MDRaisedButton(
            text='Export File',
            md_bg_color=[0.6, 0.4, 0.8, 1],
            text_color="white",
            elevation=3
        )
        close_btn = MDRaisedButton(
            text='Close',
            md_bg_color=[0.5, 0.5, 0.5, 1],
            text_color="white",
            elevation=2
        )
        
        button_layout.add_widget(export_btn)
        button_layout.add_widget(close_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title=f'View Document - {doc["original_name"][:30]}...' if len(doc["original_name"]) > 30 else f'View Document - {doc["original_name"]}',
            content=content,
            size_hint=(0.9, 0.9),
            auto_dismiss=False
        )
        
        def export_from_view(instance):
            popup.dismiss()
            self.show_export_dialog(doc)
        
        export_btn.bind(on_press=export_from_view)
        close_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def show_export_dialog(self, doc):
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
        
        info_label = MDLabel(
            text=f"Export '{doc['original_name']}' to device storage?\n\nYou will be asked to choose the destination folder.",
            text_color="white",
            halign='center'
        )
        content.add_widget(info_label)
        
        button_layout = MDBoxLayout(orientation='horizontal', spacing=10)
        
        choose_btn = MDRaisedButton(
            text='Choose Folder & Export',
            md_bg_color=[0.6, 0.4, 0.8, 1],
            text_color="white",
            elevation=3
        )
        
        cancel_btn = MDRaisedButton(
            text='Cancel',
            md_bg_color=[0.5, 0.5, 0.5, 1],
            text_color="white",
            elevation=2
        )
        
        button_layout.add_widget(choose_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)
        
        popup = Popup(
            title='Export Document',
            content=content,
            size_hint=(0.8, 0.5),
            auto_dismiss=False
        )
        
        def start_export(instance):
            popup.dismiss()
            self.choose_folder_and_export(doc)
        
        choose_btn.bind(on_press=start_export)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()

    def choose_folder_and_export(self, doc):
        def on_folder_selected(result):
            if result['success']:
                folder_path = result['folder_path']
                is_fallback = result.get('is_fallback', False)
                
                export_result = self.vault_core.export_document(doc['path'], folder_path)
                
                if export_result['success']:
                    success_text = f"Document exported successfully!\n\n"
                    success_text += f"File: {export_result['original_name']}\n"
                    success_text += f"Location: {export_result['export_path']}\n\n"
                    
                    if is_fallback:
                        success_text += "Used app storage as destination\n"
                    
                    success_text += "You can now open it with any compatible application."
                    
                    self.show_export_result(success_text, "Export Successful", True)
                else:
                    self.handle_export_error(export_result, doc)
            else:
                error_text = f"Folder selection failed!\n\nError: {result['error']}\n\nPlease try again."
                self.show_export_result(error_text, "Folder Selection Failed", False, doc)
        
        self.vault_core.select_export_folder(on_folder_selected)

    def handle_export_error(self, export_result, doc):
        if export_result.get('needs_folder_selection'):
            error_text = f"Export failed!\n\nError: {export_result['error']}\n\nWould you like to try with a different folder?"
            self.show_export_result(error_text, "Export Failed", False, doc)
        else:
            error_text = f"Export failed!\n\nError: {export_result['error']}"
            self.show_export_result(error_text, "Export Failed", False, None)

    def show_export_result(self, message, title, is_success, retry_doc=None):
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
        
        result_label = MDLabel(
            text=message,
            text_color="white" if is_success else [1, 0.6, 0.6, 1],
            halign='center'
        )
        content.add_widget(result_label)
        
        button_layout = MDBoxLayout(orientation='horizontal', spacing=10)
        
        if retry_doc and not is_success:
            retry_btn = MDRaisedButton(
                text='Try Different Folder',
                md_bg_color=[0.6, 0.4, 0.8, 1],
                text_color="white",
                elevation=3
            )
            button_layout.add_widget(retry_btn)
            
            def retry_export(instance):
                popup.dismiss()
                self.choose_folder_and_export(retry_doc)
            
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
    
    def show_delete_dialog(self, doc, refresh_callback):
        retention_days = 45
        if hasattr(self.vault_core.app, 'recycle_bin'):
            retention_days = self.vault_core.app.recycle_bin.FILE_TYPE_CONFIG['documents']['retention_days']
        
        content = MDBoxLayout(orientation='vertical', spacing=15, padding=15)
        
        label = MDLabel(
            text=f'Move this document to recycle bin?\n\n{doc["original_name"]}\n\nYou can restore it within {retention_days} days\nIt will be auto-deleted after {retention_days} days\n\nThis is much safer than permanent deletion!',
            text_color="white",
            halign='center'
        )
        content.add_widget(label)
        
        btn_layout = MDBoxLayout(orientation='horizontal', spacing=10)
        
        yes_btn = MDRaisedButton(
            text='Move to Recycle Bin',
            md_bg_color=[0.8, 0.6, 0.2, 1],
            text_color="white",
            elevation=3
        )
        
        no_btn = MDRaisedButton(
            text='Cancel',
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
            if self.vault_core.delete_document(doc['path']):
                refresh_callback()
                popup.dismiss()
                
                success_content = MDLabel(
                    text=f'Document moved to recycle bin successfully!\n\nYou can restore it anytime from the vault menu.\nIt will be kept for {retention_days} days.',
                    text_color=[0.4, 0.8, 0.4, 1],
                    halign='center'
                )
                success_popup = Popup(
                    title='Moved to Recycle Bin',
                    content=success_content,
                    size_hint=(0.8, 0.5),
                    auto_dismiss=True
                )
                success_popup.open()
                Clock.schedule_once(lambda dt: success_popup.dismiss(), 3)
            else:
                popup.dismiss()
                error_content = MDLabel(
                    text='Could not move document to recycle bin.\nPlease try again.',
                    text_color=[1, 0.4, 0.4, 1],
                    halign='center'
                )
                error_popup = Popup(
                    title='Error',
                    content=error_content,
                    size_hint=(0.7, 0.4),
                    auto_dismiss=True
                )
                error_popup.open()
                Clock.schedule_once(lambda dt: error_popup.dismiss(), 3)
        
        yes_btn.bind(on_press=delete_confirmed)
        no_btn.bind(on_press=popup.dismiss)
        
        popup.open()