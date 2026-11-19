"""実際に Chromium / FFmpeg でレンダリングするテスト（環境が無ければスキップ）。"""
import random
import subprocess

from PIL import Image

from autopilot.collectors.sample import load_sample
from autopilot.llm.template import template_copy
from autopilot.planner import plan_post
from autopilot.render.carousel import render_carousel, render_story

from .conftest import needs_chromium, needs_ffmpeg, needs_node


@needs_chromium
def test_carousel_images(settings, db):
    load_sample(settings, db)
    post = plan_post(settings, db, "carousel", random.Random(4))
    copy = template_copy(post["plan"])
    out = settings.output_dir / "c"
    files = render_carousel(settings, post["plan"], copy, post["post_no"], out)
    assert 4 <= len(files) <= 10
    for f in files:
        im = Image.open(f)
        assert im.size == (1080, 1350) and im.format == "JPEG"
    story = render_story(settings, post["plan"], copy, post["post_no"], out)
    assert Image.open(story).size == (1080, 1920)


@needs_chromium
@needs_ffmpeg
@needs_node
def test_short_video(settings, db):
    from autopilot.video.composer import render_video

    load_sample(settings, db)
    post = plan_post(settings, db, "reel", random.Random(7))
    copy = template_copy(post["plan"])
    res = render_video(settings, post["plan"], copy, post["post_no"], settings.output_dir / "v")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height",
                            "-of", "csv=p=0", str(res["video"])], capture_output=True, text=True).stdout
    assert "h264,1080,1920" in probe and "aac" in probe
    assert 10 < res["seconds"] <= 90
