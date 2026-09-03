# Indexing

Apply this guidance only after confirming that the project's declared deployment target supports SwiftData indexes: iOS 18 or the corresponding coordinated platform release. If that capability is unavailable for the target, do not add `#Index`; explain the constraint and use only a compatible design.

Indexes can speed up reads but add write cost. They may not suit data that is written frequently and read rarely, such as logs.

Use separate key-path arrays for single-property indexes:

```swift
@Model class Article {
    #Index<Article>([\.type], [\.author])

    var type: String
    var author: String
    var publishDate: Date

    init(type: String, author: String, publishDate: Date) {
        self.type = type
        self.author = author
        self.publishDate = publishDate
    }
}
```

Use a grouped key-path array for a compound index when those properties are queried together:

```swift
#Index<Article>([\.type], [\.type, \.author])
```
