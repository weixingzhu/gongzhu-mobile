import os
os.environ['KIVY_NO_ARGS'] = '1'
import sys

# 跨平台静音日志（在 Windows 上存 NUL，在 Linux 上存 /dev/null）
if sys.platform == 'win32':
    sys.stderr = open('NUL', 'w')
else:
    sys.stderr = open('/dev/null', 'w')

from kivy.core.window import Window
from kivy.utils import platform

# 针对 Windows 的图形后端优化
if sys.platform == 'win32':
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

# 注册中文字体
from kivy.core.text import LabelBase
LabelBase.register(name='STLiti', fn_regular='STLITI.TTF')

from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from controller import GameController
from view.screens import WelcomeScreen

class GongZhuApp(App):
    def build(self):
        # 使用最稳定的布局容器，不会疯狂刷新
        self.root = RelativeLayout()
        self.controller = GameController()
        self.show_welcome()
        return self.root

    def show_welcome(self):
        self.root.clear_widgets()
        welcome = WelcomeScreen(
            on_start=self.start_game,
            on_exit=self.exit_app
        )
        welcome.size_hint = (1, 1)
        self.root.add_widget(welcome)

    def start_game(self):
        self.root.clear_widgets()
        from view.screens import GameScreen
        game_screen = GameScreen(self.controller)
        game_screen.size_hint = (1, 1)
        self.root.add_widget(game_screen)

    def exit_app(self):
        self.stop()

if __name__ == '__main__':
    GongZhuApp().run()