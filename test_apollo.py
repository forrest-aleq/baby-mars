"""Test Apollo API enrichment"""
import asyncio
import json
from src.birth.enrichment import enrich_from_apollo, map_industry_to_knowledge_pack, infer_authority_from_role, determine_org_size


async def test_apollo():
    print("=== Testing Apollo Enrichment ===\n")

    email = "forrest@aleq.com"
    print(f"Looking up: {email}\n")

    result = await enrich_from_apollo(email)

    if not result:
        print("No data returned from Apollo")
        return

    print("=== Person ===")
    print(f"  Name: {result.person.name}")
    print(f"  Title: {result.person.title}")
    print(f"  Seniority: {result.person.seniority}")
    print(f"  Department: {result.person.department}")
    print(f"  Location: {result.person.city}, {result.person.state}")
    print(f"  Timezone: {result.person.timezone}")

    print("\n=== Company ===")
    print(f"  Name: {result.company.name}")
    print(f"  Industry: {result.company.industry}")
    print(f"  Sub-industry: {result.company.sub_industry}")
    print(f"  Employees: {result.company.employee_count} ({result.company.employee_range})")
    print(f"  Revenue: {result.company.revenue_range}")
    print(f"  Location: {result.company.city}, {result.company.state}")
    print(f"  Description: {result.company.description[:100]}..." if result.company.description else "  Description: N/A")
    print(f"  Technologies: {result.company.technologies[:5]}")
    print(f"  Keywords: {result.company.keywords[:5]}")

    print("\n=== Rapport Hooks ===")
    for k, v in result.rapport_hooks.items():
        print(f"  {k}: {v}")

    print("\n=== Inferred Values ===")
    authority = infer_authority_from_role(result.person.title, result.person.seniority)
    org_size = determine_org_size(result.company.employee_count)
    knowledge_packs = map_industry_to_knowledge_pack(result.company.industry)

    print(f"  Authority: {authority:.2f}")
    print(f"  Org Size: {org_size}")
    print(f"  Knowledge Packs: {knowledge_packs}")

    print("\n=== Raw Response (partial) ===")
    if result.raw_response.get("person"):
        # Just show the keys
        print(f"  Person keys: {list(result.raw_response['person'].keys())[:15]}")
        if result.raw_response['person'].get('organization'):
            print(f"  Org keys: {list(result.raw_response['person']['organization'].keys())[:15]}")


if __name__ == "__main__":
    asyncio.run(test_apollo())
