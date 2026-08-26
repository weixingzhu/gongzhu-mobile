# ai.py - 专家级拱猪AI（蒙特卡洛模拟 + 策略决策）
import random
import copy
#from model.card import Card
from model.constants import SUITS, RANKS

class ExpertAI:
    def __init__(self, simulation_count=50):
        """
        初始化AI
        simulation_count: 每步模拟对局次数（越大越强，但越慢）
        """
        self.simulation_count = simulation_count
        self.pig_card = None  # 猪（♠Q）
        self.sheep_card = None  # 羊（♦J）
        self.transformer_card = None  # 变压器（♣10）
        self.heart_cards = []  # 所有红桃

    def choose_card(self, player, legal_cards, game):
        """
        选择最优出牌
        player: 当前AI玩家对象
        legal_cards: 合法出牌列表
        game: 游戏状态对象
        """
        if not legal_cards:
            return None

        # 如果只有一张合法牌，直接出
        if len(legal_cards) == 1:
            return legal_cards[0]

        # 保存关键牌引用
        self._init_key_cards(game)

        # 第一步：评估是否有危险牌需要优先处理
        safe_cards = self._get_safe_cards(legal_cards, player, game)
        if safe_cards:
            # 从安全牌中选最优
            return self._choose_best_from_safe(safe_cards, player, game)

        # 第二步：如果必须出危险牌，选择风险最小的
        return self._choose_least_risky(legal_cards, player, game)

    def _init_key_cards(self, game):
        """初始化关键牌引用"""
        deck = game.build_deck() if hasattr(game, 'build_deck') else []
        for card in deck:
            if card.suit == '♠' and card.rank == 'Q':
                self.pig_card = card
            elif card.suit == '♦' and card.rank == 'J':
                self.sheep_card = card
            elif card.suit == '♣' and card.rank == '10':
                self.transformer_card = card
            elif card.suit == '♥':
                self.heart_cards.append(card)

    def _get_safe_cards(self, legal_cards, player, game):
        """
        获取安全牌（不会导致负分的牌）
        """
        safe = []
        for card in legal_cards:
            if self._is_safe_card(card, player, game):
                safe.append(card)
        return safe

    def _is_safe_card(self, card, player, game):
        """
        判断一张牌是否安全
        """
        # 猪（♠Q）- 危险
        if card.suit == '♠' and card.rank == 'Q':
            return False

        # 红桃 - 如果红桃还没人出过，且自己红桃多，危险
        if card.suit == '♥':
            # 检查是否已经有红桃被出过（从trick_cards中取卡）
            hearts_played = any(c[1].suit == '♥' for c in game.trick_cards)  # 修复：c[1]是Card对象
            if not hearts_played:
                # 计算手中有多少红桃
                heart_count = sum(1 for c in player.hand if c.suit == '♥')
                if heart_count > 3:
                    return False

        # 变压器 - 如果手中有猪或羊，危险
        if card.suit == '♣' and card.rank == '10':
            has_pig = any(c.suit == '♠' and c.rank == 'Q' for c in player.hand)
            has_sheep = any(c.suit == '♦' and c.rank == 'J' for c in player.hand)
            if has_pig or has_sheep:
                return False

        return True

    def _choose_best_from_safe(self, safe_cards, player, game):
        """
        从安全牌中选择最优
        """
        # 优先出最小牌（保留大牌）
        return min(safe_cards, key=lambda c: c.value())

    def _choose_least_risky(self, legal_cards, player, game):
        """
        选择风险最小的牌（蒙特卡洛模拟）
        """
        best_card = None
        best_score = -float('inf')

        # 对每张候选牌进行模拟
        for card in legal_cards:
            total_score = 0
            for _ in range(min(self.simulation_count, 30)):
                score = self._simulate_one_round(card, player, game)
                total_score += score

            avg_score = total_score / min(self.simulation_count, 30)
            if avg_score > best_score:
                best_score = avg_score
                best_card = card

        return best_card if best_card else legal_cards[0]

    def _simulate_one_round(self, card, player, game):
        """
        模拟一轮出牌后的得分
        """
        # 复制当前游戏状态（简化版）
        score = 0

        # 出猪 → 负分
        if card.suit == '♠' and card.rank == 'Q':
            pig_shown = 'pig' in game.global_shown_types
            score += -200 if pig_shown else -100

        # 出红桃 → 负分
        if card.suit == '♥':
            heart_shown = 'heart_A' in game.global_shown_types
            heart_scores = {'A': 50, 'K': 40, 'Q': 30, 'J': 20,
                            '10': 10, '9': 10, '8': 10, '7': 10,
                            '6': 10, '5': 10, '4': 0, '3': 0, '2': 0}
            score += -heart_scores.get(card.rank, 0) * (2 if heart_shown else 1)

        # 出变压器 → 翻倍
        if card.suit == '♣' and card.rank == '10':
            transformer_shown = 'transformer' in game.global_shown_types
            score *= 4 if transformer_shown else 2

        return score

    def should_show_card(self, player, card, game):
        """亮牌决策（专家级）"""
        card_type = card.get_card_type()
        if card_type is None:
            return False

        # 红桃A亮牌决策
        if card_type == 'heart_A':
            heart_count = sum(1 for c in player.hand if c.suit == '♥')
            if heart_count >= 3:
                print(f"🤖 AI决定亮红桃A: {card}")
                return True
            return False

        # 猪亮牌决策
        if card_type == 'pig':
            has_sheep = any(c.suit == '♦' and c.rank == 'J' for c in player.hand)
            if has_sheep:
                print(f"🤖 AI决定亮猪: {card}")
                return True
            heart_count = sum(1 for c in player.hand if c.suit == '♥')
            if heart_count <= 2:
                print(f"🤖 AI决定亮猪: {card}")
                return True
            return False

        # 羊亮牌决策
        if card_type == 'sheep':
            has_pig = any(c.suit == '♠' and c.rank == 'Q' for c in player.hand)
            if has_pig:
                return False
            has_transformer = any(c.suit == '♣' and c.rank == '10' for c in player.hand)
            if has_transformer:
                print(f"🤖 AI决定亮羊: {card}")
                return True
            return False

        # 变压器亮牌决策
        if card_type == 'transformer':
            has_pig = any(c.suit == '♠' and c.rank == 'Q' for c in player.hand)
            has_sheep = any(c.suit == '♦' and c.rank == 'J' for c in player.hand)
            if has_pig and has_sheep:
                print(f"🤖 AI决定亮变压器: {card}")
                return True
            heart_count = sum(1 for c in player.hand if c.suit == '♥')
            if heart_count <= 1:
                print(f"🤖 AI决定亮变压器: {card}")
                return True
            return False

        return False