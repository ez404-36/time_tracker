import pathlib
from typing import Union

import tomllib

from core.consts import PROJECT_DIR


def app_version_as_number(version: str) -> int:
    app_version_str = ''.join(version.split('.'))
    assert app_version_str.isdigit()
    return int(app_version_str)


class ProjectMetadataExtractor:
    """
    Сервис для извлечения метаданных из конфигурационных файлов проекта.
    """

    def __init__(self, file_path: Union[str, pathlib.Path]) -> None:
        """
        Инициализирует экстрактор путем указания пути к файлу.

        :param file_path: Путь к файлу pyproject.toml.
        """
        self.file_path = pathlib.Path(file_path)

    def get_version(self) -> str:
        """
        Извлекает текущую версию проекта из поля [project] -> version в pyproject.toml.

        :return: Строковое представление версии (например, '0.0.2').
        :raises FileNotFoundError: Если файл по указанному пути не найден.
        :raises KeyError: Если в файле отсутствует секция [project] или ключ 'version'.
        :raises ValueError: Если формат TOML некорректен.
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {self.file_path}")

        try:
            with self.file_path.open("rb") as f:
                config = tomllib.load(f)

            # Извлекаем данные согласно структуре PEP 621
            project_section = config.get("project")
            if not project_section:
                raise KeyError("Секция [project] отсутствует в pyproject.toml")

            version = project_section.get("version")
            if not version:
                raise KeyError("Ключ 'version' не найден в секции [project]")

            return str(version)

        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Ошибка парсинга TOML файла: {e}")
        except Exception as e:
            # Перехватываем непредвиденные ошибки для логгирования/обработки
            raise RuntimeError(f"Произошла ошибка при чтении метаданных: {e}")


if __name__ == "__main__":
    extractor = ProjectMetadataExtractor(PROJECT_DIR / "pyproject.toml")

    try:
        current_version = extractor.get_version()
        print(f"Текущая версия проекта: {current_version}")
    except Exception as error:
        print(f"Ошибка: {error}")
