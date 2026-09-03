# Performance

- Prefer modifier-value changes to unnecessary structural branching when doing so preserves view identity and remains readable.
- Avoid `AnyView` unless type erasure is necessary; prefer `@ViewBuilder`, `Group`, generics, or extracted views where appropriate.
- For a static, opaque scroll background, consider `scrollContentBackground(.visible)` when it improves the supported platform’s rendering behavior.
- Extract substantial reusable view sections into dedicated views rather than computed `some View` properties when that improves identity, reuse, or profiling results.
- Keep view initializers small. Move non-trivial work to an appropriate lifecycle or model layer.
- Treat `body` as frequently evaluated; avoid repeated sorting, filtering, or expensive calculation in it.
- Prefer native format styles over stored formatter instances when they express the required output.
- Avoid repeated expensive transforms in `List` and `ForEach` initializers.
- Derive transformed data from its source of truth. Cache only with explicit invalidation so the UI cannot become stale.
- For large `ScrollView` data sets, use lazy stacks where measurement or profiling shows they are appropriate.
- Prefer `task()` for asynchronous work when the project target supports its cancellation behavior; otherwise use the project’s established lifecycle mechanism.
- Avoid storing escaping `@ViewBuilder` closures on a view when a built view value is sufficient.

```swift
struct CardView<Content: View>: View {
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading) {
            content
        }
        .padding()
        .background(.ultraThinMaterial)
        .clipShape(.rect(cornerRadius: 8))
    }
}
```
