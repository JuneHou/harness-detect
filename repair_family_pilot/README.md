# Repair-family pilot

Preview build for one AgentDefect program and two persistent repairs. The estimator predicts a four-cell response table from donor measurements. This build stops at a semantic audit, offline tests, and, when resource caps and a runnable case exist, a construction screen plus a task-grid preview. It does not collect the 60-group suite.

## Install

Use `/data/wang/junh/envs/harnessfix`.

```bash
/data/wang/junh/envs/harnessfix/bin/python -m pytest tests
```

## Commands

```bash
python -m repair_family_pilot audit --config configs/pilot.yaml
python -m repair_family_pilot qualify --config configs/pilot.yaml
python -m repair_family_pilot freeze --config configs/pilot.yaml
python -m repair_family_pilot collect --dry-run --config configs/pilot.yaml
python -m repair_family_pilot report --config configs/pilot.yaml
```

`qualify` exits 3 when `max_model_calls` and `max_episodes` are unresolved. A missing `configs/budget.yaml` does not clear caps that a resolved manifest or `configs/pilot.yaml` already supplies. `collect` is refused in this build.

## Status values

`implementation_complete`, `data_blocked`, `partial_scientific_scope`, `pilot_complete_negative`, and `pilot_complete_supported`. This preview does not assign the last two. `pilot_complete_supported` is only for a later evaluation of zero-probe donor synthesis, and only as exploratory pilot support.
