# 🔹 Tarea 2.2 — Conexión y Sesión Asíncrona (`database/connection.py`)

## 🎯 Objetivo
Configurar el motor asíncrono `create_async_engine` y la fábrica de sesiones de SQLAlchemy para interactuar con PostgreSQL de forma no bloqueante.

---

## 📋 Pasos de Ejecución Paso a Paso

1. **Crear `database/connection.py`:**
   ```python
   from typing import AsyncGenerator
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from config.settings import settings

   engine = create_async_engine(
       settings.database_url,
       echo=False,
       future=True
   )

   AsyncSessionLocal = async_sessionmaker(
       bind=engine,
       class_=AsyncSession,
       expire_on_commit=False,
       autoflush=False
   )

   async def get_db() -> AsyncGenerator[AsyncSession, None]:
       async with AsyncSessionLocal() as session:
           try:
               yield session
           finally:
               await session.close()
   ```

---

## ✅ Verificación de la Tarea
- Probar una conexión asíncrona de prueba enviando `SELECT 1`:
  ```python
  import asyncio
  from database.connection import engine
  from sqlalchemy import text

  async def test_conn():
      async with engine.connect() as conn:
          res = await conn.execute(text("SELECT 1"))
          print(res.scalar())

  asyncio.run(test_conn())
  ```
