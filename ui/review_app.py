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


def save_review(mcq_id: str, status: str, comment: str, smiles: str = None, svg: str = None):
    """Save a review decision."""
    review = {
        'mcq_id': mcq_id,
        'status': status,
        'comment': comment,
        'smiles': smiles,
        'svg': svg,
        'reviewed_at': datetime.now().isoformat()
    }
    
    append_jsonl(REVIEWS_FILE, review)
    
    if status == 'approved':
        append_jsonl(APPROVED_FILE, review)
    else:
        append_jsonl(NEEDS_REVISION_FILE, review)


def main():
    st.title("🖼️ MCQ Image Review")
    st.markdown("Review generated SVG images. Approve or reject with comments.")
    
    # Load results
    results_file = GENERATED_DIR / "chemistry" / "batch_results.jsonl"
    
    if not results_file.exists():
        st.warning("No results found. Run Phase 1 generation first.")
        st.code("python scripts/run_phase1.py")
        return
    
    results = load_jsonl(results_file)
    reviews = load_reviews()
    
    # Initialize session state for page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0
    
    # Sidebar
    st.sidebar.header("Filters")
    
    filter_status = st.sidebar.radio(
        "Show items:",
        ["Pending review", "All", "Approved", "Rejected"],
        index=0
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
    approved_count = len([r for r in reviews.values() if r['status'] == 'approved'])
    rejected_count = len([r for r in reviews.values() if r['status'] == 'rejected'])
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
    
    # Pagination
    total_pages = (len(filtered) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if total_pages == 0:
        total_pages = 1
    
    # Ensure current page is valid
    if st.session_state.current_page >= total_pages:
        st.session_state.current_page = 0
    
    start_idx = st.session_state.current_page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, len(filtered))
    page_items = filtered[start_idx:end_idx]
    
    # Pagination controls
    col_prev, col_page, col_next = st.columns([1, 2, 1])
    
    with col_prev:
        if st.button("⬅ Previous", disabled=st.session_state.current_page == 0):
            st.session_state.current_page -= 1
            st.rerun()
    
    with col_page:
        st.markdown(f"**Page {st.session_state.current_page + 1} of {total_pages}** (Items {start_idx + 1}-{end_idx} of {len(filtered)})")
    
    with col_next:
        if st.button("Next ➡", disabled=st.session_state.current_page >= total_pages - 1):
            st.session_state.current_page += 1
            st.rerun()
    
    st.divider()
    
    # Review items on current page
    for idx, result in enumerate(page_items):
        mcq_id = result['mcq_id']
        existing_review = reviews.get(mcq_id)
        
        with st.container(border=True):
            # Header
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
            st.markdown(f"**SMILES:** `{result.get('smiles', 'N/A')}`")
            
            question = result.get('question_text', '')
            if question:
                st.markdown(f"**Question:** {question[:200]}{'...' if len(question) > 200 else ''}")
            
            # SVG Display
            st.markdown("**Generated Diagram:**")
            svg = result.get('svg', '')
            
            styled_svg = svg.replace(
                '<svg',
                '<svg style="background: white; border-radius: 8px; padding: 10px; max-width: 100%; height: auto;"'
            )
            st.components.v1.html(styled_svg, height=280)
            
            # Expander for SVG code
            with st.expander("View SVG Code"):
                st.code(svg[:1000] + "..." if len(svg) > 1000 else svg, language='xml')
            
            # Review section
            if existing_review:
                st.info(f"**Your review:** {existing_review['status'].upper()}")
                if existing_review.get('comment'):
                    st.markdown(f"**Comment:** {existing_review['comment']}")
            else:
                # Comment field
                comment = st.text_area(
                    "Comment (required for reject):",
                    placeholder="Describe issues with this diagram...",
                    key=f"input_comment_{mcq_id}",
                    height=60
                )
                
                # Buttons
                col_approve, col_reject = st.columns(2)
                
                with col_approve:
                    if st.button("✓ Approve", key=f"btn_approve_{mcq_id}", type="primary", use_container_width=True):
                        save_review(
                            mcq_id=mcq_id,
                            status='approved',
                            comment=comment,
                            smiles=result.get('smiles'),
                            svg=svg
                        )
                        st.success("✓ Approved and saved!")
                        st.rerun()
                
                with col_reject:
                    if st.button("✗ Reject", key=f"btn_reject_{mcq_id}", use_container_width=True):
                        if not comment.strip():
                            st.warning("⚠ Please add a comment explaining the issue.")
                        else:
                            save_review(
                                mcq_id=mcq_id,
                                status='rejected',
                                comment=comment,
                                smiles=result.get('smiles'),
                                svg=svg
                            )
                            st.error("✗ Rejected and saved!")
                            st.rerun()
        
        st.markdown("---")
    
    # Pagination at bottom too
    col_prev2, col_page2, col_next2 = st.columns([1, 2, 1])
    
    with col_prev2:
        if st.button("⬅ Previous", key="prev_bottom", disabled=st.session_state.current_page == 0):
            st.session_state.current_page -= 1
            st.rerun()
    
    with col_page2:
        st.markdown(f"**Page {st.session_state.current_page + 1} of {total_pages}**")
    
    with col_next2:
        if st.button("Next ➡", key="next_bottom", disabled=st.session_state.current_page >= total_pages - 1):
            st.session_state.current_page += 1
            st.rerun()
    
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
