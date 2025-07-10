import os
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivy.uix.popup import Popup
from kivy.metrics import dp

def patch_document_vault_ui(document_vault_ui_class):
    """Patch DocumentVaultUI to enhance contact file viewing"""
    original_view_method = document_vault_ui_class.view_selected_document
    
    def view_selected_document(self, instance):
        """Enhanced view method that handles both regular docs and contacts"""
        if not self.selected_document:
            self.components.show_no_selection_message("view")
            return
        
        doc = self.selected_document
        
        # Check if this is a contact file and we have contact manager
        file_ext = os.path.splitext(doc['path'].lower())[1]
        
        if file_ext in ['.vcf', '.contact'] and hasattr(self.vault_core.app, 'contact_manager'):
            self.show_contact_view(doc)
        else:
            # Use original method for non-contact files
            original_view_method(self, instance)
    
    def show_contact_view(self, doc):
        """Show enhanced contact view with calling/emailing capabilities"""
        contact_data = self.vault_core.app.contact_manager.parse_vcf_contact(doc['path'])
        
        if 'error' in contact_data:
            content = MDLabel(
                text=f"Error reading contact file:\n\n{contact_data['error']}\n\nThe file might be corrupted or in an unsupported format.",
                text_color=[1, 0.4, 0.4, 1],
                halign='center'
            )
            popup = Popup(
                title='Contact Read Error',
                content=content,
                size_hint=(0.8, 0.5),
                auto_dismiss=True
            )
            popup.open()
            return
        
        # Create contact display widget using contact manager
        contact_widget = self.vault_core.app.contact_manager.create_contact_widget(
            contact_data, 
            doc['path']
        )
        
        # Create popup content
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=15)
        
        # Add scrollable contact widget
        scroll = MDScrollView()
        scroll.add_widget(contact_widget)
        content.add_widget(scroll)
        
        # Add action buttons
        button_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=10
        )
        
        # Quick call button if contact has phone numbers
        if contact_data['phones']:
            primary_phone = contact_data['phones'][0]['number']
            quick_call_btn = MDRaisedButton(
                text=f'Call {primary_phone}',
                md_bg_color=[0.2, 0.8, 0.2, 1],
                text_color="white",
                size_hint_x=0.4,
                elevation=3
            )
            quick_call_btn.bind(on_press=lambda x: self.vault_core.app.contact_manager.make_phone_call(primary_phone))
            button_layout.add_widget(quick_call_btn)
        
        # Export contact button
        export_btn = MDRaisedButton(
            text='Export Contact',
            md_bg_color=[0.6, 0.4, 0.8, 1],
            text_color="white",
            size_hint_x=0.3,
            elevation=3
        )
        export_btn.bind(on_press=lambda x: self.export_contact_from_view(doc))
        button_layout.add_widget(export_btn)
        
        # Close button
        close_btn = MDRaisedButton(
            text='Close',
            md_bg_color=[0.5, 0.5, 0.5, 1],
            text_color="white",
            size_hint_x=0.3,
            elevation=2
        )
        button_layout.add_widget(close_btn)
        
        content.add_widget(button_layout)
        
        # Create and show popup
        popup = Popup(
            title=f'📞 {contact_data["name"]}',
            content=content,
            size_hint=(0.95, 0.9),
            auto_dismiss=False
        )
        
        def close_popup(instance):
            popup.dismiss()
        
        close_btn.bind(on_press=close_popup)
        popup.open()
    
    def export_contact_from_view(self, doc):
        """Export contact from the view dialog"""
        # Close current popup if exists
        if hasattr(self, '_current_popup'):
            self._current_popup.dismiss()
        
        # Use existing export functionality
        self.selected_document = doc
        self.export_selected_document(None)
    
    # ✅ FIX: Replace the methods in the class with correct names
    document_vault_ui_class.view_selected_document = view_selected_document
    document_vault_ui_class.show_contact_view = show_contact_view
    document_vault_ui_class.export_contact_from_view = export_contact_from_view


def create_enhanced_contact_widget(self, document):
    """Create enhanced widget for contact files with quick actions"""
    doc_card = MDCard(
        orientation='horizontal',
        size_hint_y=None,
        height=dp(80),
        padding=10,
        spacing=10,
        elevation=3,
        md_bg_color=[0.31, 0.35, 0.39, 0.9],
        ripple_behavior=True
    )
    
    # Try to parse contact for preview
    contact_preview = None
    file_ext = os.path.splitext(document['path'].lower())[1]
    
    if file_ext in ['.vcf', '.contact'] and hasattr(self.vault_core.app, 'contact_manager'):
        try:
            contact_data = self.vault_core.app.contact_manager.parse_vcf_contact(document['path'])
            if 'error' not in contact_data:
                contact_preview = contact_data
        except Exception as e:
            print(f"Error parsing contact preview: {e}")
    
    # Left side - Contact info
    info_layout = MDBoxLayout(orientation='vertical', size_hint_x=0.6)
    
    if contact_preview:
        # Use contact name and details
        name_text = f"👤 {contact_preview['name']}"
        phone_count = len(contact_preview['phones'])
        email_count = len(contact_preview['emails'])
        
        details_text = f"{phone_count} phone(s) • {email_count} email(s)"
        if contact_preview.get('organization'):
            details_text += f" • {contact_preview['organization']}"
    else:
        # Fallback to filename
        name_text = f"📄 {document['original_name']}"
        details_text = "Contact file"
    
    name_label = MDLabel(
        text=name_text,
        font_style="Body1",
        text_color="white",
        halign='left'
    )
    name_label.bind(size=name_label.setter('text_size'))
    info_layout.add_widget(name_label)
    
    # File details
    size_mb = document['size'] / (1024 * 1024)
    size_text = f"{size_mb:.1f} MB" if size_mb >= 0.1 else f"{document['size']} bytes"
    
    full_details = f"{details_text} • {size_text} • {document['modified'].strftime('%Y-%m-%d %H:%M')}"
    
    details_label = MDLabel(
        text=full_details,
        font_style="Caption",
        halign='left',
        text_color=[0.7, 0.7, 0.7, 1]
    )
    details_label.bind(size=details_label.setter('text_size'))
    info_layout.add_widget(details_label)
    
    doc_card.add_widget(info_layout)
    
    # Right side - Action buttons
    button_layout = MDBoxLayout(orientation='horizontal', size_hint_x=0.4, spacing=5)
    
    # Quick call button for contacts with phone numbers
    if contact_preview and contact_preview['phones']:
        primary_phone = contact_preview['phones'][0]['number']
        call_btn = MDRaisedButton(
            text='📞',
            size_hint_x=0.2,
            md_bg_color=[0.2, 0.8, 0.2, 1],
            text_color="white",
            elevation=3
        )
        call_btn.bind(on_press=lambda x: self.vault_core.app.contact_manager.make_phone_call(primary_phone))
        button_layout.add_widget(call_btn)
    
    # Select button
    select_btn = MDRaisedButton(
        text='Select',
        size_hint_x=0.3,
        md_bg_color=[0.2, 0.6, 0.8, 1],
        text_color="white",
        elevation=2
    )
    select_btn.bind(on_press=lambda x: self.select_document(document))
    button_layout.add_widget(select_btn)
    
    # View button
    view_btn = MDFlatButton(
        text='View',
        size_hint_x=0.25,
        text_color=[0.4, 0.8, 0.9, 1]
    )
    view_btn.bind(on_press=lambda x: self.quick_view_document(document))
    button_layout.add_widget(view_btn)
    
    # Export button
    export_btn = MDFlatButton(
        text='Export',
        size_hint_x=0.25,
        text_color=[0.6, 0.6, 0.9, 1]
    )
    export_btn.bind(on_press=lambda x: self.quick_export_document(document))
    button_layout.add_widget(export_btn)
    
    doc_card.add_widget(button_layout)
    
    return doc_card


def integrate_contact_ui_enhancements(document_vault_ui_class):
    """Main integration function - enhances DocumentVaultUI for contacts"""
    
    print("🔧 Integrating contact UI enhancements...")
    
    # Step 1: Patch the view method to handle contacts
    patch_document_vault_ui(document_vault_ui_class)
    
    # Step 2: Enhance the document widget creation for contacts
    original_create_widget = document_vault_ui_class.create_document_widget
    
    def create_document_widget(self, document):
        """Enhanced document widget creation that detects contact files"""
        file_ext = os.path.splitext(document['path'].lower())[1]
        
        # Use enhanced widget for contact files
        if file_ext in ['.vcf', '.contact']:
            return create_enhanced_contact_widget(self, document)
        else:
            # Use original widget for non-contact files
            return original_create_widget(self, document)
    
    # Replace the method
    document_vault_ui_class.create_document_widget = create_document_widget
    
    print("✅ Contact UI enhancements integrated successfully")

if __name__ == "__main__":
    print("📞 Contact UI Integration Module")