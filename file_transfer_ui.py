import logging
import base64
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.scrollview import MDScrollView
from file_transfer_server import VaultFileTransferServer

logger = logging.getLogger('VaultTransfer')


class VaultTransferUI(MDBoxLayout):
    """Beautiful and user-friendly transfer interface with 5GB support"""
    
    def __init__(self, vault_app):
        super().__init__(orientation='vertical', spacing=20, padding=20)
        self.vault_app = vault_app
        self.transfer_server = VaultFileTransferServer(vault_app)
        self.safety_dialog = None
        self.create_interface()
    
    def create_interface(self):
        """Create the beautiful transfer interface"""
        self._create_header()
        self._create_security_warning()
        self._create_server_controls()
        self._create_instructions()
        self._create_navigation()
    
    def _create_header(self):
        """Create attractive header"""
        header_card = MDCard(
            size_hint_y=None,
            height="120dp",
            padding="20dp",
            spacing="10dp",
            elevation=3,
            md_bg_color=(0.1, 0.1, 0.2, 1)
        )
        
        title = MDLabel(
            text="📡 WiFi File Transfer",
            font_style="H4",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        
        subtitle = MDLabel(
            text="Share files securely across your devices (up to 5GB)",
            font_style="Subtitle1",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.8, 0.8, 0.9, 1)
        )
        
        header_card.add_widget(title)
        header_card.add_widget(subtitle)
        self.add_widget(header_card)
    
    def _create_security_warning(self):
        """Create prominent security warning"""
        warning_card = MDCard(
            size_hint_y=None,
            height="140dp",
            padding="20dp",
            spacing="10dp",
            md_bg_color=(0.3, 0.1, 0.1, 1),
            elevation=2
        )
        
        warning_title = MDLabel(
            text="🔒 Security Notice",
            font_style="H6",
            theme_text_color="Custom",
            text_color=(1, 0.8, 0.8, 1),
            size_hint_y=None,
            height="30dp"
        )
        
        warning_text = MDLabel(
            text="Only use on trusted WiFi networks (your home/office). "
                 "Never use on public WiFi (cafes, airports, hotels). "
                 "Your files will be accessible to anyone on the same network.",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=(1, 0.9, 0.9, 1),
            size_hint_y=None,
            height="80dp"
        )
        
        warning_card.add_widget(warning_title)
        warning_card.add_widget(warning_text)
        self.add_widget(warning_card)
    
    def _create_server_controls(self):
        """Create server control panel"""
        control_card = MDCard(
            size_hint_y=None,
            height="240dp",
            padding="20dp",
            spacing="15dp",
            elevation=2
        )
        
        self.status_label = MDLabel(
            text="Server: Stopped",
            font_style="H6",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        control_card.add_widget(self.status_label)
        
        self.url_label = MDLabel(
            text="",
            font_style="Body1",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.7, 0.9, 1, 1)
        )
        control_card.add_widget(self.url_label)
        
        button_layout = MDBoxLayout(
            orientation='horizontal',
            spacing="15dp",
            size_hint_y=None,
            height="60dp"
        )
        
        self.start_button = MDRaisedButton(
            text="Start Sharing",
            size_hint_x=0.5,
            md_bg_color=(0.2, 0.7, 0.2, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        self.start_button.bind(on_press=self.show_safety_confirmation)
        
        self.stop_button = MDRaisedButton(
            text=" Stop Sharing",
            size_hint_x=0.5,
            md_bg_color=(0.7, 0.2, 0.2, 1),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            disabled=True
        )
        self.stop_button.bind(on_press=self.stop_server)
        
        button_layout.add_widget(self.start_button)
        button_layout.add_widget(self.stop_button)
        control_card.add_widget(button_layout)
        
        self.add_widget(control_card)
    
    def _create_instructions(self):
        """Create user-friendly instructions"""
        instruction_card = MDCard(
            size_hint_y=None,
            height="280dp",
            padding="20dp",
            spacing="10dp",
            elevation=1
        )
        
        instruction_title = MDLabel(
            text=" How to Share Files (Simple Steps)",
            font_style="H6",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            height="40dp"
        )
        
        scroll_view = MDScrollView()
        instruction_text = MDLabel(
            text="""1.  Make sure you're on a trusted wifi

2.  Press 'Start Sharing' button above

3.  On your phone/tablet, open any web browser (Chrome, Safari, etc.)

4.  Type the web address shown above into your browser
   (Example: http://192.168.1.100:8080)

5.  Upload files FROM your phone TO this computer (up to 5GB each!)
    Download files FROM this computer TO your phone

6.  Press 'Stop Sharing' when done (IMPORTANT for security)

⚠️ REMEMBER: Only use on trusted networks you control!""",
            font_style="Body2",
            theme_text_color="Custom",
            text_color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None
        )
        instruction_text.bind(texture_size=instruction_text.setter('size'))
        
        scroll_view.add_widget(instruction_text)
        instruction_card.add_widget(instruction_title)
        instruction_card.add_widget(scroll_view)
        self.add_widget(instruction_card)
    
    def _create_navigation(self):
        """Create navigation controls"""
        nav_layout = MDBoxLayout(
            orientation='horizontal',
            spacing="15dp",
            size_hint_y=None,
            height="60dp"
        )
        
        back_button = MDRaisedButton(
            text="← Back to Vault",
            size_hint_x=0.7,
            md_bg_color=(0.3, 0.3, 0.4, 1)
        )
        back_button.bind(on_press=self.return_to_vault)
        
        help_button = MDFlatButton(
            text=" Need Help?",
            size_hint_x=0.3,
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 1, 1)
        )
        help_button.bind(on_press=self.show_help_dialog)
        
        nav_layout.add_widget(back_button)
        nav_layout.add_widget(help_button)
        self.add_widget(nav_layout)
    
    def show_safety_confirmation(self, instance):
        """Show safety confirmation before starting server"""
        if self.safety_dialog:
            return
        
        self.safety_dialog = MDDialog(
            title="Safety Confirmation",
            text="""Are you on a TRUSTED network?

Your files will be accessible to ANYONE on the same network!

So only proceed if you're on a trusted network.""",
            buttons=[
                MDFlatButton(
                    text="Cancel",
                    theme_text_color="Custom",
                    text_color=(0.7, 0.7, 0.7, 1),
                    on_press=self.close_safety_dialog
                ),
                MDRaisedButton(
                    text="Yes, I'm on trusted WiFi",
                    md_bg_color=(0.2, 0.7, 0.2, 1),
                    on_press=self.start_server_confirmed
                )
            ]
        )
        self.safety_dialog.open()
    
    def close_safety_dialog(self, instance):
        """Close safety confirmation dialog"""
        if self.safety_dialog:
            self.safety_dialog.dismiss()
            self.safety_dialog = None
    
    def start_server_confirmed(self, instance):
        """Start server after safety confirmation"""
        self.close_safety_dialog(instance)
        
        success, result = self.transfer_server.start_server()
        
        if success:
            self.status_label.text = "Server: Running & Ready"
            self.url_label.text = f"Open this on your phone: {result}"
            self.start_button.disabled = True
            self.stop_button.disabled = False
            
            qr_code = self.transfer_server.generate_qr_code(result)
            if qr_code:
                self.show_qr_dialog(result, qr_code)
        else:
            self.status_label.text = f"❌ Error: {result}"
            logger.error(f"Server start failed: {result}")
    
    def stop_server(self, instance):
        """Stop the transfer server"""
        self.transfer_server.stop_server()
        self.status_label.text = "Server: Stopped"
        self.url_label.text = ""
        self.start_button.disabled = False
        self.stop_button.disabled = True
    
    def show_qr_dialog(self, url, qr_code_base64):
        """Show QR code for easy mobile access"""
        try:
            from kivymd.uix.boxlayout import MDBoxLayout
            from kivy.uix.image import Image
            from kivy.core.image import Image as CoreImage
            import io
            
            qr_data = base64.b64decode(qr_code_base64)
            qr_texture = CoreImage(io.BytesIO(qr_data), ext='png').texture
            
            content = MDBoxLayout(orientation='vertical', spacing="15dp", size_hint_y=None, height="400dp")
            
            qr_label = MDLabel(
                text="📱 Scan with your phone's camera:",
                font_style="H6",
                halign="center",
                size_hint_y=None,
                height="40dp"
            )
            
            qr_image = Image(texture=qr_texture, size_hint=(None, None), size=("200dp", "200dp"))
            qr_image.pos_hint = {'center_x': 0.5}
            
            url_label = MDLabel(
                text=f"Or type: {url}",
                font_style="Body2",
                halign="center",
                size_hint_y=None,
                height="60dp"
            )
            
            content.add_widget(qr_label)
            content.add_widget(qr_image)
            content.add_widget(url_label)
            
            qr_dialog = MDDialog(
                title="📲 Easy Access",
                type="custom",
                content_cls=content,
                buttons=[
                    MDRaisedButton(
                        text="Got it!",
                        on_press=lambda x: qr_dialog.dismiss()
                    )
                ]
            )
            qr_dialog.open()
            
        except Exception as e:
            logger.warning(f"QR dialog failed: {e}")
    
    def show_help_dialog(self, instance):
        """Show detailed help information"""
        help_dialog = MDDialog(
            title="Need Help?",
            text="""TROUBLESHOOTING:

Can't connect?
• Make sure both devices are on the same WiFi
• Try turning WiFi off and on
• Check if firewall is blocking

Phone can't see the website?
• Double-check the web address
• Try typing http:// before the address
• Use Chrome or Safari browser

Slow transfer?
• Move closer to WiFi router
• Close other apps using internet
• Try smaller files first

Large file transfers (up to 5GB):
• Ensure stable WiFi connection
• Keep devices close to router
• Don't interrupt transfer

Security tips:
• Only use on your home/office WiFi
• Stop sharing when done
• Never use on public networks

Still stuck? The web address should look like:
http://192.168.1.100:8080

The numbers will be different for your network.""",
            buttons=[
                MDRaisedButton(
                    text="Thanks!",
                    on_press=lambda x: help_dialog.dismiss()
                )
            ]
        )
        help_dialog.open()
    
    def return_to_vault(self, instance):
        """Return to main vault with cleanup"""
        if self.transfer_server.is_running:
            self.transfer_server.stop_server()
        
        if self.safety_dialog:
            self.safety_dialog.dismiss()
            self.safety_dialog = None
        self.vault_app.show_vault_main()