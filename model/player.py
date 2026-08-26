# model/player.py
from .constants import SUITS
from .card import Card

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.score_cards = []
        self.shown_cards = []

    def sort_hand(self):
        self.hand.sort(key=lambda c: (SUITS.index(c.suit), c.value()))