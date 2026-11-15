from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from database.models import (
    Workout, WorkoutLog, RecurringTask, QuickReminder,
    PillLog, SpotifyPaymentTracker, OfficeSchedule, DeadlineTask
)

# ---------------------------------------------------------
# WORKOUT CRUD & SMART ROTATION LOGIC
# ---------------------------------------------------------

async def get_smart_next_workout_routine(db: AsyncSession) -> Optional[Workout]:
    """
    Calcula la rutina de entrenamiento recomendada teniendo en cuenta:
    1. Si en la semana actual (Lunes a Domingo) ya completó Push, Pull y Pierna -> sugiere Full-Body o Cardio.
    2. Si el último entrenamiento físico fue Escalada -> NO sugerir Pull.
    3. Los días de descanso se ignoran al calcular la rotación para no alterar el orden Push -> Pull -> Pierna.
    """
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Lunes de esta semana
    start_of_week_dt = datetime.combine(start_of_week, datetime.min.time())

    # 1. Obtener todos los logs de esta semana (excluyendo Descanso)
    week_logs_stmt = (
        select(WorkoutLog, Workout)
        .join(Workout, WorkoutLog.workout_id == Workout.id)
        .where(and_(
            WorkoutLog.completed_at >= start_of_week_dt,
            ~func.lower(Workout.name).contains("descanso")
        ))
        .order_by(WorkoutLog.completed_at.desc())
    )
    res_week = await db.execute(week_logs_stmt)
    week_entries = res_week.all()

    completed_workout_names = [w.name.lower() for _, w in week_entries]
    
    has_push = any("push" in name or "empuje" in name for name in completed_workout_names)
    has_pull = any("pull" in name or "tirón" in name for name in completed_workout_names)
    has_leg = any("pierna" in name or "leg" in name for name in completed_workout_names)

    # Si ya completó las 3 rutinas principales esta semana, sugerir Full-Body o Cardio
    if has_push and has_pull and has_leg:
        fb_stmt = select(Workout).where(func.lower(Workout.name).contains("full-body")).limit(1)
        res_fb = await db.execute(fb_stmt)
        fb_workout = res_fb.scalar_one_or_none()
        if fb_workout:
            return fb_workout
        
        cardio_stmt = select(Workout).where(func.lower(Workout.name).contains("cardio")).limit(1)
        res_cardio = await db.execute(cardio_stmt)
        return res_cardio.scalar_one_or_none()

    # 2. Consultar el último entrenamiento físico REAL (excluyendo días de "Descanso")
    last_log_stmt = (
        select(WorkoutLog, Workout)
        .join(Workout, WorkoutLog.workout_id == Workout.id)
        .where(~func.lower(Workout.name).contains("descanso"))
        .order_by(WorkoutLog.completed_at.desc())
        .limit(1)
    )
    res_last = await db.execute(last_log_stmt)
    last_entry = res_last.first()

    if not last_entry:
        # Primer entreno: Retornar Push (order_index 1)
        first_stmt = select(Workout).where(Workout.order_index == 1).limit(1)
        res_first = await db.execute(first_stmt)
        return res_first.scalar_one_or_none()

    last_log, last_workout = last_entry
    is_last_climbing = "escalada" in last_workout.name.lower()

    # Si el último entreno fue Escalada, descartar Pull al día siguiente
    avoid_pull = is_last_climbing

    # Consultar las 3 rutinas base
    base_stmt = select(Workout).where(Workout.order_index.in_([1, 2, 3])).order_by(Workout.order_index.asc())
    res_base = await db.execute(base_stmt)
    base_workouts = res_base.scalars().all()  # [Push(1), Pull(2), Pierna(3)]

    if not base_workouts:
        return None

    # Determinar siguiente en la rotación según la última rutina física real realizada
    current_index = last_workout.order_index if last_workout.order_index in [1, 2, 3] else 1
    next_index = (current_index % 3) + 1  # 1 -> 2 -> 3 -> 1

    # Si la siguiente en rotación es Pull (2) y debemos evitar Pull por Escalada, saltar a Pierna (3)
    if next_index == 2 and avoid_pull:
        next_index = 3

    target_workout_stmt = select(Workout).where(Workout.order_index == next_index).limit(1)
    res_target = await db.execute(target_workout_stmt)
    return res_target.scalar_one_or_none()


async def log_completed_workout(db: AsyncSession, workout_id: int, notes: str = "", rpe: Optional[int] = None) -> WorkoutLog:
    log = WorkoutLog(workout_id=workout_id, notes=notes, rpe=rpe, completed_at=datetime.utcnow())
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def log_activity_by_name(db: AsyncSession, name_keyword: str, notes: str = "") -> Optional[WorkoutLog]:
    """Busca o crea una rutina por nombre (ej. 'Escalada', 'Descanso') y registra la sesión."""
    stmt = select(Workout).where(func.lower(Workout.name).contains(name_keyword.lower())).limit(1)
    res = await db.execute(stmt)
    workout = res.scalar_one_or_none()

    if not workout:
        # Crear la actividad si no existe
        max_idx_stmt = select(func.max(Workout.order_index))
        res_max = await db.execute(max_idx_stmt)
        max_idx = (res_max.scalar() or 0) + 1
        workout = Workout(name=name_keyword.capitalize(), order_index=max_idx, target_muscles="General", description="Actividad personalizada")
        db.add(workout)
        await db.commit()
        await db.refresh(workout)

    return await log_completed_workout(db, workout_id=workout.id, notes=notes)


async def get_monthly_workout_summary(
    db: AsyncSession,
    year: Optional[int] = None,
    month: Optional[int] = None
) -> Dict[str, Any]:
    """
    Genera el resumen mensual discriminando entrenamientos físicos reales de los días de descanso.

    Separa las actividades de tipo 'Descanso' del total de sesiones realizadas, garantizando
    que total_workouts contabilice exclusivamente el esfuerzo físico activo.

    Args:
        db: Sesión asíncrona de base de datos SQLAlchemy.
        year: Año a consultar (si es None, toma el año actual).
        month: Mes a consultar (si es None, toma el mes actual).

    Returns:
        Dict con las claves:
            - year (int): Año consultado.
            - month (int): Mes consultado.
            - total_workouts (int): Suma de sesiones de entrenamiento físicas reales.
            - rest_days (int): Cantidad de días de descanso registrados en el mes.
            - breakdown (Dict[str, int]): Conteo individual por cada rutina física.
    """
    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    start_date = datetime(year, month, 1, 0, 0, 0)
    if month == 12:
        end_date = datetime(year + 1, 1, 1, 0, 0, 0) - timedelta(microseconds=1)
    else:
        end_date = datetime(year, month + 1, 1, 0, 0, 0) - timedelta(microseconds=1)

    stmt = (
        select(Workout.name, func.count(WorkoutLog.id))
        .join(Workout, WorkoutLog.workout_id == Workout.id)
        .where(and_(WorkoutLog.completed_at >= start_date, WorkoutLog.completed_at <= end_date))
        .group_by(Workout.name)
    )
    res = await db.execute(stmt)
    rows = res.fetchall()

    breakdown: Dict[str, int] = {}
    rest_days = 0

    for name, count in rows:
        # Si la rutina contiene la palabra 'descanso' (case-insensitive), se aísla como descanso
        if "descanso" in name.lower():
            rest_days += count
        else:
            breakdown[name] = count

    total_workouts = sum(breakdown.values())

    return {
        "year": year,
        "month": month,
        "total_workouts": total_workouts,
        "rest_days": rest_days,
        "breakdown": breakdown
    }


# ---------------------------------------------------------
# RECURRING TASKS CRUD
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# PILL LOGGING CRUD
# ---------------------------------------------------------

async def confirm_pill_taken(db: AsyncSession, target_date: Optional[date] = None) -> PillLog:
    if not target_date:
        target_date = date.today()
    
    stmt = select(PillLog).where(PillLog.log_date == target_date)
    res = await db.execute(stmt)
    pill_entry = res.scalar_one_or_none()

    if not pill_entry:
        pill_entry = PillLog(log_date=target_date, taken=True, confirmed_at=datetime.utcnow())
        db.add(pill_entry)
    else:
        pill_entry.taken = True
        pill_entry.confirmed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(pill_entry)
    return pill_entry

async def is_pill_taken_today(db: AsyncSession, target_date: Optional[date] = None) -> bool:
    if not target_date:
        target_date = date.today()
    
    stmt = select(PillLog).where(and_(PillLog.log_date == target_date, PillLog.taken == True))
    res = await db.execute(stmt)
    return res.scalar_one_or_none() is not None


# ---------------------------------------------------------
# SPOTIFY PAYMENT TRACKER CRUD
# ---------------------------------------------------------

async def get_or_create_spotify_tracker(db: AsyncSession, month_key: Optional[str] = None) -> SpotifyPaymentTracker:
    if not month_key:
        month_key = date.today().strftime("%Y-%m")
    
    stmt = select(SpotifyPaymentTracker).where(SpotifyPaymentTracker.month_key == month_key)
    res = await db.execute(stmt)
    tracker = res.scalar_one_or_none()

    if not tracker:
        tracker = SpotifyPaymentTracker(
            month_key=month_key,
            total_friends=4,
            paid_count=0,
            ruben_paid=False,
            victoriano_paid=False,
            miquel_paid=False,
            joan_paid=False,
            is_complete=False
        )
        db.add(tracker)
        await db.commit()
        await db.refresh(tracker)

    return tracker


async def update_spotify_friend_payment(db: AsyncSession, friend_name: str, is_paid: bool = True, month_key: Optional[str] = None) -> SpotifyPaymentTracker:
    """Actualiza el pago individual de uno de los 4 amigos (Ruben, Victoriano, Miquel, Joan)."""
    tracker = await get_or_create_spotify_tracker(db, month_key)
    f_lower = friend_name.lower().strip()

    if "ruben" in f_lower:
        tracker.ruben_paid = is_paid
    elif "victoriano" in f_lower:
        tracker.victoriano_paid = is_paid
    elif "miquel" in f_lower:
        tracker.miquel_paid = is_paid
    elif "joan" in f_lower:
        tracker.joan_paid = is_paid

    # Recalcular recuento total de pagos y marcar si está completo (4/4)
    tracker.paid_count = sum([
        1 if tracker.ruben_paid else 0,
        1 if tracker.victoriano_paid else 0,
        1 if tracker.miquel_paid else 0,
        1 if tracker.joan_paid else 0
    ])
    tracker.is_complete = (tracker.paid_count >= 4)

    await db.commit()
    await db.refresh(tracker)
    return tracker


async def update_spotify_paid_count(db: AsyncSession, paid_count: int, month_key: Optional[str] = None) -> SpotifyPaymentTracker:
    tracker = await get_or_create_spotify_tracker(db, month_key)
    tracker.paid_count = min(paid_count, tracker.total_friends)
    if tracker.paid_count >= tracker.total_friends:
        tracker.is_complete = True
        tracker.ruben_paid = True
        tracker.victoriano_paid = True
        tracker.miquel_paid = True
        tracker.joan_paid = True
    await db.commit()
    await db.refresh(tracker)
    return tracker


async def update_spotify_last_reminded(db: AsyncSession, month_key: Optional[str] = None) -> SpotifyPaymentTracker:
    tracker = await get_or_create_spotify_tracker(db, month_key)
    tracker.last_reminded_at = date.today()
    await db.commit()
    await db.refresh(tracker)
    return tracker


# ---------------------------------------------------------
# OFFICE SCHEDULE CRUD
# ---------------------------------------------------------

async def set_office_attendance(db: AsyncSession, target_date: date, will_attend: bool) -> OfficeSchedule:
    stmt = select(OfficeSchedule).where(OfficeSchedule.schedule_date == target_date)
    res = await db.execute(stmt)
    schedule = res.scalar_one_or_none()

    if not schedule:
        schedule = OfficeSchedule(schedule_date=target_date, will_attend=will_attend)
        db.add(schedule)
    else:
        schedule.will_attend = will_attend

    await db.commit()
    await db.refresh(schedule)
    return schedule

async def get_office_attendance(db: AsyncSession, target_date: date) -> Optional[bool]:
    stmt = select(OfficeSchedule).where(OfficeSchedule.schedule_date == target_date)
    res = await db.execute(stmt)
    schedule = res.scalar_one_or_none()
    return schedule.will_attend if schedule else None

async def mark_office_night_notified(db: AsyncSession, target_date: date):
    stmt = select(OfficeSchedule).where(OfficeSchedule.schedule_date == target_date)
    res = await db.execute(stmt)
    schedule = res.scalar_one_or_none()
    if schedule:
        schedule.user_notified_night_before = True
        await db.commit()


def get_week_office_dates(target_date: date) -> Tuple[date, date]:
    """
    Retorna la tupla (jueves, viernes) correspondiente a la semana de la fecha dada.
    Lunes = 0, Martes = 1, Miércoles = 2, Jueves = 3, Viernes = 4, Sábado = 5, Domingo = 6.

    Args:
        target_date: Fecha de referencia dentro de la semana.

    Returns:
        Tuple[date, date]: Fechas correspondientes al jueves y viernes de esa misma semana.
    """
    monday = target_date - timedelta(days=target_date.weekday())
    thursday = monday + timedelta(days=3)
    friday = monday + timedelta(days=4)
    return thursday, friday


async def clear_office_attendance(db: AsyncSession, target_date: date) -> None:
    """
    Elimina el registro de asistencia para una fecha determinada (estado indeterminado o 'No lo sé').

    Args:
        db: Sesión asíncrona de SQLAlchemy.
        target_date: Fecha cuyo registro de asistencia se desea reiniciar.
    """
    stmt = select(OfficeSchedule).where(OfficeSchedule.schedule_date == target_date)
    res = await db.execute(stmt)
    schedule = res.scalar_one_or_none()
    if schedule:
        await db.delete(schedule)
        await db.commit()


async def get_weekly_office_decision(db: AsyncSession, today: date) -> Optional[str]:
    """
    Consulta si ya existe una decisión de oficina confirmada para la semana en curso.

    Args:
        db: Sesión asíncrona de SQLAlchemy.
        today: Fecha de referencia.

    Returns:
        - 'thursday': si asiste el jueves.
        - 'friday': si asiste el viernes.
        - 'none': si confirmó que no asiste ningún día (teletrabajo toda la semana).
        - None: si aún no ha decidido o seleccionó 'No lo sé'.
    """
    thursday, friday = get_week_office_dates(today)
    thu_status = await get_office_attendance(db, thursday)
    fri_status = await get_office_attendance(db, friday)

    if thu_status is True:
        return "thursday"
    if fri_status is True:
        return "friday"
    if thu_status is False and fri_status is False:
        return "none"
    return None


# ---------------------------------------------------------
# DEADLINE TASKS CRUD
# ---------------------------------------------------------

async def create_deadline_task(db: AsyncSession, title: str, deadline: datetime) -> DeadlineTask:
    task = DeadlineTask(title=title, deadline=deadline, is_done=False)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

async def get_pending_deadline_tasks(db: AsyncSession) -> List[DeadlineTask]:
    stmt = select(DeadlineTask).where(DeadlineTask.is_done == False).order_by(DeadlineTask.deadline.asc())
    res = await db.execute(stmt)
    return res.scalars().all()

async def mark_deadline_task_completed(db: AsyncSession, task_id: int) -> Optional[DeadlineTask]:
    """Marca la tarea como completada y la elimina de la base de datos."""
    stmt = select(DeadlineTask).where(DeadlineTask.id == task_id)
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if task:
        await db.delete(task)
        await db.commit()
        return task
    return None

async def delete_deadline_task(db: AsyncSession, task_id: int) -> bool:
    stmt = select(DeadlineTask).where(DeadlineTask.id == task_id)
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if task:
        await db.delete(task)
        await db.commit()
        return True
    return False

async def update_deadline_task(
    db: AsyncSession,
    task_id: int,
    new_title: Optional[str] = None,
    new_deadline: Optional[datetime] = None
) -> Optional[DeadlineTask]:
    stmt = select(DeadlineTask).where(DeadlineTask.id == task_id)
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if task:
        if new_title:
            task.title = new_title
        if new_deadline:
            task.deadline = new_deadline
        await db.commit()
        await db.refresh(task)
    return task

async def update_deadline_last_reminded(db: AsyncSession, task_id: int, reminded_at: Optional[datetime] = None) -> Optional[DeadlineTask]:
    if not reminded_at:
        reminded_at = datetime.utcnow()
    stmt = select(DeadlineTask).where(DeadlineTask.id == task_id)
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if task:
        task.last_reminded_at = reminded_at
        await db.commit()
        await db.refresh(task)
    return task