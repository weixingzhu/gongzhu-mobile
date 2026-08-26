# controller/game_controller.py
from model import Game


class GameController:
    def __init__(self):
        self.game = Game()

    def start_new_game(self):
        self.game = Game()
        self.game.deal()
        self.game.current_turn = self.game.find_club2_owner()
        self.game.show_phase = True
        return self.game

    def get_player_hand(self):
        return self.game.players[0].hand

    def get_legal_cards(self, player_idx):
        player = self.game.players[player_idx]
        return self.game.get_legal_cards(player, self.game.lead_suit)

    def play_card(self, player_idx, card):
        if card not in self.game.players[player_idx].hand:
            return False
        if self.game.lead_suit is None:
            self.game.lead_suit = card.suit
        self.game.players[player_idx].hand.remove(card)
        self.game.trick_cards.append((player_idx, card))
        return True

    def is_my_turn(self):
        return self.game.current_turn == 0

    def get_score(self, player_idx):
        player = self.game.players[player_idx]
        return self.game.calculate_score(player)