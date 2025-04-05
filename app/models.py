import uuid
from datetime import datetime

class GameSession:
    def __init__(self, word_length=5):
        self.session_id = str(uuid.uuid4())
        self.player1 = None  # Player ID
        self.player2 = None  # Player ID
        self.word_length = word_length
        self.wordle_game = None  # Will hold WordleGame instance
        self.game_state = "waiting"  # waiting/playing
        self.created_at = datetime.now()
        self.rematch_requests = set()  # Track who requested rematch
        self.rematch_game_id = None  # Track new game ID if rematch happens
