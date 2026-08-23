# 🔹 Tarea 2.1 — Definición de Esquemas ORM (`database/models.py`)

## 🎯 Objetivo
Definir la estructura relacional de la base de datos utilizando SQLAlchemy 2.0 con soporte asíncrono.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Crear `database/models.py`:**
   ```python
   from datetime import datetime, date
   from typing import Optional, List
   from sqlalchemy import String, Integer, DateTime, Date, Boolean, ForeignKey, Text
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

   class Base(DeclarativeBase):
       pass

   class Workout(Base):
       __tablename__ = "workouts"
       id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
       name: Mapped[str] = mapped_column(String(100), nullable=False)
       order_index: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
       target_muscles: Mapped[Optional[str]] = mapped_column(String(255))
       description: Mapped[Optional[str]] = mapped_column(Text)

       logs: Mapped[List["WorkoutLog"]] = relationship("WorkoutLog", back_populates="workout")

   class WorkoutLog(Base):
       __tablename__ = "workout_logs"
       id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
       workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"), nullable=False)
       completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       notes: Mapped[Optional[str]] = mapped_column(Text)
       rpe: Mapped[Optional[int]] = mapped_column(Integer)

       workout: Mapped["Workout"] = relationship("Workout", back_populates="logs")

   class RecurringTask(Base):
       __tablename__ = "recurring_tasks"
       id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
       title: Mapped[str] = mapped_column(String(200), nullable=False)
       frequency_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "days", "weekly", "monthly"
       interval_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
       last_completed_at: Mapped[Optional[date]] = mapped_column(Date)
       is_active: Mapped[bool] = mapped_column(Boolean, default=True)

   class QuickReminder(Base):
       __tablename__ = "quick_reminders"
       id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
       text: Mapped[str] = mapped_column(String(255), nullable=False)
       due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
       is_done: Mapped[bool] = mapped_column(Boolean, default=False)
   ```

---

## ✅ Verificación de la Tarea
- Importar `Base` y las clases en una consola de Python sin errores de sintaxis o de mapeo de SQLAlchemy.
