# 🔹 Tarea 2.4 — Script de Inicialización y Sembrado (`database/seed.py`)

## 🎯 Objetivo
Construir un script independiente que cree las tablas en PostgreSQL e inserte la rotación de rutinas inicial y las tareas periódicas predeterminadas.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Crear `database/seed.py`:**
   ```python
   import asyncio
   from database.connection import engine
   from database.models import Base, Workout, RecurringTask
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select

   async def init_models():
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)

   async def seed_data():
       async with AsyncSession(engine) as session:
           # Sembrado de entrenamientos
           res = await session.execute(select(Workout))
           if not res.scalars().all():
               workouts = [
                   Workout(name="Empuje (Push)", order_index=1, target_muscles="Pecho, Hombro, Tríceps", description="Press banca, Press militar, Fondos"),
                   Workout(name="Tirón (Pull)", order_index=2, target_muscles="Espalda, Bíceps", description="Dominadas, Remo con barra, Curls"),
                   Workout(name="Pierna (Legs)", order_index=3, target_muscles="Cuádriceps, Isquios, Gemelo", description="Sentadillas, Peso muerto, Prensa"),
               ]
               session.add_all(workouts)

           # Sembrado de tareas del hogar
           res_tasks = await session.execute(select(RecurringTask))
           if not res_tasks.scalars().all():
               tasks = [
                   RecurringTask(title="Limpiar filtros del aire acondicionado", frequency_type="days", interval_value=30),
                   RecurringTask(title="Revisar presión de neumáticos del coche", frequency_type="days", interval_value=15),
                   RecurringTask(title="Hacer colada de sábanas y toallas", frequency_type="days", interval_value=7),
               ]
               session.add_all(tasks)

           await session.commit()

   async def main():
       print("Creando tablas en la base de datos...")
       await init_models()
       print("Sembrando datos iniciales...")
       await seed_data()
       print("¡Sembrado completado con éxito!")

   if __name__ == "__main__":
       asyncio.run(main())
   ```

---

## ✅ Verificación de la Tarea
- Ejecutar el script:
  ```bash
  python -m database.seed
  ```
- Confirmar que las tablas se creen en PostgreSQL y contengan los registros semilla.
