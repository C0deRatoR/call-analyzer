"""Loader for `domains/*.yaml` configuration files.

Domains are read from `settings.domains_dir`, validated against `DomainConfig`,
and cached in-process. To pick up file edits at runtime, call `clear_cache()`.
"""

from functools import lru_cache

import yaml

from core.config import settings
from core.domains.schemas import DomainConfig


class DomainNotFoundError(KeyError):
    """Raised when no YAML file exists for the requested domain id."""


@lru_cache(maxsize=64)
def load_domain(domain_id: str) -> DomainConfig:
    path = settings.domains_dir / f"{domain_id}.yaml"
    if not path.exists():
        raise DomainNotFoundError(
            f"No domain config found at {path}. Available: {[d.id for d in list_domains()]}"
        )
    with path.open() as f:
        data = yaml.safe_load(f)
    return DomainConfig(**data)


def list_domains() -> list[DomainConfig]:
    """Return every domain config in `domains/`, sorted by file name."""
    if not settings.domains_dir.exists():
        return []
    configs: list[DomainConfig] = []
    for path in sorted(settings.domains_dir.glob("*.yaml")):
        with path.open() as f:
            data = yaml.safe_load(f)
        configs.append(DomainConfig(**data))
    return configs


def clear_cache() -> None:
    """Invalidate the in-process cache. Useful in tests or after editing YAML."""
    load_domain.cache_clear()
