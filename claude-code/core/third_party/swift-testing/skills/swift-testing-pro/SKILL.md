---
name: swift-testing-pro
description: Writes, reviews, and improves Swift Testing code using modern APIs and best practices. Use when reading, writing, or reviewing projects that use Swift Testing.
---

Write and review Swift Testing code for correctness, modern API usage, and adherence to project conventions. Report only genuine problems - do not nitpick or invent issues.

Review process:

1. Ensure tests follow core Swift Testing conventions using `references/core-rules.md`.
1. Validate test structure, assertions, dependency injection, and other best practices using `references/writing-better-tests.md`.
1. Check async tests, confirmations, time limits, actor isolation, and networking mocks using `references/async-tests.md`.
1. Ensure new features like raw identifiers, test scopes, exit tests, and attachments are used correctly using `references/new-features.md`.
1. If migrating from XCTest, follow the conversion guidance in `references/migrating-from-xctest.md`.

If doing partial work, load only the relevant reference files.


## Core Instructions

Treat the project configuration and installed toolchain as authoritative. If Swift Testing or a requested API is unavailable, say so, use the project's supported testing approach only when requested, and do not change toolchains, dependencies, or project configuration without explicit user approval.

Never automatically install, commit, push, publish, submit, send, book, pay, delete, or mutate an external system. Require explicit user approval.

- Use modern Swift concurrency only where the project's installed toolchain supports it.
- Use Swift Testing for new unit and integration tests only where the project supports it. Do not migrate existing XCTest tests unless requested.
- Swift Testing does not support UI tests. Do not create or automate UI tests; report that this skill's UI-test capability is unavailable and leave the project's existing approach unchanged unless the user explicitly requests a separate, project-supported solution.
- Use the project's existing feature-based test layout and conventions.

Swift Testing evolves with each Swift release. Treat these references as guidance, verify named APIs against the installed toolchain, and prefer the project's established patterns when they differ.


## Output Format

If the user asks for a review, organize findings by file. For each issue:

1. State the file and relevant line(s).
2. Name the rule being violated.
3. Show a brief before/after code fix.

Skip files with no issues. End with a prioritized summary of the most impactful changes to make first.

If the user asks you to write or improve tests, follow the same rules above but make the changes directly instead of returning a findings report.

Example output:

### UserTests.swift

**Line 5: Use struct, not class, for test suites.**

```swift
// Before
class UserTests: XCTestCase {

// After
struct UserTests {
```

**Line 12: Use `#expect` instead of `XCTAssertEqual`.**

```swift
// Before
XCTAssertEqual(user.name, "Taylor")

// After
#expect(user.name == "Taylor")
```

**Line 30: Use `#require` for preconditions, not `#expect`.**

```swift
// Before
#expect(users.isEmpty == false)
let first = users.first!

// After
let first = try #require(users.first)
```

### Summary

1. **Fundamentals (high):** Test suite on line 5 should be a struct, not a class inheriting from `XCTestCase`.
2. **Migration (medium):** `XCTAssertEqual` on line 12 should be migrated to `#expect`.
3. **Assertions (medium):** Force-unwrap on line 30 should use `#require` to unwrap safely and stop the test early on failure.

End of example.


## References

- `references/core-rules.md` - core Swift Testing rules: structs over classes, `init`/`deinit` over setUp/tearDown, parallel execution, parameterized tests, `withKnownIssue`, and tags.
- `references/writing-better-tests.md` - test hygiene, structuring tests, hidden dependencies, `#expect` vs `#require`, `Issue.record()`, `#expect(throws:)`, and verification methods.
- `references/async-tests.md` - serialized tests, `confirmation()`, time limits, actor isolation, testing pre-concurrency code, and mocking networking.
- `references/new-features.md` - raw identifiers, range-based confirmations, test scoping traits, exit tests, attachments, `ConditionTrait.evaluate()`, and the updated `#expect(throws:)` return value.
- `references/migrating-from-xctest.md` - XCTest-to-Swift Testing conversion steps, assertion mappings, and floating-point tolerance via Swift Numerics.
