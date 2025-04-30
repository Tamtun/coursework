import logging
from datetime import datetime
from typing import Any, Dict
import pandas as pd
import requests

from .utils import get_date_range, load_transactions, load_user_settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_greeting() -> str:
    """Возвращает приветствие в зависимости от времени суток."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def get_card_stats(df: pd.DataFrame) -> list:
    """Возвращает статистику по картам."""
    cards = []
    for last_digits, group in df.groupby("Номер карты"):
        total_spent = group["Сумма платежа"].sum()
        cashback = total_spent * 0.01  # 1% кешбэка
        cards.append(
            {
                "last_digits": last_digits,
                "total_spent": round(total_spent, 2),
                "cashback": round(cashback, 2),
            }
        )
    return cards


def get_top_transactions(df: pd.DataFrame, n: int = 5) -> list:
    """Возвращает топ-N транзакций по сумме."""
    return df.nlargest(n, "Сумма платежа")[["Дата операции", "Сумма платежа", "Категория", "Описание"]].to_dict(
        "records"
    )


def get_currency_rates(currencies: list) -> list:
    """Получает курсы валют через API."""
    rates = []
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        data = response.json()
        for currency in currencies:
            rates.append(
                {
                    "currency": currency,
                    "rate": round(data["rates"].get(currency, 0), 2),
                }
            )
    except Exception as e:
        logger.error(f"Ошибка при получении курсов валют: {e}")
    return rates


def main_page(date: str) -> Dict[str, Any]:
    """Главная функция для генерации JSON."""
    try:
        # Загрузка данных
        df = load_transactions()
        start_date, end_date = get_date_range(date)
        filtered_df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]

        # Загрузка настроек пользователя
        settings = load_user_settings()

        # Формирование ответа
        return {
            "greeting": get_greeting(),
            "cards": get_card_stats(filtered_df),
            "top_transactions": get_top_transactions(filtered_df),
            "currency_rates": get_currency_rates(settings["user_currencies"]),
        }
    except Exception as e:
        logger.error(f"Ошибка в main_page: {e}")
        return {"error": str(e)}
