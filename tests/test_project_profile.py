import json

import yaml
from conftest import ROOT
from jsonschema import Draft202012Validator


def test_project_yaml_matches_schema():
    schema = json.loads((ROOT / "schemas/project.schema.json").read_text())
    proj = yaml.safe_load((ROOT / "project.yaml").read_text())
    errs = [e.message for e in Draft202012Validator(schema).iter_errors(proj)]
    assert errs == [], errs


def test_uninitialized_has_no_assay_files():
    proj = yaml.safe_load((ROOT / "project.yaml").read_text())
    if not proj["initialized"]:
        assert not (ROOT / "schemas/samplesheet.assay.schema.json").exists()
