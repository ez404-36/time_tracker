import asyncio
import re
from typing import Dict

import aiohttp


class GitHubReleaseError(Exception):
    """Базовое исключение для ошибок парсера."""
    pass


class GitHubReleaseParser:
    """
    Класс для получения информации о релизах репозитория через GitHub API.

    Использует официальный REST API GitHub, что обеспечивает стабильность
    в отличие от классического веб-скрейпинга.
    """

    API_TEMPLATE: str = "https://api.github.com/repos/{owner}/{repo}/releases"
    URL_PATTERN: str = r"github\.com/(?P<owner>[\w-]+)/(?P<repo>[\w-]+)"

    def __init__(self, timeout: int = 10) -> None:
        """
        Инициализация парсера.

        :param timeout: Максимальное время ожидания ответа от сервера в секундах.
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    def _extract_repo_info(self, url: str) -> Dict[str, str]:
        """
        Извлекает owner и repo из URL GitHub.

        :param url: Полная ссылка на страницу релиза или репозитория.
        :return: Словарь с ключами 'owner' и 'repo'.
        :raises GitHubReleaseError: Если URL не соответствует формату GitHub.
        """
        match = re.search(self.URL_PATTERN, url)
        if not match:
            raise GitHubReleaseError(f"Некорректный URL: {url}")
        return match.groupdict()

    async def get_latest_release_tag(self, github_url: str) -> str:
        """
        Получает тег (версию) последнего релиза.

        :param github_url: Ссылка на страницу релизов GitHub.
        :return: Строка с названием тега (например, 'v1.0.0').
        :raises GitHubReleaseError: При ошибках сети или отсутствии данных.
        """
        repo_info = self._extract_repo_info(github_url)
        api_url = self.API_TEMPLATE.format(**repo_info)

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(api_url) as response:
                    if response.status == 404:
                        raise GitHubReleaseError("Репозиторий или релизы не найдены (404).")

                    response.raise_for_status()

                    releases = await response.json()

                    if not releases:
                        raise GitHubReleaseError("Список релизов пуст.")

                    # Первый элемент в списке 'releases' — это самый свежий релиз
                    return str(releases[0].get("tag_name", "Unknown"))

        except aiohttp.ClientError as e:
            raise GitHubReleaseError(f"Ошибка сетевого запроса: {e}")
        except (KeyError, IndexError, TypeError) as e:
            raise GitHubReleaseError(f"Ошибка парсинга JSON-ответа: {e}")


if __name__ == "__main__":
    # Пример использования
    TARGET_URL = "https://github.com/ez404-36/time_tracker/releases"
    parser = GitHubReleaseParser()

    latest_version = asyncio.run(parser.get_latest_release_tag(TARGET_URL))
    print(f"Актуальная версия: {latest_version}")
