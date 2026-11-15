import unittest
from datetime import datetime, timezone, date, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from tools.email_tools import parse_email_metadata
from database.models import EmailLog
from database.crud import (
    create_or_get_email_log,
    get_email_log_by_message_id,
    get_pending_alert_emails,
    mark_email_alert_sent,
    get_unsummarized_emails_for_date,
    mark_emails_night_summarized
)

class TestEmailMetadataParsing(unittest.TestCase):
    """Pruebas unitarias para el parseo seguro y determinista de metadatos de email."""

    def test_parse_standard_email(self):
        """Verifica el parseo de un correo normal sin cabeceras de publicidad."""
        raw = {
            "id": "18c21a4f91001",
            "threadId": "t_001",
            "labelIds": ["INBOX", "UNREAD"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "Banco Santander <notificaciones@santander.es>"},
                    {"name": "Subject", "value": "Transferencia pendiente de autorizar"},
                    {"name": "Date", "value": "Mon, 15 Nov 2026 10:30:00 +0100"}
                ]
            }
        }
        parsed = parse_email_metadata(raw)
        self.assertEqual(parsed["message_id"], "18c21a4f91001")
        self.assertEqual(parsed["sender"], "Banco Santander <notificaciones@santander.es>")
        self.assertEqual(parsed["subject"], "Transferencia pendiente de autorizar")
        self.assertFalse(parsed["is_promotional"])
        self.assertIsNotNone(parsed["received_at"])

    def test_parse_promotional_email_list_unsubscribe(self):
        """Verifica que un email con cabecera List-Unsubscribe se marque como promocional."""
        raw = {
            "id": "18c21a4f91002",
            "threadId": "t_002",
            "labelIds": ["INBOX", "UNREAD"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "Nike Store <news@nike.com>"},
                    {"name": "Subject", "value": "30% de descuento en zapatillas"},
                    {"name": "List-Unsubscribe", "value": "<mailto:unsub@nike.com>"},
                    {"name": "Date", "value": "Mon, 15 Nov 2026 09:00:00 +0000"}
                ]
            }
        }
        parsed = parse_email_metadata(raw)
        self.assertTrue(parsed["is_promotional"], "Emails con List-Unsubscribe deben considerarse promocionales")

    def test_parse_promotional_email_precedence_bulk(self):
        """Verifica que un email con Precedence: bulk se marque como promocional."""
        raw = {
            "id": "18c21a4f91003",
            "threadId": "t_003",
            "labelIds": ["INBOX", "UNREAD"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "Tech Newsletter <info@techdaily.com>"},
                    {"name": "Subject", "value": "Noticias tech de la semana"},
                    {"name": "Precedence", "value": "bulk"},
                    {"name": "Date", "value": "Mon, 15 Nov 2026 08:00:00 +0000"}
                ]
            }
        }
        parsed = parse_email_metadata(raw)
        self.assertTrue(parsed["is_promotional"], "Emails con Precedence bulk deben ser promocionales")

    def test_parse_promotional_label(self):
        """Verifica que un email etiquetado con CATEGORY_PROMOTIONS se detecte como promocional."""
        raw = {
            "id": "18c21a4f91004",
            "threadId": "t_004",
            "labelIds": ["INBOX", "UNREAD", "CATEGORY_PROMOTIONS"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "Ofertas <ofertas@tienda.com>"},
                    {"name": "Subject", "value": "Descuentos exclusivos"},
                    {"name": "Date", "value": "Mon, 15 Nov 2026 08:00:00 +0000"}
                ]
            }
        }
        parsed = parse_email_metadata(raw)
        self.assertTrue(parsed["is_promotional"])


class TestEmailLogCRUD(unittest.IsolatedAsyncioTestCase):
    """Pruebas unitarias para las operaciones CRUD y reglas de persistencia de EmailLog."""

    async def test_create_or_get_email_log_idempotency(self):
        """Verifica que insertar un mensaje ya existente no duplique registros (idempotencia)."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_res = MagicMock()
        
        # Simula que no existe en el primer intento
        mock_res.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_res

        now = datetime.now(timezone.utc)
        email, created = await create_or_get_email_log(
            db=mock_db,
            message_id="msg_test_123",
            sender="jefe@empresa.com",
            subject="Reunión urgente",
            received_at=now,
            is_promotional=False,
            is_important=True
        )

        self.assertTrue(created)
        self.assertEqual(email.message_id, "msg_test_123")
        self.assertEqual(email.sender, "jefe@empresa.com")
        self.assertTrue(email.is_important)
        self.assertFalse(email.alert_sent)

        # Ahora simula que ya existe en el segundo intento
        existing_email = EmailLog(
            id=1,
            message_id="msg_test_123",
            sender="jefe@empresa.com",
            subject="Reunión urgente",
            received_at=now,
            is_important=True
        )
        mock_res.scalar_one_or_none.return_value = existing_email
        email2, created2 = await create_or_get_email_log(
            db=mock_db,
            message_id="msg_test_123",
            sender="jefe@empresa.com",
            subject="Reunión urgente",
            received_at=now
        )
        self.assertFalse(created2, "Si ya existe en base de datos no debe recrearse")
        self.assertEqual(email2.id, 1)

    async def test_get_pending_alert_emails(self):
        """Verifica la consulta de correos importantes pendientes de alerta."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_res = MagicMock()
        pending_item = EmailLog(
            id=10,
            message_id="msg_urgent_1",
            sender="alerta@banco.es",
            subject="Movimiento no reconocido",
            received_at=datetime.now(timezone.utc),
            is_important=True,
            is_promotional=False,
            alert_sent=False
        )
        mock_res.scalars.return_value.all.return_value = [pending_item]
        mock_db.execute.return_value = mock_res

        results = await get_pending_alert_emails(mock_db)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].message_id, "msg_urgent_1")

if __name__ == "__main__":
    unittest.main()
