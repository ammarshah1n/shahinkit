# Using modern SwiftUI API

Apply these recommendations only when the API is available for the project’s deployment target and supported platforms.

- Prefer `foregroundStyle()` to `foregroundColor()` when available.
- Prefer `clipShape(.rect(cornerRadius:))` to `cornerRadius()` when available.
- Prefer the modern `Tab` API to `tabItem()` when available.
- Prefer an `onChange()` overload that accepts zero or two parameters rather than the one-parameter variant when available.
- Do not use `GeometryReader` when a supported alternative such as `containerRelativeFrame()`, `visualEffect()`, or the `Layout` protocol fits the requirement.
- Prefer `sensoryFeedback()` to older UIKit haptic generators when it is available.
- Use `@Entry` for custom environment and related values only when the project supports it; otherwise retain the compatible key pattern.
- Prefer closure-based `overlay` APIs to deprecated overloads when available.
- Use supported toolbar placements rather than deprecated placements.
- Use automatic grammar agreement where the project supports it and its localizations need it.
- A shape can be filled and stroked with chained modifiers when supported by the project; do not add an overlay solely for the stroke.
- When the project enables generated asset symbols, prefer them, such as `Image(.avatar)`, to string asset names.
- Prefer a native web view only when it is available for the deployment target; otherwise use the project’s existing, approved integration.
- Pass an `enumerated()` sequence directly to `ForEach` when its supported overloads fit; do not materialize an array only for enumeration.
- Prefer `.scrollIndicators(.hidden)` over initializer-only indicator flags when available.
- Do not concatenate `Text` values with `+`; use interpolation or a localization-aware alternative.

```swift
let red = Text("Hello").foregroundStyle(.red)
let blue = Text("World").foregroundStyle(.blue)
Text("\(red)\(blue)")
```

## Using ObservableObject

If `ObservableObject` is required, such as for a Combine-based integration, explicitly import `Combine` when the project needs it. Prefer the project’s established observation model; do not migrate legacy code solely to satisfy this reference.
