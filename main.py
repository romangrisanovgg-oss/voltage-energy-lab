from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.utils import get_color_from_hex


# Цветовая палитра
BG_COLOR = get_color_from_hex("#0B1020")
PANEL_COLOR = get_color_from_hex("#141D35")
PANEL_LIGHT = get_color_from_hex("#1D2948")
TEXT_COLOR = get_color_from_hex("#F4F7FF")
MUTED_COLOR = get_color_from_hex("#9BA8C7")
CYAN = get_color_from_hex("#27E6FF")
GREEN = get_color_from_hex("#55F59A")
YELLOW = get_color_from_hex("#FFD166")
PINK = get_color_from_hex("#FF5EA8")
RED = get_color_from_hex("#FF6B6B")
DARK_BUTTON = get_color_from_hex("#243354")


def money(value: float) -> str:
    """Красивое форматирование больших чисел."""
    value = int(value)

    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"

    return str(value)


class BackgroundLayout(BoxLayout):
    """Контейнер с фоновым цветом."""

    background_color = ListProperty(BG_COLOR)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*self.background_color)
            self.background = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_background, size=self._update_background)

    def _update_background(self, *_args):
        self.background.pos = self.pos
        self.background.size = self.size


class Panel(BoxLayout):
    """Закругленная панель интерфейса."""

    panel_color = ListProperty(PANEL_COLOR)
    radius = ListProperty([dp(18)])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*self.panel_color)
            self.shape = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=self.radius,
            )

        self.bind(pos=self._update_shape, size=self._update_shape)

    def _update_shape(self, *_args):
        self.shape.pos = self.pos
        self.shape.size = self.size


class GameButton(Button):
    """Единый стиль кнопок игры."""

    button_color = ListProperty(DARK_BUTTON)
    pressed_color = ListProperty(PANEL_LIGHT)

    def __init__(self, **kwargs):
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = TEXT_COLOR
        self.font_size = sp(15)
        self.bold = True
        self.halign = "center"
        self.valign = "middle"
        self.padding = (dp(10), dp(8))

        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*self.button_color)
            self.shape = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(14)],
            )

        self.bind(pos=self._update_shape, size=self._update_shape)
        self.bind(state=self._update_color)

    def _update_shape(self, *_args):
        self.shape.pos = self.pos
        self.shape.size = self.size

    def _update_color(self, *_args):
        self.shape.rgb = (
            self.pressed_color[:3]
            if self.state == "down"
            else self.button_color[:3]
        )


class EnergyCan(Button):
    """Большая центральная кнопка-банка энергетика."""

    def __init__(self, **kwargs):
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = TEXT_COLOR
        self.font_size = sp(24)
        self.bold = True
        self.halign = "center"
        self.valign = "middle"
        self.text_size = (None, None)

        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*PINK)
            self.outer = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(32)],
            )

            Color(*CYAN)
            self.inner = RoundedRectangle(
                pos=(self.x + dp(6), self.y + dp(6)),
                size=(self.width - dp(12), self.height - dp(12)),
                radius=[dp(28)],
            )

            Color(*PANEL_COLOR)
            self.center_shape = RoundedRectangle(
                pos=(self.x + dp(13), self.y + dp(13)),
                size=(self.width - dp(26), self.height - dp(26)),
                radius=[dp(23)],
            )

        self.bind(pos=self._update_shapes, size=self._update_shapes)

    def _update_shapes(self, *_args):
        self.outer.pos = self.pos
        self.outer.size = self.size

        self.inner.pos = (self.x + dp(6), self.y + dp(6))
        self.inner.size = (self.width - dp(12), self.height - dp(12))

        self.center_shape.pos = (self.x + dp(13), self.y + dp(13))
        self.center_shape.size = (
            self.width - dp(26),
            self.height - dp(26),
        )


class StatLabel(Label):
    def __init__(self, **kwargs):
        kwargs.setdefault("color", TEXT_COLOR)
        kwargs.setdefault("font_size", sp(15))
        kwargs.setdefault("halign", "left")
        kwargs.setdefault("valign", "middle")
        super().__init__(**kwargs)


class GameScreen(Screen):
    """Основной экран кликов."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root_layout = BackgroundLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(12),
        )
        self.add_widget(self.root_layout)

        # Верхняя панель
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60),
            spacing=dp(8),
        )

        title = Label(
            text="[b]VOLTAGE[/b]\n[color=#27E6FF]ENERGY LAB[/color]",
            markup=True,
            color=TEXT_COLOR,
            font_size=sp(18),
            halign="left",
            valign="middle",
        )
        header.add_widget(title)

        menu_button = GameButton(
            text="МЕНЮ",
            size_hint_x=None,
            width=dp(90),
            button_color=PANEL_LIGHT,
        )
        menu_button.bind(on_release=self.open_menu)
        header.add_widget(menu_button)

        self.root_layout.add_widget(header)

        # Баланс
        balance_panel = Panel(
            orientation="vertical",
            size_hint_y=None,
            height=dp(95),
            padding=(dp(16), dp(10)),
        )

        self.balance_label = Label(
            text="0",
            color=YELLOW,
            font_size=sp(32),
            bold=True,
        )
        balance_panel.add_widget(self.balance_label)

        self.income_label = Label(
            text="",
            color=MUTED_COLOR,
            font_size=sp(13),
        )
        balance_panel.add_widget(self.income_label)

        self.root_layout.add_widget(balance_panel)

        # Комбо
        self.combo_label = Label(
            text="КОМБО x1.0",
            color=CYAN,
            font_size=sp(18),
            bold=True,
            size_hint_y=None,
            height=dp(32),
        )
        self.root_layout.add_widget(self.combo_label)

        # Кнопка энергетика
        self.energy_button = EnergyCan(
            text="[b]VOLT[/b]\nНАЖМИ",
            markup=True,
            size_hint_y=0.65,
        )
        self.energy_button.bind(on_release=self.click_energy)
        self.root_layout.add_widget(self.energy_button)

        hint = Label(
            text="Быстрые клики увеличивают комбо и доход",
            color=MUTED_COLOR,
            font_size=sp(12),
            size_hint_y=None,
            height=dp(25),
        )
        self.root_layout.add_widget(hint)

        # Нижняя навигация
        navigation = BoxLayout(
            size_hint_y=None,
            height=dp(58),
            spacing=dp(8),
        )

        shop_button = GameButton(
            text="ПРОКАЧКА",
            button_color=get_color_from_hex("#263C60"),
        )
        shop_button.bind(on_release=lambda *_: self.go_to("shop"))
        navigation.add_widget(shop_button)

        missions_button = GameButton(
            text="ЗАДАНИЯ",
            button_color=get_color_from_hex("#3D2E5D"),
        )
        missions_button.bind(on_release=lambda *_: self.go_to("missions"))
        navigation.add_widget(missions_button)

        self.root_layout.add_widget(navigation)

        Clock.schedule_interval(self.update_screen, 0.25)

    @property
    def game(self) -> "EnergyClickerApp":
        return App.get_running_app()

    def click_energy(self, *_args):
        self.game.perform_click()
        self.update_screen()

    def update_screen(self, *_args):
        state = self.game.state

        self.balance_label.text = f"{money(state['coins'])} КРЕДИТОВ"
        self.income_label.text = (
            f"+{money(self.game.income_per_second())}/сек  •  "
            f"+{money(self.game.click_value())} за клик"
        )

        self.combo_label.text = (
            f"КОМБО x{state['combo']:.1f}    "
            f"Серия: {state['combo_hits']}"
        )

        if state["combo"] >= 3:
            self.combo_label.color = GREEN
        else:
            self.combo_label.color = CYAN

    def open_menu(self, *_args):
        self.game.screen_manager.current = "menu"

    def go_to(self, screen_name: str):
        self.game.screen_manager.current = screen_name


class MenuScreen(Screen):
    """Экран главного меню."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BackgroundLayout(
            orientation="vertical",
            padding=dp(22),
            spacing=dp(16),
        )
        self.add_widget(layout)

        layout.add_widget(
            Label(
                text="[b]VOLTAGE[/b]\n[color=#27E6FF]ENERGY LAB[/color]",
                markup=True,
                color=TEXT_COLOR,
                font_size=sp(30),
                size_hint_y=None,
                height=dp(100),
            )
        )

        layout.add_widget(
            Label(
                text="Построй свою энергетическую империю",
                color=MUTED_COLOR,
                font_size=sp(15),
                size_hint_y=None,
                height=dp(35),
            )
        )

        start_button = GameButton(
            text="НАЧАТЬ ИГРУ",
            button_color=get_color_from_hex("#176D78"),
            size_hint_y=None,
            height=dp(64),
        )
        start_button.bind(on_release=lambda *_: self.go_to("game"))
        layout.add_widget(start_button)

        shop_button = GameButton(
            text="ПРОКАЧКА",
            size_hint_y=None,
            height=dp(56),
        )
        shop_button.bind(on_release=lambda *_: self.go_to("shop"))
        layout.add_widget(shop_button)

        missions_button = GameButton(
            text="ЗАДАНИЯ",
            size_hint_y=None,
            height=dp(56),
        )
        missions_button.bind(on_release=lambda *_: self.go_to("missions"))
        layout.add_widget(missions_button)

        layout.add_widget(Label())

        reset_button = GameButton(
            text="СБРОСИТЬ ПРОГРЕСС",
            button_color=get_color_from_hex("#572A40"),
            size_hint_y=None,
            height=dp(48),
        )
        reset_button.bind(on_release=self.reset_progress)
        layout.add_widget(reset_button)

    def go_to(self, screen_name: str):
        App.get_running_app().screen_manager.current = screen_name

    def reset_progress(self, *_args):
        app = App.get_running_app()
        app.reset_game()
        self.go_to("game")


class ShopScreen(Screen):
    """Экран улучшений."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BackgroundLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(12),
        )
        self.add_widget(self.layout)

        header = BoxLayout(
            size_hint_y=None,
            height=dp(54),
            spacing=dp(8),
        )

        header.add_widget(
            Label(
                text="[b]ЛАБОРАТОРИЯ[/b]",
                markup=True,
                color=TEXT_COLOR,
                font_size=sp(22),
            )
        )

        back_button = GameButton(
            text="НАЗАД",
            size_hint_x=None,
            width=dp(90),
        )
        back_button.bind(on_release=lambda *_: self.go_to("game"))
        header.add_widget(back_button)

        self.layout.add_widget(header)

        self.coins_label = Label(
            text="",
            color=YELLOW,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(35),
        )
        self.layout.add_widget(self.coins_label)

        self.upgrades_grid = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None,
        )
        self.upgrades_grid.bind(minimum_height=self.upgrades_grid.setter("height"))

        self.layout.add_widget(self.upgrades_grid)

        self.status_label = Label(
            text="",
            color=GREEN,
            font_size=sp(13),
            size_hint_y=None,
            height=dp(32),
        )
        self.layout.add_widget(self.status_label)

        Clock.schedule_interval(self.update_screen, 0.3)

    @property
    def game(self) -> "EnergyClickerApp":
        return App.get_running_app()

    def on_pre_enter(self, *_args):
        self.render_upgrades()

    def render_upgrades(self):
        self.upgrades_grid.clear_widgets()

        upgrades = [
            (
                "⚡ ЯДРО МОЩНОСТИ",
                "Увеличивает прибыль от каждого клика",
                "click_power",
                self.game.click_upgrade_cost(),
            ),
            (
                "✦ КРИТИЧЕСКИЙ ИМПУЛЬС",
                "Повышает шанс мощного критического клика",
                "critical",
                self.game.critical_upgrade_cost(),
            ),
            (
                "× МНОЖИТЕЛЬ VOLT",
                "Увеличивает общий доход",
                "multiplier",
                self.game.multiplier_upgrade_cost(),
            ),
            (
                "🏭 МИНИ-ЗАВОД",
                "Добавляет автоматический доход каждую секунду",
                "factory",
                self.game.factory_upgrade_cost(),
            ),
        ]

        for title, description, key, cost in upgrades:
            card = Panel(
                orientation="horizontal",
                padding=dp(12),
                spacing=dp(8),
                size_hint_y=None,
                height=dp(90),
                panel_color=PANEL_COLOR,
            )

            info = BoxLayout(
                orientation="vertical",
                spacing=dp(2),
            )

            level = self.game.state["upgrades"][key]

            info.add_widget(
                Label(
                    text=f"[b]{title}[/b]  ур. {level}",
                    markup=True,
                    color=TEXT_COLOR,
                    font_size=sp(14),
                    halign="left",
                    text_size=(None, None),
                )
            )

            info.add_widget(
                Label(
                    text=description,
                    color=MUTED_COLOR,
                    font_size=sp(11),
                    halign="left",
                )
            )

            card.add_widget(info)

            buy_button = GameButton(
                text=f"КУПИТЬ\n{money(cost)}",
                size_hint_x=None,
                width=dp(105),
                button_color=get_color_from_hex("#244C62"),
            )
            buy_button.bind(
                on_release=lambda *_args, upgrade=key: self.buy_upgrade(upgrade)
            )
            card.add_widget(buy_button)

            self.upgrades_grid.add_widget(card)

    def buy_upgrade(self, upgrade: str):
        if self.game.buy_upgrade(upgrade):
            self.status_label.text = "Улучшение установлено!"
            self.status_label.color = GREEN
        else:
            self.status_label.text = "Недостаточно кредитов"
            self.status_label.color = RED

        self.render_upgrades()
        self.update_screen()

    def update_screen(self, *_args):
        self.coins_label.text = f"Баланс: {money(self.game.state['coins'])} кредитов"

    def go_to(self, screen_name: str):
        self.game.screen_manager.current = screen_name


class MissionsScreen(Screen):
    """Экран заданий и достижений."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BackgroundLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(12),
        )
        self.add_widget(self.layout)

        header = BoxLayout(
            size_hint_y=None,
            height=dp(54),
        )

        header.add_widget(
            Label(
                text="[b]ЗАДАНИЯ[/b]",
                markup=True,
                color=TEXT_COLOR,
                font_size=sp(22),
            )
        )

        back_button = GameButton(
            text="НАЗАД",
            size_hint_x=None,
            width=dp(90),
        )
        back_button.bind(on_release=lambda *_: self.go_to("game"))
        header.add_widget(back_button)

        self.layout.add_widget(header)

        self.missions_box = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
        )
        self.layout.add_widget(self.missions_box)

        self.reward_label = Label(
            text="",
            color=GREEN,
            font_size=sp(13),
            size_hint_y=None,
            height=dp(32),
        )
        self.layout.add_widget(self.reward_label)

        Clock.schedule_interval(self.update_screen, 0.4)

    @property
    def game(self) -> "EnergyClickerApp":
        return App.get_running_app()

    def on_pre_enter(self, *_args):
        self.render_missions()

    def render_missions(self):
        self.missions_box.clear_widgets()

        missions = [
            (
                "ПЕРВЫЙ ЗАРЯД",
                "Сделать 10 кликов",
                self.game.state["total_clicks"],
                10,
                100,
                "clicks",
            ),
            (
                "ЭНЕРГЕТИЧЕСКИЙ БУМ",
                "Накопить 1 000 кредитов",
                self.game.state["total_earned"],
                1000,
                300,
                "earned",
            ),
            (
                "ПРОМЫШЛЕННИК",
                "Купить 3 улучшения",
                self.game.state["total_upgrades"],
                3,
                500,
                "upgrades",
            ),
        ]

        for title, description, progress, target, reward, mission_key in missions:
            completed = self.game.state["missions"].get(mission_key, False)

            if completed:
                status = "ПОЛУЧЕНО"
                color = GREEN
            elif progress >= target:
                status = f"ЗАБРАТЬ +{reward}"
                color = YELLOW
            else:
                status = f"{min(progress, target)}/{target}"
                color = MUTED_COLOR

            card = Panel(
                orientation="horizontal",
                padding=dp(12),
                spacing=dp(8),
                size_hint_y=None,
                height=dp(78),
            )

            text_box = BoxLayout(orientation="vertical")

            text_box.add_widget(
                Label(
                    text=f"[b]{title}[/b]",
                    markup=True,
                    color=TEXT_COLOR,
                    font_size=sp(14),
                    halign="left",
                )
            )

            text_box.add_widget(
                Label(
                    text=description,
                    color=MUTED_COLOR,
                    font_size=sp(11),
                    halign="left",
                )
            )

            card.add_widget(text_box)

            action = GameButton(
                text=status,
                color=color,
                size_hint_x=None,
                width=dp(110),
                button_color=get_color_from_hex("#283552"),
            )

            action.bind(
                on_release=lambda *_args,
                key=mission_key,
                target=target,
                reward=reward: self.claim_mission(key, target, reward)
            )

            card.add_widget(action)
            self.missions_box.add_widget(card)

    def claim_mission(self, key: str, target: int, reward: int):
        if self.game.claim_mission(key, target, reward):
            self.reward_label.text = f"Награда получена: +{reward} кредитов"
            self.reward_label.color = GREEN
            self.render_missions()
        else:
            self.reward_label.text = "Задание пока не выполнено"
            self.reward_label.color = RED

    def update_screen(self, *_args):
        pass

    def go_to(self, screen_name: str):
        self.game.screen_manager.current = screen_name


class EnergyClickerApp(App):
    """Главный объект приложения и игровая логика."""

    title = "Voltage Energy Lab"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.save_path = Path(self.user_data_dir) / "save.json"
        self.state = self.default_state()
        self.last_update = time.time()

    @staticmethod
    def default_state() -> dict[str, Any]:
        return {
            "coins": 0.0,
            "total_earned": 0.0,
            "total_clicks": 0,
            "total_upgrades": 0,
            "combo": 1.0,
            "combo_hits": 0,
            "last_save": time.time(),
            "upgrades": {
                "click_power": 0,
                "critical": 0,
                "multiplier": 0,
                "factory": 0,
            },
            "missions": {
                "clicks": False,
                "earned": False,
                "upgrades": False,
            },
        }

    def build(self):
        if not self.load_game():
            self.state = self.default_state()

        self.apply_offline_income()

        self.screen_manager = ScreenManager(
            transition=FadeTransition(duration=0.15)
        )
        self.screen_manager.add_widget(MenuScreen(name="menu"))
        self.screen_manager.add_widget(GameScreen(name="game"))
        self.screen_manager.add_widget(ShopScreen(name="shop"))
        self.screen_manager.add_widget(MissionsScreen(name="missions"))

        self.screen_manager.current = "menu"

        Clock.schedule_interval(self.game_tick, 1.0)
        Clock.schedule_interval(self.auto_save, 10.0)

        return self.screen_manager

    # ---------- Игровая математика ----------

    def click_value(self) -> int:
        upgrades = self.state["upgrades"]

        base = 1 + upgrades["click_power"] * 2
        multiplier = 1 + upgrades["multiplier"] * 0.15

        return max(1, int(base * multiplier * self.state["combo"]))

    def income_per_second(self) -> int:
        upgrades = self.state["upgrades"]

        factory_income = upgrades["factory"] * 2
        multiplier = 1 + upgrades["multiplier"] * 0.15

        return max(0, int(factory_income * multiplier))

    def critical_chance(self) -> float:
        return min(0.5, self.state["upgrades"]["critical"] * 0.05)

    def perform_click(self):
        import random

        upgrades = self.state["upgrades"]

        # Комбо постепенно растет до x5
        self.state["combo_hits"] += 1
        self.state["combo"] = min(
            5.0,
            1.0 + self.state["combo_hits"] * 0.05,
        )

        reward = self.click_value()

        # Критический клик
        if random.random() < self.critical_chance():
            reward *= 5

        self.state["coins"] += reward
        self.state["total_earned"] += reward
        self.state["total_clicks"] += 1

        # Небольшой шанс восстановить серию
        if upgrades["critical"] > 0 and random.random() < 0.15:
            self.state["combo"] = min(5.0, self.state["combo"] + 0.2)

        self.check_missions()
        self.save_game()

    def game_tick(self, _dt):
        passive = self.income_per_second()

        if passive > 0:
            self.state["coins"] += passive
            self.state["total_earned"] += passive

        # Комбо уменьшается со временем
        self.state["combo_hits"] = max(0, self.state["combo_hits"] - 1)
        self.state["combo"] = max(
            1.0,
            1.0 + self.state["combo_hits"] * 0.05,
        )

        self.check_missions()

    # ---------- Стоимость улучшений ----------

    def click_upgrade_cost(self) -> int:
        level = self.state["upgrades"]["click_power"]
        return int(25 * (1.65**level))

    def critical_upgrade_cost(self) -> int:
        level = self.state["upgrades"]["critical"]
        return int(100 * (1.85**level))

    def multiplier_upgrade_cost(self) -> int:
        level = self.state["upgrades"]["multiplier"]
        return int(250 * (2.0**level))

    def factory_upgrade_cost(self) -> int:
        level = self.state["upgrades"]["factory"]
        return int(150 * (1.8**level))

    def buy_upgrade(self, upgrade: str) -> bool:
        cost_functions = {
            "click_power": self.click_upgrade_cost,
            "critical": self.critical_upgrade_cost,
            "multiplier": self.multiplier_upgrade_cost,
            "factory": self.factory_upgrade_cost,
        }

        if upgrade not in cost_functions:
            return False

        cost = cost_functions[upgrade]()

        if self.state["coins"] < cost:
            return False

        self.state["coins"] -= cost
        self.state["upgrades"][upgrade] += 1
        self.state["total_upgrades"] += 1

        self.check_missions()
        self.save_game()

        return True

    # ---------- Задания ----------

    def check_missions(self):
        missions = self.state["missions"]

        if self.state["total_clicks"] >= 10:
            missions.setdefault("clicks_ready", True)

        if self.state["total_earned"] >= 1000:
            missions.setdefault("earned_ready", True)

        if self.state["total_upgrades"] >= 3:
            missions.setdefault("upgrades_ready", True)

    def claim_mission(self, key: str, target: int, reward: int) -> bool:
        if self.state["missions"].get(key, False):
            return False

        current_value = {
            "clicks": self.state["total_clicks"],
            "earned": self.state["total_earned"],
            "upgrades": self.state["total_upgrades"],
        }[key]

        if current_value < target:
            return False

        self.state["missions"][key] = True
        self.state["coins"] += reward
        self.state["total_earned"] += reward
        self.save_game()

        return True

    # ---------- Сохранение ----------

    def save_game(self):
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            self.state["last_save"] = time.time()
            self.save_path.write_text(
                json.dumps(self.state, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def load_game(self) -> bool:
        try:
            if not self.save_path.exists():
                return False

            loaded = json.loads(
                self.save_path.read_text(encoding="utf-8")
            )

            default = self.default_state()
            default.update(loaded)

            if "upgrades" not in default:
                default["upgrades"] = self.default_state()["upgrades"]

            if "missions" not in default:
                default["missions"] = self.default_state()["missions"]

            self.state = default
            return True

        except (OSError, json.JSONDecodeError, TypeError):
            return False

    def apply_offline_income(self):
        """
        Начисляет доход максимум за 8 часов отсутствия.
        """
        previous_time = self.state.get("last_save", time.time())
        elapsed = max(0, time.time() - previous_time)

        # Ограничиваем офлайн-доход 8 часами.
        elapsed = min(elapsed, 8 * 60 * 60)

        offline_reward = int(self.income_per_second() * elapsed)

        if offline_reward > 0:
            self.state["coins"] += offline_reward
            self.state["total_earned"] += offline_reward

    def auto_save(self, _dt):
        self.save_game()

    def reset_game(self):
        self.state = self.default_state()
        self.save_game()


if __name__ == "__main__":
    # Размер окна применяется только при запуске на компьютере.
    if "android" not in __import__("sys").platform:
        Window.size = (420, 800)

    EnergyClickerApp().run()