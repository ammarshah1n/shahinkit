# Core rules

Apply these rules within the project's existing deployment targets, concurrency design, and persistence architecture.

- Autosave timing is not predictable enough for correctness-sensitive work. Prefer an explicit `save()` when the project needs persistence at a known point.
- There is no need to check `modelContext.hasChanges` before saving; call `save()` directly and handle errors according to project convention.
- `ModelContext` and model instances must never cross actor boundaries. Model containers and persistent identifiers are sendable; transfer an identifier and refetch in the destination context when work crosses actors.
- Put `@Relationship` on only one side of a relationship. Applying it to both sides creates a circular reference.
- Persistent identifiers are temporary before the first save. Temporary IDs start with a lowercase `t`, and saving assigns a new identifier. Save an object before relying on its identifier.
- Do not use `description` as an `@Model` property name; it is disallowed.
- Do not add property observers to `@Model` properties; they are ignored.
- `@Attribute(.externalStorage)` is a suggestion, not a requirement, and applies only to `Data` properties.
- `@Transient` properties are not persisted and need default values. They reset on fetch; prefer a computed property when a value is derived from stored data, reserving `@Transient` for expensive derived values.
- Prefer a specific migration schema, including for lightweight migrations, when it fits the project's existing migration architecture.
- Prefer an explicit relationship delete rule. `.nullify` is the default and can leave orphans or fail for a non-optional relationship; `.cascade` is common but must match the domain's ownership rules.
- Do not use `@Query` outside SwiftUI views. Use `ModelContext.fetch(FetchDescriptor<...>())` in non-view code.
- For a count-only query, consider `ModelContext.fetchCount()` with a fetch descriptor. It does not live-update unless another mechanism triggers an update.
- When a fetch will use known relationships, consider `relationshipKeyPathsForPrefetching` to fetch them up front.
- When a fetch needs only a subset of stored values, consider `propertiesToFetch` rather than fetching every property.
- SwiftData can infer inverse relationships incorrectly. Be explicit with `@Relationship` and its inverse where the model needs one.
- Use `#Unique` only when the deployment target supports it (macOS 15, iOS 18, tvOS 18, or watchOS 11 and later). Write it at most once per model; for multiple constraints, use separate key-path arrays in that declaration, such as `#Unique<Foo>([\.email], [\.username])`. Preserve the project's existing uniqueness strategy on earlier targets.
- Enums stored in a model must conform to `Codable`; enums with associated values are supported.
