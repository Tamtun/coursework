import json
import logging
import os
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_transactions(filepath: str = None) -> pd.DataFrame:
    """Загрузка данных из Excel"""
    try:
        if filepath is None:
            filepath = Path(__file__).parent.parent / "data" / "operations.xlsx"

        df = pd.read_excel(filepath)

        # Преобразование дат и строк
        df["Дата операции"] = pd.to_datetime(df["Дата операции"]).dt.strftime("%Y-%m-%d")
        df["Дата платежа"] = pd.to_datetime(df["Дата платежа"]).dt.strftime("%Y-%m-%d")
        df.fillna("", inplace=True)  # Замена NaN

        return df
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        raise


def load_user_settings(filepath: str = None) -> dict:
    """Загрузка пользовательских настроек из JSON"""
    try:
        if filepath is None:
            filepath = Path(__file__).parent.parent / "data" / "user_settings.json"

        with open(filepath, encoding="utf-8") as f:
            settings = json.load(f)

        return settings
    except Exception as e:
        logger.error(f"Ошибка загрузки настроек: {e}")
        raise


def get_date_range(df: pd.DataFrame) -> tuple[str, str]:
    """Получить диапазон дат из DataFrame"""
    try:
        start_date = df["Дата операции"].min()
        end_date = df["Дата операции"].max()
        return start_date, end_date
    except Exception as e:
        logger.error(f"Ошибка при получении диапазона дат: {e}")
        raise
