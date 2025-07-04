import re
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
import webbrowser
import tkinter as tk

# Desktop-only version - All Android code removed
ANDROID = False

class ContactManager:
    
    def __init__(self, vault_app):
        self.app = vault_app
        # No permissions needed on desktop
        print("📞 Desktop mode - no permissions required")
    
    def parse_vcf_contact(self, file_path):

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try different encodings for older VCF files
            encodings = ['latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return {'error': 'Could not decode VCF file'}
        
        contact = {
            'name': '',
            'phones': [],
            'emails': [],
            'organization': '',
            'title': '',
            'addresses': [],
            'notes': '',
            'birthday': '',
            'website': '',
            'photo': None,
            'raw_content': content
        }
        
        try:
            # Parse VCF fields
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Name fields
                if line.startswith('FN:'):
                    contact['name'] = line[3:].strip()
                elif line.startswith('N:'):
                    # Parse structured name (Family;Given;Middle;Prefix;Suffix)
                    name_parts = line[2:].split(';')
                    if len(name_parts) >= 2 and not contact['name']:
                        given = name_parts[1].strip()
                        family = name_parts[0].strip()
                        contact['name'] = f"{given} {family}".strip()
                
                # Phone numbers
                elif line.startswith('TEL'):
                    phone_info = self.parse_phone_line(line)
                    if phone_info:
                        contact['phones'].append(phone_info)
                
                # Email addresses
                elif line.startswith('EMAIL'):
                    email_info = self.parse_email_line(line)
                    if email_info:
                        contact['emails'].append(email_info)
                
                # Organization
                elif line.startswith('ORG:'):
                    contact['organization'] = line[4:].strip()
                elif line.startswith('TITLE:'):
                    contact['title'] = line[6:].strip()
                
                # Address
                elif line.startswith('ADR'):
                    address_info = self.parse_address_line(line)
                    if address_info:
                        contact['addresses'].append(address_info)
                
                # Other fields
                elif line.startswith('NOTE:'):
                    contact['notes'] = line[5:].strip()
                elif line.startswith('BDAY:'):
                    contact['birthday'] = line[5:].strip()
                elif line.startswith('URL:'):
                    contact['website'] = line[4:].strip()
            
            # Ensure we have at least a name
            if not contact['name'] and contact['phones']:
                contact['name'] = contact['phones'][0]['number']
            elif not contact['name']:
                contact['name'] = 'Unknown Contact'
            
            return contact
            
        except Exception as e:
            print(f"Error parsing VCF: {e}")
            return {'error': str(e)}
    
    def parse_phone_line(self, line):
        """Parse TEL line from VCF"""
        try:
            # Extract phone type and number
            if ':' not in line:
                return None
            
            type_part, number = line.split(':', 1)
            
            # Parse type attributes
            phone_type = 'Other'
            if 'CELL' in type_part or 'MOBILE' in type_part:
                phone_type = 'Mobile'
            elif 'HOME' in type_part:
                phone_type = 'Home'
            elif 'WORK' in type_part:
                phone_type = 'Work'
            elif 'FAX' in type_part:
                phone_type = 'Fax'
            
            # Clean phone number
            clean_number = re.sub(r'[^\d+\-\(\)\s]', '', number.strip())
            
            return {
                'number': clean_number,
                'type': phone_type,
                'raw': number.strip()
            }
        except:
            return None
    
    def parse_email_line(self, line):
        """Parse EMAIL line from VCF"""
        try:
            if ':' not in line:
                return None
            
            type_part, email = line.split(':', 1)
            
            # Parse email type
            email_type = 'Other'
            if 'HOME' in type_part:
                email_type = 'Home'
            elif 'WORK' in type_part:
                email_type = 'Work'
            
            return {
                'address': email.strip(),
                'type': email_type
            }
        except:
            return None
    
    def parse_address_line(self, line):
        """Parse ADR line from VCF"""
        try:
            if ':' not in line:
                return None
            
            type_part, address = line.split(':', 1)
            
            # Parse address type
            addr_type = 'Other'
            if 'HOME' in type_part:
                addr_type = 'Home'
            elif 'WORK' in type_part:
                addr_type = 'Work'
            
            # VCF address format: ;;Street;City;State;PostalCode;Country
            addr_parts = address.split(';')
            
            # Build readable address
            readable_parts = []
            if len(addr_parts) > 2 and addr_parts[2]:  # Street
                readable_parts.append(addr_parts[2])
            if len(addr_parts) > 3 and addr_parts[3]:  # City
                readable_parts.append(addr_parts[3])
            if len(addr_parts) > 4 and addr_parts[4]:  # State
                readable_parts.append(addr_parts[4])
            if len(addr_parts) > 5 and addr_parts[5]:  # Postal Code
                readable_parts.append(addr_parts[5])
            if len(addr_parts) > 6 and addr_parts[6]:  # Country
                readable_parts.append(addr_parts[6])
            
            readable_address = ', '.join(readable_parts)
            
            return {
                'address': readable_address,
                'type': addr_type,
                'raw': address
            }
        except:
            return None
    
    def make_phone_call(self, phone_number):
        """
        Open phone app or show phone number (Desktop version)
        """
        # Clean phone number
        clean_number = re.sub(r'[^\d+]', '', phone_number)
        
        if not clean_number:
            self.show_error_popup("Invalid phone number")
            return
        
        # Try to open with tel: protocol, fallback to showing number
        try:
            webbrowser.open(f"tel:{phone_number}")
            self.show_toast(f"Opening phone app for: {phone_number}")
        except Exception as e:
            print(f"Could not open phone app: {e}")
            self.show_desktop_call_message(phone_number)
    
    def show_desktop_call_message(self, phone_number):
        """Show message for desktop users"""
        content = Label(
            text=f"📞 Call: {phone_number}\n\nThis is a desktop application.\n\nTo make the call:\n• Use your phone to dial this number\n• Copy the number and use a VoIP app\n• Use Skype or other calling software"
        )
        
        popup = Popup(
            title='Desktop Call Info',
            content=content,
            size_hint=(0.7, 0.4),
            auto_dismiss=True
        )
        popup.open()
    
    def show_error_popup(self, message):
        """Show error popup"""
        content = Label(text=message)
        popup = Popup(
            title='Error',
            content=content,
            size_hint=(0.7, 0.4),
            auto_dismiss=True
        )
        popup.open()
    
    def create_contact_widget(self, contact_data, file_path):
        """Create a comprehensive contact display widget"""
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Contact header
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
        
        # Name and basic info
        name_layout = BoxLayout(orientation='vertical', size_hint_x=0.7)
        
        name_label = Label(
            text=f"👤 {contact_data['name']}",
            font_size=20,
            bold=True,
            halign='left',
            size_hint_y=None,
            height=dp(30)
        )
        name_label.bind(size=name_label.setter('text_size'))
        name_layout.add_widget(name_label)
        
        # Organization info
        if contact_data.get('organization') or contact_data.get('title'):
            org_text = []
            if contact_data.get('title'):
                org_text.append(contact_data['title'])
            if contact_data.get('organization'):
                org_text.append(contact_data['organization'])
            
            org_label = Label(
                text=' • '.join(org_text),
                font_size=14,
                color=(0.7, 0.7, 0.7, 1),
                halign='left',
                size_hint_y=None,
                height=dp(25)
            )
            org_label.bind(size=org_label.setter('text_size'))
            name_layout.add_widget(org_label)
        
        header_layout.add_widget(name_layout)
        
        # Export button
        export_btn = Button(
            text='📤\nExport',
            size_hint_x=0.15,
            font_size=12
        )
        export_btn.bind(on_press=lambda x: self.export_contact(file_path, contact_data['name']))
        header_layout.add_widget(export_btn)
        
        # Edit button (placeholder for future)
        edit_btn = Button(
            text='✏️\nEdit',
            size_hint_x=0.15,
            font_size=12
        )
        edit_btn.bind(on_press=lambda x: self.show_edit_placeholder())
        header_layout.add_widget(edit_btn)
        
        main_layout.add_widget(header_layout)
        
        # Contact details in scroll view
        scroll = ScrollView()
        details_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        details_layout.bind(minimum_height=details_layout.setter('height'))
        
        # Phone numbers section
        if contact_data['phones']:
            phone_header = Label(
                text='📞 Phone Numbers',
                font_size=16,
                bold=True,
                halign='left',
                size_hint_y=None,
                height=dp(30)
            )
            phone_header.bind(size=phone_header.setter('text_size'))
            details_layout.add_widget(phone_header)
            
            for phone in contact_data['phones']:
                phone_layout = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=dp(40),
                    spacing=10
                )
                
                # Phone info
                phone_info = Label(
                    text=f"{phone['type']}: {phone['number']}",
                    font_size=14,
                    halign='left',
                    size_hint_x=0.7
                )
                phone_info.bind(size=phone_info.setter('text_size'))
                phone_layout.add_widget(phone_info)
                
                # Call button
                call_btn = Button(
                    text='📞 Call',
                    size_hint_x=0.15,
                    background_color=(0.2, 0.8, 0.2, 1)
                )
                call_btn.bind(on_press=lambda x, num=phone['number']: self.make_phone_call(num))
                phone_layout.add_widget(call_btn)
                
                # Copy button
                copy_btn = Button(
                    text='📋',
                    size_hint_x=0.15
                )
                copy_btn.bind(on_press=lambda x, num=phone['number']: self.copy_to_clipboard(num))
                phone_layout.add_widget(copy_btn)
                
                details_layout.add_widget(phone_layout)
        
        # Email addresses section
        if contact_data['emails']:
            email_header = Label(
                text='📧 Email Addresses',
                font_size=16,
                bold=True,
                halign='left',
                size_hint_y=None,
                height=dp(30)
            )
            email_header.bind(size=email_header.setter('text_size'))
            details_layout.add_widget(email_header)
            
            for email in contact_data['emails']:
                email_layout = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=dp(40),
                    spacing=10
                )
                
                email_info = Label(
                    text=f"{email['type']}: {email['address']}",
                    font_size=14,
                    halign='left',
                    size_hint_x=0.7
                )
                email_info.bind(size=email_info.setter('text_size'))
                email_layout.add_widget(email_info)
                
                # Email button
                email_btn = Button(
                    text='📧 Email',
                    size_hint_x=0.15,
                    background_color=(0.2, 0.2, 0.8, 1)
                )
                email_btn.bind(on_press=lambda x, addr=email['address']: self.send_email(addr))
                email_layout.add_widget(email_btn)
                
                # Copy button
                copy_btn = Button(
                    text='📋',
                    size_hint_x=0.15
                )
                copy_btn.bind(on_press=lambda x, addr=email['address']: self.copy_to_clipboard(addr))
                email_layout.add_widget(copy_btn)
                
                details_layout.add_widget(email_layout)
        
        # Addresses section
        if contact_data['addresses']:
            addr_header = Label(
                text='🏠 Addresses',
                font_size=16,
                bold=True,
                halign='left',
                size_hint_y=None,
                height=dp(30)
            )
            addr_header.bind(size=addr_header.setter('text_size'))
            details_layout.add_widget(addr_header)
            
            for address in contact_data['addresses']:
                addr_layout = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=dp(40),
                    spacing=10
                )
                
                addr_info = Label(
                    text=f"{address['type']}: {address['address']}",
                    font_size=14,
                    halign='left',
                    size_hint_x=0.85
                )
                addr_info.bind(size=addr_info.setter('text_size'))
                addr_layout.add_widget(addr_info)
                
                # Maps button
                maps_btn = Button(
                    text='🗺️',
                    size_hint_x=0.15
                )
                maps_btn.bind(on_press=lambda x, addr=address['address']: self.open_maps(addr))
                addr_layout.add_widget(maps_btn)
                
                details_layout.add_widget(addr_layout)
        
        # Other info section
        other_info = []
        if contact_data.get('birthday'):
            other_info.append(f"🎂 Birthday: {contact_data['birthday']}")
        if contact_data.get('website'):
            other_info.append(f"🌐 Website: {contact_data['website']}")
        if contact_data.get('notes'):
            other_info.append(f"📝 Notes: {contact_data['notes']}")
        
        if other_info:
            other_header = Label(
                text='ℹ️ Additional Information',
                font_size=16,
                bold=True,
                halign='left',
                size_hint_y=None,
                height=dp(30)
            )
            other_header.bind(size=other_header.setter('text_size'))
            details_layout.add_widget(other_header)
            
            for info in other_info:
                info_label = Label(
                    text=info,
                    font_size=14,
                    halign='left',
                    size_hint_y=None,
                    height=dp(25)
                )
                info_label.bind(size=info_label.setter('text_size'))
                details_layout.add_widget(info_label)
        
        scroll.add_widget(details_layout)
        main_layout.add_widget(scroll)
        
        return main_layout
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard (Desktop only)"""
        try:
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
            
            self.show_toast(f"Copied: {text}")
        except Exception as e:
            print(f"Clipboard error: {e}")
            self.show_error_popup(f"Could not copy to clipboard: {e}")
    
    def send_email(self, email_address):
        """Open email app with address (Desktop)"""
        try:
            webbrowser.open(f"mailto:{email_address}")
            self.show_toast(f"Opening email for: {email_address}")
        except Exception as e:
            print(f"Email error: {e}")
            self.show_error_popup(f"Could not open email app: {e}")
    
    def open_maps(self, address):
        """Open maps in web browser (Desktop)"""
        try:
            webbrowser.open(f"https://maps.google.com/maps?q={address}")
            self.show_toast(f"Opening maps for: {address}")
        except Exception as e:
            print(f"Maps error: {e}")
            self.show_error_popup(f"Could not open maps: {e}")
    
    def export_contact(self, file_path, contact_name):
        """Export contact using existing document vault export functionality"""
        if hasattr(self.app, 'document_vault'):
            # Use the existing export functionality from document vault
            result = self.app.document_vault.export_document(file_path)
            if result['success']:
                self.show_toast(f"Contact exported: {contact_name}")
            else:
                self.show_error_popup(f"Export failed: {result.get('error', 'Unknown error')}")
    
    def show_edit_placeholder(self):
        """Placeholder for contact editing (future feature)"""
        content = Label(
            text="📝 Contact Editing\n\nThis feature is coming soon!\n\nFor now, you can:\n• Export the contact\n• Edit with external app\n• Re-import to vault"
        )
        popup = Popup(
            title='Edit Contact',
            content=content,
            size_hint=(0.7, 0.5),
            auto_dismiss=True
        )
        popup.open()
    
    def show_toast(self, message):
        content = Label(text=message)
        popup = Popup(
            title='',
            content=content,
            size_hint=(0.6, 0.3),
            auto_dismiss=True
        )
        popup.open()
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)


def integrate_contact_management(vault_app):

    vault_app.contact_manager = ContactManager(vault_app)
    
    print("🖥️ Desktop mode - External app integration enabled")
    
    return vault_app.contact_manager