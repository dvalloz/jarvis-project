import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from bot.scheduler import daytime_email_monitor_job
from database.models import EmailLog

class TestDaytimeEmailMonitor(unittest.IsolatedAsyncioTestCase):
    """Pruebas unitarias para el cron job de monitoreo diurno de emails en APScheduler."""

    @patch("bot.scheduler.get_gmail_service")
    @patch("bot.scheduler.fetch_unread_emails_metadata")
    @patch("bot.scheduler.triage_email")
    @patch("bot.scheduler.AsyncSessionLocal")
    @patch("bot.scheduler.create_or_get_email_log")
    @patch("bot.scheduler.mark_email_alert_sent")
    @patch("bot.scheduler.get_recent_user_corrections")
    async def test_daytime_monitor_alerts_important_email(
        self,
        mock_get_corrections,
        mock_mark_sent,
        mock_create_log,
        mock_session_local,
        mock_triage,
        mock_fetch_unread,
        mock_get_service
    ):
        """Verifica que envíe alerta push exclusivamente para emails importantes no promocionales."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        # Mock de correcciones recientes
        mock_get_corrections.return_value = []

        now = datetime.now(timezone.utc)
        # fetch_unread_emails_metadata se llama dos veces (inbox + promotions)
        mock_fetch_unread.side_effect = [
            [
                {
                    "message_id": "msg_important_01",
                    "sender": "banco@santander.es",
                    "subject": "Transferencia urgente pendiente",
                    "received_at": now,
                    "is_promotional": False
                }
            ],
            []  # Promociones vacías
        ]

        # Triage returns
        async def triage_side_effect(mail_data, recent_corrections=None):
            if mail_data["message_id"] == "msg_important_01":
                return {"is_important": True, "is_promotional": False, "reason": "Notificación bancaria urgente"}
            return {"is_important": False, "is_promotional": True, "reason": "Publicidad"}

        mock_triage.side_effect = triage_side_effect

        # DB returns
        email_important = EmailLog(
            id=1,
            message_id="msg_important_01",
            sender="banco@santander.es",
            subject="Transferencia urgente pendiente",
            received_at=now,
            is_promotional=False,
            is_important=True,
            alert_sent=False
        )

        async def create_log_side_effect(db, message_id, **kwargs):
            return email_important, True

        mock_create_log.side_effect = create_log_side_effect

        # Mock app and bot
        mock_app = MagicMock()
        mock_app.bot.send_message = AsyncMock()

        # Mock async session context manager
        mock_db_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db_session

        await daytime_email_monitor_job(mock_app)

        # Verificar que send_message se ejecutó exactamente una vez
        mock_app.bot.send_message.assert_called_once()
        call_kwargs = mock_app.bot.send_message.call_args[1]

        self.assertIn("🚨 **CORREO IMPORTANTE DETECTADO**", call_kwargs["text"])
        self.assertIn("banco@santander.es", call_kwargs["text"])
        self.assertIn("Transferencia urgente pendiente", call_kwargs["text"])
        self.assertIn("Notificación bancaria urgente", call_kwargs["text"])

        # Verificar que se marcó como alertado en base de datos
        mock_mark_sent.assert_called_once_with(mock_db_session, 1)

    @patch("bot.scheduler.get_gmail_service")
    async def test_daytime_monitor_graceful_service_failure(self, mock_get_service):
        """Verifica que el monitor capture fallos de inicialización sin lanzar excepción no controlada."""
        mock_get_service.side_effect = RuntimeError("Token no autenticado")

        mock_app = MagicMock()
        mock_app.bot.send_message = AsyncMock()

        # No debe lanzar excepción
        await daytime_email_monitor_job(mock_app)
        mock_app.bot.send_message.assert_not_called()

if __name__ == "__main__":
    unittest.main()
