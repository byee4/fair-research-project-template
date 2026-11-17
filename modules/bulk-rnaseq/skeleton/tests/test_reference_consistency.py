"""Chromosome naming in references must match config (agents often mix chr1 / 1)."""

import pytest
import yaml
from conftest import ROOT


@pytest.mark.parametrize("cfg", ["config/config.yaml", "tests/fixtures/mini/config.yaml"])
def test_chrom_naming(cfg):
    c = yaml.safe_load((ROOT / cfg).read_text())["genome"]
    sizes = ROOT / c["chrom_sizes"]
    if not sizes.exists():
        pytest.skip(f"{sizes} not present yet (reference not downloaded)")
    names = [ln.split("\t")[0] for ln in sizes.read_text().splitlines() if ln]
    ucsc = all(n.startswith("chr") for n in names)
    assert ucsc == (c.get("chrom_naming") == "UCSC"), (
        f"{sizes} naming does not match chrom_naming={c.get('chrom_naming')}"
    )
