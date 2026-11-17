import yaml
from check_claims import main
from conftest import ROOT


def _write(tmp_path, claim):
    p = tmp_path / "claims.yaml"
    p.write_text(yaml.safe_dump({"claims": [claim]}))
    return str(p)


BASE = dict(
    id="C1",
    text="x",
    level="statistical",
    evidence=["README.md"],
    decisions=[],
    criteria_set_before_results=True,
    gates=dict(execution="pending", design="pending", inference="pending", biological="pending", external="n/a"),
)


def test_committed_claims_ok():
    assert main(str(ROOT / "claims/claims.yaml")) == 0


def test_pending_ok(tmp_path):
    assert main(_write(tmp_path, BASE)) == 0


def test_overclaim_fails(tmp_path):
    c = dict(BASE, level="mechanism", gates=dict(BASE["gates"], execution="pass", design="pass", inference="pass"))
    assert main(_write(tmp_path, c)) == 1


def test_supported_claim_ok(tmp_path):
    c = dict(BASE, gates=dict(BASE["gates"], execution="pass", design="pass", inference="pass"))
    assert main(_write(tmp_path, c)) == 0


def test_mechanism_needs_reviewer(tmp_path):
    g = dict(BASE["gates"], execution="pass", design="pass", inference="pass", biological="pass")
    assert main(_write(tmp_path, dict(BASE, level="mechanism", gates=g))) == 1
    assert main(_write(tmp_path, dict(BASE, level="mechanism", gates=g, reviewer="PI"))) == 0


def test_criteria_must_be_preregistered(tmp_path):
    assert main(_write(tmp_path, dict(BASE, criteria_set_before_results=False))) == 1
