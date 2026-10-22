# /// script
# dependencies = [
#   "python-dotenv",
# ]
# ///

"""
cui-member-skill の docs/ ツリーを Obsidian Vault へミラーする（Step 7 アーカイブ同期）。

対象: Pigo_Obsidian (https://github.com/Pigowenhsiao/Pigo_Obsidian.git)
      <VAULT>/<VAULT_DOCS_SUBDIR>/  (= 18-Wealth/docs/)

使い方:
  uv run skills/sync_vault.py

環境変数 (.env):
  VAULT_PATH           必須。Vault ルート（例: E:\\obsidian）
  VAULT_DOCS_SUBDIR    任意。既定 "18-Wealth/docs"

仕様:
  - docs/<カテゴリ>/<日付>/... → <VAULT>/<VAULT_DOCS_SUBDIR>/<カテゴリ>/<日付>/...
    先頭カテゴリ "小翠時政財經" のみ取り除く（Vault 側の分類名に合わせる）。
  - 既存ファイルは上書きしない（Vault 側で手直し済みのノートを保護する）。
  - LF 正規化後の sha1 が Vault 側に既に存在する場合も複製しない。
  - docs/keywords.md は Vault 側の "## Linked Notes" 節を保ったまま差し替える。
  - index.md は既存行を保持したまま、新規日付の行だけを追加する
    （既存行のタイトルは人手校訂済みのため再生成しない）。
  - Git は対象パスだけをステージして commit する。push は行わない
    （セキュリティ方針：push は手動）。
"""

import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"

# docs/ 直下でミラー対象から除外する運用ファイル
EXCLUDED_BASENAMES = {
    "GIST_README.md",
    "batch_log.md",
    "download_log.md",
    "V100_WHISPER_SETUP.md",
    "keywords.md",  # 別途マージ処理
}

# 小翠時政財經 は Vault 側の分類名に存在しないため取り除く
STRIP_PREFIX = "小翠時政財經"

# index.md を持つ分類: 並び順 / セクション単位 / 表ヘッダ
INDEX_CATEGORIES = {
    "每日要聞": {"order": "asc", "unit": "month", "header": "| 日期 | 摘要 |"},
    "會員直播": {"order": "desc", "unit": "year", "header": "| 日期 | 標題 |"},
}

DATE_DIR_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})([a-z]?)$")
INDEX_ROW_RE = re.compile(
    r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*\[(?P<title>.*?)\]"
    r"\(\./(?P<dir>\d{8}[a-z]?)/summary\.md\)\s*\|$"
)


def sha1_lf(text: str) -> str:
    return hashlib.sha1(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def git(vault: Path, *args: str) -> str:
    result: subprocess.CompletedProcess[str] = subprocess.run(
        ["git", "-C", str(vault), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        print(f"  ❌ git {' '.join(args)} 失敗: {result.stderr.strip()}")
    return result.stdout


def map_path(rel: Path) -> Path:
    """docs/ からの相対パスを Vault 側のパスへ変換する"""
    parts = rel.parts
    if parts and parts[0] == STRIP_PREFIX:
        parts = parts[1:]
    return Path(*parts)


def collect_source_files() -> list[Path]:
    """ミラー対象の相対パス一覧"""
    files: list[Path] = []
    for path in sorted(DOCS_DIR.rglob("*.md")):
        rel = path.relative_to(DOCS_DIR)
        if len(rel.parts) == 1 and rel.name in EXCLUDED_BASENAMES:
            continue
        files.append(rel)
    return files


def vault_hashes(vault_docs: Path) -> set[str]:
    """Vault 側に既存するノートの内容ハッシュ（LF 正規化）"""
    hashes: set[str] = set()
    if not vault_docs.exists():
        return hashes
    for path in vault_docs.rglob("*.md"):
        try:
            hashes.add(sha1_lf(read_text(path)))
        except OSError:
            continue
    return hashes


def sync_notes(vault_docs: Path) -> tuple[int, int]:
    """(新規書き込み数, スキップ数) を返す"""
    known = vault_hashes(vault_docs)
    written = 0
    skipped = 0
    for rel in collect_source_files():
        src = DOCS_DIR / rel
        dest = vault_docs / map_path(rel)
        if dest.exists():
            skipped += 1
            continue
        text = read_text(src)
        digest = sha1_lf(text)
        if digest in known:
            skipped += 1
            continue
        write_text(dest, text)
        known.add(digest)
        written += 1
        print(f"  書込: {rel} → {map_path(rel)}")
    return written, skipped


def sync_keywords(vault_docs: Path) -> bool:
    """keywords.md を差し替える（Vault 側の Linked Notes 節は保持）"""
    src = DOCS_DIR / "keywords.md"
    if not src.exists():
        return False
    dest = vault_docs / "keywords.md"
    repo_text = read_text(src)
    if not dest.exists():
        write_text(dest, repo_text)
        print("  書込: keywords.md（新規）")
        return True

    current = read_text(dest)
    if current == repo_text:
        return False

    if current.startswith(repo_text):
        # 既存ファイルは repo 内容 + 追記節 なので、追記節だけを引き継ぐ
        new_text = repo_text + current[len(repo_text) :]
    else:
        marker = "## Linked Notes"
        idx = current.find(marker)
        if idx == -1:
            new_text = repo_text.rstrip("\n") + "\n"
        else:
            new_text = repo_text.rstrip("\n") + "\n\n" + current[idx:]
    if new_text == current:
        return False
    write_text(dest, new_text)
    print("  更新: keywords.md（Linked Notes 節を保持）")
    return True


DECORATION_BRACKETS = (
    "【會員直播】",
    "【每日要聞】",
    "【小翠時政財經】",
    "【小翠時政財經/每日要聞】",
    "【美投侃新闻】",
)


def clean_title(raw: str) -> str:
    """影片標題/H1 から装飾を除去する"""
    title = raw.strip()
    # 節目番号は括弧を外して先頭に置く
    episode = ""
    match = re.match(r"^【(EP\d+)】\s*", title)
    if match:
        episode = f"{match.group(1)} "
        title = title[match.end() :]
    # 先頭の装飾記号・分類ラベルを繰り返し除去
    while True:
        stripped = re.sub(r"^(🔴\s*|📺\s*)", "", title)
        for label in DECORATION_BRACKETS:
            if stripped.startswith(label):
                stripped = stripped[len(label) :].strip()
        if stripped == title:
            break
        title = stripped
    title = re.sub(r"^小翠時政財經\s*[｜|]\s*", "", title)
    title = re.sub(r"^每日要聞摘要\s*[｜|]\s*", "", title)
    title = re.sub(r"^每日要聞\s*[｜|]\s*", "", title)
    title = re.sub(r"｜小翠時政財經.*$", "", title)
    title = re.sub(r"\s*\.\.\.\s*$", "", title)
    title = re.sub(r"摘要$", "", title)
    return (episode + title).strip(" .｜#")


def is_generic_title(title: str) -> bool:
    """情報量のないタイトルか判定する"""
    generic = ("小翠時政財經", "每日要聞", "每日要聞摘要", "會員直播", "摘要")
    return title in generic or title.startswith("每日要聞｜")


def extract_title(summary_path: Path) -> str:
    """summary.md から 1 行のタイトルを抽出する"""
    text = read_text(summary_path)
    candidates: list[str] = []
    # 基本情報テーブル（太字あり／なしの両方）
    match = re.search(r"\|\s*\**影片標題\**\s*\|\s*(.+?)\s*\|", text)
    if match:
        candidates.append(match.group(1))
    # 箇条書きの「**影片標題**：...」
    match = re.search(r"\**影片標題\**\s*[：:]\s*(.+)", text)
    if match:
        candidates.append(match.group(1).strip())
    # H1
    for line in text.split("\n"):
        if line.startswith("# "):
            candidates.append(line[2:].strip())
            break

    for raw in candidates:
        cleaned = clean_title(raw)
        if cleaned and not is_generic_title(cleaned):
            return cleaned
    return clean_title(candidates[0]) if candidates else ""


def dir_date(dir_name: str) -> str | None:
    """20261021 → 2026-10-21"""
    match = DATE_DIR_RE.match(dir_name)
    if not match:
        return None
    year, month, day, _ = match.groups()
    return f"{year}-{month}-{day}"


def section_key(day: str, unit: str) -> str:
    """日付が属するセクションのキー"""
    return day[:7] if unit == "month" else day[:4]


def heading_for(key: str, unit: str) -> str:
    """セクション見出し"""
    return f"## {key}" if unit == "month" else f"## {key} 年"


def key_of_heading(heading: str, unit: str) -> str | None:
    """見出しからセクションキーを取り出す"""
    if unit == "month":
        match = re.match(r"^##\s+(\d{4}-\d{2})\s*$", heading)
    else:
        match = re.match(r"^##\s+(\d{4})\s*年\s*$", heading)
    return match.group(1) if match else None


def split_blocks(lines: list[str]) -> list[tuple[str | None, list[str]]]:
    """見出し (`## `) 区切りでブロックへ分解する"""
    blocks: list[tuple[str | None, list[str]]] = []
    heading: str | None = None
    body: list[str] = []
    for line in lines:
        if line.startswith("## "):
            blocks.append((heading, body))
            heading = line
            body = []
        else:
            body.append(line)
    blocks.append((heading, body))
    return blocks


def insert_into_table(body: list[str], row: str, order: str) -> list[str]:
    """表の行を日付順の正しい位置へ挿入する"""
    result = list(body)
    new_day = row_key(row)
    for i, line in enumerate(result):
        match = INDEX_ROW_RE.match(line)
        if not match:
            continue
        if order == "asc" and match.group(1) > new_day:
            result.insert(i, row)
            return result
        if order == "desc" and match.group(1) < new_day:
            result.insert(i, row)
            return result

    last_row = -1
    for i, line in enumerate(result):
        if INDEX_ROW_RE.match(line):
            last_row = i
    if last_row == -1:
        return result
    result.insert(last_row + 1, row)
    return result


def row_key(row: str) -> str:
    match = re.match(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|", row)
    return match.group(1) if match else ""


def add_row_to_blocks(
    blocks: list[tuple[str | None, list[str]]],
    day: str,
    name: str,
    title: str,
    order: str,
    unit: str,
    header: str,
) -> list[tuple[str | None, list[str]]]:
    """日付セクションの表に 1 行追加する"""
    row = f"| {day} | [{title}](./{name}/summary.md) |"
    key = section_key(day, unit)
    result = list(blocks)

    for idx, (heading, body) in enumerate(result):
        if heading is None or key_of_heading(heading, unit) != key:
            continue
        result[idx] = (heading, insert_into_table(body, row, order))
        return result

    # 対応するセクションが無い場合、末尾の同类セクション直後に作る
    insert_at = 0
    for idx, (heading, _body) in enumerate(result):
        if heading is not None and key_of_heading(heading, unit) is not None:
            insert_at = idx + 1
    # 直前のセクション末尾の区切り線 (---) は新セクションの後ろへ回す
    has_separator = False
    if insert_at > 0:
        prev_heading, prev_body = result[insert_at - 1]
        last_row = -1
        for i, line in enumerate(prev_body):
            if INDEX_ROW_RE.match(line):
                last_row = i
        if last_row >= 0:
            tail = prev_body[last_row + 1 :]
            has_separator = any(line.strip() == "---" for line in tail)
            result[insert_at - 1] = (prev_heading, prev_body[: last_row + 1] + [""])
    new_body = ["", header, "|------|------|", row, ""]
    if has_separator:
        new_body += ["---", ""]
    result.insert(insert_at, (heading_for(key, unit), new_body))
    return result


def update_index(category_dir: Path, spec: dict) -> int:
    """index.md に未掲載の日付の行を追加する。追加件数を返す"""
    index_path = category_dir / "index.md"
    if not index_path.exists():
        return 0

    order = spec["order"]
    unit = spec["unit"]
    header = spec["header"]

    text = read_text(index_path)
    lines = text.split("\n")
    listed = {m.group("dir") for line in lines if (m := INDEX_ROW_RE.match(line))}

    new_rows: list[tuple[str, str, str]] = []
    for child in sorted(category_dir.iterdir()):
        if not child.is_dir() or child.name in listed:
            continue
        summary = child / "summary.md"
        if not summary.exists():
            continue
        day = dir_date(child.name)
        if day is None:
            continue
        title = extract_title(summary)
        if not title:
            continue
        new_rows.append((day, child.name, title))

    if not new_rows:
        return 0

    blocks = split_blocks(lines)
    for day, name, title in new_rows:
        blocks = add_row_to_blocks(blocks, day, name, title, order, unit, header)

    out: list[str] = []
    for heading, body in blocks:
        if heading is not None:
            out.append(heading)
        out.extend(body)

    write_text(index_path, "\n".join(out))
    for day, name, title in new_rows:
        print(f"  index 行追加: {day} {title}")
    return len(new_rows)


def commit(vault: Path, subdir: str, changed: bool) -> str:
    """対象パスだけをステージして commit する（push はしない）"""
    if not changed:
        print("  変更なし。コミットをスキップします。")
        return ""
    _ = git(vault, "add", "--", subdir)
    status = git(vault, "status", "--porcelain", "--", subdir).strip()
    if not status:
        print("  変更なし。コミットをスキップします。")
        return ""
    msg = f"docs: 摘要同步更新 ({datetime.now().strftime('%Y-%m-%d')})"
    _ = subprocess.run(
        ["git", "-C", str(vault), "commit", "-m", msg],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    sha = git(vault, "rev-parse", "--short", "HEAD").strip()
    print(f"  ✅ コミット完了: {msg} ({sha})")
    print(f"  ⚠️ push は行いません。手動で: git -C {vault} push")
    return sha


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")

    vault_path = os.environ.get("VAULT_PATH", "").strip()
    if not vault_path:
        print("提示: VAULT_PATH が未設定のため、Vault 同期をスキップします。")
        return 0

    vault = Path(vault_path)
    if not (vault / ".git").is_dir():
        print(f"提示: {vault} は Git リポジトリではないため、スキップします。")
        return 0

    subdir = os.environ.get("VAULT_DOCS_SUBDIR", "18-Wealth/docs").strip().strip("/")
    vault_docs = vault / subdir

    print(f"🔍 Vault 同期先: {vault_docs}")

    written, skipped = sync_notes(vault_docs)
    keywords_changed = sync_keywords(vault_docs)

    index_rows = 0
    for category, spec in INDEX_CATEGORIES.items():
        index_rows += update_index(vault_docs / category, spec)

    print(f"  新規 {written} / スキップ {skipped} / index 追加 {index_rows} 行")

    commit(vault, subdir, written > 0 or keywords_changed or index_rows > 0)
    print("🎉 Vault 同期完了！")
    return 0


if __name__ == "__main__":
    sys.exit(main())
