from aiogram.types import LabeledPrice

from loader import settings


# Тарифы: plan_id -> (название, дни, цена в Stars)
PLANS = {
    "1m": {
        "title": "1 месяц",
        "days": 30,
        "price": settings.price_1_month,
        "description": "VPN на 30 дней",
    },
    "3m": {
        "title": "3 месяца",
        "days": 90,
        "price": settings.price_3_months,
        "description": "VPN на 90 дней (−11%)",
    },
    "6m": {
        "title": "6 месяцев",
        "days": 180,
        "price": settings.price_6_months,
        "description": "VPN на 180 дней (−22%)",
    },
    "12m": {
        "title": "12 месяцев",
        "days": 365,
        "price": settings.price_12_months,
        "description": "VPN на 365 дней (−33%)",
    },
}


def get_plan(plan_id: str) -> dict | None:
    return PLANS.get(plan_id)


def build_invoice_prices(plan_id: str) -> list[LabeledPrice]:
    plan = get_plan(plan_id)
    if not plan:
        raise ValueError(f"Unknown plan: {plan_id}")
    return [LabeledPrice(label=plan["title"], amount=plan["price"])]


def get_plan_days(plan_id: str) -> int:
    plan = get_plan(plan_id)
    if not plan:
        raise ValueError(f"Unknown plan: {plan_id}")
    return plan["days"]
