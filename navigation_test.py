# navigation_test.py - Test script to check vault navigation methods
"""
Run this script to test your vault navigation and find what's broken
Add this to your main.py temporarily to test navigation
"""

def test_vault_navigation(vault_app):
    """
    Test function to check all navigation methods and widget states
    Add this to your VaultApp class and call it after app initialization
    """
    print("\n🧪 === VAULT NAVIGATION TEST ===")
    
    # Test 1: Check if methods exist
    print("\n1️⃣ Testing method existence:")
    methods_to_check = [
        'open_vault',
        'show_vault_main', 
        'show_photo_gallery',
        'show_video_gallery', 
        'show_recycle_bin',
        'show_file_transfer',
        'back_to_game'
    ]
    
    for method_name in methods_to_check:
        if hasattr(vault_app, method_name):
            method = getattr(vault_app, method_name)
            print(f"   ✅ {method_name}: EXISTS - {type(method)}")
            
            # Check if it's callable
            if callable(method):
                print(f"      🔧 Callable: YES")
            else:
                print(f"      ❌ Callable: NO")
        else:
            print(f"   ❌ {method_name}: MISSING")
    
    # Test 2: Check current app state
    print(f"\n2️⃣ Current app state:")
    print(f"   📱 Current screen: {getattr(vault_app, 'current_screen', 'NOT SET')}")
    print(f"   🔒 Vault open: {getattr(vault_app, 'vault_open', 'NOT SET')}")
    print(f"   🎮 Game widget exists: {hasattr(vault_app, 'game_widget')}")
    print(f"   📦 Main layout children: {len(vault_app.main_layout.children) if hasattr(vault_app, 'main_layout') else 'NO MAIN_LAYOUT'}")
    
    # Test 3: Check vault modules
    print(f"\n3️⃣ Vault modules status:")
    modules_to_check = [
        ('photo_vault', 'Photo Vault'),
        ('recycle_bin', 'Recycle Bin'),
        ('secure_storage', 'Secure Storage')
    ]
    
    for attr_name, display_name in modules_to_check:
        if hasattr(vault_app, attr_name):
            module = getattr(vault_app, attr_name)
            print(f"   ✅ {display_name}: EXISTS - {type(module)}")
            
            # Check if module has app reference
            if hasattr(module, 'app'):
                print(f"      🔗 Has app reference: YES")
            else:
                print(f"      ❌ Has app reference: NO")
        else:
            print(f"   ❌ {display_name}: MISSING")
    
    # Test 4: Try calling show_vault_main() safely
    print(f"\n4️⃣ Testing show_vault_main() method:")
    if hasattr(vault_app, 'show_vault_main'):
        try:
            print("   🧪 Attempting to call show_vault_main()...")
            # Store current state
            current_children = len(vault_app.main_layout.children)
            current_screen = getattr(vault_app, 'current_screen', None)
            
            # Call the method
            vault_app.show_vault_main()
            
            # Check what changed
            new_children = len(vault_app.main_layout.children)
            new_screen = getattr(vault_app, 'current_screen', None)
            
            print(f"   📊 BEFORE: {current_children} widgets, screen='{current_screen}'")
            print(f"   📊 AFTER:  {new_children} widgets, screen='{new_screen}'")
            
            if current_children != new_children:
                print(f"   ✅ Widgets changed: {current_children} → {new_children}")
            else:
                print(f"   ⚠️  No widget change detected")
                
            print(f"   ✅ show_vault_main() completed successfully")
            
        except Exception as e:
            print(f"   ❌ show_vault_main() FAILED: {e}")
            import traceback
            print(f"   🔍 Error details:\n{traceback.format_exc()}")
    else:
        print("   ❌ show_vault_main() method not found")
    
    # Test 5: Check widget bindings
    print(f"\n5️⃣ Widget binding test:")
    if hasattr(vault_app, 'main_layout') and vault_app.main_layout.children:
        print(f"   📦 Main layout has {len(vault_app.main_layout.children)} widgets")
        
        # Check first widget for bindings
        first_widget = vault_app.main_layout.children[0]
        print(f"   🎯 First widget type: {type(first_widget)}")
        
        # Try to find bound events
        if hasattr(first_widget, 'get_property_observers'):
            observers = first_widget.get_property_observers('on_release')
            if observers:
                print(f"   🔗 Found {len(observers)} on_release bindings")
            else:
                print(f"   ⚠️  No on_release bindings found")
    else:
        print("   📦 No widgets to test")
    
    print(f"\n🏁 === TEST COMPLETE ===\n")
    
    return True

# Quick method check function
def quick_navigation_check(vault_app):
    """Quick check - just see what navigation methods exist"""
    print("\n🔍 QUICK NAVIGATION CHECK:")
    
    nav_methods = ['open_vault', 'show_vault_main', 'back_to_game']
    
    for method in nav_methods:
        exists = hasattr(vault_app, method)
        print(f"   {method}: {'✅ EXISTS' if exists else '❌ MISSING'}")
        
        if exists:
            try:
                # Get method and check its source
                func = getattr(vault_app, method)
                if hasattr(func, '__code__'):
                    line_no = func.__code__.co_firstlineno
                    print(f"      📍 Defined at line ~{line_no}")
            except:
                pass
    
    current_screen = getattr(vault_app, 'current_screen', 'unknown')
    vault_open = getattr(vault_app, 'vault_open', 'unknown')
    print(f"   📱 Current state: screen='{current_screen}', vault_open={vault_open}")

# Integration instructions
INTEGRATION_CODE = '''
# Add this to your VaultApp class in main.py (temporarily for testing):

def test_navigation(self):
    """Test method - add this to VaultApp class"""
    from navigation_test import test_vault_navigation, quick_navigation_check
    
    print("🧪 Starting navigation test...")
    quick_navigation_check(self)
    test_vault_navigation(self)

# Then in your main.py, after app initialization, add:
# app.test_navigation()  # Add this line to test

# Or add a test button to your game interface:
test_btn = MDRaisedButton(text='🧪 Test Navigation')
test_btn.bind(on_press=lambda x: self.test_navigation())
button_layout.add_widget(test_btn)  # Add to your button layout
'''

if __name__ == "__main__":
    print("🧪 Navigation Test Script Ready")
    print("\nTo use this:")
    print("1. Copy the test functions to your main.py")
    print("2. Add the integration code shown above")
    print("3. Run your app and click the test button")
    print("4. Check console output for test results")
    print("\nThis will tell us exactly what's broken with navigation!")
    print(INTEGRATION_CODE)