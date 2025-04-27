import random
from .element import ELEMENTS, WILD_CARDS, ACTION_CARDS

class Card:
    def __init__(self, element, value=None, card_type='Basic', name=None):
        self.element = element
        self.value = value
        self.card_type = card_type
        self.name = name

    def __str__(self):
        if self.card_type == 'Basic':
            return f"{self.element} {self.value}"
        else:
            return  f"{self.name} ({self.element})"

class Deck:
    def __init__(self):
        self.cards = []
        self.create_deck()
        random.shuffle(self.cards)

    def create_deck(self):
        #basic cards
        for element in ELEMENTS:
            for _ in range(2): # two sets of 0-9
                for value in range(0, 10):
                    self.cards.append(Card(element, value))

        # Wild Cards (Add 4 copies of each)
        for name in WILD_CARDS.keys():
            for _ in range(4):  # Add 4 of each
                self.cards.append(Card('Wild', None, 'Wild', name))

        # Action Cards
        for name in ACTION_CARDS.keys():
            if name == 'Shield':
                for element in ELEMENTS:
                    for _ in range(2):  # 2 Shields per element
                        self.cards.append(Card(element, None, 'Action', f"{element} Shield"))
            else:
                for _ in range(4):  # 4 of each non-shield action card
                    self.cards.append(Card('Action', None, 'Action', name))

    def draw_card(self):
        return self.cards.pop() if self.cards else None

    def deal_hand(self, num_cards):
        return [self.draw_card() for _ in range (num_cards)]

class DiscardPile:
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def top_card(self):
        return self.cards[-1] if self.cards else None

    def __str__(self):
        if self.cards:
            return f"Top Card: {self.top_card()}"
        return "Discard pile is empty"

# Player Class
class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.skip_turn = False
        self.chain_lightning_count = 0

    def draw_card(self, deck):
        card = deck.draw_card()
        if card:
            self.hand.append(card)
        return card

    def play_card(self, card_index):
        if 0 <= card_index < len(self.hand):
            return self.hand.pop(card_index)
        return None

    def show_hand(self):
        return [str(card) for card in self.hand]

    def hand_size(self):
        return len(self.hand)

class GameEngine:
    def __init__(self, player1_name, player2_name):
        self.deck = Deck()
        self.discard_pile = DiscardPile()
        self.players = [Player(player1_name), Player(player2_name)]
        self.current_player_idx = None  # Will be set after coin flip
        self.game_over = False
        self.last_played_cards = {
            "You": None,
            "CPU": None
        }
        self.declared_element = None

        self.winner_name = None  # 🛠️ ADD THIS properly inside __init__

        # Deal 7 cards to each player
        for player in self.players:
            for _ in range(7):
                player.draw_card(self.deck)

        # Start discard pile
        first_card = self.deck.draw_card()
        self.discard_pile.add_card(first_card)

    def coin_flip(self):
        self.current_player_idx = random.choice([0, 1])
        print(f"\nCoin Flip Result: {self.players[self.current_player_idx].name} starts!")

    def switch_turn(self):
        self.current_player_idx = 1 - self.current_player_idx

    def current_player(self):
        return self.players[self.current_player_idx]

    def check_match(self, card, top_card):
        # 1. Declared element overrides normal rules
        if self.declared_element:
            return card.element == self.declared_element or card.card_type in ["Wild", "Action"]

        # 2. Wilds can always be played
        if card.card_type in ["Wild", "Action"]:
            return True

        # 3. Match by element or value
        if card.element == top_card.element:
            return True
        if card.card_type == 'Basic' and top_card.card_type == 'Basic' and card.value == top_card.value:
            return True

        return False

        # NEW: If there's a declared element, match only by element
        if self.declared_element:
            return card.element == self.declared_element or card.card_type == 'Wild' or card.card_type == 'Action'

        # Otherwise: Normal rules
        if card.card_type == 'Wild' or top_card.card_type == 'Wild':
            return True  # Wilds can be played anytime or stacked
        if card.card_type == 'Action' and top_card.card_type == 'Action':
            return True
        return (
                card.element == top_card.element or
                card.number == top_card.number or
                card.symbol == top_card.symbol
        )

    def play_turn(self):
        player = self.current_player()

        # Skip turn logic
        if player.skip_turn:
            print(f"{player.name} skips their turn due to Tornado!")
            player.skip_turn = False
            return False

        # Chain Lightning penalty
        if player.chain_lightning_count > 0:
            print(f"{player.name} hit by Chain Lightning! Drawing {player.chain_lightning_count} cards.")
            for _ in range(player.chain_lightning_count):
                player.draw_card(self.deck)
            player.chain_lightning_count = 0

        print(f"\n{player.name}'s turn:")
        print(f"Hand: {player.show_hand()}")
        print(f"Top card: {self.discard_pile.top_card()}")

        # Try to find playable card
        top_card = self.discard_pile.top_card()

        # Check if discard pile is empty
        if top_card is None:
            print(f"Discard pile is empty! Skipping turn.")
            return False

        played = False
        for idx, card in enumerate(player.hand):
            if self.check_match(card, top_card):
                played_card = player.play_card(idx)
                self.discard_pile.add_card(played_card)
                print(f"{player.name} played: {played_card}")
                if played_card.card_type not in ["Wild", "Action"]:
                    self.declared_element = None
                self.last_played_cards[player.name] = played_card
                # Apply special effect
                self.apply_special_effect(played_card)
                self.check_for_winner()
                played = True
                break

        # No match → draw
        if not played:
            drawn = player.draw_card(self.deck)
            print(f"{player.name} had no match. Drew card: {drawn}")
            if drawn is None:
                print(f"The deck is empty! {player.name} cannot draw.")

                # Check if player has any playable cards left
                top_card = self.discard_pile.top_card()
                can_play = False
                for card in player.hand:
                    if self.check_match(card, top_card):
                        can_play = True
                        break

                if not can_play:
                    print(f"\n🛑 No more moves for {player.name}. Game ends!")
                    print(f"{player.name} cards left: {len(player.hand)}")
                    opponent = self.players[1 - self.current_player_idx]
                    print(f"{opponent.name} cards left: {len(opponent.hand)}")

                    # Determine winner by fewest cards left
                    if len(player.hand) < len(opponent.hand):
                        print(f"\n🏆 {player.name} wins by fewest cards left!")
                    elif len(opponent.hand) < len(player.hand):
                        print(f"\n🏆 {opponent.name} wins by fewest cards left!")
                    else:
                        print("\n🤝 It's a draw!")

                    return True  # Game over

        # Check win
        if player.hand_size() == 0:
            print(f"\n🎉 {player.name} WINS! 🎉")
            self.game_over = True
            self.winner_name = player.name  # 🛠️ SET THE WINNER
            return True

        return False  # Continue game

    def apply_special_effect(self, played_card):
        current_player = self.current_player()
        opponent = self.players[1 - self.current_player_idx]

        # --- WILD CARDS ---
        if played_card.card_type == 'Wild':
            if played_card.name == 'Firestorm':
                print(f"{opponent.name} is hit by Firestorm! Discarding hand and redrawing same number of cards.")
                hand_size = opponent.hand_size()
                opponent.hand = []
                for _ in range(hand_size):
                    opponent.draw_card(self.deck)

            elif played_card.name == 'Earthquake':
                print(f"Earthquake! Players pass their hands to the left.")
                current_player.hand, opponent.hand = opponent.hand, current_player.hand

            elif played_card.name == 'Tornado':
                print(f"Tornado! {opponent.name} must skip next turn unless they play a Grounding Shield.")
                opponent.skip_turn = True

            elif played_card.name == 'Flood':
                print(f"{current_player.name} played Flood!")
                chosen_element = random.choice(['Fire', 'Water', 'Earth', 'Air'])
                print(f"Flood targets element: {chosen_element}")
                for player in self.players:
                    player.hand = [card for card in player.hand if card.element != chosen_element]

        # --- ACTION CARDS ---
        elif played_card.card_type == 'Action':
            if 'Shield' in played_card.name:
                print(f"{current_player.name} played Shield: {played_card.name}. Blocks incoming effect!")

            elif played_card.name == 'Elemental Swap':
                print(f"{current_player.name} swaps hands with {opponent.name}.")
                current_player.hand, opponent.hand = opponent.hand, current_player.hand

            elif played_card.name == 'Chaos Orb':
                print(f"{current_player.name} played Chaos Orb! Drawing 5 random cards from discard pile.")
                available_cards = self.discard_pile.cards[:-1]  # Don't include top card
                random.shuffle(available_cards)
                draw_count = min(5, len(available_cards))
                for _ in range(draw_count):
                    drawn_card = available_cards.pop()
                    current_player.hand.append(drawn_card)

            elif played_card.name == 'Chain Lightning':
                print(f"{current_player.name} used Chain Lightning!")
                opponent.chain_lightning_count = getattr(opponent, 'chain_lightning_count', 0) + 3
        # After playing any special card, declare the next element
        if played_card.card_type in ["Wild", "Action"]:
            chosen_element = random.choice(['Fire', 'Water', 'Earth', 'Air'])
            self.declared_element = chosen_element
            print(f"{self.current_player().name} declares next element to be {chosen_element}!")

    def check_for_winner(self):
        for player in self.players:
            if player.hand_size() == 0:
                print(f"🎉 {player.name} wins!")
                self.game_over = True
                self.winner_name = player.name  # 🛠️ SET THE WINNER
                return player.name
        return None


