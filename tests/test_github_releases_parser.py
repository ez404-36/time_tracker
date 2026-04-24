import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from scripts.github_release_parser import GitHubReleaseError, GitHubReleaseParser


class TestGitHubReleaseParser(unittest.IsolatedAsyncioTestCase):
    """
    Набор асинхронных тестов для GitHubReleaseParser.
    Использует IsolatedAsyncioTestCase для поддержки await внутри тестов.
    """

    def setUp(self) -> None:
        self.parser = GitHubReleaseParser()
        self.valid_url = "https://github.com/ez404-36/time_tracker/releases"

    def test_extract_repo_params_success(self) -> None:
        """Проверка корректного извлечения параметров из URL."""
        result = self.parser._extract_repo_info(self.valid_url)
        self.assertEqual(result['owner'], 'ez404-36')
        self.assertEqual(result['repo'], 'time_tracker')

    @patch('aiohttp.ClientSession.get')
    async def test_get_latest_release_tag_success(self, mock_get) -> None:
        """Проверка успешного получения тега (имитация асинхронного ответа)."""
        # Создаем мок для ответа (Response)
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = [{"tag_name": "v2.0.0"}]

        # Настраиваем контекстный менеджер: session.get() -> mock_response
        # В aiohttp 'async with' вызывает __aenter__
        mock_get.return_magic_for_context_manager = MagicMock()
        mock_get.return_value.__aenter__.return_value = mock_response

        version = await self.parser.get_latest_release_tag(self.valid_url)
        self.assertEqual(version, "v2.0.0")

    @patch('aiohttp.ClientSession.get')
    async def test_get_latest_release_404(self, mock_get) -> None:
        """Проверка обработки ошибки 404."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        with self.assertRaises(GitHubReleaseError) as context:
            await self.parser.get_latest_release_tag(self.valid_url)
        self.assertIn("не найдены (404)", str(context.exception))

    @patch('aiohttp.ClientSession.get')
    async def test_get_latest_release_empty(self, mock_get) -> None:
        """Проверка ситуации с пустым списком релизов."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = []
        mock_get.return_value.__aenter__.return_value = mock_response

        with self.assertRaises(GitHubReleaseError) as context:
            await self.parser.get_latest_release_tag(self.valid_url)
        self.assertIn("пуст", str(context.exception))

    @patch('aiohttp.ClientSession.get')
    async def test_network_failure(self, mock_get) -> None:
        """Проверка обработки сетевой ошибки (ClientError)."""
        import aiohttp
        # Имитируем исключение при попытке запроса
        mock_get.side_effect = aiohttp.ClientError("Connection Refused")

        with self.assertRaises(GitHubReleaseError) as context:
            await self.parser.get_latest_release_tag(self.valid_url)
        self.assertIn("Ошибка сетевого запроса", str(context.exception))


if __name__ == "__main__":
    unittest.main()
