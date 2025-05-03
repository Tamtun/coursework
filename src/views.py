import logging
from typing import Any, Dict

from .utils import (
    load_transactions,
    load_user_settings,
    get_date_range,
    get_greeting,
    get_card_stats,
    get_top_transactions,
    get_sp500_price,
)

logger = logging.getLogger(__name__)


def main_page(date: str) -> Dict[str, Any]:
    """Главная функция для генерации JSON-ответа"""
    try:
        df = load_transactions()
        start_date, end_date = get_date_range(date)
        filtered_df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]
        settings = load_user_settings()

        return {
            "greeting": get_greeting(),
            "cards": get_card_stats(filtered_df),
            "top_transactions": get_top_transactions(filtered_df),
            "currency_rates": get_currency_rates(settings["user_currencies"]),
            "sp500_price": get_sp500_price(),
        }
    except Exception as e:
        logger.error(f"Ошибка в main_page: {e}")
        return {"error": str(e)}
