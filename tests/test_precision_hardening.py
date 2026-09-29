from __future__ import annotations

import json

from configreach.engine import scan


def test_static_indirection_and_precision_hardening(tmp_path):
    (tmp_path / "src").mkdir()

    (tmp_path / "src" / "app.py").write_text(
        "import os\n"
        "prefix = 'DYNAMIC'\n"
        "token = os.getenv(prefix + '_TOKEN')\n"
        "def stats_value(stats):\n"
        "    return stats.variation('coefficient-of-variation')\n"
        "def enabled(client):\n"
        "    return client.variation('new-checkout', False)\n",
        encoding="utf-8",
    )

    (tmp_path / "src" / "web.js").write_text(
        "const { JS_DESTRUCTURED } = process.env;\n"
        "const spread = stats.variation('stddev');\n"
        "const flag = featureClient.variation('beta-banner', false);\n",
        encoding="utf-8",
    )

    (tmp_path / "src" / "service.go").write_text(
        "package service\n"
        "import \"os\"\n"
        "func mode() string {\n"
        "  key := \"GO_DYNAMIC\"\n"
        "  return os.Getenv(key)\n"
        "}\n",
        encoding="utf-8",
    )

    (tmp_path / "src" / "App.java").write_text(
        "import org.springframework.beans.factory.annotation.Value;\n"
        "class App {\n"
        "  @Value(\"${service.mode:dev}\")\n"
        "  String mode;\n"
        "}\n",
        encoding="utf-8",
    )

    (tmp_path / "src" / "settings.py").write_text(
        "from pydantic_settings import BaseSettings\n"
        "class AppSettings(BaseSettings):\n"
        "    debug: bool = False\n",
        encoding="utf-8",
    )

    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "name": "demo",
                "version": "1.2.3",
                "scripts": {"test": "pytest"},
                "config": {"runtime": "prod"},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'demo'\nversion = '1.2.3'\n",
        encoding="utf-8",
    )

    report = scan(tmp_path, use_cache=False)

    assert report.keys["DYNAMIC_TOKEN"].used
    assert report.keys["JS_DESTRUCTURED"].used
    assert report.keys["GO_DYNAMIC"].used

    assert "new-checkout" in report.keys
    assert "feature-flag" in report.keys["new-checkout"].categories
    assert "beta-banner" in report.keys
    assert "feature-flag" in report.keys["beta-banner"].categories
    assert "coefficient-of-variation" not in report.keys
    assert "stddev" not in report.keys

    assert "service.mode" in report.keys
    assert report.keys["service.mode"].declared

    assert "name" not in report.keys
    assert "version" not in report.keys
    assert "scripts.test" not in report.keys
    assert "project.name" not in report.keys
    assert "project.version" not in report.keys
    assert report.keys["config.runtime"].declared

    assert report.keys["DEBUG"].expected_values >= {"true", "false"}
    assert report.keys["DEBUG"].branch_values == set()
