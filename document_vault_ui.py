import os
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.metrics import dp

class DocumentVaultUI(BoxLayout):
    """
    Universal Document Vault UI
    
    Features:
    - View-only document management
    - Category filtering
    - File preview for text files
    - Export functionality
    - Cross-platform compatible
    """
    
    def __init__(self, document_vault_core, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.vault_core = document_vault_core
        self.current_filter = None  # None = show all
        self.selected_document = None
        self.document_widgets = []
        
        self.build_ui()
        
        # Load documents after a short delay
        Clock.schedule_once(lambda dt: self.refresh_documents(), 0.1)
    
    def build_ui(self):
        """Build the main UI layout"""
        # Header with title and controls
        self.build_header()
        
        # Category filter tabs
        self.build_category_filter()
        
        # Document list in scroll view
        self.build_document_list()
        
        # Bottom action buttons
        self.build_bottom_buttons()
    
    def build_header(self):
        """Build header with title and add button"""
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), padding=10)
        
        title = Label(
            text='📁 Document Vault',
            font_size=24,
            size_hint_x=0.6,
            halign='left'
        )
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)
        
        # Stats display
        self.stats_label = Label(
            text='Loading...',
            font_size=14,
            size_hint_x=0.2,
            halign='center'
        )
        self.stats_label.bind(size=self.stats_label.setter('text_size'))
        header.add_widget(self.stats_label)
        
        # Add documents button
        self.add_btn = Button(
            text='+ Add Files',
            font_size=16,
            size_hint_x=0.2
        )
        self.add_btn.bind(on_press=self.add_documents)
        header.add_widget(self.add_btn)
        
        self.add_widget(header)
    
    def build_category_filter(self):
        """Build category filter buttons"""
        filter_scroll = ScrollView(
            size_hint_y=None,
            height=dp(60),
            do_scroll_x=True,
            do_scroll_y=False
        )
        
        filter_layout = BoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            height=dp(50),
            spacing=5,
            padding=[10, 5]
        )
        filter_layout.bind(minimum_width=filter_layout.setter('width'))
        
        # All files button
        all_btn = Button(
            text='📋 All Files',
            size_hint_x=None,
            width=dp(100),
            height=dp(40)
        )
        all_btn.bind(on_press=lambda x: self.filter_by_category(None))
        filter_layout.add_widget(all_btn)
        
        # Category buttons
        for category, config in self.vault_core.FILE_CATEGORIES.items():
            if category == 'other':  # Skip 'other' for now, add at end
                continue
                
            btn_text = f"{config['icon']} {config['display_name']}"
            btn = Button(
                text=btn_text,
                size_hint_x=None,
                width=dp(120),
                height=dp(40)
            )
            btn.bind(on_press=lambda x, cat=category: self.filter_by_category(cat))
            filter_layout.add_widget(btn)
        
        # Other files button (at the end)
        other_config = self.vault_core.FILE_CATEGORIES['other']
        other_btn = Button(
            text=f"{other_config['icon']} {other_config['display_name']}",
            size_hint_x=None,
            width=dp(100),
            height=dp(40)
        )
        other_btn.bind(on_press=lambda x: self.filter_by_category('other'))
        filter_layout.add_widget(other_btn)
        
        filter_scroll.add_widget(filter_layout)
        self.add_widget(filter_scroll)
    
    def build_document_list(self):
        """Build scrollable document list"""
        scroll = ScrollView()
        
        self.document_grid = GridLayout(
            cols=1,
            spacing=5,
            padding=10,
            size_hint_y=None
        )
        self.document_grid.bind(minimum_height=self.document_grid.setter('height'))
        
        scroll.add_widget(self.document_grid)
        self.add_widget(scroll)
    
    def build_bottom_buttons(self):
        """Build bottom action buttons"""
        bottom_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=10,
            spacing=5
        )
        
        # Refresh button
        refresh_btn = Button(text='🔄 Refresh', size_hint_x=0.2)
        refresh_btn.bind(on_press=lambda x: self.refresh_documents())
        bottom_layout.add_widget(refresh_btn)
        
        # View selected button
        self.view_btn = Button(text='👁️ View', size_hint_x=0.2)
        self.view_btn.bind(on_press=self.view_selected_document)
        bottom_layout.add_widget(self.view_btn)
        
        # Export selected button
        self.export_btn = Button(text='📤 Export', size_hint_x=0.2)
        self.export_btn.bind(on_press=self.export_selected_document)
        bottom_layout.add_widget(self.export_btn)
        
        # Delete selected button
        self.delete_btn = Button(text='🗑️ Delete', size_hint_x=0.2)
        self.delete_btn.bind(on_press=self.delete_selected_document)
        bottom_layout.add_widget(self.delete_btn)
        
        # Back to vault button
        back_btn = Button(text='⬅️ Back', size_hint_x=0.2)
        back_btn.bind(on_press=self.back_to_vault)
        bottom_layout.add_widget(back_btn)
        
        self.add_widget(bottom_layout)
    
    def filter_by_category(self, category):
        """Filter documents by category"""
        self.current_filter = category
        self.selected_document = None
        self.refresh_documents()
    
    def add_documents(self, instance):
        """Handle add documents button press"""
        if self.vault_core.processing:
            return
        
        # Disable button during processing
        self.add_btn.disabled = True
        self.add_btn.text = 'Processing...'
        
        self.vault_core.request_permissions()
        
        def on_documents_added(imported_files, skipped_files):
            # Re-enable button
            self.add_btn.disabled = False
            self.add_btn.text = '+ Add Files'
            
            # Show results
            self.show_import_results(imported_files, skipped_files)
            
            # Refresh document list
            if imported_files:
                self.refresh_documents()
        
        self.vault_core.select_documents_from_storage(on_documents_added)
    
    def show_import_results(self, imported_files, skipped_files):
        """Show import results popup"""
        content = BoxLayout(orientation='vertical', spacing=10)
        
        # Success message
        if imported_files:
            success_text = f"✅ Successfully imported {len(imported_files)} file(s):\n\n"
            for file_info in imported_files[:5]:  # Show first 5
                success_text += f"• {file_info['original_name']} ({file_info['category']})\n"
            
            if len(imported_files) > 5:
                success_text += f"... and {len(imported_files) - 5} more files"
            
            success_label = Label(
                text=success_text,
                text_size=(None, None),
                halign='left'
            )
            content.add_widget(success_label)
        
        # Skipped files message
        if skipped_files:
            skipped_text = f"\n⚠️ Skipped {len(skipped_files)} file(s):\n"
            for skipped in skipped_files[:3]:  # Show first 3
                skipped_text += f"• {skipped}\n"
            
            if len(skipped_files) > 3:
                skipped_text += f"... and {len(skipped_files) - 3} more"
            
            skipped_label = Label(
                text=skipped_text,
                text_size=(None, None),
                halign='left'
            )
            content.add_widget(skipped_label)
        
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
        
        # Auto-dismiss after 5 seconds if successful
        if imported_files and not skipped_files:
            Clock.schedule_once(lambda dt: popup.dismiss(), 5)
    
    def refresh_documents(self):
        """Refresh the document list"""
        # Clear existing widgets
        self.cleanup_document_widgets()
        self.document_grid.clear_widgets()
        self.selected_document = None
        
        # Get documents
        documents = self.vault_core.get_vault_documents(self.current_filter)
        
        # Update stats
        self.update_stats_display(documents)
        
        if not documents:
            # Show empty state
            if self.current_filter:
                category_name = self.vault_core.FILE_CATEGORIES[self.current_filter]['display_name']
                empty_text = f'No {category_name.lower()} in vault\nTap "Add Files" to get started'
            else:
                empty_text = 'No documents in vault\nTap "Add Files" to get started'
            
            empty_label = Label(
                text=empty_text,
                font_size=18,
                halign='center'
            )
            self.document_grid.add_widget(empty_label)
            return
        
        # Load documents
        for doc in documents:
            doc_widget = self.create_document_widget(doc)
            self.document_grid.add_widget(doc_widget)
            self.document_widgets.append(doc_widget)
    
    def update_stats_display(self, documents):
        """Update the stats display in header"""
        try:
            if self.current_filter:
                category_name = self.vault_core.FILE_CATEGORIES[self.current_filter]['display_name']
                total_size = sum(doc['size'] for doc in documents) / (1024 * 1024)
                self.stats_label.text = f"{len(documents)} {category_name}\n{total_size:.1f} MB"
            else:
                # Show total stats
                total_size = sum(doc['size'] for doc in documents) / (1024 * 1024)
                self.stats_label.text = f"{len(documents)} files\n{total_size:.1f} MB"
        except:
            self.stats_label.text = f"{len(documents)} files"
    
    def cleanup_document_widgets(self):
        """Clean up document widgets"""
        self.document_widgets.clear()
    
    def create_document_widget(self, document):
        """Create a widget for displaying a document"""
        layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(80),
            padding=5,
            spacing=10
        )
        
        # Category icon and file info
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.7)
        
        # File name and category
        category_info = document['category_info']
        name_text = f"{category_info['icon']} {document['original_name']}"
        
        name_label = Label(
            text=name_text,
            font_size=16,
            halign='left',
            text_size=(None, None)
        )
        name_label.bind(size=name_label.setter('text_size'))
        info_layout.add_widget(name_label)
        
        # File details
        size_mb = document['size'] / (1024 * 1024)
        size_text = f"{size_mb:.1f} MB" if size_mb >= 0.1 else f"{document['size']} bytes"
        
        details_text = f"{category_info['display_name']} • {size_text} • {document['modified'].strftime('%Y-%m-%d %H:%M')}"
        
        details_label = Label(
            text=details_text,
            font_size=12,
            halign='left',
            color=(0.7, 0.7, 0.7, 1),
            text_size=(None, None)
        )
        details_label.bind(size=details_label.setter('text_size'))
        info_layout.add_widget(details_label)
        
        layout.add_widget(info_layout)
        
        # Action buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_x=0.3, spacing=5)
        
        # Select button
        select_btn = Button(
            text='Select',
            size_hint_x=0.5
        )
        select_btn.bind(on_press=lambda x: self.select_document(document))
        button_layout.add_widget(select_btn)
        
        # Quick view button
        view_btn = Button(
            text='👁️',
            size_hint_x=0.25
        )
        view_btn.bind(on_press=lambda x: self.quick_view_document(document))
        button_layout.add_widget(view_btn)
        
        # Quick export button
        export_btn = Button(
            text='📤',
            size_hint_x=0.25
        )
        export_btn.bind(on_press=lambda x: self.quick_export_document(document))
        button_layout.add_widget(export_btn)
        
        layout.add_widget(button_layout)
        
        return layout
    
    def select_document(self, document):
        """Select a document"""
        self.selected_document = document
        
        # Show selection feedback
        content = Label(
            text=f"Selected: {document['original_name']}\n\nCategory: {document['category_info']['display_name']}\nSize: {document['size'] / (1024 * 1024):.1f} MB\n\nUse the buttons below to view, export, or delete this file."
        )
        
        popup = Popup(
            title='Document Selected',
            content=content,
            size_hint=(0.7, 0.5),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def quick_view_document(self, document):
        """Quick view document"""
        self.selected_document = document
        self.view_selected_document(None)
    
    def quick_export_document(self, document):
        """Quick export document using folder selection"""
        self.selected_document = document
        self.export_selected_document(None)
    
    def view_selected_document(self, instance):
        """View the selected document"""
        if not self.selected_document:
            self.show_no_selection_message("view")
            return
        
        doc = self.selected_document
        
        # Get document preview
        preview_result = self.vault_core.get_document_preview(doc['path'])
        
        content = BoxLayout(orientation='vertical', spacing=10)
        
        # Document info header
        info_text = f"📄 {doc['original_name']}\n"
        info_text += f"Category: {doc['category_info']['display_name']}\n"
        info_text += f"Size: {doc['size'] / (1024 * 1024):.1f} MB\n"
        info_text += f"Modified: {doc['modified'].strftime('%Y-%m-%d %H:%M:%S')}"
        
        info_label = Label(
            text=info_text,
            font_size=14,
            size_hint_y=None,
            height=dp(100),
            halign='left'
        )
        info_label.bind(size=info_label.setter('text_size'))
        content.add_widget(info_label)
        
        # Preview content or message
        if preview_result['preview_available'] and preview_result['success']:
            preview_scroll = ScrollView(size_hint_y=0.7)
            
            preview_text = preview_result['content']
            if preview_result['truncated']:
                preview_text += f"\n\n... (showing first {preview_result.get('total_lines', 20)} lines)"
            
            preview_input = TextInput(
                text=preview_text,
                readonly=True,
                font_size=12,
                font_name='RobotoMono-Regular'  # Monospace font for code
            )
            
            preview_scroll.add_widget(preview_input)
            content.add_widget(preview_scroll)
            
        else:
            # No preview available
            no_preview_label = Label(
                text=f"📋 Preview not available for this file type\n\n{doc['category_info']['description']}\n\nTo view this file, export it and open with an appropriate application.",
                halign='center',
                size_hint_y=0.7
            )
            no_preview_label.bind(size=no_preview_label.setter('text_size'))
            content.add_widget(no_preview_label)
        
        # Buttons
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=10
        )
        
        export_btn = Button(text='📤 Export File')
        close_btn = Button(text='❌ Close')
        
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
            self.export_selected_document(None)
        
        export_btn.bind(on_press=export_from_view)
        close_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def export_selected_document(self, instance):
        """Export the selected document with folder selection"""
        if not self.selected_document:
            self.show_no_selection_message("export")
            return
        
        doc = self.selected_document
        
        # Show initial export dialog
        content = BoxLayout(orientation='vertical', spacing=10)
        
        info_label = Label(
            text=f"Export '{doc['original_name']}' to device storage?\n\nYou will be asked to choose the destination folder."
        )
        content.add_widget(info_label)
        
        button_layout = BoxLayout(orientation='horizontal')
        
        choose_btn = Button(text='📁 Choose Folder & Export')
        cancel_btn = Button(text='❌ Cancel')
        
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
        """Choose folder and perform export"""
        def on_folder_selected(result):
            if result['success']:
                folder_path = result['folder_path']
                is_fallback = result.get('is_fallback', False)
                
                # Perform export
                export_result = self.vault_core.export_document(doc['path'], folder_path)
                
                if export_result['success']:
                    # Success message with location
                    success_text = f"✅ Document exported successfully!\n\n"
                    success_text += f"📄 File: {export_result['original_name']}\n"
                    success_text += f"📁 Location: {export_result['export_path']}\n\n"
                    
                    if is_fallback:
                        success_text += "⚠️ Used app storage as destination\n"
                    
                    success_text += "You can now open it with any compatible application."
                    
                    self.show_export_result(success_text, "Export Successful", True)
                else:
                    self.handle_export_error(export_result, doc)
            else:
                # Folder selection failed
                error_text = f"❌ Folder selection failed!\n\nError: {result['error']}\n\nPlease try again."
                self.show_export_result(error_text, "Folder Selection Failed", False, doc)
        
        # Start folder selection
        self.vault_core.select_export_folder(on_folder_selected)

    def handle_export_error(self, export_result, doc):
        """Handle export errors with retry option"""
        if export_result.get('needs_folder_selection'):
            error_text = f"❌ Export failed!\n\nError: {export_result['error']}\n\nWould you like to try with a different folder?"
            self.show_export_result(error_text, "Export Failed", False, doc)
        else:
            error_text = f"❌ Export failed!\n\nError: {export_result['error']}"
            self.show_export_result(error_text, "Export Failed", False, None)

    def show_export_result(self, message, title, is_success, retry_doc=None):
        """Show export result with optional retry"""
        content = BoxLayout(orientation='vertical', spacing=10)
        
        result_label = Label(text=message)
        content.add_widget(result_label)
        
        button_layout = BoxLayout(orientation='horizontal')
        
        if retry_doc and not is_success:
            # Add retry button for failures
            retry_btn = Button(text='🔄 Try Different Folder')
            button_layout.add_widget(retry_btn)
            
            def retry_export(instance):
                popup.dismiss()
                self.choose_folder_and_export(retry_doc)
            
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
    
    def delete_selected_document(self, instance):
        """Delete the selected document"""
        if not self.selected_document:
            self.show_no_selection_message("delete")
            return
        
        doc = self.selected_document
        
        # Get retention days from recycle bin config
        retention_days = 45  # Default for documents
        if hasattr(self.vault_core.app, 'recycle_bin'):
            retention_days = self.vault_core.app.recycle_bin.FILE_TYPE_CONFIG['documents']['retention_days']
        
        content = BoxLayout(orientation='vertical', spacing=10)
        
        label = Label(
            text=f'Move this document to recycle bin?\n\n📄 {doc["original_name"]}\n\n♻️ You can restore it within {retention_days} days\n🗑️ It will be auto-deleted after {retention_days} days\n\nThis is much safer than permanent deletion!'
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
            if self.vault_core.delete_document(doc['path']):
                self.refresh_documents()
                popup.dismiss()
                
                success_content = Label(
                    text=f'Document moved to recycle bin successfully!\n\n♻️ You can restore it anytime from the vault menu.\n🕒 It will be kept for {retention_days} days.'
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
                    text='Could not move document to recycle bin.\nPlease try again.'
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
    
    def show_no_selection_message(self, action):
        """Show message when no document is selected"""
        content = Label(text=f'Please select a document first by tapping "Select" on any file')
        popup = Popup(
            title=f'No Document Selected',
            content=content,
            size_hint=(0.7, 0.3),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def back_to_vault(self, instance):
        """Go back to main vault screen"""
        # Clean up before leaving
        self.cleanup_document_widgets()
        
        # Navigate back
        if hasattr(self.vault_core.app, 'show_vault_main'):
            self.vault_core.app.show_vault_main()


# Integration helper function
def integrate_document_vault(vault_app):
    """Helper function to integrate document vault into the main app"""
    from document_vault_core import DocumentVaultCore
    
    vault_app.document_vault = DocumentVaultCore(vault_app)
    
    def show_document_vault():
        """Show the document vault"""
        vault_app.main_layout.clear_widgets()
        
        # Create document vault UI
        document_ui = DocumentVaultUI(vault_app.document_vault)
        vault_app.main_layout.add_widget(document_ui)
        
        # Store reference for navigation
        vault_app.current_screen = 'document_vault'
    
    # Add method to vault app
    vault_app.show_document_vault = show_document_vault
    
    return vault_app.document_vault

print("✅ Universal Document Vault UI loaded successfully")
print("🎨 Features: View-only, category filtering, text preview, export")
print("🌐 Cross-platform compatible UI components")