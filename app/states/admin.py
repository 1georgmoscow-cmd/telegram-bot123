from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    waiting_add_day = State()
    waiting_add_slot_date = State()
    waiting_add_slot_time = State()
    waiting_delete_slot_date = State()
    waiting_close_day = State()
    waiting_view_schedule = State()
    waiting_cancel_booking_date = State()
