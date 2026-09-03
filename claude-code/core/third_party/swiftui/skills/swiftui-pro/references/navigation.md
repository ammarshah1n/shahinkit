# Navigation and presentation

Apply these recommendations only when they are available for the project’s deployment target and platform.

- Use `NavigationStack` or `NavigationSplitView` where they fit the project; retain a compatible navigation approach for older targets.
- Prefer value-based `navigationDestination(for:)` when appropriate. Do not mix it with destination-bearing `NavigationLink` patterns in the same hierarchy without a deliberate compatibility reason.
- Register a value-based destination once per data type in a hierarchy unless the project architecture requires a different scope.

## Alerts, confirmation dialogs, and sheets

- Attach `confirmationDialog()` near the control that triggers it when that produces the intended presentation behavior.
- Omit an alert whose only action is a default dismissal unless the message itself is needed.
- For optional data, prefer `sheet(item:)` to `sheet(isPresented:)` when the item identity and project target support it.
- When a sheet view accepts only the presented item, `content: SomeView.init` can be clearer than an equivalent closure.
