import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])


class DocumentationTests(unittest.TestCase):
    def test_frontend_assets_exist_and_are_linked(self):
        html = (DOCS / "index.html").read_text(encoding="utf-8")
        self.assertTrue((DOCS / "styles.css").is_file())
        self.assertTrue((DOCS / "app.js").is_file())
        self.assertTrue((DOCS / "assets" / "demo.gif").is_file())
        self.assertTrue((DOCS / "assets" / "demo-poster.png").is_file())
        self.assertIn('href="styles.css"', html)
        self.assertIn('src="app.js"', html)
        self.assertIn('src="assets/demo.gif"', html)

        parser = IdCollector()
        parser.feed(html)
        self.assertTrue(
            {
                "demo-prompt",
                "run-demo",
                "language-toggle",
                "result-task-type",
                "result-complexity",
                "result-risk",
                "result-mode",
            }.issubset(parser.ids)
        )

    def test_frontend_defaults_to_english_and_has_language_switch(self):
        html = (DOCS / "index.html").read_text(encoding="utf-8")
        javascript = (DOCS / "app.js").read_text(encoding="utf-8")
        self.assertIn('<html lang="en" data-lang="en">', html)
        self.assertIn("data-i18n", html)
        self.assertIn("language-toggle", html)
        self.assertIn("codex-jev-language", javascript)
        self.assertIn("zh-CN", javascript)

    def test_frontend_content_is_visible_without_javascript_observation(self):
        styles = (DOCS / "styles.css").read_text(encoding="utf-8")
        reveal_rule = styles.split(".reveal {", 1)[1].split("}", 1)[0]
        self.assertNotIn("opacity: 0", reveal_rule)
        self.assertIn("opacity: 1", reveal_rule)

    def test_frontend_demo_has_no_network_calls(self):
        javascript = (DOCS / "app.js").read_text(encoding="utf-8")
        forbidden = ("fetch(", "XMLHttpRequest", "WebSocket", "EventSource")
        for token in forbidden:
            self.assertNotIn(token, javascript)

    def test_readme_has_quick_start_prompt_and_pages_link(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Quick start", readme)
        self.assertIn("https://wellkilo.github.io/codex-jev-preflight/", readme)
        self.assertIn("codex-jev-configure", readme)
        self.assertIn("codex-jev-install", readme)
        self.assertIn("README.zh-CN.md", readme)

    def test_readme_has_gif_badges_and_visual_structure(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn('<div align="center">', readme)
        self.assertIn("docs/assets/demo.gif", readme)
        self.assertIn("actions/workflows/ci.yml/badge.svg", readme)
        self.assertIn("img.shields.io/github/v/release", readme)
        self.assertIn("```mermaid", readme)

    def test_chinese_readme_links_back_to_english(self):
        readme = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("README.md", readme)
        self.assertIn("docs/assets/demo.gif", readme)
        self.assertIn("## 快速开始", readme)

    def test_pages_workflow_deploys_docs(self):
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("actions/configure-pages@v5", workflow)
        self.assertIn("actions/upload-pages-artifact@v3", workflow)
        self.assertIn("actions/deploy-pages@v4", workflow)
        self.assertIn("path: docs", workflow)


if __name__ == "__main__":
    unittest.main()
