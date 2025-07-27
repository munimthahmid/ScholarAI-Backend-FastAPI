"""
Debug script to test gap elimination with a simple scenario
"""

import asyncio
from app.services.gap_analyzer.orchestrator import GapAnalysisOrchestrator

# Test with a simple gap that should be easily eliminated
TEST_PAPER = {
    "title": "Simple Gap Test",
    "text": """
    Title: Deep Learning for Image Classification: A Comprehensive Study

    Abstract: This paper provides a comprehensive analysis of deep learning approaches for image classification tasks, focusing on convolutional neural networks and their variants.

    Key Findings:
    1. ResNet architectures achieve 96% accuracy on ImageNet dataset
    2. Transfer learning reduces training time by 80% for new domains
    3. Data augmentation improves generalization by 15%

    Methods:
    - Convolutional Neural Networks (CNNs)
    - ResNet, DenseNet, and EfficientNet architectures
    - Transfer learning with pretrained models

    Limitations:
    1. Image classification requires large labeled datasets
    2. Models struggle with out-of-distribution examples

    Future Work:
    1. Develop techniques for few-shot image classification
    2. Improve robustness to domain shift

    Conclusion:
    Deep learning has achieved remarkable success in image classification, but challenges remain in data efficiency and robustness.
    """
}

async def debug_gap_elimination():
    """Test gap elimination with controlled scenario"""
    print("🐛 DEBUG: Testing Gap Elimination Logic")
    print("=" * 60)
    
    try:
        # Initialize orchestrator
        orchestrator = GapAnalysisOrchestrator()
        
        # Run with very small scope for debugging
        print("🚀 Starting gap analysis...")
        result = await orchestrator.analyze_research_gaps_from_text(
            paper_text=TEST_PAPER["text"],
            paper_id="debug_test",
            max_papers=2,
            validation_threshold=1
        )
        
        print(f"\n📊 RESULTS:")
        print(f"   📄 Papers Analyzed: {result.process_metadata.total_papers_analyzed}")
        print(f"   🔍 Gaps Discovered: {result.process_metadata.gaps_discovered}")
        print(f"   ✅ Gaps Validated: {len(result.validated_gaps)}")
        print(f"   ❌ Gaps Eliminated: {result.process_metadata.gaps_eliminated}")
        print(f"   🔎 Search Queries: {result.process_metadata.search_queries_executed}")
        
        if result.process_metadata.gaps_eliminated > 0:
            print(f"\n🎉 SUCCESS: {result.process_metadata.gaps_eliminated} gaps were eliminated!")
        else:
            print(f"\n⚠️  ISSUE: No gaps were eliminated - debugging needed")
        
        print(f"\n🎯 FINAL VALIDATED GAPS:")
        for i, gap in enumerate(result.validated_gaps, 1):
            print(f"   {i}. {gap.gap_title}")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_gap_elimination())