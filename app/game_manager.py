from collections import defaultdict
from typing import Optional
from .models import GameSession

class GameManager:
    """Manages game sessions, including creation, joining, and cleanup.

    :ivar sessions: Active game sessions keyed by session ID
    :ivar waiting_sessions: Game IDs waiting for players, grouped by word length
    :ivar player_to_game: Mapping of player IDs to their current game ID
    """

    def __init__(self) -> None:
        """Initializes a new GameManager with empty session containers."""
        self.sessions = {}
        self.waiting_sessions = defaultdict(list)
        self.player_to_game = {}

    def create_session(self, player_id: str, word_length: int=5) -> str:
        """Creates a new game session with the given player as the first participant.

        :param player_id: The ID of the player creating the session
        :param word_length: The length of the word for the game (default: 5)
        :return: The ID of the newly created game session
        """
        session = GameSession(word_length)
        session.player1 = player_id
        self.sessions[session.session_id] = session
        self.waiting_sessions[word_length].append(session.session_id)
        self.player_to_game[player_id] = session.session_id
        return session.session_id

    def join_session(self, player_id: str, game_id: str) -> bool:
        """Joins a player to an existing game session.

        :param player_id: The ID of the player joining the session
        :param game_id: The ID of the game session to join
        :return: True if the player successfully joined, False if the session is full
        :raises ValueError: If the specified game session does not exist
        """
        if game_id not in self.sessions:
            raise ValueError("Game not found")

        session = self.sessions[game_id]

        if session.player2 is not None:
            return False  # Already full

        session.player2 = player_id
        session.game_state = "playing"
        self.player_to_game[player_id] = game_id

        # Initialize the game if not already done
        if session.wordle_game is None:
            from .game_logic import WordleGame
            session.wordle_game = WordleGame(session.word_length)

        return True

    def get_session(self, player_id: str) -> Optional[GameSession]:
        """Retrieves the game session associated with a player.

        :param player_id: The ID of the player
        :return: The game session if found, otherwise None
        """
        game_id = self.player_to_game.get(player_id)
        return self.sessions.get(game_id) if game_id else None


    def end_session(self, game_id: str) -> None:
        """Ends and cleans up a game session.

        :param game_id: The ID of the game session to end
        """
        if game_id in self.sessions:
            session = self.sessions[game_id]
            # Remove player references
            if session.player1 in self.player_to_game:
                del self.player_to_game[session.player1]
            if session.player2 in self.player_to_game:
                del self.player_to_game[session.player2]
            # Remove from waiting sessions if present
            for length, sessions in self.waiting_sessions.items():
                if game_id in sessions:
                    sessions.remove(game_id)
            # Remove the session itself
            del self.sessions[game_id]
