# OpenCode static Caveman plugin

`plugin.js` uses OpenCode’s native message and system-transform hooks. It keeps
only current selected mode (`full` by default) in plugin memory, then injects
that mode on next turn. `caveman-config.js` is pure: explicit input only,
defaulting to `full`; it reads no environment, files, private configuration,
or secrets.

No session lifecycle handler, flag file, persistent state, cache, telemetry, or
raw event retention is shipped. Message text is inspected only to select a
whitelisted mode and is never stored. `off` removes next-turn reinforcement.
