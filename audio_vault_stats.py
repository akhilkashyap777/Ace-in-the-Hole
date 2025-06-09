import os
from datetime import datetime, timedelta
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp

class AudioVaultStatsWidget(BoxLayout):
    """
    Audio Vault Statistics Widget - Detailed analytics and insights
    """
    
    def __init__(self, audio_vault_core, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.audio_vault = audio_vault_core
        
        # Create UI
        self.create_stats_interface()
        
        # Load stats
        Clock.schedule_once(lambda dt: self.refresh_stats(), 0.1)
    
    def create_stats_interface(self):
        """Create the statistics interface"""
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), padding=10)
        
        title = Label(
            text='📊 Audio Vault Statistics',
            font_size=20,
            size_hint_x=0.8
        )
        header.add_widget(title)
        
        refresh_btn = Button(
            text='🔄 Refresh',
            size_hint_x=0.2,
            font_size=14
        )
        refresh_btn.bind(on_press=self.refresh_stats)
        header.add_widget(refresh_btn)
        
        self.add_widget(header)
        
        # Create scrollable content
        scroll = ScrollView()
        
        self.stats_layout = BoxLayout(
            orientation='vertical',
            spacing=15,
            padding=15,
            size_hint_y=None
        )
        self.stats_layout.bind(minimum_height=self.stats_layout.setter('height'))
        
        scroll.add_widget(self.stats_layout)
        self.add_widget(scroll)
        
        # Close button
        close_btn = Button(
            text='❌ Close',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        close_btn.bind(on_press=self.close_stats)
        self.add_widget(close_btn)
    
    def refresh_stats(self, instance=None):
        """Refresh all statistics"""
        # Clear existing content
        self.stats_layout.clear_widgets()
        
        # Get basic stats
        stats = self.audio_vault.get_vault_statistics()
        
        # Create stat sections
        self.create_overview_section(stats)
        self.create_format_breakdown_section(stats)
        self.create_size_analysis_section()
        self.create_duration_analysis_section()
        self.create_recent_activity_section()
        self.create_metadata_insights_section()
    
    def create_overview_section(self, stats):
        """Create overview statistics section"""
        section = self.create_section_widget("📊 Overview", (0.2, 0.6, 0.8, 1))
        
        # Format duration nicely
        total_minutes = stats['total_duration_minutes']
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        
        if hours > 24:
            days = int(hours // 24)
            remaining_hours = int(hours % 24)
            duration_str = f"{days}d {remaining_hours}h {minutes}m"
        elif hours > 0:
            duration_str = f"{hours}h {minutes}m"
        else:
            duration_str = f"{minutes}m"
        
        overview_text = f"""📁 Total Files: {stats['total_files']}
💾 Total Size: {stats['total_size_mb']} MB ({stats['total_size_mb'] / 1024:.1f} GB)
⏱️ Total Duration: {duration_str}
📅 Added This Week: {stats['recent_files']}"""
        
        if stats['total_files'] > 0:
            avg_size = stats['total_size_mb'] / stats['total_files']
            avg_duration = stats['total_duration_minutes'] / stats['total_files']
            overview_text += f"""
📊 Average File Size: {avg_size:.1f} MB
⏱️ Average Duration: {avg_duration:.1f} minutes"""
        
        overview_label = Label(
            text=overview_text,
            font_size=14,
            halign='left',
            size_hint_y=None,
            height=dp(160)
        )
        overview_label.bind(size=overview_label.setter('text_size'))
        section.add_widget(overview_label)
        
        self.stats_layout.add_widget(section)
    
    def create_format_breakdown_section(self, stats):
        """Create format breakdown section"""
        section = self.create_section_widget("🎵 Format Breakdown", (0.6, 0.4, 0.8, 1))
        
        if stats['formats']:
            # Sort formats by count
            sorted_formats = sorted(stats['formats'].items(), key=lambda x: x[1], reverse=True)
            
            format_text = ""
            for format_name, count in sorted_formats:
                percentage = (count / stats['total_files']) * 100
                format_text += f"• {format_name}: {count} files ({percentage:.1f}%)\n"
            
            format_label = Label(
                text=format_text,
                font_size=13,
                halign='left',
                size_hint_y=None,
                height=dp(len(sorted_formats) * 25 + 20)
            )
            format_label.bind(size=format_label.setter('text_size'))
            section.add_widget(format_label)
        else:
            empty_label = Label(
                text="No audio files in vault",
                font_size=14,
                size_hint_y=None,
                height=dp(40)
            )
            section.add_widget(empty_label)
        
        self.stats_layout.add_widget(section)
    
    def create_size_analysis_section(self):
        """Create size analysis section"""
        section = self.create_section_widget("📊 Size Analysis", (0.8, 0.6, 0.2, 1))
        
        try:
            files = self.audio_vault.get_audio_files()
            
            if not files:
                empty_label = Label(
                    text="No files to analyze",
                    font_size=14,
                    size_hint_y=None,
                    height=dp(40)
                )
                section.add_widget(empty_label)
                self.stats_layout.add_widget(section)
                return
            
            # Categorize by size
            size_categories = {
                'Small (< 5 MB)': 0,
                'Medium (5-20 MB)': 0,
                'Large (20-50 MB)': 0,
                'Very Large (> 50 MB)': 0
            }
            
            largest_file = None
            largest_size = 0
            
            for file_info in files:
                size_mb = file_info['size_mb']
                
                if size_mb < 5:
                    size_categories['Small (< 5 MB)'] += 1
                elif size_mb < 20:
                    size_categories['Medium (5-20 MB)'] += 1
                elif size_mb < 50:
                    size_categories['Large (20-50 MB)'] += 1
                else:
                    size_categories['Very Large (> 50 MB)'] += 1
                
                if size_mb > largest_size:
                    largest_size = size_mb
                    largest_file = file_info
            
            size_text = "File Size Distribution:\n\n"
            for category, count in size_categories.items():
                if count > 0:
                    percentage = (count / len(files)) * 100
                    size_text += f"• {category}: {count} ({percentage:.1f}%)\n"
            
            if largest_file:
                size_text += f"\n🏆 Largest File:\n{largest_file['display_name']}\n({largest_size:.1f} MB)"
            
            size_label = Label(
                text=size_text,
                font_size=13,
                halign='left',
                size_hint_y=None,
                height=dp(200)
            )
            size_label.bind(size=size_label.setter('text_size'))
            section.add_widget(size_label)
            
        except Exception as e:
            error_label = Label(
                text=f"Error analyzing sizes: {str(e)}",
                font_size=12,
                size_hint_y=None,
                height=dp(40)
            )
            section.add_widget(error_label)
        
        self.stats_layout.add_widget(section)
    
    def create_duration_analysis_section(self):
        """Create duration analysis section"""
        section = self.create_section_widget("⏱️ Duration Analysis", (0.4, 0.8, 0.6, 1))
        
        try:
            files = self.audio_vault.get_audio_files()
            
            if not files:
                empty_label = Label(
                    text="No files to analyze",
                    font_size=14,
                    size_hint_y=None,
                    height=dp(40)
                )
                section.add_widget(empty_label)
                self.stats_layout.add_widget(section)
                return
            
            # Categorize by duration
            duration_categories = {
                'Short (< 3 min)': 0,
                'Medium (3-10 min)': 0,
                'Long (10-30 min)': 0,
                'Very Long (> 30 min)': 0,
                'Unknown': 0
            }
            
            longest_file = None
            longest_duration = 0
            total_with_duration = 0
            
            for file_info in files:
                duration = file_info['metadata'].get('duration')
                
                if duration is None:
                    duration_categories['Unknown'] += 1
                    continue
                
                total_with_duration += 1
                duration_minutes = duration / 60
                
                if duration_minutes < 3:
                    duration_categories['Short (< 3 min)'] += 1
                elif duration_minutes < 10:
                    duration_categories['Medium (3-10 min)'] += 1
                elif duration_minutes < 30:
                    duration_categories['Long (10-30 min)'] += 1
                else:
                    duration_categories['Very Long (> 30 min)'] += 1
                
                if duration > longest_duration:
                    longest_duration = duration
                    longest_file = file_info
            
            duration_text = "Duration Distribution:\n\n"
            for category, count in duration_categories.items():
                if count > 0:
                    percentage = (count / len(files)) * 100
                    duration_text += f"• {category}: {count} ({percentage:.1f}%)\n"
            
            if longest_file:
                hours = int(longest_duration // 3600)
                minutes = int((longest_duration % 3600) // 60)
                seconds = int(longest_duration % 60)
                
                if hours > 0:
                    longest_str = f"{hours}h {minutes}m {seconds}s"
                else:
                    longest_str = f"{minutes}m {seconds}s"
                
                duration_text += f"\n🏆 Longest File:\n{longest_file['display_name']}\n({longest_str})"
            
            duration_label = Label(
                text=duration_text,
                font_size=13,
                halign='left',
                size_hint_y=None,
                height=dp(220)
            )
            duration_label.bind(size=duration_label.setter('text_size'))
            section.add_widget(duration_label)
            
        except Exception as e:
            error_label = Label(
                text=f"Error analyzing durations: {str(e)}",
                font_size=12,
                size_hint_y=None,
                height=dp(40)
            )
            section.add_widget(error_label)
        
        self.stats_layout.add_widget(section)
    
    def create_recent_activity_section(self):
        """Create recent activity section"""
        section = self.create_section_widget("📅 Recent Activity", (0.2, 0.8, 0.4, 1))
        
        try:
            files = self.audio_vault.get_audio_files(sort_by='added_date')
            
            if not files:
                empty_label = Label(
                    text="No recent activity",
                    font_size=14,
                    size_hint_y=None,
                    height=dp(40)
                )
                section.add_widget(empty_label)
                self.stats_layout.add_widget(section)
                return
            
            # Analyze recent activity
            now = datetime.now()
            activity_periods = {
                'Today': 0,
                'This Week': 0,
                'This Month': 0,
                'Older': 0
            }
            
            recent_files = []
            
            for file_info in files:
                added_date = datetime.fromisoformat(file_info['added_date'])
                days_ago = (now - added_date).days
                
                if days_ago == 0:
                    activity_periods['Today'] += 1
                elif days_ago < 7:
                    activity_periods['This Week'] += 1
                elif days_ago < 30:
                    activity_periods['This Month'] += 1
                else:
                    activity_periods['Older'] += 1
                
                # Get recent files for display
                if len(recent_files) < 5 and days_ago < 7:
                    recent_files.append(file_info)
            
            activity_text = "Files Added:\n\n"
            for period, count in activity_periods.items():
                if count > 0:
                    activity_text += f"• {period}: {count}\n"
            
            if recent_files:
                activity_text += "\n📁 Recent Files:\n"
                for file_info in recent_files:
                    added_date = datetime.fromisoformat(file_info['added_date'])
                    date_str = added_date.strftime("%m/%d %H:%M")
                    filename = file_info['display_name']
                    if len(filename) > 25:
                        filename = filename[:22] + "..."
                    activity_text += f"• {date_str}: {filename}\n"
            
            activity_label = Label(
                text=activity_text,
                font_size=12,
                halign='left',
                size_hint_y=None,
                height=dp(max(200, len(recent_files) * 20 + 120))
            )
            activity_label.bind(size=activity_label.setter('text_size'))
            section.add_widget(activity_label)
            
        except Exception as e:
            error_label = Label(
                text=f"Error analyzing activity: {str(e)}",
                font_size=12,
                size_hint_y=None,
                height=dp(40)
            )
            section.add_widget(error_label)
        
        self.stats_layout.add_widget(section)
    
    def create_metadata_insights_section(self):
        """Create dynamic metadata insights section"""
        section = self.create_section_widget("🎨 Metadata Insights", (0.8, 0.4, 0.6, 1))
        
        try:
            files = self.audio_vault.get_audio_files()
            
            if not files:
                empty_label = Label(
                    text="No metadata to analyze",
                    font_size=14,
                    size_hint_y=None,
                    height=dp(40)
                )
                section.add_widget(empty_label)
                self.stats_layout.add_widget(section)
                return
            
            # Dynamic metadata analysis - collect ALL fields found
            all_fields = {}
            files_with_metadata = 0
            files_with_artwork = 0
            
            for file_info in files:
                extracted_fields = file_info.get('metadata', {}).get('extracted_fields', {})
                
                if extracted_fields:
                    files_with_metadata += 1
                    
                    # Count occurrence of each metadata field
                    for field_name, value in extracted_fields.items():
                        if value and not field_name.startswith('raw_'):  # Skip empty and raw fields
                            if field_name not in all_fields:
                                all_fields[field_name] = {'count': 0, 'sample_values': set()}
                            
                            all_fields[field_name]['count'] += 1
                            # Keep sample values (limit to 3 for display)
                            if len(all_fields[field_name]['sample_values']) < 3:
                                all_fields[field_name]['sample_values'].add(str(value))
                
                # Check for artwork
                if file_info.get('thumbnail_path') and os.path.exists(file_info['thumbnail_path']):
                    files_with_artwork += 1
            
            # Build dynamic metadata text
            metadata_text = f"Metadata Coverage:\n\n"
            metadata_text += f"• Files with metadata: {files_with_metadata}/{len(files)} ({(files_with_metadata/len(files)*100):.1f}%)\n"
            metadata_text += f"• Files with artwork: {files_with_artwork}/{len(files)} ({(files_with_artwork/len(files)*100):.1f}%)\n"
            
            if all_fields:
                metadata_text += f"\n📋 Available Fields:\n"
                
                # Sort fields by frequency
                sorted_fields = sorted(all_fields.items(), key=lambda x: x[1]['count'], reverse=True)
                
                for field_name, field_info in sorted_fields[:10]:  # Show top 10 fields
                    count = field_info['count']
                    percentage = (count / len(files)) * 100
                    
                    # Clean up field name for display
                    display_name = field_name.replace('_', ' ').title()
                    
                    metadata_text += f"• {display_name}: {count} files ({percentage:.1f}%)\n"
            
            # Calculate dynamic height based on content
            content_lines = metadata_text.count('\n') + 2
            calculated_height = max(200, content_lines * 20)
            
            metadata_label = Label(
                text=metadata_text,
                font_size=12,
                halign='left',
                size_hint_y=None,
                height=dp(calculated_height)
            )
            metadata_label.bind(size=metadata_label.setter('text_size'))
            section.add_widget(metadata_label)
            
        except Exception as e:
            error_label = Label(
                text=f"Error analyzing metadata: {str(e)}",
                font_size=12,
                size_hint_y=None,
                height=dp(40)
            )
            section.add_widget(error_label)
        
        self.stats_layout.add_widget(section)
    
    def create_section_widget(self, title, color):
        """Create a styled section widget"""
        section = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=5,
            padding=10
        )
        
        # Section header
        header = Label(
            text=title,
            font_size=16,
            bold=True,
            size_hint_y=None,
            height=dp(30),
            color=color
        )
        section.add_widget(header)
        
        # Section will auto-size based on content
        section.bind(minimum_height=section.setter('height'))
        
        return section
    
    def close_stats(self, instance):
        """Close the statistics widget"""
        # Find parent popup and dismiss it
        parent = self.parent
        while parent:
            if isinstance(parent, Popup):
                parent.dismiss()
                break
            parent = parent.parent

print("✅ Audio Vault Statistics widget loaded successfully")
print("📊 Comprehensive analytics and insights for audio files")
print("🎵 Format breakdown, size analysis, and metadata insights")