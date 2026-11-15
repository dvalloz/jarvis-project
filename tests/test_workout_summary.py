import unittest
from unittest.mock import AsyncMock, MagicMock
from database.crud import get_monthly_workout_summary

class TestWorkoutMonthlySummary(unittest.IsolatedAsyncioTestCase):
    """Pruebas unitarias para la segregación de días de descanso en el resumen mensual."""

    async def test_get_monthly_workout_summary_separates_rest_days(self):
        """
        Verifica el caso específico reportado en el Issue #4:
        7 Descansos, 3 Push, 1 Escalada, 1 Full-Body, 3 Legs, 4 Pull.
        Total físico debe ser 12 (no 19) y días de descanso debe ser 7.
        """
        mock_db = AsyncMock()
        mock_res = MagicMock()
        mock_res.fetchall.return_value = [
            ("Descanso", 7),
            ("Empuje (Push)", 3),
            ("Escalada", 1),
            ("Full-Body", 1),
            ("Pierna (Legs)", 3),
            ("Tirón (Pull)", 4),
        ]
        mock_db.execute.return_value = mock_res

        summary = await get_monthly_workout_summary(mock_db, year=2026, month=10)

        self.assertEqual(summary["year"], 2026)
        self.assertEqual(summary["month"], 10)
        self.assertEqual(summary["total_workouts"], 12, "El total de sesiones debe ser 12 excluyendo descansos")
        self.assertEqual(summary["rest_days"], 7, "Los días de descanso deben contabilizarse en 7")
        self.assertNotIn("Descanso", summary["breakdown"], "Descanso no debe figurar en el desglose de rutinas físicas")
        self.assertEqual(summary["breakdown"]["Empuje (Push)"], 3)
        self.assertEqual(summary["breakdown"]["Escalada"], 1)
        self.assertEqual(summary["breakdown"]["Full-Body"], 1)
        self.assertEqual(summary["breakdown"]["Pierna (Legs)"], 3)
        self.assertEqual(summary["breakdown"]["Tirón (Pull)"], 4)

    async def test_get_monthly_workout_summary_no_rest_days(self):
        """Verifica el cálculo cuando no hay registros de descanso."""
        mock_db = AsyncMock()
        mock_res = MagicMock()
        mock_res.fetchall.return_value = [
            ("Empuje (Push)", 4),
            ("Tirón (Pull)", 4),
        ]
        mock_db.execute.return_value = mock_res

        summary = await get_monthly_workout_summary(mock_db, year=2026, month=11)

        self.assertEqual(summary["total_workouts"], 8)
        self.assertEqual(summary["rest_days"], 0)
        self.assertEqual(summary["breakdown"], {"Empuje (Push)": 4, "Tirón (Pull)": 4})

    async def test_get_monthly_workout_summary_only_rest_days(self):
        """Verifica el cálculo cuando únicamente hubo días de descanso."""
        mock_db = AsyncMock()
        mock_res = MagicMock()
        mock_res.fetchall.return_value = [
            ("Día de Descanso", 5),
        ]
        mock_db.execute.return_value = mock_res

        summary = await get_monthly_workout_summary(mock_db, year=2026, month=11)

        self.assertEqual(summary["total_workouts"], 0)
        self.assertEqual(summary["rest_days"], 5)
        self.assertEqual(summary["breakdown"], {})

if __name__ == "__main__":
    unittest.main()
