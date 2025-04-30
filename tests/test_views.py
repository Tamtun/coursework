import logging
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.utils import get_date_range, load_transactions, load_user_settings
from src.views import (
    get_card_stats,
    get_currency_rates,
    get_greeting,
    get_top_transactions,
    main_page,
)

# Настройка логирования для тестов
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Фикстура с тестовыми данными
@pytest.fixture
def sample_transactions():
    df = pd.DataFrame(
        {
            "Номер карты": ["1234", "1234", "5678"],
            "Дата операции": pd.to_datetime(
                ["01.05.2023", "15.05.2023", "20.05.2023"],
                dayfirst=True,  # Преобразуем строки в datetime
            ),
            "Сумма платежа": [100.0, 200.0, 50.0],
            "Категория": ["Еда", "Транспорт", "Еда"],
            "Описание": ["Магазин", "Такси", "Кафе"],
        }
    )
    return df


# Тесты для отдельных функций
def test_get_greeting():
    """Тестируем функцию приветствия"""
    with patch("src.views.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 10
        assert get_greeting() == "Доброе утро"

        mock_datetime.now.return_value.hour = 14
        assert get_greeting() == "Добрый день"

        mock_datetime.now.return_value.hour = 20
        assert get_greeting() == "Добрый вечер"

        mock_datetime.now.return_value.hour = 2
        assert get_greeting() == "Доброй ночи"


def test_get_card_stats(sample_transactions):
    """Тестируем статистику по картам"""
    result = get_card_stats(sample_transactions)
    assert len(result) == 2  # Две уникальные карты
    assert result[0]["last_digits"] == "1234"
    assert result[0]["total_spent"] == 300.0
    assert result[0]["cashback"] == 3.0


def test_get_top_transactions(sample_transactions):
    """Тестируем получение топ-транзакций"""
    result = get_top_transactions(sample_transactions, n=2)
    assert len(result) == 2
    assert result[0]["Сумма платежа"] == 200.0


# Тест с моком для API валют
@patch("src.views.requests.get")
def test_get_currency_rates(mock_get):
    """Тестируем получение курсов валют с моком API"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"rates": {"USD": 1.0, "EUR": 0.85, "RUB": 75.0}}
    mock_get.return_value = mock_response

    result = get_currency_rates(["EUR", "RUB"])
    assert len(result) == 2
    assert result[0]["currency"] == "EUR"
    assert result[0]["rate"] == 0.85
    assert result[1]["rate"] == 75.0


# Интеграционный тест для main_page
@patch("src.views.load_transactions")
@patch("src.views.load_user_settings")
def test_main_page(mock_settings, mock_transactions, sample_transactions):
    """Тестируем главную функцию страницы"""
    # Настраиваем моки
    mock_transactions.return_value = sample_transactions
    mock_settings.return_value = {"user_currencies": ["EUR"]}

    # Мок для API валют
    with patch("src.views.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": {"EUR": 0.85}}
        mock_get.return_value = mock_response

        result = main_page("20.05.2023 14:00:00")

        assert "greeting" in result
        assert len(result["cards"]) == 2
        assert len(result["top_transactions"]) <= 5
        assert result["currency_rates"][0]["currency"] == "EUR"
