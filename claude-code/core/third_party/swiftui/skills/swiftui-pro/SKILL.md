---
name: swiftui-pro
description: Review SwiftUI code for correctness, appropriate API use, accessibility, maintainability, and performance. Use when reading, writing, or reviewing SwiftUI projects.
---

Review Swift and SwiftUI code against the project’s requirements and conventions. Report genuine problems only; do not invent issues or nitpick.

Never automatically install, commit, push, publish, submit, send, book, pay, delete, or mutate an external system. Require explicit user approval.

The project’s configured deployment target, supported platforms, toolchain, architecture, conventions, and approved dependencies are authoritative. Recommend an API only when it is available for that project; otherwise explain the constraint and offer a compatible alternative. Do not introduce UIKit, third-party frameworks, or architectural changes unless the project requires or approves them.

Preview renderers and documentation tools are optional. Use them only when available and approved; when unavailable, review the source, state what could not be verified, and do not launch, control, or automate GUI applications. This skill does not require any companion skill.

## Review process

1. Check applicable modern API guidance in `references/api.md`.
2. Check views, modifiers, and animations using `references/views.md`.
3. Validate data flow using `references/data.md`.
4. Check navigation using `references/navigation.md`.
5. Check accessible design using `references/design.md` and `references/accessibility.md`.
6. Check efficiency using `references/performance.md`.
7. Check Swift practices using `references/swift.md`.
8. Finish with `references/hygiene.md`.

For a partial review, load only the relevant references. If the project target or toolchain is unknown, ask for it or limit findings to APIs whose availability can be established from the project.

## Output format

Organize findings by file. For each issue:

1. State the file and relevant line(s).
2. Name the rule being violated.
3. Show a brief before/after fix that is compatible with the project.

Skip files with no issues. End with a prioritized summary of the most impactful changes.

### Example

#### ContentView.swift

**Line 12: Prefer `foregroundStyle()` where it is available for this project.**

```swift
// Before
Text("Hello").foregroundColor(.red)

// After
Text("Hello").foregroundStyle(.red)
```

**Line 24: Give an icon-only control an accessible label.**

```swift
// Before
Button(action: addUser) {
    Image(systemName: "plus")
}

// After
Button("Add user", systemImage: "plus", action: addUser)
```

#### Summary

1. **Accessibility (high):** Add accessible labels to icon-only controls.
2. **API (medium):** Use supported modern styling APIs where appropriate.

## References

- `references/accessibility.md` — Dynamic Type, VoiceOver, Reduce Motion, and other accessibility requirements.
- `references/api.md` — modern API guidance and availability-aware replacements.
- `references/design.md` — accessible, flexible system design.
- `references/hygiene.md` — maintainability, credentials, tests, and optional tools.
- `references/navigation.md` — navigation and presentation.
- `references/performance.md` — efficient SwiftUI rendering.
- `references/data.md` — data flow and property wrappers.
- `references/swift.md` — modern Swift and concurrency.
- `references/views.md` — view structure, composition, and animation.
