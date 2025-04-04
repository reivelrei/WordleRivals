import random
import os


class WordleGame:
    # Class-level storage for word lists (shared across all instances)
    _word_lists = {}  # Format: {word_length: [word1, word2, ...]}

    def __init__(self, word_length=5, new_game=True):
        self.word_length = word_length
        self.guesses = []
        self.max_guesses = 6
        self.target_word = ""

        self._initialize_word_list()

        # Only set new target word for brand-new games
        if new_game:
            self.target_word = random.choice(self.valid_words)
            print(f"New game! Target word: {self.target_word}")

    def _initialize_word_list(self):
        """Load word list if not already loaded for this word length"""
        if self.word_length not in self._word_lists:
            # Load from file if not already loaded
            dir_path = os.path.dirname(os.path.realpath(__file__))
            wordlist_path = os.path.join(dir_path, "..", "wordlist.txt")

            with open(wordlist_path, "r") as f:
                valid_words = [
                    word.strip().upper() for word in f.readlines()
                    if len(word.strip()) == self.word_length
                ]

            if not valid_words:
                raise ValueError(f"No valid {self.word_length}-letter words found!")

            self._word_lists[self.word_length] = valid_words

        # Reference the shared word list
        self.valid_words = self._word_lists[self.word_length]

    def is_valid_word(self, word):
        return word in self.valid_words

    def submit_guess(self, guess):
        guess = guess.upper()
        if len(guess) != self.word_length:
            return False
        if not self.is_valid_word(guess):
            return False

        self.guesses.append(guess)
        return True

    def get_feedback(self, guess):
        feedback = []
        for i, letter in enumerate(guess):
            if letter == self.target_word[i]:
                feedback.append("correct")  # Green
            elif letter in self.target_word:
                feedback.append("present")  # Yellow
            else:
                feedback.append("absent")  # Gray
        return feedback

    def to_dict(self):
        """Convert to session-storable dict (excludes large word lists)"""
        return {
            "word_length": self.word_length,
            "target_word": self.target_word,
            "guesses": self.guesses,
            "max_guesses": self.max_guesses
        }

    @classmethod
    def from_dict(cls, data):
        """Recreate game from session data"""
        game = cls(data["word_length"], new_game=False)
        game.target_word = data["target_word"]
        game.guesses = data["guesses"]
        game.max_guesses = data["max_guesses"]
        return game

    def is_game_over(self):
        return self.is_won() or len(self.guesses) >= self.max_guesses

    def is_won(self):
        return len(self.guesses) > 0 and self.guesses[-1] == self.target_word

    def remaining_guesses(self):
        return self.max_guesses - len(self.guesses)
