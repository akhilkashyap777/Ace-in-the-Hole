# password_ui.py - Game-themed password interface
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock
import time

class GamePasswordUI:
    def __init__(self, app_instance):
        self.app = app_instance
        self.current_pin = ""
        self.setup_mode = False
        self.confirm_pin = ""
        self.security_question = ""
        self.security_answer = ""
        self.setup_step = 1  # 1: PIN, 2: Confirm PIN, 3: Security Q, 4: Security A
        
    def show_first_setup(self):
        """Show initial setup screen disguised as game setup"""
        self.setup_mode = True
        self.setup_step = 1
        
        self.app.main_layout.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Game-themed title
        title = Label(
            text='Game Setup Required',
            font_size='24sp',
            size_hint_y=None,
            height=60,
            color=(0.2, 0.6, 1, 1)
        )
        layout.add_widget(title)
        
        # Instruction
        instruction = Label(
            text='Set your player PIN (4 digits):',
            font_size='18sp',
            size_hint_y=None,
            height=40
        )
        layout.add_widget(instruction)
        
        # PIN display
        self.pin_display = Label(
            text='_ _ _ _',
            font_size='32sp',
            size_hint_y=None,
            height=60,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(self.pin_display)
        
        # Number pad
        numpad = self.create_numpad()
        layout.add_widget(numpad)
        
        self.app.main_layout.add_widget(layout)
    
    def show_password_prompt(self):
        """Show password entry screen disguised as game login"""
        self.setup_mode = False
        self.current_pin = ""
        
        self.app.main_layout.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Check if locked out
        lockout_time = self.app.password_manager.get_lockout_time_remaining()
        if lockout_time > 0:
            self.show_lockout_screen(lockout_time)
            return
        
        # Game-themed title
        title = Label(
            text='Player Verification',
            font_size='24sp',
            size_hint_y=None,
            height=60,
            color=(0.2, 0.6, 1, 1)
        )
        layout.add_widget(title)
        
        # Instruction
        instruction = Label(
            text='Enter your player PIN:',
            font_size='18sp',
            size_hint_y=None,
            height=40
        )
        layout.add_widget(instruction)
        
        # PIN display
        self.pin_display = Label(
            text='_ _ _ _',
            font_size='32sp',
            size_hint_y=None,
            height=60,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(self.pin_display)
        
        # Number pad
        numpad = self.create_numpad()
        layout.add_widget(numpad)
        
        # Forgot PIN button (added here for easier access)
        forgot_btn = Button(
            text='Forgot PIN?',
            size_hint_y=None,
            height=40,
            background_color=(0.6, 0.6, 0.3, 1)
        )
        forgot_btn.bind(on_press=self.show_security_question)
        layout.add_widget(forgot_btn)
        
        # Back to game button
        back_btn = Button(
            text='Back to Game',
            size_hint_y=None,
            height=50,
            background_color=(0.3, 0.3, 0.3, 1)
        )
        back_btn.bind(on_press=self.back_to_game)
        layout.add_widget(back_btn)
        
        self.app.main_layout.add_widget(layout)
    
    def create_numpad(self):
        """Create number pad for PIN entry"""
        numpad = GridLayout(cols=3, spacing=10, size_hint_y=None, height=300)
        
        # Number buttons 1-9
        for i in range(1, 10):
            btn = Button(text=str(i), font_size='24sp')
            btn.bind(on_press=lambda x, num=i: self.add_digit(num))
            numpad.add_widget(btn)
        
        # Clear button
        clear_btn = Button(text='Clear', font_size='18sp', background_color=(0.8, 0.3, 0.3, 1))
        clear_btn.bind(on_press=self.clear_pin)
        numpad.add_widget(clear_btn)
        
        # Zero button
        zero_btn = Button(text='0', font_size='24sp')
        zero_btn.bind(on_press=lambda x: self.add_digit(0))
        numpad.add_widget(zero_btn)
        
        # Delete button
        del_btn = Button(text='Del', font_size='18sp', background_color=(0.6, 0.6, 0.3, 1))
        del_btn.bind(on_press=self.delete_digit)
        numpad.add_widget(del_btn)
        
        return numpad
    
    def add_digit(self, digit):
        """Add digit to PIN"""
        if len(self.current_pin) < 4:
            self.current_pin += str(digit)
            self.update_pin_display()
            
            if len(self.current_pin) == 4:
                Clock.schedule_once(self.process_pin, 0.5)
    
    def delete_digit(self, instance):
        """Delete last digit"""
        if self.current_pin:
            self.current_pin = self.current_pin[:-1]
            self.update_pin_display()
    
    def clear_pin(self, instance):
        """Clear all digits"""
        self.current_pin = ""
        self.update_pin_display()
    
    def update_pin_display(self):
        """Update PIN display with dots and underscores"""
        display = ""
        for i in range(4):
            if i < len(self.current_pin):
                display += "● "
            else:
                display += "_ "
        self.pin_display.text = display.strip()
    
    def process_pin(self, dt):
        """Process entered PIN"""
        if self.setup_mode:
            self.handle_setup_pin()
        else:
            self.verify_pin()
    
    def handle_setup_pin(self):
        """Handle PIN during setup process"""
        if self.setup_step == 1:
            # First PIN entry
            self.confirm_pin = self.current_pin
            self.current_pin = ""
            self.setup_step = 2
            self.show_pin_confirm()
        
        elif self.setup_step == 2:
            # PIN confirmation
            if self.current_pin == self.confirm_pin:
                self.setup_step = 3
                self.show_security_question_setup()
            else:
                self.show_error("PINs don't match! Try again.")
                self.setup_step = 1
                self.current_pin = ""
                self.confirm_pin = ""
                Clock.schedule_once(lambda dt: self.show_first_setup(), 2)
    
    def show_pin_confirm(self):
        """Show PIN confirmation screen"""
        self.app.main_layout.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        title = Label(
            text='Confirm Player PIN',
            font_size='24sp',
            size_hint_y=None,
            height=60,
            color=(0.2, 0.6, 1, 1)
        )
        layout.add_widget(title)
        
        instruction = Label(
            text='Enter your PIN again:',
            font_size='18sp',
            size_hint_y=None,
            height=40
        )
        layout.add_widget(instruction)
        
        self.pin_display = Label(
            text='_ _ _ _',
            font_size='32sp',
            size_hint_y=None,
            height=60,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(self.pin_display)
        
        numpad = self.create_numpad()
        layout.add_widget(numpad)
        
        self.app.main_layout.add_widget(layout)
    
    def show_security_question_setup(self):
        """Show security question setup"""
        self.app.main_layout.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        title = Label(
            text='Security Setup',
            font_size='24sp',
            size_hint_y=None,
            height=60,
            color=(0.2, 0.6, 1, 1)
        )
        layout.add_widget(title)
        
        # Predefined questions
        questions = [
            "What city were you born in?",
            "What is your favorite color?", 
            "What is your pet's name?",
            "What is your mother's maiden name?",
            "Custom question..."
        ]
        
        instruction = Label(
            text='Choose a security question:',
            font_size='18sp',
            size_hint_y=None,
            height=40
        )
        layout.add_widget(instruction)
        
        # Question buttons
        for question in questions:
            btn = Button(
                text=question,
                size_hint_y=None,
                height=50,
                text_size=(None, None)
            )
            if question == "Custom question...":
                btn.bind(on_press=self.show_custom_question_input)
            else:
                btn.bind(on_press=lambda x, q=question: self.select_security_question(q))
            layout.add_widget(btn)
        
        self.app.main_layout.add_widget(layout)
    
    def select_security_question(self, question):
        """Select a predefined security question"""
        self.security_question = question
        self.show_security_answer_setup()
    
    def show_custom_question_input(self, instance):
        """Show custom question input"""
        content = BoxLayout(orientation='vertical', spacing=10)
        
        content.add_widget(Label(text='Enter your custom question:', size_hint_y=None, height=40))
        
        text_input = TextInput(
            multiline=False,
            size_hint_y=None,
            height=40
        )
        content.add_widget(text_input)
        
        buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        ok_btn = Button(text='OK')
        ok_btn.bind(on_press=lambda x: self.set_custom_question(text_input.text, popup))
        buttons.add_widget(ok_btn)
        
        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        buttons.add_widget(cancel_btn)
        
        content.add_widget(buttons)
        
        popup = Popup(title='Custom Security Question', content=content, size_hint=(0.8, 0.6))
        popup.open()
    
    def set_custom_question(self, question, popup):
        """Set custom security question"""
        if question.strip():
            self.security_question = question.strip()
            popup.dismiss()
            self.show_security_answer_setup()
    
    def show_security_answer_setup(self):
        """Show security answer setup"""
        self.app.main_layout.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        title = Label(
            text='Security Answer',
            font_size='24sp',
            size_hint_y=None,
            height=60,
            color=(0.2, 0.6, 1, 1)
        )
        layout.add_widget(title)
        
        question_label = Label(
            text=f'Question: {self.security_question}',
            font_size='16sp',
            size_hint_y=None,
            height=80,
            text_size=(400, None),
            halign='center'
        )
        layout.add_widget(question_label)
        
        instruction = Label(
            text='Enter your answer:',
            font_size='18sp',
            size_hint_y=None,
            height=40
        )
        layout.add_widget(instruction)
        
        self.answer_input = TextInput(
            multiline=False,
            size_hint_y=None,
            height=50,
            font_size='18sp'
        )
        layout.add_widget(self.answer_input)
        
        finish_btn = Button(
            text='Complete Setup',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        finish_btn.bind(on_press=self.complete_setup)
        layout.add_widget(finish_btn)
        
        self.app.main_layout.add_widget(layout)
    
    def complete_setup(self, instance):
        """Complete the setup process"""
        answer = self.answer_input.text.strip()
        if not answer:
            self.show_error("Please enter an answer!")
            return
        
        # Save password and security info
        success = self.app.password_manager.setup_password(
            self.confirm_pin, 
            self.security_question, 
            answer
        )
        
        if success:
            self.show_success("Setup complete! Welcome to the game.")
            Clock.schedule_once(lambda dt: self.app.back_to_game(None), 3)
        else:
            self.show_error("Setup failed! Please try again.")
    
    def verify_pin(self):
        """Verify entered PIN"""
        result, status = self.app.password_manager.verify_pin(self.current_pin)
        
        if result:
            self.show_success("Access granted!")
            Clock.schedule_once(lambda dt: self.app.open_vault(), 2)
        else:
            if status == "locked":
                lockout_time = self.app.password_manager.get_lockout_time_remaining()
                self.show_lockout_screen(lockout_time)
            elif status.startswith("failed"):
                attempts = int(status.split("_")[1])
                remaining = 5 - attempts
                if remaining > 0:
                    self.show_error(f"Wrong PIN! {remaining} attempts remaining.")
                    self.current_pin = ""
                    Clock.schedule_once(lambda dt: self.update_pin_display(), 0.5)
                else:
                    lockout_time = self.app.password_manager.get_lockout_time_remaining()
                    self.show_lockout_screen(lockout_time)
            else:
                self.show_error("Access denied!")
                self.current_pin = ""
                Clock.schedule_once(lambda dt: self.update_pin_display(), 0.5)
    
    def show_lockout_screen(self, lockout_time):
        """Show lockout screen"""
        self.app.main_layout.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        title = Label(
            text='Game Temporarily Locked',
            font_size='24sp',
            size_hint_y=None,
            height=60,
            color=(1, 0.3, 0.3, 1)
        )
        layout.add_widget(title)
        
        minutes = lockout_time // 60
        seconds = lockout_time % 60
        
        self.lockout_label = Label(
            text=f'Try again in: {minutes:02d}:{seconds:02d}',
            font_size='20sp',
            size_hint_y=None,
            height=60
        )
        layout.add_widget(self.lockout_label)
        
        # Forgot PIN button
        forgot_btn = Button(
            text='Forgot PIN?',
            size_hint_y=None,
            height=50,
            background_color=(0.6, 0.6, 0.3, 1)
        )
        forgot_btn.bind(on_press=self.show_security_question)
        layout.add_widget(forgot_btn)
        
        # Back to game button
        back_btn = Button(
            text='Back to Game',
            size_hint_y=None,
            height=50,
            background_color=(0.3, 0.3, 0.3, 1)
        )
        back_btn.bind(on_press=self.back_to_game)
        layout.add_widget(back_btn)
        
        self.app.main_layout.add_widget(layout)
        
        # Update countdown
        self.update_lockout_countdown()
    
    def update_lockout_countdown(self):
        """Update lockout countdown timer"""
        lockout_time = self.app.password_manager.get_lockout_time_remaining()
        if lockout_time > 0:
            minutes = lockout_time // 60
            seconds = lockout_time % 60
            self.lockout_label.text = f'Try again in: {minutes:02d}:{seconds:02d}'
            Clock.schedule_once(lambda dt: self.update_lockout_countdown(), 1)
        else:
            # Lockout expired, show password prompt
            self.show_password_prompt()
    
    def show_security_question(self, instance):
        """Show security question for password recovery"""
        question = self.app.password_manager.get_security_question()
        if not question:
            self.show_error("Security question not found!")
            return
        
        content = BoxLayout(orientation='vertical', spacing=10)
        
        content.add_widget(Label(
            text='Answer your security question to reset PIN:',
            size_hint_y=None,
            height=40
        ))
        
        content.add_widget(Label(
            text=question,
            size_hint_y=None,
            height=60,
            text_size=(300, None),
            halign='center'
        ))
        
        answer_input = TextInput(
            multiline=False,
            size_hint_y=None,
            height=40
        )
        content.add_widget(answer_input)
        
        buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        ok_btn = Button(text='Submit')
        ok_btn.bind(on_press=lambda x: self.verify_security_answer(answer_input.text, popup))
        buttons.add_widget(ok_btn)
        
        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        buttons.add_widget(cancel_btn)
        
        content.add_widget(buttons)
        
        popup = Popup(title='Security Question', content=content, size_hint=(0.8, 0.6))
        popup.open()
    
    def verify_security_answer(self, answer, popup):
        """Verify security answer and allow PIN reset"""
        if self.app.password_manager.verify_security_answer(answer):
            popup.dismiss()
            self.show_pin_reset()
        else:
            self.show_error("Incorrect answer!")
    
    def show_pin_reset(self):
        """Show PIN reset screen"""
        self.setup_mode = True
        self.setup_step = 1
        self.current_pin = ""
        self.confirm_pin = ""
        
        self.app.main_layout.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        title = Label(
            text='Reset Your PIN',
            font_size='24sp',
            size_hint_y=None,
            height=60,
            color=(0.2, 0.6, 1, 1)
        )
        layout.add_widget(title)
        
        instruction = Label(
            text='Enter new PIN (4 digits):',
            font_size='18sp',
            size_hint_y=None,
            height=40
        )
        layout.add_widget(instruction)
        
        self.pin_display = Label(
            text='_ _ _ _',
            font_size='32sp',
            size_hint_y=None,
            height=60,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(self.pin_display)
        
        numpad = self.create_numpad()
        layout.add_widget(numpad)
        
        self.app.main_layout.add_widget(layout)
    
    def show_error(self, message):
        """Show error message"""
        content = Label(text=message, text_size=(250, None), halign='center')
        popup = Popup(
            title='Error',
            content=content,
            size_hint=(0.6, 0.4),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def show_success(self, message):
        """Show success message"""
        content = Label(text=message, text_size=(250, None), halign='center')
        popup = Popup(
            title='Success',
            content=content,
            size_hint=(0.6, 0.4),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def back_to_game(self, instance):
        """Return to game interface"""
        self.app.volume_pattern = []  # Reset pattern
        self.app.back_to_game(None)