from video_vault_operations import VideoVaultCore, ANDROID, IMAGEIO_AVAILABLE

# Import UI components (unchanged, but will benefit from core optimizations)
from video_vault_ui import VideoVault, VideoGalleryWidget, integrate_video_vault

# Re-export the main classes and functions for backwards compatibility
__all__ = [
    'VideoVault',
    'VideoVaultCore', 
    'VideoGalleryWidget',
    'integrate_video_vault',
    'ANDROID',
    'IMAGEIO_AVAILABLE'
]

# You can also import specific components if needed:
# from video_vault_operations import VideoVaultCore  # Optimized core
# from video_vault_ui import VideoGalleryWidget      # UI components

print("✅ Video Vault module loaded successfully - OPTIMIZED VERSION")
print(f"🖥️ Platform: {'Android' if ANDROID else 'Desktop'}")
print(f"🎬 ImageIO available: {IMAGEIO_AVAILABLE}")
print("🧹 Memory leak fixes: ResourceManager, WeakRefs, periodic cleanup")
print("⚡ Performance optimizations: Caching, background processing, ffprobe")

# For debugging, you can enable verbose logging by setting this to True
DEBUG_MODE = True

if DEBUG_MODE:
    print("🔧 DEBUG MODE ENABLED - Verbose logging active")
    print("📁 Video files will be stored in: vault_videos/")
    print("🖼️ Thumbnails will be stored in: vault_videos/thumbnails/")
    print("💾 Video info cache will be stored in: vault_videos/video_info_cache.json")
    print("🗑️ Enhanced deletion methods enabled for Windows file locking issues")
    print("🧹 Periodic cleanup every 30 seconds to prevent memory leaks")
    print("⚡ Thumbnail generation optimized with caching and background processing")

# Additional helper functions for the optimized version

def get_memory_usage_stats():
    """Get current memory usage statistics for debugging"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': round(memory_info.rss / (1024 * 1024), 1),  # Resident Set Size
            'vms_mb': round(memory_info.vms / (1024 * 1024), 1),  # Virtual Memory Size
            'percent': round(process.memory_percent(), 1)
        }
    except ImportError:
        return {'rss_mb': 0, 'vms_mb': 0, 'percent': 0}

def force_full_cleanup(vault_instance):
    """Force a complete cleanup of all resources (for debugging)"""
    if hasattr(vault_instance, 'resource_manager'):
        print("🧹 Forcing full cleanup...")
        cleaned = vault_instance.resource_manager.full_cleanup()
        
        # Also cleanup widgets if available
        if hasattr(vault_instance, 'cleanup_widgets'):
            vault_instance.cleanup_widgets()
        
        # Force garbage collection
        import gc
        collected = gc.collect()
        
        print(f"✅ Forced cleanup complete: {cleaned} resources, {collected} objects")
        
        # Show memory stats if available
        memory_stats = get_memory_usage_stats()
        if memory_stats['rss_mb'] > 0:
            print(f"📊 Memory usage: {memory_stats['rss_mb']} MB RSS, {memory_stats['percent']}%")
        
        return cleaned
    else:
        print("❌ No resource manager found")
        return 0

def cleanup_temp_files():
    """Clean up any temporary files marked for deletion"""
    import tempfile
    temp_dir = tempfile.gettempdir()
    
    try:
        cleaned = 0
        for filename in os.listdir(temp_dir):
            if filename.startswith('delete_me_') or filename.endswith('.DELETE_ME'):
                file_path = os.path.join(temp_dir, filename)
                try:
                    os.remove(file_path)
                    cleaned += 1
                    print(f"🧹 Cleaned up temp file: {filename}")
                except:
                    pass
        
        if cleaned > 0:
            print(f"✅ Cleaned up {cleaned} temporary files")
        return cleaned
    except Exception as e:
        print(f"Error cleaning temp files: {e}")
        return 0

def get_vault_statistics(vault_instance):
    """Get statistics about the video vault including memory usage"""
    try:
        videos = vault_instance.get_vault_videos()
        total_size = 0
        
        for video_path in videos:
            try:
                total_size += os.path.getsize(video_path)
            except:
                pass
        
        total_size_mb = round(total_size / (1024 * 1024), 1)
        
        # Get resource manager stats
        resource_stats = {}
        if hasattr(vault_instance, 'resource_manager'):
            rm = vault_instance.resource_manager
            resource_stats = {
                'imageio_readers': len(rm.imageio_readers),
                'video_players': len(rm.video_players),
                'temp_files': len(rm.temp_files),
                'background_threads': len(rm.background_threads)
            }
        
        # Get cache stats
        cache_stats = {}
        if hasattr(vault_instance, 'video_info_cache'):
            cache_stats = {
                'cache_entries': len(vault_instance.video_info_cache),
                'cache_file_exists': os.path.exists(vault_instance.video_info_cache_file)
            }
        
        return {
            'video_count': len(videos),
            'total_size_mb': total_size_mb,
            'vault_directory': vault_instance.vault_dir,
            'memory_stats': get_memory_usage_stats(),
            'resource_stats': resource_stats,
            'cache_stats': cache_stats
        }
    except Exception as e:
        print(f"Error getting vault statistics: {e}")
        return {
            'video_count': 0, 
            'total_size_mb': 0, 
            'vault_directory': 'Unknown',
            'memory_stats': {},
            'resource_stats': {},
            'cache_stats': {}
        }