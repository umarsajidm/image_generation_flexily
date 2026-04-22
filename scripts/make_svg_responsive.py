"""
Make SVG files responsive by removing hardcoded width/height
and adding responsive attributes.

Golden Rule: SVG with viewBox + responsive width = perfect scaling
"""
import re
import glob
from pathlib import Path
from typing import List, Tuple


def make_svg_responsive(svg_content: str) -> Tuple[str, bool]:
    """
    Make a single SVG responsive.
    Returns (modified_content, was_changed).
    """
    original = svg_content
    
    # 1. Remove hardcoded width and height (e.g., width="460pt" height="345pt")
    svg_content = re.sub(r'(<svg[^>]*?)\swidth="[^"]+"', r'\1', svg_content)
    svg_content = re.sub(r'(<svg[^>]*?)\sheight="[^"]+"', r'\1', svg_content)
    
    # 2. Inject responsive width/height while keeping original viewBox
    svg_content = svg_content.replace(
        '<svg ', 
        '<svg width="100%" height="auto" preserveAspectRatio="xMidYMid meet" '
    )
    
    # 3. Remove 'pt' units from font sizes (browsers interpret unitless as px)
    svg_content = re.sub(r'font-size="(\d+)pt"', r'font-size="\1"', svg_content)
    
    return svg_content, svg_content != original


def make_svgs_responsive(directory_path: str) -> dict:
    """
    Make all SVG files in a directory responsive.
    Returns stats dict with counts.
    """
    src_dir = Path(directory_path)
    svg_files = list(src_dir.glob("*.svg"))
    
    stats = {
        'total': len(svg_files),
        'converted': 0,
        'skipped': 0,
        'errors': 0
    }
    
    if not svg_files:
        print(f"No SVG files found in {directory_path}")
        return stats
    
    for file_path in svg_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            modified_content, was_changed = make_svg_responsive(svg_content)
            
            if was_changed:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                stats['converted'] += 1
            else:
                stats['skipped'] += 1
                
        except Exception as e:
            print(f"  Error: {file_path.name}: {e}")
            stats['errors'] += 1
    
    print(f"Responsive SVG Conversion:")
    print(f"  Total:     {stats['total']}")
    print(f"  Converted: {stats['converted']}")
    print(f"  Skipped:   {stats['skipped']}")
    print(f"  Errors:    {stats['errors']}")
    
    return stats


def verify_responsive(directory_path: str) -> dict:
    """
    Verify all SVGs in a directory are responsive.
    Returns stats dict with verification results.
    """
    src_dir = Path(directory_path)
    svg_files = list(src_dir.glob("*.svg"))
    
    stats = {
        'total': len(svg_files),
        'responsive': 0,
        'not_responsive': 0,
        'issues': []
    }
    
    for svg_file in svg_files:
        content = svg_file.read_text()
        
        has_viewbox = 'viewBox' in content
        has_responsive_width = 'width="100%"' in content
        has_responsive_height = 'height="auto"' in content
        has_preserve = 'preserveAspectRatio=' in content
        
        if has_viewbox and has_responsive_width and has_responsive_height:
            stats['responsive'] += 1
        else:
            stats['not_responsive'] += 1
            issues = []
            if not has_viewbox:
                issues.append('missing viewBox')
            if not has_responsive_width:
                issues.append('missing width="100%"')
            if not has_responsive_height:
                issues.append('missing height="auto"')
            stats['issues'].append({
                'file': svg_file.name,
                'issues': issues
            })
    
    print(f"Responsive Verification:")
    print(f"  Total:          {stats['total']}")
    print(f"  Responsive:     {stats['responsive']}")
    print(f"  Not Responsive: {stats['not_responsive']}")
    
    if stats['issues']:
        print(f"\n  Issues found:")
        for item in stats['issues'][:10]:
            print(f"    {item['file']}: {', '.join(item['issues'])}")
    
    return stats


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = 'output/generated/phase3a'
    
    print(f"Processing: {directory}\n")
    make_svgs_responsive(directory)
    print()
    verify_responsive(directory)
