from app.discovery.normalizer import normalize_capabilities
from app.models.capability import Capability


def test_normalize_chat():
    # Test 1: CHAT normalization
    assert normalize_capabilities("chat") == frozenset([Capability.CHAT])
    assert normalize_capabilities(["CHAT"]) == frozenset([Capability.CHAT])
    assert normalize_capabilities(Capability.CHAT) == frozenset([Capability.CHAT])


def test_normalize_embeddings():
    # Test 2: EMBEDDINGS normalization
    assert normalize_capabilities("embeddings") == frozenset([Capability.EMBEDDINGS])
    assert normalize_capabilities("embedding") == frozenset([Capability.EMBEDDINGS])
    assert normalize_capabilities(["EMBEDDINGS"]) == frozenset([Capability.EMBEDDINGS])


def test_normalize_multiple_capabilities():
    # Test 3: Multiple capabilities
    raw = ["chat", "tools", "streaming", "vision"]
    result = normalize_capabilities(raw)
    assert result == frozenset(
        [
            Capability.CHAT,
            Capability.TOOLS,
            Capability.STREAMING,
            Capability.VISION,
        ]
    )


def test_normalize_unknown_capability():
    # Test 4: Unknown provider capability must not crash, should be ignored
    raw = ["chat", "unknown-feature-xyz", 123, None]
    result = normalize_capabilities(raw)
    assert result == frozenset([Capability.CHAT])


def test_normalize_duplicate_capabilities():
    # Test 5: Duplicate provider capability values produce one canonical capability
    raw = ["chat", "chat", "CHAT", Capability.CHAT, "embeddings", "embeddings"]
    result = normalize_capabilities(raw)
    assert result == frozenset([Capability.CHAT, Capability.EMBEDDINGS])
    assert len(result) == 2
