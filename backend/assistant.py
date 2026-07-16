import os
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError 
from typing import Optional, List, Dict, Any
# Импортируем dotenv для автоматической локальной загрузки ключей из файла .env
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Извлекаем ключ
ai_key = os.getenv("GEMINI_API_KEY")

# Инициализируем клиент. Если ai_key равен None, библиотека попробует 
# взять его напрямую из переменной окружения GEMINI_API_KEY.
try:
    if ai_key:
        client = genai.Client(api_key=ai_key)
    else:
        # Попытка инициализации по умолчанию (будет искать системную переменную GEMINI_API_KEY)
        client = genai.Client()
except Exception as init_err:
    print(f"CRITICAL WARNING: Failed to initialize Gemini Client: {init_err}")
    print("Please ensure GEMINI_API_KEY is set in your environment or .env file.")
    client = None


def generate_individual_response(user_message: str, data: Optional[Dict[str, Any]] = None) -> str:
    """
    Generates tailored, concise agricultural advice.
    Includes fallback models and retry mechanisms to handle 503/429 API Overload errors.
    """
    # Если клиент не инициализировался из-за отсутствия API ключа
    if not client:
        return (
            "WindGuard AI engine configuration error: No valid API key was found on the server. "
            "Please configure GEMINI_API_KEY in your environment variables to enable smart assistance."
        )

    if not data:
        system_instruction = (
            "You are WindGuard AI, a leading agro-ecological expert in wind erosion prevention in Kazakhstan. "
            "The user has not selected any region on the map yet. Kindly ask them to draw a polygon "
            "on the map first and run the analysis so you can provide personalized recommendations."
        )
    else:
        # Extract and compute stats safely
        risk_percentage = round(data.get("risk_score", 0) * 100, 1)
        total_cells = data.get("total_cells", 0)
        hotspots = data.get("hotspots_count", 0)
        
        worst_pts = data.get("worst_cells", [])
        pts_list = []
        for pt in worst_pts[:3]:
            lat = pt.get("lat")
            lon = pt.get("lon")
            r_val = pt.get("risk") or pt.get("avg_risk") or 0
            
            # Безопасное форматирование координат на случай, если они пришли некорректными (например, None)
            if lat is not None and lon is not None:
                try:
                    pts_list.append(f"[Lat: {float(lat):.4f}, Lon: {float(lon):.4f}] ({round(r_val * 100)}%)")
                except (ValueError, TypeError):
                    pts_list.append(f"[Lat: {lat}, Lon: {lon}] ({round(r_val * 100)}%)")
        
        pts_str = ", ".join(pts_list) if pts_list else "no critical coordinates detected"

        system_instruction = f"""
You are WindGuard AI, an expert agricultural consultant specializing in wind erosion.
You are evaluating real field analytical data calculated for the user's selected polygon in Kazakhstan:
- Average Wind Erosion Risk: {risk_percentage}%
- Total Grid Cells Analyzed: {total_cells}
- Critical Hotspots Detected: {hotspots}
- Highest Risk Spots: {pts_str}

RESPONSE RULES:
1. STRICT BAN on generic disasters: Do not mention oceans, hurricanes, flooding, earthquakes, tsunamis, or wildfires. Focus exclusively on WIND EROSION in Kazakhstan.
2. Be specific to the numbers: Briefly explain what {risk_percentage}% risk means for their topsoil.
3. Provide concrete farming solutions to tackle wind blowing (e.g., No-Till, shelterbelts, retaining stubble, perennial crops).

STRICT CONCISENESS & LENGTH RULES:
- Keep the entire response extremely brief and dense (maximum 3-4 short bullet points total).
- Avoid long introductory sentences or polite conclusions.
- Total length of the response must not exceed 100-120 words.
- Provide the response in ENGLISH using clean markdown.
"""

    # Список стабильных моделей для фолбека (сначала пробуем быструю 2.5, затем стабильную 1.5)
    models_to_try = ['gemini-2.5-flash', 'gemini-1.5-flash']
    
    for model_name in models_to_try:
        for attempt in range(2):
            try:
                print(f"Attempting chat generation using {model_name} (Attempt {attempt + 1})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2, # Низкая температура гарантирует четкие, строгие факты
                    ),
                )
                print(f"Successfully generated response using {model_name}!")
                return response.text
            except APIError as e:
                # Перехватываем ошибки перегрузки серверов Google (503 / 429)
                print(f"Google API Error ({e.code}) on {model_name}: {e.message}")
                if attempt == 0:
                    time.sleep(1)  # Делаем паузу в 1 секунду перед повторной попыткой
                    continue
            except Exception as e:
                print(f"Unexpected error with {model_name}: {e}")
                break  # Ошибка критическая — выходим из цикла попыток и переключаемся на резервную модель
                
    # Запасной хардкод-ответ на случай полной недоступности облака Google
    return (
        "The AI Engine is currently experiencing extremely heavy traffic. "
        "Here is a quick tip for your region: Keep your crop residues on the soil surface "
        "and consider zero-tillage (No-Till) to secure your topsoil. Please try sending your message again in a minute!"
    )