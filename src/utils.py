import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple

import pandas as pd
import requests

logger = logging.getLogger(__name__)


def load_transactions():
    try:
        filepath = Path(__file__).parent.parent / "data" / "operations.xlsx"
        df = pd.read_excel(
            filepath,
            engine="openpyxl",
            thousands=None,  # Отключаем авто-форматирование чисел
            decimal=",",  # Указываем десятичный разделитель
        )
        # Конвертируем даты
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")
        return df
    except Exception as e:
        logger.error(f"Ошибка загрузки: {str(e)}")
        raise


def load_user_settings(filepath: str = None) -> dict:
    """Загрузка пользовательских настроек"""
    try:
        if filepath is None:
            filepath = Path(__file__).parent.parent / "data" / "user_settings.json"

        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки настроек: {e}")
        raise


def get_date_range(date_str: str) -> Tuple[str, str]:
    """Преобразует строку даты в диапазон (начало дня, конец дня)"""
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        start = date.replace(hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
        end = date.replace(hour=23, minute=59, second=59).strftime("%Y-%m-%d %H:%M:%S")
        return start, end
    except ValueError as e:
        logger.error(f"Неверный формат даты: {date_str}. Ожидается YYYY-MM-DD HH:MM:SS")
        raise


def get_greeting() -> str:
    """Возвращает приветствие по времени суток"""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def get_card_stats(df: pd.DataFrame) -> list:
    """Статистика по картам"""
    cards = []
    for last_digits, group in df.groupby("Номер карты"):
        cards.append(
            {
                "last_digits": last_digits,
                "total_spent": float(round(group["Сумма платежа"].sum(), 2)),
                "cashback": float(round(group["Сумма платежа"].sum() * 0.01, 2)),
            }
        )
    return cards


def get_top_transactions(df: pd.DataFrame, n: int = 5) -> list:
    """Топ-N транзакций по сумме"""
    top = df.nlargest(n, "Сумма платежа")[["Дата операции", "Сумма платежа", "Категория", "Описание"]].copy()
    top["Дата операции"] = top["Дата операции"].dt.strftime("%d.%m.%Y")
    return top.to_dict("records")


def get_currency_rates(currencies: list[str]) -> list[dict]:
    """Получает курсы валют через API"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD?base=RUB"
        response = requests.get(url)
        rates = response.json()["rates"]
        return [{"currency": currency, "rate": rates[currency]} for currency in currencies if currency in rates]
    except Exception as e:
        logger.error(f"Ошибка при получении курсов валют: {e}")
        return []


def get_sp500_price() -> float:
    """Получает цену S&P500 через Yahoo Finance"""
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        return response.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except Exception as e:
        logger.error(f"Ошибка при получении S&P500: {e}")
        return 0.0
