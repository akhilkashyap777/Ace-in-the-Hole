import asyncio
import websockets
import json
import time

class DiagnosticClient:
    def __init__(self, server_url="ws://69.62.78.126:8765"):
        self.server_url = server_url
        
    async def run_diagnostic_tests(self):
        """Run a series of tests to isolate the pygame issue"""
        
        print("🔍 Starting diagnostic tests...")
        print(f"🎯 Target server: {self.server_url}")
        print("=" * 60)
        
        tests = [
            ("test_basic", "Basic WebSocket communication"),
            ("test_environment", "Server environment info"),
            ("test_pygame_import", "pygame import test"),
            ("test_pygame_init", "pygame.init() test"), 
            ("test_pygame_surface", "pygame.Surface creation test"),
            ("test_monte_game_import", "MonteGame import test"),
            ("test_monte_game_create", "MonteGame instance creation test")
        ]
        
        results = {}
        
        for test_command, test_description in tests:
            print(f"\n🧪 Running: {test_description}")
            print(f"   Command: {test_command}")
            
            try:
                async with websockets.connect(self.server_url) as websocket:
                    # Wait for initial connection message
                    initial_msg = await websocket.recv()
                    initial_data = json.loads(initial_msg)
                    print(f"   📡 Server says: {initial_data.get('message', 'Connected')}")
                    
                    # Send test command
                    await websocket.send(json.dumps({"command": test_command}))
                    
                    # Get response
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    result = json.loads(response)
                    
                    results[test_command] = result
                    
                    # Display result
                    status = result.get("status", "unknown")
                    message = result.get("message", "No message")
                    
                    if status == "success":
                        print(f"   ✅ SUCCESS: {message}")
                        if "data" in result:
                            print(f"   📊 Data: {result['data']}")
                    else:
                        print(f"   ❌ FAILED: {message}")
                        
                        # If this test failed, we found our breaking point
                        if test_command in ["test_pygame_init", "test_pygame_surface", "test_monte_game_create"]:
                            print(f"\n🔥 BREAKING POINT IDENTIFIED: {test_description}")
                            print(f"   This is likely where your server crashes!")
                            break
                            
            except asyncio.TimeoutError:
                print(f"   ⏰ TIMEOUT: Server didn't respond within 10 seconds")
                results[test_command] = {"status": "timeout", "message": "Server timeout"}
                break
                
            except websockets.exceptions.ConnectionClosed as e:
                print(f"   💥 CONNECTION CLOSED: Server crashed during this test!")
                print(f"   Error: {e}")
                results[test_command] = {"status": "crash", "message": f"Server crash: {e}"}
                break
                
            except Exception as e:
                print(f"   ❌ CLIENT ERROR: {e}")
                results[test_command] = {"status": "client_error", "message": str(e)}
                break
                
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 60)
        
        for test_command, test_description in tests:
            if test_command in results:
                result = results[test_command]
                status = result.get("status", "unknown")
                
                if status == "success":
                    print(f"✅ {test_description}: PASSED")
                elif status == "crash":
                    print(f"💥 {test_description}: SERVER CRASHED HERE!")
                    print(f"   This is your problem: {result.get('message', '')}")
                    break
                elif status == "timeout":
                    print(f"⏰ {test_description}: TIMEOUT")
                    break
                else:
                    print(f"❌ {test_description}: FAILED - {result.get('message', '')}")
                    break
            else:
                print(f"⏸️ {test_description}: NOT REACHED")
        
        print("\n🎯 RECOMMENDATIONS:")
        
        # Provide specific recommendations based on results
        if "test_pygame_init" in results and results["test_pygame_init"]["status"] in ["crash", "failed"]:
            print("   1. pygame.init() is failing on your VPS")
            print("   2. Your server has no display/X11 server") 
            print("   3. Solution: Use headless pygame or remove pygame dependency")
            print("   4. Try: export SDL_VIDEODRIVER=dummy before running")
            
        elif "test_monte_game_create" in results and results["test_monte_game_create"]["status"] in ["crash", "failed"]:
            print("   1. MonteGame creation is failing")
            print("   2. Likely due to pygame.init() in the constructor")
            print("   3. Solution: Create headless version of MonteGame")
            
        elif all(test in results and results[test]["status"] == "success" for test in ["test_pygame_init", "test_pygame_surface"]):
            print("   1. pygame works fine on your server!")
            print("   2. The issue might be elsewhere")
            print("   3. Check your original websocket_game_server.py for other issues")
            
        print(f"\n📝 Save this output and fix the first failing test!")

async def main():
    client = DiagnosticClient()
    await client.run_diagnostic_tests()

if __name__ == "__main__":
    print("🚀 Pygame WebSocket Diagnostic Tool")
    print("This will help identify exactly where your server crashes")
    asyncio.run(main())

# Run the diagnostic
