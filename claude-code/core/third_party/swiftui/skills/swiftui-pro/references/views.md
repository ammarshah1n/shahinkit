# SwiftUI views

- Prefer dedicated `View` structs over large computed `some View` properties or methods when extraction improves clarity, identity, or reuse.
- Flag excessively long `body` properties and suggest focused subviews.
- Extract substantial button actions and business logic from layout code.
- Do not place non-trivial business logic inline in `task()`, `onAppear()`, or `body`.
- Put testable view logic in the project’s existing model or reducer layer where appropriate.
- Keep type declarations in files that match the project’s organization; do not split tightly coupled small types solely to satisfy this reference.
- Prefer a multiline `TextField` to `TextEditor` for short editable text when it meets the product requirements and project target.
- Pass an existing action directly to `Button` when that is clearer: `Button("Label", systemImage: "plus", action: myAction)`.
- Prefer `ImageRenderer` to older platform renderers when it is available and appropriate for the project.
- Prefer `#Preview` to `PreviewProvider` when the project target and toolchain support it; otherwise retain the compatible preview form.
- For `TabView(selection:)`, prefer a stable enum selection value over magic integers or strings when it fits the project model.

## Animating views

- Prefer `@Animatable` to manual `animatableData` only when the macro is supported by the toolchain; otherwise use the project’s compatible animation design.
- Supply a watched value to `animation(_:value:)` rather than using unconstrained animation modifiers.
- Chain animations with a `withAnimation` completion only when the project target supports that API; otherwise use a compatible, cancellation-aware sequence.
