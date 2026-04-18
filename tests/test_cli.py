from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from tripplanner.cli import cli
from tripplanner.core.models import Attraction, Location


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _mock_attraction(name: str = "Tower", xid: str = "N1") -> Attraction:
    return Attraction(
        xid=xid,
        name=name,
        location=Location(longitude=139.74, latitude=35.65),
        kinds="towers",
        rating=4.5,
    )


class TestPlanHelp:
    def test_plan_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["plan", "--help"])
        assert result.exit_code == 0
        assert "--city" in result.output
        assert "--dry-run" in result.output
        assert "--interests" in result.output

    def test_missing_city(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["plan"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "--city" in result.output


class TestPlanDryRun:
    @patch("tripplanner.cli.OpenTripMapClient")
    def test_dry_run_success(self, mock_client_cls: AsyncMock, runner: CliRunner) -> None:
        mock_instance = AsyncMock()
        mock_instance.geoname.return_value = (35.6762, 139.6503)
        mock_instance.search_places.return_value = [_mock_attraction("Tokyo Tower")]
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_instance

        result = runner.invoke(cli, ["plan", "--city", "Tokyo", "--dry-run"])
        assert result.exit_code == 0
        assert "Tokyo" in result.output
        assert "Tokyo Tower" in result.output

    @patch("tripplanner.cli.OpenTripMapClient")
    def test_dry_run_no_results(self, mock_client_cls: AsyncMock, runner: CliRunner) -> None:
        mock_instance = AsyncMock()
        mock_instance.geoname.return_value = (35.6762, 139.6503)
        mock_instance.search_places.return_value = []
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_instance

        result = runner.invoke(cli, ["plan", "--city", "Tokyo", "--dry-run"])
        assert result.exit_code == 0
        assert "No places found" in result.output

    @patch("tripplanner.cli.OpenTripMapClient")
    def test_dry_run_city_not_found(self, mock_client_cls: AsyncMock, runner: CliRunner) -> None:
        mock_instance = AsyncMock()
        mock_instance.geoname.return_value = None
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_instance

        result = runner.invoke(cli, ["plan", "--city", "InvalidCity", "--dry-run"])
        assert result.exit_code == 0
        assert "Could not find city" in result.output


class TestPlanDates:
    def test_invalid_date_format(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["plan", "--city", "Tokyo", "--dates", "not-a-date", "2026-04-13"])
        assert result.exit_code != 0
        assert "Invalid date" in result.output

    def test_end_before_start(self, runner: CliRunner) -> None:
        result = runner.invoke(
            cli, ["plan", "--city", "Tokyo", "--dates", "2026-04-13", "2026-04-10"]
        )
        assert result.exit_code != 0
        assert "after start" in result.output

    @patch("tripplanner.cli.OpenTripMapClient")
    @patch("tripplanner.cli.db_save", new_callable=AsyncMock, return_value="test-id")
    def test_interests_split(
        self, mock_save: AsyncMock, mock_client_cls: AsyncMock, runner: CliRunner
    ) -> None:
        mock_instance = AsyncMock()
        mock_instance.geoname.return_value = (35.6762, 139.6503)
        mock_instance.search_city.return_value = [_mock_attraction("Museum")]
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_instance

        with patch("tripplanner.cli._get_session", new_callable=AsyncMock) as mock_get_session:
            mock_session = AsyncMock()
            mock_factory = MagicMock()
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_get_session.return_value = mock_factory

            result = runner.invoke(cli, ["plan", "--city", "Tokyo", "--interests", "museums,food"])

        assert result.exit_code == 0
