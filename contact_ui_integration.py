# contact_ui_integration.py - UI Integration for Contact Management
"""
This file modifies the existing document_vault_ui.py to properly handle contacts
It replaces the view_selected_document method to show contacts with calling capability
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

def patch_document_vault_ui(document_vault_ui_class):
    """
    Patch the existing DocumentVaultUI class to handle contacts
    Call this after importing DocumentVaultUI but before using it
    """
    
    # Store original method
    original_view_method = document_vault_ui_class.view_selected_document
    
    def enhanced_view_selected_document(self, instance):
        """Enhanced view method that handles contacts with calling"""
        if not self.selected_document:
            self.show_no_selection_message("view")
            return
        
        doc = self.selected_document
        
        # Check if this is a contact file
        file_ext = os.path.splitext(doc['path'].lower())[1]
        
        if file_ext in ['.vcf', '.contact'] and hasattr(self.vault_core.app, 'contact_manager'):
            # Handle contact viewing
            self.show_contact_view(doc)
        else:
            # Use original method for non-contact files
            original_view_method(self, instance)
    
    def show_contact_view(self, doc):
        """Show detailed contact view with calling capability"""
        # Parse the contact file
        contact_data = self.vault_core.app.contact_manager.parse_vcf_contact(doc['path'])
        
        if 'error' in contact_data:
            # Show error popup
            content = Label(
                text=f"❌ Error reading contact file:\n\n{contact_data['error']}\n\nThe file might be corrupted or in an unsupported format."
            )
            popup = Popup(
                title='Contact Read Error',
                content=content,
                size_hint=(0.8, 0.5),
                auto_dismiss=True
            )
            popup.open()
            return
        
        # Create contact display widget
        contact_widget = self.vault_core.app.contact_manager.create_contact_widget(
            contact_data, 
            doc['path']
        )
        
        # Create popup with contact widget
        content = BoxLayout(orientation='vertical', spacing=10)
        
        # Add contact widget to scrollview
        scroll = ScrollView()
        scroll.add_widget(contact_widget)
        content.add_widget(scroll)
        
        # Bottom buttons
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=10
        )
        
        # Quick call button (if has phone)
        if contact_data['phones']:
            primary_phone = contact_data['phones'][0]['number']
            quick_call_btn = Button(
                text=f'📞 Call {primary_phone}',
                background_color=(0.2, 0.8, 0.2, 1),
                size_hint_x=0.4
            )
            quick_call_btn.bind(on_press=lambda x: self.vault_core.app.contact_manager.make_phone_call(primary_phone))
            button_layout.add_widget(quick_call_btn)
        
        # Export button
        export_btn = Button(text='📤 Export Contact', size_hint_x=0.3)
        export_btn.bind(on_press=lambda x: self.export_contact_from_view(doc))
        button_layout.add_widget(export_btn)
        
        # Close button
        close_btn = Button(text='❌ Close', size_hint_x=0.3)
        button_layout.add_widget(close_btn)
        
        content.add_widget(button_layout)
        
        # Create and show popup
        popup = Popup(
            title=f'👤 {contact_data["name"]}',
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
        # Close current popup first
        if hasattr(self, '_current_popup'):
            self._current_popup.dismiss()
        
        # Use existing export functionality
        self.export_selected_document(None)
    
    # Apply the patches to the class
    document_vault_ui_class.view_selected_document = enhanced_view_selected_document
    document_vault_ui_class.show_contact_view = show_contact_view
    document_vault_ui_class.export_contact_from_view = export_contact_from_view
    
    print("✅ DocumentVaultUI patched for contact support")


# Additional helper function to enhance contact creation widget
def create_enhanced_contact_widget(self, document):
    """
    Enhanced version of create_document_widget specifically for contacts
    This replaces the generic document widget when the file is a contact
    """
    import os
    
    layout = BoxLayout(
        orientation='horizontal',
        size_hint_y=None,
        height=dp(80),
        padding=5,
        spacing=10
    )
    
    # Try to parse contact for preview info
    contact_preview = None
    file_ext = os.path.splitext(document['path'].lower())[1]
    
    if file_ext in ['.vcf', '.contact'] and hasattr(self.vault_core.app, 'contact_manager'):
        try:
            contact_data = self.vault_core.app.contact_manager.parse_vcf_contact(document['path'])
            if 'error' not in contact_data:
                contact_preview = contact_data
        except:
            pass
    
    # Contact info layout
    info_layout = BoxLayout(orientation='vertical', size_hint_x=0.6)
    
    # Contact name and basic info
    if contact_preview:
        name_text = f"👤 {contact_preview['name']}"
        phone_count = len(contact_preview['phones'])
        email_count = len(contact_preview['emails'])
        
        details_text = f"📞 {phone_count} phone(s) • 📧 {email_count} email(s)"
        if contact_preview.get('organization'):
            details_text += f" • 🏢 {contact_preview['organization']}"
    else:
        name_text = f"👤 {document['original_name']}"
        details_text = "Contact file"
    
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
    
    full_details = f"{details_text} • {size_text} • {document['modified'].strftime('%Y-%m-%d %H:%M')}"
    
    details_label = Label(
        text=full_details,
        font_size=12,
        halign='left',
        color=(0.7, 0.7, 0.7, 1),
        text_size=(None, None)
    )
    details_label.bind(size=details_label.setter('text_size'))
    info_layout.add_widget(details_label)
    
    layout.add_widget(info_layout)
    
    # Action buttons layout
    button_layout = BoxLayout(orientation='horizontal', size_hint_x=0.4, spacing=5)
    
    # Quick call button (if contact has phone)
    if contact_preview and contact_preview['phones']:
        primary_phone = contact_preview['phones'][0]['number']
        call_btn = Button(
            text='📞',
            size_hint_x=0.2,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        call_btn.bind(on_press=lambda x: self.vault_core.app.contact_manager.make_phone_call(primary_phone))
        button_layout.add_widget(call_btn)
    
    # Select button
    select_btn = Button(
        text='Select',
        size_hint_x=0.3
    )
    select_btn.bind(on_press=lambda x: self.select_document(document))
    button_layout.add_widget(select_btn)
    
    # View button
    view_btn = Button(
        text='👁️',
        size_hint_x=0.2
    )
    view_btn.bind(on_press=lambda x: self.quick_view_document(document))
    button_layout.add_widget(view_btn)
    
    # Export button
    export_btn = Button(
        text='📤',
        size_hint_x=0.2
    )
    export_btn.bind(on_press=lambda x: self.quick_export_document(document))
    button_layout.add_widget(export_btn)
    
    layout.add_widget(button_layout)
    
    return layout


# Main integration function
def integrate_contact_ui_enhancements(document_vault_ui_class):
    """
    Main function to integrate all contact UI enhancements
    Call this after importing DocumentVaultUI
    """
    
    # Patch the main UI class
    patch_document_vault_ui(document_vault_ui_class)
    
    # Store original create_document_widget method
    original_create_widget = document_vault_ui_class.create_document_widget
    
    def enhanced_create_document_widget(self, document):
        """Enhanced widget creator that handles contacts specially"""
        import os
        
        file_ext = os.path.splitext(document['path'].lower())[1]
        
        if file_ext in ['.vcf', '.contact']:
            # Create enhanced contact widget
            return create_enhanced_contact_widget(self, document)
        else:
            # Use original method for non-contact files
            return original_create_widget(self, document)
    
    # Apply the enhancement
    document_vault_ui_class.create_document_widget = enhanced_create_document_widget
    
    print("✅ Contact UI enhancements integrated")
    print("👤 Contact files now show enhanced preview with quick call buttons")


# Usage instructions for main.py
INTEGRATION_INSTRUCTIONS = """
🔧 INTEGRATION INSTRUCTIONS FOR CONTACTS:

1. Add these imports to your main.py (after existing document vault imports):
   ```python
   from contact_manager import integrate_contact_management
   from contact_ui_integration import integrate_contact_ui_enhancements
   from document_vault_ui import DocumentVaultUI
   ```

2. After creating your vault app but before showing the UI, add:
   ```python
   # Integrate contact management
   integrate_contact_management(self)
   
   # Enhance UI for contacts
   integrate_contact_ui_enhancements(DocumentVaultUI)
   ```

3. Add CALL_PHONE permission to your buildozer.spec (Android):
   ```
   android.permissions = ..., android.permission.CALL_PHONE, android.permission.READ_PHONE_STATE
   ```

4. Contact files (.vcf, .contact) will now:
   ✅ Show contact preview with name, phone count, email count
   ✅ Have quick call buttons (📞) for instant calling on Android
   ✅ Display detailed contact view when opened
   ✅ Support calling, emailing, maps integration
   ✅ Work with existing export/import functionality

5. Features available:
   📞 One-tap calling (Android only)
   📧 Email integration
   🗺️ Maps integration for addresses
   📋 Copy to clipboard
   📤 Export contacts
   👁️ Full contact preview
   🔍 Search and filter contacts

6. Security:
   ⚠️ Shows confirmation before making calls
   🔒 Uses secure vault storage
   ♻️ Integrates with recycle bin system
"""

if __name__ == "__main__":
    print(INTEGRATION_INSTRUCTIONS)