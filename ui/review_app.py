"""
Streamlit UI for reviewing generated MCQ images.
"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="MCQ Image Review",
    page_icon="🖼️",
    layout="wide"
)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
GENERATED_DIR = OUTPUT_DIR / "generated"
REVIEW_DIR = OUTPUT_DIR / "review"


def load_jsonl(filepath):
    """Load JSONL file."""
    items = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items


def save_reviewed(items, filepath):
    """Save reviewed items."""
    with open(filepath, 'w') as f:
        for item in items:
            f.write(json.dumps(item) + '\n')


def main():
    st.title("🖼️ MCQ Image Review Interface")
    st.markdown("Review and approve generated SVG images for MCQs")
    
    # Sidebar
    st.sidebar.header("Navigation")
    
    # Select phase to review
    phase = st.sidebar.radio(
        "Select Phase",
        ["Pilot Results", "Phase 1: Chemistry", "Phase 2: Reference", "Phase 3: Pure AI"],
        index=0
    )
    
    # Load results based on selection
    if phase == "Pilot Results":
        results_file = OUTPUT_DIR / "pilot" / "pilot_results.jsonl"
    else:
        phase_num = int(phase.split(":")[0].replace("Phase ", ""))
        source_type = ['chemistry', 'reference', 'pure'][phase_num - 1]
        results_file = GENERATED_DIR / source_type / f"batch_results.jsonl"
    
    # Load results
    if results_file.exists():
        results = load_jsonl(results_file)
        st.sidebar.success(f"Loaded {len(results)} items")
    else:
        results = []
        st.sidebar.warning("No results file found. Run generation first.")
    
    if not results:
        st.info("No results to review. Run the pilot or batch generation first.")
        st.code("python src/main.py  # Run pilot")
        return
    
    # Filter options
    st.sidebar.header("Filters")
    show_only = st.sidebar.radio(
        "Show",
        ["All", "Successful only", "Failed only"],
        index=0
    )
    
    if show_only == "Successful only":
        filtered_results = [r for r in results if r.get('svg')]
    elif show_only == "Failed only":
        filtered_results = [r for r in results if not r.get('svg')]
    else:
        filtered_results = results
    
    # Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", len(results))
    with col2:
        st.metric("Successful", len([r for r in results if r.get('svg')]))
    with col3:
        st.metric("Failed", len([r for r in results if not r.get('svg')]))
    with col4:
        success_rate = len([r for r in results if r.get('svg')]) / len(results) * 100 if results else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    st.divider()
    
    # Review items
    approved = []
    rejected = []
    
    for idx, result in enumerate(filtered_results):
        with st.container():
            # Header
            col_header, col_status = st.columns([3, 1])
            with col_header:
                st.subheader(f"MCQ: {result.get('mcq_id', 'Unknown')}")
                st.caption(f"Phase {result.get('phase', '?')} | {result.get('source_type', 'Unknown')}")
            
            with col_status:
                if result.get('svg'):
                    st.success("✓ Generated")
                else:
                    st.error("✗ Failed")
            
            # Question details
            st.markdown(f"**Subject:** {result.get('subject', 'N/A')}")
            st.markdown(f"**Chapter:** {result.get('chapter', 'N/A')}")
            st.markdown(f"**Question:** {result.get('question_text', 'N/A')}")
            
            if result.get('smiles'):
                st.markdown(f"**SMILES:** `{result.get('smiles')}`")
            
            if result.get('reference_image'):
                st.markdown(f"**Reference:** {result.get('reference_image')}")
                st.markdown(f"**Similarity:** {result.get('similarity_score', 0):.2f}")
            
            # Show SVG if generated
            if result.get('svg'):
                st.markdown("**Generated Image:**")
                
                # Render SVG
                svg_html = result['svg']
                
                # Add styling for dark mode compatibility
                styled_svg = svg_html.replace(
                    '<svg',
                    '<svg style="background: white; border-radius: 8px; padding: 10px; max-width: 100%; height: auto;"'
                )
                
                st.components.v1.html(styled_svg, height=300)
                
                # SVG code expander
                with st.expander("View SVG Code"):
                    st.code(result['svg'], language='xml')
                
                # Approval buttons
                col_approve, col_reject = st.columns(2)
                with col_approve:
                    if st.button("✓ Approve", key=f"approve_{idx}"):
                        approved.append(result)
                        st.success("Approved!")
                
                with col_reject:
                    if st.button("✗ Reject", key=f"reject_{idx}"):
                        rejected.append(result)
                        st.warning("Rejected!")
            
            else:
                st.error(f"**Error:** {result.get('error', 'Unknown error')}")
                st.markdown(f"**Attempts:** {result.get('attempts', 0)}")
            
            st.divider()
    
    # Summary at bottom
    st.sidebar.header("Actions")
    
    if st.sidebar.button("Export Approved"):
        if approved:
            export_file = REVIEW_DIR / f"approved_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            save_reviewed(approved, export_file)
            st.sidebar.success(f"Exported {len(approved)} approved items")
        else:
            st.sidebar.warning("No items approved yet")
    
    if st.sidebar.button("Export Failed for Retry"):
        failed = [r for r in results if not r.get('svg')]
        if failed:
            retry_file = REVIEW_DIR / f"retry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            save_reviewed(failed, retry_file)
            st.sidebar.success(f"Exported {len(failed)} failed items for retry")
        else:
            st.sidebar.success("No failed items!")


if __name__ == "__main__":
    main()
