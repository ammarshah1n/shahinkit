# Class inheritance

Apply this guidance only after confirming that the project's declared deployment target supports SwiftData model inheritance: iOS 26 or the corresponding coordinated platform release. If the project also supports an earlier release, retain its existing availability strategy; do not introduce inheritance as if it were universally available.

Model subclassing is uncommon. Add it only when it materially benefits the existing architecture; protocols or composition are often simpler.

Child models must be explicitly marked available for the required release even when that release is the minimum deployment target.

```swift
@Model class Article {
    var type: String

    init(type: String) {
        self.type = type
    }
}

@available(iOS 26, *)
@Model class Tutorial: Article {
    var difficulty: Int

    init(difficulty: Int) {
        self.difficulty = difficulty
        super.init(type: "Tutorial")
    }
}

@available(iOS 26, *)
@Model class News: Article {
    var topic: String

    init(topic: String) {
        self.topic = topic
        super.init(type: "News")
    }
}
```

Mark both parent and child classes with `@Model`. When creating a model container schema, list the parent and every child explicitly; SwiftData does not infer the connection.

A relationship to a parent model can contain that parent or any subclass:

```swift
@Model class Magazine {
    @Relationship(deleteRule: .cascade) var articles: [Article]

    init(articles: [Article]) {
        self.articles = articles
    }
}
```

If a relationship supports only one child type, declare that type. Avoid deep inheritance merely to filter a subset of children; it adds migration complexity.

## Filtering with subclasses

A query for a child returns that child type. A query for the parent includes child instances.

```swift
@Query private var tutorials: [Tutorial]
@Query private var articles: [Article]
```

Use `is` to filter selected child types while preserving the parent result type:

```swift
@Query(filter: #Predicate<Article> {
    $0 is Tutorial || $0 is News
}) private var tutorialsAndNews: [Article]
```

The result elements remain `Article`; typecast before accessing child-specific members. Typecasts can also filter child properties inside a predicate:

```swift
@Query(filter: #Predicate<Article> { article in
    if let tutorial = article as? Tutorial {
        tutorial.difficulty < 3
    } else if let news = article as? News {
        news.topic == "General"
    } else {
        false
    }
}) private var frontPageArticles: [Article]
```
