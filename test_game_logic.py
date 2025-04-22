from game_logic.engine import GameEngine

# Initialize Game
game = GameEngine("Player 1", "Player 2")

# Coin flip
game.coin_flip()

# Game Loop
game_over = False
round_counter = 1

while not game_over:
    print(f"\n--- Round {round_counter} ---")
    game_over = game.play_turn()
    if not game_over:
        game.switch_turn()
        round_counter += 1
