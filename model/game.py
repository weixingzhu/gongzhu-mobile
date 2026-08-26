# model/game.py
import random
from .card import Card
from .player import Player
from .score import ScoreCalculator
from .constants import SUITS, RANKS   # 替换

class Game:
    def build_deck(self):
        deck = []
        for suit in SUITS:
            for rank in RANKS:
                deck.append(Card(suit, rank))
        return deck

    def __init__(self):
        self.players = [Player("你"), Player("东"), Player("北"), Player("西")]
        self.lead_suit = None
        self.trick_cards = []
        self.current_turn = 0
        self.show_phase = True
        self.suits_that_have_been_led = set()
        self.global_shown_types = set()
        self.is_game_over = False
        self._score_calculator = ScoreCalculator()

    def deal(self):
        deck = self.build_deck()
        random.shuffle(deck)
        for p in self.players:
            p.hand = []
            p.score_cards = []
            p.shown_cards = []
        for i, card in enumerate(deck):
            self.players[i % 4].hand.append(card)
        for p in self.players:
            p.sort_hand()
        self.show_phase = True
        self.suits_that_have_been_led = set()
        self.global_shown_types = set()
        self.is_game_over = False
        self.lead_suit = None
        self.trick_cards = []
        self.current_turn = self.find_club2_owner()

    def find_club2_owner(self):
        for i, player in enumerate(self.players):
            for card in player.hand:
                if card.suit == '♣' and card.rank == '2':
                    return i
        return 0

    def is_shown_card(self, player, card):
        for shown_card in player.shown_cards:
            if shown_card.suit == card.suit and shown_card.rank == card.rank:
                return True
        return False

    def update_global_shown(self, card_type):
        self.global_shown_types.add(card_type)

    def get_legal_cards(self, player, lead_suit):
        if lead_suit is None:
            legal = []
            for card in player.hand:
                if self.is_shown_card(player, card):
                    if card.suit not in self.suits_that_have_been_led:
                        has_non_shown = any(
                            c.suit == card.suit and not self.is_shown_card(player, c)
                            for c in player.hand
                        )
                        if has_non_shown:
                            continue
                legal.append(card)
            return legal if legal else player.hand[:]

        same_suit = [c for c in player.hand if c.suit == lead_suit]
        if same_suit:
            if lead_suit in self.suits_that_have_been_led:
                return same_suit
            else:
                non_shown = [c for c in same_suit if not self.is_shown_card(player, c)]
                return non_shown if non_shown else same_suit
        else:
            return player.hand[:]

    def determine_winner(self, trick_cards, lead_suit):
        valid = [(idx, card) for idx, card in trick_cards if card.suit == lead_suit]
        if not valid:
            return trick_cards[0][0]
        valid.sort(key=lambda x: x[1].value(), reverse=True)
        return valid[0][0]

    def calculate_score(self, player):
        return self._score_calculator.calculate(
            player.score_cards,
            player.shown_cards,
            self.global_shown_types
        )