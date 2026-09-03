# Working with predicates

SwiftData predicates support a subset of Swift. Some unsupported expressions fail to compile; others compile and fail at runtime. Use only stored model data in predicates.

## String matching

Use `localizedStandardContains()` for normal user-facing string matching rather than `lowercased().contains()` or similar transformations.

```swift
@Query(filter: #Predicate<Movie> {
    $0.name.localizedStandardContains("titanic")
}) private var movies: [Movie]
```

## Prefixes

`hasPrefix()` and `hasSuffix()` are not supported in SwiftData predicates. Use `starts(with:)` for prefix matching.

```swift
@Query(filter: #Predicate<Website> {
    $0.type.starts(with: "https:")
}) private var websites: [Website]
```

## Unsupported predicates

These common operations are unsupported:

- `String.hasSuffix()`
- `String.lowercased()`
- `Sequence.map()`
- `Sequence.reduce()`
- `Sequence.count(where:)`
- `Collection.first`
- Custom operators

## Runtime hazards

Use `!` for a non-empty relationship check; `isEmpty == false` can compile then fail at runtime.

```swift
@Query(filter: #Predicate<Movie> { !$0.cast.isEmpty }, sort: \Movie.name)
private var movies: [Movie]
```

Do not predicate on computed properties, `@Transient` properties, custom `Codable` struct data, or regular expressions. They can compile but fail at runtime. Predicates must use data stored by `@Model` classes.
