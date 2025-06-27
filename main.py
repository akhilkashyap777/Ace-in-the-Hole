import os
import threading
import subprocess
import sys
import weakref
from kivymd.app import MDApp

from kivymd.uix.boxlayout import MDBoxLayout

from kivymd.uix.label import MDLabel

from kivymd.uix.button import MDRaisedButton, MDIconButton

from kivymd.uix.card import MDCard

from kivymd.uix.gridlayout import MDGridLayout

from kivymd.uix.scrollview import MDScrollView

from kivy.core.window import Window

from game_widget import GameWidget

from photo_vault import integrate_photo_vault

from video_vault import integrate_video_vault

from recycle_bin_ui import integrate_recycle_bin

from secure_storage import SecureStorage

from vault_secure_integration import initialize_secure_vault

from document_vault import integrate_document_vault

from complete_contact_integration import setup_contact_system

from audio_vault_main_ui import integrate_audio_vault

from password_manager import PasswordManager

from password_ui import GamePasswordUI

from file_transfer_vault import integrate_file_transfer



try:

    from android.permissions import request_permissions, Permission

    from plyer import notification

    ANDROID = True

except ImportError:

    ANDROID = False



class VaultCardManager:

    """Manages vault cards lifecycle and prevents memory leaks"""

    

    def __init__(self, app_ref):

        self.app_ref = app_ref

        self.active_cards = []

        

    def create_card(self, icon, title, subtitle, method_name):

        """Create a single vault card with proper lifecycle management"""

        

        card = MDCard(

            orientation='horizontal',

            size_hint_y=None,

            height="120dp",

            padding="20dp",

            spacing="15dp",

            elevation=4,

            radius=[8],

            ripple_behavior=True

        )

        

        card.md_bg_color = [0.37, 0.49, 0.55, 1]

        

        icon_btn = MDIconButton(

            icon=icon,

            icon_color="white",

            icon_size="40dp",

            size_hint=(None, None),

            size=("40dp", "40dp")

        )

        card.add_widget(icon_btn)

        

        text_container = MDBoxLayout(

            orientation='vertical',

            spacing="5dp",

            adaptive_height=True

        )

        

        title_label = MDLabel(

            text=title,

            font_style="H6",

            text_color="white",

            size_hint_y=None,

            height="30dp",

            bold=True

        )

        text_container.add_widget(title_label)

        

        subtitle_label = MDLabel(

            text=subtitle,

            font_style="Caption",

            text_color=[0.9, 0.9, 0.9, 0.8],

            size_hint_y=None,

            height="20dp"

        )

        text_container.add_widget(subtitle_label)

        

        card.add_widget(text_container)

        

        def on_card_press(instance):

            app = self.app_ref()

            if app and hasattr(app, method_name):

                getattr(app, method_name)()

        

        card.bind(on_release=on_card_press)

        self.active_cards.append(card)

        

        return card

    

    def cleanup(self):

        """Clean up all cards and their references"""

        for card in self.active_cards:

            card.clear_widgets()

            card.unbind(on_release=None)

        self.active_cards.clear()



class ScreenManager:

    """Manages screen transitions and widget lifecycle"""

    

    def __init__(self, app_ref):

        self.app_ref = app_ref

        self.current_screen = 'game'

        self.screen_widgets = {}

        

    def transition_to(self, screen_name, widget_factory=None):

        """Clean transition between screens"""

        app = self.app_ref()

        if not app:

            return

            

        self.cleanup_current_screen()

        app.main_layout.clear_widgets()

        

        if widget_factory:

            new_widget = widget_factory()

            app.main_layout.add_widget(new_widget)

            self.screen_widgets[screen_name] = new_widget

        

        self.current_screen = screen_name

        app.current_screen = screen_name

    

    def cleanup_current_screen(self):

        """Cleanup widgets from current screen"""

        if self.current_screen in self.screen_widgets:

            widget = self.screen_widgets[self.current_screen]

            if hasattr(widget, 'cleanup'):

                widget.cleanup()

            del self.screen_widgets[self.current_screen]



class VaultApp(MDApp):

    def __init__(self):

        super().__init__()

        

        self.volume_pattern = []

        self.target_pattern = ['up', 'down', 'up', 'down', 'up']

        self.vault_open = False

        self.current_screen = 'game'

        

        self.screen_manager = ScreenManager(weakref.ref(self))

        self.card_manager = None

        

        self.password_manager = PasswordManager("SecretVault")

        self.password_ui = GamePasswordUI(self)

        

    def build(self):

        """Build the application"""

        self.theme_cls.theme_style = "Dark"

        self.theme_cls.primary_palette = "BlueGray"

        

        if ANDROID:

            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])

        

        Window.bind(on_key_down=self.on_key_down)

        

        self.main_layout = MDBoxLayout(orientation='vertical')

        

        self.secure_storage = SecureStorage("SecretVault")

        self.initialize_vault_modules()

        

        self.show_game_screen()

        

        return self.main_layout

    

    def initialize_vault_modules(self):

        """Initialize all vault modules once"""

        initialize_secure_vault(self)

        integrate_document_vault(self)

        setup_contact_system(self)

        integrate_audio_vault(self)

        integrate_photo_vault(self)

        integrate_video_vault(self)

        integrate_recycle_bin(self)

        integrate_file_transfer(self)

    

    def create_game_widget(self):

        """Factory method to create game screen"""

        container = MDBoxLayout(orientation='vertical')

        

        game_widget = GameWidget()

        container.add_widget(game_widget)

        

        button_layout = MDBoxLayout(

            orientation='horizontal', 

            size_hint_y=None, 

            height="60dp",

            spacing=10, 

            padding=10

        )

        

        start_btn = MDRaisedButton(text='Start Game', size_hint_x=0.5)

        start_btn.bind(on_press=lambda x: game_widget.start_game())

        button_layout.add_widget(start_btn)

        

        reset_btn = MDRaisedButton(text='Reset', size_hint_x=0.5)

        reset_btn.bind(on_press=lambda x: self.reset_game(game_widget))

        button_layout.add_widget(reset_btn)

        

        container.add_widget(button_layout)

        container.game_widget = game_widget

        

        return container

    

    def create_vault_widget(self):

        """Factory method to create vault screen"""

        

        self.card_manager = VaultCardManager(weakref.ref(self))

        

        main_container = MDBoxLayout(orientation='vertical')

        

        title = MDLabel(

            text='High Roller Suite',

            font_style="H4",

            halign="center",

            size_hint_y=None,

            height="60dp",

            theme_text_color="Primary"

        )

        main_container.add_widget(title)

        

        scroll_view = MDScrollView()

        scroll_content = MDBoxLayout(

            orientation='vertical',

            spacing="15dp",

            size_hint_y=None,

            adaptive_height=True,

            padding=["20dp", "10dp", "20dp", "20dp"]

        )

        

        cards_layout = MDBoxLayout(

            orientation='vertical', 

            spacing="12dp",

            size_hint_y=None,

            adaptive_height=True

        )

        

        vault_cards = [

            ("image-multiple", "Hidden Photos", "Secure photo storage", "show_photo_gallery"),

            ("video", "Hidden Videos", "Private video collection", "show_video_gallery"),

            ("file-document", "Documents", "Important files & papers", "show_document_vault"),

            ("music", "Audio Files", "Private audio recordings", "show_audio_vault"),

            ("delete", "Recycle Bin", "Restore deleted files", "show_recycle_bin"),

            ("wifi", "File Transfer", "Share files via WiFi", "show_file_transfer")

        ]

        

        for icon, title, subtitle, method_name in vault_cards:

            card = self.card_manager.create_card(icon, title, subtitle, method_name)

            cards_layout.add_widget(card)

        

        scroll_content.add_widget(cards_layout)

        

        back_btn = MDRaisedButton(

            text='Back to Game',

            size_hint_y=None,

            height="50dp",

            size_hint_x=None,

            width="200dp",

            pos_hint={'center_x': 0.5}

        )

        back_btn.bind(on_press=lambda x: self.show_game_screen())

        scroll_content.add_widget(back_btn)

        

        scroll_view.add_widget(scroll_content)

        main_container.add_widget(scroll_view)

        

        def cleanup():

            if self.card_manager:

                self.card_manager.cleanup()

                self.card_manager = None

        

        main_container.cleanup = cleanup

        

        return main_container

    

    def show_game_screen(self):

        """Show the game screen"""

        self.vault_open = False

        self.volume_pattern = []

        self.screen_manager.transition_to('game', self.create_game_widget)

    

    def show_vault_screen(self):

        """Show the vault screen"""

        self.vault_open = True

        self.screen_manager.transition_to('vault_main', self.create_vault_widget)

        

        if ANDROID:

            try:

                notification.notify(

                    title='Vault Opened',

                    message='Secret vault has been unlocked',

                    timeout=2

                )

            except:

                pass

    

    def open_vault(self):

        """Backward compatibility for existing code"""

        self.show_vault_screen()

    

    def show_vault_main(self):

        """Backward compatibility for modules"""

        self.show_vault_screen()

    

    def back_to_game(self, instance=None):

        """Backward compatibility for existing code"""

        self.show_game_screen()

    

    def reset_game(self, game_widget):

        """Reset the game"""

        if hasattr(game_widget, 'game') and game_widget.game:

            game_widget.game.reset_game()

            game_widget.game.show_cards()

    

    def on_key_down(self, window, key, scancode, codepoint, modifier):

        """Handle volume button presses"""

        key_map = {

            24: 'up',

            25: 'down',

            273: 'up',

            274: 'down'

        }

        

        if key in key_map:

            button = key_map[key]

            self.volume_pattern.append(button)

            

            if len(self.volume_pattern) > 5:

                self.volume_pattern.pop(0)

            

            if self.volume_pattern == self.target_pattern:

                self.request_vault_access()

            

            return True

        

        return False

    

    def request_vault_access(self):

        """Handle vault access request"""

        if self.password_manager.is_first_launch():

            self.password_ui.show_first_setup()

        else:

            self.password_ui.show_password_prompt()

    

    def on_stop(self):

        """Clean shutdown"""

        self.screen_manager.cleanup_current_screen()

        

        if self.card_manager:

            self.card_manager.cleanup()



if __name__ == '__main__':

    app = VaultApp()

    try:

        app.run()

    except KeyboardInterrupt:

        print("App interrupted by user")

    finally:

        app.on_stop()
