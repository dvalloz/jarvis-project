import logging
from telegram.ext import Application
from telegram.request import HTTPXRequest
from config.settings import settings
from bot.handlers import register_handlers
from bot.scheduler import start_scheduler
from database.seed import init_models, seed_data

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    logger.info("Verificando estructura de tablas e información semilla en PostgreSQL...")
    await init_models()
    await seed_data()
    logger.info("Iniciando APScheduler dentro del event loop...")
    start_scheduler(application)
    logger.info("🤖 Bot listo y escuchando mensajes de Telegram en tiempo real...")

def main():
    logger.info("Iniciando Jarvis - Telegram Personal Assistant...")
    logger.info(f"Timezone: {settings.timezone} | User ID: {settings.telegram_user_id}")

    # Configuración de petición HTTP robusta (30s) para evitar ReadTimeout / ConnectTimeout por fluctuaciones de red
    request_config = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )

    # Construir Application con post_init hook y red adaptada
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .request(request_config)
        .post_init(post_init)
        .build()
    )

    # Registrar handlers y error handler global
    register_handlers(application)

    # Start Polling con reintentos automáticos infinitos (bootstrap_retries=-1) si hay micro-cortes al conectar
    application.run_polling(bootstrap_retries=-1)

if __name__ == "__main__":
    main()
