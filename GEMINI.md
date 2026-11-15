# Reglas de Trabajo Autónomo de Jarvis Assistant

Este documento establece el marco de trabajo, el protocolo de ejecución autónoma y las directrices de ingeniería de software que el agente debe seguir de forma estricta e independiente en todas las sesiones.

---

## 🤖 1. Principio de Autonomía Total
- **Cero interrupciones:** El agente debe trabajar de manera completamente autónoma. No debe solicitar permisos ni confirmaciones conversacionales para ejecutar comandos de terminal, instalar dependencias, crear ramas, modificar archivos o ejecutar pruebas.
- **Resolución proactiva:** Si un test falla o surge un error de sintaxis/dependencias, el agente investiga, corrige y reintenta por sí mismo.
- **Punto de parada:** El agente solo detiene su turno cuando la tarea ha alcanzado el estado **`In review`** y está lista para que el usuario la inspeccione, o en caso de un error externo insalvable que requiera intervención de credenciales humanas.
- **Despliegues en Servidor:** El agente **NO realiza despliegues en el servidor de producción**. Esa responsabilidad pertenece exclusivamente al usuario tras revisar el código y aprobar la PR.

---

## 📋 2. Protocolo de Gestión del Tablero Kanban (GitHub Projects)

- **Repositorio:** `dvalloz/jarvis-project`
- **Proyecto GitHub (v2):** `Jarvis Personal Assistant` (ID: `PVT_kwHOCPdEf84BhRaL`)
- **Campo de Estado (Status):** `PVTSSF_lAHOCPdEf84BhRaLzhgNvcY`
  - `Backlog`: `f75ad846`
  - `Ready`: `61e4505c`
  - `In progress`: `47fc9ee4`
  - `In review`: `df73e18b`
  - `Done`: `98236657`

### Flujo de Ejecución por Tarea:
1. **Triage:** Al recibir la orden de abordar trabajo (o al decir "siguiente tarea"), consultar las tareas en la columna **`Ready`** y seleccionar la primera por orden de prioridad.
2. **Inicio del Trabajo:** 
   - Cambiar el estado de la tarea en el tablero a **`In progress`**.
   - Publicar un primer comentario en la Issue de GitHub indicando que se ha iniciado el desarrollo y el enfoque planeado.
3. **Desarrollo y Bitácora:**
   - Crear una rama de desarrollo dedicada a la tarea.
   - Modificar el código, añadir herramientas, modelos o configuraciones necesarias.
   - Dejar comentarios en la Issue si hay hitos clave o decisiones de diseño relevantes.
4. **Verificación:**
   - Ejecutar pruebas automáticas o verificaciones de sintaxis y consistencia de datos.
5. **Pase a Revisión y Creación de PR:**
   - Subir la rama a GitHub y abrir una Pull Request (PR) dirigida a `dev` (o `main`) enlazando la Issue (`Closes #<número>`).
   - Cambiar el estado de la tarjeta en el tablero a **`In review`**.
   - Publicar un comentario final de cierre en la Issue con el resumen de cambios realizados, archivos tocados, enlace a la PR y estado de los tests.
   - Presentar al usuario el reporte final indicando que la tarea está lista para su revisión y despliegue.

---

## 🛠️ 3. Buenas Prácticas de Ingeniería de Software (Development Standards)

El agente debe adherirse rigurosamente a los estándares de desarrollo profesional de un ingeniero senior:

### 3.1 Gestión de Ramas y Git Flow
- **Ramas dedicadas por tarea:** Nunca realizar commits directamente sobre `main` ni `master`. Cada tarea debe trabajarse en su propia rama descriptiva derivada de `dev` (o `main` si `dev` no existe), siguiendo la convención:
  - Funcionalidades: `feat/issue-<numero>-<slug-descriptivo>` (ej. `feat/issue-6-gmail-api-model`)
  - Corrección de bugs: `fix/issue-<numero>-<slug-descriptivo>`
  - Refactorizaciones: `refactor/issue-<numero>-<slug-descriptivo>`
- **Commits atómicos y convencionales:** Utilizar la especificación **Conventional Commits** (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`) con mensajes descriptivos que expliquen el *qué* y el *por qué*.
- **Pull Requests (PRs) obligatorias:** Todo desarrollo debe concluir en una Pull Request clara hacia `dev` (o `main`) con descripción detallada de cambios, checklist de verificación y referencia a la Issue (`Closes #X`). **Está terminantemente prohibido mergear a `main`/`master` directamente.**

### 3.2 Calidad del Código y Documentación Interna
- **Docstrings y Anotaciones de Tipo:** Todas las nuevas funciones, clases y métodos deben contar con type hinting estricto (`typing`, `pydantic`) y docstrings explicativos indicando parámetros, tipo de retorno y posibles excepciones.
- **Comentarios en el código:** Añadir comentarios explicativos en bloques de lógica compleja, reglas de negocio no triviales o decisiones de diseño críticas, priorizando siempre la legibilidad.
- **Manejo robusto de errores y Logging:** Implementar captura de excepciones específicas y trazabilidad mediante el módulo `logging` del proyecto (`logger.info`, `logger.warning`, `logger.error`), evitando capturas genéricas desatendidas (`except Exception: pass`).
- **Arquitectura Limpia en Capas:** Respetar la modularidad del proyecto (`bot/`, `tools/`, `agent/`, `database/`, `config/`). Cada nuevo componente debe ubicarse en su capa correspondiente sin acoplamientos circulares.
- **Actualización de Documentación:** Si la funcionalidad introduce nuevas herramientas, modelos de base de datos o cron jobs, actualizar consecuentemente [`DOCUMENTACION_TECNICA.md`](file:///c:/Users/dvdva/Documents/jarvis-project/DOCUMENTACION_TECNICA.md) y [`README.md`](file:///c:/Users/dvdva/Documents/jarvis-project/README.md).

### 3.3 Orden y Limpieza del Repositorio
- **Cero basura en el árbol de trabajo:** Nunca commitear archivos temporales, scripts de scratch/depuración, volcados locales de base de datos, credenciales ni carpetas `__pycache__`.
- **Inspección de `git status`:** Antes de crear commits, verificar exhaustivamente el estado del árbol de trabajo (`git status`) para asegurar que solo los archivos intencionados forman parte del commit.
- **Mantenimiento de `.gitignore`:** Asegurar que cualquier nuevo artefacto temporal o secreto quede cubierto en `.gitignore`.

### 3.4 Trazabilidad y Comunicación en GitHub
- **Bitácora en Issues:** Mantener al día la Issue de GitHub con comentarios informativos:
  1. *Comentario inicial:* Al arrancar el trabajo, indicando enfoque técnico y rama creada.
  2. *Comentarios intermedios:* Ante decisiones técnicas relevantes, trade-offs o desbloqueos.
  3. *Comentario final:* Resumen del pull request, checklist de criterios de aceptación verificados y pruebas ejecutadas.

---

## 🔒 4. Políticas de Privacidad y Seguridad
- **Protección de PII en Correos:** En tareas de procesamiento de email, **nunca** enviar el cuerpo (`body`), fragmentos extensos o datos sensibles a modelos de IA externos. Solo metadatos sanitizados (`sender`, `subject`).
- **Gestión de Secretos:** Nunca exponer ni commitear tokens, credenciales ni claves privadas fuera de `.env` o el directorio `credentials/`.
