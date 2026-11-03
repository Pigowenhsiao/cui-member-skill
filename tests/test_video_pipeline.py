# /// script
# dependencies = [
#     "python-dotenv",
# ]
# ///

import os
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skills import process_video, resolve_target_dir, subtitle_to_text
from skills.path_utils import project_path, report_path, safe_component, video_folder_name
from skills.video_state import get, is_complete, mark


class PathAndChannelTests(unittest.TestCase):
    def test_windows_safe_components(self):
        self.assertEqual(safe_component('CON'), '_CON')
        for reserved in ('CON', 'PRN', 'AUX', 'NUL', 'COM1', 'LPT9'):
            self.assertEqual(safe_component(reserved + '.txt'), '_' + reserved + '.txt')
        self.assertEqual(safe_component('bad<>:"/\\|?* name'), 'bad- name')
        self.assertEqual(safe_component('name. '), 'name')
        self.assertEqual(safe_component('***'), 'untitled')
        self.assertLessEqual(len(safe_component('長' * 500)), 120)

    def test_empty_long_and_colliding_titles_keep_video_identity(self):
        self.assertTrue(safe_component('   '))
        self.assertNotEqual(video_folder_name('A/B', 'video001'), video_folder_name('A:B', 'video002'))
        self.assertLessEqual(len(video_folder_name('影片' * 500, 'id123')), 160)

    def test_supplementary_letters_fit_utf16_component_and_folder_budgets(self):
        letter = "\U00010400"
        units = lambda value: len(value.encode("utf-16-le")) // 2
        component = safe_component(letter * 100, max_length=11)
        folder = video_folder_name(letter * 300, letter * 30)
        report = report_path(Path("docs") / (letter * 300)).name

        self.assertEqual(component, letter * 5)
        self.assertLessEqual(units(component), 11)
        self.assertLessEqual(units(folder), 160)
        self.assertLessEqual(units(report), 180)
        self.assertFalse(any(0xD800 <= ord(char) <= 0xDFFF for char in folder))

    def test_report_path_uses_safe_folder_name(self):
        self.assertEqual(report_path(Path("docs") / "分類" / "T: title. ").name, "T- title.md")

    def test_project_paths_are_rooted_and_unicode_friendly(self):
        result = project_path(Path("docs") / "空 格" / "報告.txt")
        self.assertTrue(result.is_absolute())
        self.assertIn("空 格", str(result))
        self.assertEqual(Path(result).name, "報告.txt")

    def test_channel_spelling_variants_resolve_consistently(self):
        self.assertEqual(resolve_target_dir.categorize('美投侃新闻', ''), resolve_target_dir.categorize('美投侃新聞', ''))
        self.assertEqual(resolve_target_dir.categorize('美投讲美股', ''), resolve_target_dir.categorize('美投講美股', ''))
        self.assertEqual(resolve_target_dir.categorize('小翠时政财经', ''), resolve_target_dir.categorize('小翠時政財經', ''))
        self.assertEqual(resolve_target_dir.categorize('美投講美股', ''), os.path.join('美投君', '美投講美股'))
        self.assertEqual(
            resolve_target_dir.categorize('美投君', '一般市場更新', channel_key='meitou_stock'),
            os.path.join('美投君', '美投講美股'),
        )
        self.assertEqual(
            resolve_target_dir.categorize('美投君', '一般市場更新'),
            os.path.join('美投君', '美投侃新聞'),
        )


class SubtitleTests(unittest.TestCase):
    def test_vtt_parser_removes_minute_second_timestamps(self):
        content = (
            "WEBVTT\n\n"
            "00:01.000 --> 00:02.000\n"
            "cue text remains\n\n"
            "00:00:03,000 --> 00:00:04,000 align:start\n"
            "second cue remains\n"
        )
        self.assertEqual(
            subtitle_to_text.vtt_to_text(content),
            "cue text remains\nsecond cue remains",
        )

    def test_prefers_manual_traditional_chinese_then_fallback_languages(self):
        metadata = {
            'subtitles': {'en': [{}], 'zh-TW': [{}]},
            'automatic_captions': {'zh-Hant': [{}]},
        }
        self.assertEqual(subtitle_to_text._select_track(metadata), ('zh-TW', False))
        self.assertEqual(subtitle_to_text._select_track({'subtitles': {}, 'automatic_captions': {'en': [{}]}}), ('en', True))
        self.assertIsNone(subtitle_to_text._select_track({'subtitles': {'ja': [{}]}, 'automatic_captions': {}}))

    def test_caption_download_failure_falls_through_to_auto_track(self):
        metadata = {
            "id": "vid123",
            "subtitles": {"zh-Hant": [{}]},
            "automatic_captions": {"zh-Hant": [{}]},
        }
        commands = []

        def fake_yt_dlp(args):
            commands.append(args)
            if "--dump-single-json" in args:
                return subprocess.CompletedProcess(args, 0, json.dumps(metadata), "")
            if "--write-subs" in args:
                raise subprocess.CalledProcessError(1, args, stderr="manual unavailable")
            template = Path(args[args.index("-o") + 1].replace("%(ext)s", "zh-Hant.vtt"))
            template.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n字幕內容\n", encoding="utf-8")
            return subprocess.CompletedProcess(args, 0, "", "")

        with tempfile.TemporaryDirectory(prefix="字幕 路徑 ") as directory:
            with patch.object(subtitle_to_text, "_cookies", return_value=["--cookies", "cookies.txt"]), patch.object(subtitle_to_text, "_yt_dlp", side_effect=fake_yt_dlp):
                output = subtitle_to_text.download_subtitle("https://youtu.be/vid123", Path(directory), "")

            self.assertEqual(output.read_text(encoding="utf-8"), "字幕內容\n")
            self.assertIn("--write-subs", commands[1])
            self.assertIn("--write-auto-subs", commands[2])

    def test_vtt_conversion_returns_clean_consumer_transcript(self):
        vtt = 'WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n<c>第一句</c>\n\n00:00:02.000 --> 00:00:03.000\n第一句\n'
        self.assertEqual(subtitle_to_text.vtt_to_text(vtt), '第一句')

    def test_valid_caption_skips_mp3_and_whisper(self):
        with tempfile.TemporaryDirectory(prefix="字幕 路徑 ") as directory:
            root = Path(directory)
            target = root / "docs" / "分類" / "字幕 vid002"
            db = root / "state.sqlite3"
            calls = []

            def fake_stage(script, *args):
                calls.append((script, args))
                if script == "resolve_target_dir.py":
                    target.mkdir(parents=True, exist_ok=True)
                    return subprocess.CompletedProcess([], 0, f"TARGET_DIR={target}\n", "")
                if script == "subtitle_to_text.py":
                    (target / "vid002.txt").write_text("有效字幕", encoding="utf-8")
                    return subprocess.CompletedProcess([], 0, "", "")
                raise AssertionError(f"unexpected stage: {script}")

            def project_path(path):
                candidate = Path(path)
                return candidate if candidate.is_absolute() else root / candidate

            with patch.object(process_video, "project_path", side_effect=project_path), patch.object(process_video, "run_stage", side_effect=fake_stage):
                process_video.process("vid002", "https://youtu.be/vid002", "字幕標題", db,
                                      channel_key="meitou_stock")

            self.assertEqual([call[0] for call in calls], ["resolve_target_dir.py", "subtitle_to_text.py"])
            self.assertEqual(calls[0][1][-2:], ("--channel-key", "meitou_stock"))
            self.assertEqual(get("vid002", db)["status"], "transcript_ready")
            self.assertFalse(is_complete("vid002", db))
            with patch.object(process_video, "project_path", side_effect=project_path), patch.object(process_video, "run_stage", side_effect=fake_stage):
                with self.assertRaisesRegex(FileNotFoundError, "report exists"):
                    process_video.process("vid002", "https://youtu.be/vid002", "字幕標題", db, mark_summarized=True)
                self.assertFalse(is_complete("vid002", db))
                report_path(target).write_text("# 摘要", encoding="utf-8")
                process_video.process("vid002", "https://youtu.be/vid002", "字幕標題", db, mark_summarized=True)
            self.assertTrue(is_complete("vid002", db))


class ResumeTests(unittest.TestCase):
    def test_transcription_retry_redownloads_missing_audio_and_resumes_summary(self):
        with tempfile.TemporaryDirectory(prefix="影片 路徑 ") as directory:
            root = Path(directory)
            docs = root / 'docs'
            target = docs / '分類' / '測試 video001'
            target.mkdir(parents=True)
            db = root / 'state.sqlite3'
            calls = []
            transcription_attempts = 0

            def fake_stage(script, *args):
                nonlocal transcription_attempts
                calls.append(script)
                if script == 'resolve_target_dir.py':
                    return subprocess.CompletedProcess([], 0, f'TARGET_DIR={target}\n', '')
                if script == 'subtitle_to_text.py':
                    raise subprocess.CalledProcessError(1, script, stderr='no captions')
                if script == 'download_audio.py':
                    (target / 'video001.mp3').write_bytes(b'audio')
                    return subprocess.CompletedProcess([], 0, '', '')
                if script == 'transcribe.py':
                    transcription_attempts += 1
                    if transcription_attempts == 1:
                        raise subprocess.CalledProcessError(1, script, stderr='temporary transcription failure')
                    (target / 'video001.txt').write_text('transcript', encoding='utf-8')
                    return subprocess.CompletedProcess([], 0, '', '')
                raise AssertionError(script)

            def project_path(path):
                candidate = Path(path)
                return candidate if candidate.is_absolute() else root / candidate

            with patch.object(process_video, 'project_path', side_effect=project_path), patch.object(process_video, 'run_stage', side_effect=fake_stage):
                with self.assertRaisesRegex(RuntimeError, 'subtitle attempt: no captions'):
                    process_video.process('video001', 'https://youtu.be/video001', 'Title', db)
                self.assertEqual(get('video001', db)['status'], 'audio')
                (target / 'video001.mp3').unlink()
                process_video.process('video001', 'https://youtu.be/video001', 'Title', db)
                self.assertEqual(get('video001', db)['status'], 'transcript_ready')
                before_summary_retry = list(calls)
                process_video.process('video001', 'https://youtu.be/video001', 'Title', db)
                self.assertEqual(calls, before_summary_retry)
                report_path(target).write_text('# Summary', encoding='utf-8')
                process_video.process('video001', 'https://youtu.be/video001', 'Title', db, mark_summarized=True)

            self.assertEqual(calls.count('subtitle_to_text.py'), 1)
            self.assertEqual(calls.count('download_audio.py'), 2)
            self.assertEqual(calls.count('transcribe.py'), 2)
            self.assertTrue((target / 'video001.txt').is_file())
            self.assertTrue(is_complete('video001', db))
            self.assertIn('no captions', get('video001', db)['subtitle_error'])

    def test_empty_transcript_retries_captions_and_requires_nonempty_output(self):
        with tempfile.TemporaryDirectory(prefix="文字稿 路徑 ") as directory:
            root = Path(directory)
            target = root / "docs" / "分類" / "empty vid003"
            target.mkdir(parents=True)
            (target / "vid003.mp3").write_bytes(b"audio")
            (target / "vid003.txt").write_text("  \n", encoding="utf-8")
            db = root / "state.sqlite3"
            mark("vid003", "audio", title="Empty transcript", db_path=db)
            calls = []
            attempts = 0

            def fake_stage(script, *args):
                nonlocal attempts
                calls.append(script)
                if script == "subtitle_to_text.py":
                    raise subprocess.CalledProcessError(1, script, stderr="captions unavailable")
                if script == "transcribe.py":
                    attempts += 1
                    text = "   \n" if attempts == 1 else "Recovered transcript\n"
                    (target / "vid003.txt").write_text(text, encoding="utf-8")
                    return subprocess.CompletedProcess([], 0, "", "")
                raise AssertionError(f"unexpected stage: {script}")

            def project_path(path):
                candidate = Path(path)
                return candidate if candidate.is_absolute() else root / candidate

            with patch.object(process_video, "project_path", side_effect=project_path), patch.object(process_video, "run_stage", side_effect=fake_stage):
                with self.assertRaisesRegex(RuntimeError, "empty or unreadable transcript"):
                    process_video.process("vid003", "https://youtu.be/vid003", "Empty transcript", db)
                self.assertEqual(get("vid003", db)["status"], "pending")
                self.assertFalse(is_complete("vid003", db))
                process_video.process("vid003", "https://youtu.be/vid003", "Empty transcript", db)

            self.assertEqual(calls.count("subtitle_to_text.py"), 2)
            self.assertEqual(calls.count("download_audio.py"), 0)
            self.assertEqual(calls.count("transcribe.py"), 2)
            self.assertEqual(get("vid003", db)["status"], "transcript_ready")
            self.assertEqual((target / "vid003.txt").read_text(encoding="utf-8").strip(), "Recovered transcript")


if __name__ == '__main__':
    unittest.main()
