import unittest
from unittest.mock import patch, MagicMock

from scripts.github_release_parser import GitHubReleaseError, GitHubReleaseParser


class TestGitHubReleaseParser(unittest.TestCase):
    """Набор unit-тестов для проверки логики парсера."""

    def setUp(self) -> None:
        self.parser = GitHubReleaseParser()
        self.valid_url = "https://github.com/ez404-36/time_tracker/releases"

    def test_extract_repo_info_success(self) -> None:
        """Проверка корректного извлечения владельца и репозитория."""
        result = self.parser._extract_repo_info(self.valid_url)
        self.assertEqual(result['owner'], 'ez404-36')
        self.assertEqual(result['repo'], 'time_tracker')

    def test_extract_repo_info_invalid_url(self) -> None:
        """Проверка обработки некорректного URL."""
        with self.assertRaises(GitHubReleaseError):
            self.parser._extract_repo_info("https://google.com")

    @patch('requests.get')
    def test_get_latest_release_tag_success(self, mock_get: MagicMock) -> None:
        """Проверка успешного получения тега при валидном API ответе."""
        # Имитация ответа API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"tag_name": "v1.2.3"},
            {"tag_name": "v1.2.2"}
        ]
        mock_get.return_value = mock_response

        version = self.parser.get_latest_release_tag(self.valid_url)
        self.assertEqual(version, "v1.2.3")

    @patch('requests.get')
    def test_get_latest_release_tag_404(self, mock_get: MagicMock) -> None:
        """Проверка обработки ошибки 404 (репозиторий не найден)."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with self.assertRaises(GitHubReleaseError) as context:
            self.parser.get_latest_release_tag(self.valid_url)
        self.assertIn("не найдены", str(context.exception))

    @patch('requests.get')
    def test_get_latest_release_empty_list(self, mock_get: MagicMock) -> None:
        """Проверка ситуации, когда релизов в репозитории нет."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        with self.assertRaises(GitHubReleaseError) as context:
            self.parser.get_latest_release_tag(self.valid_url)
        self.assertIn("список релизов пуст", str(context.exception).lower())

if __name__ == "__main__":
    unittest.main()
