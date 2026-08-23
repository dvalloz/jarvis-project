from typing import Optional, Dict
from database.connection import AsyncSessionLocal
from database.crud import (
    get_smart_next_workout_routine,
    log_completed_workout,
    log_activity_by_name,
    get_monthly_workout_summary
)

async def get_next_workout_tool() -> str:
    """Wrapper de herramienta para obtener la rutina sugerida de gym para el LLM."""
    async with AsyncSessionLocal() as db:
        workout = await get_smart_next_workout_routine(db)
        if workout:
            return (
                f"ID: {workout.id}, Nombre: {workout.name}, "
                f"Músculos: {workout.target_muscles}, Ejercicios: {workout.description}"
            )
        return "No se encontraron rutinas registradas."

async def log_climbing_tool() -> str:
    """Wrapper de herramienta para registrar una sesión de escalada."""
    async with AsyncSessionLocal() as db:
        await log_activity_by_name(db, "Escalada", notes="Registrado vía agente")
        return "Sesión de Escalada registrada correctamente."

async def log_rest_day_tool() -> str:
    """Wrapper de herramienta para registrar un día de descanso de entrenamiento."""
    async with AsyncSessionLocal() as db:
        await log_activity_by_name(db, "Descanso", notes="Registrado por conversación en lenguaje natural")
        return "Día de descanso registrado en la base de datos. La rotación de tu entrenamiento se mantendrá intacta para tu próxima sesión."

async def get_monthly_workout_summary_tool(year: Optional[int] = None, month: Optional[int] = None) -> Dict:
    """Wrapper de herramienta para obtener el resumen mensual de entrenamientos."""
    async with AsyncSessionLocal() as db:
        return await get_monthly_workout_summary(db, year, month)
