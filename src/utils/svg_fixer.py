"""
Standalone SVG fixer utility.
Fixes broken attributes from Gemini output.
"""
import re


def fix_broken_svg_attributes(svg: str) -> str:
    """Fix incomplete stroke- and fill- attributes from Gemini output."""
    result = svg
    
    # Fix stroke- without value
    result = result.replace('stroke-/>', 'stroke-width="1"/>')
    result = result.replace('stroke->', 'stroke-width="1">')
    result = result.replace('stroke- />', 'stroke-width="1"/>')
    result = result.replace('stroke- >', 'stroke-width="1">')
    
    # Fix fill- without value
    result = result.replace('fill-/>', 'fill="black"/>')
    result = result.replace('fill->', 'fill="black">')
    
    # Fix patterns with preceding quote
    result = result.replace('" stroke-/>', '" stroke-width="1"/>')
    result = result.replace('" stroke->', '" stroke-width="1">')
    result = result.replace('" fill-/>', '" fill="black"/>')
    result = result.replace('" fill->', '" fill="black">')
    
    return result


def fix_svg_file(filepath: str) -> bool:
    """Fix a single SVG file in place."""
    import os
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        fixed = fix_broken_svg_attributes(content)
        
        if fixed != content:
            with open(filepath, 'w') as f:
                f.write(fixed)
            return True
        return False
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False


def fix_all_svgs_in_directory(directory: str) -> int:
    """Fix all SVG files in a directory."""
    import os
    from pathlib import Path
    
    fixed_count = 0
    for svg_file in Path(directory).glob('*.svg'):
        if fix_svg_file(str(svg_file)):
            fixed_count += 1
            print(f"Fixed: {svg_file.name}")
    
    return fixed_count


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = "/root/image_generation_flexily/output/generated/reference"
    
    print(f"Fixing SVGs in: {directory}")
    count = fix_all_svgs_in_directory(directory)
    print(f"Fixed {count} SVG files")
