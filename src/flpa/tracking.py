"""Log verified benchmark CSVs and figures to a shared W&B project."""

import argparse
import json
import os
from pathlib import Path

import pandas as pd


def track_bundle(directory: Path, mode: str, project: str) -> dict:
    """Log one experiment with a named ledger row per trial and its artifacts."""
    import wandb

    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    plan = manifest["plan"]
    name = f"{plan['experiment_id']}-{plan['profile']}"
    with wandb.init(
        project=project, group=plan["experiment_id"], name=name, job_type=plan["experiment_type"],
        config={"plan": plan, "environment": manifest["environment"]}, mode=mode, save_code=False,
        settings=wandb.Settings(disable_git=True, console="off"),
    ) as run:
        tables = {
            key: wandb.Table(dataframe=pd.read_csv(directory / filename))
            for key, filename in (("trials", "raw.csv"), ("summary", "summary.csv"), ("paired", "paired.csv"))
        }
        run.log(tables)
        run.summary.update(manifest["counts"])
        artifact = wandb.Artifact(f"{name}-benchmark", type="benchmark-results")
        artifact.add_file(str(directory / "manifest.json"), name="manifest.json")
        for filename in manifest["sha256"]:
            artifact.add_file(str(directory / filename), name=filename)
        run.log_artifact(artifact)
        record = {"project": project, "mode": mode, "id": run.id, "name": name, "url": run.url}

    print(json.dumps(record, ensure_ascii=False))
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--mode", choices=("offline", "online"), default="offline")
    parser.add_argument("--project", default=os.environ.get("WANDB_PROJECT", "hcmus-flpa-clustering"))
    args = parser.parse_args()
    record = track_bundle(args.directory, args.mode, args.project)
    (args.directory / "tracking.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
