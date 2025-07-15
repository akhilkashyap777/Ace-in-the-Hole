"""
File Transfer Integration Module
This replaces your existing file_transfer_vault.py file
Compatible with main.py structure - supports 5GB file transfers
"""

import logging

logger = logging.getLogger('VaultTransfer')


def integrate_file_transfer(vault_app):
    """
    Integrate file transfer functionality with the main vault app
    
    This function follows the same pattern as other vault modules in main.py:
    - integrate_document_vault(self)
    - integrate_photo_vault(self)
    - integrate_video_vault(self)
    - etc.
    
    Args:
        vault_app: The main VaultApp instance from main.py
    """
    
    def show_file_transfer():
        """
        Display the file transfer interface
        
        This method will be added to the vault_app instance and called
        when the user clicks the "File Transfer" card in the vault.
        """
        # Clear the main layout (standard pattern from main.py)
        vault_app.main_layout.clear_widgets()
        
        # Import UI module here to avoid circular imports
        from file_transfer_ui import VaultTransferUI
        
        # Create the transfer interface
        transfer_interface = VaultTransferUI(vault_app)
        
        # Add to main layout
        vault_app.main_layout.add_widget(transfer_interface)
        
        # Update current screen tracking (following main.py pattern)
        vault_app.current_screen = 'file_transfer'
    
    # Add the method to the vault app instance
    # This is how all other vault modules integrate with main.py
    vault_app.show_file_transfer = show_file_transfer

__all__ = ['integrate_file_transfer']


if __name__ == "__main__":
    logger.info("  • Non-technical user friendly interface")