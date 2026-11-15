import unittest
from datetime import datetime, timezone, date
from unittest.mock import AsyncMock, patch, MagicMock

from bot.scheduler import nightly_checks_job
from database.models import EmailLog

class TestNightlyEmailSummary(unittest.IsolatedAsyncioTestCase):
    """Pruebas unitarias para el resumen consolidado nocturno de emails en el cron job de las 23:00 PM."""

    @patch("bot.scheduler.get_gmail_service")
    @patch("bot.scheduler.fetch_unread_emails_metadata")
    @patch("bot.scheduler.get_unsummarized_emails_for_date")
    @patch("bot.scheduler.mark_emails_night_summarized")
    @patch("bot.scheduler.is_pill_taken_today")
    @patch("bot.scheduler.get_office_attendance")
    @patch("bot.scheduler.get_or_create_spotify_tracker")
    @patch("bot.scheduler.AsyncSessionLocal")
    async def test_nightly_email_summary_formatting(
        self,
        mock_session_local,
        mock_spotify,
        mock_office,
        mock_pill,
        mock_mark_summarized,
        mock_get_unsummarized,
        mock_fetch_unread,
        mock_get_service
    ):
        """Verifica que el resumen nocturno agrupe correos importantes y secundarios limpiamente."""
        mock_get_service.side_effect = RuntimeError("No Gmail in test")
        mock_fetch_unread.return_value = []
        mock_pill.return_value = True
        mock_office.return_value = False
        mock_spotify.return_value = MagicMock(is_complete=True)

        now = datetime.now(timezone.utc)
        emails = [
            EmailLog(
                id=1,
                message_id="msg_01",
                sender="Banco Santander <notificaciones@santander.es>",
                subject="Liquidación de cuenta",
                received_at=now,
                is_important=True,
                is_promotional=False
            ),
            EmailLog(
                id=2,
                message_id="msg_02",
                sender="Iberdrola Clientes <factura@iberdrola.es>",
                subject="Tu factura de luz de noviembre ya está disponible",
                received_at=now,
                is_important=False,
                is_promotional=False
            )
        ]
        mock_get_unsummarized.return_value = emails

        mock_app = MagicMock()
        mock_app.bot.send_message = AsyncMock()

        mock_db_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db_session

        await nightly_checks_job(mock_app)

        # Buscar el mensaje de correos enviado
        email_calls = [
            c for c in mock_app.bot.send_message.call_args_list
            if "RESUMEN DE CORREOS DEL DÍA" in c[1].get("text", "")
        ]
        self.assertEqual(len(email_calls), 1, "Debe enviarse un mensaje con el resumen nocturno de correos")
        sent_text = email_calls[0][1]["text"]

        self.assertIn("🔴 **Correos Importantes / Prioritarios:**", sent_text)
        self.assertIn("Banco Santander", sent_text)
        self.assertIn("Liquidación de cuenta", sent_text)

        self.assertIn("ℹ️ **Otros correos relevantes del día:**", sent_text)
        self.assertIn("Iberdrola Clientes", sent_text)
        self.assertIn("Tu factura de luz", sent_text)

        # Verificar que se marcaron como resumidos
        mock_mark_summarized.assert_called_once_with(mock_db_session, [1, 2])

    @patch("bot.scheduler.get_gmail_service")
    @patch("bot.scheduler.fetch_unread_emails_metadata")
    @patch("bot.scheduler.get_unsummarized_emails_for_date")
    @patch("bot.scheduler.mark_emails_night_summarized")
    @patch("bot.scheduler.is_pill_taken_today")
    @patch("bot.scheduler.get_office_attendance")
    @patch("bot.scheduler.get_or_create_spotify_tracker")
    @patch("bot.scheduler.AsyncSessionLocal")
    async def test_nightly_email_summary_empty(
        self,
        mock_session_local,
        mock_spotify,
        mock_office,
        mock_pill,
        mock_mark_summarized,
        mock_get_unsummarized,
        mock_fetch_unread,
        mock_get_service
    ):
        """Verifica el comportamiento cuando no hubo correos pendientes para resumir hoy."""
        mock_get_service.side_effect = RuntimeError("No Gmail in test")
        mock_fetch_unread.return_value = []
        mock_pill.return_value = True
        mock_office.return_value = False
        mock_spotify.return_value = MagicMock(is_complete=True)
        mock_get_unsummarized.return_value = []

        mock_app = MagicMock()
        mock_app.bot.send_message = AsyncMock()

        mock_db_session = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db_session

        await nightly_checks_job(mock_app)

        email_calls = [
            c for c in mock_app.bot.send_message.call_args_list
            if "RESUMEN DE CORREOS DEL DÍA" in c[1].get("text", "")
        ]
        self.assertEqual(len(email_calls), 0)
        mock_mark_summarized.assert_not_called()

if __name__ == "__main__":
    unittest.main()
