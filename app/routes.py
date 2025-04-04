from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from .game_logic import WordleGame

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    if "game" not in session:
        game = WordleGame()
        session["game"] = game.to_dict()  # Store as dict
    else:
        game = WordleGame.from_dict(session["game"])  # Recreate from dict

    return render_template("game.html", game=game)


@bp.route("/guess", methods=["POST"])
def submit_guess():
    if 'game' not in session:
        return redirect(url_for("main.home"))

    game = WordleGame.from_dict(session["game"])

    if game.is_game_over():
        flash("Game already over! Start a new game.")
        return redirect(url_for("main.home"))

    guess = request.form.get("guess", "").strip().upper()

    if len(guess) != game.word_length:
        flash(f"Word must be exactly {game.word_length} letters!")
        return redirect(url_for("main.home"))

    if not game.is_valid_word(guess):
        flash("Not a valid word!")
        return redirect(url_for("main.home"))

    game.submit_guess(guess)
    session["game"] = game.to_dict()

    if game.is_won():
        return redirect(url_for("main.win"))
    elif game.is_game_over():
        return redirect(url_for("main.lose"))

    return redirect(url_for("main.home"))


@bp.route("/lose")
def lose():
    if "game" not in session:
        return redirect(url_for("main.home"))
    game = WordleGame.from_dict(session["game"])
    target = game.target_word
    session.pop("game")
    return render_template("lose.html", target_word=target)


@bp.route("/win")
def win():
    if "game" not in session:
        return redirect(url_for("main.home"))

    # Get game data BEFORE removing from session
    game = WordleGame.from_dict(session["game"])
    target_word = game.target_word
    guess_count = len(game.guesses)

    session.pop("game")  # Clear the game after getting data

    return render_template("win.html",
                           target_word=target_word,
                           guess_count=guess_count)