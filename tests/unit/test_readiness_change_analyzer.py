import json
import subprocess
import sys
from pathlib import Path

from scripts.readiness import change_analyzer as ca


def test_category_mapping():
    cases = {
        "src/security/module.py": "security_critical",
        "src/feature/module.py": "functional_core",
        ".github/workflows/pipeline.yml": "infrastructure",
        "observability/logging.conf": "observability",
        "tests/test_sample.py": "test_coverage",
        "docs/readme.md": "documentation",
        "src/moral_filter/rules.py": "security_critical",
    }
    for path, expected in cases.items():
        assert ca.classify_category(path) == expected


def test_risk_max_rank_uses_numeric_order(tmp_path):
    paths = [
        "docs/readme.md",
        "config/service.yaml",
        "src/security/config.json",
    ]
    result = ca.analyze_paths(paths, base_ref="HEAD", root=tmp_path)
    assert result["max_risk"] == "critical"
    assert result["summary"]["categories"]["security_critical"] == 1


def test_extract_signatures_top_level_and_method_ignore_nested():
    source = """
@decorator
def top(a, /, b, *, c, **kwargs):
    def inner():
        return 2
    return a


class Sample(Base):
    @classmethod
    def build(cls, value):
        def nested():
            return value
        return value

    def process(self, item):
        return item
"""
    signatures = ca.extract_signatures(source, "src/pkg/mod.py")
    assert signatures["top"] == "pkg.mod:top(a,/,b,*,c,**kwargs)->None|decorators=decorator"
    assert signatures["Sample"] == "pkg.mod:Sample[bases=Base]"
    assert signatures["Sample.build"] == "pkg.mod:Sample.build(cls,value)->None|decorators=classmethod"
    assert signatures["Sample.process"] == "pkg.mod:Sample.process(self,item)->None"
    assert all("inner" not in sig for sig in signatures.values())


def _git(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def test_semantic_diff_added_removed_modified(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    src_dir = repo / "src"
    src_dir.mkdir()
    module_path = src_dir / "mod.py"
    module_path.write_text(
        "def removed_func():\n"
        "    return 1\n\n"
        "def changed(x):\n"
        "    return x\n\n"
        "class Demo:\n"
        "    def greet(self, name):\n"
        "        return name\n",
        encoding="utf-8",
    )
    _git(["git", "init"], cwd=repo)
    _git(["git", "config", "user.email", "test@example.com"], cwd=repo)
    _git(["git", "config", "user.name", "Test User"], cwd=repo)
    _git(["git", "add", "src/mod.py"], cwd=repo)
    _git(["git", "commit", "-m", "base"], cwd=repo)

    module_path.write_text(
        "def changed(x, y):\n"
        "    return x\n\n"
        "def added_func():\n"
        "    return 2\n\n"
        "class Demo:\n"
        "    def greet(self, name):\n"
        "        return name\n"
        "    def added(self, z):\n"
        "        return z\n",
        encoding="utf-8",
    )

    result = ca.analyze_paths(["src/mod.py"], base_ref="HEAD", root=repo)
    semantic = result["files"]["src/mod.py"]["semantic"]
    assert "mod:added_func()->None" in semantic["functions_added"]
    assert "mod:Demo.added(self,z)->None" in semantic["functions_added"]
    assert "mod:removed_func()->None" in semantic["functions_removed"]
    assert "mod:changed(x)->None -> mod:changed(x,y)->None" in semantic["functions_modified"]


def test_handles_empty_deleted_and_unparseable(tmp_path):
    empty_result = ca.analyze_paths([], base_ref="HEAD", root=tmp_path)
    assert empty_result["summary"]["files_analyzed"] == 0
    assert all(count == 0 for count in empty_result["summary"]["categories"].values())

    repo = tmp_path / "repo2"
    repo.mkdir()
    src_dir = repo / "src"
    src_dir.mkdir()
    deleted_path = src_dir / "gone.py"
    deleted_path.write_text("def will_go():\n    return 1\n", encoding="utf-8")
    _git(["git", "init"], cwd=repo)
    _git(["git", "config", "user.email", "test@example.com"], cwd=repo)
    _git(["git", "config", "user.name", "Test User"], cwd=repo)
    _git(["git", "add", "src/gone.py"], cwd=repo)
    _git(["git", "commit", "-m", "base"], cwd=repo)
    deleted_path.unlink()

    unparseable_path = repo / "src" / "broken.py"
    # Intentionally malformed Python to verify graceful handling
    unparseable_path.write_text("def broken(:\n", encoding="utf-8")

    result = ca.analyze_paths(["src/gone.py", "src/broken.py"], base_ref="HEAD", root=repo)
    gone_semantic = result["files"]["src/gone.py"]["semantic"]
    assert "gone:will_go()->None" in gone_semantic["functions_removed"]

    broken_semantic = result["files"]["src/broken.py"]["semantic"]
    assert broken_semantic["functions_added"] == []
    assert broken_semantic["functions_removed"] == []
    assert broken_semantic["functions_modified"] == []


def test_cli_writes_output(tmp_path):
    files_list = tmp_path / "files.txt"
    files_list.write_text("docs/unknown.md\n", encoding="utf-8")
    output = tmp_path / "out" / "result.json"
    script_path = Path(ca.__file__)
    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--files",
            str(files_list),
            "--base-ref",
            "HEAD",
            "--output",
            str(output),
        ],
        cwd=ca.ROOT,
        text=True,
    )
    assert completed.returncode == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert set(data.keys()) == {"primary_category", "max_risk", "summary", "files"}
    assert "docs/unknown.md" in data["files"]
