# Role Models

`roles.schema.json` is canonical adapter-input contract. Every role carries `default_model`, `resolved_model`, and documented `shahinkit.models.<role>` override setting.

Renderer starts `resolved_model` at host default. User may set any role's override before rendering; renderer copies override into that same role's `resolved_model`. No role may inherit controller or peer value. Adapters read only `roles.<role>.resolved_model`.

Host templates belong to later adapter work. This directory defines no host config, approval, sandbox, network, trust, or credential setting.
