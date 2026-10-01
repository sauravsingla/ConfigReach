# ConfigReach measured accuracy

Results from the repository's hand-labelled benchmark corpus. Labels are committed before scoring and include deliberately difficult positive and negative examples.

Tool: ConfigReach `0.9.4` at source revision `916a34838871cd7cfe134d84ae5e7836022ab223`.

| Task | Precision | Recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| env var discovery | 100.0% | 100.0% | 100.0% | 11 | 0 | 0 |
| feature flags | 100.0% | 100.0% | 100.0% | 2 | 0 | 0 |
| config declarations | 100.0% | 100.0% | 100.0% | 11 | 0 | 0 |
| test evidence | 100.0% | 100.0% | 100.0% | 6 | 0 | 0 |
| branch inference | 100.0% | 100.0% | 100.0% | 7 | 0 | 0 |

**Micro precision:** 100.0%  
**Micro recall:** 100.0%  
**Micro F1:** 100.0%  
**Macro F1:** 100.0%

## Errors exposed by the benchmark

### Env Var Discovery

- False positives: none
- False negatives: none

### Feature Flags

- False positives: none
- False negatives: none

### Config Declarations

- False positives: none
- False negatives: none

### Test Evidence

- False positives: none
- False negatives: none

### Branch Inference

- False positives: none
- False negatives: none

## Label policy

- **env var discovery:** Runtime environment-variable inputs that a human reviewer can identify from source, including statically recoverable intent expressed through simple indirection; declarations alone do not count.
- **feature flags:** Runtime boolean/variant flag lookups whose call is semantically a feature-flag decision; unrelated methods named variation do not count.
- **config declarations:** Declarations of application/runtime/deployment configuration. Package/project metadata such as package.json name/version/scripts and pyproject project metadata do not count.
- **test evidence:** Configuration keys for which a human reviewer can see a test intentionally supplies or exercises the key, including a small helper abstraction.
- **branch inference:** Explicit configuration-dependent decision states. A finite boolean type without an actual decision branch does not itself count as a branch.

## Reproduce

```bash
python validation/accuracy/run_accuracy.py --corpus validation/accuracy/corpus.json --json validation/results/accuracy.json --markdown validation/results/accuracy.md
```

This corpus is intentionally small and transparent. It measures the committed cases exactly; it is not claimed to estimate all repositories or all configuration frameworks.
