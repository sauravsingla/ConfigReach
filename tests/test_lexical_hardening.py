from __future__ import annotations

from configreach.engine import scan


def test_lexical_hardening_drops_comment_string_and_lookalike_false_positives(tmp_path):
    cases = {
        "web.js": "const s = `raw process.env.CR_FP_JS`; // process.env.CR_FP_JS_COMMENT\n",
        "types.ts": 'const s: string = "process.env.CR_FP_TS";\n',
        "service.go": 'package main\nfunc main(){ _ = `os.Getenv("CR_FP_GO")` }\n',
        "App.java": '// System.getenv("CR_FP_JAVA")\nclass App {}\n',
        "App.kt": '// System.getenv("CR_FP_KT")\nclass App\n',
        "Program.cs": '// Environment.GetEnvironmentVariable("CR_FP_CS")\nclass Program {}\n',
        "main.rs": 'fn main(){ let _ = r#"std::env::var("CR_FP_RS")"#; }\n',
        "app.rb": 'x = "ENV[\\"CR_FP_RB\\"]"\n',
        "app.php": '<?php $x = $cfg->getenv("CR_FP_PHP");\n',
        "run.sh": "echo '${CR_FP_SH}'\n",
        "action.yml": '# ${{ vars.CR_FP_GHA }}\nname: x\n',
    }
    for name, text in cases.items():
        (tmp_path / name).write_text(text, encoding="utf-8")

    report = scan(tmp_path, use_cache=False)

    for key in {
        "CR_FP_JS",
        "CR_FP_JS_COMMENT",
        "CR_FP_TS",
        "CR_FP_GO",
        "CR_FP_JAVA",
        "CR_FP_KT",
        "CR_FP_CS",
        "CR_FP_RS",
        "CR_FP_RB",
        "CR_FP_PHP",
        "CR_FP_SH",
        "CR_FP_GHA",
    }:
        assert key not in report.keys


def test_lexical_hardening_preserves_real_reads_and_interpolation(tmp_path):
    cases = {
        "web.js": "const s = `value=${process.env.CR_OK_JS}`;\n",
        "types.ts": "const s: string = `value=${process.env.CR_OK_TS}`;\n",
        "service.go": 'package main\nimport "os"\nfunc main(){ _ = os.Getenv("CR_OK_GO") }\n',
        "App.java": 'class App { String x = System.getenv("CR_OK_JAVA"); }\n',
        "App.kt": 'val s = "value=${System.getenv("CR_OK_KT")}"\n',
        "Program.cs": 'var s = $"value={Environment.GetEnvironmentVariable("CR_OK_CS")}";\n',
        "main.rs": 'fn main(){ let _ = std::env::var("CR_OK_RS"); }\n',
        "app.rb": 's = "value=#{ENV[\'CR_OK_RB\']}"\n',
        "app.php": '<?php $x = getenv("CR_OK_PHP");\n',
        "run.sh": 'echo "${CR_OK_SH}"\n',
        "action.yml": 'name: x\nruns:\n  using: composite\n  steps:\n    - shell: bash\n      run: echo "${{ vars.CR_OK_GHA }}"\n',
    }
    for name, text in cases.items():
        (tmp_path / name).write_text(text, encoding="utf-8")

    report = scan(tmp_path, use_cache=False)

    for key in {
        "CR_OK_JS",
        "CR_OK_TS",
        "CR_OK_GO",
        "CR_OK_JAVA",
        "CR_OK_KT",
        "CR_OK_CS",
        "CR_OK_RS",
        "CR_OK_RB",
        "CR_OK_PHP",
        "CR_OK_SH",
        "CR_OK_GHA",
    }:
        assert key in report.keys
