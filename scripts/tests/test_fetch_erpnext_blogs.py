#!/usr/bin/env python3
"""Tests for fetch-erpnext-blogs.py fidelity checking functions."""

import sys
from pathlib import Path
import tempfile
import os

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


class TestCheckFidelity:
    """Tests for check_fidelity function."""

    def test_identical_content_returns_true(self):
        module = get_module()
        local = "Hello world"
        remote = "Hello world"
        assert module.check_fidelity(local, remote) is True

    def test_different_content_returns_false(self):
        module = get_module()
        local = "Hello world"
        remote = "Goodbye world"
        assert module.check_fidelity(local, remote) is False

    def test_ignores_html_formatting(self):
        module = get_module()
        local = "Hello world"
        remote = "<p>Hello <strong>world</strong></p>"
        assert module.check_fidelity(local, remote) is True

    def test_ignores_whitespace_differences(self):
        module = get_module()
        local = "Hello world"
        remote = "Hello    \n\n   world"
        assert module.check_fidelity(local, remote) is True

    def test_ignores_case_differences(self):
        module = get_module()
        local = "hello world"
        remote = "HELLO WORLD"
        assert module.check_fidelity(local, remote) is True

    def test_ignores_hugo_shortcodes(self):
        module = get_module()
        local = "Hello world"
        remote = '{{< block >}}Hello world{{< /block >}}'
        assert module.check_fidelity(local, remote) is True


class TestReadLocalBlog:
    """Tests for read_local_blog function."""

    def test_reads_frontmatter_and_content(self):
        module = get_module()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
title: "Test Article"
erpnext_id: "test-123"
---

This is the content.
""")
            f.flush()
            try:
                front_matter, content = module.read_local_blog(Path(f.name))
                assert front_matter['title'] == "Test Article"
                assert front_matter['erpnext_id'] == "test-123"
                assert "This is the content." in content
            finally:
                os.unlink(f.name)

    def test_returns_none_for_missing_file(self):
        module = get_module()
        result = module.read_local_blog(Path("/nonexistent/file.md"))
        assert result is None

    def test_handles_file_without_frontmatter(self):
        module = get_module()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Just plain content without frontmatter.")
            f.flush()
            try:
                result = module.read_local_blog(Path(f.name))
                assert result is not None
                front_matter, content = result
                assert front_matter == {}
                assert "Just plain content" in content
            finally:
                os.unlink(f.name)
