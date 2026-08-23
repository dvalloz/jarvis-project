from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, Date, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connection import Base

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

class PillLog(Base):
    __tablename__ = "pill_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    log_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    taken: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

class SpotifyPaymentTracker(Base):
    __tablename__ = "spotify_payment_trackers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    month_key: Mapped[str] = mapped_column(String(7), nullable=False, unique=True)  # YYYY-MM
    total_friends: Mapped[int] = mapped_column(Integer, default=4)
    paid_count: Mapped[int] = mapped_column(Integer, default=0)
    ruben_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    victoriano_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    miquel_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    joan_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    last_reminded_at: Mapped[Optional[date]] = mapped_column(Date)

class OfficeSchedule(Base):
    __tablename__ = "office_schedules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    schedule_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    will_attend: Mapped[bool] = mapped_column(Boolean, default=False)
    user_notified_night_before: Mapped[bool] = mapped_column(Boolean, default=False)

class DeadlineTask(Base):
    __tablename__ = "deadline_tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    last_reminded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)