# 📍 Fase 2: Modelado de Datos y Capa de Persistencia (Resumen de Fase)

Esta fase abarca la construcción de la base de datos del proyecto mediante SQLAlchemy Asíncrono y PostgreSQL, incluyendo los modelos de rutinas de entreno, registros históricos, tareas periódicas y recordatorios rápidos, así como sus operaciones CRUD y script de sembrado inicial.

---

## 📂 Documentos de Tarea Incluidos

1. 🔹 [Tarea 2.1 — Definición de Esquemas ORM (`models.py`)](./tarea_2_1_modelos_orm.md)
2. 🔹 [Tarea 2.2 — Conexión y Sesión Asíncrona (`connection.py`)](./tarea_2_2_conexion_async.md)
3. 🔹 [Tarea 2.3 — Implementación de Operaciones CRUD (`crud.py`)](./tarea_2_3_operaciones_crud.md)
4. 🔹 [Tarea 2.4 — Script de Inicialización y Sembrado (`seed.py`)](./tarea_2_4_script_seed.md)

---

## 🎯 Entregables Globales de la Fase

* Tablas `workouts`, `workout_logs`, `recurring_tasks` y `quick_reminders` definidas.
* Generador de sesiones `get_db()` asíncrono con `asyncpg`.
* Funciones de consulta y actualización CRUD probadas y funcionalmente deterministas.
* Script `seed.py` para crear las tablas y poblar datos iniciales.
