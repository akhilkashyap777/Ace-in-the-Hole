import asyncio
import websockets
import json
import logging
import time
from monte_game import MonteGame

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameServer:
    def __init__(self):
        self.active_games = {}
        self.running = True
    
    async def handle_client(self, websocket):  # FIXED: Removed 'path' parameter
        user_id = id(websocket)
        logger.info(f"New client connected: {user_id}")
        
        try:
            # Create a new game for this client
            self.active_games[user_id] = MonteGame()
            
            # Send initial game state
            game_state = self.get_game_state(user_id)
            await websocket.send(json.dumps(game_state))
            
            # Start the game loop for this client
            game_task = asyncio.create_task(self.game_loop(websocket, user_id))
            message_task = asyncio.create_task(self.handle_messages(websocket, user_id))
            
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [game_task, message_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {user_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {user_id}: {e}")
        finally:
            # Clean up
            if user_id in self.active_games:
                del self.active_games[user_id]
            logger.info(f"Cleaned up game for client {user_id}")

    async def handle_messages(self, websocket, user_id):
        async for message in websocket:
            try:
                data = json.loads(message)
                await self.process_message(websocket, user_id, data)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {user_id}: {message}")
            except Exception as e:
                logger.error(f"Error processing message from {user_id}: {e}")

    async def process_message(self, websocket, user_id, data):
        if user_id not in self.active_games:
            return
            
        game = self.active_games[user_id]
        message_type = data.get('type')
        
        if message_type == 'start_game':
            game.show_cards()
            logger.info(f"Game started for user {user_id}")
            
        elif message_type == 'click':
            x, y = data.get('x', 0), data.get('y', 0)
            game.handle_click((x, y))
            logger.info(f"Click processed for user {user_id}: ({x}, {y})")
            
        elif message_type == 'reset_game':
            self.active_games[user_id] = MonteGame()
            logger.info(f"Game reset for user {user_id}")
        
        # Send immediate response
        try:
            game_state = self.get_game_state(user_id)
            await websocket.send(json.dumps(game_state))
        except Exception as e:
            logger.error(f"Error sending immediate response to {user_id}: {e}")

    async def game_loop(self, websocket, user_id: str):
        """Main game loop that sends periodic updates"""
        last_update = time.time()
        
        while self.running and user_id in self.active_games:
            try:
                current_time = time.time()
                
                # Update game state (60 FPS)
                if current_time - last_update >= 1/60:
                    game = self.active_games[user_id]
                    
                    game.update()
                    
                    # Send updated game state
                    game_state = self.get_game_state(user_id)
                    await websocket.send(json.dumps(game_state))
                    
                    last_update = current_time
                
                # Small sleep to prevent excessive CPU usage
                await asyncio.sleep(0.016)  # ~60 FPS
                
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"Client {user_id} disconnected during game loop")
                break
            except Exception as e:
                logger.error(f"Error in game loop for user {user_id}: {e}")
                break

    def get_game_state(self, user_id: str):
        """Get current game state for a user"""
        try:
            if user_id not in self.active_games:
                return {"error": "Game not found"}
            
            game = self.active_games[user_id]
            
            # Prepare cards data
            cards_data = []
            for card in game.cards:
                cards_data.append({
                    'x': float(card.x),
                    'y': float(card.y),
                    'target_x': float(card.target_x),
                    'target_y': float(card.target_y),
                    'is_winner': card.is_winner,
                    'is_face_up': card.is_face_up,
                    'moving': card.moving
                })
            
            # Determine instruction text
            if game.game_state == "showing":
                instruction = "Remember the RED ACE!"
            elif game.game_state == "shuffling":
                instruction = "Follow the cards..."
            elif game.game_state == "guessing":
                instruction = "Click the card with the RED ACE!"
            elif game.game_state == "result":
                if game.last_guess_correct:
                    instruction = f"CORRECT! +10 points | Streak: {game.streak} (Click to continue)"
                else:
                    instruction = f"WRONG! Streak broken! Speed reset (Click to continue)"
            else:
                instruction = ""
            
            state_data = {
                'type': 'game_state',
                'cards': cards_data,
                'game_state': game.game_state,
                'score': game.score,
                'streak': game.streak,
                'best_streak': game.best_streak,
                'round_num': game.round_num,
                'shuffle_speed': game.shuffle_speed,
                'shuffle_count': game.shuffle_count,
                'max_shuffles': game.max_shuffles,
                'last_guess_correct': game.last_guess_correct,
                'screen_size': [game.SCREEN_WIDTH, game.SCREEN_HEIGHT],
                'card_size': [game.CARD_WIDTH, game.CARD_HEIGHT],
                'colors': {
                    'FELT_GREEN': game.FELT_GREEN,
                    'WOOD_BROWN': game.WOOD_BROWN,
                    'LIGHT_BROWN': game.LIGHT_BROWN,
                    'DARK_GREEN': game.DARK_GREEN,
                    'WHITE': game.WHITE,
                    'BLACK': game.BLACK,
                    'RED': game.RED,
                    'BLUE': game.BLUE,
                    'GOLD': game.GOLD
                },
                'instruction': instruction,
                'timestamp': time.time()
            }
            
            return state_data
            
        except Exception as e:
            logger.error(f"Error getting game state for user {user_id}: {e}")
            return {"error": f"Game state error: {str(e)}"}

async def main():
    server = GameServer()
    
    # Start the WebSocket server
    start_server = websockets.serve(
        server.handle_client, 
        "0.0.0.0", 
        8765,
        ping_interval=20,
        ping_timeout=10
    )
    
    logger.info("🎮 Monte Carlo Game Server starting on ws://0.0.0.0:8765")
    
    await start_server
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")