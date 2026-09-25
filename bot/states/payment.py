from aiogram.fsm.state import State, StatesGroup


class PaymentStates(StatesGroup):
    choosing_plan = State()
    waiting_payment = State()
