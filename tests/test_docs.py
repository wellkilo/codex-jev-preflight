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
        self.assertIn('href="styles.css"', html)
        self.assertIn('src="app.js"', html)

        parser = IdCollector()
        parser.feed(html)
        self.assertTrue(
            {
                "demo-prompt",
                "run-demo",
                "result-task-type",
                "result-complexity",
                "result-risk",
                "result-mode",
            }.issubset(parser.ids)
        )

    def test_frontend_demo_has_no_network_calls(self):
        javascript = (DOCS / "app.js").read_text(encoding="utf-8")
        forbidden = ("fetch(", "XMLHttpRequest", "WebSocket", "EventSource")
        for token in forbidden:
            self.assertNotIn(token, javascript)

    def test_readme_has_quick_start_prompt_and_pages_link(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## 快速开始（复制 Prompt 给 Codex）", readme)
        self.assertIn("https://wellkilo.github.io/codex-jev-preflight/", readme)
        self.assertIn("codex-jev-configure", readme)
        self.assertIn("codex-jev-install", readme)

    def test_pages_workflow_deploys_docs(self):
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("actions/configure-pages@v5", workflow)
        self.assertIn("actions/upload-pages-artifact@v3", workflow)
        self.assertIn("actions/deploy-pages@v4", workflow)
        self.assertIn("path: docs", workflow)


if __name__ == "__main__":
    unittest.main()
