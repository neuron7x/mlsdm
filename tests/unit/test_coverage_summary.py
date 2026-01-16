from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from defusedxml.common import DefusedXmlException

from scripts.test_hygiene.coverage_summary import _collect_coverage, _write_summary

if TYPE_CHECKING:
    from pathlib import Path

def test_collect_coverage_parses_lines(tmp_path: Path) -> None:
    coverage_xml = tmp_path / "coverage.xml"
    coverage_xml.write_text(
        """<?xml version='1.0'?>
<coverage>
  <packages>
    <package name="mlsdm">
      <classes>
        <class filename="api/schemas.py">
          <lines>
            <line number="1" hits="1" />
            <line number="2" hits="0" />
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
        encoding="utf-8",
    )

    stats = _collect_coverage(coverage_xml, root="src/mlsdm")
    assert stats["src/mlsdm/api/schemas.py"].lines == 2
    assert stats["src/mlsdm/api/schemas.py"].covered == 1

    output_path = tmp_path / "summary.json"
    _write_summary(stats, output_path, root="src/mlsdm")
    assert output_path.exists()


def test_collect_coverage_rejects_dtd(tmp_path: Path) -> None:
    coverage_xml = tmp_path / "coverage.xml"
    coverage_xml.write_text(
        """<?xml version='1.0'?>
<!DOCTYPE coverage [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<coverage>
  <packages>
    <package name="mlsdm">
      <classes>
        <class filename="api/schemas.py">
          <lines>
            <line number="1" hits="1" />
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
        encoding="utf-8",
    )

    with pytest.raises(DefusedXmlException):
        _collect_coverage(coverage_xml, root="src/mlsdm")
