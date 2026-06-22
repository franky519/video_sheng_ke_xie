#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("2026-06-15_17-23_openrouter_fullvideo_followup_probe.py")


def load_module():
    if not SCRIPT_PATH.exists():
        raise AssertionError(f"target script does not exist: {SCRIPT_PATH}")
    spec = importlib.util.spec_from_file_location("openrouter_fullvideo_followup_probe", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FullVideoFollowupProbeTests(unittest.TestCase):
    def test_parse_segments_accepts_comma_separated_ranges(self):
        module = load_module()
        self.assertEqual(module.parse_segments("0-20,20-40,40-60"), [(0, 20), (20, 40), (40, 60)])

    def test_build_segments_stops_at_video_duration(self):
        module = load_module()
        self.assertEqual(module.build_segments(segment_seconds=20, max_segments=4, video_duration=55), [(0, 20), (20, 40), (40, 55)])

    def test_repeat_video_mode_includes_video_in_current_user_turn(self):
        module = load_module()
        video = module.VideoPayload(mime_type="video/mp4", data_url="data:video/mp4;base64,AAA")
        history = [module.TurnResult(segment=(0, 20), content="第一段结果", generation_id="gen-1")]

        messages = module.build_messages(
            mode="repeat-video",
            video=video,
            segment=(20, 40),
            prompt_text="分析 20-40 秒",
            history=history,
        )

        current_content = messages[-1]["content"]
        self.assertTrue(any(part.get("type") == "video_url" for part in current_content))

    def test_text_followup_mode_omits_video_after_first_turn(self):
        module = load_module()
        video = module.VideoPayload(mime_type="video/mp4", data_url="data:video/mp4;base64,AAA")
        history = [module.TurnResult(segment=(0, 20), content="第一段结果", generation_id="gen-1")]

        messages = module.build_messages(
            mode="text-followup",
            video=video,
            segment=(20, 40),
            prompt_text="分析 20-40 秒",
            history=history,
        )

        current_content = messages[-1]["content"]
        self.assertIsInstance(current_content, str)
        self.assertNotIn("data:video", current_content)

    def test_extract_cost_prefers_generation_total_cost(self):
        module = load_module()
        cost = module.extract_cost_usd(
            generation_metadata={"data": {"total_cost": 0.0123}},
            stream_usage={"cost": 0.0999},
        )
        self.assertEqual(cost.usd, 0.0123)
        self.assertEqual(cost.source, "generation.total_cost")

    def test_build_turn_log_row_persists_full_content(self):
        module = load_module()
        row = module.build_turn_log_row(
            index=4,
            model="google/gemini-3.1-pro-preview",
            mode="carry-first-video",
            segment=(85, 120),
            generation_id="gen-test",
            elapsed=12.5,
            finish_reason="stop",
            cost=module.CostInfo(0.123, "stream.usage.cost"),
            cny=0.89175,
            usage={"prompt_tokens": 10},
            metadata=None,
            content="完整分段正文",
        )
        self.assertEqual(row["content"], "完整分段正文")
        self.assertEqual(row["content_chars"], 6)

    def test_check_model_only_can_run_without_api_key_when_model_check_is_skipped(self):
        module = load_module()
        code = module.main(["--check-model-only", "--skip-model-check", "--env", "/path/that/does/not/exist"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
