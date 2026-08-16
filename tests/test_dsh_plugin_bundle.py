from __future__ import annotations

import json
import tomllib
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]


class _CordisLoader(yaml.SafeLoader):
    pass


def _construct_js(loader: yaml.SafeLoader, node: yaml.Node) -> str:
    return loader.construct_scalar(node)


_CordisLoader.add_constructor("tag:yaml.org,2002:js", _construct_js)


def test_dsh_package_declares_bundle_and_matches_python_version() -> None:
    package = json.loads((REPO / "package.json").read_text(encoding="utf-8"))
    project = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert package["name"] == "local-shell-mcp-dsh"
    assert package["version"] == project["version"]
    assert package["dsh"]["bundle"]["patch"] == "./cordis.patch.yml"
    assert "dsh-plugin" in package["keywords"]


def test_dsh_bundle_uses_full_http_mcp_surface() -> None:
    rows = yaml.load((REPO / "cordis.patch.yml").read_text(encoding="utf-8"), Loader=_CordisLoader)
    assert isinstance(rows, list) and len(rows) == 1
    entries = rows[0]["insert"]
    assert len(entries) == 1

    bridge = entries[0]
    assert bridge["name"] == "@deepseek-ai/dsh-mcp-client"
    config = bridge["config"]
    assert config["serverName"] == "lsm"
    assert config["transport"] == "streamable-http"
    assert "127.0.0.1:8765/mcp" in config["url"]
    assert config["failOnStartupError"] is False

    text = (REPO / "cordis.patch.yml").read_text(encoding="utf-8")
    assert "--no-remote" not in text
    assert "allowRawNames" not in text
