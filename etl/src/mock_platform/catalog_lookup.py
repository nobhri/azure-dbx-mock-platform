"""SDLC environment-to-catalog resolution.

Demonstrates the SDLC pattern: pipeline code references an environment name;
this module resolves it to the correct Unity Catalog catalog name. When the
platform scales to multi-catalog (e.g. mock_dev / mock_prod), only the map
below changes — pipeline notebooks remain unchanged.
"""


def get_catalog(env: str) -> str:
    """Resolve an environment name to its Unity Catalog catalog name.

    Args:
        env: Target environment name (e.g. "dev", "prod").

    Returns:
        The catalog name for the given environment.

    Raises:
        ValueError: If env is not a recognised environment.
    """
    catalog_map: dict[str, str] = {
        "dev": "mock",
        "prod": "mock",
    }
    if env not in catalog_map:
        raise ValueError(
            f"Unknown environment '{env}'. Valid values: {sorted(catalog_map)}"
        )
    return catalog_map[env]
