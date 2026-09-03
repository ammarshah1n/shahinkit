# Design

## Creating a uniform design

Prefer project-approved shared constants or design tokens for standard fonts, colors, spacing, padding, rounding, and animation timing. Do not add a design system when the project already has a different convention.

## Flexible, accessible design

- Do not use `UIScreen.main.bounds` to infer available layout space. Prefer a supported layout API, or `GeometryReader` only when no suitable alternative exists.
- Avoid fixed frames unless the content remains correct across device sizes and Dynamic Type settings.
- Meet the platform’s minimum supported tap target; on iOS, this is generally 44 by 44 points.

## Standard system styling

- Prefer `ContentUnavailableView` for missing or empty content when it is available and fits the project design.
- With `searchable()`, use supported search-empty-state APIs rather than duplicating search text unnecessarily.
- Prefer `Label` to an `HStack` for a standard icon-and-text control.
- Prefer system hierarchical styles over manual opacity where they provide the required result.
- In `Form`, use `LabeledContent` for labeled controls when available and appropriate.
- `RoundedRectangle` initializers default to continuous cornering in current supported SDKs. Pass `style` explicitly only when overriding that default or when the project's target/toolchain conventions require the intent to be spelled out.

## Ensuring designs work for everyone

- Prefer `bold()` to `fontWeight(.bold)` so the system can choose an appropriate weight.
- Use other `fontWeight` values only for a clear design reason.
- Avoid unexplained hard-coded padding and stack spacing.
- Use SwiftUI `Color` or catalog colors rather than UIKit colors in SwiftUI code unless platform integration requires otherwise.
- Use `.caption2` sparingly and check its readability at supported Dynamic Type sizes.
