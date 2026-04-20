#!/usr/bin/env python3
"""
Run pilot mode for image generation.
Generates sample images for each phase and saves for review.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import run_pilot
from src.generators.chemistry_generator import ChemistryGenerator


async def main():
    print("\n" + "=" * 60)
    print("PILOT MODE - Image Generation Testing")
    print("=" * 60)
    print("\nThis will generate sample images for each phase:")
    print("  - Phase 1: 10 chemistry molecules (SMILES)")
    print("  - Phase 2: Will be tested with actual MCQs")
    print("  - Phase 3: Will be tested with actual MCQs")
    print()
    
    # Run pilot
    results = await run_pilot()
    
    # Summary
    successful = [r for r in results if r.svg]
    failed = [r for r in results if not r.svg]
    
    print("\n" + "=" * 60)
    print("PILOT RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total attempts:  {len(results)}")
    print(f"Successful:      {len(successful)}")
    print(f"Failed:          {len(failed)}")
    print(f"Success rate:    {len(successful)/len(results)*100:.1f}%")
    print()
    
    if successful:
        print("✓ Sample SVGs generated:")
        for r in successful[:3]:  # Show first 3
            print(f"  - {r.mcq_id}: {len(r.svg)} bytes")
    
    if failed:
        print("\n✗ Failed generations:")
        for r in failed:
            print(f"  - {r.mcq_id}: {r.error}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Review generated images:")
    print("   streamlit run ui/review_app.py")
    print()
    print("2. If satisfied, run full batches:")
    print("   python scripts/run_phase1.py")
    print("   python scripts/run_phase2.py")
    print("   python scripts/run_phase3.py")
    print()
    print("3. After review, integrate with Flexily database")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
