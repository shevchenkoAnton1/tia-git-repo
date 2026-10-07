import subprocess
from pathlib import Path
from ..logger import setup_logger

log = setup_logger()


class GitSync:
    """Обертка над git-командами для коммита и пуша."""

    def __init__(self, repo_path: str, branch: str = "main", remote: str = "origin"):
        self.repo_path = Path(repo_path).expanduser()
        self.branch = branch or "main"
        self.remote = remote or "origin"

    def _run(self, *args, check: bool = True):
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if check and result.returncode != 0:
            error_text = (result.stderr or result.stdout or "git command failed").strip()
            log.error(f"git {' '.join(args)}: {error_text}")
            raise RuntimeError(error_text)
        return result.stdout.strip()

    def _ensure_branch(self):
        try:
            current_branch = self._run("rev-parse", "--abbrev-ref", "HEAD")
        except RuntimeError:
            try:
                self._run("checkout", "-b", self.branch)
            except RuntimeError:
                self._run("checkout", "-B", self.branch)
            return self.branch

        if current_branch != self.branch:
            try:
                self._run("checkout", self.branch)
            except RuntimeError:
                self._run("checkout", "-b", self.branch)
        return self.branch

    def has_changes(self) -> bool:
        status = self._run("status", "--porcelain")
        return bool(status)

    def commit_and_push(self, message: str) -> bool:
        self._ensure_branch()

        if not self.has_changes():
            log.info("Изменений нет — коммит не нужен")
            return False

        self._run("add", ".")
        self._run("commit", "-m", message)

        try:
            self._run("push", self.remote, self.branch)
        except RuntimeError:
            self._run("push", "-u", self.remote, self.branch)

        log.info(f"Отправлено в {self.remote}/{self.branch}: {message}")
        return True