"""Тесты сервиса OrganizationService: форматирование контактов и AI-контекста."""

from __future__ import annotations

import pytest

from bot.services.organization import OrganizationService


class TestOrganizationService:
    def test_format_contacts_contains_key_info(self, org_service: OrganizationService) -> None:
        """Проверяет, что блок контактов содержит название, e-mail и адрес."""
        text = org_service.format_contacts()
        assert "Пример" in text
        assert "info@example-tsn.local" in text
        assert "Демонстрационная" in text or "Примерный" in text

    def test_format_dispatcher_contains_phone_and_schedule(
        self, org_service: OrganizationService
    ) -> None:
        """Проверяет наличие телефона и графика в блоке диспетчерской."""
        text = org_service.format_dispatcher()
        assert "Диспетчерская" in text
        assert "+7" in text
        assert "08:00" in text or "круглосуточно" in text.lower()

    def test_format_schedule_lists_staff(self, org_service: OrganizationService) -> None:
        """Проверяет, что график содержит должности сотрудников."""
        text = org_service.format_schedule()
        assert "Бухгалтер" in text
        assert "Инженер" in text

    def test_context_for_ai_includes_organization_data(
        self, org_service: OrganizationService
    ) -> None:
        """Проверяет, что AI-контекст включает адрес и диспетчерскую, но не ИНН."""
        context = org_service.context_for_ai()
        assert "Примерный" in context
        assert "0000000000" not in context  # ИНН не передаётся в AI-контекст
        assert "Диспетчерская" in context or "диспетчер" in context.lower()

    def test_organization_data_structure(self, org_service: OrganizationService) -> None:
        """Проверяет структуру JSON и наличие обязательных полей."""
        data = org_service.data
        assert data["inn"] == "0000000000"
        assert data["management"]["chairman"]["name"] == "Уточняется у правления"
        assert len(data["staff_schedule"]) >= 3
