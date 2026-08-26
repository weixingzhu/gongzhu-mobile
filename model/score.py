# model/score.py
class ScoreCalculator:
    def __init__(self):
        self.heart_scores = {'A': -50, 'K': -40, 'Q': -30, 'J': -20,
                             '10': -10, '9': -10, '8': -10, '7': -10,
                             '6': -10, '5': -10, '4': 0, '3': 0, '2': 0}

    def calculate(self, cards, shown_cards, global_shown_types):
        """计算分数 - 完整版"""
        has_pig = False
        has_sheep = False
        has_transformer = False
        hearts = []

        for card in cards:
            if card.suit == '♥':
                hearts.append(card.rank)
            if card.suit == '♠' and card.rank == 'Q':
                has_pig = True
            if card.suit == '♦' and card.rank == 'J':
                has_sheep = True
            if card.suit == '♣' and card.rank == '10':
                has_transformer = True

        all_hearts = len(hearts) == 13

        pig_shown = 'pig' in global_shown_types
        sheep_shown = 'sheep' in global_shown_types
        heart_A_shown = 'heart_A' in global_shown_types
        transformer_shown = 'transformer' in global_shown_types

        # 大满贯
        if all_hearts and has_pig and has_sheep and has_transformer:
            heart_score = 400 if heart_A_shown else 200
            pig_score = 200 if pig_shown else 100
            sheep_score = 200 if sheep_shown else 100
            base_score = heart_score + pig_score + sheep_score
            return base_score * 4 if transformer_shown else base_score * 2

        result = 0

        # 红桃
        if all_hearts:
            heart_score = 400 if heart_A_shown else 200
        else:
            heart_score = 0
            for rank in hearts:
                heart_score += self.heart_scores.get(rank, 0)
            if heart_A_shown:
                heart_score *= 2
        result += heart_score

        # 猪
        if has_pig:
            result += -200 if pig_shown else -100

        # 羊
        if has_sheep:
            result += 200 if sheep_shown else 100

        # 变压器
        if has_transformer:
            is_isolated = not (hearts or has_pig or has_sheep)
            if is_isolated:
                result = 100 if transformer_shown else 50
            else:
                result *= 4 if transformer_shown else 2

        return result