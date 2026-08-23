from datetime import datetime
from typing import Optional
from database.connection import AsyncSessionLocal
from database.crud import (
    confirm_pill_taken,
    is_pill_taken_today,
    update_spotify_paid_count,
    update_spotify_friend_payment,
    set_office_attendance,
    create_deadline_task,
    get_pending_deadline_tasks,
    mark_deadline_task_completed,
    delete_deadline_task,
    update_deadline_task
)

async def confirm_pill_tool() -> str:
    """Wrapper de herramienta para confirmar la toma de pastilla."""
    async with AsyncSessionLocal() as db:
        entry = await confirm_pill_taken(db)
        return f"Pastilla confirmada como tomada el {entry.log_date} a las {entry.confirmed_at}."

async def check_pill_status_tool() -> str:
    """Wrapper de herramienta para consultar si el usuario ya se ha tomado la pastilla hoy."""
    async with AsyncSessionLocal() as db:
        taken = await is_pill_taken_today(db)
        if taken:
            return "La pastilla de hoy SÍ ha sido tomada y confirmada."
        return "La pastilla de hoy AÚN NO ha sido tomada ni confirmada."

async def update_spotify_tool(paid_count: int) -> str:
    """Wrapper de herramienta para actualizar los cobros del Bizum de Spotify."""
    async with AsyncSessionLocal() as db:
        tracker = await update_spotify_paid_count(db, paid_count)
        return f"Actualizado cobro de Spotify: {tracker.paid_count}/{tracker.total_friends} amigos han pagado."

async def update_spotify_friend_tool(friend_name: str, is_paid: bool = True) -> str:
    """Wrapper de herramienta para registrar el pago del Bizum de Spotify de un amigo específico (Ruben, Victoriano, Miquel, Joan)."""
    async with AsyncSessionLocal() as db:
        tracker = await update_spotify_friend_payment(db, friend_name, is_paid)
        return f"Registrado pago de {friend_name}. Estado actual: {tracker.paid_count}/4 amigos han pagado (Ruben: {tracker.ruben_paid}, Victoriano: {tracker.victoriano_paid}, Miquel: {tracker.miquel_paid}, Joan: {tracker.joan_paid})."

async def set_office_tool(date_str: str, will_attend: bool) -> str:
    """Wrapper de herramienta para registrar asistencia a la oficina."""
    target_dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    async with AsyncSessionLocal() as db:
        sched = await set_office_attendance(db, target_dt, will_attend)
        estado = "asistirá" if sched.will_attend else "no asistirá"
        return f"Registrado que el usuario {estado} a la oficina el {sched.schedule_date}."

async def add_deadline_tool(title: str, deadline_iso: str) -> str:
    """Wrapper de herramienta para crear una tarea con plazo límite."""
    deadline_dt = datetime.fromisoformat(deadline_iso)
    async with AsyncSessionLocal() as db:
        task = await create_deadline_task(db, title, deadline_dt)
        return f"Tarea registrada: '[ID {task.id}] {task.title}' con fecha límite {task.deadline}."

async def get_pending_deadline_tasks_tool() -> str:
    """Wrapper de herramienta para consultar las tareas pendientes con plazo límite."""
    async with AsyncSessionLocal() as db:
        tasks = await get_pending_deadline_tasks(db)
        if not tasks:
            return "No tienes ninguna tarea con plazo límite pendiente."
        
        formatted = []
        for t in tasks:
            formatted.append(f"- [ID {t.id}] '{t.title}' (Vence: {t.deadline.strftime('%Y-%m-%d %H:%M')})")
        return "Tareas pendientes registradas:\n" + "\n".join(formatted)

async def mark_deadline_task_completed_tool(task_id: int) -> str:
    """Wrapper de herramienta para marcar una tarea puntual como completada."""
    async with AsyncSessionLocal() as db:
        task = await mark_deadline_task_completed(db, task_id)
        if task:
            return f"Tarea ID {task.id} ('{task.title}') marcada como completada."
        return f"No se encontró ninguna tarea pendiente con el ID {task_id}."

async def delete_deadline_task_tool(task_id: int) -> str:
    """Wrapper de herramienta para eliminar/borrar una tarea puntual por su ID."""
    async with AsyncSessionLocal() as db:
        success = await delete_deadline_task(db, task_id)
        if success:
            return f"Tarea ID {task_id} eliminada correctamente de la base de datos."
        return f"No se encontró ninguna tarea registrada con el ID {task_id}."

async def update_deadline_task_tool(task_id: int, new_title: Optional[str] = None, new_deadline_iso: Optional[str] = None) -> str:
    """Wrapper de herramienta para modificar el título o fecha límite de una tarea puntual."""
    new_dt = datetime.fromisoformat(new_deadline_iso) if new_deadline_iso else None
    async with AsyncSessionLocal() as db:
        task = await update_deadline_task(db, task_id, new_title=new_title, new_deadline=new_dt)
        if task:
            return f"Tarea ID {task.id} actualizada: '{task.title}' (Vence: {task.deadline.strftime('%Y-%m-%d %H:%M')})."
        return f"No se encontró ninguna tarea registrada con el ID {task_id}."
