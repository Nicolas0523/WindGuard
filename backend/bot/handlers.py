from datetime import datetime, timedelta
import os

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from .config import settings
from .states import Reg, Forecast
from .regions import REGIONS
from .api import analyze_region, analyze_climate, analyze_short
from assistant import generate_individual_response
from . import keyboard as kb  

user = Router()

async def send_analysis(
    message: Message,
    region_name: str,
    start_date: str,
    end_date: str,
    analyzer,
    ai_prompt: str
):
    region_info = REGIONS.get(region_name)

    if not region_info:
        await message.answer(f"Region geometry not found: {region_name}")
        return

    await message.answer("Analyzing data... ⏳")

    result = await analyzer(
        polygon=region_info["polygon"],
        start_date=start_date,
        end_date=end_date
    )

    if not result:
        await message.answer("Empty response from server.")
        return


    if result.get("error"):
        await message.answer(result["error"])
        return

    risk_score = result.get("risk_score", 0)
    hotspots = result.get("hotspots", [])

    risk_percent = risk_score * 100

    if risk_percent >= 60:
        level = "High 🔴"
    elif risk_percent >= 30:
        level = "Medium 🟡"
    else:
        level = "Low 🟢"

    text = (
        "🌪 **WindGuard Analysis**\n\n"
        f"📍 Region: {region_name}\n"
        f"📊 Average risk: {risk_percent:.2f}%\n"
        f"Risk level: {level}\n\n"
    )

    if hotspots:
        text += f"⚠️ Hotspots: {len(hotspots)}\n\n"

        for i, hotspot in enumerate(hotspots, 1):
            text += (
                f"{i}. Risk: {hotspot['avg_risk']:.2f}\n"
                f"Cells: {len(hotspot['cells'])}\n\n"
            )
    else:
        text += "✅ No hotspots found.\n"

    await message.answer(text, parse_mode="Markdown")

    ai_data = {
        "risk_score": risk_score,
        "hotspots_count": len(hotspots),
        "feature_importances": result.get("feature_importances"),
        "context": result.get("context")
    }

    recommendations = generate_individual_response(
        user_message=ai_prompt,
        data=ai_data
    )

    await message.answer(
        f"💡 **AI Recommendations**\n\n{recommendations}",
        parse_mode="Markdown"
    )

@user.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await message.answer(
        text="Hello! This is WindGuard Bot. \n"
              "You can use this bot to get information about wind conditions in your area. \n"
              "To get started, please register first.\n\nPlease enter your name!",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Reg.name)


@user.message(Reg.name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await message.answer(text="Thank you! Now, please send your phone number!",
    reply_markup=kb.get_number)
    await state.set_state(Reg.number)


@user.message(Reg.number, F.contact)
async def reg_contact(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.contact.phone_number)

    data = await state.get_data()
    await message.answer(
        text=f"Thank you for providing your contact information! You successfully registered!!!\n\nName: {data['name']}\nContact: {data['phone']} \n")
    await message.answer(text="You can now choose a region to get the latest wind forecast or check the wind forecast directly.",
    reply_markup=kb.menu)
    await state.clear()


@user.message(Reg.number)
async def reg_contact(message: Message, state: FSMContext) -> None:
    await message.answer(text="Please send your phone number using the button below.",
    reply_markup=kb.get_number)


@user.message(F.text == "Choose Region")
async def choose_region(message: Message) -> None:
    await message.answer("Please select a region:", reply_markup=kb.region)


@user.message(Command("Help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        text="This bot provides information about wind conditions in your area. \n"
              "You can choose a region to get the latest wind forecast or check the wind forecast directly. \n"
              "Use the buttons below to navigate through the bot's features.",
        reply_markup=kb.menu
    )


@user.callback_query(F.data.startswith("region_"))
async def region_callback(callback: CallbackQuery, state: FSMContext) -> None:
    region_parts = callback.data.split("_")[1:] 
    region_name_formatted = " ".join(word.capitalize() for word in region_parts)
    full_region_name = f"{region_name_formatted} Region"
    await state.update_data(region=full_region_name) 
    
    await callback.message.answer(
        f"You have selected {full_region_name}.\n\n"
        "You can now choose a date to get the wind forecast.", 
        reply_markup=kb.date
    ) 
    await callback.answer()


@user.message(F.text == "Historical wind forecast")
async def historical_wind_forecast(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    if "region" not in user_data:
        await message.answer("Please choose a region first using 'Choose Region' button.")
        return

    await message.answer(
        "Please enter the date range for analysis.\n"
        "Format: YYYY-MM-DD to YYYY-MM-DD\n"
        "Example: 2024-06-01 to 2024-08-31"
    )
    await state.set_state(Forecast.historical)


@user.message(Forecast.historical)
async def process_historical_dates(message: Message, state: FSMContext) -> None:
    try:
        text_input = message.text
        if " to " not in text_input:
            await message.answer("Incorrect format. Please use: YYYY-MM-DD to YYYY-MM-DD")
            return
            
        start_date, end_date = text_input.split(" to ")
        
        user_data = await state.get_data()
        region_name = user_data.get("region")
        
        await send_analysis(
            message,
            region_name,
            start_date,
            end_date,
            analyze_region,
            "Provide agricultural recommendations based on the historical wind analysis."
        )

        await state.clear()
    except Exception as e:
        await message.answer(f"Something went wrong: {str(e)}")


@user.message(F.text == "Climate Prediction (2050)")
async def process_climate_prediction(message: Message, state: FSMContext) -> None:
    try:
        start_date = "2044-06-01"
        end_date = "2046-08-31"
        
        user_data = await state.get_data()
        region_name = user_data.get("region")
        
        if "region" not in user_data:
            await message.answer("Please choose a region first using 'Choose Region' button.")
            return

        await send_analysis(
            message,
            region_name,
            start_date,
            end_date,
            analyze_climate,
            "Provide climate adaptation recommendations for 2050."
        )

        await state.clear()
    except Exception as e:
        await message.answer(f"Something went wrong: {str(e)}")


@user.message(F.text == "10-day Forecast")
async def process_short_forecast(message: Message, state: FSMContext) -> None:
    try:
        today = datetime.now()
        start_date = today.strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        
        user_data = await state.get_data()
        
        region_name = user_data.get("region")
        if "region" not in user_data:
            await message.answer("Please choose a region first using 'Choose Region' button.")
            return

        await send_analysis(
            message,
            region_name,
            start_date,
            end_date,
            analyze_short,
            "Provide recommendations for the next 10 days."
        )

        await state.clear()
    except Exception as e:
        await message.answer(f"Something went wrong: {str(e)}")


@user.message()
async def chat_with_assistant(message: Message, state: FSMContext):
    if await state.get_state():
        return

    await message.bot.send_chat_action(
        message.chat.id,
        action="typing"
    )

    try:
        data = await state.get_data()

        region = data.get("region")

        prompt = message.text

        if region:
            prompt = f"[User Region: {region}] {prompt}"

        answer = generate_individual_response(
            user_message=prompt,
            data=None
        )

        await message.answer(answer, parse_mode="Markdown")

    except Exception:
        await message.answer(
            "My system is overloaded. Try again later."
        )
        
@user.message(F.text == "Send document")
async def send_document(message: Message, state: FSMContext) -> None:
    try:
        user_data = await state.get_data()
        region_name = user_data.get("region")

        if not region_name:
            await message.answer("Please select a region first using 'Choose Region' button.")
            return

        pdf_path = f"reports/report_{region_name.replace(' ', '_')}.pdf" 
        if not os.path.exists(pdf_path):
            await message.answer(
                "Sorry, the report hasn't been generated yet."
            )
            return

        await message.answer("Preparing your PDF report... ⏳")
        await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_document")

        document = FSInputFile(path=pdf_path, filename=f"WindGuard_Report_{region_name}.pdf")

        await message.answer_document(
            document=document,
            caption=f"📋 Here is your detailed WindGuard report for {region_name}."
        )

    except FileNotFoundError:
        await message.answer("Sorry, the report for this region hasn't been generated yet. Please run the forecast first.")
    except Exception as e:
        await message.answer(f"Failed to send document: {str(e)}")