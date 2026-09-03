# Swift

- Prefer Swift-native string methods over Foundation equivalents when they express the same behavior.
- Prefer modern Foundation APIs, such as `URL.documentsDirectory` and `appending(path:)`, only when they are available for the project target.
- Prefer `FormatStyle` APIs to C-style number formatting for user-visible values when supported.
- Prefer static member lookup where it improves clarity, such as `.circle` rather than `Circle()`.
- Avoid force unwraps and force `try` unless failure is genuinely unrecoverable. Prefer explicit error handling or a clear `fatalError()` for an impossible state.
- For user-entered text filtering, use a locale-aware comparison appropriate for the product’s matching requirements.
- Prefer `Double` to `CGFloat` unless an API requires `CGFloat`, an optional, or `inout` behavior.
- Use `count(where:)` rather than allocating a filtered array only to count it when the toolchain supports it.
- Prefer `Date.now` to `Date()` where it improves clarity.
- Do not add UIKit or AppKit imports merely for image types already made available through SwiftUI; retain imports required by platform-specific code.
- Use `PersonNameComponents` and locale-aware formatting when presenting people’s names.
- Centralize repeated sort order when a type’s natural ordering is stable and project conventions support `Comparable`.
- Avoid manual date formats for display. If a manual display format is necessary, use locale-correct year symbols; interchange formats may have separate requirements.
- Prefer modern `Date` parsing strategies where they are available and fit the input format.
- Do not silently swallow errors triggered by a user action; present or propagate them through the project’s error-handling design.
- Prefer optional-binding shorthand and single-expression return omission where supported and readable.

```swift
var tileColor: Color {
    if isCorrect {
        .green
    } else {
        .red
    }
}
```

## Swift concurrency

- Prefer `async` and `await` equivalents when they are available and fit the project’s concurrency model.
- Avoid Grand Central Dispatch for new code when structured concurrency is available; retain it where required by a supported API or compatibility boundary.
- Prefer `Task.sleep(for:)` to nanosecond-based sleep when supported.
- Protect mutable shared state with an actor, `@MainActor`, or the project’s documented isolation strategy.
- Check the project’s default actor isolation before suggesting `MainActor.run()`.
- Treat `Task.detached()` as exceptional and review its isolation, cancellation, and lifetime carefully.
