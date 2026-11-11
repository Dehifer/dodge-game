from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.core.window import Window
import random
import math
import json
import os

# --- РАБОТА С РЕКОРДОМ ---
RECORD_FILE = "record.json"

def load_record():
    if os.path.exists(RECORD_FILE):
        try:
            with open(RECORD_FILE, "r") as f:
                return json.load(f).get("highscore", 0)
        except:
            return 0
    return 0

def save_record(score):
    with open(RECORD_FILE, "w") as f:
        json.dump({"highscore": score}, f)

# --- АНИМИРОВАННОЕ МЕНЮ ---
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time = 0
        
        with self.canvas:
            Color(0.05, 0.05, 0.1, 1)
            self.bg = Rectangle(pos=(0, 0), size=Window.size)
            self.stars = []
            for _ in range(50):
                Color(1, 1, 1, random.uniform(0.2, 0.8))
                x = random.randint(0, int(Window.width))
                y = random.randint(0, int(Window.height))
                size = random.randint(2, 4)
                star = Ellipse(pos=(x, y), size=(size, size))
                self.stars.append(star)

        self.layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        self.layout.add_widget(Label(text="", size_hint_y=0.1)) 
        
        self.title_label = Label(text="DODGE\nTHE SHIT", font_size='40sp', bold=True, halign="center")
        self.layout.add_widget(self.title_label)
        
        self.layout.add_widget(Label(text="", size_hint_y=0.1))
        
        self.btn_levels = Button(text="УРОВНИ", font_size='18sp', background_color=(0, 0.8, 0.4, 1), size_hint_y=0.12)
        self.btn_levels.bind(on_press=lambda x: self.start_mode('levels'))
        self.layout.add_widget(self.btn_levels)

        self.btn_record = Button(text="НА РЕКОРД", font_size='18sp', background_color=(0.8, 0.4, 0, 1), size_hint_y=0.12)
        self.btn_record.bind(on_press=lambda x: self.start_mode('record'))
        self.layout.add_widget(self.btn_record)

        self.btn_mp = Button(text="МУЛЬТИПЛЕЕР (2 ИГРОКА)", font_size='18sp', background_color=(0.2, 0.4, 0.9, 1), size_hint_y=0.12)
        self.btn_mp.bind(on_press=lambda x: self.start_mode('multiplayer'))
        self.layout.add_widget(self.btn_mp)
        
        self.add_widget(self.layout)
        
        Clock.schedule_interval(self.animate_menu, 1/60.0)

    def animate_menu(self, dt):
        self.time += dt
        r = (math.sin(self.time * 3) + 1) / 2
        b = 1 - r
        self.title_label.color = (r, 0, b, 1)
        
        for star in self.stars:
            star.pos = (star.pos[0], star.pos[1] - 50 * dt)
            if star.pos[1] < 0:
                star.pos = (random.randint(0, int(Window.width)), int(Window.height))

    def start_mode(self, mode):
        game_screen = self.manager.get_screen('game')
        game_screen.setup_mode(mode)
        self.manager.current = 'game'

# --- ИГРОВОЙ ЭКРАН ---
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_active = False
        self.mode = 'levels'
        
        self.score = 0
        self.level = 1
        self.target_score = 10
        self.time_elapsed = 0
        self.spawn_timer = 0
        
        self.high_score = load_record()
        
        self.area = FloatLayout() 
        self.add_widget(self.area)
        
        self.ui_top = BoxLayout(orientation='vertical', size_hint=(1, 0.1), pos_hint={'top': 1})
        self.ui_label = Label(text="", font_size='20sp', halign="left")
        self.ui_top.add_widget(self.ui_label)
        self.add_widget(self.ui_top)

        self.ui_bottom = BoxLayout(orientation='vertical', size_hint=(1, 0.1), pos_hint={'y': 0})
        self.record_label = Label(text="", font_size='18sp', halign="center")
        self.ui_bottom.add_widget(self.record_label)
        self.add_widget(self.ui_bottom)

        self.p1 = None
        self.p2 = None
        self.obstacles = []

    def setup_mode(self, mode):
        self.mode = mode
        self.start_game()

    def start_game(self):
        if hasattr(self, 'game_clock'):
            Clock.unschedule(self.game_clock)
        self.area.clear_widgets()
        self.area.canvas.clear()
        
        self.obstacles = []
        self.score = 0
        self.time_elapsed = 0
        self.spawn_timer = 0.5
        self.game_active = True
        self.p1 = None
        self.p2 = None
        
        if self.mode == 'levels':
            self.target_score = self.level * 10
            self.ui_label.text = f"УРОВЕНЬ: {self.level} | ЦЕЛЬ: 0/{self.target_score}"
            self.record_label.text = ""
            self.create_player(1)
        elif self.mode == 'record':
            self.level = 1
            self.high_score = load_record()
            self.ui_label.text = "ВРЕМЯ: 0с | СЧЕТ: 0"
            self.record_label.text = f"РЕКОРД: {self.high_score}"
            self.create_player(1)
        elif self.mode == 'multiplayer':
            self.ui_label.text = "ВЫЖИВИ! ЛЕВО - ЗЕЛЕНЫЙ, ПРАВО - СИНИЙ"
            self.record_label.text = ""
            self.create_player(1) # Левый
            self.create_player(2) # Правый
        
        self.game_clock = Clock.schedule_interval(self.update, 1/60.0)

    def create_player(self, player_num):
        if player_num == 1:
            self.p1 = Widget(size_hint=(None, None), size=(50, 50), pos=(Window.width/4 - 25, 50))
            with self.p1.canvas:
                Color(0, 1, 0, 1) # Зеленый
                self.p1.rect = Rectangle(pos=self.p1.pos, size=self.p1.size)
            self.area.add_widget(self.p1)
        else:
            self.p2 = Widget(size_hint=(None, None), size=(50, 50), pos=((Window.width*3/4) - 25, 50))
            with self.p2.canvas:
                Color(0, 0.5, 1, 1) # Синий
                self.p2.rect = Rectangle(pos=self.p2.pos, size=self.p2.size)
            self.area.add_widget(self.p2)

    def update(self, dt):
        if not self.game_active:
            return

        self.time_elapsed += dt
        
        if self.mode == 'levels':
            fall_speed = 250 + (self.level * 50)
            spawn_rate = max(0.2, 0.8 - (self.level * 0.1))
        else:
            fall_speed = 300 + (self.time_elapsed * 25)
            spawn_rate = max(0.15, 1.0 - (self.time_elapsed * 0.02))

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_obstacle()
            self.spawn_timer = spawn_rate

        for obs in self.obstacles[:]:
            obs.pos = (obs.pos[0], obs.pos[1] - fall_speed * dt)
            obs.rect.pos = obs.pos
            
            # Проверка коллизий для Игрока 1
            if self.p1 and self.check_collision(self.p1, obs):
                self.area.remove_widget(self.p1)
                self.p1 = None
                
            # Проверка коллизий для Игрока 2
            if self.p2 and self.check_collision(self.p2, obs):
                self.area.remove_widget(self.p2)
                self.p2 = None
                
            # Если оба мертвы в мультиплеере
            if self.mode == 'multiplayer' and not self.p1 and not self.p2:
                self.game_over()
                return

            if obs.pos[1] < -100:
                self.area.remove_widget(obs)
                self.obstacles.remove(obs)
                
                # Очки даем только в сингле
                if self.mode != 'multiplayer':
                    self.score += 1
                    if self.mode == 'levels':
                        self.ui_label.text = f"УРОВЕНЬ: {self.level} | ЦЕЛЬ: {self.score}/{self.target_score}"
                        if self.score >= self.target_score:
                            self.level_passed()
                            return
                    else:
                        self.ui_label.text = f"ВРЕМЯ: {int(self.time_elapsed)}с | СЧЕТ: {self.score}"

        # Если в одиночной игре игрок умер
        if self.mode != 'multiplayer' and not self.p1:
            self.game_over()
            return

    def level_passed(self):
        self.game_active = False
        Clock.unschedule(self.game_clock)
        
        overlay = BoxLayout(orientation='vertical', size_hint=(0.8, 0.4), pos_hint={'center_x': 0.5, 'center_y': 0.5}, spacing=10)
        with self.area.canvas.before:
            Color(0, 0, 0, 0.8)
            self.overlay_bg = Rectangle(pos=(0, 0), size=Window.size)
            
        lbl = Label(text=f"УРОВЕНЬ {self.level} ПРОЙДЕН!", font_size='24sp', color=(0, 1, 0, 1))
        overlay.add_widget(lbl)
        
        btn_next = Button(text="СЛЕДУЮЩИЙ УРОВЕНЬ", background_color=(0, 0.8, 0.4, 1))
        btn_next.bind(on_press=self.next_level)
        overlay.add_widget(btn_next)
        
        btn_menu = Button(text="ВЫЙТИ В МЕНЮ", background_color=(0.5, 0.5, 0.5, 1))
        btn_menu.bind(on_press=self.go_to_menu)
        overlay.add_widget(btn_menu)
        
        self.area.add_widget(overlay)

    def next_level(self, instance):
        self.level += 1
        self.area.canvas.before.clear()
        self.start_game()

    def spawn_obstacle(self):
        size = random.randint(40, 70)
        x = random.randint(0, int(Window.width) - size)
        y = Window.height
        
        obs = Widget(size_hint=(None, None), size=(size, size), pos=(x, y))
        with obs.canvas:
            Color(1, 0, 0, 1)
            obs.rect = Rectangle(pos=obs.pos, size=obs.size)
            
        self.obstacles.append(obs)
        self.area.add_widget(obs)

    def check_collision(self, p1, p2):
        return (p1.x < p2.x + p2.width and
                p1.x + p1.width > p2.x and
                p1.y < p2.y + p2.height and
                p1.y + p1.height > p2.y)

    def on_touch_down(self, touch):
        if self.game_active:
            self.on_touch_move(touch)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.game_active:
            # В мультиплеере разделяем экран пополам
            if self.mode == 'multiplayer':
                if touch.x < Window.width / 2:
                    if self.p1:
                        new_x = touch.x - self.p1.width / 2
                        new_x = max(0, min(new_x, (Window.width / 2) - self.p1.width))
                        self.p1.pos = (new_x, self.p1.pos[1])
                        self.p1.rect.pos = self.p1.pos
                else:
                    if self.p2:
                        new_x = touch.x - self.p2.width / 2
                        new_x = max(Window.width / 2, min(new_x, Window.width - self.p2.width))
                        self.p2.pos = (new_x, self.p2.pos[1])
                        self.p2.rect.pos = self.p2.pos
            # В сингле управляем одним
            else:
                if self.p1:
                    new_x = touch.x - self.p1.width / 2
                    new_x = max(0, min(new_x, Window.width - self.p1.width))
                    self.p1.pos = (new_x, self.p1.pos[1])
                    self.p1.rect.pos = self.p1.pos
            return True
        return super().on_touch_move(touch)

    def game_over(self):
        self.game_active = False
        Clock.unschedule(self.game_clock)
        
        if self.mode == 'multiplayer':
            self.ui_label.text = "ИГРА ОКОНЧЕНА. ВЫ ОБА СДОХЛИ."
        elif self.mode == 'record':
            if self.score > self.high_score:
                self.high_score = self.score
                save_record(self.high_score)
                self.record_label.text = f"РЕКОРД: {self.high_score} (НОВЫЙ!)"
            else:
                self.record_label.text = f"РЕКОРД: {self.high_score}"
            self.ui_label.text = f"ТЫ СДОХ. Счет: {self.score}"
        else:
            self.ui_label.text = f"ТЫ СДОХ НА УРОВНЕ {self.level}. ЦЕЛЬ: {self.score}/{self.target_score}"
            
        with self.area.canvas:
            Color(1, 0, 0, 0.5)
            self.flash = Rectangle(pos=(0, 0), size=Window.size)
            
        overlay = BoxLayout(orientation='vertical', size_hint=(0.6, 0.2), pos_hint={'center_x': 0.5, 'center_y': 0.5}, spacing=10)
        
        btn_restart = Button(text="ЗАНОВО", background_color=(0, 0.8, 0.4, 1))
        btn_restart.bind(on_press=lambda x: self.restart_death())
        overlay.add_widget(btn_restart)

        btn_menu = Button(text="В МЕНЮ", background_color=(0.5, 0.5, 0.5, 1))
        btn_menu.bind(on_press=self.go_to_menu)
        overlay.add_widget(btn_menu)
        
        self.area.add_widget(overlay)

    def restart_death(self):
        self.area.clear_widgets()
        self.area.canvas.clear()
        if self.mode == 'levels':
            self.level = 1
        self.start_game()

    def go_to_menu(self, instance):
        self.game_active = False
        if hasattr(self, 'game_clock'):
            Clock.unschedule(self.game_clock)
        self.manager.current = 'menu'

# --- ЗАПУСК ---
class DodgeApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    DodgeApp().run()