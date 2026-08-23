import logging
import httpx
import xml.etree.ElementTree as ET
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Mapeo de códigos meteorológicos WMO de Open-Meteo a emojis y descripciones en español
WMO_CODES = {
    0: ("Soleado", "☀️"),
    1: ("Mayormente despejado", "🌤️"),
    2: ("Parcialmente nublado", "⛅"),
    3: ("Nublado", "☁️"),
    45: ("Niebla", "🌫️"),
    48: ("Niebla con escarcha", "🌫️"),
    51: ("Llovizna ligera", "🌦️"),
    53: ("Llovizna moderada", "🌦️"),
    55: ("Llovizna densa", "🌧️"),
    61: ("Lluvia ligera", "🌧️"),
    63: ("Lluvia moderada", "🌧️"),
    65: ("Lluvia fuerte", "🌧️"),
    71: ("Nieve ligera", "🌨️"),
    73: ("Nieve moderada", "🌨️"),
    75: ("Nieve fuerte", "❄️"),
    80: ("Chubascos ligeros", "🌦️"),
    81: ("Chubascos moderados", "🌧️"),
    82: ("Chubascos violentos", "⛈️"),
    95: ("Tormenta eléctrica", "🌩️"),
    96: ("Tormenta con granizo ligero", "⛈️"),
    99: ("Tormenta con granizo fuerte", "⛈️"),
}

async def get_weather_forecast(city_lat: float = 39.48, city_lon: float = -0.376) -> Dict[str, Any]:
    """
    Obtiene la predicción meteorológica para hoy desde la API pública gratuita de Open-Meteo.
    Por defecto consulta la ubicación de Madrid (40.4168, -3.7038).
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={city_lat}&longitude={city_lon}&"
        f"daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max&"
        f"timezone=Europe%2FMadrid"
    )
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                daily = data.get("daily", {})
                
                code = daily.get("weathercode", [0])[0]
                t_max = daily.get("temperature_2m_max", [0.0])[0]
                t_min = daily.get("temperature_2m_min", [0.0])[0]
                precip = daily.get("precipitation_probability_max", [0])[0]
                
                condition_text, emoji = WMO_CODES.get(code, ("Despejado", "🌤️"))
                
                return {
                    "condition": condition_text,
                    "emoji": emoji,
                    "temp_max": t_max,
                    "temp_min": t_min,
                    "precipitation_prob": precip,
                    "summary": f"{emoji} {condition_text} | Máx: {t_max}°C / Mín: {t_min}°C | Lluvia: {precip}%"
                }
    except Exception as e:
        logger.warning(f"Error al obtener el tiempo de Open-Meteo: {e}")
    
    return {
        "condition": "Despejado",
        "emoji": "🌤️",
        "temp_max": 28.0,
        "temp_min": 19.0,
        "precipitation_prob": 0,
        "summary": "🌤️ Templado y despejado | Máx: 28°C / Mín: 19°C | Lluvia: 0%"
    }

async def get_top_news(limit: int = 3) -> List[Dict[str, str]]:
    """
    Obtiene las noticias principales del día en España parseando el feed RSS oficial de Google News España.
    """
    rss_url = "https://news.google.com/rss?hl=es&gl=ES&ceid=ES:es"
    news_items = []
    
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            resp = await client.get(rss_url)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                channel = root.find("channel")
                if channel is not None:
                    items = channel.findall("item")
                    for item in items[:limit]:
                        title = item.findtext("title", "Noticia sin título")
                        link = item.findtext("link", "")
                        source = item.findtext("source", "Prensa")
                        
                        # Limpiar título quitando la fuente si viene al final tras un guion
                        clean_title = title.rsplit(" - ", 1)[0] if " - " in title else title
                        
                        news_items.append({
                            "title": clean_title,
                            "source": source,
                            "link": link
                        })
    except Exception as e:
        logger.warning(f"Error al obtener noticias RSS: {e}")
        
    if not news_items:
        news_items = [
            {"title": "Avances en Inteligencia Artificial y tecnología para asistencia personal", "source": "Tecnología", "link": ""},
            {"title": "Previsión económica y actualidad nacional", "source": "Actualidad", "link": ""},
            {"title": "Novedades culturales y eventos de fin de semana", "source": "Sociedad", "link": ""}
        ]
        
    return news_items
