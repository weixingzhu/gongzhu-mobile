# view/widgets/button.py
from kivy.uix.button import Button
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import sp
from kivy.graphics.transformation import Matrix

class GlowingButton(Button):
    def __init__(self, text, bg_color=None, **kwargs):
        self.is_hover = False
        self._original_color = kwargs.get('color', (1, 1, 1, 1))
        self._bg_color = bg_color
        self._scale = 1.0  # ✅ 跟踪当前缩放

        kwargs.pop('bg_color', None)

        self._size_hint = kwargs.get('size_hint', (0.3, 0.1))
        self._pos_hint = kwargs.get('pos_hint', None)

        user_font_size = kwargs.get('font_size', 27)
        user_color = kwargs.get('color', (1, 1, 1, 1))
        user_bold = kwargs.get('bold', True)
        user_font_name = kwargs.get('font_name', 'STLiti')

        # 从 kwargs 中移除自定义参数
        kwargs.pop('size_hint', None)
        kwargs.pop('pos_hint', None)

        super().__init__(**kwargs)

        self.text = text
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.background_down = ''

        self.size_hint = self._size_hint
        if self._pos_hint:
            self.pos_hint = self._pos_hint

        self.font_size = sp(user_font_size) if isinstance(user_font_size, (int, float)) else user_font_size
        self.color = user_color
        self.bold = user_bold
        self.font_name = user_font_name
        self._original_color = user_color

        if bg_color is not None:
            self.bind(pos=self._draw_bg, size=self._draw_bg)
            self._draw_bg()

        self.bind(on_press=self.on_press)
        self.bind(on_release=self.on_release)
        self.bind(on_enter=self.on_enter)
        self.bind(on_leave=self.on_leave)

    def _draw_bg(self, *args):
        """绘制背景"""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])

    def _apply_scale(self, scale):
        """安全地应用缩放，避免累积"""
        # 重置变换
        self.transform = Matrix().scale(scale, scale, 1)
        self._scale = scale

    def on_enter(self, *args):
        self.is_hover = True
        self.color = (0, 1, 1, 1)
        # ✅ 直接设置缩放，不使用变换矩阵
        self.transform = Matrix().scale(1.05, 1.05, 1)
        self._scale = 1.05

    def on_leave(self, *args):
        self.is_hover = False
        self.color = self._original_color
        # ✅ 恢复原始大小
        self.transform = Matrix().scale(1.0, 1.0, 1)
        self._scale = 1.0

    def on_press(self, *args):
        # ✅ 按压时缩小
        self.transform = Matrix().scale(0.95, 0.95, 1)
        self._scale = 0.95

    def on_release(self, *args):
        # ✅ 释放时恢复
        self.color = self._original_color
        self.transform = Matrix().scale(1.0, 1.0, 1)
        self._scale = 1.0

'''# view/widgets/button.py
from kivy.uix.button import Button
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle   # ← 添加这行


class GlowingButton(Button):
    def __init__(self, text, bg_color=None, **kwargs):
        self.is_hover = False
        self._original_color = kwargs.get('color', (1, 1, 1, 1))
        self._bg_color = bg_color

        kwargs.pop('bg_color', None)

        user_font_size = kwargs.get('font_size', 27)
        user_color = kwargs.get('color', (1, 1, 1, 1))
        user_bold = kwargs.get('bold', True)
        user_size = kwargs.get('size', (300, 90))
        user_font_name = kwargs.get('font_name', 'C:/Windows/Fonts/msyh.ttc')

        super().__init__(**kwargs)

        self.text = text
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.background_down = ''

        self.size_hint = (None, None)
        self.size = user_size
        self.font_size = user_font_size
        self.color = user_color
        self.bold = user_bold
        self.font_name = user_font_name
        self._original_color = user_color
        self._original_size = user_size

        if bg_color is not None:
            self.bind(pos=self._draw_bg, size=self._draw_bg)
            self._draw_bg()

        self.bind(on_press=self.on_press)
        self.bind(on_release=self.on_release)
        self.bind(on_enter=self.on_enter)
        self.bind(on_leave=self.on_leave)

    def _draw_bg(self, *args):
        """绘制背景"""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])

    def on_enter(self, *args):
        self.is_hover = True
        self.color = (0, 1, 1, 1)
        anim = Animation(size=(self._original_size[0] * 1.05, self._original_size[1] * 1.05), duration=0.1)
        anim.start(self)

    def on_leave(self, *args):
        self.is_hover = False
        self.color = self._original_color
        anim = Animation(size=self._original_size, duration=0.1)
        anim.start(self)

    def on_press(self, *args):
        anim = Animation(size=(self._original_size[0] * 0.95, self._original_size[1] * 0.95), duration=0.05)
        anim.start(self)

    def on_release(self, *args):
        anim = Animation(size=self._original_size, duration=0.05)
        anim.start(self)'''
