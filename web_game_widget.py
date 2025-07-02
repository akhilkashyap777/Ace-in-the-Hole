from kivy.uix.widget import Widget
from kivy.clock import Clock

# Android-only WebView implementation
try:
    from android.webview import WebView
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False

class WebGameWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.webview = None
        self.game_started = False
        
        # Setup WebView immediately
        Clock.schedule_once(self.setup_webview, 0.1)
    
    def setup_webview(self, dt):
        if WEBVIEW_AVAILABLE:
            print("Creating Android WebView...")
            self.webview = WebView()
            
            # Configure WebView for Android
            if hasattr(self.webview, 'settings'):
                self.webview.settings.setJavaScriptEnabled(True)
                self.webview.settings.setDomStorageEnabled(True)
                self.webview.settings.setLoadWithOverviewMode(True)
                self.webview.settings.setUseWideViewPort(True)
            
            self.load_game()
            self.add_widget(self.webview)
            print("Android WebView ready!")
        else:
            print("WebView not available (development mode)")
    
    def get_html_content(self):
        """Complete 3 Card Monte game optimized for Android"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1.0">
    <title>3 Card Monte</title>
    <style>
        * { 
            box-sizing: border-box; 
            -webkit-tap-highlight-color: transparent;
        }
        
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #0f4c3a, #1a6b4f);
            color: white;
            margin: 0;
            padding: 10px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            -webkit-user-select: none;
            user-select: none;
            overflow-x: hidden;
        }

        .game-container {
            width: 100%;
            max-width: 100%;
            text-align: center;
        }

        h1 {
            font-size: 2.2em;
            margin: 10px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
        }

        .game-info {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            font-size: 1.2em;
            font-weight: bold;
        }

        .cards-container {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 30px 0;
            perspective: 1000px;
        }

        .card {
            width: 90px;
            height: 135px;
            background: #fff;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5em;
            border: 2px solid #333;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            touch-action: manipulation;
            cursor: pointer;
        }

        .card:active {
            transform: scale(0.95);
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }

        .card.shuffling {
            pointer-events: none;
            z-index: 10;
            transition: transform 0.6s ease-in-out;
        }

        .card.swapping-left {
            transform: translateX(-105px) translateY(-25px) rotate(-12deg) scale(1.05);
        }

        .card.swapping-right {
            transform: translateX(105px) translateY(-25px) rotate(12deg) scale(1.05);
        }

        .card.swapping-center-left {
            transform: translateX(-210px) translateY(-35px) rotate(-18deg) scale(1.1);
        }

        .card.swapping-center-right {
            transform: translateX(210px) translateY(-35px) rotate(18deg) scale(1.1);
        }

        .card.face-down {
            background: linear-gradient(45deg, #8B0000, #DC143C);
            color: white;
        }

        .card.ace { color: black; }
        .card.other { color: red; }

        .message {
            margin: 20px 0;
            font-size: 1.1em;
            font-weight: bold;
            min-height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 0 10px;
        }

        .win {
            color: #00ff88;
            animation: glow 1s ease-in-out infinite alternate;
        }

        .lose {
            color: #ff4444;
            animation: shake 0.5s ease-in-out;
        }

        @keyframes glow {
            from { text-shadow: 0 0 5px #00ff88; }
            to { text-shadow: 0 0 20px #00ff88; }
        }

        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-3px); }
            75% { transform: translateX(3px); }
        }

        .controls {
            margin: 20px 0;
            display: flex;
            gap: 15px;
            justify-content: center;
        }

        button {
            background: linear-gradient(45deg, #FFD700, #FFA500);
            border: none;
            padding: 12px 25px;
            font-size: 1em;
            font-weight: bold;
            color: #333;
            border-radius: 20px;
            box-shadow: 0 3px 10px rgba(255,215,0,0.3);
            touch-action: manipulation;
            cursor: pointer;
            min-width: 120px;
            min-height: 45px;
        }

        button:active {
            transform: translateY(1px);
            box-shadow: 0 2px 5px rgba(255,215,0,0.2);
        }

        button:disabled {
            background: #666;
            color: #999;
            box-shadow: none;
        }

        .instructions {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="game-container">
        <h1>🃏 3 Card Monte 🃏</h1>
        
        <div class="instructions">
            <p>Find the Ace of Spades! Each round gets faster!</p>
        </div>

        <div class="game-info">
            <div>Round: <span id="round">1</span></div>
            <div>Score: <span id="score">0</span></div>
        </div>

        <div class="cards-container">
            <div class="card face-down" data-index="0">🂠</div>
            <div class="card face-down" data-index="1">🂠</div>
            <div class="card face-down" data-index="2">🂠</div>
        </div>

        <div class="message" id="message">Ready to play!</div>

        <div class="controls">
            <button id="startBtn">Start Round</button>
            <button id="resetBtn">Reset</button>
        </div>
    </div>

    <script>
        class ThreeCardMonte {
            constructor() {
                this.round = 1;
                this.score = 0;
                this.aceCard = null;
                this.gameState = 'ready';
                this.shuffleSpeed = 800;
                this.cards = document.querySelectorAll('.card');
                this.message = document.getElementById('message');
                this.startBtn = document.getElementById('startBtn');
                this.resetBtn = document.getElementById('resetBtn');
                
                this.initializeGame();
            }

            initializeGame() {
                // Touch-optimized event listeners
                this.cards.forEach(card => {
                    card.addEventListener('touchend', (e) => {
                        e.preventDefault();
                        this.makeGuess(card);
                        this.vibrate(30);
                    });
                    card.addEventListener('click', (e) => {
                        e.preventDefault();
                        this.makeGuess(card);
                    });
                });

                this.startBtn.addEventListener('touchend', (e) => {
                    e.preventDefault();
                    this.startRound();
                    this.vibrate(20);
                });
                this.startBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.startRound();
                });

                this.resetBtn.addEventListener('touchend', (e) => {
                    e.preventDefault();
                    this.resetGame();
                    this.vibrate(20);
                });
                this.resetBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.resetGame();
                });
                
                this.updateDisplay();
                this.message.textContent = 'Tap "Start Round" to begin!';
            }

            vibrate(duration = 50) {
                if (navigator.vibrate) {
                    navigator.vibrate(duration);
                }
            }

            startRound() {
                if (this.gameState !== 'ready') return;
                
                this.gameState = 'shuffling';
                this.startBtn.disabled = true;
                this.message.textContent = 'Watch the Ace of Spades!';
                
                this.revealCards(true);
                
                setTimeout(() => {
                    this.hideCards();
                    setTimeout(() => {
                        this.shuffleCards();
                    }, 1000);
                }, 2000);
            }

            revealCards(isInitialReveal = false) {
                if (isInitialReveal) {
                    const acePosition = Math.floor(Math.random() * 3);
                    this.aceCard = this.cards[acePosition];
                }
                
                this.cards.forEach(card => {
                    card.classList.remove('face-down');
                    if (card === this.aceCard) {
                        card.textContent = '🂡';
                        card.classList.add('ace');
                        card.classList.remove('other');
                    } else {
                        card.textContent = Math.random() < 0.5 ? '🂢' : '🂣';
                        card.classList.add('other');
                        card.classList.remove('ace');
                    }
                });
            }

            hideCards() {
                this.cards.forEach(card => {
                    card.classList.add('face-down');
                    card.textContent = '🂠';
                    card.classList.remove('ace', 'other');
                });
            }

            shuffleCards() {
                const shuffleCount = 3 + this.round;
                let shufflesDone = 0;
                
                const performShuffle = () => {
                    if (shufflesDone >= shuffleCount) {
                        this.gameState = 'guessing';
                        this.message.textContent = 'Where is the Ace of Spades?';
                        this.cards.forEach(card => {
                            card.classList.remove('shuffling', 'swapping-left', 'swapping-right', 'swapping-center-left', 'swapping-center-right');
                        });
                        return;
                    }
                    
                    const swapPairs = [[0, 1], [1, 2], [0, 2]];
                    const [pos1, pos2] = swapPairs[shufflesDone % 3];
                    
                    this.cards[pos1].classList.add('shuffling');
                    this.cards[pos2].classList.add('shuffling');
                    
                    if (pos1 === 0 && pos2 === 1) {
                        this.cards[0].classList.add('swapping-right');
                        this.cards[1].classList.add('swapping-left');
                    } else if (pos1 === 1 && pos2 === 2) {
                        this.cards[1].classList.add('swapping-right');
                        this.cards[2].classList.add('swapping-left');
                    } else if (pos1 === 0 && pos2 === 2) {
                        this.cards[0].classList.add('swapping-center-right');
                        this.cards[2].classList.add('swapping-center-left');
                    }
                    
                    setTimeout(() => {
                        const container = this.cards[0].parentNode;
                        const card1 = this.cards[pos1];
                        const card2 = this.cards[pos2];
                        
                        const temp = document.createElement('div');
                        container.insertBefore(temp, card1);
                        container.insertBefore(card1, card2);
                        container.insertBefore(card2, temp);
                        container.removeChild(temp);
                        
                        this.cards = document.querySelectorAll('.card');
                        
                        this.cards.forEach(card => {
                            card.classList.remove('shuffling', 'swapping-left', 'swapping-right', 'swapping-center-left', 'swapping-center-right');
                        });
                        
                        shufflesDone++;
                        setTimeout(performShuffle, 200);
                    }, Math.max(600, this.shuffleSpeed * 0.8));
                };
                
                performShuffle();
            }

            makeGuess(clickedCard) {
                if (this.gameState !== 'guessing') return;
                
                this.gameState = 'ready';
                this.revealCards(false);
                
                if (clickedCard === this.aceCard) {
                    this.score++;
                    this.message.textContent = '🎉 Correct! Well done!';
                    this.message.className = 'message win';
                    this.vibrate(100);
                    this.nextRound();
                } else {
                    let aceVisualPosition = -1;
                    this.cards.forEach((card, index) => {
                        if (card === this.aceCard) {
                            aceVisualPosition = index + 1;
                        }
                    });
                    
                    this.message.textContent = '❌ Wrong! Ace was in position ' + aceVisualPosition;
                    this.message.className = 'message lose';
                    this.vibrate([50, 50, 50]);
                    setTimeout(() => this.resetGame(), 2000);
                }
            }

            nextRound() {
                this.round++;
                this.shuffleSpeed = Math.max(200, this.shuffleSpeed - 100);
                
                setTimeout(() => {
                    this.message.textContent = 'Get ready for round ' + this.round + '!';
                    this.message.className = 'message';
                    this.startBtn.disabled = false;
                    this.updateDisplay();
                }, 2000);
            }

            resetGame() {
                this.round = 1;
                this.score = 0;
                this.shuffleSpeed = 800;
                this.gameState = 'ready';
                this.message.textContent = 'Tap "Start Round" to begin!';
                this.message.className = 'message';
                this.startBtn.disabled = false;
                this.hideCards();
                this.updateDisplay();
            }

            updateDisplay() {
                document.getElementById('round').textContent = this.round;
                document.getElementById('score').textContent = this.score;
            }
        }

        // Initialize game
        window.addEventListener('load', () => {
            window.game = new ThreeCardMonte();
        });

        // Auto-start function for Kivy
        function startNewGame() {
            if (window.game) {
                window.game.resetGame();
            }
        }
    </script>
</body>
</html>'''
    
    def load_game(self):
        """Load game into Android WebView"""
        if self.webview:
            html_content = self.get_html_content()
            
            # Use Android WebView methods
            if hasattr(self.webview, 'loadData'):
                self.webview.loadData(html_content, "text/html", "UTF-8")
            elif hasattr(self.webview, 'load_string'):
                self.webview.load_string(html_content)
    
    def start_game(self):
        """Start new game - called by Kivy buttons"""
        if self.webview and WEBVIEW_AVAILABLE:
            try:
                if hasattr(self.webview, 'evaluateJavascript'):
                    self.webview.evaluateJavascript("startNewGame();", None)
                elif hasattr(self.webview, 'execute_js'):
                    self.webview.execute_js("startNewGame();")
            except Exception as e:
                print(f"JS call error: {e}")
        
        self.game_started = True

    def on_size(self, *args):
        """Handle resizing"""
        if self.webview and WEBVIEW_AVAILABLE:
            self.webview.size = self.size
            self.webview.pos = self.pos