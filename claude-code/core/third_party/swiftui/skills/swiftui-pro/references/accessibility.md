# Accessibility

- Respect the user’s accessibility settings for fonts, colors, animations, and more.
- Do not force specific font sizes. Prefer Dynamic Type styles such as `.font(.body)` and `.font(.headline)`.
- If a custom font size is necessary, use an availability-appropriate scaling approach such as `@ScaledMetric` when supported by the project.
- Flag images with unclear VoiceOver output. Decorative images can use `Image(decorative:)` or `accessibilityHidden()`; meaningful images need an `accessibilityLabel()`.
- When Reduce Motion is enabled, replace large motion-based animations with a calmer alternative such as opacity.
- For complex or frequently changing button labels, consider `accessibilityInputLabels()` where it is available for the project.
- Image-label buttons need an accessible text label, even when the visible design is icon-led: `Button("Label", systemImage: "plus", action: myAction)`.
- Respect `.accessibilityDifferentiateWithoutColor` when color communicates meaning by adding icons, patterns, strokes, or another non-color cue.
- Apply the same label guidance to `Menu`; `Menu("Options", systemImage: "ellipsis.circle") { }` is more accessible than an image alone.
- Use `onTapGesture()` only when tap location or count is needed. Other tappable controls should normally be `Button`.
- If `onTapGesture()` is necessary, add appropriate accessibility traits such as `.accessibilityAddTraits(.isButton)`.
