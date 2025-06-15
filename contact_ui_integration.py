import os
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivy.uix.popup import Popup
from kivy.metrics import dp

def patch_document_vault_ui(document_vault_ui_class):
    original_view_method = document_vault_ui_class.view_selected_document
    
    def enhanced_view_selected_document(self, instance):
        if not self.selected_document:
            self.components.show_no_selection_message("view")
            return
        
        doc = self.selected_document
        
        file_ext = os.path.splitext(doc['path'].lower())[1]
        
        if file_ext in ['.vcf', '.contact'] and hasattr(self.vault_core.app, 'contact_manager'):
            self.show_contact_view(doc)
        else:
            original_view_method(self, instance)
    
    def show_contact_view(self, doc):
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
        
        contact_widget = self.vault_core.app.contact_manager.create_contact_widget(
            contact_data, 
            doc['path']
        )
        
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=15)
        
        scroll = MDScrollView()
        scroll.add_widget(contact_widget)
        content.add_widget(scroll)
        
        button_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=10
        )
        
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
        
        export_btn = MDRaisedButton(
            text='Export Contact',
            md_bg_color=[0.6, 0.4, 0.8, 1],
            text_color="white",
            size_hint_x=0.3,
            elevation=3
        )
        export_btn.bind(on_press=lambda x: self.export_contact_from_view(doc))
        button_layout.add_widget(export_btn)
        
        close_btn = MDRaisedButton(
            text='Close',
            md_bg_color=[0.5, 0.5, 0.5, 1],
            text_color="white",
            size_hint_x=0.3,
            elevation=2
        )
        button_layout.add_widget(close_btn)
        
        content.add_widget(button_layout)
        
        popup = Popup(
            title=f'{contact_data["name"]}',
            content=content,
            size_hint=(0.95, 0.9),
            auto_dismiss=False
        )
        
        def close_popup(instance):
            popup.dismiss()
        
        close_btn.bind(on_press=close_popup)
        popup.open()
    
    def export_contact_from_view(self, doc):
        if hasattr(self, '_current_popup'):
            self._current_popup.dismiss()
        
        self.export_selected_document(None)
    
    document_vault_ui_class.view_selected_document = enhanced_view_selected_document
    document_vault_ui_class.show_contact_view = show_contact_view
    document_vault_ui_class.export_contact_from_view = export_contact_from_view
    
    print("DocumentVaultUI patched for contact support")


def create_enhanced_contact_widget(self, document):
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
    
    contact_preview = None
    file_ext = os.path.splitext(document['path'].lower())[1]
    
    if file_ext in ['.vcf', '.contact'] and hasattr(self.vault_core.app, 'contact_manager'):
        try:
            contact_data = self.vault_core.app.contact_manager.parse_vcf_contact(document['path'])
            if 'error' not in contact_data:
                contact_preview = contact_data
        except:
            pass
    
    info_layout = MDBoxLayout(orientation='vertical', size_hint_x=0.6)
    
    if contact_preview:
        name_text = contact_preview['name']
        phone_count = len(contact_preview['phones'])
        email_count = len(contact_preview['emails'])
        
        details_text = f"{phone_count} phone(s) • {email_count} email(s)"
        if contact_preview.get('organization'):
            details_text += f" • {contact_preview['organization']}"
    else:
        name_text = document['original_name']
        details_text = "Contact file"
    
    name_label = MDLabel(
        text=name_text,
        font_style="Body1",
        text_color="white",
        halign='left'
    )
    name_label.bind(size=name_label.setter('text_size'))
    info_layout.add_widget(name_label)
    
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
    
    button_layout = MDBoxLayout(orientation='horizontal', size_hint_x=0.4, spacing=5)
    
    if contact_preview and contact_preview['phones']:
        primary_phone = contact_preview['phones'][0]['number']
        call_btn = MDRaisedButton(
            text='Call',
            size_hint_x=0.2,
            md_bg_color=[0.2, 0.8, 0.2, 1],
            text_color="white",
            elevation=3
        )
        call_btn.bind(on_press=lambda x: self.vault_core.app.contact_manager.make_phone_call(primary_phone))
        button_layout.add_widget(call_btn)
    
    select_btn = MDRaisedButton(
        text='Select',
        size_hint_x=0.3,
        md_bg_color=[0.2, 0.6, 0.8, 1],
        text_color="white",
        elevation=2
    )
    select_btn.bind(on_press=lambda x: self.select_document(document))
    button_layout.add_widget(select_btn)
    
    view_btn = MDFlatButton(
        text='View',
        size_hint_x=0.2,
        text_color=[0.4, 0.8, 0.9, 1]
    )
    view_btn.bind(on_press=lambda x: self.quick_view_document(document))
    button_layout.add_widget(view_btn)
    
    export_btn = MDFlatButton(
        text='Export',
        size_hint_x=0.2,
        text_color=[0.6, 0.6, 0.9, 1]
    )
    export_btn.bind(on_press=lambda x: self.quick_export_document(document))
    button_layout.add_widget(export_btn)
    
    doc_card.add_widget(button_layout)
    
    return doc_card


def integrate_contact_ui_enhancements(document_vault_ui_class):
    patch_document_vault_ui(document_vault_ui_class)
    
    original_create_widget = document_vault_ui_class.create_document_widget
    
    def enhanced_create_document_widget(self, document):
        file_ext = os.path.splitext(document['path'].lower())[1]
        
        if file_ext in ['.vcf', '.contact']:
            return create_enhanced_contact_widget(self, document)
        else:
            return original_create_widget(self, document)
    
    document_vault_ui_class.create_document_widget = enhanced_create_document_widget
    
    print("Contact UI enhancements integrated")
    print("Contact files now show enhanced preview with quick call buttons")


INTEGRATION_INSTRUCTIONS = """
INTEGRATION INSTRUCTIONS FOR CONTACTS:

1. Add these imports to your main.py (after existing document vault imports):
   ```python
   from contact_manager import integrate_contact_management
   from contact_ui_integration import integrate_contact_ui_enhancements
   from document_vault_ui import DocumentVaultUI
   ```

2. After creating your vault app but before showing the UI, add:
   ```python
   integrate_contact_management(self)
   
   integrate_contact_ui_enhancements(DocumentVaultUI)
   ```

3. Add CALL_PHONE permission to your buildozer.spec (Android):
   ```
   android.permissions = ..., android.permission.CALL_PHONE, android.permission.READ_PHONE_STATE
   ```

4. Contact files (.vcf, .contact) will now:
   Show contact preview with name, phone count, email count
   Have quick call buttons for instant calling on Android
   Display detailed contact view when opened
   Support calling, emailing, maps integration
   Work with existing export/import functionality

5. Features available:
   One-tap calling (Android only)
   Email integration
   Maps integration for addresses
   Copy to clipboard
   Export contacts
   Full contact preview
   Search and filter contacts

6. Security:
   Shows confirmation before making calls
   Uses secure vault storage
   Integrates with recycle bin system
"""

if __name__ == "__main__":
    print(INTEGRATION_INSTRUCTIONS)
