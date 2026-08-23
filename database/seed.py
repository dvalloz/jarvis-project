import asyncio
from database.connection import engine
from database.models import Base, Workout, RecurringTask
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Añadir columnas para Ruben, Victoriano, Miquel y Joan si no existen en la tabla spotify_payment_trackers
        await conn.execute(text("ALTER TABLE spotify_payment_trackers ADD COLUMN IF NOT EXISTS ruben_paid BOOLEAN DEFAULT FALSE;"))
        await conn.execute(text("ALTER TABLE spotify_payment_trackers ADD COLUMN IF NOT EXISTS victoriano_paid BOOLEAN DEFAULT FALSE;"))
        await conn.execute(text("ALTER TABLE spotify_payment_trackers ADD COLUMN IF NOT EXISTS miquel_paid BOOLEAN DEFAULT FALSE;"))
        await conn.execute(text("ALTER TABLE spotify_payment_trackers ADD COLUMN IF NOT EXISTS joan_paid BOOLEAN DEFAULT FALSE;"))

async def seed_data():
    async with AsyncSession(engine) as session:
        # Sembrado de entrenamientos personalizados de David
        res = await session.execute(select(Workout))
        existing_workouts = res.scalars().all()
        if not existing_workouts:
            workouts = [
                Workout(
                    name="Empuje (Push)",
                    order_index=1,
                    target_muscles="Pecho, Hombros, Bíceps, Tríceps",
                    description="• Bíceps\n• Press de banca en máquina\n• Press inclinado\n• Aperturas en máquina\n• Fondos"
                ),
                Workout(
                    name="Tirón (Pull)",
                    order_index=2,
                    target_muscles="Espalda, Hombros, Tríceps",
                    description="• Dominadas\n• Remo con barra\n• Jalón al pecho\n• Remo sentado\n• Press militar\n• Elevaciones laterales\n• Tríceps"
                ),
                Workout(
                    name="Pierna (Legs)",
                    order_index=3,
                    target_muscles="Cuádriceps, Isquiotibiales, Gemelos, Glúteo, Core",
                    description="• Sentadillas\n• Gemelos\n• Isquiotibiales\n• Cuádriceps\n• Aperturas y cierres para glúteo\n• Core / Abdominales"
                ),
                Workout(
                    name="Full-Body",
                    order_index=4,
                    target_muscles="Pecho, Espalda, Hombros, Brazos, Core",
                    description="• Press inclinado\n• Jalón al pecho\n• Elevaciones laterales\n• Bíceps + Tríceps\n• Core / Abdominales"
                ),
                Workout(
                    name="Cardio & Core",
                    order_index=5,
                    target_muscles="Resistencia y Abdomen",
                    description="• Carrera continua\n• Remo ergómetro\n• Planchas"
                ),
                Workout(
                    name="Escalada",
                    order_index=6,
                    target_muscles="Antebrazos, Espalda, Core",
                    description="• Sesión de búlder o vía de escalada"
                ),
            ]
            session.add_all(workouts)

        await session.commit()

async def main():
    print("Creando/actualizando tablas en la base de datos...")
    await init_models()
    print("Sembrando datos iniciales...")
    await seed_data()
    print("¡Sembrado completado con éxito!")

if __name__ == "__main__":
    asyncio.run(main())
