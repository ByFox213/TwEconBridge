from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

API_TOKEN = 'YOUR_API_TOKEN'

class FormBan(StatesGroup):
    ip = State()
    nickname = State()
    time = State()
    reason = State()


def fast_button_time():
    builder = InlineKeyboardBuilder()
    return builder.attach(InlineKeyboardBuilder.from_markup(
        InlineKeyboardMarkup(inline_keyboard=
        [
            [
                InlineKeyboardButton(text="5m", callback_data="time:5"),
                InlineKeyboardButton(text="30m", callback_data="time:30")
            ],
            [
                InlineKeyboardButton(text="1h", callback_data="time:60"),
                InlineKeyboardButton(text="24h", callback_data="time:1440")
            ],
            [
                InlineKeyboardButton(text="Своё значение", callback_data="time:custom_value")
            ]
        ]
    )))


def fast_button_reason():
    builder = InlineKeyboardBuilder()
    return builder.attach(InlineKeyboardBuilder.from_markup(
        InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="krx", callback_data="reason:krx"),
                InlineKeyboardButton(text="funvote", callback_data="reason:funvote"),
            ],
            [
                InlineKeyboardButton(text="Своё значение", callback_data="reason:custom_value")
            ],
        ]
        )))

def fast_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="ban", callback_data="menu:ban")
    return builder.as_markup()


def fast_button_adm():
    builder = InlineKeyboardBuilder()
    return builder.attach(InlineKeyboardBuilder.from_markup(
        InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="ban", callback_data="menu:ban"),
                InlineKeyboardButton(text="admin panel", callback_data="menu:adm_panel"),
            ],
        ]
    )))


def fast_button_adm_panel():
    builder = InlineKeyboardBuilder()
    return builder.attach(InlineKeyboardBuilder.from_markup(InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="list moderators", callback_data="adm:list_moderators"),
                InlineKeyboardButton(text="add moderator", callback_data="adm:add_moderator"),
                InlineKeyboardButton(text="remove moderator", callback_data="adm:remove_moderator"),
            ],
        ]
    )))
