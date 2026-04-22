"""
Mermaid.js SVG Generator
Generates flowcharts, cycles, and pedigree diagrams using Mermaid.js
and renders them to SVG using Playwright.
"""
import os
import re
import json
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

from google import genai
from google.genai import types

from config.settings import GCP_PROJECT_ID, GCP_LOCATION
from src.utils.svg_validator import inject_textbook_style


MERMAID_PROMPT_TEMPLATE = """You are an expert at creating Mermaid.js diagrams for educational biology content.

Generate a Mermaid.js diagram that illustrates the concept described in the question below.

RULES:
1. Use appropriate diagram type:
   - flowchart TD/TB for processes and pathways
   - graph LR for cycles with feedback
   - For pedigrees, use specific pedigree notation if possible, otherwise use a simple graph
2. Use clear, educational labels
3. Keep the diagram simple and easy to read
4. Use black and white styling (no colors)
5. Label all important nodes and transitions

QUESTION: {question}

Output ONLY the Mermaid.js code. Start with the diagram type declaration.
Example format:
```mermaid
flowchart TD
    A[Start] --> B[Process]
    B --> C[End]
```

For pedigree charts, use this format:
```mermaid
graph TD
    A((Male)) --- B((Female))
    A --- C[Child 1]
    B --- C[Child 1]
```

Generate the Mermaid.js code now:
"""


@dataclass
class MermaidGenResult:
    success: bool
    svg: Optional[str]
    mermaid_code: Optional[str]
    error: Optional[str]


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: white;
        }}
        .mermaid {{
            font-family: 'Times New Roman', serif;
        }}
    </style>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            fontFamily: 'Times New Roman, serif'
        }});
    </script>
</head>
<body>
    <div class="mermaid">
{mermaid_code}
    </div>
</body>
</html>
"""


class MermaidGenerator:
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=GCP_LOCATION
        )
        self.model_name = "gemini-2.5-pro"
        self._playwright = None
    
    async def _init_playwright(self):
        if self._playwright is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
            except ImportError:
                raise ImportError(
                    "Playwright not installed. Run: pip install playwright && playwright install chromium"
                )
        return self._playwright
    
    async def generate_mermaid_code(self, question: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate Mermaid.js code from question using Gemini."""
        prompt = MERMAID_PROMPT_TEMPLATE.format(question=question)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            code = response.text
            
            mermaid_match = re.search(r'```(?:mermaid)?\s*([\s\S]*?)```', code)
            if mermaid_match:
                code = mermaid_match.group(1).strip()
            
            if code.startswith('mermaid'):
                code = code[7:].strip()
            
            if not any(code.startswith(dt) for dt in ['flowchart', 'graph', 'sequenceDiagram', 'classDiagram', 'stateDiagram', 'erDiagram', 'pie', 'gantt']):
                return None, "Invalid Mermaid.js code - missing diagram type"
            
            return code, None
            
        except Exception as e:
            return None, str(e)
    
    async def render_to_svg(self, mermaid_code: str) -> Tuple[Optional[str], Optional[str]]:
        """Render Mermaid.js code to SVG using Playwright."""
        playwright = await self._init_playwright()
        
        html_content = HTML_TEMPLATE.format(mermaid_code=mermaid_code)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            html_path = f.name
        
        try:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(f'file://{html_path}')
            
            await page.wait_for_selector('.mermaid svg', timeout=10000)
            
            await asyncio.sleep(0.5)
            
            svg_element = await page.query_selector('.mermaid svg')
            if not svg_element:
                await browser.close()
                return None, "SVG element not found in rendered page"
            
            svg = await svg_element.inner_html()
            outer_svg = await svg_element.evaluate('el => el.outerHTML')
            
            await browser.close()
            
            svg = self._clean_mermaid_svg(outer_svg)
            
            return svg, None
            
        except Exception as e:
            return None, f"Playwright rendering error: {str(e)}"
        finally:
            os.unlink(html_path)
    
    def _clean_mermaid_svg(self, svg: str) -> str:
        """Clean and apply textbook styling to Mermaid SVG."""
        svg = re.sub(r'<\?xml[^>]*\?>', '', svg)
        
        svg = re.sub(r'font-family="[^"]*"', 'font-family="Times New Roman, serif"', svg)
        
        svg = re.sub(r'fill="[^"]*"(?=[^>]*stroke)', 'fill="none"', svg)
        svg = re.sub(r'stroke="[^"]*"', 'stroke="#111111"', svg)
        
        svg = inject_textbook_style(svg)
        
        if 'xmlns' not in svg:
            svg = svg.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        
        return svg.strip()
    
    async def generate(self, question: str) -> MermaidGenResult:
        """Generate SVG from question using Mermaid.js."""
        mermaid_code, code_error = await self.generate_mermaid_code(question)
        
        if code_error or not mermaid_code:
            return MermaidGenResult(
                success=False,
                svg=None,
                mermaid_code=mermaid_code,
                error=code_error or "Failed to generate Mermaid code"
            )
        
        svg, render_error = await self.render_to_svg(mermaid_code)
        
        if render_error or not svg:
            return MermaidGenResult(
                success=False,
                svg=None,
                mermaid_code=mermaid_code,
                error=render_error or "Failed to render SVG"
            )
        
        return MermaidGenResult(
            success=True,
            svg=svg,
            mermaid_code=mermaid_code,
            error=None
        )
    
    async def close(self):
        """Close Playwright browser."""
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


async def generate_mermaid_diagram(question: str) -> MermaidGenResult:
    """Convenience function to generate a Mermaid diagram."""
    generator = MermaidGenerator()
    try:
        return await generator.generate(question)
    finally:
        await generator.close()


if __name__ == "__main__":
    async def test():
        test_questions = [
            "Based on the provided pedigree for hemophilia, determine the genotype of individual 5.",
            "The Krebs cycle involves multiple steps. Show the main transformations.",
            "Identify the phases A, B, C, and D in the provided cell cycle diagram.",
        ]
        
        generator = MermaidGenerator()
        
        for q in test_questions:
            print(f"\nQ: {q[:60]}...")
            result = await generator.generate(q)
            
            if result.success:
                print(f"  SUCCESS - SVG length: {len(result.svg)} chars")
                print(f"  Mermaid code:\n{result.mermaid_code[:200]}...")
            else:
                print(f"  FAILED: {result.error}")
        
        await generator.close()
    
    asyncio.run(test())
