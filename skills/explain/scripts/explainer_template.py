"""Explainer video skeleton: one `with self.beat(id)` block per scene of script.json.

Voice the script first (narrate.py), so audio/durations.json exists. Then, from this folder:

    uv run --with manim manim -ql explainer.py Explainer    # 480p draft
    uv run --with manim manim -qh explainer.py Explainer    # 1080p final
"""
import json

from manim import *

# after the star import, so nothing from manim can replace these
from contextlib import contextmanager
from pathlib import Path

AUDIO = Path(__file__).parent / "audio"
CLIPS = json.loads((AUDIO / "durations.json").read_text())


class Explainer(Scene):
    @contextmanager
    def beat(self, scene_id):
        """Start one scene's narration, give its length to the block, then wait out the rest."""
        clip = CLIPS[scene_id]
        self.add_sound(str(AUDIO / clip["file"]))
        start = self.renderer.time
        yield clip["seconds"]
        left = clip["seconds"] - (self.renderer.time - start)
        if left > 0.05:
            self.wait(left)
        elif left < -0.3:
            print(f"beat {scene_id}: the animation runs {-left:.1f}s past its narration")

    def construct(self):
        # Replace this example with one beat per scene, in script order.
        with self.beat("01-hook") as t:
            browser = RoundedRectangle(width=2.6, height=1.6, corner_radius=0.2, color=BLUE)
            browser_label = Text("Browser", font_size=30).move_to(browser)
            globe = Circle(radius=0.8, color=GREEN)
            globe_label = Text("Website", font_size=30).next_to(globe, DOWN)
            VGroup(browser, browser_label).to_edge(LEFT, buff=1.5)
            VGroup(globe, globe_label).to_edge(RIGHT, buff=1.5)
            question = Text("?", font_size=72, color=YELLOW)

            self.play(Create(browser), Write(browser_label), run_time=t * 0.35)
            self.play(Create(globe), Write(globe_label), run_time=t * 0.35)
            self.play(FadeIn(question, scale=1.5), run_time=t * 0.2)
