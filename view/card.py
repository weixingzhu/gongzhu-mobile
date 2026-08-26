# view/widgets/card.py
import os
from kivy.uix.image import Image
from kivy.uix.label import Label

CARD_WIDTH = 108
CARD_HEIGHT = 155
SMALL_CARD_WIDTH = 30
SMALL_CARD_HEIGHT = 44

class CardWidget(Image):
    def __init__(self, card, size=(CARD_WIDTH, CARD_HEIGHT), **kwargs):
        super().__init__(**kwargs)
        self.card = card
        self.size = size
        self.size_hint = (None, None)
        self.keep_ratio = True
        self.allow_stretch = True
        image_path = f"cards/{card.key()}.png"
        if os.path.exists(image_path):
            self.source = image_path

        self.is_raised = False
        self.raise_offset = 30
        self.status_label = None
        self.star_label = None
        self.border_line = None
        self.is_hand_card = False
        self.is_trick_card = False

    def set_raised(self, raised):
        self.is_raised = raised
        if raised:
            self.y += self.raise_offset
        else:
            self.y -= self.raise_offset

    def add_status_label(self, text, color):
        if self.status_label:
            self.remove_widget(self.status_label)
        self.status_label = Label(
            text=text,
            font_size=16,
            color=color,
            size_hint=(None, None),
            size=(26, 26),
            pos=(self.x + self.width - 32, self.y + (self.raise_offset if self.is_raised else 0) - 3)
        )
        self.add_widget(self.status_label)
        self.bind(pos=self.update_status_pos)

    def update_status_pos(self, instance, value):
        if self.status_label:
            self.status_label.pos = (
            self.x + self.width - 32, self.y + (self.raise_offset if self.is_raised else 0) - 3)

    def add_star(self):
        if self.star_label:
            self.remove_widget(self.star_label)
        self.star_label = Label(
            text="⭐",
            font_size=18,
            color=(1, 0.84, 0, 1),
            size_hint=(None, None),
            size=(30, 30),
            pos=(self.x + self.width - 35, self.y + self.height - 35 + (self.raise_offset if self.is_raised else 0))
        )
        self.add_widget(self.star_label)
        self.bind(pos=self.update_star_pos)

    def update_star_pos(self, instance, value):
        if self.star_label:
            self.star_label.pos = (
            self.x + self.width - 35, self.y + self.height - 35 + (self.raise_offset if self.is_raised else 0))

    def clear_status(self):
        if self.status_label:
            self.remove_widget(self.status_label)
            self.status_label = None
        if self.star_label:
            self.remove_widget(self.star_label)
            self.star_label = None
        if self.border_line:
            self.canvas.before.remove(self.border_line)
            self.border_line = None

class SmallCardWidget(Image):
    def __init__(self, card, size=(SMALL_CARD_WIDTH, SMALL_CARD_HEIGHT), rotated=False, **kwargs):
        kwargs.pop('rotated', None)
        super().__init__(**kwargs)
        self.card = card  # 保存card为实例变量
        self.size = size
        self.size_hint = (None, None)
        self.keep_ratio = True
        self.allow_stretch = True
        self.rotated = rotated

        # 强制重新加载，不使用缓存
        self.reload(rotated)

    def reload(self, rotated):
        """重新加载图片"""
        image_path = f"cards/{self.card.key()}.png"  # 使用 self.card
        if not os.path.exists(image_path):
            return

        if rotated:
            from PIL import Image as PILImage
            import io
            from kivy.core.image import Image as CoreImage

            pil_img = PILImage.open(image_path)
            pil_img = pil_img.rotate(90, expand=True)

            data = io.BytesIO()
            pil_img.save(data, format='png')
            data.seek(0)

            # 每次重新创建纹理，不使用缓存
            self.texture = CoreImage(data, ext='png', nocache=True).texture
            self.texture_size = pil_img.size
        else:
            # 正常加载，也禁用缓存
            self.source = image_path
            self.reload = True  # 强制重新加载

class FlyingCardWidget(Image):
    def __init__(self, card, start_pos, end_pos, **kwargs):
        super().__init__(**kwargs)
        self.card = card
        self.size = (SMALL_CARD_WIDTH, SMALL_CARD_HEIGHT)
        self.size_hint = (None, None)
        self.keep_ratio = True
        self.allow_stretch = True
        image_path = f"cards/{card.key()}.png"
        if os.path.exists(image_path):
            self.source = image_path
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.progress = 0
        self.flying = True




