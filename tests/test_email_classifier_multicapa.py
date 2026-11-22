"""
Tests para el clasificador de emails multicapa mejorado (Issue #18).
Cubre: Capa 2 (reglas duras), Capa 3 (heurística bilingüe),
pipeline triage_email completo y el nuevo campo user_corrected.
"""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from agent.email_classifier import (
    apply_hard_rules,
    evaluate_heuristic_multilingual,
    triage_email,
    _load_email_rules,
    EMAIL_RULES,
)


class TestLayer2HardRules(unittest.TestCase):
    """Tests para Capa 2: reglas duras VIP / bloqueados."""

    def test_vip_sender_exact_match(self):
        """Remitente VIP exacto → importante."""
        result = apply_hard_rules("informacion@thebigschool.com", "Clase de Python")
        self.assertIsNotNone(result)
        self.assertTrue(result["is_important"])
        self.assertEqual(result["layer"], 2)

    def test_vip_sender_commitacademy(self):
        """Remitente VIP de Commit Academy → importante."""
        result = apply_hard_rules("hola@commitacademy.io", "Tu próxima clase")
        self.assertIsNotNone(result)
        self.assertTrue(result["is_important"])

    def test_vip_sender_newsletter_commitacademy(self):
        """Remitente newsletter Commit Academy → importante."""
        result = apply_hard_rules("marti.cristobal@newsletter.commitacademy.io", "Tips de esta semana")
        self.assertIsNotNone(result)
        self.assertTrue(result["is_important"])

    def test_vip_subject_reservation(self):
        """Asunto de reserva → importante."""
        result = apply_hard_rules("noreply@booking.com", "Confirmación de reserva en Hotel Ritz")
        self.assertIsNotNone(result)
        self.assertTrue(result["is_important"])

    def test_vip_subject_flight(self):
        """Asunto de vuelo → importante."""
        result = apply_hard_rules("no-reply@iberia.com", "Tu billete de avión para MAD-BCN")
        self.assertIsNotNone(result)
        self.assertTrue(result["is_important"])

    def test_blocked_sender_github(self):
        """GitHub notifications → bloqueado."""
        result = apply_hard_rules("noreply@github.com", "[GitHub] New pull request")
        self.assertIsNotNone(result)
        self.assertFalse(result["is_important"])
        self.assertEqual(result["layer"], 2)

    def test_blocked_sender_linkedin(self):
        """LinkedIn → bloqueado."""
        result = apply_hard_rules("notifications@linkedin.com", "Tu resumen semanal de LinkedIn")
        self.assertIsNotNone(result)
        self.assertFalse(result["is_important"])

    def test_blocked_subject_job_offer_es(self):
        """Oferta de empleo en español → bloqueado."""
        result = apply_hard_rules("recruiter@empresa.com", "Oferta de empleo: Senior Developer")
        self.assertIsNotNone(result)
        self.assertFalse(result["is_important"])

    def test_blocked_subject_job_offer_en(self):
        """Job offer en inglés → bloqueado."""
        result = apply_hard_rules("talent@company.com", "New job offer: We love your profile")
        self.assertIsNotNone(result)
        self.assertFalse(result["is_important"])

    def test_blocked_subject_github_prefix(self):
        """Asunto [GitHub] → bloqueado."""
        result = apply_hard_rules("random@example.com", "[GitHub] Someone starred your repo")
        self.assertIsNotNone(result)
        self.assertFalse(result["is_important"])

    def test_no_rule_returns_none(self):
        """Email sin regla dura → None (pasa a Capa 3)."""
        result = apply_hard_rules("amigo@gmail.com", "Quedamos el sábado?")
        self.assertIsNone(result)

    def test_vip_booking_sender_pattern(self):
        """Patrón de remitente Booking.com → importante."""
        result = apply_hard_rules("confirmations@booking.com", "Tu reserva de hotel está confirmada")
        self.assertIsNotNone(result)
        self.assertTrue(result["is_important"])


class TestLayer3Heuristic(unittest.TestCase):
    """Tests para Capa 3: heurística bilingüe mejorada."""

    def test_otp_code_not_important(self):
        """Email con código OTP → no importante (el número puede ir antes o después)."""
        # Caso 1: "código XXXXX"
        result1 = evaluate_heuristic_multilingual(
            "noreply@google.com", "Tu código de verificación es 483921"
        )
        self.assertIsNotNone(result1)
        self.assertFalse(result1["is_important"])
        self.assertEqual(result1["layer"], 3)
        # Caso 2: "XXXXX código"
        result2 = evaluate_heuristic_multilingual(
            "noreply@google.com", "483921 es tu código de acceso"
        )
        self.assertIsNotNone(result2)
        self.assertFalse(result2["is_important"])

    def test_two_high_signals_important(self):
        """Dos señales HIGH → importante sin LLM."""
        result = evaluate_heuristic_multilingual(
            "banco@bbva.es", "Urgente: transferencia bancaria pendiente de autorizar"
        )
        self.assertIsNotNone(result)
        self.assertTrue(result["is_important"])
        self.assertEqual(result["layer"], 3)

    def test_monetary_amount_signal(self):
        """Importe monetario en asunto → señal HIGH."""
        result = evaluate_heuristic_multilingual(
            "facturas@empresa.es", "Factura €1.250 — vencimiento esta semana"
        )
        self.assertIsNotNone(result)
        self.assertTrue(result["is_important"])

    def test_hacienda_irpf_important(self):
        """Hacienda + IRPF → señal HIGH doble → importante."""
        result = evaluate_heuristic_multilingual(
            "agencia_tributaria@aeat.es", "Declaración del IRPF: plazo hasta el 30 de junio"
        )
        self.assertIsNotNone(result)
        self.assertTrue(result["is_important"])

    def test_english_urgent_payment(self):
        """Señales en inglés: urgent + payment → importante."""
        result = evaluate_heuristic_multilingual(
            "billing@service.com", "URGENT: Payment required for your account"
        )
        self.assertIsNotNone(result)
        self.assertTrue(result["is_important"])

    def test_single_signal_passes_to_llm(self):
        """Solo una señal → retorna None para pasar a Capa 4."""
        result = evaluate_heuristic_multilingual(
            "amigo@gmail.com", "Hey, ¿quedamos mañana?"
        )
        self.assertIsNone(result)

    def test_no_signals_passes_to_llm(self):
        """Sin señales → retorna None para pasar a Capa 4."""
        result = evaluate_heuristic_multilingual(
            "newsletter@tech.com", "Top 5 noticias de la semana"
        )
        self.assertIsNone(result)


class TestTriagePipeline(unittest.IsolatedAsyncioTestCase):
    """Tests de integración para el pipeline completo triage_email."""

    async def test_promo_email_vip_rescued(self):
        """Email en Promociones de un VIP → rescatado como importante."""
        email_metadata = {
            "message_id": "promo_vip_001",
            "sender": "informacion@thebigschool.com",
            "subject": "Tu clase de esta semana",
            "is_promotional": True,
            "labels": ["CATEGORY_PROMOTIONS"],
        }
        result = await triage_email(email_metadata)
        self.assertTrue(result["is_important"])
        self.assertTrue(result["is_promotional"])

    async def test_promo_email_non_vip_discarded(self):
        """Email en Promociones sin regla VIP → descartado."""
        email_metadata = {
            "message_id": "promo_nonvip_001",
            "sender": "marketing@tienda.com",
            "subject": "¡50% de descuento en todo!",
            "is_promotional": True,
            "labels": ["CATEGORY_PROMOTIONS"],
        }
        result = await triage_email(email_metadata)
        self.assertFalse(result["is_important"])
        self.assertTrue(result["is_promotional"])

    async def test_blocked_sender_pipeline(self):
        """Email de remitente bloqueado → no importante (Capa 2)."""
        email_metadata = {
            "message_id": "blocked_001",
            "sender": "noreply@github.com",
            "subject": "[GitHub] New issue on your repo",
            "is_promotional": False,
        }
        result = await triage_email(email_metadata)
        self.assertFalse(result["is_important"])
        self.assertEqual(result.get("layer"), 2)

    async def test_vip_sender_pipeline(self):
        """Email de remitente VIP → importante (Capa 2)."""
        email_metadata = {
            "message_id": "vip_001",
            "sender": "hola@commitacademy.io",
            "subject": "Tu acceso al curso de Docker",
            "is_promotional": False,
        }
        result = await triage_email(email_metadata)
        self.assertTrue(result["is_important"])
        self.assertEqual(result.get("layer"), 2)

    async def test_heuristic_otp_not_important(self):
        """OTP detectado en Capa 3 → no importante."""
        email_metadata = {
            "message_id": "otp_001",
            "sender": "auth@google.com",
            # El código viene DESPUÉS de "código": matchea el nuevo regex bidireccional
            "subject": "483921 es tu código de verificación para acceder",
            "is_promotional": False,
        }
        result = await triage_email(email_metadata)
        self.assertFalse(result["is_important"])
        self.assertEqual(result.get("layer"), 3)

    @patch("agent.email_classifier.evaluate_email_importance_llm", new_callable=AsyncMock)
    async def test_ambiguous_email_reaches_llm(self, mock_llm):
        """Email ambiguo sin señales duras ni heurísticas → llega a Capa 4 LLM."""
        mock_llm.return_value = {
            "is_important": True,
            "priority": "ALTA",
            "reason": "LLM clasificó como importante",
            "layer": 4
        }
        email_metadata = {
            "message_id": "ambiguous_001",
            "sender": "persona@ejemplo.com",
            "subject": "Reunión el lunes",
            "is_promotional": False,
        }
        result = await triage_email(email_metadata)
        mock_llm.assert_called_once()
        self.assertEqual(result.get("layer"), 4)

    async def test_pipeline_returns_layer_field(self):
        """El resultado del pipeline incluye siempre el campo 'layer'."""
        email_metadata = {
            "message_id": "layer_test_001",
            "sender": "noreply@github.com",
            "subject": "[GitHub] PR merged",
            "is_promotional": False,
        }
        result = await triage_email(email_metadata)
        self.assertIn("layer", result)

    async def test_recent_corrections_passed_to_llm(self):
        """Las correcciones recientes se pasan correctamente al LLM."""
        corrections = [
            {"sender": "spam@example.com", "subject": "Oferta", "was_important": False}
        ]
        email_metadata = {
            "message_id": "correction_test_001",
            "sender": "persona@ejemplo.com",
            "subject": "Hola qué tal",
            "is_promotional": False,
        }
        # Solo verificamos que el pipeline acepta el parámetro sin error
        with patch("agent.email_classifier.evaluate_email_importance_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "is_important": False, "priority": "BAJA",
                "reason": "test", "layer": 4
            }
            result = await triage_email(email_metadata, recent_corrections=corrections)
            # Verificar que se pasaron las correcciones al LLM
            call_args = mock_llm.call_args
            self.assertEqual(call_args[1].get("recent_corrections") or call_args[0][2], corrections)


class TestEmailRulesLoading(unittest.TestCase):
    """Tests para la carga de email_rules.json."""

    def test_rules_file_loaded(self):
        """El fichero email_rules.json se carga correctamente."""
        self.assertIsInstance(EMAIL_RULES, dict)

    def test_vip_senders_present(self):
        """Los remitentes VIP configurados están en las reglas."""
        vip = EMAIL_RULES.get("vip_senders", [])
        self.assertIn("informacion@thebigschool.com", vip)
        self.assertIn("hola@commitacademy.io", vip)
        self.assertIn("marti.cristobal@newsletter.commitacademy.io", vip)

    def test_blocked_senders_present(self):
        """Los remitentes bloqueados están en las reglas."""
        blocked = EMAIL_RULES.get("blocked_senders", [])
        self.assertIn("noreply@github.com", blocked)
        self.assertIn("notifications@linkedin.com", blocked)

    def test_vip_subject_patterns_present(self):
        """Los patrones de asuntos VIP (reservas) están presentes."""
        patterns = EMAIL_RULES.get("vip_subject_patterns", [])
        self.assertGreater(len(patterns), 0)

    def test_blocked_subject_patterns_present(self):
        """Los patrones de asuntos bloqueados (ofertas empleo) están presentes."""
        patterns = EMAIL_RULES.get("blocked_subject_patterns", [])
        self.assertGreater(len(patterns), 0)


if __name__ == "__main__":
    unittest.main()
