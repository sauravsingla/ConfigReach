# ConfigReach external holdout validation — full frozen corpus

Committed evidence consolidated from the successful 11-job GitHub Actions full holdout run.
Target projects were scanned statically at immutable upstream commit SHAs; target code was not executed and target dependencies were not installed.
Observed configuration coverage is ConfigReach evidence-linking output, not independently labelled precision/recall/F1.

- Suite: `external-holdout-v1`
- Captured: `2026-09-29`
- Source revision: `0bb468da29355a86f05b0870a1ac61bf8a5696b8`
- GitHub Actions run: `36588655396`
- Profile: `full`
- Frozen projects: **11**
- Baseline overlap: **0**
- All repository jobs: **success**

## Results by repository

| Project | Ecosystem | Configs | Covered | Coverage | Runtime | Files | Tests |
|---|---|---:|---:|---:|---:|---:|---:|
| `apache/airflow` | Python | 19,669 | 959 | 4.88% | 16028.985s | 10,694 | 4,557 |
| `PrefectHQ/prefect` | Python | 27,677 | 318 | 1.15% | 6757.554s | 3,809 | 935 |
| `vercel/next.js` | JavaScript/TypeScript | 17,880 | 734 | 4.11% | 8817.497s | 28,242 | 19,893 |
| `vitejs/vite` | JavaScript/TypeScript | 271 | 75 | 27.68% | 16.678s | 2,025 | 486 |
| `argoproj/argo-cd` | Go/Kubernetes | 5,107 | 242 | 4.74% | 589.126s | 4,221 | 732 |
| `spring-projects/spring-boot` | Java/Spring | 4,464 | 673 | 15.08% | 1098.859s | 9,704 | 3,956 |
| `dotnet/aspnetcore` | .NET/C# | 16,780 | 2,199 | 13.10% | 758.537s | 12,510 | 4,247 |
| `astral-sh/uv` | Rust | 2,801 | 132 | 4.71% | 556.336s | 1,273 | 438 |
| `rails/rails` | Ruby | 199 | 148 | 74.37% | 26.565s | 3,760 | 2,110 |
| `laravel/framework` | PHP | 1,707 | 59 | 3.46% | 283.089s | 3,229 | 1,343 |
| `terraform-aws-modules/terraform-aws-vpc` | Terraform | 290 | 0 | 0.00% | 0.406s | 84 | 0 |

## Results by ecosystem

| Ecosystem | Projects | Configs | Covered | Coverage | Cumulative runtime |
|---|---:|---:|---:|---:|---:|
| Python | 2 | 47,346 | 1,277 | 2.70% | 22786.539s |
| JavaScript/TypeScript | 2 | 18,151 | 809 | 4.46% | 8834.175s |
| Go/Kubernetes | 1 | 5,107 | 242 | 4.74% | 589.126s |
| Java/Spring | 1 | 4,464 | 673 | 15.08% | 1098.859s |
| .NET/C# | 1 | 16,780 | 2,199 | 13.10% | 758.537s |
| Rust | 1 | 2,801 | 132 | 4.71% | 556.336s |
| Ruby | 1 | 199 | 148 | 74.37% | 26.565s |
| PHP | 1 | 1,707 | 59 | 3.46% | 283.089s |
| Terraform | 1 | 290 | 0 | 0.00% | 0.406s |

## Aggregate

- Projects scanned: **11 / 11**
- Configuration inputs discovered: **96,845**
- Inputs with detected test/runtime evidence: **5,539**
- Aggregate observed configuration coverage: **5.72%**
- Cumulative scanner runtime: **34933.633s**
- Projects with manual review: **0**
- Workflow failures: **0**

> Runtime note: the 11 repositories ran as independent GitHub Actions jobs. The cumulative runtime above is the sum of scanner runtimes, not workflow elapsed wall-clock time.

## Claim boundary

This holdout measures ConfigReach behavior on a frozen set of external public repositories selected before results were examined. The coverage percentage is the fraction of discovered configuration inputs for which ConfigReach linked test/runtime evidence. It is **not** model/scanner accuracy, precision, recall or F1. Those metrics require independently labelled ground truth and remain separate from this repository-level holdout.

## Reproduction

```bash
python validation/run_external_holdout.py --manifest validation/external_holdout_projects.json --baseline-manifest validation/real_world_projects.json --profile full --json validation/results/external-holdout-full.json --markdown validation/results/external-holdout-full.md --reviews validation/external_holdout_reviews.json
```

Workflow evidence: https://github.com/sauravsingla/ConfigReach/actions/runs/36588655396

## Artifact provenance

Each repository result was uploaded as a GitHub Actions artifact in the run above. Artifact IDs and SHA-256 digests are recorded in `external-holdout-full.json` under `execution.artifacts`.
