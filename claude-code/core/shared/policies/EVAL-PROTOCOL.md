# Eval Protocol

## Protocol

1. Pick a task directory under `tasks/T01` through `tasks/T10`.
2. Run the candidate model on `brief.md` with the same input files and constraints.
3. Grade the output with `rubric.md`.
4. Record the result in `scores.csv`.

Graders must be a DIFFERENT model than the candidate model.

Each task is graded as:

- Each rubric item: binary `0` or `1`.
- `rubric_pass_count`: sum of passed binary items.
- `rubric_total`: total binary items in that task rubric.
- `overall_5`: holistic score from `1` to `5`.

## Promotion Rule

A model is promoted to the strong-controller profile when it scores within 1 point of the incumbent's baseline on at least 8 of the 10 tasks.

Use the same `config_label` consistently for config-change A/B tests so pass rates can be grouped across runs.

## Profiles

| Profile | Operating mode | Gates |
|---|---|---|
| `strong-controller` | Lean/trusted. Fewer choreography rails. | Must still preserve C01-C16, done verification, and tier policy. |
| `mid-controller` | Choreographed/gated. | Research tables, spec-drift table, cross-provider review, phase reassertion, and explicit verification ledger. |

NEW MODEL ARRIVES -> starts mid-controller -> earns promotion via eval, never by marketing tier.

## Improvement Metrics

### 1. Eval Pass Rate Per Config Label

Metric name: eval pass rate per `config_label`.

Definition: a task pass means all binary rubric criteria pass and `overall_5 >= 4`.

### 2. Corrections Per Week

Metric name: corrections-per-week.

Definition: count dated entries from `claude-code/core/docs/rules/corrections-log.md` across local repos by ISO week.

### 3. Redo Rate

Metric name: redo-rate.

Definition: fraction of delegated fleet jobs whose `.status` files indicate a retry, failure, rework, or changes-required result.
