# ConfigReach real-world validation

Static scans of pinned upstream commits. Target projects are not executed and their dependencies are not installed.
Runtime is wall-clock scan time on the recorded runner and is therefore performance evidence, not a cross-machine guarantee.
Manual false-positive/false-negative entries are targeted spot checks, not exhaustive repository-wide error rates; measured accuracy comes from the hand-labelled corpus.

Tool: ConfigReach `0.9.4` at source revision `916a34838871cd7cfe134d84ae5e7836022ab223`.

| Project | Ecosystem | Configs | Covered | Coverage | Runtime | Reviewed FP | Reviewed FN |
|---|---|---:|---:|---:|---:|---:|---:|
| pallets/flask | Python | 135 | 24 | 17.8% | 0.816s | 0 | 0 |
| django/django | Python | 363 | 136 | 37.5% | 61.848s | 0 | 0 |
| pydantic/pydantic | Python | 795 | 31 | 3.9% | 41.033s | 0 | 0 |
| encode/httpx | Python | 41 | 5 | 12.2% | 0.795s | 0 | 0 |
| expressjs/express | JavaScript | 7 | 4 | 57.1% | 0.792s | 0 | 0 |
| axios/axios | JavaScript | 7354 | 23 | 0.3% | 109.290s | 0 | 0 |
| gin-gonic/gin | Go | 15 | 1 | 6.7% | 0.585s | 0 | 0 |
| helm/helm | Go | 456 | 96 | 21.1% | 11.851s | 0 | 0 |
| spring-projects/spring-petclinic | Java/Spring | 100 | 30 | 30.0% | 0.233s | 0 | 0 |
| hashicorp/terraform | Go/Terraform | 8429 | 242 | 2.9% | 1074.779s | 0 | 0 |

## Aggregate

- Projects scanned: **10**
- Configuration inputs discovered: **17695**
- Inputs with detected test/runtime evidence: **592**
- Aggregate key coverage: **3.3%**
- Total scan wall time: **1302.023s**
- Projects with manual spot checks: **4**
- Manually reviewed false-positive examples: **0**
- Manually reviewed false-negative examples: **0**

## Manual review evidence

The targeted spot checks below found no reviewed false-positive or false-negative examples after the current hardening pass:

- **django/django** — Rechecked the pinned django/conf/__init__.py environment-variable indirection after static string propagation hardening.
- **expressjs/express** — Rechecked package.json project metadata after runtime-configuration metadata filtering.
- **axios/axios** — Rechecked package.json project metadata after runtime-configuration metadata filtering.
- **hashicorp/terraform** — Rechecked pinned Go environment-variable reads whose names are held in constants after deterministic constant propagation hardening.

## Reproduction

```bash
python validation/run_real_world.py --manifest validation/real_world_projects.json --reviews validation/real_world_reviews.json --json validation/results/real-world.json --markdown validation/results/real-world.md
```

Runner: `Linux-6.17.0-1022-azure-x86_64-with-glibc2.39` / Python `3.12.14`.
