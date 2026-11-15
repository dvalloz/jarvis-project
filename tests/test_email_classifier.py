import unittest
from unittest.mock import AsyncMock, patch, MagicMock

from agent.email_classifier import (
    evaluate_email_importance_heuristic,
    evaluate_email_importance_llm,
    triage_email
)

class TestEmailClassifier(unittest.IsolatedAsyncioTestCase):
    """Pruebas unitarias para el clasificador de emails Zero-PII."""

    def test_heuristic_critical_detection(self):
        """Verifica que la heurística detecte palabras clave de alta prioridad."""
        res1 = evaluate_email_importance_heuristic(
            sender="Banco Santander <notificaciones@santander.es>",
            subject="Confirmación de transferencia inmediata"
        )
        self.assertTrue(res1["is_important"])
        self.assertEqual(res1["priority"], "ALTA")

        res2 = evaluate_email_importance_heuristic(
            sender="Seguridad Google",
            subject="Alerta de seguridad: nuevo inicio de sesión"
        )
        self.assertTrue(res2["is_important"])
        self.assertEqual(res2["priority"], "ALTA")

    def test_heuristic_normal_email(self):
        """Verifica que un email común sin urgencia se clasifique como no prioritario."""
        res = evaluate_email_importance_heuristic(
            sender="Club de Lectura",
            subject="Próxima reunión mensual"
        )
        self.assertFalse(res["is_important"])
        self.assertEqual(res["priority"], "BAJA")

    @patch("agent.email_classifier.client.chat.completions.create", new_callable=AsyncMock)
    async def test_triage_promotional_skips_llm(self, mock_llm_create):
        """
        Verifica que los correos marcados como promocionales por cabeceras
        NUNCA consuman inferencia ni envíen datos a la API del LLM.
        """
        promo_metadata = {
            "message_id": "promo_1",
            "sender": "Ofertas Nike <news@nike.com>",
            "subject": "50% de descuento en ropa deportiva",
            "is_promotional": True
        }

        result = await triage_email(promo_metadata)

        self.assertFalse(result["is_important"])
        self.assertTrue(result["is_promotional"])
        # Verificar que el LLM jamás fue invocado
        mock_llm_create.assert_not_called()

    @patch("agent.email_classifier.client.chat.completions.create", new_callable=AsyncMock)
    async def test_evaluate_llm_zero_pii_payload(self, mock_llm_create):
        """
        Verifica que la llamada al LLM envíe ÚNICA Y EXCLUSIVAMENTE sender y subject.
        Cero exposición de campos corporales o datos sensibles adicionales.
        """
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"is_important": true, "priority": "ALTA", "reason": "Notificación bancaria"}'))
        ]
        mock_llm_create.return_value = mock_response

        res = await evaluate_email_importance_llm(
            sender="banco@entidad.es",
            subject="Cargo sospechoso en tarjeta"
        )

        self.assertTrue(res["is_important"])
        self.assertEqual(res["priority"], "ALTA")

        # Inspeccionar el payload enviado al LLM
        mock_llm_create.assert_called_once()
        call_kwargs = mock_llm_create.call_args[1]
        sent_messages = call_kwargs["messages"]

        user_content = next(m["content"] for m in sent_messages if m["role"] == "user")
        self.assertIn("Remitente: banco@entidad.es", user_content)
        self.assertIn("Asunto: Cargo sospechoso en tarjeta", user_content)
        # Asegurar que no hay ningún otro campo en el mensaje de usuario
        self.assertEqual(user_content, "Remitente: banco@entidad.es\nAsunto: Cargo sospechoso en tarjeta")

if __name__ == "__main__":
    unittest.main()
