from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from .game_logic import WordleGame
from . import game_manager
from .sockets import socketio
import uuid

bp = Blueprint("main", __name__)


# ======================
# COMMON UTILITIES
# ======================
def get_player_id():
    if "player_id" not in session:
        session["player_id"] = str(uuid.uuid4())
    return session["player_id"]


# ======================
# SINGLE PLAYER ROUTES
# ======================
@bp.route("/")
def home():
    return redirect(url_for("main.singleplayer_home"))


@bp.route("/singleplayer")
def singleplayer_home():
    if "sp_game" not in session:
        game = WordleGame()
        session["sp_game"] = game.to_dict()
    else:
        game = WordleGame.from_dict(session["sp_game"])

    return render_template("singleplayer/game.html",
                           game=game,
                           remaining_guesses=game.remaining_guesses())


@bp.route("/singleplayer/guess", methods=["POST"])
def sp_submit_guess():
    if "sp_game" not in session:
        return redirect(url_for("main.singleplayer_home"))

    game = WordleGame.from_dict(session["sp_game"])

    if game.is_game_over():
        flash("Game already over! Start a new game.")
        return redirect(url_for("main.singleplayer_home"))

    guess = request.form.get("guess", "").strip().upper()

    if len(guess) != game.word_length:
        flash(f"Word must be exactly {game.word_length} letters!")
        return redirect(url_for("main.singleplayer_home"))

    if not game.is_valid_word(guess):
        flash("Not a valid word!")
        return redirect(url_for("main.singleplayer_home"))

    game.submit_guess(guess)
    session["sp_game"] = game.to_dict()

    if game.is_won():
        return redirect(url_for("main.sp_win"))
    elif game.is_game_over():
        return redirect(url_for("main.sp_lose"))

    return redirect(url_for("main.singleplayer_home"))


@bp.route("/singleplayer/win")
def sp_win():
    if "sp_game" not in session:
        return redirect(url_for("main.singleplayer_home"))

    game = WordleGame.from_dict(session["sp_game"])
    target_word = game.target_word
    guess_count = len(game.guesses)
    session.pop("sp_game")

    return render_template("singleplayer/win.html",
                           target_word=target_word,
                           guess_count=guess_count)


@bp.route("/singleplayer/lose")
def sp_lose():
    if "sp_game" not in session:
        return redirect(url_for("main.singleplayer_home"))

    game = WordleGame.from_dict(session["sp_game"])
    target_word = game.target_word
    session.pop("sp_game")

    return render_template("singleplayer/lose.html",
                           target_word=target_word)


# ======================
# MULTIPLAYER ROUTES
# ======================
@bp.route("/multiplayer")
def multiplayer_lobby():
    return render_template("multiplayer/lobby.html")


@bp.route("/multiplayer/create", methods=["GET", "POST"])
def mp_create_game():
    if request.method == "GET":
        return render_template("multiplayer/create.html")

    player_id = get_player_id()
    word_length = request.form.get("length", 5, type=int)

    try:
        game_id = game_manager.create_session(player_id, word_length)
        return jsonify({
            "success": True,
            "invite_link": f"/multiplayer/join/{game_id}",
            "game_id": game_id
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@bp.route("/multiplayer/join/<game_id>")
def mp_join_game(game_id):
    player_id = get_player_id()

    try:
        if game_manager.join_session(player_id, game_id):
            return redirect(url_for("main.mp_game", game_id=game_id))
        flash("Game is already full")
    except ValueError as e:
        flash(str(e))

    return redirect(url_for("main.multiplayer_lobby"))


@bp.route("/multiplayer/game/<game_id>")
def mp_game(game_id):
    player_id = get_player_id()
    game_session = game_manager.get_session(player_id)

    if not game_session or game_session.session_id != game_id:
        flash("Invalid game session")
        return redirect(url_for("main.multiplayer_lobby"))


    return render_template("multiplayer/game.html",
                         game=game_session.wordle_game,
                         session=game_session,
                         player_num=1 if player_id == game_session.player1 else 2)


@bp.route("/multiplayer/guess/<game_id>", methods=["POST"])
def mp_submit_guess(game_id):
    player_id = get_player_id()
    game_session = game_manager.get_session(player_id)

    if not game_session:
        flash("Session expired")
        return redirect(url_for("main.multiplayer_lobby"))

    guess = request.form.get("guess", "").strip().upper()
    game = game_session.wordle_game

    # Validation logic same as single-player
    if len(guess) != game.word_length:
        flash(f"Word must be exactly {game.word_length} letters!")
        return redirect(url_for("main.mp_game", game_id=game_id))

    if not game.is_valid_word(guess):
        flash("Not a valid word!")
        return redirect(url_for("main.mp_game", game_id=game_id))

    game.submit_guess(guess)

    if game.is_won():
        return redirect(url_for("main.mp_win", game_id=game_id))

    return redirect(url_for("main.mp_game", game_id=game_id))


@bp.route("/multiplayer/game/<game_id>/win")
def mp_win(game_id):
    player_id = get_player_id()
    game_session = game_manager.get_session(player_id)

    if not game_session:
        return redirect(url_for("main.multiplayer_lobby"))

    game = game_session.wordle_game
    return render_template("multiplayer/result.html",
                           won=True,
                           target_word=game.target_word,
                           guess_count=len(game.guesses))


@bp.route("/multiplayer/game/<game_id>/lose")
def mp_lose(game_id):
    player_id = get_player_id()
    game_session = game_manager.get_session(player_id)

    if not game_session:
        return redirect(url_for("main.multiplayer_lobby"))

    game = game_session.wordle_game
    return render_template("multiplayer/result.html",
                           won=False,
                           target_word=game.target_word)

@bp.route("/game-status")
def game_status():
    game_id = request.args.get("game_id")
    game = game_manager.get_session(game_id)
    return jsonify({
        "ready": bool(game and game.player2),
        "game_id": game_id
    })
