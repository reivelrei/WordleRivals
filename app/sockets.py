from flask import session
from flask_socketio import join_room
from . import socketio, game_manager


@socketio.on("connect")
def handle_connect():
    """Handles new socket.io connections.

    :event connect: Automatically triggered on client connection
    :action:
        - Checks for player_id in session
        - Joins game room if player is in a game
        - Emits 'game_ready' if both players are present
    """
    player_id = session.get("player_id")
    print(f"New connection from player: {player_id}")

    if player_id:
        game = game_manager.get_session(player_id)
        if game:
            print(f"Player {player_id} joining room {game.session_id}")
            join_room(game.session_id)

            # Only emit game_ready if both players are present
            if game.player1 and game.player2:
                socketio.emit("game_ready", game.session_id, room=game.session_id)

@socketio.on("game_ready")
def handle_game_ready(game_id):
    """Handles game ready event by redirecting players to game page.

    :event game_ready: Triggered when both players are connected
    :param game_id: The ID of the game session
    :type game_id: str
    :emits redirect_to_game: Sends redirect URL to game room
    """
    socketio.emit("redirect_to_game", {
        "url": f"/multiplayer/game/{game_id}"
    }, room=game_id)

@socketio.on("join_game")
def handle_join_game(data):
    """Handles player joining a game room.

    :event join_game: Triggered when player joins a game
    :param data: Event data containing game_id
    :type data: dict
    :action: Joins both game room and player's personal room
    """
    game_id = data.get("game_id")
    player_id = session.get("player_id")  # Make sure this is set

    if game_id and player_id:
        join_room(game_id)
        join_room(player_id)  # This is the missing piece!
        print(f"Player {player_id} joined game room {game_id} and their personal room")


@socketio.on("submit_guess")
def handle_guess(data):
    """Handles word guess submissions from players.

    :event submit_guess: Triggered when player submits a word guess
    :param data: Event data containing game_id and guess
    :type data: dict
    :action:
        - Validates the guess
        - Processes feedback
        - Sends updates to both players
        - Handles win/lose conditions
    :emits:
        - player_update: Sends guess feedback to respective players
        - game_won: Sent to winning player
        - game_lost: Sent to losing player
    """
    game_id = data["game_id"]
    guess = data["guess"].upper()
    player_id = session.get("player_id")

    game_session = game_manager.get_session(player_id)
    if not game_session or game_session.session_id != game_id:
        return

    # Validate guess
    if len(guess) != game_session.wordle_game.word_length:
        return
    if not game_session.wordle_game.is_valid_word(guess):
        return

    # Process guess and get feedback
    feedback = game_session.wordle_game.get_feedback(guess)
    game_session.wordle_game.submit_guess(guess)

    # Determine which player is which
    is_player1 = (player_id == game_session.player1)
    opponent_id = game_session.player2 if is_player1 else game_session.player1

    # Send different data to each player
    socketio.emit("player_update", {
        "type": "own_guess",
        "letters": guess,
        "feedback": feedback,
    }, room=player_id)  # Only to the player who guessed

    socketio.emit("player_update", {
        "type": "opponent_guess",
        "feedback": feedback,
    }, room=opponent_id)  # Only to the opponent

    if game_session.wordle_game.is_won():
        # Send different events to winner and loser
        socketio.emit("game_won", {
            "won": True,
            "word": game_session.wordle_game.target_word
        }, room=player_id)  # To the winner

        socketio.emit("game_lost", {
            "word": game_session.wordle_game.target_word
        }, room=opponent_id)  # To the loser


@socketio.on("end_game")
def handle_end_game(data):
    """Handles game termination.

    :event end_game: Triggered when game should be ended
    :param data: Event data containing game_id
    :type data: dict
    :action:
        - Emits game_ended event
        - Cleans up game session
    :emits game_ended: Notifies clients game has ended
    """
    game_id = data.get("game_id")
    player_id = session.get("player_id")

    game_session = game_manager.get_session(player_id)
    if game_session and game_session.session_id == game_id:
        # Only end if both players have left or game is over
        socketio.emit("game_ended", {}, room=game_id)
        game_manager.end_session(game_id)
