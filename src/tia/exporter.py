import json
from datetime import datetime
from pathlib import Path
from ..logger import setup_logger

log = setup_logger()


class TiaExporter:
    """Экспорт блоков и тегов из проекта TIA Portal в текстовый вид."""

    def __init__(self, project_path: str, output_dir: str):
        self.project_path = project_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _to_list(value):
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return list(value)
        return [value]

    @staticmethod
    def _safe_get(obj, *names, default=None):
        for name in names:
            if obj is None:
                return default
            value = getattr(obj, name, None)
            if value is not None:
                return value
            if isinstance(obj, dict):
                value = obj.get(name)
                if value is not None:
                    return value
        return default

    def _iter_devices(self, project):
        devices = self._safe_get(project, "Devices", "devices", default=[])
        return self._to_list(devices)

    def _iter_blocks(self, device):
        blocks = self._safe_get(device, "Blocks", "blocks", default=[])
        return self._to_list(blocks)

    def export_all(self, project):
        """Экспортирует сведения о проекте и блоках в папку exports."""
        project_name = self._safe_get(project, "Name", "name", default=Path(self.project_path).stem if self.project_path else "TIA_Project")
        devices = self._iter_devices(project)
        block_count = 0

        log.info(f"Экспорт проекта {project_name} → {self.output_dir}")

        for device in devices:
            device_name = self._safe_get(device, "Name", "name", default="device")
            blocks = self._iter_blocks(device)
            device_dir = self.output_dir / str(device_name)
            device_dir.mkdir(parents=True, exist_ok=True)

            for block in blocks:
                block_name = self._safe_get(block, "Name", "name", default=f"block_{block_count + 1}")
                block_type = self._safe_get(block, "Type", "type", default="unknown")
                block_payload = {
                    "name": block_name,
                    "type": block_type,
                    "device": str(device_name),
                    "project": str(project_name),
                }
                block_path = device_dir / f"{str(block_name)}.json"
                block_path.write_text(json.dumps(block_payload, indent=2, ensure_ascii=False), encoding="utf-8")
                block_count += 1

        summary = {
            "project_name": str(project_name),
            "project_path": str(self.project_path),
            "device_count": len(devices),
            "block_count": block_count,
            "generated_at": datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        }
        summary_path = self.output_dir / "project_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        return self.output_dir