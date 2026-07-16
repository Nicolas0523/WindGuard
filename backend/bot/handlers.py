from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

import keyboard as kb
from config import settings
from states import Reg, Forecast
from regions import REGIONS
from api import analyze_region, analyze_climate, analyze_short
from assistant import generate_individual_response


user = Router()


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
        
        region_info = REGIONS.get(region_name)

        if not region_info:
            await message.answer(f"Region geometry not found for: {region_name}")
            return

        await message.answer("Analyzing data via WindGuard API... Please wait. ⏳")

        result = analyze_region(
            polygon=region_info["polygon"], 
            start_date=start_date.strip(),
            end_date=end_date.strip()
        )
        
        if "error" in result:
            await message.answer(f"API Error: {result['error']}")
            return

        risk_score = result.get('risk_score', 0)
        response_text = f"🌪 **WindGuard Analysis**\n\n"
        response_text += f"📍 Region: {region_name}\n" 
        

        risk_percent = risk_score * 100
        if risk_score > 0.6:
            response_text += f"📊 Average risk: {risk_percent:.2f}%\n\nRisk level: High 🔴\n\n"
        elif risk_score > 0.3:
            response_text += f"📊 Average risk: {risk_percent:.2f}%\n\nRisk level: Medium 🟡\n\n"
        else:
            response_text += f"📊 Average risk: {risk_percent:.2f}%\n\nRisk level: Low 🟢\n\n"

        hotspots = result.get("hotspots", [])
        if hotspots:
            response_text += f"⚠️ **Hotspots found ({len(hotspots)}):**\n\n"
            for i, hotspot in enumerate(hotspots, start=1):
                response_text += (
                    f"{i}. Risk Score: {hotspot['avg_risk']:.2f}\n"
                    f"   Affected Cells: {len(hotspot['cells'])}\n\n"
                )
        else:
            response_text += "✅ No critical hotspots found in this area.\n\n"

        await message.answer(response_text)

        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        ai_data = {
            "risk_score": risk_score,
            "total_cells": result.get("total_cells", 100), 
            "hotspots_count": len(hotspots),
            "worst_cells": result.get("worst_cells", [])
        }
        
        ai_recommendations = generate_individual_response(
            user_message="Provide recommendations based on this analysis.",
            data=ai_data
        )
        
        await message.answer(f"💡 **AI Agro-Consultant Recommendations:**\n\n{ai_recommendations}", parse_mode="Markdown")


        await state.set_state(None) 

    except Exception as e:
        await message.answer(f"Something went wrong: {str(e)}")


@user.message(F.text == "Climate Prediction (2050)")
async def process_climate_prediction(message: Message, state: FSMContext) -> None:
    try:
        start_date = "2044-06-01"
        end_date = "2046-08-31"
        
        user_data = await state.get_data()
        region_name = user_data.get("region")
        
        region_info = REGIONS.get(region_name)

        if not region_info:
            await message.answer(f"Region geometry not found for: {region_name}")
            return

        await message.answer("Analyzing data via WindGuard API... Please wait. ⏳")

        result = analyze_climate(
            polygon=region_info["polygon"], 
            start_date=start_date.strip(),
            end_date=end_date.strip()
        )
        
        if "error" in result:
            await message.answer(f"API Error: {result['error']}")
            return

        risk_score = result.get('risk_score', 0)
        response_text = f"🌪 **WindGuard Analysis**\n\n"
        response_text += f"📍 Region: {region_name}\n" 
        
        risk_percent = risk_score * 100
        if risk_score > 0.6:
            response_text += f"📊 Average risk: {risk_percent:.2f}%\n\nRisk level: High 🔴\n\nScenario: Worst SSP-8.5 case\n\n"
        elif risk_score > 0.3:
            response_text += f"📊 Average risk: {risk_percent:.2f}%\n\nRisk level: Medium 🟡\n\nScenario: Average SSP-8.5 case\n\n"
        else:
            response_text += f"📊 Average risk: {risk_percent:.2f}%\n\nRisk level: Low 🟢\n\nScenario: Best SSP-8.5 case\n\n"

        hotspots = result.get("hotspots", [])
        if hotspots:
            response_text += f"⚠️ **Hotspots found ({len(hotspots)}):**\n\n"
            for i, hotspot in enumerate(hotspots, start=1):
                response_text += (
                    f"{i}. Risk Score: {hotspot['avg_risk']:.2f}\n"
                    f"   Affected Cells: {len(hotspot['cells'])}\n\n"
                )
        else:
            response_text += "✅ No critical hotspots found in this area.\n\n"

        await message.answer(response_text)

        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        ai_data = {
            "risk_score": risk_score,
            "total_cells": result.get("total_cells", 100),
            "hotspots_count": len(hotspots),
            "worst_cells": result.get("worst_cells", [])
        }
        
        ai_recommendations = generate_individual_response(
            user_message="Explain what these long-term climate predictions mean for my field and how to prepare.",
            data=ai_data
        )
        
        await message.answer(f"💡 **AI Climate Risk Mitigation advice:**\n\n{ai_recommendations}", parse_mode="Markdown")

        await state.set_state(None) 

    except Exception as e:
        await message.answer(f"Something went wrong: {str(e)}")


@user.message(F.text == "10-day Forecast")
async def process_short_forecast(message: Message, state: FSMContext) -> None:
    try:
        today = datetime.now()
        forecast_from = today.strftime("%Y-%m-%d")
        forecast_to = (today + timedelta(days=10)).strftime("%Y-%m-%d")
        
        user_data = await state.get_data()
        region_name = user_data.get("region")
        
        region_info = REGIONS.get(region_name)

        if not region_info:
            await message.answer(f"Region geometry not found for: {region_name}")
            return

        await message.answer("Analyzing data via WindGuard API... Please wait. ⏳")

        result = analyze_short(
            polygon=region_info["polygon"], 
            start_date=forecast_from.strip(),
            end_date=forecast_to.strip()
        )
        
        if "error" in result:
            await message.answer(f"API Error: {result['error']}")
            return

        risk_score = result.get('risk_score', 0)
        response_text = f"🌪 **WindGuard Analysis**\n\n"
        response_text += f"📍 Region: {region_name}\n" 
        
        risk_percent = risk_score * 100
        if risk_score > 0.6:
            response_text += f"📊 Average risk: {risk_percent:.2f}%\n\nRisk level: High 🔴\n\n"
        elif risk_score > 0.3:
            response_text += f"📊 Average risk: {risk_percent:.2f}%\n\nRisk level: Medium 🟡\n\n"
        else:
            response_text += f"📊 Average risk: {risk_percent:.2f}%\n\nRisk level: Low 🟢\n\n"

        hotspots = result.get("hotspots", [])
        if hotspots:
            response_text += f"⚠️ **Hotspots found ({len(hotspots)}):**\n\n"
            for i, hotspot in enumerate(hotspots, start=1):
                response_text += (
                    f"{i}. Risk Score: {hotspot['avg_risk']:.2f}\n"
                    f"   Affected Cells: {len(hotspot['cells'])}\n\n"
                )
        else:
            response_text += "✅ No critical hotspots found in this area.\n\n"

        await message.answer(response_text)

        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        ai_data = {
            "risk_score": risk_score,
            "total_cells": result.get("total_cells", 100),
            "hotspots_count": len(hotspots),
            "worst_cells": result.get("worst_cells", [])
        }
        
        ai_recommendations = generate_individual_response(
            user_message="What are the immediate actions for the next 10 days?",
            data=ai_data
        )
        
        await message.answer(f"💡 **AI Agro-Consultant Recommendations:**\n\n{ai_recommendations}", parse_mode="Markdown")


        await state.set_state(None) 

    except Exception as e:
        await message.answer(f"Something went wrong: {str(e)}")


@user.message(F.text == "Send document")
async def send_document(message: Message) -> None:
    await message.answer("Download the document by clicking the button below.", reply_markup=kb.download_doc)


@user.message()
async def chat_with_assistant(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is not None:
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        user_data = await state.get_data()
        region_name = user_data.get("region", None)
        
        prompt = message.text
        if region_name:
            prompt = f"[User Region: {region_name}] {message.text}"

        ai_response = generate_individual_response(user_message=prompt, data=None)
        
        await message.answer(ai_response, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Error in Gemini chat: {e}")
        await message.answer("My system is slightly overloaded. Please rephrase your question or try again in a moment!")