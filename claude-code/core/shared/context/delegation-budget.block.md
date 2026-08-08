<!-- SHAHINKIT:DELEGATION-BUDGET:START -->
Budget preset is `{{BUDGET_PRESET}}`; delegation mode is `{{DELEGATION_MODE}}`.
Roles resolve explicitly: `controller` uses `{{ROLE_MODEL_CONTROLLER}}`,
`research` uses `{{ROLE_MODEL_RESEARCH}}`, `implementation` uses
`{{ROLE_MODEL_IMPLEMENTATION}}`, `review` uses `{{ROLE_MODEL_REVIEW}}`, and
`mechanical` uses `{{ROLE_MODEL_MECHANICAL}}`. No role inherits or substitutes
another role's model, effort, or authority.
Implementation touching more than {{INLINE_FILE_LIMIT}} files or changing more
than {{INLINE_LINE_LIMIT}} lines is delegated to a worker, not written inline.
Work under that threshold may be done inline; do not dispatch a worker when the
brief costs more than the change. The controller keeps planning, architecture,
final synthesis, and acceptance at every budget, and never delegates them.
{{CROSS_HOST_ROUTE}}
<!-- SHAHINKIT:DELEGATION-BUDGET:END -->
