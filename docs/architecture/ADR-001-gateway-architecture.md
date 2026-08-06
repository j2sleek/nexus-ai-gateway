# ADR-001: Gateway Architecture

## 1. Goals
- **Provider Agnostic:** Abstract underlying providers via a unified interface.
- **OpenAI/Anthropic Compatible:** Native interface support for common API standards.
- **Dynamic Model Discovery:** Automatic normalization of model metadata.
- **Intelligent Routing:** Deterministic capability-aware selection.
- **Streaming Support:** First-class handling for real-time model output.
- **High Availability:** Health-aware selection and failover.
- **Extensibility:** Simple plugin architecture for new providers.

## 2. Request Flow
```mermaid
sequenceDiagram
    participant C as Client
    participant A as FastAPI/Gateway
    participant R as RouteResolver
    participant Reg as ModelRegistry
    participant PReg as ProviderRegistry
    participant P as BaseProvider
    participant Con as ConcreteProvider

    C->>A: Request
    A->>A: Validation/Auth
    A->>R: Resolve(requested_model, capability)
    R->>Reg: Get Model Info
    Reg->>PReg: Get Provider
    PReg->>P: Delegate Call
    P->>Con: Execute
    Con-->>A: Normalized Response
    A-->>C: Response/Stream
```

## 3. Registry Lookup Complexity
- **Exact model lookup:** $O(1)$
- **Indexed lookups:** $O(k)$ (where k = number of matching records)

## 4. Provider Plugin Architecture
The startup lifecycle orchestrates provider registration through `ProviderRegistry`. Providers remain isolated implementations of `BaseProvider`. Adding a new provider simply requires:
1. Implement `BaseProvider`.
2. Add provider module.
3. Register in `main.py` lifespan.
4. Registry/Discovery naturally include it in candidate lists.

## 5. Data Ownership
- **Configuration:** Immutable startup settings (`pydantic-settings`).
- **Provider instances:** Owned by `ProviderRegistry`.
- **Model metadata:** Owned by `ModelRegistry`.
- **Discovery state:** Owned by `DiscoveryManager`.
- **Routing decisions:** Ephemeral (per-request).
- **Runtime metrics:** Aggregated by metrics middleware/collectors.

## 6. Architecture Diagram
```mermaid
graph TD
    Client --> API_Layer[API Layer]
    API_Layer --> Auth[Auth/Validation]
    Auth --> RouteResolver[Route Resolver]
    RouteResolver --> ModelRegistry[Model Registry]
    ModelRegistry --> ProviderRegistry[Provider Registry]
    ProviderRegistry --> BaseProvider[BaseProvider]
    BaseProvider --> ConcreteProviders[Concrete Providers]
    ConcreteProviders --> LiteLLM[LiteLLM Proxy]
    LiteLLM --> ExternalModels[External Models]
```
