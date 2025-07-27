"""
Quick test for Gap Analyzer - single paper type for fast validation
"""

import asyncio
import time
from datetime import datetime
from app.services.gap_analyzer.orchestrator import GapAnalysisOrchestrator

# Single test paper for quick validation - BIOINFORMATICS DOMAIN
TEST_PAPER = {
    "title": "Bioinformatics Test",
    "text": """
    Title: Multi-Omics Data Integration for Precision Cancer Medicine: Computational Challenges and Opportunities

    Abstract: Precision cancer medicine requires the integration of multi-omics data including genomics, transcriptomics, proteomics, and metabolomics to understand tumor heterogeneity and identify personalized therapeutic targets. This study presents a comprehensive analysis of current computational approaches for multi-omics integration and their clinical applications.

    Methods:
    We developed and evaluated several integration frameworks:
    - Deep learning-based autoencoders for dimensionality reduction
    - Graph neural networks for pathway analysis
    - Bayesian methods for uncertainty quantification
    - Ensemble methods combining multiple data modalities

    Key Findings:
    1. Graph-based integration methods achieve 87.3% accuracy in predicting drug response
    2. Multi-omics signatures outperform single-omics approaches by 15-20% in prognosis prediction
    3. Pathway-informed models show better interpretability than black-box approaches

    Limitations:
    Despite significant advances, several critical challenges remain:
    1. Batch effects and technical variation across different omics platforms create integration difficulties
    2. Missing data patterns are inconsistent across modalities, limiting comprehensive analysis
    3. Computational scalability issues when processing large patient cohorts (>10,000 samples)
    4. Limited availability of high-quality paired multi-omics datasets for model training
    5. Lack of standardized preprocessing pipelines across different research institutions

    Future Work:
    Critical research directions for advancing precision medicine through multi-omics:
    1. Development of robust batch correction methods for cross-platform omics integration
    2. Novel imputation algorithms for handling missing data in multi-omics contexts
    3. Federated learning approaches for collaborative analysis while preserving patient privacy
    4. Interpretable AI methods for clinical decision support
    5. Real-time omics analysis for point-of-care applications

    Conclusion:
    While multi-omics integration shows tremendous promise for precision cancer medicine, significant computational and methodological challenges must be addressed to realize its full clinical potential. The development of scalable, interpretable, and clinically validated approaches remains a priority.
    """
}

async def quick_test():
    """Run a quick gap analyzer test with comprehensive output display"""
    print("🚀 QUICK GAP ANALYZER TEST - COMPREHENSIVE OUTPUT")
    print("=" * 70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    try:
        # Initialize orchestrator
        orchestrator = GapAnalysisOrchestrator()
        
        # Run gap analysis with MINIMAL scope but allow validation
        result = await orchestrator.analyze_research_gaps_from_text(
            paper_text=TEST_PAPER["text"],
            paper_id="quick_test",
            max_papers=3,  # Need at least 2-3 papers to validate gaps
            validation_threshold=1
        )
        
        processing_time = time.time() - start_time
        
        # Print core results
        print(f"\n📊 CORE RESULTS:")
        print(f"   ✅ Analysis Success: {len(result.validated_gaps) > 0}")
        print(f"   ⏱️  Execution Time: {processing_time:.2f} seconds")
        print(f"   📄 Papers Analyzed: {result.process_metadata.total_papers_analyzed}")
        print(f"   🔍 Gaps Discovered: {result.process_metadata.gaps_discovered}")
        print(f"   ✅ Gaps Validated: {len(result.validated_gaps)}")
        print(f"   ❌ Gaps Eliminated: {result.process_metadata.gaps_eliminated}")
        print(f"   🔎 Search Queries: {result.process_metadata.search_queries_executed}")
        
        # Print frontier statistics
        print(f"\n🚀 FRONTIER STATISTICS:")
        fs = result.process_metadata.frontier_stats
        print(f"   🌐 Research Domains: {fs.research_domains_explored}")
        print(f"   🔗 Cross-Domain Connections: {fs.cross_domain_connections}")
        print(f"   ⚡ Research Velocity: {fs.research_velocity:.1f} papers/min")
        print(f"   📈 Breakthrough Potential: {fs.breakthrough_potential_score}/10")
        print(f"   🎯 Elimination Rate: {fs.elimination_effectiveness:.1f}%")
        
        # Print research landscape
        print(f"\n🗺️  RESEARCH LANDSCAPE:")
        rl = result.process_metadata.research_landscape
        print(f"   🏆 Dominant Areas: {', '.join(rl.dominant_research_areas)}")
        print(f"   📊 Research Clusters: {dict(list(rl.research_clusters.items())[:3])}")
        print(f"   🔥 Emerging Trends: {', '.join(rl.emerging_trends[:3])}")
        
        # Print validated gaps with details
        if result.validated_gaps:
            print(f"\n🎯 VALIDATED RESEARCH GAPS:")
            for i, gap in enumerate(result.validated_gaps, 1):
                print(f"\n   {i}. {gap.gap_title}")
                print(f"      📂 Category: {gap.category}")
                print(f"      📝 Description: {gap.description[:120]}...")
                print(f"      💼 Commercial Viability: {gap.gap_metrics.commercial_viability}/10")
                print(f"      🔬 Innovation Potential: {gap.gap_metrics.innovation_potential}/10")
                print(f"      ⏰ Time to Solution: {gap.gap_metrics.time_to_solution}")
                print(f"      🎨 Opportunity Tags: {', '.join(gap.opportunity_tags[:3])}")
        
        # Print executive summary
        print(f"\n📋 EXECUTIVE SUMMARY:")
        es = result.executive_summary
        print(f"   📖 Overview: {es.frontier_overview}")
        print(f"   💡 Key Insights: {len(es.key_insights)} insights identified")
        print(f"   🎯 Priorities: {', '.join(es.research_priorities[:2])}")
        print(f"   💰 Investment Opportunities: {len(es.investment_opportunities)} identified")
        
        # Print research intelligence
        print(f"\n🧠 RESEARCH INTELLIGENCE:")
        ri = result.research_intelligence
        print(f"   🗑️  Eliminated Gaps: {len(ri.eliminated_gaps)} gaps eliminated")
        print(f"   📈 Research Momentum: {dict(list(ri.research_momentum.items())[:3])}")
        print(f"   🤝 Collaboration Areas: {len(ri.emerging_collaborations)} identified")
        
        # Print quality metrics
        print(f"\n✅ QUALITY METRICS:")
        qm = result.quality_metrics
        print(f"   📊 Analysis Completeness: {qm['analysis_completeness']:.1f}%")
        print(f"   🔬 Validation Rigor: {qm['validation_rigor']:.1f}%")
        print(f"   🧠 AI Confidence: {qm['ai_confidence']:.1f}%")
        print(f"   🗺️  Frontier Coverage: {qm['frontier_coverage']:.1f}%")
        
        # Assessment
        print(f"\n🏆 ASSESSMENT:")
        if result.process_metadata.gaps_eliminated > 0:
            print(f"   🎉 Gap elimination working! ({result.process_metadata.gaps_eliminated} eliminated)")
        else:
            print(f"   ⚠️  No gaps eliminated (check validation logic)")
            
        if len(result.validated_gaps) > 0:
            print(f"   ✅ Gap discovery successful ({len(result.validated_gaps)} validated)")
        else:
            print(f"   ⚠️  No gaps validated (check threshold settings)")
            
        if processing_time < 120:  # 2 minutes
            print(f"   🚀 Performance excellent: {processing_time:.1f}s (under 2 min)")
        else:
            print(f"   ⏰ Performance: {processing_time:.1f}s (consider optimization)")
        
        # Save sample output
        import json
        output_dict = result.model_dump()
        with open("quick_test_output.json", "w") as f:
            json.dump(output_dict, f, indent=2, default=str)
        print(f"\n💾 Full output saved to: quick_test_output.json")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())