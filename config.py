from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    main_ini_dir: Optional[str] = None
    pseudos_list_dir: Optional[str] = None
    load_dir: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
