# Hygiene

- Never include API keys, credentials, personal data, or other secrets in the repository.
- Add comments or documentation comments when logic is not self-evident.
- Add unit tests for core application logic; add UI tests only where unit tests cannot cover the behavior.
- Do not store usernames, passwords, or other sensitive data in `@AppStorage`; use the project’s approved secure-storage mechanism.
- If SwiftLint is configured, keep it free of warnings and errors.
- If the project uses string catalogs, follow its established localization conventions and generated-symbol configuration.
- Preview renderers and documentation tools are optional. Use them only when available and explicitly approved. If unavailable, review source code, state the verification limit, and do not launch, control, or automate GUI applications.
