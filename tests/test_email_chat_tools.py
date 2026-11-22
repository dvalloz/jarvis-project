import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, date, timezone
from database.models import EmailLog
from database.crud import get_important_emails, get_recent_emails
from tools.email_tools import check_important_emails_tool, get_recent_emails_summary_tool
from agent.engine import execute_tool_call


class TestEmailChatTools(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mail_important = EmailLog(
            id=1,
            message_id="msg-101",
            sender="jefe@empresa.com",
            subject="URGENTE: Revisión de contrato",
            received_at=datetime(2026, 11, 21, 10, 30, tzinfo=timezone.utc),
            is_promotional=False,
            is_important=True,
            alert_sent=True,
            night_summary_included=False
        )
        self.mail_regular = EmailLog(
            id=2,
            message_id="msg-102",
            sender="soporte@proveedor.com",
            subject="Actualización de tickets",
            received_at=datetime(2026, 11, 21, 11, 15, tzinfo=timezone.utc),
            is_promotional=False,
            is_important=False,
            alert_sent=False,
            night_summary_included=False
        )
        self.mail_promo = EmailLog(
            id=3,
            message_id="msg-103",
            sender="ofertas@tienda.com",
            subject="Descuentos del 50%",
            received_at=datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc),
            is_promotional=True,
            is_important=False,
            alert_sent=False,
            night_summary_included=False
        )

    async def test_crud_get_important_emails(self):
        """Verifica que get_important_emails devuelva solo correos importantes no promocionales."""
        mock_db = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [self.mail_important]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        res = await get_important_emails(mock_db, target_date=date(2026, 11, 21), limit=5)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].subject, "URGENTE: Revisión de contrato")
        self.assertTrue(res[0].is_important)
        self.assertFalse(res[0].is_promotional)

    async def test_crud_get_recent_emails(self):
        """Verifica que get_recent_emails respete el filtro de exclusión de promociones."""
        mock_db = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [self.mail_regular, self.mail_important]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        res = await get_recent_emails(mock_db, target_date=date(2026, 11, 21), limit=10, include_promotional=False)
        self.assertEqual(len(res), 2)
        self.assertNotIn(self.mail_promo, res)

    @patch("tools.email_tools.sync_latest_emails_metadata", new_callable=AsyncMock)
    @patch("tools.email_tools.get_important_emails", new_callable=AsyncMock)
    @patch("tools.email_tools.AsyncSessionLocal")
    async def test_check_important_emails_tool_with_results(self, mock_session_local, mock_get_imp, mock_sync):
        """Verifica el formato del texto de check_important_emails_tool cuando hay correos importantes."""
        mock_sync.return_value = 0
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_get_imp.return_value = [self.mail_important]

        output = await check_important_emails_tool(date_str="2026-11-21")
        self.assertIn("Se encontraron 1 correos importantes", output)
        self.assertIn("jefe@empresa.com", output)
        self.assertIn("URGENTE: Revisión de contrato", output)

    @patch("tools.email_tools.sync_latest_emails_metadata", new_callable=AsyncMock)
    @patch("tools.email_tools.get_important_emails", new_callable=AsyncMock)
    @patch("tools.email_tools.AsyncSessionLocal")
    async def test_check_important_emails_tool_empty(self, mock_session_local, mock_get_imp, mock_sync):
        """Verifica el mensaje devuelto cuando no hay correos importantes."""
        mock_sync.return_value = 0
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_get_imp.return_value = []

        output = await check_important_emails_tool(date_str="2026-11-21")
        self.assertIn("No se han registrado correos importantes", output)

    @patch("tools.email_tools.sync_latest_emails_metadata", new_callable=AsyncMock)
    @patch("tools.email_tools.get_recent_emails", new_callable=AsyncMock)
    @patch("tools.email_tools.AsyncSessionLocal")
    async def test_get_recent_emails_summary_tool(self, mock_session_local, mock_get_rec, mock_sync):
        """Verifica que el resumen agrupe importantes y otros correos correctamente."""
        mock_sync.return_value = 0
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_get_rec.return_value = [self.mail_important, self.mail_regular]

        output = await get_recent_emails_summary_tool(limit=5, date_str="2026-11-21")
        self.assertIn("Total: 2", output)
        self.assertIn("Correos Importantes / Prioritarios:", output)
        self.assertIn("jefe@empresa.com", output)
        self.assertIn("Otros correos relevantes:", output)
        self.assertIn("soporte@proveedor.com", output)

    @patch("agent.engine.check_important_emails_tool", new_callable=AsyncMock)
    async def test_execute_tool_call_check_important_emails(self, mock_tool):
        """Verifica que el despachador de engine.py invoque check_important_emails_tool."""
        mock_tool.return_value = "Resultado test importante"
        res = await execute_tool_call("check_important_emails", {"date_str": "2026-11-21"})
        mock_tool.assert_awaited_once_with("2026-11-21")
        self.assertEqual(res, "Resultado test importante")

    @patch("agent.engine.get_recent_emails_summary_tool", new_callable=AsyncMock)
    async def test_execute_tool_call_get_recent_emails_summary(self, mock_tool):
        """Verifica que el despachador de engine.py invoque get_recent_emails_summary_tool."""
        mock_tool.return_value = "Resultado resumen"
        res = await execute_tool_call("get_recent_emails_summary", {"limit": 5, "date_str": "2026-11-21"})
        mock_tool.assert_awaited_once_with(5, "2026-11-21")
        self.assertEqual(res, "Resultado resumen")


if __name__ == "__main__":
    unittest.main()
