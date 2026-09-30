# ConfigReach real-world validation

Static scans of pinned upstream commits. Target projects are not executed and their dependencies are not installed.
Runtime is wall-clock scan time on the recorded runner and is therefore performance evidence, not a cross-machine guarantee.
Manual false-positive/false-negative entries are targeted spot checks, not exhaustive repository-wide error rates; measured accuracy comes from the hand-labelled corpus.

Tool: ConfigReach `0.9.4` at source revision `8a3f93b2f696d5f32ab610506143cc2f35db6b2d`.

| Project | Ecosystem | Configs | Covered | Coverage | Runtime | Reviewed FP | Reviewed FN |
|---|---|---:|---:|---:|---:|---:|---:|
| pallets/flask | Python | 139 | 24 | 17.3% | 1.096s | 0 | 0 |
| django/django | Python | 368 | 136 | 37.0% | 85.337s | 0 | 0 |
| pydantic/pydantic | Python | 798 | 31 | 3.9% | 57.104s | 0 | 0 |
| encode/httpx | Python | 41 | 5 | 12.2% | 1.061s | 0 | 0 |
| expressjs/express | JavaScript | 9 | 4 | 44.4% | 0.899s | 0 | 0 |
| axios/axios | JavaScript | 7364 | 28 | 0.4% | 149.924s | 0 | 0 |
| gin-gonic/gin | Go | 17 | 2 | 11.8% | 0.484s | 0 | 0 |
| helm/helm | Go | 476 | 106 | 22.3% | 14.923s | 0 | 0 |
| spring-projects/spring-petclinic | Java/Spring | 100 | 30 | 30.0% | 0.249s | 0 | 0 |
| hashicorp/terraform | Go/Terraform | 8465 | 273 | 3.2% | 1525.465s | 0 | 0 |

## Aggregate

- Projects scanned: **10**
- Configuration inputs discovered: **17777**
- Inputs with detected test/runtime evidence: **639**
- Aggregate key coverage: **3.6%**
- Total scan wall time: **1836.541s**
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
