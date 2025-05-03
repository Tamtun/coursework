import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def report_to_file(filename: Optional[str] = None) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)

            if isinstance(result, pd.DataFrame):
                result = result.to_dict(orient="records")

            output_file = filename or f"report_{func.__name__}.json"

            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
                logger.info(f"Отчет сохранен в {output_file}")
            except Exception as e:
                logger.error(f"Ошибка сохранения отчета: {e}")

            return result

        return wrapper

    return decorator


@report_to_file()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    try:
        target_date = pd.to_datetime(date) if date else pd.Timestamp.now()
        start_date = target_date - pd.DateOffset(months=3)

        mask = (
            (transactions["Категория"] == category)
            & (transactions["Дата операции"] >= start_date)
            & (transactions["Дата операции"] <= target_date)
        )

        return (
            transactions[mask]
            .groupby(transactions["Дата операции"].dt.to_period("M"))["Сумма платежа"]
            .sum()
            .reset_index()
        )

    except Exception as e:
        logger.error(f"Ошибка в spending_by_category: {e}")
        return pd.DataFrame()


@report_to_file("weekday_report.json")
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    try:
        target_date = pd.to_datetime(date) if date else pd.Timestamp.now()
        start_date = target_date - pd.DateOffset(months=3)

        filtered = transactions[
            (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= target_date)
        ]

        days_translation = {
            "Monday": "Понедельник",
            "Tuesday": "Вторник",
            "Wednesday": "Среда",
            "Thursday": "Четверг",
            "Friday": "Пятница",
            "Saturday": "Суббота",
            "Sunday": "Воскресенье",
        }

        filtered["День недели"] = filtered["Дата операции"].dt.day_name().map(days_translation)

        return filtered.groupby("День недели")["Сумма платежа"].mean().reset_index()

    except Exception as e:
        logger.error(f"Ошибка в spending_by_weekday: {e}")
        return pd.DataFrame()


@report_to_file("workday_report.json")
def spending_by_workday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    try:
        target_date = pd.to_datetime(date) if date else pd.Timestamp.now()
        start_date = target_date - pd.DateOffset(months=3)

        filtered = transactions[
            (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= target_date)
        ]

        filtered["Тип дня"] = filtered["Дата операции"].dt.weekday.apply(lambda x: "Рабочий" if x < 5 else "Выходной")

        return filtered.groupby("Тип дня")["Сумма платежа"].mean().reset_index()

    except Exception as e:
        logger.error(f"Ошибка в spending_by_workday: {e}")
        return pd.DataFrame()
