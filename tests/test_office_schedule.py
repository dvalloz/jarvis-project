import unittest
from datetime import date
from unittest.mock import AsyncMock, patch
from database.crud import (
    get_week_office_dates,
    get_weekly_office_decision
)

class TestOfficeScheduleLogic(unittest.IsolatedAsyncioTestCase):
    """Pruebas unitarias para la lógica de registro y consulta de asistencia a la oficina."""

    def test_get_week_office_dates_from_tuesday(self):
        """Verifica que desde un martes se calculen correctamente el jueves y viernes de esa semana."""
        tuesday = date(2026, 11, 17) # Martes
        thu, fri = get_week_office_dates(tuesday)

        self.assertEqual(thu, date(2026, 11, 19)) # Jueves
        self.assertEqual(fri, date(2026, 11, 20)) # Viernes

    def test_get_week_office_dates_from_wednesday(self):
        """Verifica que desde un miércoles se calculen correctamente el jueves y viernes de esa semana."""
        wednesday = date(2026, 11, 18) # Miércoles
        thu, fri = get_week_office_dates(wednesday)

        self.assertEqual(thu, date(2026, 11, 19)) # Jueves
        self.assertEqual(fri, date(2026, 11, 20)) # Viernes

    @patch("database.crud.get_office_attendance")
    async def test_get_weekly_office_decision_thursday(self, mock_get_attendance):
        """Verifica decisión confirmada para ir el jueves."""
        # thursday=True, friday=False
        mock_get_attendance.side_effect = lambda db, d: True if d.weekday() == 3 else False

        mock_db = AsyncMock()
        today = date(2026, 11, 17) # Martes
        decision = await get_weekly_office_decision(mock_db, today)

        self.assertEqual(decision, "thursday")

    @patch("database.crud.get_office_attendance")
    async def test_get_weekly_office_decision_friday(self, mock_get_attendance):
        """Verifica decisión confirmada para ir el viernes."""
        # thursday=False, friday=True
        mock_get_attendance.side_effect = lambda db, d: True if d.weekday() == 4 else False

        mock_db = AsyncMock()
        today = date(2026, 11, 17) # Martes
        decision = await get_weekly_office_decision(mock_db, today)

        self.assertEqual(decision, "friday")

    @patch("database.crud.get_office_attendance")
    async def test_get_weekly_office_decision_none(self, mock_get_attendance):
        """Verifica decisión confirmada de no asistir ningún día (teletrabajo)."""
        # thursday=False, friday=False
        mock_get_attendance.return_value = False

        mock_db = AsyncMock()
        today = date(2026, 11, 17) # Martes
        decision = await get_weekly_office_decision(mock_db, today)

        self.assertEqual(decision, "none")

    @patch("database.crud.get_office_attendance")
    async def test_get_weekly_office_decision_undecided(self, mock_get_attendance):
        """Verifica cuando aún no se ha decidido o se seleccionó 'No lo sé'."""
        # thursday=None, friday=None
        mock_get_attendance.return_value = None

        mock_db = AsyncMock()
        today = date(2026, 11, 17) # Martes
        decision = await get_weekly_office_decision(mock_db, today)

        self.assertIsNone(decision, "Debe ser None para indicar que sigue pendiente preguntar")

if __name__ == "__main__":
    unittest.main()
