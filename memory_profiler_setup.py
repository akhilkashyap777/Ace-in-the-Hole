# memory_profiler_setup.py - Memory profiling utilities for your vault app

import os
import gc
import tracemalloc
from memory_profiler import profile, memory_usage
from functools import wraps
import threading
import time

# Method 1: Decorator-based profiling for specific functions
def memory_profile(func):
    """Decorator to profile memory usage of individual functions"""
    @wraps(func)
    @profile
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

# Method 2: Context manager for profiling code blocks
class MemoryProfiler:
    def __init__(self, description="Memory usage"):
        self.description = description
        self.start_memory = 0
        
    def __enter__(self):
        gc.collect()  # Clean up before measuring
        self.start_memory = memory_usage()[0]
        print(f"🔍 {self.description} - Starting memory: {self.start_memory:.2f} MB")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        gc.collect()
        end_memory = memory_usage()[0]
        diff = end_memory - self.start_memory
        print(f"🔍 {self.description} - Ending memory: {end_memory:.2f} MB")
        print(f"🔍 {self.description} - Memory difference: {diff:+.2f} MB")
        if diff > 10:  # Alert if memory increased by more than 10MB
            print(f"⚠️  WARNING: Potential memory leak detected! (+{diff:.2f} MB)")

# Method 3: Continuous memory monitoring
class ContinuousMemoryMonitor:
    def __init__(self, interval=5):
        self.interval = interval
        self.monitoring = False
        self.thread = None
        self.memory_log = []
        
    def start_monitoring(self):
        self.monitoring = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"📊 Started continuous memory monitoring (every {self.interval}s)")
        
    def stop_monitoring(self):
        self.monitoring = False
        if self.thread:
            self.thread.join()
        self._analyze_memory_trend()
        
    def _monitor_loop(self):
        while self.monitoring:
            current_memory = memory_usage()[0]
            self.memory_log.append({
                'timestamp': time.time(),
                'memory': current_memory
            })
            print(f"📊 Memory: {current_memory:.2f} MB")
            time.sleep(self.interval)
            
    def _analyze_memory_trend(self):
        if len(self.memory_log) < 2:
            return
            
        start_memory = self.memory_log[0]['memory']
        end_memory = self.memory_log[-1]['memory']
        total_change = end_memory - start_memory
        
        print(f"\n📈 Memory Analysis:")
        print(f"   Start: {start_memory:.2f} MB")
        print(f"   End: {end_memory:.2f} MB") 
        print(f"   Total change: {total_change:+.2f} MB")
        
        # Check for consistent growth (potential leak)
        if len(self.memory_log) >= 5:
            recent_changes = []
            for i in range(1, min(6, len(self.memory_log))):
                change = self.memory_log[-i]['memory'] - self.memory_log[-i-1]['memory']
                recent_changes.append(change)
            
            avg_growth = sum(recent_changes) / len(recent_changes)
            if avg_growth > 1:  # Growing by more than 1MB per interval on average
                print(f"⚠️  LEAK DETECTED: Consistent growth of {avg_growth:.2f} MB per interval")

# Method 4: Enhanced VaultApp with memory profiling
class ProfiledVaultApp:
    """Wrapper class to add memory profiling to your existing VaultApp"""
    
    def __init__(self, vault_app_instance):
        self.app = vault_app_instance
        self.monitor = ContinuousMemoryMonitor(interval=10)
        self._patch_methods()
        
    def _patch_methods(self):
        """Add memory profiling to key methods"""
        # Profile vault operations
        original_open_vault = self.app.open_vault
        original_show_photo_gallery = getattr(self.app, 'show_photo_gallery', None)
        original_show_video_gallery = getattr(self.app, 'show_video_gallery', None)
        original_back_to_game = self.app.back_to_game
        
        @memory_profile
        def profiled_open_vault():
            with MemoryProfiler("Opening vault"):
                return original_open_vault()
                
        @memory_profile 
        def profiled_show_photo_gallery():
            if original_show_photo_gallery:
                with MemoryProfiler("Loading photo gallery"):
                    return original_show_photo_gallery()
                    
        @memory_profile
        def profiled_show_video_gallery():
            if original_show_video_gallery:
                with MemoryProfiler("Loading video gallery"):
                    return original_show_video_gallery()
                    
        @memory_profile
        def profiled_back_to_game(instance):
            with MemoryProfiler("Returning to game"):
                return original_back_to_game(instance)
        
        # Replace methods with profiled versions
        self.app.open_vault = profiled_open_vault
        if original_show_photo_gallery:
            self.app.show_photo_gallery = profiled_show_photo_gallery
        if original_show_video_gallery:
            self.app.show_video_gallery = profiled_show_video_gallery
        self.app.back_to_game = profiled_back_to_game
        
    def start_monitoring(self):
        self.monitor.start_monitoring()
        
    def stop_monitoring(self):
        self.monitor.stop_monitoring()

# Method 5: Tracemalloc integration for detailed analysis
class DetailedMemoryProfiler:
    def __init__(self):
        self.snapshots = []
        
    def start_tracing(self):
        tracemalloc.start()
        print("🔬 Started detailed memory tracing")
        
    def take_snapshot(self, label=""):
        if tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            self.snapshots.append((label, snapshot))
            print(f"📸 Snapshot taken: {label}")
            
    def analyze_snapshots(self):
        if len(self.snapshots) < 2:
            print("Need at least 2 snapshots to compare")
            return
            
        print(f"\n🔬 Detailed Memory Analysis:")
        for i in range(1, len(self.snapshots)):
            label1, snap1 = self.snapshots[i-1]
            label2, snap2 = self.snapshots[i]
            
            top_stats = snap2.compare_to(snap1, 'lineno')
            print(f"\n📊 Memory changes from '{label1}' to '{label2}':")
            print("Top 10 differences:")
            
            for index, stat in enumerate(top_stats[:10], 1):
                print(f"{index:2d}. {stat}")
                
    def stop_tracing(self):
        if tracemalloc.is_tracing():
            tracemalloc.stop()
            print("🔬 Stopped memory tracing")

# Usage example in your main.py
def setup_memory_profiling(vault_app):
    """Setup comprehensive memory profiling for your vault app"""
    
    # Method 1: Wrap your app with profiling
    profiled_app = ProfiledVaultApp(vault_app)
    
    # Method 2: Setup detailed tracing
    detailed_profiler = DetailedMemoryProfiler()
    detailed_profiler.start_tracing()
    
    # Take initial snapshot
    detailed_profiler.take_snapshot("App startup")
    
    # Start continuous monitoring
    profiled_app.start_monitoring()
    
    # Add cleanup function
    def cleanup_profiling():
        profiled_app.stop_monitoring()
        detailed_profiler.take_snapshot("App shutdown")
        detailed_profiler.analyze_snapshots()
        detailed_profiler.stop_tracing()
    
    return profiled_app, detailed_profiler, cleanup_profiling

if __name__ == "__main__":
    # Example usage - integrate this into your main.py
    print("Memory profiling utilities loaded!")
    print("To use:")
    print("1. Import this module in your main.py")
    print("2. Call setup_memory_profiling(your_vault_app)")
    print("3. Use @memory_profile decorator on suspect functions")
    print("4. Use MemoryProfiler context manager around suspect code blocks")