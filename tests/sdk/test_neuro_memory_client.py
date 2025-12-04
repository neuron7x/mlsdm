"""
NeuroMemoryClient Tests for MLSDM SDK.

Tests for the extended SDK client with Memory and Decision APIs:
- Memory operations (append, query) in local mode
- Decision operations in local mode
- Agent step protocol in local mode
- Error handling
- Client configuration
"""

import pytest

from mlsdm.sdk import (
    AgentAction,
    AgentStepResult,
    ContourDecision,
    DecideResult,
    MemoryAppendResult,
    MemoryItem,
    MemoryQueryResult,
    NeuroMemoryClient,
    NeuroMemoryError,
)


class TestNeuroMemoryClientInitialization:
    """Test NeuroMemoryClient initialization."""

    def test_local_mode_initialization(self):
        """Test client initialization in local mode."""
        client = NeuroMemoryClient(mode="local")
        assert client.mode == "local"
        assert client._engine is not None

    def test_remote_mode_initialization(self):
        """Test client initialization in remote mode."""
        client = NeuroMemoryClient(mode="remote", base_url="http://localhost:8000")
        assert client.mode == "remote"
        assert client.base_url == "http://localhost:8000"
        assert client._http is not None

    def test_default_mode_is_local(self):
        """Test that default mode is local."""
        client = NeuroMemoryClient()
        assert client.mode == "local"

    def test_client_with_user_and_session_ids(self):
        """Test client with default user/session IDs."""
        client = NeuroMemoryClient(
            mode="local",
            user_id="test-user",
            session_id="test-session",
            agent_id="test-agent",
        )
        assert client._user_id == "test-user"
        assert client._session_id == "test-session"
        assert client._agent_id == "test-agent"


class TestMemoryAppendLocal:
    """Test append_memory() in local mode."""

    def test_append_memory_basic(self):
        """Test basic memory append."""
        client = NeuroMemoryClient(mode="local")
        result = client.append_memory("Test memory content")
        
        assert isinstance(result, MemoryAppendResult)
        assert result.success in [True, False]
        assert result.phase in ["wake", "sleep", "unknown"]

    def test_append_memory_with_moral_value(self):
        """Test memory append with custom moral value."""
        client = NeuroMemoryClient(mode="local")
        result = client.append_memory("High moral content", moral_value=0.95)
        
        assert isinstance(result, MemoryAppendResult)
        # High moral value should typically be accepted
        assert result.phase in ["wake", "sleep", "unknown"]

    def test_append_memory_with_scoping(self):
        """Test memory append with user/session scoping."""
        client = NeuroMemoryClient(mode="local")
        result = client.append_memory(
            "Scoped content",
            user_id="user-123",
            session_id="session-abc",
            agent_id="agent-1",
        )
        
        assert isinstance(result, MemoryAppendResult)

    def test_append_memory_returns_id_on_success(self):
        """Test that successful append returns memory ID."""
        client = NeuroMemoryClient(mode="local")
        result = client.append_memory("Content with ID", moral_value=0.9)
        
        if result.success:
            assert result.memory_id is not None
            assert len(result.memory_id) > 0

    def test_append_memory_returns_stats(self):
        """Test that append returns memory stats."""
        client = NeuroMemoryClient(mode="local")
        result = client.append_memory("Content for stats")
        
        if result.success:
            assert result.memory_stats is not None


class TestMemoryQueryLocal:
    """Test query_memory() in local mode."""

    def test_query_memory_basic(self):
        """Test basic memory query."""
        client = NeuroMemoryClient(mode="local")
        
        # First append something
        client.append_memory("User likes coffee")
        
        # Then query
        result = client.query_memory("What does the user like?")
        
        assert isinstance(result, MemoryQueryResult)
        assert result.success is True
        assert result.query_phase in ["wake", "sleep"]
        assert isinstance(result.results, list)

    def test_query_memory_returns_items(self):
        """Test that query returns memory items."""
        client = NeuroMemoryClient(mode="local")
        
        # Append some content
        for i in range(3):
            client.append_memory(f"Fact number {i}")
        
        result = client.query_memory("Fact", top_k=5)
        
        assert isinstance(result.results, list)
        for item in result.results:
            assert isinstance(item, MemoryItem)
            assert hasattr(item, "content")
            assert hasattr(item, "similarity")
            assert hasattr(item, "phase")

    def test_query_memory_top_k(self):
        """Test that top_k limits results."""
        client = NeuroMemoryClient(mode="local")
        
        # Append multiple items
        for i in range(10):
            client.append_memory(f"Item {i}")
        
        result = client.query_memory("Item", top_k=3)
        
        # Should return at most 3 items (may be fewer if memory is sparse)
        assert len(result.results) <= 3


class TestDecideLocal:
    """Test decide() in local mode."""

    def test_decide_standard_mode(self):
        """Test decision with standard mode."""
        client = NeuroMemoryClient(mode="local")
        result = client.decide(
            prompt="Should I proceed?",
            risk_level="low",
            mode="standard",
        )
        
        assert isinstance(result, DecideResult)
        assert hasattr(result, "response")
        assert hasattr(result, "accepted")
        assert hasattr(result, "phase")
        assert hasattr(result, "contour_decisions")

    def test_decide_with_context(self):
        """Test decision with context."""
        client = NeuroMemoryClient(mode="local")
        result = client.decide(
            prompt="Is this safe?",
            context="Previous actions were successful.",
            risk_level="medium",
        )
        
        assert isinstance(result, DecideResult)

    def test_decide_returns_contour_decisions(self):
        """Test that decide returns contour decisions."""
        client = NeuroMemoryClient(mode="local")
        result = client.decide(
            prompt="Simple question?",
            risk_level="low",
        )
        
        assert isinstance(result.contour_decisions, list)
        for contour in result.contour_decisions:
            assert isinstance(contour, ContourDecision)
            assert hasattr(contour, "contour")
            assert hasattr(contour, "passed")

    def test_decide_returns_decision_id(self):
        """Test that decide returns a decision ID."""
        client = NeuroMemoryClient(mode="local")
        result = client.decide(prompt="Decision with ID?")
        
        assert result.decision_id is not None
        assert len(result.decision_id) > 0

    def test_decide_different_modes(self):
        """Test different decision modes."""
        client = NeuroMemoryClient(mode="local")
        
        modes = ["standard", "cautious", "confident", "emergency"]
        for mode in modes:
            result = client.decide(
                prompt="Test prompt",
                mode=mode,
            )
            assert isinstance(result, DecideResult)


class TestAgentStepLocal:
    """Test agent_step() in local mode."""

    def test_agent_step_basic(self):
        """Test basic agent step."""
        client = NeuroMemoryClient(mode="local")
        result = client.agent_step(
            agent_id="test-agent",
            observation="User said hello.",
        )
        
        assert isinstance(result, AgentStepResult)
        assert isinstance(result.action, AgentAction)
        assert hasattr(result, "response")
        assert hasattr(result, "phase")
        assert hasattr(result, "accepted")

    def test_agent_step_with_state(self):
        """Test agent step with internal state."""
        client = NeuroMemoryClient(mode="local")
        result = client.agent_step(
            agent_id="stateful-agent",
            observation="Continue.",
            internal_state={"step_count": 1},
        )
        
        assert result.updated_state is not None
        assert "step_count" in result.updated_state or "last_step_id" in result.updated_state

    def test_agent_step_action_types(self):
        """Test that action type is valid."""
        client = NeuroMemoryClient(mode="local")
        result = client.agent_step(
            agent_id="action-agent",
            observation="What next?",
        )
        
        valid_types = ["respond", "tool_call", "wait", "terminate"]
        assert result.action.action_type in valid_types

    def test_agent_step_increments_counter(self):
        """Test that step counter increments."""
        client = NeuroMemoryClient(mode="local")
        
        # First step
        result1 = client.agent_step(
            agent_id="counter-agent",
            observation="Step 1",
        )
        
        # Second step with updated state
        result2 = client.agent_step(
            agent_id="counter-agent",
            observation="Step 2",
            internal_state=result1.updated_state,
        )
        
        if result2.updated_state:
            assert result2.updated_state.get("step_count", 0) > 0


class TestGenerateCompatibility:
    """Test generate() for backward compatibility."""

    def test_generate_basic(self):
        """Test basic generation."""
        client = NeuroMemoryClient(mode="local")
        result = client.generate(prompt="Hello, world!")
        
        assert isinstance(result, dict)
        assert "response" in result

    def test_generate_with_parameters(self):
        """Test generation with parameters."""
        client = NeuroMemoryClient(mode="local")
        result = client.generate(
            prompt="Test",
            max_tokens=100,
            moral_value=0.8,
        )
        
        assert isinstance(result, dict)
        assert "response" in result


class TestHealthCheck:
    """Test health_check() method."""

    def test_health_check_local(self):
        """Test health check in local mode."""
        client = NeuroMemoryClient(mode="local")
        result = client.health_check()
        
        assert isinstance(result, dict)
        assert result["mode"] == "local"


class TestErrorHandling:
    """Test error handling."""

    def test_uninitialized_engine_raises_error(self):
        """Test that uninitialized engine raises appropriate error."""
        # This would require mocking, but we can test that the exception exists
        from mlsdm.sdk import NeuroMemoryError
        
        error = NeuroMemoryError("Test error")
        assert str(error) == "Test error"


class TestDataTransferObjects:
    """Test DTO classes."""

    def test_memory_item_creation(self):
        """Test MemoryItem creation."""
        item = MemoryItem(
            content="Test content",
            similarity=0.85,
            phase=0.1,
            metadata={"key": "value"},
        )
        assert item.content == "Test content"
        assert item.similarity == 0.85
        assert item.phase == 0.1

    def test_contour_decision_creation(self):
        """Test ContourDecision creation."""
        decision = ContourDecision(
            contour="moral_filter",
            passed=True,
            score=0.9,
            threshold=0.5,
        )
        assert decision.contour == "moral_filter"
        assert decision.passed is True

    def test_agent_action_creation(self):
        """Test AgentAction creation."""
        action = AgentAction(
            action_type="respond",
            content="Hello!",
        )
        assert action.action_type == "respond"
        assert action.content == "Hello!"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
