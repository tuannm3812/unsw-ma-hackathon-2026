"""A renderer import must not execute exports or write to external folders."""
import runpy
from pathlib import Path

import pytest


def test_renderer_import_is_inert_and_missing_template_creates_no_outputs(tmp_path):
    namespace = runpy.run_path('scripts/render_review_pdfs.py')
    output = tmp_path / 'new-exports'
    with pytest.raises(FileNotFoundError, match='template'):
        namespace['main'](['--template', str(tmp_path / 'absent.typ'),
                           '--output-dir', str(output)])
    assert not output.exists()
    assert namespace['REPO'] == Path.cwd()
