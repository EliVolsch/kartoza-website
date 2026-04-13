#!/usr/bin/env python3
"""Tests for fetch-erpnext-blogs.py fidelity checking functions."""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import will fail until we implement
from importlib import import_module


def get_module():
    """Import the fetch script as a module."""
    spec = import_module('fetch-erpnext-blogs')
    return spec


class TestNormalizeForComparison:
    """Tests for normalize_for_comparison function."""

    def test_strips_html_tags(self):
        module = get_module()
        html = "<p>Hello <strong>world</strong></p>"
        result = module.normalize_for_comparison(html)
        assert "hello world" == result

    def test_removes_hugo_shortcodes(self):
        module = get_module()
        content = '{{< block title="Test" >}}Hello{{< /block >}}'
        result = module.normalize_for_comparison(content)
        assert "hello" == result

    def test_collapses_whitespace(self):
        module = get_module()
        content = "Hello    \n\n   world"
        result = module.normalize_for_comparison(content)
        assert "hello world" == result

    def test_lowercases_text(self):
        module = get_module()
        content = "Hello WORLD"
        result = module.normalize_for_comparison(content)
        assert "hello world" == result

    def test_empty_string(self):
        module = get_module()
        result = module.normalize_for_comparison("")
        assert "" == result

    def test_complex_html(self):
        module = get_module()
        html = """
        <div class="content">
            <h2>Title</h2>
            <p>First paragraph with <a href="#">link</a>.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </div>
        """
        result = module.normalize_for_comparison(html)
        # Note: BeautifulSoup's get_text(separator=' ') adds space between elements
        # so "link</a>." becomes "link ." - this is expected for text extraction
        assert "title first paragraph with link . item 1 item 2" == result
