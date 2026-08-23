TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Obtiene la lista de eventos guardados en Google Calendar para un día concreto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_str": {
                        "type": "string",
                        "description": "Fecha en formato YYYY-MM-DD"
                    }
                },
                "required": ["date_str"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weekly_calendar_events",
            "description": "Obtiene la lista de eventos guardados en Google Calendar para toda la semana completa (Lunes a Domingo).",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_str": {
                        "type": "string",
                        "description": "Cualquier fecha YYYY-MM-DD dentro de la semana a consultar"
                    }
                },
                "required": ["date_str"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Crea una nueva cita o evento en Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Título de la reunión o evento"},
                    "start_iso": {"type": "string", "description": "Hora de inicio en formato ISO 8601"},
                    "end_iso": {"type": "string", "description": "Hora de fin en formato ISO 8601"},
                    "description": {"type": "string", "description": "Detalles adicionales"}
                },
                "required": ["summary", "start_iso", "end_iso"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_next_workout",
            "description": "Obtiene la rutina de gimnasio recomendada según la rotación inteligente (Push/Pull/Pierna), descansos por escalada y rutinas semanales completadas.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_workout_summary",
            "description": "Obtiene el recuento total de entrenamientos realizados este mes y cuántas veces se ha hecho cada rutina específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Año a consultar (opcional)"},
                    "month": {"type": "integer", "description": "Mes del 1 al 12 (opcional)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_pill_taken",
            "description": "Registra que el usuario ya se ha tomado la pastilla correspondiente al día de hoy.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_pill_status",
            "description": "Consulta si el usuario ya se ha tomado o confirmado la pastilla correspondiente al día de hoy.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_spotify_bizum",
            "description": "Actualiza la cantidad total de amigos que han pagado el Bizum de Spotify de este mes (total 4 amigos).",
            "parameters": {
                "type": "object",
                "properties": {
                    "paid_count": {
                        "type": "integer",
                        "description": "Número de amigos que han pagado de 0 a 4"
                    }
                },
                "required": ["paid_count"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_spotify_friend_payment",
            "description": "Actualiza el pago individual de Bizum de Spotify para un amigo específico (Ruben, Victoriano, Miquel o Joan).",
            "parameters": {
                "type": "object",
                "properties": {
                    "friend_name": {"type": "string", "description": "Nombre exacto del amigo: Ruben, Victoriano, Miquel o Joan"},
                    "is_paid": {"type": "boolean", "description": "True si ha pagado, False si está pendiente"}
                },
                "required": ["friend_name", "is_paid"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_office_attendance",
            "description": "Registra si el usuario asistirá presencialmente a la oficina en una fecha específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_str": {"type": "string", "description": "Fecha YYYY-MM-DD"},
                    "will_attend": {"type": "boolean", "description": "True si irá a la oficina, False si hará teletrabajo"}
                },
                "required": ["date_str", "will_attend"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_deadline_task",
            "description": "Registra una nueva tarea puntual que tiene una fecha y hora límite de vencimiento (deadline).",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Título o descripción de la tarea"},
                    "deadline_iso": {"type": "string", "description": "Fecha y hora límite en ISO 8601 (YYYY-MM-DDTHH:MM:SS)"}
                },
                "required": ["title", "deadline_iso"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pending_deadline_tasks",
            "description": "Consulta todas las tareas pendientes con fecha límite de vencimiento.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mark_deadline_task_completed",
            "description": "Marca como completada una tarea puntual con fecha límite y la borra de la base de datos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID numérico de la tarea a completar"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_deadline_task",
            "description": "Elimina directamente una tarea puntual con fecha límite de la base de datos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID numérico de la tarea a eliminar"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_deadline_task",
            "description": "Modifica el título o la fecha límite de una tarea puntual existente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID numérico de la tarea a modificar"},
                    "new_title": {"type": "string", "description": "Nuevo título o descripción de la tarea (opcional)"},
                    "new_deadline_iso": {"type": "string", "description": "Nueva fecha/hora límite en ISO 8601 YYYY-MM-DDTHH:MM:SS (opcional)"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_climbing_activity",
            "description": "Registra que el usuario ha ido a escalar hoy, lo cual influirá en las recomendaciones de gimnasio para no sugerir Pull al día siguiente.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_rest_day",
            "description": "Registra que el usuario hoy se toma el día de descanso en su entrenamiento. No altera el orden de la rotación para la próxima sesión.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "Obtiene la predicción meteorológica en tiempo real (temperatura máxima, mínima, probabilidad de lluvia y estado del cielo con emojis).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_news",
            "description": "Obtiene los titulares de las 2 o 3 noticias principales destacadas del día en España.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]
