import configparser
from pathlib import Path
from typing import Optional

from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    main_ini_dir: Optional[str] = None
    pseudos_list_dir: Optional[str] = None
    load_dir: Optional[str] = None
    _icons_directory: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @computed_field
    def icons_dir(self) -> str | Path:
        return self._icons_directory or Path(__file__).parent / "icons"


settings = Settings()


class AppConfig:
    """
    Обёртка над main.ini.

    Отвечает за:
    - загрузку и сохранение ini-файла;
    - координаты окна;
    - последний каталог открытия файлов.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.parser = configparser.ConfigParser()
        self._load()

    @property
    def window_position(self) -> Optional[tuple[int, int]]:
        try:
            x = self.parser.getint("window", "coord_x")
            y = self.parser.getint("window", "coord_y")
            return x, y
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return None

    @window_position.setter
    def window_position(self, pos: tuple[int, int]) -> None:
        x, y = pos
        if "window" not in self.parser:
            self.parser["window"] = {}
        self.parser.set("window", "coord_x", str(x))
        self.parser.set("window", "coord_y", str(y))
        self.save()

    # --- Каталог открытия файлов ---

    @property
    def last_open_dir(self) -> Path:
        dir_str = self.parser.get("config", "last_open_dir", fallback=str(Path.cwd()))
        return Path(dir_str)

    @last_open_dir.setter
    def last_open_dir(self, value: Path) -> None:
        if "config" not in self.parser:
            self.parser["config"] = {}
        self.parser.set("config", "last_open_dir", str(value))
        self.save()

    @property
    def pseudos_file(self) -> Optional[Path]:
        """Возвращает путь к файлу псевдонимов;
        @return: объект Path или None, если путь не задан;
        """
        path_str = self.parser.get("config", "pseudos_file", fallback="")
        path_str = path_str.strip()
        if not path_str:
            return None
        return Path(path_str)

    @pseudos_file.setter
    def pseudos_file(self, value: Path) -> None:
        """Сохраняет путь к файлу псевдонимов в main.ini;
        @param value: объект Path с путём к JSON-файлу псевдонимов;
        """
        if "config" not in self.parser:
            self.parser["config"] = {}
        self.parser.set("config", "pseudos_file", str(value))
        self.save()

    @staticmethod
    def default_path() -> Path:
        # По сути логика из get_config_path
        if settings.main_ini_dir:
            return Path(settings.main_ini_dir) / "main.ini"
        return Path(__file__).parent / "main.ini"

    def _create_default(self) -> None:
        self.parser["window"] = {"coord_x": "100", "coord_y": "100"}
        self.parser["config"] = {
            "load_dir": str(Path.cwd()),
            "last_open_dir": str(Path.cwd()),
        }
        self.save()

    def _load(self) -> None:
        if not self.path.exists():
            self._create_default()
        self.parser.read(self.path, encoding="utf-8")

    # --- Окно ---

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            self.parser.write(f)
