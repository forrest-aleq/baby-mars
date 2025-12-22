"""Test Apollo-enriched birth with Knowledge vs Beliefs distinction"""
import asyncio
from src.birth import birth_from_apollo, knowledge_to_context_string
from src.graphs.belief_graph import get_belief_graph
from src.graphs.belief_graph_manager import get_belief_graph_manager
from src.cognitive_loop.nodes.cognitive_activation import process as cognitive_activation
from src.cognitive_loop.nodes.appraisal import process as appraisal_process


async def test_apollo_birth():
    print("=" * 60)
    print("BABY MARS: Apollo Birth Test")
    print("=" * 60)

    email = "forrest@aleq.com"
    message = "Help me track our SaaS revenue metrics and deferred revenue"

    print(f"\nEmail: {email}")
    print(f"Message: {message}\n")

    # Birth from Apollo
    state = await birth_from_apollo(email, message, persist=False)

    print("=" * 60)
    print("THE 6 THINGS")
    print("=" * 60)

    # 1. Person
    print(f"\n1. PERSON:")
    print(f"   Name: {state['person']['name']}")
    print(f"   Role: {state['person']['role']}")
    print(f"   Authority: {state['person']['authority']}")

    # 2. Capabilities (binary)
    print(f"\n2. CAPABILITIES (binary flags):")
    for cap, enabled in list(state['capabilities'].items())[:5]:
        print(f"   {'✓' if enabled else '✗'} {cap}")

    # 3. Relationships
    print(f"\n3. RELATIONSHIPS (org structure):")
    print(f"   Reports to: {state['relationships'].get('reports_to', 'N/A')}")
    print(f"   Authority: {state['relationships'].get('authority', 0)}")
    print(f"   Org: {state['org_id']}")

    # 4. KNOWLEDGE (facts, NO strength)
    print(f"\n4. KNOWLEDGE (facts, NO strength): {len(state.get('knowledge', []))} facts")
    for k in state.get('knowledge', [])[:5]:
        print(f"   [{k.get('scope', 'global'):8}] {k['statement'][:60]}...")

    # 5. BELIEFS (claims, WITH strength)
    print(f"\n5. BELIEFS (claims, WITH strength): {len(state['activated_beliefs'])} beliefs")
    by_category = {}
    for b in state['activated_beliefs']:
        cat = b.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(b)

    for cat, beliefs in sorted(by_category.items()):
        print(f"\n   {cat.upper()} ({len(beliefs)}):")
        for b in beliefs[:3]:
            strength = b.get('strength', 0)
            immutable = " [IMMUTABLE]" if b.get('immutable') else ""
            print(f"   - {b['belief_id'][:30]:30} @ {strength:.2f}{immutable}")
            print(f"     \"{b['statement'][:50]}...\"")

    # 6. Goals
    print(f"\n6. GOALS ({len(state['active_goals'])}):")
    for g in state['active_goals'][:3]:
        print(f"   [{g.get('type', 'standing'):8}] {g['description']} (priority: {g['priority']})")

    # 7. Style
    print(f"\n7. STYLE:")
    for k, v in state['style'].items():
        print(f"   {k}: {v}")

    # Show temporal
    print(f"\n8. TEMPORAL (computed at mount):")
    temporal = state.get('temporal', {})
    print(f"   Time: {temporal.get('day_of_week', 'N/A')}, {temporal.get('time_of_day', 'N/A')}")
    print(f"   Phase: {temporal.get('month_phase', 'N/A')}")
    print(f"   Month-end: {temporal.get('is_month_end', False)}")

    # ============================================================
    # KEY DISTINCTION: Knowledge vs Beliefs
    # ============================================================

    print("\n" + "=" * 60)
    print("KEY DISTINCTION: Knowledge vs Beliefs")
    print("=" * 60)

    print("\nKNOWLEDGE (facts, no strength, replace to change):")
    print("-" * 50)
    knowledge_facts = state.get('knowledge', [])
    for k in knowledge_facts[:3]:
        print(f"  FACT: \"{k['statement']}\"")
        print(f"        scope={k.get('scope')}, source={k.get('source')}")
        print(f"        → No strength, no learning loop\n")

    print("\nBELIEFS (claims, with strength, learning loop updates):")
    print("-" * 50)
    for b in state['activated_beliefs'][:3]:
        if not b.get('immutable'):
            print(f"  CLAIM: \"{b['statement']}\"")
            print(f"         strength={b.get('strength', 0):.2f}, category={b.get('category')}")
            print(f"         → Learning loop will adjust based on outcomes\n")

    # ============================================================
    # COGNITIVE LOOP TEST
    # ============================================================

    print("\n" + "=" * 60)
    print("COGNITIVE LOOP")
    print("=" * 60)

    # Populate manager cache for cognitive loop
    graph = get_belief_graph()
    manager = get_belief_graph_manager()
    manager._cache[state["org_id"]] = graph

    # Run cognitive activation
    print("\n1. Cognitive Activation:")
    activation_result = await cognitive_activation(state)
    activated = activation_result.get('activated_beliefs', [])
    print(f"   Activated {len(activated)} beliefs for this context")

    state.update(activation_result)

    # Run appraisal
    print("\n2. Appraisal:")
    appraisal_result = await appraisal_process(state)

    supervision = appraisal_result.get('supervision_mode')
    strength = appraisal_result.get('belief_strength_for_action')
    appraisal = appraisal_result.get('appraisal', {})

    print(f"   Supervision mode: {supervision}")
    print(f"   Belief strength: {strength}")
    print(f"   Difficulty: {appraisal.get('difficulty')}")
    print(f"   Ethical concerns: {appraisal.get('involves_ethical_beliefs')}")

    # Show attributed beliefs
    attr_ids = appraisal.get('attributed_beliefs', [])
    if attr_ids:
        print(f"\n   Attributed beliefs ({len(attr_ids)}):")
        belief_map = {b["belief_id"]: b for b in activated}
        for bid in attr_ids[:5]:
            if bid in belief_map:
                b = belief_map[bid]
                print(f"   - {bid}: {b.get('category')} @ {b.get('strength', 0):.2f}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\n  Person: {state['person']['name']} ({state['person']['role']})")
    print(f"  Org: {state['org_id']}")
    print(f"  Knowledge facts: {len(state.get('knowledge', []))}")
    print(f"  Beliefs: {len(state['activated_beliefs'])}")
    print(f"  Supervision: {supervision} @ strength {strength}")
    print(f"\n  Birth mode: {state.get('birth_mode', 'N/A')}")
    print(f"  Salience: {state.get('birth_salience', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(test_apollo_birth())
