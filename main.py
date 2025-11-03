# main.py — OKX Perpetual (SWAP) Margin Calculator — без фильтра объёма
import ccxt
import pandas as pd
import json
import os
from datetime import datetime
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRectangleFlatButton, MDRaisedButton
from kivymd.uix.scrollview import MDScrollView
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window

Window.size = (360, 640)


class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.df = pd.DataFrame()
        self.cache_file = os.path.join(MDApp.get_running_app().user_data_dir, "cache.json")
        self.build_ui()
        self.load_cache()
        Clock.schedule_once(self.update_prices, 1)

    def build_ui(self):
        layout = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))

        from kivymd.uix.toolbar import MDTopAppBar
        toolbar = MDTopAppBar(title="OKX Margin Calculator", elevation=10)
        layout.add_widget(toolbar)

        self.update_btn = MDRectangleFlatButton(
            text="Обновить цены", icon="refresh",
            pos_hint={"center_x": 0.5}, on_release=self.update_prices
        )
        self.last_update_label = MDLabel(text="Последнее: —", halign="center", theme_text_color="Secondary")
        layout.add_widget(self.update_btn)
        layout.add_widget(self.last_update_label)

        self.symbol_field = MDTextField(
            hint_text="Пара (напр. BTC/USDT:USDT)", mode="rectangle", text="BTC/USDT:USDT"
        )
        layout.add_widget(self.symbol_field)

        self.stop_ticks = MDTextField(hint_text="Stop Loss (тики)", input_filter="float", text="55")
        self.risk_usd = MDTextField(hint_text="Риск ($)", input_filter="float", text="2")
        self.leverage = MDTextField(hint_text="Плечо (x)", input_filter="float", text="10")

        for field in [self.stop_ticks, self.risk_usd, self.leverage]:
            layout.add_widget(field)

        calc_btn = MDRaisedButton(text="РАССЧИТАТЬ", pos_hint={"center_x": 0.5}, on_release=self.calculate)
        layout.add_widget(calc_btn)

        self.result_card = MDCard(orientation="vertical", padding=dp(16), spacing=dp(8), size_hint_y=None, height=dp(180))
        self.result_card.opacity = 0
        layout.add_widget(self.result_card)

        self.top_list = MDScrollView()
        self.top_list_box = MDBoxLayout(orientation="vertical", adaptive_height=True, spacing=dp(2))
        self.top_list.add_widget(self.top_list_box)
        layout.add_widget(self.top_list)

        self.add_widget(layout)

    def update_prices(self, *args):
        self.update_btn.disabled = True
        self.update_btn.text = "Загрузка..."
        Clock.schedule_once(self._fetch_data, 0.1)

    def _fetch_data(self, dt):
        try:
            exchange = ccxt.okx({'enableRateLimit': True})
            markets = exchange.load_markets()

            # Загружаем все активные SWAP контракты с USDT
            swaps = {
                symbol: market
                for symbol, market in markets.items()
                if market.get('type') == 'swap'
                and market.get('quote') == 'USDT'
                and market.get('active')
            }

            print(f"Найдено SWAP инструментов: {len(swaps)}")

            if not swaps:
                raise ValueError("Нет SWAP пар. Проверьте интернет или VPN.")

            tickers = exchange.fetch_tickers(list(swaps.keys()))
            print(f"Загружено тикеров: {len(tickers)}")

            data = []
            for symbol, ticker in tickers.items():
                try:
                    if not symbol or not ticker or ticker.get('last') is None:
                        continue
                    market = swaps[symbol]
                    data.append({
                        'symbol': symbol,
                        'last_price': float(ticker['last']),
                        'tick_size': float(market.get('tickSize', market['precision']['price'])),
                        'contract_size': float(market.get('contractSize', 1)),
                        'min_size': float(market['limits']['amount'].get('min', 0.01))
                    })
                except Exception as e:
                    print(f"Пропущен {symbol}: {e}")

            self.df = pd.DataFrame(data)
            print(f"Успешно загружено пар: {len(self.df)}")

            self.save_cache()
            self.update_top_list()
            self.last_update_label.text = f"Последнее: {datetime.now().strftime('%H:%M:%S')}"

        except Exception as e:
            self.last_update_label.text = f"Ошибка: {str(e)[:40]}"
            print(f"Критическая ошибка: {e}")
        finally:
            self.update_btn.text = "Обновить цены"
            self.update_btn.disabled = False

    def update_top_list(self):
        self.top_list_box.clear_widgets()
        if self.df.empty:
            self.top_list_box.add_widget(MDLabel(text="Нет данных. Нажмите 'Обновить цены'."))
        else:
            for _, row in self.df.head(100).iterrows():
                item = MDRectangleFlatButton(
                    text=f"{row['symbol']} | ${row['last_price']:,.2f}",
                    size_hint_y=None, height=dp(40),
                    on_release=lambda x, s=row['symbol']: self.select_symbol(s)
                )
                self.top_list_box.add_widget(item)

    def select_symbol(self, symbol):
        self.symbol_field.text = symbol

    def calculate(self, *args):
        try:
            symbol = self.symbol_field.text.strip().upper()
            if not symbol:
                raise ValueError("Введите пару")

            if "/" not in symbol:
                symbol = f"{symbol}/USDT:USDT"

            stop_ticks = float(self.stop_ticks.text or 0)
            risk_usd = float(self.risk_usd.text or 0)
            leverage = float(self.leverage.text or 1)

            if self.df.empty:
                raise ValueError("Обновите данные и выберите пару")

            row = self.df[self.df['symbol'] == symbol]
            if row.empty:
                raise ValueError("Пара не найдена в списке")

            row = row.iloc[0]
            last_price = row['last_price']
            tick_size = row['tick_size']
            contract_size = row['contract_size']
            min_size = row['min_size']

            stop_distance = stop_ticks * tick_size
            stop_percent = stop_distance / last_price
            position_value = risk_usd / stop_percent
            margin = position_value / leverage
            contracts = position_value / (last_price * contract_size)

            self.result_card.clear_widgets()
            results = [
                f"Маржа входа: ${margin:,.2f}",
                f"Позиция: ${position_value:,.2f}",
                f"Контрактов: {contracts:.4f}",
                f"Цена: ${last_price:,.2f}",
                f"Стоп-цена: ${last_price - stop_distance:,.2f}",
                f"Мин. размер: {min_size} → {'✓' if contracts >= min_size else '✗'}"
            ]
            for text in results:
                self.result_card.add_widget(MDLabel(text=text, halign="center"))
            self.result_card.opacity = 1
            self.result_card.height = dp(200)

        except Exception as e:
            self.result_card.clear_widgets()
            self.result_card.add_widget(MDLabel(text=f"Ошибка: {str(e)}", theme_text_color="Error"))
            self.result_card.opacity = 1

    def save_cache(self):
        if not self.df.empty:
            cache = {'timestamp': datetime.now().isoformat(), 'data': self.df.to_dict('records')}
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f)

    def load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                self.df = pd.DataFrame(cache['data'])
                self.update_top_list()
                self.last_update_label.text = f"Кэш: {cache['timestamp'][11:16]}"
            except:
                pass


class OKXApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        return MainScreen()


if __name__ == "__main__":
    OKXApp().run()
