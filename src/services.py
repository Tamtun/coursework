import logging
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Union, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def profitable_cashback(
    year: int, month: int, transactions: List[Dict[str, Union[str, float]]]
) -> Dict[str, Union[float, str]]:
    """Анализ кешбэка по категориям за указанный месяц"""
    try:
        if not transactions:
            return {"error": "Нет данных для анализа"}

        df = pd.DataFrame(transactions)

        # Проверка обязательных колонок
        required_cols = ["Дата операции", "Категория", "Кешбэк"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return {"error": f"Отсутствуют колонки: {', '.join(missing_cols)}"}

        # Обработка дат
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce")
        df = df[df["Дата операции"].notna()]

        # Фильтрация по месяцу
        filtered = df[(df["Дата операции"].dt.year == year) & (df["Дата операции"].dt.month == month)]

        if filtered.empty:
            return {"error": "Нет данных за указанный период"}

        # Расчет кешбэка
        result = filtered.groupby("Категория")["Кешбэк"].sum().round(2).sort_values(ascending=False).to_dict()

        logger.info(f"Расчет кешбэка за {month}.{year} завершен")
        return result

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}", exc_info=True)
        return {"error": str(e)}


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> Dict[str, float]:
    """
    Рассчитывает сумму для инвесткопилки через округление транзакций.

    Args:
        month: Месяц в формате 'YYYY-MM'
        transactions: Список транзакций
        limit: Лимит округления (например, 100)
    """
    try:
        if not transactions:
            return {"total": 0.0}

        target_month = datetime.strptime(month, "%Y-%m")
        total = 0.0

        for t in transactions:
            try:
                # Обработка разных форматов даты
                op_date_str = str(t["Дата операции"]).split()[0]
                op_date = datetime.strptime(op_date_str, "%Y-%m-%d")
                amount = float(t["Сумма операции"])

                if op_date.month == target_month.month and op_date.year == target_month.year and amount > 0:
                    rounded = ((amount + limit - 1) // limit) * limit
                    total += rounded - amount

            except (ValueError, KeyError, AttributeError) as e:
                logger.warning(f"Ошибка обработки транзакции: {t}. Ошибка: {str(e)}")
                continue

        result = {"total": round(total, 2)}
        logger.debug(f"Результат: {json.dumps(result, ensure_ascii=False)}")
        return result

    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}", exc_info=True)
        return {"error": str(e)}


def find_phone_transactions(transactions: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Поиск транзакций с телефонными номерами"""
    try:
        if not transactions:
            return []

        df = pd.DataFrame(transactions)

        if "Описание" not in df.columns:
            logger.warning("Колонка 'Описание' не найдена")
            return []

        phone_regex = re.compile(r"(?:\+7|8)[\s\-()]*\d{3}[\s\-()]*\d{3}[\s\-()]*\d{2}[\s\-()]*\d{2}")

        mask = df["Описание"].apply(lambda x: bool(phone_regex.search(str(x))))  # Исправлено
        return df[mask].to_dict("records")

    except Exception as e:
        logger.error(f"Ошибка поиска телефонов: {str(e)}", exc_info=True)
        return []


def find_person_transfers(transactions: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Ищет переводы физлицам по шаблону 'Фамилия И.'.
    """
    try:
        if not transactions:
            return []

        df = pd.DataFrame(transactions)

        required_cols = ["Категория", "Описание"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Отсутствуют колонки: {missing_cols}")
            return []

        name_pattern = re.compile(r"\b[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.")
        mask = (df["Категория"] == "Переводы") & (df["Описание"].apply(lambda x: bool(name_pattern.search(str(x)))))
        return df[mask].to_dict("records")

    except Exception as e:
        logger.error(f"Ошибка поиска переводов: {str(e)}", exc_info=True)
        return []


def spending_by_category(
    transactions: pd.DataFrame, category: str, date: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Анализ трат по категории с исправленной сериализацией"""
    try:
        # Парсинг дат с явным указанием формата и dayfirst=True
        transactions["Дата операции"] = pd.to_datetime(
            transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S", dayfirst=True
        )

        # Конвертация сумм
        transactions["Сумма платежа"] = transactions["Сумма платежа"].astype(str).str.replace(",", ".").astype(float)

        # Определяем период анализа
        end_date = transactions["Дата операции"].max()
        start_date = end_date - pd.DateOffset(months=3)

        # Фильтрация
        mask = (
            (transactions["Категория"].str.strip().str.lower() == category.strip().lower())
            & (transactions["Дата операции"] >= start_date)
            & (transactions["Дата операции"] <= end_date)
        )
        filtered = transactions[mask]

        # Группировка и преобразование Period в строку
        result = filtered.groupby(filtered["Дата операции"].dt.to_period("M"))["Сумма платежа"].sum().reset_index()
        result["Месяц"] = result["Дата операции"].astype(str)  # Конвертируем Period в строку
        return {
            "category": category,
            "period": f"{start_date.date()} - {end_date.date()}",
            "data": result[["Месяц", "Сумма платежа"]].to_dict("records"),
        }

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}", exc_info=True)
        return {"error": str(e)}


def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    """Средние траты по дням недели за последние 3 месяца данных"""
    try:
        transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S")

        end_date = transactions["Дата операции"].max()
        start_date = end_date - pd.DateOffset(months=3)

        filtered = transactions[
            (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= end_date)
        ]

        days_map = {
            0: "Понедельник",
            1: "Вторник",
            2: "Среда",
            3: "Четверг",
            4: "Пятница",
            5: "Суббота",
            6: "Воскресенье",
        }
        filtered["День недели"] = filtered["Дата операции"].dt.dayofweek.map(days_map)

        return filtered.groupby("День недели")["Сумма платежа"].mean().round(2).reset_index()

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}", exc_info=True)
        return pd.DataFrame(columns=["День недели", "Сумма платежа"])


def spending_by_workday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    """Траты в рабочие/выходные за последние 3 месяца данных"""
    try:
        transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S")

        end_date = transactions["Дата операции"].max()
        start_date = end_date - pd.DateOffset(months=3)

        filtered = transactions[
            (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= end_date)
        ]

        filtered["Тип дня"] = filtered["Дата операции"].dt.dayofweek.apply(
            lambda x: "Рабочий" if x < 5 else "Выходной"
        )

        return filtered.groupby("Тип дня")["Сумма платежа"].mean().round(2).reset_index()

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}", exc_info=True)
        return pd.DataFrame(columns=["Тип дня", "Сумма платежа"])
