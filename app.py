from flask import Flask, render_template, redirect, url_for
from game_logic.engine import GameEngine

app = Flask(__name__)

# GLOBAL GAME INSTANCE
game = None

@app.route('/new_game')
def new_game():
    global game
    game = GameEngine("You", "CPU")  # Create a new game instance
    game.coin_flip()  # Decide who starts
    return redirect(url_for('game_page'))

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/game')
def game_page():
    global game
    if game is None:
        return redirect(url_for('new_game'))

    player = game.current_player()
    discard = game.discard_pile.top_card()

    # If the game is over, show winner immediately
    if game.game_over:
        winner = game.winner_name if game.winner_name else "Unknown"
        return render_template("game.html", player=player, discard=discard,
                               message=f"🎉 {winner} WINS!", last_played=game.last_played_cards)

    # CPU Turn
    if player.name != "You":
        game_over = game.play_turn()
        if game_over:
            game.game_over = True
            winner = game.winner_name if game.winner_name else player.name
            return render_template("game.html", player=player, discard=game.discard_pile.top_card(),
                                   message=f"🎉 {winner} WINS!", last_played=game.last_played_cards)
        else:
            game.switch_turn()
            return redirect(url_for('game_page'))

    # Player Turn
    return render_template("game.html", player=player, discard=discard,
                           message=None, last_played=game.last_played_cards)

@app.route('/play_card/<int:card_index>')
def play_card(card_index):
    global game
    if game is None:
        return redirect(url_for('new_game'))

    player = game.current_player()
    if player.name == "You":
        top_card = game.discard_pile.top_card()
        selected_card = player.hand[card_index]

        if game.check_match(selected_card, top_card):
            played_card = player.play_card(card_index)
            game.discard_pile.add_card(played_card)
            game.apply_special_effect(played_card)

            if player.hand_size() == 0:
                game.game_over = True
                game.winner_name = player.name
                return render_template("game.html", player=player, discard=game.discard_pile.top_card(),
                                       message=f"🎉 {game.winner_name} WINS!", last_played=game.last_played_cards)

            if played_card.card_type in ["Wild", "Action"]:
                return render_template("choose_element.html", card=played_card)

            game.switch_turn()

    return redirect(url_for('game_page'))

@app.route('/draw_card')
def draw_card():
    global game
    if game is None:
        return redirect(url_for('new_game'))

    player = game.current_player()
    if player.name == "You":
        drawn = player.draw_card(game.deck)
        if drawn is not None:
            top_card = game.discard_pile.top_card()
            if game.check_match(drawn, top_card):
                player.hand.remove(drawn)
                game.discard_pile.add_card(drawn)
                game.apply_special_effect(drawn)
                if player.hand_size() == 0:
                    game.game_over = True
                    game.winner_name = player.name
                    return render_template("game.html", player=player, discard=game.discard_pile.top_card(),
                                           message=f"🎉 {game.winner_name} WINS!", last_played=game.last_played_cards)
                game.switch_turn()
        else:
            message = "The deck is empty! Can't draw."
            return render_template("game.html", player=player, discard=game.discard_pile.top_card(),
                                   message=message, last_played=game.last_played_cards)

    return redirect(url_for('game_page'))

@app.route('/choose_element/<element>')
def choose_element(element):
    global game
    if game is None:
        return redirect(url_for('new_game'))

    game.declared_element = element.capitalize()
    print(f"You declared the next element to be: {game.declared_element}")

    player = game.current_player()
    if player.name == "You" and player.hand_size() == 0:
        game.game_over = True
        game.winner_name = player.name
        return render_template("game.html", player=player, discard=game.discard_pile.top_card(),
                               message=f"🎉 {game.winner_name} WINS!", last_played=game.last_played_cards)

    game.switch_turn()
    return redirect(url_for('game_page'))

if __name__ == '__main__':
    app.run(debug=True)

