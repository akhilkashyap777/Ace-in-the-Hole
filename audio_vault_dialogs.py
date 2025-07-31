import os
import threading
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.clock import Clock
from kivy.metrics import dp

# Import plyer for cross-platform file dialogs
try:
    from plyer import filechooser
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

# Import stats widget
from audio_vault_stats import AudioVaultStatsWidget

# ===============================================================================
# FILE PICKER DIALOGS
# ===============================================================================

def show_add_audio_dialog(audio_vault_core, refresh_callback):
    """Show file picker to add audio files - Cross-platform implementation"""
    if PLYER_AVAILABLE:
        plyer_file_picker(audio_vault_core, refresh_callback)
    else:
        fallback_file_picker(audio_vault_core, refresh_callback)

def plyer_file_picker(audio_vault_core, refresh_callback):
    """Universal file picker using plyer - works on all platforms"""
    try:
        def on_selection(selection):
            # Direct call instead of Clock.schedule_once - NUITKA FIX
            handle_selection_async(selection, audio_vault_core, refresh_callback)
        
        # Use plyer's cross-platform file chooser
        filechooser.open_file(
            on_selection=on_selection,
            multiple=True,
            filters=[
                ("Audio files", "*.mp3", "*.wav", "*.flac", "*.aac", "*.m4a", "*.ogg", "*.wma", "*.opus"),
                ("All files", "*")
            ],
            title="Select Audio Files to Add to Vault"
        )
        
    except Exception as e:
        print(f"Plyer file chooser error: {e}")
        fallback_file_picker(audio_vault_core, refresh_callback)

def fallback_file_picker(audio_vault_core, refresh_callback):
    """Fallback file picker using Kivy's FileChooser"""
    content = BoxLayout(orientation='vertical', spacing=10, padding=10)
    
    # Instructions
    instruction_label = Label(
        text='📁 Select audio files to add to your vault:\n\nSupported formats: MP3, WAV, FLAC, AAC, M4A, OGG, and many more',
        font_size=16,
        halign='center',
        size_hint_y=None,
        height=dp(80)
    )
    instruction_label.bind(size=instruction_label.setter('text_size'))
    content.add_widget(instruction_label)
    
    # File chooser
    try:
        start_path = os.path.join(os.path.expanduser('~'), 'Music')
        if not os.path.exists(start_path):
            start_path = os.path.expanduser('~')
    except:
        start_path = os.getcwd()
    
    file_chooser = FileChooserIconView(
        path=start_path,
        filters=['*.mp3', '*.wav', '*.flac', '*.aac', '*.m4a', '*.ogg', '*.wma', '*.opus'],
        multiselect=True
    )
    content.add_widget(file_chooser)
    
    # Buttons
    button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=10)
    
    add_btn = Button(
        text='➕ Add Selected Files',
        background_color=(0.2, 0.7, 0.2, 1),
        font_size=16
    )
    
    cancel_btn = Button(
        text='❌ Cancel',
        background_color=(0.5, 0.5, 0.5, 1),
        font_size=16
    )
    
    button_layout.add_widget(add_btn)
    button_layout.add_widget(cancel_btn)
    content.add_widget(button_layout)
    
    popup = Popup(
        title='➕ Add Audio Files',
        content=content,
        size_hint=(0.95, 0.9),
        auto_dismiss=False
    )
    
    def add_selected_files(instance):
        selected_files = file_chooser.selection
        if selected_files:
            popup.dismiss()
            handle_selection_async(selected_files, audio_vault_core, refresh_callback)
        else:
            # Show no selection popup
            no_selection_popup = Popup(
                title='No Files Selected',
                content=Label(text='Please select at least one audio file to add.'),
                size_hint=(0.6, 0.3),
                auto_dismiss=True
            )
            no_selection_popup.open()
            Clock.schedule_once(lambda dt: no_selection_popup.dismiss(), 2)
    
    add_btn.bind(on_press=add_selected_files)
    cancel_btn.bind(on_press=popup.dismiss)
    
    popup.open()

def handle_selection_async(file_paths, audio_vault_core, refresh_callback):
    """Handle selected audio files asynchronously"""
    if not file_paths:
        return

    # Handle both single file and multiple files
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    elif isinstance(file_paths, list) and len(file_paths) == 1 and isinstance(file_paths[0], list):
        file_paths = file_paths[0]  # Flatten nested list
    
    # Filter valid audio files
    valid_files = []
    for file_path in file_paths:
        if audio_vault_core.is_audio_file(file_path):
            valid_files.append(file_path)
        else:
            print(f"⚠️ Skipping non-audio file: {file_path}")
    
    if valid_files:
        add_audio_files_with_progress(valid_files, audio_vault_core, refresh_callback)
    else:
        # Show no valid files popup
        no_files_popup = Popup(
            title='❌ No Audio Files',
            content=Label(text='No valid audio files were selected.\n\nPlease select MP3, WAV, FLAC, or other supported audio formats.'),
            size_hint=(0.7, 0.4),
            auto_dismiss=True
        )
        no_files_popup.open()
        Clock.schedule_once(lambda dt: no_files_popup.dismiss(), 4)

def add_audio_files_with_progress(file_paths, audio_vault_core, refresh_callback):
    """Add multiple audio files with progress tracking"""
    total_files = len(file_paths)
    completed_files = 0
    failed_files = []
    
    # Create progress popup
    progress_content = BoxLayout(orientation='vertical', spacing=15, padding=15)
    
    progress_label = Label(
        text=f'📁 Adding audio files...\n0 of {total_files} completed',
        font_size=16,
        halign='center'
    )
    progress_label.bind(size=progress_label.setter('text_size'))
    progress_content.add_widget(progress_label)
    
    current_file_label = Label(
        text='Preparing...',
        font_size=14,
        halign='center',
        color=(0.7, 0.7, 0.7, 1)
    )
    current_file_label.bind(size=current_file_label.setter('text_size'))
    progress_content.add_widget(current_file_label)
    
    progress_popup = Popup(
        title='➕ Adding Audio Files',
        content=progress_content,
        size_hint=(0.8, 0.4),
        auto_dismiss=False
    )
    progress_popup.open()
    
    def process_next_file(file_index=0):
        if file_index >= total_files:
            # All files processed
            progress_popup.dismiss()
            refresh_callback()
            show_add_results(total_files, len(failed_files), failed_files)
            return
        
        file_path = file_paths[file_index]
        filename = os.path.basename(file_path)
        
        # Update progress
        progress_label.text = f'📁 Adding audio files...\n{completed_files} of {total_files} completed'
        current_file_label.text = f'Processing: {filename}'
        
        def on_file_added(result):
            nonlocal completed_files
            completed_files += 1
            
            if not result['success']:
                failed_files.append({'file': filename, 'error': result['error']})
            
            # Process next file
            Clock.schedule_once(lambda dt: process_next_file(file_index + 1), 0.1)
        
        # Add file asynchronously
        audio_vault_core.add_audio_file(file_path, on_file_added)
    
    # Start processing
    Clock.schedule_once(lambda dt: process_next_file(), 0.1)

def show_add_results(total, failed_count, failed_files):
    """Show results of adding audio files"""
    success_count = total - failed_count
    
    if failed_count == 0:
        # All successful
        popup = Popup(
            title='✅ Files Added Successfully',
            content=Label(text=f'All {success_count} audio files were added to your vault!'),
            size_hint=(0.7, 0.4),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 3)
    else:
        # Some failures - show summary
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        
        summary_text = f'📊 Results:\n✅ {success_count} files added successfully\n❌ {failed_count} files failed'
        
        summary_label = Label(
            text=summary_text,
            font_size=16,
            halign='center'
        )
        summary_label.bind(size=summary_label.setter('text_size'))
        content.add_widget(summary_label)
        
        close_btn = Button(
            text='❌ Close',
            size_hint_y=None,
            height=dp(50)
        )
        content.add_widget(close_btn)
        
        popup = Popup(
            title='📊 Add Audio Results',
            content=content,
            size_hint=(0.7, 0.5),
            auto_dismiss=False
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

# ===============================================================================
# AUDIO FILE INFO AND OPTIONS DIALOGS
# ===============================================================================

def show_audio_info_dialog(audio_file):
    """Show detailed audio file information"""
    content = BoxLayout(orientation='vertical', spacing=10, padding=15)
    
    # Basic info
    basic_info = f"""📁 {audio_file['display_name']}
📊 {audio_file['format_info']} • {audio_file['size_mb']:.1f} MB
⏱️ Duration: {audio_file['duration_str']}
📅 Added: {datetime.fromisoformat(audio_file['added_date']).strftime("%Y-%m-%d %H:%M")}"""
    
    # Add metadata if available
    extracted_fields = audio_file.get('metadata', {}).get('extracted_fields', {})
    if extracted_fields:
        basic_info += "\n\n🎵 Metadata:"
        for field, value in list(extracted_fields.items())[:5]:  # Show first 5 fields
            if not field.startswith('raw_') and value:
                clean_field = field.replace('_', ' ').title()
                basic_info += f"\n• {clean_field}: {value}"
    
    basic_label = Label(
        text=basic_info,
        font_size=14,
        halign='left'
    )
    basic_label.bind(size=basic_label.setter('text_size'))
    content.add_widget(basic_label)
    
    # Close button
    close_btn = Button(
        text='❌ Close',
        size_hint_y=None,
        height=dp(50)
    )
    content.add_widget(close_btn)
    
    popup = Popup(
        title=f'ℹ️ Audio Information',
        content=content,
        size_hint=(0.8, 0.7),
        auto_dismiss=False
    )
    
    close_btn.bind(on_press=popup.dismiss)
    popup.open()

def show_audio_options(audio_file, audio_vault_core, refresh_callback):
    """Show audio file options menu"""
    content = BoxLayout(orientation='vertical', spacing=10, padding=15)
    
    # File info
    info_text = f"🎵 {audio_file['display_name']}\n📊 {audio_file['format_info']} • {audio_file['size_mb']:.1f} MB"
    
    info_label = Label(
        text=info_text,
        font_size=14,
        halign='center'
    )
    info_label.bind(size=info_label.setter('text_size'))
    content.add_widget(info_label)
    
    # Action buttons
    button_layout = BoxLayout(orientation='vertical', spacing=8)
    
    play_btn = Button(
        text='▶️ Play Audio',
        background_color=(0.2, 0.6, 0.8, 1),
        size_hint_y=None,
        height=dp(50)
    )
    
    export_btn = Button(
        text='📤 Export File',
        background_color=(0.6, 0.4, 0.8, 1),
        size_hint_y=None,
        height=dp(50)
    )
    
    delete_btn = Button(
        text='🗑️ Delete',
        background_color=(0.8, 0.2, 0.2, 1),
        size_hint_y=None,
        height=dp(50)
    )
    
    cancel_btn = Button(
        text='❌ Cancel',
        background_color=(0.5, 0.5, 0.5, 1),
        size_hint_y=None,
        height=dp(50)
    )
    
    button_layout.add_widget(play_btn)
    button_layout.add_widget(export_btn)
    button_layout.add_widget(delete_btn)
    button_layout.add_widget(cancel_btn)
    
    content.add_widget(button_layout)
    
    popup = Popup(
        title='🎵 Audio Options',
        content=content,
        size_hint=(0.7, 0.7),
        auto_dismiss=False
    )
    
    def handle_play(instance):
        popup.dismiss()
        play_audio_file_system(audio_file)
    
    def handle_export(instance):
        popup.dismiss()
        export_audio_file(audio_file, audio_vault_core)
    
    def handle_delete(instance):
        popup.dismiss()
        confirm_delete_audio(audio_file, audio_vault_core, refresh_callback, None)
    
    play_btn.bind(on_press=handle_play)
    export_btn.bind(on_press=handle_export)
    delete_btn.bind(on_press=handle_delete)
    cancel_btn.bind(on_press=popup.dismiss)
    
    popup.open()

def play_audio_file_system(audio_file):
    """Play audio file using system default player"""
    try:
        import subprocess
        import platform
        
        audio_path = audio_file['vault_path']
        
        if not os.path.exists(audio_path):
            popup = Popup(
                title='❌ File Not Found',
                content=Label(text='Audio file not found on disk.'),
                size_hint=(0.6, 0.3),
                auto_dismiss=True
            )
            popup.open()
            Clock.schedule_once(lambda dt: popup.dismiss(), 2)
            return
        
        # Use device's native audio player
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(audio_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", audio_path])
            else:  # Linux
                subprocess.run(["xdg-open", audio_path])
            
            # Show confirmation
            popup = Popup(
                title='🎵 Opening Audio',
                content=Label(text=f'Opening in device audio player:\n{audio_file["display_name"]}'),
                size_hint=(0.7, 0.4),
                auto_dismiss=True
            )
            popup.open()
            Clock.schedule_once(lambda dt: popup.dismiss(), 2)
            
        except Exception as e:
            # Fallback: show file location
            popup = Popup(
                title='🎵 Audio File',
                content=Label(text=f'Audio File: {audio_file["display_name"]}\n\nLocation: {audio_path}\n\nPlease open with your preferred audio player.'),
                size_hint=(0.8, 0.5),
                auto_dismiss=True
            )
            popup.open()
            Clock.schedule_once(lambda dt: popup.dismiss(), 4)
            
    except Exception as e:
        print(f"Error opening audio file: {e}")
        popup = Popup(
            title='❌ Error',
            content=Label(text=f'Could not open audio file:\n{str(e)}'),
            size_hint=(0.7, 0.4),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 3)

# ===============================================================================
# EXPORT DIALOGS
# ===============================================================================

def export_audio_file(audio_file, audio_vault_core):
    """Export audio file using cross-platform folder picker"""
    if PLYER_AVAILABLE:
        export_with_plyer_picker(audio_file, audio_vault_core)
    else:
        export_with_fallback_picker(audio_file, audio_vault_core)

def export_with_plyer_picker(audio_file, audio_vault_core):
    """Export using plyer folder picker"""
    try:
        def on_folder_selection(selection):
            if selection:
                # plyer returns a list, take the first folder
                folder_path = selection[0] if isinstance(selection, list) else selection
                destination_path = os.path.join(folder_path, audio_file['original_filename'])
                Clock.schedule_once(lambda dt: export_audio_file_with_progress(audio_file, destination_path, audio_vault_core), 0)
            else:
                # User cancelled
                pass
        
        # Use plyer's folder chooser
        filechooser.choose_dir(
            on_selection=on_folder_selection,
            title="Select Export Destination Folder"
        )
        
    except Exception as e:
        print(f"Plyer export picker error: {e}")
        export_with_fallback_picker(audio_file, audio_vault_core)

def export_with_fallback_picker(audio_file, audio_vault_core):
    """Fallback export dialog using Kivy file chooser"""
    content = BoxLayout(orientation='vertical', spacing=15, padding=15)
    
    info_text = f'📤 Export Audio File:\n{audio_file["display_name"]}\n{audio_file["format_info"]} • {audio_file["size_mb"]:.1f} MB'
    
    info_label = Label(
        text=info_text,
        font_size=16,
        halign='center',
        size_hint_y=None,
        height=dp(100)
    )
    info_label.bind(size=info_label.setter('text_size'))
    content.add_widget(info_label)
    
    # File chooser for destination
    try:
        start_path = os.path.join(os.path.expanduser('~'), 'Music')
        if not os.path.exists(start_path):
            start_path = os.path.expanduser('~')
    except:
        start_path = os.getcwd()
    
    file_chooser = FileChooserIconView(
        path=start_path,
        dirselect=True,
        size_hint_y=0.6
    )
    content.add_widget(file_chooser)
    
    # Filename input
    filename_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
    
    filename_label = Label(
        text='Filename:',
        size_hint_x=0.3,
        font_size=14
    )
    filename_layout.add_widget(filename_label)
    
    filename_input = TextInput(
        text=audio_file['original_filename'],
        size_hint_x=0.7,
        multiline=False,
        font_size=14
    )
    filename_layout.add_widget(filename_input)
    
    content.add_widget(filename_layout)
    
    # Buttons
    button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=10)
    
    export_btn = Button(
        text='📤 Export Here',
        background_color=(0.6, 0.4, 0.8, 1),
        font_size=16
    )
    
    cancel_btn = Button(
        text='❌ Cancel',
        background_color=(0.5, 0.5, 0.5, 1),
        font_size=16
    )
    
    button_layout.add_widget(export_btn)
    button_layout.add_widget(cancel_btn)
    content.add_widget(button_layout)
    
    popup = Popup(
        title='📤 Export Audio File',
        content=content,
        size_hint=(0.9, 0.9),
        auto_dismiss=False
    )
    
    def do_export(instance):
        destination_dir = file_chooser.path
        filename = filename_input.text.strip()
        
        if not filename:
            filename = audio_file['original_filename']
        
        destination_path = os.path.join(destination_dir, filename)
        
        popup.dismiss()
        export_audio_file_with_progress(audio_file, destination_path, audio_vault_core)
    
    export_btn.bind(on_press=do_export)
    cancel_btn.bind(on_press=popup.dismiss)
    
    popup.open()

def export_audio_file_with_progress(audio_file, destination_path, audio_vault_core):
    """Export audio file with progress indication"""
    # Show progress popup
    progress_content = Label(
        text=f'📤 Exporting audio file...\n{audio_file["display_name"]}\n\nPlease wait...',
        halign='center',
        font_size=16
    )
    
    progress_popup = Popup(
        title='Exporting Audio',
        content=progress_content,
        size_hint=(0.7, 0.4),
        auto_dismiss=False
    )
    progress_popup.open()
    
    def do_export():
        result = audio_vault_core.export_audio_file(audio_file['id'], destination_path)
        Clock.schedule_once(lambda dt: finish_export(result), 0)
    
    def finish_export(result):
        progress_popup.dismiss()
        
        if result['success']:
            success_popup = Popup(
                title='✅ Export Successful',
                content=Label(text=f'Audio file exported to:\n{result["exported_path"]}'),
                size_hint=(0.8, 0.4),
                auto_dismiss=True
            )
            success_popup.open()
            Clock.schedule_once(lambda dt: success_popup.dismiss(), 4)
        else:
            error_popup = Popup(
                title='❌ Export Failed',
                content=Label(text=f'Could not export audio file:\n{result["error"]}'),
                size_hint=(0.8, 0.4),
                auto_dismiss=True
            )
            error_popup.open()
            Clock.schedule_once(lambda dt: error_popup.dismiss(), 4)
    
    # Start export in background
    thread = threading.Thread(target=do_export, daemon=True)
    thread.start()

# ===============================================================================
# DELETE DIALOGS
# ===============================================================================

def confirm_delete_audio(audio_file, audio_vault_core, refresh_callback, clear_selection_callback):
    """Confirm deletion of audio file"""
    content = BoxLayout(orientation='vertical', spacing=15, padding=15)
    
    warning_text = f"""⚠️ DELETE AUDIO FILE ⚠️

File: {audio_file['display_name']}
Format: {audio_file['format_info']}
Size: {audio_file['size_mb']:.1f} MB

This will move the file to the recycle bin.
You can restore it later if needed.

Are you sure you want to delete this audio file?"""
    
    warning_label = Label(
        text=warning_text,
        halign='center',
        font_size=14,
        color=(1, 0.8, 0, 1)
    )
    warning_label.bind(size=warning_label.setter('text_size'))
    content.add_widget(warning_label)
    
    button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=10)
    
    delete_btn = Button(
        text='🗑️ DELETE',
        background_color=(0.8, 0.2, 0.2, 1),
        font_size=16
    )
    
    cancel_btn = Button(
        text='❌ CANCEL',
        background_color=(0.5, 0.5, 0.5, 1),
        font_size=16
    )
    
    button_layout.add_widget(delete_btn)
    button_layout.add_widget(cancel_btn)
    content.add_widget(button_layout)
    
    popup = Popup(
        title='🗑️ Confirm Delete',
        content=content,
        size_hint=(0.8, 0.6),
        auto_dismiss=False
    )
    
    def delete_confirmed(instance):
        popup.dismiss()
        delete_audio_file_with_progress(audio_file, audio_vault_core, refresh_callback, clear_selection_callback)
    
    delete_btn.bind(on_press=delete_confirmed)
    cancel_btn.bind(on_press=popup.dismiss)
    
    popup.open()

def delete_audio_file_with_progress(audio_file, audio_vault_core, refresh_callback, clear_selection_callback):
    """Delete audio file with progress indication"""
    # Show progress popup
    progress_content = Label(
        text=f'🗑️ Deleting audio file...\n{audio_file["display_name"]}\n\nPlease wait...',
        halign='center',
        font_size=16
    )
    
    progress_popup = Popup(
        title='Deleting Audio',
        content=progress_content,
        size_hint=(0.7, 0.4),
        auto_dismiss=False
    )
    progress_popup.open()
    
    def do_delete():
        result = audio_vault_core.delete_audio_file(audio_file['id'])
        Clock.schedule_once(lambda dt: finish_delete(result), 0)
    
    def finish_delete(result):
        progress_popup.dismiss()
        
        if result['success']:
            if clear_selection_callback:
                clear_selection_callback()
            refresh_callback()
            
            message = 'Audio file moved to recycle bin successfully!\nYou can restore it later if needed.' if result.get('recycled') else 'Audio file deleted successfully!'
            
            success_popup = Popup(
                title='✅ File Deleted',
                content=Label(text=message),
                size_hint=(0.7, 0.4),
                auto_dismiss=True
            )
            success_popup.open()
            Clock.schedule_once(lambda dt: success_popup.dismiss(), 3)
        else:
            error_popup = Popup(
                title='❌ Delete Failed',
                content=Label(text=f'Could not delete audio file:\n{result["error"]}'),
                size_hint=(0.8, 0.4),
                auto_dismiss=True
            )
            error_popup.open()
            Clock.schedule_once(lambda dt: error_popup.dismiss(), 4)
    
    # Start deletion in background
    thread = threading.Thread(target=do_delete, daemon=True)
    thread.start()

# ===============================================================================
# STATISTICS DIALOG
# ===============================================================================

def show_detailed_stats_dialog(audio_vault_core):
    """Show detailed audio vault statistics"""
    stats_widget = AudioVaultStatsWidget(audio_vault_core)
    
    popup = Popup(
        title='📊 Audio Vault Statistics',
        content=stats_widget,
        size_hint=(0.9, 0.9),
        auto_dismiss=True
    )
    popup.open()

# ===============================================================================
# UTILITY DIALOGS
# ===============================================================================

def show_no_selection_popup(action):
    """Show popup when no audio file is selected"""
    popup = Popup(
        title='No Audio Selected',
        content=Label(text=f'Please select an audio file first to {action} it.'),
        size_hint=(0.7, 0.3),
        auto_dismiss=True
    )
    popup.open()
    Clock.schedule_once(lambda dt: popup.dismiss(), 2)