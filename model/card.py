# model/card.py
from .constants import SUITS, RANKS, SUIT_MAP

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def value(self):
        return RANKS.index(self.rank)

    def key(self):
        return f"{SUIT_MAP[self.suit]}{self.rank}"

    def __str__(self):
        return f"{self.suit}{self.rank}"

    def __repr__(self):
        return self.__str__()

    def is_score_card(self):
        if self.suit == '♥':
            return True
        if self.suit == '♠' and self.rank == 'Q':
            return True
        if self.suit == '♦' and self.rank == 'J':
            return True
        if self.suit == '♣' and self.rank == '10':
            return True
        return False

    def get_card_type(self):
        if self.suit == '♥' and self.rank == 'A':
            return 'heart_A'
        if self.suit == '♠' and self.rank == 'Q':
            return 'pig'
        if self.suit == '♦' and self.rank == 'J':
            return 'sheep'
        if self.suit == '♣' and self.rank == '10':
            return 'transformer'
        return None