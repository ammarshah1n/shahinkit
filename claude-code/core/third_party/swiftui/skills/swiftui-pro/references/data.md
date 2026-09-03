# Data flow, shared state, and property wrappers

Keep SwiftUI body code and logic code separate where it improves clarity and testability. The project’s architecture remains authoritative.

## Shared state

- Mark `@Observable` classes with `@MainActor` unless the project configures main-actor default isolation or has a documented alternative.
- For new code, prefer the project’s established observation and ownership pattern. Where appropriate, this can be `@Observable` with `@State` ownership and `@Bindable` or `@Environment` passing.
- Treat `ObservableObject`, `@Published`, `@StateObject`, `@ObservedObject`, and `@EnvironmentObject` as valid for legacy or integration contexts; do not force a migration without project approval.

## Local state

- Mark locally owned `@State` as `private` where practical.
- A view may keep an expensive class instance such as `CIContext` in `@State` as a cache when the project supports that pattern and no observation is needed.

## Bindings

- Avoid constructing `Binding(get:set:)` inside `body` when an existing binding plus `onChange()` makes effects clearer.
- For numeric `TextField` input, bind a numeric type and use a format initializer when supported. Use an appropriate keyboard type only on platforms where it is meaningful.

## Working with data

- Prefer `Identifiable` models where it makes identity stable and clear; do not change public model contracts only to avoid `id:`.
- Do not use `@AppStorage` inside an `@Observable` class as a substitute for observable state updates.

## SwiftData

- If only a query count is needed, consider `ModelContext.fetchCount()` where available. It does not live-update unless another mechanism causes a refresh.
- If the project uses SwiftData with CloudKit, follow its model constraints: avoid `@Attribute(.unique)`, give properties defaults or make them optional, and model relationships appropriately for the project’s schema.
