import sys
from pathlib import Path
from ..logger import setup_logger

log = setup_logger()

try:
    import clr
except ImportError:  # pragma: no cover - runtime dependency only exists in TIA environment
    clr = None


class TiaConnector:
    """Подключение к TIA Portal через Openness API."""

    def __init__(self, version: str, public_api_path: str, project_path: str = None):
        self.version = version
        self.public_api_path = public_api_path
        self.project_path = project_path
        self.tia = None

    def _load_assemblies(self):
        if not Path(self.public_api_path).exists():
            raise FileNotFoundError(
                f"Не найден PublicAPI: {self.public_api_path}\n"
                f"Проверь версию TIA в config/settings.json"
            )
        if clr is None:
            raise ImportError("pythonnet is not installed. Install the dependency from src/requirements.txt")

        sys.path.append(self.public_api_path)
        clr.AddReference("Siemens.Engineering")
        log.info(f"Загружена Siemens.Engineering из {self.public_api_path}")

    def connect(self):
        self._load_assemblies()
        from Siemens.Engineering import TiaPortal, TiaPortalMode
        self.tia = TiaPortal(TiaPortalMode.WithoutUserInterface)
        log.info("TIA Portal запущен в фоновом режиме")
        return self.tia

    def open_project(self, project_path: str = None):
        if self.tia is None:
            self.connect()

        target = project_path or self.project_path
        if not target:
            log.warning("Не указан путь к проекту TIA, возвращаем объект TIA без открытия проекта")
            return self.tia

        project = None
        projects = getattr(self.tia, "Projects", None)
        if projects is not None:
            open_method = getattr(projects, "Open", None)
            if callable(open_method):
                project = open_method(target)

        if project is None:
            try:
                project = self.tia.OpenProject(target)
            except Exception:
                log.warning("Не удалось открыть проект %s через API TIA. Возвращается объект TIA без проекта.", target)
                project = self.tia

        return project

    def dispose(self):
        if self.tia:
            self.tia.Dispose()
            log.info("TIA Portal закрыт")