# Using SwiftData with CloudKit

Apply these rules only when the project is already configured to use SwiftData with CloudKit. Do not enable CloudKit, change entitlements, or create external resources as part of this guidance.

- Do not use `@Attribute(.unique)` or `#Unique`; CloudKit does not support them, and their use can also make local data fail.
- Give every model property a default value or make it optional.
- Make every relationship optional.
- Indexes and subclasses are supported only when the project's declared deployment target supports their required platform version.
- Design for eventual consistency: synchronized data can arrive later, so code must function before synchronization completes.
