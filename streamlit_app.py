import streamlit as st
from pathlib import Path
import json
from collections import defaultdict

OUTPUT_DIR = Path("/root/image_generation_flexily/output/generated")

st.set_page_config(page_title="MCQ Image Generation", layout="wide")

st.title("MCQ Image Generation Pipeline")

# Sidebar with overall stats
with st.sidebar:
    st.header("Overall Progress")
    
    # Phase 3A stats
    phase3a_checkpoint = OUTPUT_DIR / "phase3a" / "checkpoint.jsonl"
    if phase3a_checkpoint.exists():
        with open(phase3a_checkpoint) as f:
            lines = [l for l in f.readlines() if l.strip()]
        st.metric("Phase 3A Processed", len(lines))
    
    # Total SVG count
    svg_count = len(list((OUTPUT_DIR / "phase3a").glob("mcq_*.svg")))
    st.metric("Total SVGs", svg_count)

tabs = st.tabs(["Phase 3A Live", "Phase 3A Test", "Phase 3C Test"])

def load_checkpoint_results(checkpoint_path):
    """Load results from checkpoint.jsonl file."""
    results = []
    if checkpoint_path.exists():
        with open(checkpoint_path) as f:
            for line in f:
                if line.strip():
                    try:
                        results.append(json.loads(line))
                    except:
                        pass
    return results

def show_responsive_svg(svg_content, max_width=600):
    """Display SVG with responsive styling."""
    st.markdown(f'''
    <div style="background:white;padding:10px;border:1px solid #ddd;max-width:{max_width}px;margin:0 auto">
        {svg_content}
    </div>
    ''', unsafe_allow_html=True)

def show_phase_batch(output_dir, phase_name):
    """Show results for a phase batch."""
    checkpoint_path = output_dir / "checkpoint.jsonl"
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    results = load_checkpoint_results(checkpoint_path)
    
    if results:
        success = sum(1 for r in results if r.get("success"))
        failed = len(results) - success
        avg_quality = sum(r.get("quality_score", 0) for r in results if r.get("success")) / max(success, 1)
        
        col1.metric("Total Processed", len(results))
        col2.metric("Success", success)
        col3.metric("Failed", failed)
        col4.metric("Avg Quality", f"{avg_quality:.1f}")
        
        # Progress bar
        total_expected = 340  # Phase 3A total
        progress = min(len(results) / total_expected, 1.0)
        st.progress(progress)
        st.caption(f"Progress: {len(results)}/{total_expected} ({progress*100:.1f}%)")
        
        st.divider()
        
        # Results by type
        by_type = defaultdict(list)
        for r in results:
            by_type[r.get("diagram_type", "unknown")].append(r)
        
        st.subheader("Results by Type")
        cols = st.columns(len(by_type))
        for i, (dtype, type_results) in enumerate(by_type.items()):
            success_count = sum(1 for r in type_results if r.get("success"))
            avg_q = sum(r.get("quality_score", 0) for r in type_results if r.get("success")) / max(success_count, 1)
            with cols[i]:
                st.metric(dtype.capitalize(), f"{success_count}/{len(type_results)}")
                st.caption(f"Avg: {avg_q:.1f}")
        
        st.divider()
        
        # Recent results
        st.subheader("Recent Results")
        
        # Filter options
        show_only = st.selectbox("Show", ["All", "Success only", "Failed only"], key=f"filter_{phase_name}")
        
        filtered = results
        if show_only == "Success only":
            filtered = [r for r in results if r.get("success")]
        elif show_only == "Failed only":
            filtered = [r for r in results if not r.get("success")]
        
        for r in filtered[-10:][::-1]:  # Show last 10, newest first
            mcq_id = r.get("mcq_id", "Unknown")
            dtype = r.get("diagram_type", "unknown")
            method = r.get("generation_method", "unknown")
            quality = r.get("quality_score", 0)
            success = r.get("success", False)
            svg_path = r.get("svg_path")
            error = r.get("error")
            
            with st.expander(f"{'✅' if success else '❌'} {mcq_id[:50]} - {dtype} - Quality: {quality:.1f}"):
                col_info, col_svg = st.columns([1, 2])
                
                with col_info:
                    st.markdown(f"**MCQ ID:** {mcq_id}")
                    st.markdown(f"**Type:** {dtype}")
                    st.markdown(f"**Method:** {method}")
                    st.markdown(f"**Quality:** {quality:.1f}")
                    
                    if quality >= 70:
                        st.success("✓ Auto-accept")
                    elif quality >= 50:
                        st.warning("⚠ Manual review")
                    else:
                        st.error("✗ Auto-reject")
                    
                    if error:
                        st.error(f"Error: {error[:200]}")
                    
                    # Show question text
                    question = r.get("question_text", "")
                    if question:
                        st.caption(f"Q: {question[:150]}...")
                
                with col_svg:
                    if svg_path:
                        svg_full_path = Path(svg_path) if Path(svg_path).is_absolute() else output_dir / Path(svg_path).name
                        if svg_full_path.exists():
                            with open(svg_full_path) as f:
                                svg_content = f.read()
                            show_responsive_svg(svg_content)
                        else:
                            st.warning(f"File not found: {svg_path}")
    else:
        st.info(f"No results yet for {phase_name}")
        
        # Show SVG files if any
        svg_files = list(output_dir.glob("mcq_*.svg"))
        if svg_files:
            st.write(f"Found {len(svg_files)} SVG files")
            
            for svg_file in svg_files[:10]:
                with st.expander(svg_file.name):
                    with open(svg_file) as f:
                        show_responsive_svg(f.read())

def show_phase_test(output_dir, phase_name):
    """Show test results from test_results.json."""
    results_file = output_dir / "test_results.json"
    
    if results_file.exists():
        with open(results_file) as f:
            data = json.load(f)
        
        results = data.get("results", [])
        success = sum(1 for r in results if r.get("success"))
        avg_quality = sum(r.get("quality_score", 0) for r in results) / max(len(results), 1)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", len(results))
        col2.metric("Success", f"{success}/{len(results)}")
        col3.metric("Avg Quality", f"{avg_quality:.1f}")
        
        st.divider()
        
        for i, r in enumerate(results):
            mcq_id = r.get("mcq_id", f"Result {i+1}")
            dtype = r.get("type", "unknown")
            quality = r.get("quality_score", 0)
            svg_path = r.get("svg_path")
            
            with st.expander(f"{'✅' if r.get('success') else '❌'} {mcq_id[:40]} - {dtype} - Q: {quality:.1f}"):
                if svg_path:
                    full_path = Path(svg_path) if Path(svg_path).is_absolute() else output_dir / Path(svg_path).name
                    if full_path.exists():
                        with open(full_path) as f:
                            show_responsive_svg(f.read())
    else:
        svg_files = list(output_dir.glob("*.svg"))
        if svg_files:
            st.write(f"**{len(svg_files)} SVG files**")
            for svg_file in svg_files[:20]:
                with st.expander(svg_file.name):
                    with open(svg_file) as f:
                        show_responsive_svg(f.read())
        else:
            st.info("No results yet")

with tabs[0]:
    show_phase_batch(OUTPUT_DIR / "phase3a", "Phase 3A")

with tabs[1]:
    show_phase_test(OUTPUT_DIR / "phase3a_test", "Phase 3A Test")

with tabs[2]:
    show_phase_test(OUTPUT_DIR / "phase3c_test", "Phase 3C Test")
