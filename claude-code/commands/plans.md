# `/plans`

Use the `plans` skill for a batch of multiple changes or ideas.

Expected shape:

1. Parse the list into task groups.
2. Identify dependencies between groups.
3. Run independent groups in parallel where safe.
4. Produce a plan per group or a shared mission plan if outputs are coupled.
5. Stop for plan vetting unless the user explicitly requested full auto execution.
