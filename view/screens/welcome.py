# view/screens/welcome.py
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.core.window import Window
from ..widgets import GlowingButton


class WelcomeScreen(FloatLayout):
    def __init__(self, on_start=None, on_exit=None, **kwargs):
        super().__init__(**kwargs)
        # 确保填满父容器
        self.size_hint = (1, 1)
        self.on_start = on_start
        self.on_exit = on_exit
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()

        # ========================
        # 1. 设置与游戏牌桌一致的深绿色背景
        # ========================
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(0.08, 0.42, 0.18, 1)  # 与 game.py 里面一样的 RGBA 值
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)

        # ========================
        # 2. 标题
        # ========================
        welcome_label = Label(
            text="经典四人扑克游戏",
            font_name="STLiti",
            font_size=dp(45),    # 使用 sp 动态适配
            bold=True,
            color=(1, 0.84, 0, 1),
            size_hint=(1, 0.15),
            pos_hint={'center_y': 0.75},
            halign='center'
        )
        self.add_widget(welcome_label)

        # ========================
        # 3. 按钮
        # ========================
        start_btn = GlowingButton(
            text="开始游戏",
            font_name="STLiti",
            font_size=dp(18),
            color=(0.3, 0.1, 0.0, 1),
            size_hint=(0.20, 0.08),
            pos_hint={'center_x': 0.38, 'center_y': 0.45},
            bg_color=(1, 0.84, 0, 1)
        )
        start_btn.bind(on_release=lambda x: self.on_start() if self.on_start else None)
        self.add_widget(start_btn)

        exit_btn = GlowingButton(
            text="🚪 退出游戏",
            font_name="STLiti",
            font_size=dp(18),
            color=(0.3, 0.1, 0.0, 1),
            size_hint=(0.20, 0.08),
            pos_hint={'center_x': 0.62, 'center_y': 0.45},
            bg_color=(1, 0.84, 0, 1)
        )
        exit_btn.bind(on_release=lambda x: self.on_exit() if self.on_exit else None)
        self.add_widget(exit_btn)

    def update_bg(self, instance, value):
        """当窗口大小改变时，更新背景的大小"""
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size