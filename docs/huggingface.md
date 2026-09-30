# ConfigReach on Hugging Face

ConfigReach is published on Hugging Face as a public project collection, a static Space, and a reproducible validation dataset.

## Recommended entry point

Start with the public collection:

**ConfigReach — Configuration Coverage**  
https://huggingface.co/collections/sauravsingla08/configreach-configuration-coverage

The collection keeps the project assets together in one place. The Space is the public overview/demo surface, while the Dataset contains the reproducible validation evidence.

## Resources

- **ConfigReach collection:** https://huggingface.co/collections/sauravsingla08/configreach-configuration-coverage
- **ConfigReach Space:** https://huggingface.co/spaces/sauravsingla08/ConfigReach
- **Validation dataset:** https://huggingface.co/datasets/sauravsingla08/configreach-validation
- **Hugging Face profile:** https://huggingface.co/sauravsingla08
- **GitHub repository:** https://github.com/sauravsingla/ConfigReach
- **PyPI package:** https://pypi.org/project/configreach/

## Try ConfigReach

```bash
python -m pip install --upgrade configreach
configreach scan .
configreach coverage .
```

ConfigReach is deterministic and CPU-only. Repository scanning runs locally, in CI, or from the public container rather than inside the static Hugging Face Space.

## Validation dataset

The public dataset contains ConfigReach-derived configuration-coverage measurements and reproducibility metadata for pinned open-source repository revisions. It does not redistribute the scanned repositories' source code.

Load it with Hugging Face Datasets:

```python
from datasets import load_dataset

ds = load_dataset("sauravsingla08/configreach-validation")
print(ds["validation"])
```

## Discovery funnel

For external sharing, use the Collection URL as the primary project link. Visitors can then move from the Collection to the Space for the project overview and from the Space to the Dataset for reproducible evidence.

The Space and Dataset are synchronized from the GitHub repository through GitHub Actions and Hugging Face Trusted Publishers/OIDC.
