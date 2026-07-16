from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Choose Region")],
        [KeyboardButton(text="Help")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Choose an option...",
)

date = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Historical wind forecast")],
        [KeyboardButton(text="Climate Prediction (2050)")],
        [KeyboardButton(text="10-day Forecast")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Choose an option...",
)


region = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Abay Region", callback_data="region_abay")],
        [InlineKeyboardButton(text="Aqmola Region", callback_data="region_aqmola")],
        [InlineKeyboardButton(text="Aqtobe Region", callback_data="region_aqtobe")],
        [InlineKeyboardButton(text="Almaty Region", callback_data="region_almaty_region")],
        [InlineKeyboardButton(text="Atyrau Region", callback_data="region_atyrau")],
        [InlineKeyboardButton(text="East Kazakhstan Region", callback_data="region_east_kazakhstan")],
        [InlineKeyboardButton(text="Jambyl Region", callback_data="region_jambyl")],
        [InlineKeyboardButton(text="Jetisu Region", callback_data="region_jetisu")],
        [InlineKeyboardButton(text="West Kazakhstan Region", callback_data="region_west_kazakhstan")],
        [InlineKeyboardButton(text="Karagandy Region", callback_data="region_karagandy")],
        [InlineKeyboardButton(text="Kostanay Region", callback_data="region_kostanay")],
        [InlineKeyboardButton(text="Kyzylorda Region", callback_data="region_kyzylorda")],
        [InlineKeyboardButton(text="Mangystau Region", callback_data="region_mangystau")],
        [InlineKeyboardButton(text="Pavlodar Region", callback_data="region_pavlodar")],
        [InlineKeyboardButton(text="North Kazakhstan Region", callback_data="region_north_kazakhstan")],
        [InlineKeyboardButton(text="Turkestan Region", callback_data="region_turkestan")],
        [InlineKeyboardButton(text="Ulytau Region", callback_data="region_ulytau")],
    ]
)

get_number = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Send my phone number", 
        request_contact=True)],
    ], 
    resize_keyboard=True
)

download_doc = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Download document", request_document=True)],
    ]
)