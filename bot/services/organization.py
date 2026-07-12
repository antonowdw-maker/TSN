"""Форматирование контактных данных и графиков работы организации для бота и AI."""

from __future__ import annotations

from pathlib import Path

from bot.config import load_json


class OrganizationService:
    """Сервис для чтения данных организации из JSON и форматирования текстовых блоков."""

    def __init__(self, organization_path: Path) -> None:
        self._data = load_json(organization_path)

    @property
    def data(self) -> dict:
        """Возвращает сырые данные организации из JSON."""
        return self._data

    def format_contacts(self) -> str:
        """Формирует текст с контактами руководства и офиса для команды /contacts."""
        org = self._data
        chairman = org["management"]["chairman"]
        deputy = org["management"]["deputy_chairman"]

        lines = [
            f"🏠 *{org['name']}*",
            f"📍 {org['address']}",
            f"📧 {org['email']}",
            "",
            "👤 *Руководство:*",
            f"• {chairman['position']}: {chairman['name']}",
            f"  📞 {chairman['phone']}",
            f"  🕐 Приём: {chairman['reception_hours']}",
            "",
            f"• {deputy['position']}: {deputy['name']}",
            f"  📞 {deputy['phone']}",
            f"  🕐 Приём: {deputy['reception_hours']}",
            "",
            f"🕐 *Часы работы офиса:* {org['office_hours']}",
            "",
            f"ℹ️ _{org['legal_notes']}_",
        ]
        return "\n".join(lines)

    def format_dispatcher(self) -> str:
        """Формирует текст с телефонами и режимом работы диспетчерской."""
        dispatcher = self._data["dispatcher"]
        org_name = self._data["name"]
        return (
            f"📞 *Диспетчерская {org_name}*\n\n"
            f"☎️ Основной телефон: `{dispatcher['phone']}`\n"
            f"🕐 Режим работы: {dispatcher['schedule']}\n\n"
            f"🚨 *Аварийная служба:* `{dispatcher['emergency_phone']}`\n"
            f"⏰ {dispatcher['emergency_schedule']}\n\n"
            f"_{dispatcher['description']}_"
        )

    def format_schedule(self) -> str:
        """Формирует текст с графиком работы сотрудников и офиса."""
        lines = [
            "📅 *График работы сотрудников ТСН*\n",
            f"🏢 *Офис:* {self._data['office_hours']}\n",
        ]
        for staff in self._data["staff_schedule"]:
            lines.extend(
                [
                    f"👔 *{staff['position']}*",
                    f"   {staff['name']}",
                    f"   🕐 {staff['schedule']}",
                    f"   📞 {staff['phone']}",
                    f"   _{staff['notes']}_",
                    "",
                ]
            )
        lines.append(f"ℹ️ _{self._data['legal_notes']}_")
        return "\n".join(lines)

    def context_for_ai(self) -> str:
        """Собирает текстовый контекст об организации для передачи в AI-промпт."""
        org = self._data
        staff_lines = []
        for staff in org["staff_schedule"]:
            staff_lines.append(
                f"- {staff['position']} ({staff['name']}): {staff['schedule']}, "
                f"тел. {staff['phone']}"
            )

        chairman = org["management"]["chairman"]
        dispatcher = org["dispatcher"]

        return (
            f"Организация: {org['name']}\n"
            f"Адрес: {org['address']}\n"
            f"E-mail: {org['email']}\n"
            f"Председатель: {chairman['name']}, тел. {chairman['phone']}, "
            f"приём: {chairman['reception_hours']}\n"
            f"Диспетчерская: {dispatcher['phone']}, режим: {dispatcher['schedule']}\n"
            f"Аварийный телефон: {dispatcher['emergency_phone']}\n"
            f"Часы работы офиса: {org['office_hours']}\n"
            "Сотрудники:\n"
            + "\n".join(staff_lines)
        )
