from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class Reg(StatesGroup):
    name = State()
    number = State()

class Forecast(StatesGroup):
    historical = State()

class Climate(StatesGroup):
    climate = State()

class Short(StatesGroup):
    short = State()