# document_vault.py - Universal Document Vault for Secret Vault App
"""
Universal Document Vault for the Secret Vault App

This module provides secure storage and management for ANY non-media file type:
- Documents: PDF, Word, PowerPoint, text files
- Code: Python, JavaScript, HTML, CSS, etc.
- Archives: ZIP, RAR, 7z, etc.
- Applications: APK, EXE, etc.
- Data files: JSON, XML, CSV, etc.
- And literally any other file type (future-proof)

Key Features:
✅ Cross-platform: Android, Windows, macOS, Linux
✅ Secure storage in app-private directories
✅ View-only approach with text file preview
✅ Category-based organization and filtering
✅ Export functionality to device storage
✅ Recycle bin integration for safe deletion
✅ Future-ready for contacts, certificates, etc.

Architecture:
- document_vault_core.py: Core functionality (file operations, categorization)
- document_vault_ui.py: User interface components (gallery, filtering, preview)
- document_vault.py: Main integration file (this file)

Usage in main.py:
    from document_vault import integrate_document_vault
    integrate_document_vault(self)  # Add this after secure storage setup
    
    # Then add a button in your vault main screen:
    document_btn = Button(text='📁 Documents')
    document_btn.bind(on_press=lambda x: self.show_document_vault())
"""

# Import all functionality from separate files
from document_vault_core import DocumentVaultCore
from document_vault_ui import DocumentVaultUI, integrate_document_vault

# Re-export main classes and functions for backwards compatibility
__all__ = [
    'DocumentVaultCore',
    'DocumentVaultUI', 
    'integrate_document_vault'
]

# Platform detection for logging
try:
    from android.storage import app_storage_path
    PLATFORM = "Android"
except ImportError:
    import platform
    PLATFORM = platform.system()

# For debugging and development
DEBUG_MODE = True

if DEBUG_MODE:
    
    # Print supported categories
    for category, config in DocumentVaultCore.FILE_CATEGORIES.items():
        if category == 'other':
            continue
        ext_sample = ', '.join(config['extensions'][:3])
        if len(config['extensions']) > 3:
            ext_sample += f", ... (+{len(config['extensions'])-3} more)"
        
        print(f"  {config['icon']} {config['display_name']}: {ext_sample}")
    

# Quick integration test function
def test_document_vault_integration():
    """
    Test function to verify document vault can be integrated
    Run this to check if all dependencies are available
    """
    try:
        print("🧪 Testing Document Vault Integration...")
        
        # Test core functionality
        print("✅ DocumentVaultCore imported successfully")
        print("✅ DocumentVaultUI imported successfully")
        print("✅ integrate_document_vault function available")
        
        # Test file categorization
        test_files = [
            "test.pdf", "document.docx", "spreadsheet.xlsx", 
            "script.py", "archive.zip", "app.apk", "data.json",
            "contact.vcf", "unknown.xyz"
        ]
        
        # Create a mock core instance to test categorization
        class MockApp:
            pass
        
        mock_app = MockApp()
        mock_app.secure_storage = None  # Will use fallback
        
        core = DocumentVaultCore(mock_app)
        
        print("📋 File categorization test:")
        for filename in test_files:
            category = core.detect_file_category(filename)
            if category:
                config = core.FILE_CATEGORIES[category]
                print(f"  {filename} → {config['icon']} {config['display_name']}")
            else:
                print(f"  {filename} → ❌ Not supported (likely media file)")
        
        print("✅ Document Vault integration test completed successfully!")
        print("🚀 Ready to integrate with your main vault app")
        
        return True
        
    except Exception as e:
        print(f"❌ Document Vault integration test failed: {e}")
        return False

# Integration instructions for developers
INTEGRATION_INSTRUCTIONS = """
🔧 INTEGRATION INSTRUCTIONS:

1. Add to main.py (after secure storage setup):
   ```python
   from document_vault import integrate_document_vault
   integrate_document_vault(self)
   ```

2. Add button to vault main screen in main.py:
   ```python
   # In your open_vault() method, add this button:
   document_btn = Button(
       text='📁 Documents (Click to manage)',
       font_size=20,
       size_hint_y=None,
       height=60
   )
   document_btn.bind(on_press=lambda x: self.show_document_vault())
   content_layout.add_widget(document_btn)
   ```

3. The document vault will automatically:
   - Use your secure storage system
   - Integrate with your recycle bin
   - Follow your app's navigation patterns
   - Support all platforms (Android, Windows, macOS, Linux)

4. File categories supported:
   📄 Documents: PDF, Word, PowerPoint, text files, e-books
   📊 Spreadsheets: Excel, CSV, data files  
   💻 Code & Scripts: Python, JavaScript, HTML, config files
   📦 Archives: ZIP, RAR, 7z, compressed files
   ⚙️ Applications: APK, EXE, installers
   💾 Data Files: Databases, logs, backups
   👥 Contacts: VCF files (future feature)
   📁 Other Files: Any unknown file type

5. Features:
   - View-only mode with text file preview
   - Category filtering and organization
   - Export to device storage
   - Safe deletion via recycle bin
   - Cross-platform file picker
   - Secure app-private storage
"""

if __name__ == "__main__":
    print(INTEGRATION_INSTRUCTIONS)
    test_document_vault_integration()