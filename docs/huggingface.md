# ConfigReach on Hugging Face

ConfigReach is available on Hugging Face as both an interactive static Space and a reproducible validation dataset.

## Resources

- **ConfigReach Space:** https://huggingface.co/spaces/sauravsingla08/ConfigReach
- **Validation dataset:** https://huggingface.co/datasets/sauravsingla08/configreach-validation
- **Hugging Face profile:** https://huggingface.co/sauravsingla08
- **GitHub repository:** https://github.com/sauravsingla/ConfigReach
- **PyPI package:** https://pypi.org/project/configreach/

## Validation dataset

The public dataset contains ConfigReach-derived configuration-coverage measurements and reproducibility metadata for pinned open-source repository revisions. It does not redistribute the scanned repositories' source code.

Load it with Hugging Face Datasets:

```python
from datasets import load_dataset

ds = load_dataset("sauravsingla08/configreach-validation")
print(ds["validation"])
```

The Space and Dataset are synchronized from the GitHub repository through GitHub Actions and Hugging Face Trusted Publishers/OIDC.
