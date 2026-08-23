# 🔹 Tarea 2.3 — Implementación de Operaciones CRUD (`database/crud.py`)

## 🎯 Objetivo
Desarrollar funciones asíncronas deterministas para consultar y modificar el estado de entrenamientos y tareas.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Crear `database/crud.py`:**
   ```python
   from datetime import date, datetime, timedelta
   from typing import Optional, List
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, func
   from database.models import Workout, WorkoutLog, RecurringTask, QuickReminder

   async def get_next_workout_routine(db: AsyncSession) -> Optional[Workout]:
       """Determina la rutina que toca hoy calculando la siguiente según el último registro."""
       stmt = select(WorkoutLog).order_by(WorkoutLog.completed_at.desc()).limit(1)
       result = await db.execute(stmt)
       last_log = result.scalar_one_or_none()

       if not last_log:
           first_stmt = select(Workout).order_by(Workout.order_index.asc()).limit(1)
           res = await db.execute(first_stmt)
           return res.scalar_one_or_none()

       last_workout_stmt = select(Workout).where(Workout.id == last_log.workout_id)
       res = await db.execute(last_workout_stmt)
       last_workout = res.scalar_one_or_none()

       if not last_workout:
           return None

       next_stmt = select(Workout).where(Workout.order_index > last_workout.order_index).order_index.asc().limit(1)
       res = await db.execute(select(Workout).where(Workout.order_index > last_workout.order_index).order_by(Workout.order_index.asc()).limit(1))
       next_workout = res.scalar_one_or_none()

       if not next_workout:
           first_stmt = select(Workout).order_by(Workout.order_index.asc()).limit(1)
           res = await db.execute(first_stmt)
           next_workout = res.scalar_one_or_none()

       return next_workout

   async def log_completed_workout(db: AsyncSession, workout_id: int, notes: str = "", rpe: Optional[int] = None) -> WorkoutLog:
       log = WorkoutLog(workout_id=workout_id, notes=notes, rpe=rpe, completed_at=datetime.utcnow())
       db.add(log)
       await db.commit()
       await db.refresh(log)
       return log

   async def get_due_recurring_tasks(db: AsyncSession) -> List[RecurringTask]:
       today = date.today()
       stmt = select(RecurringTask).where(RecurringTask.is_active == True)
       res = await db.execute(stmt)
       tasks = res.scalars().all()
       due_tasks = []
       for task in tasks:
           if not task.last_completed_at:
               due_tasks.append(task)
           else:
               due_date = task.last_completed_at + timedelta(days=task.interval_value)
               if due_date <= today:
                   due_tasks.append(task)
       return due_tasks

   async def mark_task_completed(db: AsyncSession, task_id: int) -> Optional[RecurringTask]:
       stmt = select(RecurringTask).where(RecurringTask.id == task_id)
       res = await db.execute(stmt)
       task = res.scalar_one_or_none()
       if task:
           task.last_completed_at = date.today()
           await db.commit()
           await db.refresh(task)
       return task
   ```

---

## ✅ Verificación de la Tarea
- Ejecutar pruebas unitarias de inserción y consulta de tareas y rutinas.
