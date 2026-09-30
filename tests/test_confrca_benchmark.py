from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validation" / "confrca" / "run_confrca_benchmark.py"
spec = importlib.util.spec_from_file_location("confrca_benchmark", MODULE_PATH)
assert spec and spec.loader
benchmark = importlib.util.module_from_spec(spec)
sys_modules = __import__("sys").modules
sys_modules[spec.name] = benchmark
spec.loader.exec_module(benchmark)


def test_registry_classification_keeps_extras_separate_from_fp():
    result = benchmark.classify_registry({"a", "b", "c"}, {"a", "b", "x"})
    assert result["tp"] == 2
    assert result["fn"] == 1
    assert result["out_of_registry"] == 1
    assert result["recall"] == 2 / 3
    assert "false positive" in result["claim_boundary"].lower()


def test_pair_classification_confusion_matrix():
    rows = [
        {"prompt_id": "1", "project": "hdfs", "version": "3.4.1", "config1_id": "a", "config2_id": "b", "dep_label": "True", "dep_type": "Control"},
        {"prompt_id": "2", "project": "hdfs", "version": "3.4.1", "config1_id": "a", "config2_id": "c", "dep_label": "False", "dep_type": "Value"},
        {"prompt_id": "3", "project": "hdfs", "version": "3.4.1", "config1_id": "d", "config2_id": "e", "dep_label": "True", "dep_type": "Behavioral"},
        {"prompt_id": "4", "project": "hdfs", "version": "3.4.1", "config1_id": "f", "config2_id": "g", "dep_label": "False", "dep_type": "Priority"},
    ]
    result = benchmark.classify_pairs(rows, {("a", "b"), ("a", "c")})
    assert (result["tp"], result["fp"], result["tn"], result["fn"]) == (1, 1, 1, 1)
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["f1"] == 0.5


def test_pair_key_is_order_independent_and_trimmed():
    assert benchmark._pair_key(" z ", "a") == ("a", "z")


def test_boolean_label_parser():
    assert benchmark._bool_label("True") is True
    assert benchmark._bool_label("false") is False
