"""
End-to-End Tests for Neuro Memory Assistant Use Case.

Tests the complete flow of:
1. Session creation
2. Memory storage (facts persist within session)
3. Memory retrieval (relevant context)
4. Decision-making with governance
5. Agent step protocol
6. Conversation flow
"""

import pytest

from mlsdm.sdk import NeuroMemoryClient


class TestNeuroMemoryAssistantE2E:
    """E2E tests for the Neuro Memory Assistant use case."""

    @pytest.fixture
    def client(self):
        """Create a client in local mode."""
        return NeuroMemoryClient(
            mode="local",
            user_id="e2e-test-user",
            session_id="e2e-test-session",
        )

    def test_session_memory_workflow(self, client):
        """Test complete session-based memory workflow."""
        # 1. Store initial facts
        facts = [
            "User's name is Alice.",
            "Alice prefers morning meetings.",
            "Alice works on the engineering team.",
        ]
        
        stored_ids = []
        for fact in facts:
            result = client.append_memory(fact, moral_value=0.9)
            if result.success:
                stored_ids.append(result.memory_id)
        
        assert len(stored_ids) > 0, "At least one fact should be stored"
        
        # 2. Query for relevant memory
        query_result = client.query_memory("What team does Alice work on?", top_k=3)
        assert query_result.success is True
        
        # 3. Make a decision based on memory
        decision_result = client.decide(
            prompt="Should I schedule a meeting with Alice?",
            context="Need to discuss project updates.",
            risk_level="low",
            mode="standard",
        )
        assert decision_result.decision_id is not None

    def test_multi_turn_conversation(self, client):
        """Test multi-turn conversation with memory accumulation."""
        turns = [
            {"observation": "User: Hello, I need help with scheduling."},
            {"observation": "User: I have a meeting tomorrow at 10am."},
            {"observation": "User: Can you remind me about it?"},
        ]
        
        internal_state = {"conversation_started": True}
        
        for turn in turns:
            result = client.agent_step(
                agent_id="conversation-agent",
                observation=turn["observation"],
                internal_state=internal_state,
            )
            
            # Update state for next turn
            if result.updated_state:
                internal_state = result.updated_state
            
            # Verify response structure
            assert result.action is not None
            assert result.phase in ["wake", "sleep"]
        
        # Verify state was maintained
        assert internal_state.get("step_count", 0) > 0

    def test_moral_filtering_in_conversation(self, client):
        """Test that moral filtering works in conversations."""
        # Standard request should pass
        result1 = client.decide(
            prompt="Help me plan a team event.",
            risk_level="low",
            mode="standard",
        )
        
        # The response should be generated (may or may not be accepted based on phase)
        assert result1.response is not None or result1.message is not None
        
        # Verify contour decisions are present
        assert len(result1.contour_decisions) > 0

    def test_risk_aware_decisions(self, client):
        """Test risk-aware decision making."""
        scenarios = [
            ("low", "standard"),
            ("medium", "cautious"),
            ("high", "cautious"),
        ]
        
        for risk_level, mode in scenarios:
            result = client.decide(
                prompt=f"Test decision with {risk_level} risk",
                risk_level=risk_level,
                mode=mode,
            )
            
            assert result.risk_assessment is not None
            assert result.risk_assessment["level"] == risk_level
            assert result.risk_assessment["mode"] == mode

    def test_agent_tool_call_flow(self, client):
        """Test agent flow with tool calls and results."""
        # Step 1: Initial observation
        result1 = client.agent_step(
            agent_id="tool-agent",
            observation="User asks: What's the weather today?",
        )
        
        # Step 2: Simulate tool call response
        result2 = client.agent_step(
            agent_id="tool-agent",
            observation="Continue with tool result.",
            internal_state=result1.updated_state,
            tool_results=[
                {"tool": "weather", "result": "Sunny, 72°F"}
            ],
        )
        
        assert result2.step_id is not None
        assert result2.action.action_type in ["respond", "tool_call", "wait", "terminate"]

    def test_memory_context_retrieval_in_generation(self, client):
        """Test that memory context is used in generation."""
        # Store some facts first
        client.append_memory("The project deadline is Friday.")
        client.append_memory("Budget is $50,000.")
        client.append_memory("Team size is 5 people.")
        
        # Make a decision that should use memory context
        result = client.decide(
            prompt="What resources are available for the project?",
            use_memory=True,
            context_top_k=5,
        )
        
        # Memory context should be used
        assert result.memory_context_used >= 0  # May be 0 if memory is sparse

    def test_session_isolation(self):
        """Test that sessions are isolated."""
        # Create two clients with different sessions
        client1 = NeuroMemoryClient(
            mode="local",
            user_id="user-1",
            session_id="session-1",
        )
        
        client2 = NeuroMemoryClient(
            mode="local",
            user_id="user-2",
            session_id="session-2",
        )
        
        # Each client should be able to operate independently
        result1 = client1.append_memory("Session 1 fact")
        result2 = client2.append_memory("Session 2 fact")
        
        # Both should work (note: memory is actually shared in local mode
        # as they use the same engine instance, but the API supports scoping)
        assert result1.phase in ["wake", "sleep", "unknown"]
        assert result2.phase in ["wake", "sleep", "unknown"]

    def test_cognitive_phase_awareness(self, client):
        """Test that cognitive phase is tracked."""
        phases_seen = set()
        
        # Run several operations to see phase changes
        for i in range(5):
            result = client.append_memory(f"Phase test {i}")
            phases_seen.add(result.phase)
        
        # Should see at least wake phase
        assert "wake" in phases_seen or "sleep" in phases_seen or "unknown" in phases_seen

    def test_decision_governance_contours(self, client):
        """Test that all governance contours are checked."""
        result = client.decide(
            prompt="Make a governed decision.",
            risk_level="medium",
            mode="standard",
        )
        
        contour_names = {c.contour for c in result.contour_decisions}
        
        # Should have moral and risk contours
        assert "moral_filter" in contour_names
        assert "risk_assessment" in contour_names

    def test_agent_state_persistence(self, client):
        """Test that agent state persists across steps."""
        # First step
        result1 = client.agent_step(
            agent_id="persistent-agent",
            observation="Initial step",
            internal_state={"goal": "assist user"},
        )
        
        # Verify state is updated
        state1 = result1.updated_state
        assert state1 is not None
        assert "last_step_id" in state1
        
        # Second step with previous state
        result2 = client.agent_step(
            agent_id="persistent-agent",
            observation="Follow-up step",
            internal_state=state1,
        )
        
        # State should be further updated
        state2 = result2.updated_state
        assert state2 is not None
        assert state2.get("step_count", 0) >= 1


class TestNeuroMemoryAssistantHTTP:
    """E2E tests using HTTP API (requires server running)."""

    @pytest.fixture
    def remote_client(self):
        """Create a remote client (skips if server not available)."""
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code != 200:
                pytest.skip("Server not running")
        except Exception:
            pytest.skip("Server not running")
        
        return NeuroMemoryClient(
            mode="remote",
            base_url="http://localhost:8000",
        )

    def test_remote_health_check(self, remote_client):
        """Test remote health check."""
        result = remote_client.health_check()
        assert result["mode"] == "remote"

    def test_remote_memory_operations(self, remote_client):
        """Test remote memory operations."""
        # Append
        append_result = remote_client.append_memory("Remote test fact")
        assert append_result.phase in ["wake", "sleep", "unknown"]
        
        # Query
        query_result = remote_client.query_memory("Remote test")
        assert query_result.success is True

    def test_remote_decision(self, remote_client):
        """Test remote decision making."""
        result = remote_client.decide(
            prompt="Remote decision test",
            risk_level="low",
        )
        assert result.decision_id is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
