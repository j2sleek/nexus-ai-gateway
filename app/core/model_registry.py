class ModelRegistry:
    def register(model: ModelInfo)

    def register_many(models: Iterable[ModelInfo])

    def get(model_id: str)

    def all()

    def providers()

    def by_provider(provider: str)

    def by_capability(capability: Capability)

    def clear()
