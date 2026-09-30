# ConfigReach real-world validation

Static scans of pinned upstream commits. Target projects are not executed and their dependencies are not installed.
Runtime is wall-clock scan time on the recorded runner and is therefore performance evidence, not a cross-machine guarantee.
Manual false-positive/false-negative entries are targeted spot checks, not exhaustive repository-wide error rates; measured accuracy comes from the hand-labelled corpus.

Tool: ConfigReach `0.9.3` at source revision `09f181f67d6e0a6df119341bc522afd6e7ef3b2c`.

| Project | Ecosystem | Configs | Covered | Coverage | Runtime | Reviewed FP | Reviewed FN |
|---|---|---:|---:|---:|---:|---:|---:|
| pallets/flask | Python | 139 | 24 | 17.3% | 1.052s | 0 | 0 |
| django/django | Python | 368 | 136 | 37.0% | 83.575s | 0 | 0 |
| pydantic/pydantic | Python | 798 | 31 | 3.9% | 56.076s | 0 | 0 |
| encode/httpx | Python | 41 | 5 | 12.2% | 0.993s | 0 | 0 |
| expressjs/express | JavaScript | 9 | 4 | 44.4% | 0.863s | 0 | 0 |
| axios/axios | JavaScript | 7364 | 28 | 0.4% | 148.350s | 0 | 0 |
| gin-gonic/gin | Go | 17 | 2 | 11.8% | 0.471s | 0 | 0 |
| helm/helm | Go | 476 | 106 | 22.3% | 14.819s | 0 | 0 |
| spring-projects/spring-petclinic | Java/Spring | 100 | 30 | 30.0% | 0.246s | 0 | 0 |
| hashicorp/terraform | Go/Terraform | 8465 | 273 | 3.2% | 1525.822s | 0 | 0 |

## Aggregate

- Projects scanned: **10**
- Configuration inputs discovered: **17777**
- Inputs with detected test/runtime evidence: **639**
- Aggregate key coverage: **3.6%**
- Total scan wall time: **1832.265s**
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
