import json
import tempfile
from pathlib import Path

from src.tia.exporter import TiaExporter


class DummyProject:
    def __init__(self, name):
        self.name = name
        self.devices = [
            {
                "name": "PLC_1",
                "blocks": [
                    {"name": "FB_Alarm", "type": "FunctionBlock"},
                    {"name": "FC_Start", "type": "Function"},
                ],
            }
        ]


def test_exporter_creates_summary_file():
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "exports"
        project = DummyProject("DemoProject")

        exporter = TiaExporter("C:/Dummy/Project.ap17", str(output_dir))
        result = exporter.export_all(project)

        assert result == output_dir
        assert result.exists()

        summary_path = result / "project_summary.json"
        assert summary_path.exists()

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary["project_name"] == "DemoProject"
        assert summary["device_count"] == 1
        assert summary["block_count"] == 2
