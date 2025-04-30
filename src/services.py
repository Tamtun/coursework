import logging
import re
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


def profitable_cashback(data: pd.DataFrame, year: int, month: int) -> Dict[str, float]:
    """Анализ выгодных категорий кешбэка"""
    try:
        filtered = data[(data["Дата операции"].dt.year == year) & (data["Дата операции"].dt.month == month)]
        return filtered.groupby("Категория")["Кешбэк"].sum().to_dict()
    except Exception as e:
        logger.error(f"Ошибка в profitable_cashback: {e}")
        return {}


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """Расчет суммы для инвесткопилки"""
    try:
        total = 0.0
        target_month = datetime.strptime(month, "%Y-%m")

        for t in transactions:
            op_date = datetime.strptime(t["Дата операции"], "%Y-%m-%d")
            if op_date.month == target_month.month and op_date.year == target_month.year:
                rounded = ((t["Сумма операции"] + limit - 1) // limit) * limit
                total += rounded - t["Сумма операции"]

        return round(total, 2)
    except Exception as e:
        logger.error(f"Ошибка в investment_bank: {e}")
        return 0.0


def simple_search(data: pd.DataFrame, query: str) -> List[Dict[str, Any]]:
    """Поиск по описанию и категории"""
    try:
        query = query.lower()
        mask = data["Описание"].str.lower().str.contains(query, na=False) | data["Категория"].str.lower().str.contains(
            query, na=False
        )
        return data[mask].to_dict("records")
    except Exception as e:
        logger.error(f"Ошибка в simple_search: {e}")
        return []


def find_phone_transactions(data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Поиск по телефонным номерам"""
    try:
        pattern = r"(?:\+7|8)[\s\-()]*\d{3}[\s\-()]*\d{3}[\s\-()]*\d{2}[\s\-()]*\d{2}"
        mask = data["Описание"].str.contains(pattern, regex=True, na=False)
        return data[mask].to_dict("records")
    except Exception as e:
        logger.error(f"Ошибка в find_phone_transactions: {e}")
        return []


def find_person_transfers(data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Поиск переводов физлицам"""
    try:
        mask = (data["Категория"] == "Переводы") & data["Описание"].str.contains(
            r"\b[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.", regex=True, na=False
        )
        return data[mask].to_dict("records")
    except Exception as e:
        logger.error(f"Ошибка в find_person_transfers: {e}")
        return []
