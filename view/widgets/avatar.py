# view/widgets/avatar.py
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Line


class AvatarWidget(Widget):
    def __init__(self, emoji, color, size=55, **kwargs):
        super().__init__(**kwargs)
        self.size = (size, size)
        self.size_hint = (None, None)
        self.emoji = emoji
        self.color = color

        with self.canvas:
            Color(*color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
            Color(1, 1, 1, 0.8)
            Line(rounded_rectangle=(self.x - 1, self.y - 1, self.size[0] + 2, self.size[1] + 2, 12), width=2)

        self.bind(pos=self.update_canvas, size=self.update_canvas)

        self.emoji_label = Label(
            text=emoji,
            font_size=size * 0.5,
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(size, size),
            pos=(self.x, self.y)
        )
        self.add_widget(self.emoji_label)

    def update_canvas(self, instance, value):
        self.canvas.clear()
        with self.canvas:
            Color(*self.color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
            Color(1, 1, 1, 0.8)
            Line(rounded_rectangle=(self.x - 1, self.y - 1, self.size[0] + 2, self.size[1] + 2, 12), width=2)
        self.emoji_label.pos = (self.x, self.y)