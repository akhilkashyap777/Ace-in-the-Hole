# complete_contact_integration.py - Complete Contact Integration (Desktop Only)
"""
Complete integration file for adding contact management and calling functionality
to your existing document vault system.

This file combines all the contact functionality into one easy-to-use integration.

Usage in main.py:
    from complete_contact_integration import setup_contact_system
    setup_contact_system(self)  # Add after vault setup
"""

import os
from contact_manager import integrate_contact_management
from contact_ui_integration import integrate_contact_ui_enhancements

def setup_contact_system(vault_app):
    
    try:
        # Step 1: Integrate contact management core
        contact_manager = integrate_contact_management(vault_app)
        
        # Step 2: Enhance UI for contacts (import here to avoid circular imports)
        try:
            from document_vault_ui import DocumentVaultUI
            integrate_contact_ui_enhancements(DocumentVaultUI)
        except ImportError as e:
            print(f"⚠️ UI enhancement skipped: {e}")
        
        # Step 3: Update document vault core to mark contacts as active
        activate_contact_category(vault_app.document_vault)
        
        # Step 4: Add contact-specific methods to vault app
        add_contact_methods(vault_app)
        
        return contact_manager
        
    except Exception as e:
        print(f"❌ Contact system setup failed: {e}")
        return None

def activate_contact_category(document_vault):
    """
    Activate the contact category in the document vault
    Moves contacts from 'future' to active category
    """
    
    # Contacts are already defined in FILE_CATEGORIES, 
    # but let's ensure they're properly recognized
    contact_extensions = ['.vcf', '.contact', '.abbu', '.ldif']
    
    # Verify contact category exists and is active
    if 'contacts' in document_vault.FILE_CATEGORIES:
        
        # Ensure contact directory exists
        contact_dir = os.path.join(document_vault.vault_dir, 'contacts')
        if not os.path.exists(contact_dir):
            os.makedirs(contact_dir)
    else:
        print("⚠️ Contact category not found in FILE_CATEGORIES")

def add_contact_methods(vault_app):
    """
    Add convenience methods to the vault app for contact operations
    """
    
    def get_all_contacts(category_filter=None):
        """Get all contacts from the vault"""
        if hasattr(vault_app, 'document_vault'):
            return vault_app.document_vault.get_vault_documents('contacts')
        return []
    
    def parse_contact_file(file_path):
        """Parse a contact file"""
        if hasattr(vault_app, 'contact_manager'):
            return vault_app.contact_manager.parse_vcf_contact(file_path)
        return {'error': 'Contact manager not available'}
    
    def make_call_to_contact(contact_name_or_number):
        """Make a call to a contact by name or number"""
        if hasattr(vault_app, 'contact_manager'):
            # If it looks like a phone number, call directly
            if contact_name_or_number.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
                vault_app.contact_manager.make_phone_call(contact_name_or_number)
            else:
                # Search for contact by name
                contacts = get_all_contacts()
                for contact_file in contacts:
                    contact_data = parse_contact_file(contact_file['path'])
                    if 'error' not in contact_data and contact_data['name'].lower() == contact_name_or_number.lower():
                        if contact_data['phones']:
                            vault_app.contact_manager.make_phone_call(contact_data['phones'][0]['number'])
                            return
                print(f"Contact '{contact_name_or_number}' not found")
    
    def get_contact_stats():
        """Get statistics about contacts in vault"""
        contacts = get_all_contacts()
        stats = {
            'total_contacts': len(contacts),
            'total_size_mb': sum(c['size'] for c in contacts) / (1024 * 1024),
            'contacts_with_phones': 0,
            'contacts_with_emails': 0,
            'phone_numbers': [],
            'email_addresses': []
        }
        
        for contact_file in contacts:
            contact_data = parse_contact_file(contact_file['path'])
            if 'error' not in contact_data:
                if contact_data['phones']:
                    stats['contacts_with_phones'] += 1
                    stats['phone_numbers'].extend([p['number'] for p in contact_data['phones']])
                if contact_data['emails']:
                    stats['contacts_with_emails'] += 1
                    stats['email_addresses'].extend([e['address'] for e in contact_data['emails']])
        
        return stats
    
    # Add methods to vault app
    vault_app.get_all_contacts = get_all_contacts
    vault_app.parse_contact_file = parse_contact_file
    vault_app.make_call_to_contact = make_call_to_contact
    vault_app.get_contact_stats = get_contact_stats

def verify_contact_integration(vault_app):
    """
    Verify that contact integration is working properly
    Returns status report
    """
    
    status = {
        'contact_manager': False,
        'document_vault': False,
        'contact_category': False,
        'desktop_integration': False,
        'ui_integration': False,
        'permissions': True  # Always true on desktop
    }
    
    # Check contact manager
    if hasattr(vault_app, 'contact_manager'):
        status['contact_manager'] = True
    
    # Check document vault
    if hasattr(vault_app, 'document_vault'):
        status['document_vault'] = True
        
        # Check contact category
        if 'contacts' in vault_app.document_vault.FILE_CATEGORIES:
            status['contact_category'] = True
    
    # Desktop integration is always available
    status['desktop_integration'] = True
    
    # Check UI integration
    try:
        from document_vault_ui import DocumentVaultUI
        if hasattr(DocumentVaultUI, 'show_contact_view'):
            status['ui_integration'] = True
    except ImportError:
        pass
    
    return status

def print_contact_integration_status(vault_app):
    
    status = verify_contact_integration(vault_app)
    
    for component, is_working in status.items():
        icon = "✅" if is_working else "❌"
        print(f"{icon} {component.replace('_', ' ').title()}: {'Working' if is_working else 'Not Available'}")
    
    # Additional info
    if hasattr(vault_app, 'contact_manager'):
        print(f"\n📞 Platform: Desktop (External App Integration)")
    
    if hasattr(vault_app, 'document_vault'):
        contact_dir = os.path.join(vault_app.document_vault.vault_dir, 'contacts')
        print(f"📁 Contact Storage: {contact_dir}")
        
        if os.path.exists(contact_dir):
            contact_count = len([f for f in os.listdir(contact_dir) if f.endswith(('.vcf', '.contact'))])
            print(f"👤 Contacts in Vault: {contact_count}")

# Example usage and documentation
USAGE_EXAMPLE = '''
# Example usage in main.py:

from complete_contact_integration import setup_contact_system, print_contact_integration_status

class VaultApp(App):
    def build(self):
        # ... existing vault setup code ...
        
        # Add contact system
        setup_contact_system(self)
        
        # Optional: Print status for debugging
        print_contact_integration_status(self)
        
        return self.main_layout
    
    def some_method(self):
        # Example of using contact methods
        
        # Get all contacts
        contacts = self.get_all_contacts()
        
        # Make a call by contact name
        self.make_call_to_contact("John Doe")
        
        # Make a call by phone number
        self.make_call_to_contact("+1234567890")
        
        # Get contact statistics
        stats = self.get_contact_stats()
        print(f"Total contacts: {stats['total_contacts']}")
'''

if __name__ == "__main__":
    print("📞 Complete Contact Integration for Document Vault (Desktop)")
    print("=" * 60)
    print(__doc__)
    print(USAGE_EXAMPLE)