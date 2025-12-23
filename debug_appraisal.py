"""
Quick debug script to test appraisal node
"""

import asyncio

from src.birth import quick_birth
from src.cognitive_loop.nodes.appraisal import process as appraisal_process
from src.cognitive_loop.nodes.cognitive_activation import process as cognitive_activation
from src.graphs.belief_graph import get_belief_graph, reset_belief_graph
from src.graphs.belief_graph_manager import get_belief_graph_manager, reset_belief_graph_manager


async def debug_appraisal():
    # Reset both the in-memory graph AND the manager cache
    reset_belief_graph()
    reset_belief_graph_manager()

    # Create test state
    state = quick_birth(
        name="Angela Park",
        role="Treasury Analyst",
        industry="real_estate",
        message="Collect weekly bank balances for our 68 accounts across 3 banks",
    )
    org_id = "storagecorner"
    state["org_id"] = org_id

    # CRITICAL: Populate the manager cache with the birthed beliefs
    manager = get_belief_graph_manager()
    birthed_graph = get_belief_graph()
    manager._cache[org_id] = birthed_graph

    print("=== Initial State ===")
    print(f"org_id: {state.get('org_id')}")
    print(f"messages: {len(state.get('messages', []))}")

    # Run cognitive activation
    print("\n=== Running Cognitive Activation ===")
    try:
        activation_result = await cognitive_activation(state)
        print(f"activated_beliefs: {len(activation_result.get('activated_beliefs', []))}")
        print(f"context_key: {activation_result.get('current_context_key')}")

        # Show first few beliefs
        for b in activation_result.get("activated_beliefs", [])[:3]:
            print(
                f"  - {b['belief_id']}: {b['statement'][:50]}... (strength={b.get('strength', 0)})"
            )

    except Exception as e:
        print(f"Cognitive activation error: {e}")
        import traceback

        traceback.print_exc()
        return

    # Merge activation into state
    state.update(activation_result)

    # Show all beliefs with categories
    print("\n=== All Beliefs by Category ===")
    beliefs = activation_result.get("activated_beliefs", [])
    by_category = {}
    for b in beliefs:
        cat = b.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(f"{b['belief_id']}: {b.get('strength', 0):.2f}")
    for cat, items in sorted(by_category.items()):
        print(f"  {cat}: {len(items)} beliefs")
        for item in items[:3]:
            print(f"    - {item}")

    # Run appraisal
    print("\n=== Running Appraisal ===")
    try:
        appraisal_result = await appraisal_process(state)
        print(f"supervision_mode: {appraisal_result.get('supervision_mode')}")
        print(f"belief_strength: {appraisal_result.get('belief_strength_for_action')}")
        print(f"appraisal keys: {list(appraisal_result.get('appraisal', {}).keys())}")

        # Show attributed beliefs with categories
        appraisal = appraisal_result.get("appraisal", {})
        attr_ids = appraisal.get("attributed_beliefs", [])
        belief_map = {b["belief_id"]: b for b in beliefs}
        print(f"\nAttributed beliefs ({len(attr_ids)}):")
        for bid in attr_ids:
            if bid in belief_map:
                b = belief_map[bid]
                print(
                    f"  - {bid}: category={b.get('category')}, strength={b.get('strength', 0):.2f}"
                )
            else:
                print(f"  - {bid}: NOT FOUND")

        print(f"\nrecommended_action_type: {appraisal.get('recommended_action_type')}")
        print(f"difficulty: {appraisal.get('difficulty')}")
        print(f"involves_ethical_beliefs: {appraisal.get('involves_ethical_beliefs')}")

    except Exception as e:
        print(f"Appraisal error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_appraisal())
