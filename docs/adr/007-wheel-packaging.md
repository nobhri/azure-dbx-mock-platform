# ADR-007: Wheel Packaging over `%run` for Shared ETL Code

**Status:** Accepted
**Date:** 2026-03-12

---

## Context

The ETL codebase is split across two concerns:

- **Shared library code** (`transform.py`, `catalog_lookup.py`) — pure functions with no I/O,
  independently testable, used by multiple notebooks
- **Orchestration notebooks** (`pipeline.py`, `e2e_test.py`) — entry points that import shared
  code and perform I/O (`spark.table`, `saveAsTable`, `CREATE OR REPLACE VIEW`)

This split was established by the code-design-transform-separation proposal: business logic lives
in the library, orchestration and persistence live in notebooks.

To make the shared code available to notebooks running on a Databricks cluster, a distribution
mechanism is required. Two approaches were evaluated: `%run` (and naive relative imports) and
wheel packaging via `pyproject.toml`.

---

## Decision

- Package `src/mock_platform/` as a Python wheel via `pyproject.toml` and `python -m build`
- Distribute the wheel to clusters via Asset Bundles `libraries` in job resource YAMLs
- `%run` and naive relative imports are rejected

---

## Why `%run` Fails on Clusters

`%run` is a Databricks magic command that executes another notebook or `.py` file. It appears to
solve the code-sharing problem but fails in practice for two reasons:

**Path resolution is fragile across environments.**
`%run path/to/file.py` resolves paths relative to the notebook's location in the Databricks
Workspace (or DBFS). When notebooks are deployed to different Workspace paths in `dev` vs `prod`,
the relative path breaks silently — the file may not be found, or a stale cached version may be
executed. There is no compile-time error; the failure only surfaces at runtime on the cluster.

**Naive relative imports do not work in Databricks notebooks.**
Python's module import system (`from ..transform import clean_orders`) requires the calling file
to be part of a Python package — i.e., the parent directory must contain an `__init__.py` and
the package must be on `sys.path`. Databricks notebooks are not executed as part of a package;
they are run as top-level scripts. Relative imports raise `ImportError` at runtime, and adding
the source directory to `sys.path` manually is fragile, non-reproducible, and environment-specific.

Both approaches require manual path management that differs between a developer's local machine,
a CI runner, and a Databricks cluster — a different failure mode in each environment.

---

## Wheel Packaging Integration

The wheel distribution pipeline maps directly onto the existing project structure:

| Step | Tool | Output |
|------|------|--------|
| Define package | `pyproject.toml` (`setuptools`, `src/` layout) | Package metadata |
| Build wheel | `python -m build --wheel --outdir dist/` | `dist/mock_platform-*.whl` |
| Upload to Workspace | `databricks bundle deploy` (`libraries` stanza) | Wheel on cluster classpath |
| Import in notebook | Standard Python: `from mock_platform.transform import clean_orders` | |

The `libraries` stanza in job resource YAMLs (`etl/resources/etl-pipeline.yml`,
`etl/resources/etl-e2e-test.yml`) references `../dist/*.whl`. On `bundle deploy`, the Databricks
CLI resolves the glob, uploads the wheel to the Workspace, and injects it into the cluster
configuration for the job. No manual DBFS copy or path manipulation is required.

**CI integration:** `test-unit.yaml` runs `pip install build && python -m build --wheel --outdir dist/`
after the test step on every PR. This verifies that the package builds successfully before a
`bundle deploy` could be attempted — packaging failures are caught in CI, not at deploy time.

**Local development:** Tests run via `pip install -e ".[dev]"` (editable install from the source
tree). No wheel build is required for local testing — changes to `src/mock_platform/` take
effect immediately. The wheel is only needed for cluster deployment.

---

## Trade-offs Accepted

- **Additional build step in CI:** `pip install build && python -m build` adds a small step to
  the CI workflow. This is standard Python toolchain; the overhead is negligible (~5–10s) and
  justified by catching packaging issues before they reach `bundle deploy`.
- **Wheel must be rebuilt before every `bundle deploy`:** Changes to `src/mock_platform/` require
  a new `bundle deploy` (not just `bundle run`) to propagate the updated wheel to the cluster.
  This is intentional: the wheel version deployed is always the one built from the current commit.
- **`dist/` is not committed:** The built wheel is a build artifact, not source. `dist/` is
  gitignored; CI and deploy always build fresh from source.

---

## Rejected Alternatives

**`%run`** — path fragility and environment coupling documented above. Also untestable outside
Databricks: a test suite that validates `%run`-based imports cannot run on a GitHub Actions runner
without a Databricks cluster. Rejected.

**DBFS direct copy (`dbutils.fs.cp`)** — requires a manually managed upload step outside of
CI/CD, is not reproducible, and creates an undeclared dependency on a DBFS path that may differ
between environments. Rejected.

**Inline functions duplicated across notebooks** — violates the code-design-transform-separation
principle. Transform logic becomes untestable in isolation and must be kept in sync across
multiple notebooks manually. Rejected.

**`setup.py` instead of `pyproject.toml`** — `setup.py` is the legacy build interface; `pyproject.toml`
with `setuptools` is the current standard (PEP 517/518). Both are technically equivalent for this
use case; `pyproject.toml` is used to align with current Python toolchain conventions.

---

## Consequences

- Every change to `src/mock_platform/` requires a `bundle deploy` (not just `bundle run`) to take
  effect on the cluster. Developers who run `bundle run` without a preceding `bundle deploy` after
  a code change will run against the previously deployed wheel version.
- The `dist/*.whl` glob in the job YAML means the package version in `pyproject.toml` does not
  need to be incremented on every deploy — the glob picks the latest built artifact. Version
  management becomes relevant only if multiple wheel versions need to coexist (e.g., pinned
  prod vs rolling dev).
- Unit tests on the GitHub Actions runner use `pip install -e ".[dev]"` — no wheel is involved.
  This means CI can validate transform logic without a Databricks cluster or a wheel build step,
  keeping the test feedback loop fast.
- Adding a new module to `src/mock_platform/` follows the same pattern: add the file, update
  tests, and the next `bundle deploy` will include it automatically via the `src/` layout
  discovery in `pyproject.toml`.
