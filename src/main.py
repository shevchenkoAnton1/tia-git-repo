import json
import sys
from pathlib import Path
from datetime import datetime

# Добавляем src в путь, чтобы импорты работали
sys.path.insert(0, str(Path(__file__).parent))

from logger import setup_logger
from tia.connector import TiaConnector
from tia.exporter import TiaExporter
from git.sync import GitSync

log = setup_logger()
ROOT = Path(__file__).parent.parent


def load_config():
    with open(ROOT / "config" / "settings.json", encoding="utf-8") as f:
        return json.load(f)


def main():
    cfg = load_config()
    log.info("=== Запуск TIA -> GitLab sync ===")

    git = GitSync(cfg["git"]["repo_path"], cfg["git"].get("branch", "main"), cfg["git"].get("remote", "origin"))

    tia = TiaConnector(
        cfg["tia"]["version"],
        cfg["tia"]["public_api_path"],
        cfg["tia"].get("project_path"),
    )

    export_dir = cfg.get("export", {}).get("output_dir", "exports")
    exporter = TiaExporter(cfg["tia"].get("project_path", ""), export_dir)

    try:
        try:
            project = tia.open_project(cfg["tia"].get("project_path"))
            exporter.export_all(project)
            log.info("Экспорт проекта TIA завершён")
        except Exception as exc:
            log.warning("TIA Portal недоступен или проект не открыт: %s", exc)
    finally:
        tia.dispose()

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    git.commit_and_push(f"Auto-export TIA Portal {stamp}")

    log.info("=== Готово ===")


if __name__ == "__main__":
    main()