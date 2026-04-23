"""
Streamlit UI for reviewing generated MCQ images.
Features: Approve/Reject with comments, persistent storage, filtering, pagination.
"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="MCQ Image Review",
    page_icon="🖼️",
    layout="wide"
)

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
GENERATED_DIR = OUTPUT_DIR / "generated"
REVIEW_DIR = OUTPUT_DIR / "reviews"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)

REVIEWS_FILE = REVIEW_DIR / "reviews.jsonl"
APPROVED_FILE = REVIEW_DIR / "approved.jsonl"
NEEDS_REVISION_FILE = REVIEW_DIR / "needs_revision.jsonl"
ITEMS_PER_PAGE = 10


def load_jsonl(filepath):
    """Load JSONL file."""
    items = []
    if not filepath.exists():
        return items
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items


def append_jsonl(filepath, item):
    """Append item to JSONL file."""
    with open(filepath, 'a') as f:
        f.write(json.dumps(item) + '\n')


def load_reviews():
    """Load all reviews as dict keyed by mcq_id."""
    reviews = {}
    if REVIEWS_FILE.exists():
        for item in load_jsonl(REVIEWS_FILE):
            reviews[item['mcq_id']] = item
    return reviews


def save_review(mcq_id: str, status: str, comment: str, phase: int = None, reference_image: str = None, svg: str = None):
    """Save a review decision."""
    review = {
        'mcq_id': mcq_id,
        'status': status,
        'comment': comment,
        'phase': phase,
        'reference_image': reference_image,
        'svg': svg,
        'reviewed_at': datetime.now().isoformat()
    }
    
    append_jsonl(REVIEWS_FILE, review)
    
    if status == 'approved':
        append_jsonl(APPROVED_FILE, review)
    else:
        append_jsonl(NEEDS_REVISION_FILE, review)


def display_results(results, reviews, phase_label):
    """Display results for a phase."""
    if not results:
        st.info(f"No {phase_label} results found.")
        return
    
    # Initialize session state for page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0
    
    # Filter control
    filter_status = st.radio(
        "Show items:",
        ["Pending review", "All", "Approved", "Rejected"],
        index=0,
        horizontal=True,
        key=f"filter_{phase_label}"
    )
    
    # Filter results
    if filter_status == "Pending review":
        filtered = [r for r in results if r.get('svg') and r['mcq_id'] not in reviews]
    elif filter_status == "Approved":
        filtered = [r for r in results if r['mcq_id'] in reviews and reviews[r['mcq_id']]['status'] == 'approved']
    elif filter_status == "Rejected":
        filtered = [r for r in results if r['mcq_id'] in reviews and reviews[r['mcq_id']]['status'] == 'rejected']
    else:
        filtered = [r for r in results if r.get('svg')]
    
    # Stats
    total = len([r for r in results if r.get('svg')])
    approved_count = len([r for r in reviews.values() if r['status'] == 'approved' and r.get('phase') == (1 if 'Phase 1' in phase_label else 2)])
    rejected_count = len([r for r in reviews.values() if r['status'] == 'rejected' and r.get('phase') == (1 if 'Phase 1' in phase_label else 2)])
    pending_count = total - approved_count - rejected_count
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Generated", total)
    with col2:
        st.metric("Pending", pending_count)
    with col3:
        st.metric("Approved", approved_count)
    with col4:
        st.metric("Rejected", rejected_count)
    
    # Progress bar
    if total > 0:
        progress = (approved_count + rejected_count) / total
        st.progress(progress, text=f"Review progress: {int(progress * 100)}%")
    
    st.divider()
    
    if not filtered:
        st.info(f"No items match the filter.")
        return
    
    # Pagination
    total_pages = (len(filtered) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if total_pages == 0:
        total_pages = 1
    
    # Reset page if needed
    page_key = f"current_page_{phase_label}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 0
    
    if st.session_state[page_key] >= total_pages:
        st.session_state[page_key] = 0
    
    start_idx = st.session_state[page_key] * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, len(filtered))
    page_items = filtered[start_idx:end_idx]
    
    # Pagination controls
    col_prev, col_page, col_next = st.columns([1, 2, 1])
    
    with col_prev:
        if st.button("⬅ Previous", disabled=st.session_state[page_key] == 0, key=f"prev_{phase_label}"):
            st.session_state[page_key] -= 1
            st.rerun()
    
    with col_page:
        st.markdown(f"**Page {st.session_state[page_key] + 1} of {total_pages}** (Items {start_idx + 1}-{end_idx} of {len(filtered)})")
    
    with col_next:
        if st.button("Next ➡", disabled=st.session_state[page_key] >= total_pages - 1, key=f"next_{phase_label}"):
            st.session_state[page_key] += 1
            st.rerun()
    
    st.divider()
    
    # Review items
    for idx, result in enumerate(page_items):
        mcq_id = result['mcq_id']
        existing_review = reviews.get(mcq_id)
        phase_num = 1 if 'Phase 1' in phase_label else 2
        
        with st.container(border=True):
            col_id, col_status = st.columns([4, 1])
            with col_id:
                st.subheader(f"MCQ: {mcq_id[:60]}...")
            with col_status:
                if existing_review:
                    if existing_review['status'] == 'approved':
                        st.success("✓ Approved")
                    else:
                        st.error("✗ Rejected")
                else:
                    st.info("○ Pending")
            
            # Details
            st.markdown(f"**Subject:** {result.get('subject', 'N/A')}")
            
            if phase_num == 1:
                st.markdown(f"**SMILES:** `{result.get('smiles', 'N/A')}`")
            else:
                if result.get('reference_image'):
                    st.markdown(f"**Reference Image:** `{result.get('reference_image', '').split('/')[-1]}`")
                if result.get('similarity_score'):
                    st.markdown(f"**Similarity:** `{result.get('similarity_score', 0):.3f}`")
            
            # Question display
            question = result.get('question_text', '')
            if question:
                st.markdown(f"**Question:** {question[:200]}{'...' if len(question) > 200 else ''}")
            
            # SIDE-BY-SIDE DISPLAY FOR PHASE 2
            if phase_num == 2:
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.markdown("**Inspiration (References):**")
                    ref_paths = result.get('references_used', [])
                    if isinstance(ref_paths, str):
                        # Some old results might have single string
                        ref_paths = [ref_paths]
                    
                    if ref_paths:
                        for i, img_path in enumerate(ref_paths):
                            if Path(img_path).exists():
                                st.image(img_path, caption=f"Reference {i+1}", use_column_width=True)
                            else:
                                st.warning(f"Image not found: {Path(img_path).name}")
                    else:
                        st.info("No reference images stored for this result.")
                
                with col_right:
                    st.markdown("**Generated Diagram:**")
                    svg = result.get('svg', '')
                    
                    if svg.startswith('data:image'):
                        # Display PNG/JPEG from data URI
                        st.image(svg, use_column_width=True)
                    else:
                        # Original SVG display
                        st.markdown(
                            f"""
                            <div style="background-color: white; padding: 10px; border: 1px solid #ddd; border-radius: 8px; display: flex; justify-content: center; align-items: center; min-height: 200px;">
                                {svg}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            else:
                # Original Phase 1 display
                st.markdown("**Generated Diagram:**")
                svg = result.get('svg', '')
                if svg.startswith('data:image'):
                    st.image(svg, use_column_width=True)
                else:
                    st.markdown(
                        f"""
                        <div style="background-color: white; padding: 20px; border: 1px solid #ddd; border-radius: 10px; display: flex; justify-content: center; align-items: center; margin-bottom: 20px;">
                            {svg}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            # Expander for SVG code
            with st.expander("View SVG Code"):
                svg = result.get('svg', '')
                st.code(svg[:1000] + "..." if len(svg) > 1000 else svg, language='xml')
            
            # Review section
            if existing_review:
                st.info(f"**Your review:** {existing_review['status'].upper()}")
                if existing_review.get('comment'):
                    st.markdown(f"**Comment:** {existing_review['comment']}")
            else:
                comment = st.text_area(
                    "Comment (required for reject):",
                    placeholder="Describe issues with this diagram...",
                    key=f"input_comment_{phase_label}_{mcq_id}",
                    height=60
                )
                
                col_approve, col_reject = st.columns(2)
                
                with col_approve:
                    if st.button("✓ Approve", key=f"btn_approve_{phase_label}_{mcq_id}", type="primary", use_container_width=True):
                        save_review(
                            mcq_id=mcq_id,
                            status='approved',
                            comment=comment,
                            phase=phase_num,
                            reference_image=result.get('reference_image'),
                            svg=svg
                        )
                        st.success("✓ Approved and saved!")
                        st.rerun()
                
                with col_reject:
                    if st.button("✗ Reject", key=f"btn_reject_{phase_label}_{mcq_id}", use_container_width=True):
                        if not comment.strip():
                            st.warning("⚠ Please add a comment explaining the issue.")
                        else:
                            save_review(
                                mcq_id=mcq_id,
                                status='rejected',
                                comment=comment,
                                phase=phase_num,
                                reference_image=result.get('reference_image'),
                                svg=svg
                            )
                            st.error("✗ Rejected and saved!")
                            st.rerun()
        
        st.markdown("---")


def main():
    st.title("🖼️ MCQ Image Review")
    st.markdown("Review generated SVG images. Approve or reject with comments.")
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    phase1_file = GENERATED_DIR / "chemistry" / "batch_results.jsonl"
    phase2_file = GENERATED_DIR / "reference" / "phase2_results.jsonl"
    test_v3_dir = GENERATED_DIR / "test_v3"
    
    phase1_results = load_jsonl(phase1_file) if phase1_file.exists() else []
    phase2_results = load_jsonl(phase2_file) if phase2_file.exists() else []
    
    test_v3_results = []
    if test_v3_dir.exists():
        for svg_file in test_v3_dir.glob("*.svg"):
            mcq_id = svg_file.stem
            with open(svg_file, 'r') as f:
                svg_content = f.read()
            test_v3_results.append({
                'mcq_id': mcq_id,
                'svg': svg_content,
                'subject': 'test',
                'question_text': f'Test V3 result for {mcq_id}',
                'generation_method': 'test_v3'
            })
        
        for html_file in test_v3_dir.glob("*.html"):
            mcq_id = html_file.stem
            with open(html_file, 'r') as f:
                html_content = f.read()
            test_v3_results.append({
                'mcq_id': mcq_id,
                'svg': html_content,
                'subject': 'test',
                'question_text': f'Test V3 Imagen result: {mcq_id}',
                'generation_method': 'test_v3_imagen'
            })
    
    reviews = load_reviews()
    
    st.sidebar.header("📊 Summary")
    st.sidebar.write(f"Phase 1: {len(phase1_results)} generated")
    st.sidebar.write(f"Phase 2: {len(phase2_results)} generated")
    st.sidebar.write(f"Test V3: {len(test_v3_results)} generated")
    
    tab1, tab2, tab3 = st.tabs([
        f"Phase 1: SMILES ({len(phase1_results)})",
        f"Phase 2: Reference ({len(phase2_results)})",
        f"Test V3 ({len(test_v3_results)})"
    ])
    
    with tab1:
        st.header("Phase 1: Chemistry SMILES → SVG")
        st.markdown("Generated from SMILES strings using RDKit with custom organic molecule renderer.")
        display_results(phase1_results, reviews, "Phase 1")
    
    with tab2:
        st.header("Phase 2: Reference-Based Generation")
        st.markdown("Generated using Gemini Vision with textbook reference images.")
        display_results(phase2_results, reviews, "Phase 2")
    
    with tab3:
        st.header("Test V3: Improved Textbook Style")
        st.markdown("Generated with enhanced Python/Mermaid/Imagen generators.")
        display_results(test_v3_results, reviews, "Test V3")
    
    # Sidebar info
    st.sidebar.divider()
    st.sidebar.header("Files")
    st.sidebar.markdown(f"**Reviews:** `{REVIEWS_FILE}`")
    st.sidebar.markdown(f"**Approved:** `{APPROVED_FILE}`")
    st.sidebar.markdown(f"**Rejected:** `{NEEDS_REVISION_FILE}`")
    
    # Recent rejected comments
    st.sidebar.divider()
    st.sidebar.header("Recent Rejected")
    
    if NEEDS_REVISION_FILE.exists():
        recent = load_jsonl(NEEDS_REVISION_FILE)[-5:]
        for r in reversed(recent):
            with st.sidebar.container(border=True):
                st.markdown(f"**{r['mcq_id'][:25]}...**")
                st.markdown(f"_{r.get('comment', 'No comment')[:80]}..._")


if __name__ == "__main__":
    main()
