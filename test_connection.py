import asyncio
import websockets
import json
import time

async def test_connection():
    try:
        print("🔌 Connecting to server...")
        async with websockets.connect("ws://69.62.78.126:8765") as websocket:
            print("✅ Connected successfully!")
            
            # Test 1: Initial connection - check if we get game state
            print("\n📊 Test 1: Initial game state")
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Initial state: {data.get('game_state')}, score={data.get('score')}")
            print(f"Cards count: {len(data.get('cards', []))}")
            print(f"Instruction: {data.get('instruction', 'None')}")
            
            # Test 2: Start game and monitor state changes
            print("\n🎮 Test 2: Starting game...")
            await websocket.send(json.dumps({"type": "start_game"}))
            print("📤 Sent start_game command")
            
            # Monitor for 10 seconds to see state transitions
            start_time = time.time()
            last_state = None
            state_changes = []
            
            print("📈 Monitoring state changes for 10 seconds...")
            while time.time() - start_time < 10:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    current_state = data.get('game_state')
                    
                    if current_state != last_state:
                        state_changes.append({
                            'time': time.time() - start_time,
                            'state': current_state,
                            'instruction': data.get('instruction', ''),
                            'shuffle_count': data.get('shuffle_count', 0),
                            'max_shuffles': data.get('max_shuffles', 0)
                        })
                        last_state = current_state
                        print(f"⚡ State change: {current_state} - {data.get('instruction', '')}")
                        
                        # If cards are face up, check their positions
                        if any(card.get('is_face_up') for card in data.get('cards', [])):
                            print("👁️  Cards are face up!")
                            for i, card in enumerate(data.get('cards', [])):
                                if card.get('is_winner'):
                                    print(f"   🏆 Winner card {i} at ({card.get('x')}, {card.get('y')})")
                        
                        # If in guessing state, try clicking
                        if current_state == "guessing":
                            print("🎯 Game is ready for guessing! Sending click...")
                            # Click on middle card
                            await websocket.send(json.dumps({"type": "click", "x": 400, "y": 300}))
                            print("📤 Sent click command")
                            
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break
            
            print(f"\n📋 State Changes Summary ({len(state_changes)} changes):")
            for change in state_changes:
                print(f"  {change['time']:.1f}s: {change['state']} - {change['instruction']}")
                if change['state'] == 'shuffling':
                    print(f"    Shuffle: {change['shuffle_count']}/{change['max_shuffles']}")
            
            # Test 3: Check if game is stuck
            print("\n🔍 Test 3: Checking if game is stuck...")
            final_response = await websocket.recv()
            final_data = json.loads(final_response)
            final_state = final_data.get('game_state')
            
            if final_state == "shuffling" and len(state_changes) <= 2:
                print("❌ ISSUE DETECTED: Game appears stuck in shuffling state!")
                print(f"   Shuffle count: {final_data.get('shuffle_count', 0)}")
                print(f"   Max shuffles: {final_data.get('max_shuffles', 0)}")
                print("   Cards movement status:")
                for i, card in enumerate(final_data.get('cards', [])):
                    print(f"     Card {i}: moving={card.get('moving', False)}, pos=({card.get('x')}, {card.get('y')})")
            elif len(state_changes) > 2:
                print("✅ Game state transitions working correctly!")
            else:
                print(f"🤔 Inconclusive: Final state is {final_state}")
            
            # Test 4: Manual click test
            print("\n🖱️ Test 4: Manual click test...")
            await websocket.send(json.dumps({"type": "click", "x": 300, "y": 300}))
            await asyncio.sleep(0.5)
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Click response: {data.get('game_state')} - {data.get('instruction', '')}")
            
            print("\n🎮 Test completed!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_message_sending():
    """Test the specific message sending issue"""
    print("\n🧪 Testing message sending mechanism...")
    
    try:
        async with websockets.connect("ws://69.62.78.126:8765") as websocket:
            print("✅ Connected for message test")
            
            # Test rapid message sending (like in your client)
            messages = [
                {"type": "start_game"},
                {"type": "click", "x": 100, "y": 100},
                {"type": "click", "x": 200, "y": 200},
                {"type": "reset_game"}
            ]
            
            for i, msg in enumerate(messages):
                print(f"📤 Sending message {i+1}: {msg}")
                await websocket.send(json.dumps(msg))
                await asyncio.sleep(0.1)  # Small delay
                
                # Check immediate response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(response)
                    print(f"📥 Response: {data.get('game_state')} - {data.get('instruction', '')}")
                except asyncio.TimeoutError:
                    print("⏰ No immediate response")
            
    except Exception as e:
        print(f"❌ Message test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting comprehensive WebSocket game tests...\n")
    asyncio.run(test_connection())
    asyncio.run(test_message_sending())