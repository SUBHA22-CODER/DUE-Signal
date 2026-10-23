import asyncio
import sys
from mcp_server.db import seed_scenario, count_deadlines

async def main():
    scenario = sys.argv[1] if len(sys.argv) > 1 else "finals_crisis"
    print(f"[DueSignal] Seeding demo curriculum: {scenario} ...")
    res = await seed_scenario(scenario)
    counts = await count_deadlines()
    print(f"[DueSignal] Successfully seeded {res['count']} assignments. Total: {counts['total']} (Pending: {counts['pending']})")

if __name__ == "__main__":
    asyncio.run(main())
