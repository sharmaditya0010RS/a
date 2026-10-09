from __future__ import annotations

import ast
from pathlib import Path

from streamlit_app.case_reports import report_filename

ROOT = Path(__file__).resolve().parents[2]


def test_export_module_exists():
    path = ROOT / "streamlit_app" / "case_export.py"
    assert path.is_file()


def test_workbench_imports_case_export():
    path = (
        ROOT
        / "streamlit_app"
        / "pages"
        / "workbench.py"
    )

    tree = ast.parse(path.read_text(encoding="utf-8"))

    imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "streamlit_app.case_export"
    ]

    assert imports


def test_workbench_has_no_page_config():
    path = (
        ROOT
        / "streamlit_app"
        / "pages"
        / "workbench.py"
    )

    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr != "set_page_config"


def test_report_filename_is_html():
    filename = report_filename(695)

    assert filename == "FCI_Investigation_Alert_695.html"
    assert filename.endswith(".html")


def test_case_export_uses_download_button():
    path = ROOT / "streamlit_app" / "case_export.py"

    tree = ast.parse(path.read_text(encoding="utf-8"))

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "download_button"
    ]

    assert calls