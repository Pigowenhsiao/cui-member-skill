"""
Git Auto Commit & Push utility for docs/ writes.

用法：
    from git_auto_push import auto_push

    # 寫入檔案後自動 commit + push
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    auto_push(out_path, "feat: add transcription from video {video_id}")

    # 或只 push（不另外 commit）
    auto_push()
"""

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def _run(cmd: list[str], cwd: Path | str | None = None) -> str:
    cwd = cwd or PROJECT_ROOT
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git command failed: {' '.join(cmd)}\n{result.stderr}"
        )
    return result.stdout.strip()


def auto_push(
    file_path: str | None = None,
    message: str | None = None,
) -> bool:
    """
    將指定檔案（或 docs/ 目錄下所有變更）commit 並 push 到 origin main。
    若無變更則直接略過。
    """
    try:
        _run(["git", "status", "--porcelain"])
    except Exception:
        return False

    if file_path:
        for p in _resolve_paths(file_path):
            _run(["git", "add", str(p)])

    if message is None:
        import datetime
        date = datetime.date.today().isoformat()
        message = f"chore(docs): auto-save {date}"

    status = _run(["git", "status", "--porcelain"])
    if not status:
        print("[git-auto-push] nothing to commit")
        return True

    try:
        _run(["git", "commit", "-m", message])
    except RuntimeError:
        return False

    try:
        _run(["git", "push", "origin", "main"])
        print(f"[git-auto-push] pushed: {message}")
        return True
    except RuntimeError as e:
        print(f"[git-auto-push] push failed: {e}")
        return False


def _resolve_paths(pattern: str) -> list[Path]:
    """支援 glob pattern 或直接路徑，回傳符合的 Path 清單。"""
    root = PROJECT_ROOT
    if "*" in pattern:
        import glob
        matches = glob.glob(str(root / pattern), recursive=True)
        return [Path(m) for m in matches]
    return [root / pattern]
