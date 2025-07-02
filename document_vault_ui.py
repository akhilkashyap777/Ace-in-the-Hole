from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from document_vault_ui_components import DocumentComponents

class DocumentVaultUI(MDBoxLayout):
    
    def __init__(self, document_vault_core, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.vault_core = document_vault_core
        self.current_filter = None
        self.selected_document = None
        self.document_widgets = []
        
        self.md_bg_color = [0.37, 0.49, 0.55, 1]
        
        self.components = DocumentComponents(self)
        
        self.build_ui()
        
        Clock.schedule_once(lambda dt: self.refresh_documents(), 0.1)
    
    def build_ui(self):
        self.build_header()
        self.build_category_filter()
        self.build_document_list()
        self.build_bottom_buttons()
    
    def build_header(self):
        header = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(120),
            padding=[20, 20, 20, 10],
            spacing=10
        )
        
        title = MDLabel(
            text='DOCUMENT VAULT',
            font_style="H3",
            text_color="white",
            halign="center",
            bold=True
        )
        header.add_widget(title)
        
        stats_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=15
        )
        
        self.stats_label = MDLabel(
            text='Loading...',
            font_style="Body1",
            text_color=[0.8, 0.8, 0.8, 1],
            halign="center",
            size_hint_x=0.4
        )
        stats_row.add_widget(self.stats_label)
        
        self.add_btn = MDRaisedButton(
            text='Add Files',
            md_bg_color=[0.2, 0.7, 0.3, 1],
            text_color="white",
            size_hint_x=0.6,
            elevation=3
        )
        self.add_btn.bind(on_press=self.add_documents)
        stats_row.add_widget(self.add_btn)
        
        header.add_widget(stats_row)
        self.add_widget(header)
    
    def build_category_filter(self):
        filter_scroll = MDScrollView(
            size_hint_y=None,
            height=dp(60),
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=dp(4),
            bar_color=[0.46, 0.53, 0.6, 0.7],
            bar_inactive_color=[0.7, 0.7, 0.7, 0.3]
        )
        
        filter_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            height=dp(50),
            spacing=5,
            padding=[10, 5],
            adaptive_width=True
        )
        
        all_btn = MDFlatButton(
            text='All Files',
            size_hint_x=None,
            width=dp(100),
            text_color="white"
        )
        all_btn.bind(on_press=lambda x: self.filter_by_category(None))
        filter_layout.add_widget(all_btn)
        
        for category, config in self.vault_core.FILE_CATEGORIES.items():
            if category == 'other':
                continue
                
            btn = MDFlatButton(
                text=config['display_name'],
                size_hint_x=None,
                width=dp(120),
                text_color="white"
            )
            btn.bind(on_press=lambda x, cat=category: self.filter_by_category(cat))
            filter_layout.add_widget(btn)
        
        other_config = self.vault_core.FILE_CATEGORIES['other']
        other_btn = MDFlatButton(
            text=other_config['display_name'],
            size_hint_x=None,
            width=dp(100),
            text_color="white"
        )
        other_btn.bind(on_press=lambda x: self.filter_by_category('other'))
        filter_layout.add_widget(other_btn)
        
        filter_scroll.add_widget(filter_layout)
        self.add_widget(filter_scroll)
    
    def build_document_list(self):
        scroll = MDScrollView(
            bar_width=dp(4),
            bar_color=[0.46, 0.53, 0.6, 0.7],
            bar_inactive_color=[0.7, 0.7, 0.7, 0.3]
        )
        
        self.document_grid = MDGridLayout(
            cols=1,
            spacing=10,
            padding=[20, 10, 20, 10],
            size_hint_y=None,
            adaptive_height=True
        )
        
        scroll.add_widget(self.document_grid)
        self.add_widget(scroll)
    
    def build_bottom_buttons(self):
        bottom_bar = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(70),
            padding=15,
            spacing=12,
            elevation=8,
            md_bg_color=[0.25, 0.29, 0.31, 1]
        )
        
        refresh_btn = MDFlatButton(
            text='Refresh',
            text_color="white",
            size_hint_x=0.2
        )
        refresh_btn.bind(on_press=lambda x: self.refresh_documents())
        bottom_bar.add_widget(refresh_btn)
        
        self.view_btn = MDFlatButton(
            text='View',
            text_color=[0.4, 0.8, 0.9, 1],
            size_hint_x=0.2
        )
        self.view_btn.bind(on_press=self.view_selected_document)
        bottom_bar.add_widget(self.view_btn)
        
        self.export_btn = MDFlatButton(
            text='Export',
            text_color=[0.6, 0.6, 0.9, 1],
            size_hint_x=0.2
        )
        self.export_btn.bind(on_press=self.export_selected_document)
        bottom_bar.add_widget(self.export_btn)
        
        self.delete_btn = MDFlatButton(
            text='Delete',
            text_color=[0.9, 0.4, 0.4, 1],
            size_hint_x=0.2
        )
        self.delete_btn.bind(on_press=self.delete_selected_document)
        bottom_bar.add_widget(self.delete_btn)
        
        back_btn = MDFlatButton(
            text='Back',
            text_color=[0.7, 0.7, 0.7, 1],
            size_hint_x=0.2
        )
        back_btn.bind(on_press=self.back_to_vault)
        bottom_bar.add_widget(back_btn)
        
        self.add_widget(bottom_bar)
    
    def filter_by_category(self, category):
        self.current_filter = category
        self.selected_document = None
        self.refresh_documents()
    
    def add_documents(self, instance):
        if self.vault_core.processing:
            return
        
        self.add_btn.disabled = True
        self.add_btn.text = 'Processing...'
        
        self.vault_core.request_permissions()
        
        def on_documents_added(imported_files, skipped_files):
            self.add_btn.disabled = False
            self.add_btn.text = 'Add Files'
            
            self.components.show_import_results(imported_files, skipped_files)
            
            if imported_files:
                self.refresh_documents()
        
        self.vault_core.select_documents_from_storage(on_documents_added)
    
    def refresh_documents(self):
        self.cleanup_document_widgets()
        self.document_grid.clear_widgets()
        self.selected_document = None
        
        documents = self.vault_core.get_vault_documents(self.current_filter)
        
        self.update_stats_display(documents)
        
        if not documents:
            empty_widget = self.components.create_empty_state_widget(self.current_filter)
            self.document_grid.add_widget(empty_widget)
            return
        
        for doc in documents:
            doc_widget = self.create_document_widget(doc)
            self.document_grid.add_widget(doc_widget)
            self.document_widgets.append(doc_widget)
    
    def update_stats_display(self, documents):
        try:
            if self.current_filter:
                category_name = self.vault_core.FILE_CATEGORIES[self.current_filter]['display_name']
                total_size = sum(doc['size'] for doc in documents) / (1024 * 1024)
                self.stats_label.text = f"{len(documents)} {category_name}\n{total_size:.1f} MB"
            else:
                total_size = sum(doc['size'] for doc in documents) / (1024 * 1024)
                self.stats_label.text = f"{len(documents)} files\n{total_size:.1f} MB"
        except:
            self.stats_label.text = f"{len(documents)} files"
    
    def cleanup_document_widgets(self):
        self.document_widgets.clear()
    
    def create_document_widget(self, document):
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
        
        info_layout = MDBoxLayout(orientation='vertical', size_hint_x=0.6)
        
        category_info = document['category_info']
        name_text = document['original_name']
        
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
        
        details_text = f"{category_info['display_name']} • {size_text} • {document['modified'].strftime('%Y-%m-%d %H:%M')}"
        
        details_label = MDLabel(
            text=details_text,
            font_style="Caption",
            halign='left',
            text_color=[0.7, 0.7, 0.7, 1]
        )
        details_label.bind(size=details_label.setter('text_size'))
        info_layout.add_widget(details_label)
        
        doc_card.add_widget(info_layout)
        
        button_layout = MDBoxLayout(orientation='horizontal', size_hint_x=0.4, spacing=5)
        
        select_btn = MDRaisedButton(
            text='Select',
            size_hint_x=0.5,
            md_bg_color=[0.2, 0.6, 0.8, 1],
            text_color="white",
            elevation=2
        )
        select_btn.bind(on_press=lambda x: self.select_document(document))
        button_layout.add_widget(select_btn)
        
        view_btn = MDFlatButton(
            text='View',
            size_hint_x=0.25,
            text_color=[0.4, 0.8, 0.9, 1]
        )
        view_btn.bind(on_press=lambda x: self.quick_view_document(document))
        button_layout.add_widget(view_btn)
        
        export_btn = MDFlatButton(
            text='Export',
            size_hint_x=0.25,
            text_color=[0.6, 0.6, 0.9, 1]
        )
        export_btn.bind(on_press=lambda x: self.quick_export_document(document))
        button_layout.add_widget(export_btn)
        
        doc_card.add_widget(button_layout)
        
        return doc_card
    
    def select_document(self, document):
        self.selected_document = document
        
        content = MDLabel(
            text=f"Selected: {document['original_name']}\n\nCategory: {document['category_info']['display_name']}\nSize: {document['size'] / (1024 * 1024):.1f} MB\n\nUse the buttons below to view, export, or delete this file.",
            text_color="white",
            halign='center'
        )
        
        popup = Popup(
            title='Document Selected',
            content=content,
            size_hint=(0.7, 0.5),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def quick_view_document(self, document):
        self.selected_document = document
        self.view_selected_document(None)
    
    def quick_export_document(self, document):
        self.selected_document = document
        self.export_selected_document(None)
    
    def view_selected_document(self, instance):
        if not self.selected_document:
            self.components.show_no_selection_message("view")
            return
        
        self.components.show_document_view(self.selected_document)
    
    def export_selected_document(self, instance):
        if not self.selected_document:
            self.components.show_no_selection_message("export")
            return
        
        self.components.show_export_dialog(self.selected_document)

    def delete_selected_document(self, instance):
        if not self.selected_document:
            self.components.show_no_selection_message("delete")
            return
        
        self.components.show_delete_dialog(self.selected_document, self.refresh_documents)
    
    def back_to_vault(self, instance):
        self.cleanup_document_widgets()
        
        if hasattr(self.vault_core.app, 'show_vault_main'):
            self.vault_core.app.show_vault_main()


def integrate_document_vault(vault_app):
    from document_vault_core import DocumentVaultCore
    
    vault_app.document_vault = DocumentVaultCore(vault_app)
    
    def show_document_vault():
        vault_app.main_layout.clear_widgets()
        
        document_ui = DocumentVaultUI(vault_app.document_vault)
        vault_app.main_layout.add_widget(document_ui)
        
        vault_app.current_screen = 'document_vault'
    
    vault_app.show_document_vault = show_document_vault
    
    return vault_app.document_vault