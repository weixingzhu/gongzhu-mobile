# view/screens/game.py
import os
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window

from ..widgets import GlowingButton, AvatarWidget, CardWidget, SmallCardWidget, FlyingCardWidget
from model import Game

# 尺寸常量已被删除，全部改为动态计算

AVATAR_COLORS = [
    (1, 0.42, 0.42, 1),
    (0.31, 0.80, 0.77, 1),
    (0.27, 0.72, 0.82, 1),
    (1, 0.66, 0.30, 1)
]
AVATAR_EMOJIS = ['😊', '🤖', '🧙', '👾']


class GameScreen(FloatLayout):

    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.game = controller.game
        from ai import ExpertAI
        self.ai = ExpertAI()
        self.game_active = True
        self.game_round = 1
        self.game_over = False

        # ==================== 动态尺寸计算 ====================
        # 所有尺寸均基于 1920x1080 固定画布计算，游戏整体通过 Scatter 缩放
        self.scale = 1.0
        self.AVATAR_SIZE = int(75 * self.scale)  # 头像改大一点

        self.SMALL_CARD_WIDTH = int(35 * self.scale)
        self.SMALL_CARD_HEIGHT = int(self.SMALL_CARD_WIDTH * (44 / 30))

        self.CARD_WIDTH_BASE = int(108 * self.scale)
        self.CARD_HEIGHT_BASE = int(self.CARD_WIDTH_BASE * (155 / 108))
        # ==========================================================

        # 亮牌阶段数据
        self.show_pending = {}
        self.operated_count = 0
        self.total_showable = 0
        self._operated_keys = set()
        self.show_phase_time_left = 15
        self.show_timer_id = None

        # 出牌计时器
        self.timer_id = None
        self.time_left = 15

        self.anim_cards = []
        self.anim_id = None
        self.card_widgets = []
        self.show_btns = []
        self.timer_label = None
        self.msg_label = None
        self.game_over_widgets = []
        self.play_timer_label = None

        self._shown_cards_created = False
        self.shown_card_positions = [
            {'x': 0.57, 'y': 0.30},
            {'x': 0.94, 'y': 0.57},
            {'x': 0.57, 'y': 0.90},
            {'x': 0.06, 'y': 0.57}
        ]

        self.build_ui()
        # 强制图纸在游戏开始前就正确居中
        Clock.schedule_once(lambda dt: self.update_bg(self, None), 0.01)
        Clock.schedule_once(lambda dt: self._init_round(), 0.2)
        self.start_game()

    def build_ui(self):
        """构建游戏界面 - 物理画卷缩放（绝对保证元素钉死在画布上）"""
        self.clear_widgets()

        # 1. 定义永远不变的基准尺寸
        self.BASE_WIDTH = 1920
        self.BASE_HEIGHT = 1080

        # 2. 绿色背景
        with self.canvas.before:
            Color(0.08, 0.42, 0.18, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        # 3. 最核心：物理画卷容器
        from kivy.uix.scatter import Scatter
        self.game_canvas = Scatter(
            do_rotation=False,  # 绝对禁止旋转
            do_scale=True,  # 允许缩放
            do_translation=False,  # 绝对禁止平移（钉死在屏幕上）
            size_hint=(None, None),
            size=(self.BASE_WIDTH, self.BASE_HEIGHT),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}  # 永远死死钉在屏幕正中央
        )
        self.add_widget(self.game_canvas)

        # 4. 加上一个强约束：无论怎么缩放，画面永远嵌在屏幕内，绝不越界
        from kivy.core.window import Window
        def enforce_aspect_ratio(*args):
            win_w, win_h = Window.size
            # 计算完美比例，确保游戏能完整装进屏幕
            scale = min(win_w / self.BASE_WIDTH, win_h / self.BASE_HEIGHT)
            self.game_canvas.scale = scale

        Window.bind(on_resize=enforce_aspect_ratio)
        Clock.schedule_once(lambda dt: enforce_aspect_ratio(), 0.01)  # 启动时立刻计算

        # 5. 把你的游戏容器全部放进这个画布里
        self.table_area = RelativeLayout(size=(self.BASE_WIDTH, self.BASE_HEIGHT))
        self.game_canvas.add_widget(self.table_area)

        self.static_container = RelativeLayout(size=(self.BASE_WIDTH, self.BASE_HEIGHT))
        self.hand_container = RelativeLayout(size=(self.BASE_WIDTH, self.BASE_HEIGHT))
        self.dynamic_container = RelativeLayout(size=(self.BASE_WIDTH, self.BASE_HEIGHT))

        self.table_area.add_widget(self.static_container)
        self.table_area.add_widget(self.hand_container)
        self.table_area.add_widget(self.dynamic_container)

        # 6. 消息提示（不参与缩放，永远清晰）
        self.msg_label = Label(
            text="",
            font_size=22,
            font_name="STLiti",
            color=(1, 1, 1, 1),
            size_hint=(1, 0.05),
            pos_hint={'y': 0.01}
        )
        self.add_widget(self.msg_label)

        # 7. 强制刷新
        Clock.schedule_once(lambda dt: self.update_hand(), 0.2)
        Clock.schedule_once(lambda dt: self.update_dynamic(), 0.3)

    def update_bg(self, instance, value):
        # 只负责让绿色背景铺满屏幕
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _show_message(self, text, color):
        if self.msg_label:
            self.msg_label.text = text
            self.msg_label.color = color
            Clock.schedule_once(lambda dt: self._clear_message(), 2)

    def _clear_message(self):
        if self.msg_label:
            self.msg_label.text = ""

    def start_game(self):
        """开始游戏"""
        self.game_over = False
        if self.game_round == 0:
            self.game_round = 1

        self._shown_cards_created = False
        self.setup_static_elements()

        self.game_active = True
        self.game = self.controller.start_new_game()
        self.game.show_phase = True

        self._ai_show_cards()

        self.show_pending = {}
        self.operated_count = 0
        self.total_showable = 0
        self._operated_keys = set()

        player = self.game.players[0]
        for card in player.hand:
            card_type = card.get_card_type()
            if card_type is not None:
                self.show_pending[card.key()] = True
                self.total_showable += 1

        self.show_phase_time_left = 15
        self.time_left = 15

        Clock.schedule_once(lambda dt: self._init_round(), 0.1)

    def _init_round(self):
        """初始化一轮游戏（延迟执行，确保布局完成）"""
        self.update_hand()
        self.update_dynamic()
        self.draw_table_buttons()
        self.start_show_timer()

    def setup_static_elements(self):
        """设置静态元素（头像、名字、水印）"""
        self.static_container.clear_widgets()

        watermark = Label(
            text=f"第 {self.game_round} 局",
            font_name="STLiti",
            font_size=int(90 * self.scale),  # 动态字体
            color=(0.3, 0.6, 0.3, 0.45),
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.6},
            bold=True
        )
        self.static_container.add_widget(watermark)

        players = [
            {'idx': 2, 'name': '北', 'x': 0.50, 'y': 0.90},
            {'idx': 1, 'name': '东', 'x': 0.88, 'y': 0.60},
            {'idx': 0, 'name': '你', 'x': 0.50, 'y': 0.30},
            {'idx': 3, 'name': '西', 'x': 0.12, 'y': 0.60}
        ]
        for p in players:
            idx = p['idx']
            avatar = AvatarWidget(
                emoji=AVATAR_EMOJIS[idx],
                color=AVATAR_COLORS[idx],
                size=self.AVATAR_SIZE  # 动态尺寸
            )
            avatar.pos_hint = {'center_x': p['x'], 'center_y': p['y']}
            self.static_container.add_widget(avatar)

            if idx == 2:
                name_y = p['y'] + 0.07
            else:
                name_y = p['y'] - 0.07
            name_label = Label(
                text=p['name'],
                font_name="STLiti",
                font_size=int(22 * self.scale),  # 动态字体
                color=(1, 1, 1, 1),
                size_hint=(None, None),
                size=(int(70 * self.scale), int(35 * self.scale)),  # 动态尺寸
                pos_hint={'center_x': p['x'], 'center_y': name_y}
            )
            self.static_container.add_widget(name_label)

    def _ai_show_cards(self):
        """AI自动亮牌"""
        for idx in range(1, 4):
            ai_player = self.game.players[idx]
            for card in ai_player.hand[:]:
                card_type = card.get_card_type()
                if card_type is not None:
                    if self.ai.should_show_card(ai_player, card, self.game):
                        ai_player.shown_cards.append(card)
                        self.game.update_global_shown(card_type)
                        print(f"🤖 {ai_player.name} 亮牌: {card}")

        self._display_ai_shown_cards()

    def _display_ai_shown_cards(self):
        """显示AI的亮牌（只显示AI，不涉及玩家）"""
        to_remove = []
        for child in self.static_container.children:
            if isinstance(child, SmallCardWidget):
                if hasattr(child, 'is_ai_card') and child.is_ai_card:
                    to_remove.append(child)
        for child in to_remove:
            self.static_container.remove_widget(child)

        positions = self.shown_card_positions
        card_gap = 0.027

        for idx in range(1, 4):
            player = self.game.players[idx]
            if not player.shown_cards:
                continue

            pos = positions[idx]
            x, y = pos['x'], pos['y']
            card_count = len(player.shown_cards)

            if idx == 2:
                # 【修改点】去掉了 * self.scale，因为 ScatterLayout 外面已经整体缩放了
                show_x = x - 0.13
                show_y = y
                step = card_gap
                start_x = show_x - (card_count - 1) * step / 2
                for i, card in enumerate(player.shown_cards):
                    card_img = SmallCardWidget(card, size=(self.SMALL_CARD_WIDTH, self.SMALL_CARD_HEIGHT))
                    card_img.is_ai_card = True
                    card_img.pos_hint = {
                        'center_x': start_x - i * step,
                        'center_y': show_y
                    }
                    self.static_container.add_widget(card_img)
            else:
                # 【修改点】去掉了 * self.scale
                show_x = x
                show_y = y + 0.12
                step = card_gap
                start_x = show_x - (card_count - 1) * step / 2
                for i, card in enumerate(player.shown_cards):
                    card_img = SmallCardWidget(card, size=(self.SMALL_CARD_WIDTH, self.SMALL_CARD_HEIGHT))
                    card_img.is_ai_card = True
                    card_img.pos_hint = {
                        'center_x': start_x + i * step,
                        'center_y': show_y
                    }
                    self.static_container.add_widget(card_img)

    def setup_shown_cards(self):
        """显示所有亮牌"""
        if self._shown_cards_created:
            return
        self._shown_cards_created = True

        positions = self.shown_card_positions
        card_width_ratio = self.SMALL_CARD_WIDTH / self.width  # 用动态尺寸计算比例

        for idx in range(4):
            if idx != 0:
                continue
            player = self.game.players[idx]
            if not player.shown_cards:
                continue

            pos = positions[idx]
            x, y = pos['x'], pos['y']

            if idx == 2:
                # 【修改点】去掉了 * self.scale
                show_x = x - 0.12
                show_y = y
                step = card_width_ratio
            elif idx == 0:
                # 【修改点】去掉了 * self.scale
                show_x = x - 0.13
                show_y = y
                step = card_width_ratio
            else:
                show_x = x
                # 【修改点】去掉了 * self.scale
                show_y = y + 0.12
                step = card_width_ratio

            card_count = len(player.shown_cards)
            if idx == 0 or idx == 2:
                for i, card in enumerate(player.shown_cards):
                    card_img = SmallCardWidget(card, size=(self.SMALL_CARD_WIDTH, self.SMALL_CARD_HEIGHT))
                    card_img.pos_hint = {
                        'center_x': show_x - i * step,
                        'center_y': show_y
                    }
                    self.static_container.add_widget(card_img)
            else:
                start_x = show_x - (card_count - 1) * step / 2
                for i, card in enumerate(player.shown_cards):
                    card_img = SmallCardWidget(card, size=(self.SMALL_CARD_WIDTH, self.SMALL_CARD_HEIGHT))
                    card_img.pos_hint = {
                        'center_x': start_x + i * step,
                        'center_y': show_y
                    }
                    self.static_container.add_widget(card_img)

    def update_hand(self):
        """更新手牌"""
        self.hand_container.clear_widgets()
        self._draw_hand_cards()

    def _draw_hand_cards(self):
        """绘制手牌"""
        if not self.game_active:
            return

        player = self.game.players[0]
        if len(player.hand) == 0:
            return

        # ===== 1. 强制固定宽度（因为外层是 Scatter 布局，固定 1920 最稳） =====
        table_width = 1920  # 不管你之前改没改，这里我直接硬编码
        card_gap = 4  # 牌和牌之间的缝隙

        # ===== 2. 计算牌的具体大小 =====
        card_count = len(player.hand)

        # 使用我们之前在 __init__ 里计算的基准大小 (108 * 1.0 = 108)
        ideal_width = self.CARD_WIDTH_BASE * 0.65
        ideal_height = ideal_width * (155 / 108)

        # 计算如果按理想大小排列，所有牌的总宽度
        total_ideal_width = card_count * (ideal_width + card_gap) - card_gap

        # 如果总宽度超出 1920 的桌面（比如在手机上），就强制挤一挤
        if total_ideal_width > table_width:
            card_width = (table_width - (card_count - 1) * card_gap) / card_count
            card_height = card_width * (155 / 108)
        else:
            card_width = ideal_width
            card_height = ideal_height

        card_size = (card_width, card_height)

        # ===== 3. 计算起始位置 =====
        # 重新算一遍总宽度用于居中
        total_width = card_count * (card_width + card_gap) - card_gap
        start_x = (table_width - total_width) / 2

        # ===== 4. 最重要的绘制循环 =====
        for i, card in enumerate(player.hand):
            can_play = False
            is_shown = self.game.is_shown_card(player, card)
            is_my_turn = (self.game.current_turn == 0 and not self.game.show_phase)
            is_show_phase = self.game.show_phase

            if is_my_turn and not is_show_phase:
                can_play = card in self.game.get_legal_cards(player, self.game.lead_suit)

            card_widget = CardWidget(card, size=card_size)
            card_widget.is_hand_card = True

            is_raised = False
            if is_show_phase:
                card_type = card.get_card_type()
                if card_type is not None and not is_shown:
                    if self.show_pending.get(card.key(), True):
                        is_raised = True

            # 设置 Y 轴位置：如果有抬起效果，就往上挪一点点
            # 设置 Y 轴位置：强制将手牌从图纸底部往上提 750 像素，让牌铺满视野
            if is_raised:
                y_pos = 30  # 抬起的牌再加 10 像素
                card_widget.is_raised = True
            else:
                y_pos = 30  # 基础高度提升到 750

            # 设置绝对位置！（最关键的一步）
            card_widget.pos = (start_x + i * (card_width + card_gap), y_pos)
            card_widget.size = card_size

            if is_shown:
                card_widget.add_star()

            if is_show_phase and not is_shown:
                card_type = card.get_card_type()
                if card_type is not None:
                    if self.show_pending.get(card.key(), True):
                        card_widget.add_status_label("▲ 亮", (1, 0.84, 0, 1))
                    else:
                        card_widget.add_status_label("▼", (0.5, 0.5, 0.5, 1))

            if can_play:
                card_widget.bind(on_touch_down=lambda instance, touch, c=card: self.on_card_touch(instance, touch, c))
            elif is_show_phase and not is_shown:
                card_widget.bind(on_touch_down=lambda instance, touch, c=card: self.on_card_touch(instance, touch, c))

            # 把手牌加入到容器中
            self.hand_container.add_widget(card_widget)
            print(f"🃏 画了一张牌: {card}")
            print(f"  -> 坐标: x={card_widget.pos[0]:.1f}, y={card_widget.pos[1]:.1f}")
            print(f"  -> 容器底部位置: {self.hand_container.pos}")


    def update_dynamic(self):
        """更新动态内容（得分牌、圈牌）"""
        self.dynamic_container.clear_widgets()
        if self.game_over:
            return

        players_pos = [
            {'idx': 0, 'x': 0.50, 'y': 0.29},
            {'idx': 1, 'x': 1.00, 'y': 0.59},
            {'idx': 2, 'x': 0.50, 'y': 0.91},
            {'idx': 3, 'x': 0.00, 'y': 0.59}
        ]

        for p in players_pos:
            idx = p['idx']
            player = self.game.players[idx]
            score_cards = [c for c in player.score_cards if c.is_score_card()]
            score = self.game.calculate_score(player)

            if score_cards:
                if idx == 0:
                    sc_x, sc_y = p['x'], p['y'] + 0.10
                    label_y = sc_y - 0.06
                    label_x = sc_x + 0.07
                elif idx == 2:
                    sc_x, sc_y = p['x'], p['y'] - 0.10
                    label_y = sc_y + 0.06
                    label_x = sc_x + 0.07
                elif idx == 1:
                    sc_x, sc_y = p['x'] - 0.11, p['y']
                    label_y = sc_y + 0.15
                    label_x = sc_x - 0.0
                else:
                    sc_x, sc_y = p['x'] + 0.11, p['y']
                    label_y = sc_y + 0.15
                    label_x = sc_x + 0.0

                gap = 0.015
                n = len(score_cards)
                if n > 0:
                    if idx == 0 or idx == 2:
                        total_width = (n - 1) * gap
                        start_x = sc_x - total_width / 2
                        for i, card in enumerate(score_cards):
                            card_img = SmallCardWidget(card, size=(self.SMALL_CARD_WIDTH, self.SMALL_CARD_HEIGHT),
                                                       rotated=False)  # 动态尺寸
                            card_img.pos_hint = {
                                'center_x': start_x + i * gap,
                                'center_y': sc_y
                            }
                            card_img.is_score_card = True
                            self.dynamic_container.add_widget(card_img)
                    else:
                        gap = 0.026
                        total_height = (n - 1) * gap
                        start_y = sc_y - total_height / 2
                        for i, card in enumerate(score_cards):
                            card_img = SmallCardWidget(card, size=(self.SMALL_CARD_HEIGHT, self.SMALL_CARD_WIDTH),
                                                       rotated=True)  # 动态尺寸
                            card_img.pos_hint = {
                                'center_x': sc_x,
                                'center_y': start_y + i * gap
                            }
                            card_img.is_score_card = True
                            self.dynamic_container.add_widget(card_img)

                if score != 0:
                    score_color = (1, 0.6, 0, 1) if score < 0 else (0, 1, 0, 1)
                    score_label = Label(
                        text=f"{score}分",
                        font_name="STLiti",
                        font_size=int(20 * self.scale),  # 动态字体
                        color=score_color,
                        size_hint=(None, None),
                        size=(int(60 * self.scale), int(24 * self.scale)),  # 动态尺寸
                        pos_hint={'center_x': label_x, 'center_y': label_y},
                        bold=True
                    )
                    score_label.is_score_label = True
                    self.dynamic_container.add_widget(score_label)

        if self.game.trick_cards:
            trick_positions = [
                {'x': 0.50, 'y': 0.49, 'idx': 0},
                {'x': 0.83, 'y': 0.60, 'idx': 1},
                {'x': 0.50, 'y': 0.71, 'idx': 2},
                {'x': 0.17, 'y': 0.60, 'idx': 3}
            ]
            for player_idx, card in self.game.trick_cards:
                pos = trick_positions[player_idx]
                # 桌面打出的牌：用动态基准尺寸乘以0.55
                card_img = CardWidget(card, size=(self.CARD_WIDTH_BASE * 0.55, self.CARD_HEIGHT_BASE * 0.55))
                card_img.pos_hint = {'center_x': pos['x'], 'center_y': pos['y']}
                card_img.is_trick_card = True
                self.dynamic_container.add_widget(card_img)

    def draw_table_buttons(self):
        """绘制亮牌按钮"""
        for item in self.show_btns:
            if item in self.children:
                self.remove_widget(item)
        self.show_btns = []
        if self.timer_label:
            if self.timer_label in self.children:
                self.remove_widget(self.timer_label)
            self.timer_label = None

        if self.game.show_phase:
            self.timer_label = Label(
                text=f"⏰ {self.show_phase_time_left}s",
                font_name="STLiti",
                font_size=int(24 * self.scale),  # 动态字体
                color=(1, 1, 0, 1),
                size_hint=(None, None),
                size=(int(100 * self.scale), int(35 * self.scale)),  # 动态尺寸
                pos_hint={'center_x': 0.50, 'center_y': 0.68}
            )
            self.add_widget(self.timer_label)

            if self.total_showable > 0:
                show_btn = GlowingButton(
                    text="亮牌",
                    size_hint=(None, None),
                    size=(int(75 * self.scale), int(40 * self.scale)),  # 动态尺寸
                    pos_hint={'center_x': 0.45, 'center_y': 0.4},
                    color=(1, 0.84, 0, 1),
                    font_size=int(15 * self.scale),  # 动态字体
                    font_name="STLiti",
                    bold=True,
                    bg_color=(0.2, 0.6, 0.2, 1)
                )
                show_btn.bind(on_release=lambda x: self.confirm_show())
                self.add_widget(show_btn)
                self.show_btns.append(show_btn)

                not_show_btn = GlowingButton(
                    text="不亮",
                    size_hint=(None, None),
                    size=(int(75 * self.scale), int(40 * self.scale)),  # 动态尺寸
                    pos_hint={'center_x': 0.55, 'center_y': 0.4},
                    color=(1, 0.84, 0, 1),
                    font_size=int(15 * self.scale),  # 动态字体
                    font_name="STLiti",
                    bold=True,
                    bg_color=(0.2, 0.6, 0.2, 1)
                )
                not_show_btn.bind(on_release=lambda x: self.confirm_not_show())
                self.add_widget(not_show_btn)
                self.show_btns.append(not_show_btn)

                hint_label = Label(
                    text="💡 点击手牌切换亮牌状态",
                    font_name="STLiti",
                    font_size=int(14 * self.scale),  # 动态字体
                    color=(0.7, 0.7, 0.7, 1),
                    size_hint=(1, 0.03),
                    pos_hint={'y': 0.52}
                )
                self.add_widget(hint_label)
                self.show_btns.append(hint_label)
            else:
                wait_label = Label(
                    text="⏳ 等待其他玩家亮牌...",
                    font_name="STLiti",
                    font_size=int(18 * self.scale),  # 动态字体
                    color=(0.7, 0.7, 0.7, 1),
                    size_hint=(1, 0.05),
                    pos_hint={'y': 0.56}
                )
                self.add_widget(wait_label)
                self.show_btns.append(wait_label)

    def start_show_timer(self):
        """启动亮牌计时器"""
        self.show_phase_time_left = 15

        def countdown(dt):
            if not self.game_active:
                return False

            self.show_phase_time_left -= 1

            if self.timer_label:
                self.timer_label.text = f"⏰ {self.show_phase_time_left}s"
                if self.show_phase_time_left <= 3:
                    self.timer_label.color = (1, 0, 0, 1)

            if self.show_phase_time_left <= 0:
                self.show_pending = {k: False for k in self.show_pending}
                self.update_hand()
                self.end_show_phase()
                return False

            return True

        self.show_timer_id = Clock.schedule_interval(countdown, 1)

    def toggle_show(self, card):
        """切换亮牌状态"""
        if not self.game_active or not self.game.show_phase:
            return

        player = self.game.players[0]

        for shown_card in player.shown_cards:
            if shown_card.suit == card.suit and shown_card.rank == card.rank:
                self._show_message("❌ 这张牌已经亮了", (1, 0, 0, 1))
                return

        card_type = card.get_card_type()
        if card_type is None:
            return

        current = self.show_pending.get(card.key(), True)
        self.show_pending[card.key()] = not current

        if card.key() not in self._operated_keys:
            self._operated_keys.add(card.key())
            self.operated_count += 1

        if self.show_pending[card.key()]:
            self._show_message(f"🔺 {card} 待亮", (1, 0.84, 0, 1))
        else:
            self._show_message(f"🔽 {card} 不亮", (0.6, 0.6, 0.6, 1))

        self.update_hand()

    def confirm_show(self):
        """确认亮牌"""
        if not self.game_active or not self.game.show_phase:
            return

        if self.show_timer_id:
            self.show_timer_id.cancel()
            self.show_timer_id = None

        player = self.game.players[0]

        for card in player.hand[:]:
            card_key = card.key()
            card_type = card.get_card_type()
            if card_type is not None:
                already_shown = False
                for shown_card in player.shown_cards:
                    if shown_card.suit == card.suit and shown_card.rank == card.rank:
                        already_shown = True
                        break
                if already_shown:
                    continue
                if self.show_pending.get(card_key, False):
                    player.shown_cards.append(card)
                    self.game.update_global_shown(card_type)
                    print(f"⭐ 亮牌: {card}")

        self.update_hand()
        self.end_show_phase()

    def confirm_not_show(self):
        """确认不亮"""
        if not self.game_active or not self.game.show_phase:
            return

        if self.show_timer_id:
            self.show_timer_id.cancel()
            self.show_timer_id = None

        self.show_pending = {k: False for k in self.show_pending}
        self.update_hand()
        self.end_show_phase()

    def end_show_phase(self):
        """结束亮牌阶段"""
        self.game.show_phase = False

        for item in self.show_btns:
            if item in self.children:
                self.remove_widget(item)
        self.show_btns = []
        if self.timer_label:
            if self.timer_label in self.children:
                self.remove_widget(self.timer_label)
            self.timer_label = None
        self.show_pending = {}

        self.setup_shown_cards()
        self.update_hand()
        self.update_dynamic()

        if self.game.current_turn != 0:
            Clock.schedule_once(lambda dt: self.ai_play_turn(), 0.5)
        else:
            self.start_play_timer()

    def on_card_touch(self, instance, touch, card):
        """点击手牌"""
        if not instance.collide_point(touch.x, touch.y):
            return

        if self.game.show_phase:
            self.toggle_show(card)
            return

        if self.game.current_turn == 0 and not self.game.show_phase:
            self.play_card(card)

    def play_card(self, card):
        """玩家出牌"""
        if not self.game_active or self.game.current_turn != 0 or self.game.show_phase:
            return

        legal = self.game.get_legal_cards(self.game.players[0], self.game.lead_suit)
        if card not in legal:
            self._show_message("❌ 不能出这张牌", (1, 0, 0, 1))
            return

        self.stop_timer()
        self.execute_play(0, card)

    def start_play_timer(self):
        """启动出牌计时器"""
        if self.timer_id:
            self.timer_id.cancel()
            self.timer_id = None

        if self.play_timer_label:
            if self.play_timer_label in self.children:
                self.remove_widget(self.play_timer_label)
            self.play_timer_label = None

        self.time_left = 15

        self.play_timer_label = Label(
            text=f"⏰ {self.time_left}s",
            font_name="STLiti",
            font_size=int(28 * self.scale),  # 动态字体
            color=(1, 0.5, 0, 1),
            size_hint=(None, None),
            size=(int(100 * self.scale), int(40 * self.scale)),  # 动态尺寸
            pos_hint={'center_x': 0.50, 'center_y': 0.48}
        )
        self.add_widget(self.play_timer_label)

        def countdown(dt):
            if not self.game_active:
                return False

            self.time_left -= 1
            if self.play_timer_label:
                self.play_timer_label.text = f"⏰ {self.time_left}s"
                if self.time_left <= 3:
                    self.play_timer_label.color = (1, 0, 0, 1)

            if self.time_left <= 0:
                if self.play_timer_label and self.play_timer_label in self.children:
                    self.remove_widget(self.play_timer_label)
                    self.play_timer_label = None
                self.auto_play()
                return False
            return True

        self.timer_id = Clock.schedule_interval(countdown, 1)

    def auto_play(self):
        if not self.game_active:
            return

        player = self.game.players[self.game.current_turn]
        legal = self.game.get_legal_cards(player, self.game.lead_suit)
        if legal:
            self.execute_play(self.game.current_turn, legal[0])

    def stop_timer(self):
        if self.timer_id:
            self.timer_id.cancel()
            self.timer_id = None
        if self.show_timer_id:
            self.show_timer_id.cancel()
            self.show_timer_id = None

        if self.play_timer_label and self.play_timer_label in self.children:
            self.remove_widget(self.play_timer_label)
            self.play_timer_label = None

        for child in self.children[:]:
            if isinstance(child, Label) and "⏰" in child.text:
                self.remove_widget(child)

    def execute_play(self, player_idx, card):
        if card not in self.game.players[player_idx].hand:
            return

        if self.game.lead_suit is None:
            self.game.lead_suit = card.suit

        self.game.players[player_idx].hand.remove(card)
        self.game.trick_cards.append((player_idx, card))

        self.update_hand()
        self.update_dynamic()

        if len(self.game.trick_cards) == 4:
            Clock.schedule_once(lambda dt: self.finish_trick(), 0.5)
        else:
            self.game.current_turn = (self.game.current_turn + 1) % 4
            self.update_hand()
            if self.game.current_turn == 0:
                self.start_play_timer()
            else:
                Clock.schedule_once(lambda dt: self.ai_play_turn(), 0.5)

    def finish_trick(self):
        winner = self.game.determine_winner(self.game.trick_cards, self.game.lead_suit)

        if self.game.lead_suit is not None:
            self.game.suits_that_have_been_led.add(self.game.lead_suit)

        self.animate_trick_cards(winner)

    def animate_trick_cards(self, winner):
        trick_cards = self.game.trick_cards
        if not trick_cards:
            self.finish_trick_after_animation(winner)
            return

        player_positions = [
            {'x': 0.50, 'y': 0.38, 'idx': 0},
            {'x': 0.70, 'y': 0.50, 'idx': 1},
            {'x': 0.50, 'y': 0.68, 'idx': 2},
            {'x': 0.30, 'y': 0.50, 'idx': 3}
        ]

        if winner == 0:
            target_x = 0.50
            target_y = 0.25 + 0.10
        elif winner == 2:
            target_x = 0.50
            target_y = 0.82 - 0.10
        elif winner == 1:
            target_x = 0.85 - 0.10
            target_y = 0.50
        else:
            target_x = 0.15 + 0.10
            target_y = 0.50

        flying_cards = []
        for i, (player_idx, card) in enumerate(trick_cards):
            start_pos = player_positions[player_idx]
            start_x = start_pos['x']
            start_y = start_pos['y']

            offset_x = (i - 1.5) * 0.018
            offset_y = (i - 1.5) * 0.012

            flying_card = FlyingCardWidget(
                card,
                (start_x, start_y),
                (target_x + offset_x, target_y + offset_y)
            )
            flying_card.pos_hint = {'center_x': start_x, 'center_y': start_y}
            flying_card.size = (self.SMALL_CARD_WIDTH, self.SMALL_CARD_HEIGHT)  # 动态尺寸
            self.dynamic_container.add_widget(flying_card)
            flying_cards.append(flying_card)

        def update_animation(dt):
            all_done = True
            for card in flying_cards:
                if not card.flying:
                    continue

                card.progress += 0.06
                if card.progress >= 1:
                    card.progress = 1
                    card.flying = False

                progress = card.progress
                eased = 1 - (1 - progress) * (1 - progress)

                current_x = card.start_pos[0] + (card.end_pos[0] - card.start_pos[0]) * eased
                current_y = card.start_pos[1] + (card.end_pos[1] - card.start_pos[1]) * eased
                card.pos_hint = {'center_x': current_x, 'center_y': current_y}

                if card.flying:
                    all_done = False

            if all_done:
                for card in flying_cards:
                    self.dynamic_container.remove_widget(card)
                for _, card in trick_cards:
                    self.game.players[winner].score_cards.append(card)
                self.finish_trick_after_animation(winner)
                return False

            return True

        Clock.schedule_interval(update_animation, 0.03)

    def finish_trick_after_animation(self, winner):
        self.game.current_turn = winner
        self.game.lead_suit = None
        self.game.trick_cards = []

        self.update_dynamic()
        self.update_hand()

        player = self.game.players[winner]
        score = self.game.calculate_score(player)
        if score != 0:
            self._show_message(f"🎯 {player.name} 获得 {score}分", (1, 0.84, 0, 1))

        if len(self.game.players[0].hand) == 0:
            Clock.schedule_once(lambda dt: self.finish_game(), 0.5)
        elif self.game.current_turn == 0:
            self.start_play_timer()
        else:
            Clock.schedule_once(lambda dt: self.ai_play_turn(), 0.5)

    def ai_play_turn(self):
        """AI出牌"""
        if not self.game_active or self.game.current_turn == 0 or self.game.show_phase:
            return

        player = self.game.players[self.game.current_turn]
        legal = self.game.get_legal_cards(player, self.game.lead_suit)

        if not legal:
            self.game.current_turn = (self.game.current_turn + 1) % 4
            Clock.schedule_once(lambda dt: self.ai_play_turn(), 0.5)
            return

        card = min(legal, key=lambda c: c.value())
        Clock.schedule_once(lambda dt: self.execute_play(self.game.current_turn, card), 0.3)

    def finish_game(self):
        """游戏结束 - 锦旗风格小窗口"""
        self.game_active = False
        self.game_over = True
        self.stop_timer()

        scores = []
        for player in self.game.players:
            score = self.game.calculate_score(player)
            scores.append(score)

        # ===== 小窗口容器 =====
        from kivy.uix.floatlayout import FloatLayout

        result_container = FloatLayout(
            size_hint=(None, None),
            size=(int(320 * self.scale), int(330 * self.scale)),  # 动态尺寸
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(result_container)
        self.game_over_widgets.append(result_container)

        # 锦旗背景
        with result_container.canvas.before:
            Color(0.75, 0.08, 0.08, 1)
            self.result_bg = RoundedRectangle(
                pos=result_container.pos,
                size=result_container.size,
                radius=[20]
            )
            Color(1, 0.84, 0, 1)
            self.result_border = Line(
                rounded_rectangle=(
                    result_container.pos[0] + int(5 * self.scale),
                    result_container.pos[1] + int(5 * self.scale),
                    result_container.size[0] - int(10 * self.scale),
                    result_container.size[1] - int(10 * self.scale),
                    18
                ),
                width=int(3 * self.scale)
            )

        def update_result_bg(instance, value):
            self.result_bg.pos = instance.pos
            self.result_bg.size = instance.size
            self.result_border.rounded_rectangle = (
                instance.pos[0] + int(5 * self.scale),
                instance.pos[1] + int(5 * self.scale),
                instance.size[0] - int(10 * self.scale),
                instance.size[1] - int(10 * self.scale),
                18
            )

        result_container.bind(pos=update_result_bg, size=update_result_bg)

        # ===== 标题 =====
        result_label = Label(
            text=f"第 {self.game_round} 局",
            font_name="STLiti",
            font_size=int(26 * self.scale),  # 动态字体
            color=(1, 0.84, 0, 1),
            size_hint=(1, None),
            height=int(35 * self.scale),  # 动态尺寸
            pos_hint={'x': 0, 'top': 0.95}
        )
        result_container.add_widget(result_label)

        # ===== 分隔线 =====
        line_label = Label(
            text="━" * 14,
            font_name="STLiti",
            font_size=int(14 * self.scale),  # 动态字体
            color=(1, 0.84, 0, 0.5),
            size_hint=(1, None),
            height=int(20 * self.scale),  # 动态尺寸
            pos_hint={'x': 0, 'top': 0.88}
        )
        result_container.add_widget(line_label)

        # ===== 玩家分数 =====
        y_pos = 0.82
        for i, player in enumerate(self.game.players):
            score = scores[i]

            if score > 0:
                emoji = "⭐"
                color = (0.3, 1, 0.3, 1)
                sign = "+"
            elif score < 0:
                emoji = "💪" if score > -30 else "🔥"
                color = (1, 0.5, 0.3, 1)
                sign = ""
            else:
                emoji = "➖"
                color = (1, 1, 1, 0.6)
                sign = ""

            score_label = Label(
                text=f"{emoji} {player.name}：{sign}{score}分",
                font_name="STLiti",
                font_size=int(18 * self.scale),  # 动态字体
                color=color,
                size_hint=(1, None),
                height=int(30 * self.scale),  # 动态尺寸
                pos_hint={'x': 0, 'top': y_pos}
            )
            result_container.add_widget(score_label)
            y_pos -= 0.085

        # ===== 底部装饰线 =====
        line_label2 = Label(
            text="━" * 14,
            font_name="STLiti",
            font_size=int(14 * self.scale),  # 动态字体
            color=(1, 0.84, 0, 0.4),
            size_hint=(1, None),
            height=int(20 * self.scale),  # 动态尺寸
            pos_hint={'x': 0, 'top': 0.48}
        )
        result_container.add_widget(line_label2)

        # ===== 按钮（使用 GlowingButton 统一风格） =====
        continue_btn = GlowingButton(
            text="继续",
            font_name="STLiti",
            size_hint=(None, None),
            size=(int(60 * self.scale), int(40 * self.scale)),  # 动态尺寸
            pos_hint={'center_x': 0.35, 'center_y': 0.30},
            color=(0.3, 0.1, 0.0, 1),
            font_size=int(20 * self.scale),  # 动态字体
            bg_color=(0.9, 0.7, 0.1, 1)
        )
        continue_btn.bind(on_release=self.restart_game)
        result_container.add_widget(continue_btn)

        exit_btn = GlowingButton(
            text="退出",
            font_name="STLiti",
            size_hint=(None, None),
            size=(int(60 * self.scale), int(40 * self.scale)),  # 动态尺寸
            pos_hint={'center_x': 0.65, 'center_y': 0.30},
            color=(0.3, 0.1, 0.0, 1),
            font_size=int(20 * self.scale),  # 动态字体
            bg_color=(0.9, 0.7, 0.1, 1)
        )
        exit_btn.bind(on_release=self.exit_game)
        result_container.add_widget(exit_btn)

    def restart_game(self, *args):
        """重新开始游戏（下一局）- 直接进入发牌，不返回欢迎页面"""
        print("🔄 进入下一局")

        # 清除结束界面
        for widget in self.game_over_widgets[:]:
            if widget in self.children:
                self.remove_widget(widget)
        self.game_over_widgets = []
        self.game_over = False

        # 重置状态
        self.game_active = False
        self.stop_timer()
        self.game_round += 1
        self._shown_cards_created = False

        # 清空容器
        self.dynamic_container.clear_widgets()
        self.hand_container.clear_widgets()

        # 清除 AI 亮牌标记
        for child in self.static_container.children[:]:
            if isinstance(child, SmallCardWidget) and hasattr(child, 'is_ai_card'):
                self.static_container.remove_widget(child)

        # 重新创建游戏
        self.game = self.controller.start_new_game()
        self.game.show_phase = True
        self.game_active = True

        # 更新静态元素
        self.setup_static_elements()

        # AI亮牌
        self._ai_show_cards()

        # 玩家亮牌准备
        self.show_pending = {}
        self.operated_count = 0
        self.total_showable = 0
        self._operated_keys = set()

        player = self.game.players[0]
        for card in player.hand:
            card_type = card.get_card_type()
            if card_type is not None:
                self.show_pending[card.key()] = True
                self.total_showable += 1

        self.show_phase_time_left = 15
        self.time_left = 15

        # 更新界面
        self.update_hand()
        self.update_dynamic()
        self.draw_table_buttons()
        self.start_show_timer()

        print(f"✅ 第 {self.game_round} 局已开始")

    def exit_game(self, *args):
        """退出游戏返回欢迎页"""
        from .welcome import WelcomeScreen
        from kivy.app import App
        self.clear_widgets()
        welcome = WelcomeScreen(
            on_start=lambda: self.parent.start_game() if hasattr(self.parent, 'start_game') else None,
            on_exit=lambda: App.get_running_app().stop()
        )
        self.add_widget(welcome)