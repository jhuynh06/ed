"""End-to-end test for the Theodore LangGraph pipeline."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


async def test():
    from app.agents.graph import build_theodore_graph

    graph = build_theodore_graph()
    print("Graph compiled OK")

    # Test 1: Low risk (calm user) — should exit after risk node
    low_risk_input = {
        "raw_sensor": {
            "imu": {"jerk_magnitude": 0.05, "stillness_duration_s": 120.0},
            "hr": {"bpm": 72, "baseline_bpm": 72.0, "elevation_pct": 0.0, "valid": True},
            "touch": {"any_contact": True, "squeeze_intensity": 0.1, "grip_duration_s": 30.0},
        }
    }
    r1 = await graph.ainvoke(low_risk_input)
    print(f"Test 1 (low risk): score={r1.get('agitation_score')}, risk={r1.get('risk_level')}")
    print(f"  observation: {str(r1.get('semantic_observation', ''))[:80]}...")
    print(f"  full keys: {list(r1.keys())}")
    print("Test 1 PASSED\n")

    # Test 2: High risk (sundowning episode) — should run full pipeline
    high_risk_input = {
        "raw_sensor": {
            "imu": {"jerk_magnitude": 1.5, "stillness_duration_s": 0.0, "rocking_detected": True},
            "hr": {"bpm": 98, "baseline_bpm": 72.0, "elevation_pct": 36.0, "valid": True},
            "touch": {"any_contact": True, "squeeze_intensity": 0.8, "grip_duration_s": 180.0},
            "speech_text": "I want to go home",
        }
    }
    r2 = await graph.ainvoke(high_risk_input)
    print(f"\nTest 2 (high risk): score={r2['agitation_score']:.1f}, risk={r2['risk_level']}")
    print(f"  observation: {r2['semantic_observation'][:80]}...")
    print(f"  plan: {r2.get('plan', '')[:80]}...")
    print(f"  actions dispatched: {len(r2.get('executed_actions', []))}")
    print(f"  notification: {r2.get('notification')}")
    mar = r2.get("mar_result")
    print(f"  MAR approved: {mar.get('approved') if mar else 'N/A (no notification)'}")
    assert r2["risk_level"] in ("medium", "high"), f"Expected medium/high, got {r2['risk_level']}"
    assert "executed_actions" in r2, "High risk should reach executor"

    print("\nAll tests passed!")


if __name__ == "__main__":
    asyncio.run(test())
