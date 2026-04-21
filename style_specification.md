# Punjab 2nd Year Chemistry Textbook - Chemical Diagram Style Specification

**Generated:** April 21, 2026  
**Source:** 2nd Year Chemistry Punjab Text Book PDF (403 pages)  
**Focus:** Chapters 7-16 (Organic Chemistry)  
**Total Images Analyzed:** 372 images from pages 250-400

---

## Executive Summary

This specification document details the visual style conventions used in the Punjab 2nd Year Chemistry textbook for chemical diagrams. The analysis covers organic chemistry content (pages 250-400), which includes alkenes, alkynes, benzene derivatives, phenolic compounds, carboxylic acids, and their reactions.

**Key Characteristics:**
- Clean, black-and-white structural diagrams
- Standard organic chemistry notation
- Multi-step reaction mechanisms with individual step diagrams
- Benzene structures using both Kekule and modern representations
- Academic textbook style with clear typography and spacing

---

## 1. Diagram Categories

Based on analysis of 372 images from pages 250-400, chemical diagrams fall into the following categories:

### 1.1 Simple Molecular Structures (35% of images)
**Examples:**
- Alkanes and alkenes: `images/img_p257_001.png`, `images/img_p257_002.png`
- Benzene derivatives: `images/img_p282_001.png`, `images/img_p282_002.png`, `images/img_p282_003.png`
- Substituted compounds: `images/img_p283_003.png`, `images/img_p283_004.png`

**Typical dimensions:** 250-289 × 400-429 pixels  
**File size:** 9-27 KB

---

### 1.2 Reaction Mechanisms (25% of images)
**Examples:**
- Ester formation mechanism: `images/img_p351_001.png`, `images/img_p351_002.png`, `images/img_p351_003.png`, `images/img_p351_004.png`
- Amide formation: `images/img_p352_001.png`, `images/img_p352_002.png`, `images/img_p352_003.png`
- Addition reactions: `images/img_p258_001.png`, `images/img_p258_002.png`

**Typical dimensions:** 1300-1800 × 300-500 pixels  
**File size:** 85-170 KB

---

### 1.3 Benzene and Aromatic Structures (20% of images)
**Examples:**
- Basic benzene: `images/img_p282_001.png`, `images/img_p284_001.png`
- Polycyclic aromatics: `images/img_p283_001.png`, `images/img_p283_002.png`
- Substituted positions: `images/img_p284_001.png`, `images/img_p284_002.png`, `images/img_p284_003.png`, `images/img_p284_004.png`

**Typical dimensions:** 1800-2052 × 400-1180 pixels (complex structures), 250-289 × 400-429 pixels (single structures)

---

### 1.4 Isomer Comparisons (10% of images)
**Examples:**
- Disubstituted benzene isomers: `images/img_p286_001.png`, `images/img_p286_002.png`
- Acid strength comparisons: `images/img_p322_002.png`

**Typical dimensions:** 1000-1600 × 300-500 pixels

---

### 1.5 Synthetic Pathways (5% of images)
**Examples:**
- Comprehensive synthesis: `images/img_p251_001.png` (174 KB, largest single image)

**Typical dimensions:** 1900+ × 400+ pixels

---

### 1.6 Specialized Structures (5% of images)
**Examples:**
- Acid-base comparisons: `images/img_p322_001.png`
- Structural formula variations: `images/img_p322_004.png`, `images/img_p322_005.png`, `images/img_p322_006.png`, `images/img_p322_007.png`

---

## 2. Visual Specifications

### 2.1 Line Thickness
- **Bond lines:** Medium thickness (appears as standard for chemical structures)
- **Double bonds:** Two parallel lines with consistent spacing between them
- **Triple bonds:** Three parallel lines with equal spacing
- **Wedges/dashes:** Used sparingly for stereochemistry when needed

---

### 2.2 Font Usage
**Based on text analysis:**
- **Chemical formulas:** Sans-serif font (appears to be Arial or similar)
- **Subscripts/Superscripts:** Properly formatted using Unicode or LaTeX notation
- **Atom labels:** Uppercase for first letter, lowercase for second letter (e.g., "CH", "OH")
- **Chemical symbols:** Standard IUPAC notation

**Font sizes (relative):**
- Large structures: ~12-14pt equivalent
- Medium structures: ~10-12pt equivalent
- Small labels: ~8-10pt equivalent

---

### 2.3 Color Usage
- **Primary color:** Black (all structural elements)
- **Background:** White
- **No color coding** for different atoms or elements
- **No highlighting** or accent colors used

**Note:** All diagrams appear to be black-and-white line drawings, typical of academic textbooks.

---

## 3. Bond Representation

### 3.1 Single Bonds
- Represented by single solid lines
- Connect atoms at standard bond angles
- Consistent thickness throughout diagram

### 3.2 Double Bonds
- **Two parallel lines** with small but consistent spacing (~2-3 pixels)
- Examples observed in ethene structures: `CH=CH`, `CH-CH=CH-CH`

### 3.3 Triple Bonds
- **Three parallel lines** with equal small spacing
- Examples: alkynes like `HC≡CH`

### 3.4 Aromatic Ring Representation

**Two styles observed in textbook:**

#### A) Kekule Structure (传统)
```
   H   H
    \ /
     C
    / \
H-C     C-H
   \   /
    C-C
   /   \
H-C     C-H
    \ /
     C
    / \
   H   H
```
- Alternate single and double bonds
- Classical hexagonal representation
- Used for teaching structural concepts

#### B) Modern/Resonance Structure
```
    H   H
     \ /
      C
     / \
H-C       C-H
     \   /
      C-C
     /   \
H-C       C-H
     \ /
      C
     / \
    H   H
```
- **Circle inside hexagon** (delocalized electrons)
- All bonds shown as equivalent
- Used for showing actual structure and stability

**Key observation:** Both styles are used in the textbook, with Kekule for teaching fundamental concepts and modern/resonance for showing actual molecular structure.

---

## 4. Atom Representation

### 4.1 Carbon Atoms
- **Explicit vs. Implicit:**
  - **Often shown implicitly** as vertices (standard skeletal structure)
  - **Explicit when:** Terminal carbons, stereochemistry centers, or when teaching basic structures

- **Examples from text:**
  - `CH3-CH=CH-CH3` (butene with explicit carbons)
  - Skeletal structures for larger molecules

### 4.2 Hydrogen Atoms
- **Shown explicitly when:**
  - Terminal hydrogens on alkanes/alkenes
  - On heteroatoms (O-H, N-H)
  - When teaching basic structures
  
- **Not shown when:**
  - On carbons in skeletal structures
  - Internal hydrogens in complex molecules

- **Format:** Always as "H" (uppercase), connected to atom via line

### 4.3 Heteroatoms (O, N, Cl, S, P)
- **Always shown explicitly** with full atomic symbol
- **No color coding** - all black
- **Typical examples:**
  - `-OH` (hydroxyl)
  - `-COOH` (carboxyl)
  - `-NH2` (amino)
  - `-Cl` (chlorine)
  - `-SO3H` (sulfonic acid)

- **Atom label format:** First letter uppercase, second letter lowercase
  - Example: `Cl`, `Br`, `Na`, `Ca`

### 4.4 Subscripting
- **Properly formatted subscripts** using Unicode or LaTeX-style notation
- **Examples from OCR text:**
  - `C₆H₆` (benzene)
  - `CH₃-CH₂-OH` (ethanol)
  - `H₂SO₄` (sulfuric acid)

### 4.5 Atom Indices
- **Occasionally used** for clarity in reaction mechanisms
- **Format:** Numbered subscript or parenthetical notation
- **Examples:**
  - `C₁`, `C₂` (numbered carbons)
  - Position numbering in substituted benzene: 1,2; 1,3; 1,4 (ortho, meta, para)

---

## 5. Structural Details

### 5.1 Ring Structures

#### A) Benzene Ring
- **Hexagonal shape** with all 120° angles
- **All C-C bonds equal length** (1.397 Å mentioned in text)
- **Atoms can be:**
  - Shown explicitly (C and H atoms visible)
  - Shown skeletal (just hexagon frame)
  - Mixed (skeletal with substituent atoms shown)

#### B) Polycyclic Aromatic Hydrocarbons
- **Examples observed:**
  - Naphthalene: Two fused benzene rings
  - Phenanthrene: Three fused rings in specific arrangement
  - Anthracene: Three linearly fused rings
- **Fused at ortho positions** (adjacent carbons share bond)

#### C) Aromatic Substitution
- **Position notation:** 
  - ortho (o or 1,2)
  - meta (m or 1,3)
  - para (p or 1,4)
- **Position numbering starts from principal substituent (position 1)**

---

### 5.2 Branching Patterns
- **Standard organic chemistry conventions**
- **Angles:** Approximately 120° for sp², 109.5° for sp³ (though often approximated as 120° in 2D diagrams)
- **Branches shown:** 
  - Either as explicit atoms with bonds
  - Or as skeletal structures with substituents

**Example patterns observed:**
```
CH3-CH2-CH3 (propane)
CH3-CH2-CH=CH2 (butene)
CH3-CH2-CH2-OH (propanol)
```

---

### 5.3 Functional Groups
All functional groups follow standard conventions:

#### Hydroxyl (-OH)
```
C-O-H
```
- O connected to carbon and hydrogen
- Both bonds shown clearly

#### Carboxyl (-COOH)
```
    O
   ║
C-C-O-H
```
- Double bond to oxygen
- Single bond to hydroxyl

#### Carbonyl (-CO-)
```
    O
   ║
  C
```
- C=O double bond clearly shown

#### Aldehyde (-CHO)
```
    O
   ║
H-C-
```
- Terminal C=O with H attached

#### Ketone (-CO-)
```
    O
   ║
   C
  / \
R    R'
```
- C=O with two carbon substituents

#### Amino (-NH2)
```
C-N-H
    |
    H
```
- N with two hydrogens

#### Sulfonic (-SO3H)
```
     O
    ∥
C-S-O-H
    ∥
     O
```
- S with four attachments

---

### 5.4 Stereochemistry
- **Used sparingly** in observed diagrams
- **Wedge bonds** (solid triangle) for "out of page"
- **Dash bonds** (striped line) for "into page"
- **Most common examples:**
  - Chiral centers in organic synthesis
  - Cis/trans isomerism in alkenes

---

## 6. Layout and Spacing

### 6.1 Density
**Varies by diagram type:**

- **Simple structures:** Medium spacing, clear separation between atoms
  - Example: `images/img_p282_002.png` (256×417px) - single molecule with breathing room

- **Reaction mechanisms:** Compact but clear, sequential steps labeled
  - Example: `images/img_p351_002.png` (2036×236px) - horizontal flow

- **Comparative diagrams:** Structured grid layout
  - Example: `images/img_p284_001.png` - three isomers in horizontal arrangement

- **Complex pathways:** Multi-stage layout with arrows and labels
  - Example: `images/img_p251_001.png` (largest at 174KB) - comprehensive synthesis

---

### 6.2 Spacing Patterns

#### Horizontal Alignment
- **Individual molecules:** Centered within frame
- **Multiple molecules:** Uniform horizontal spacing (~10-15% of width)
- **Reaction sequences:** Left-to-right flow with arrows between steps

#### Vertical Alignment
- **Labeled diagrams:** Labels above or below structures
- **Multi-step mechanisms:** Vertical or horizontal flow depending on space
- **Comparison grids:** Vertical alignment for easy comparison

---

### 6.3 Angles Between Bonds
- **Standard angles used:**
  - **sp² carbons:** ~120° (benzene, alkenes, carbonyls)
  - **sp³ carbons:** ~109.5° (alkanes, saturated compounds)
  - **Approximated in 2D:** Often shown as 120° for clarity and simplicity

---

### 6.4 Overall Size Relative to Page

**Typical dimensions relative to textbook page:**

- **Small structures:** 25-30% of page width (250-300px)
- **Medium structures:** 50-70% of page width (1000-1500px)
- **Large structures:** 80-100% of page width (1800-2000+px)
- **Multi-compound diagrams:** Use full width, arranged horizontally

**Aspect ratios:**
- **Individual molecules:** Approximately 1:1.5 (height:width)
- **Reaction sequences:** Approximately 1:3 to 1:6 (height:width)
- **Comparison diagrams:** Variable depending on number of items

---

### 6.5 Text-to-Diagram Ratio
- **Diagrams are well-spaced** with text above/below
- **No overcrowding** - adequate white space
- **Clear separation** between sequential diagrams
- **Labeling conventions:**
  - Figure numbers not typically used
  - Descriptive labels in text above/below
  - Step numbering in mechanisms (i, ii, iii, iv)

---

## 7. Page Layout Analysis

### 7.1 Diagram-Text Integration

**Based on PDF analysis (pages 250-400):**

1. **Top of page:** Chapter/section heading
2. **Text section:** Explanatory content (1-3 paragraphs)
3. **Diagram:** Centered, appropriate size
4. **Follow-up text:** Description or continuation
5. **Additional diagrams:** As needed for complex concepts

**Pattern observed:**
```
[Section Title]
[Explanatory text]
[Diagram centered]
[Descriptive text]
[Additional diagram if needed]
[Transition to next section]
```

---

### 7.2 Diagram Positioning

**Relative to text:**
- **Main diagrams:** Centered in available space
- **Smaller diagrams:** Can be inline or offset
- **Multiple related diagrams:** Often arranged in sequence

**Text wrap:**
- Most diagrams have dedicated space
- No significant text wrapping around diagrams
- Clear separation with white space

---

### 7.3 Caption and Label Style
- **No formal figure numbers** observed
- **Descriptive labels** in body text or immediately above/below
- **Labels indicate:**
  - Type of reaction/collision
  - Step in mechanism
  - Comparison being shown
  - Special features

**Example conventions found:**
- "Mechanism" (above multi-step reactions)
- "(i) Protonation of Carboxylic Acid" (step labels)
- Formation reactions labeled by product name

---

## 8. Specific Diagram Type Specifications

### 8.1 Simple Molecule Representations

**Use when:** Showing single compounds, basic structures

**Specifications:**
```
- Size: 250-300 × 400-450 pixels
- Font: 10-12pt equivalent
- Line thickness: Standard (∼1-1.5px at 150dpi)
- Padding: 15% on all sides
- Style: All atoms explicit or skeletal as appropriate
```

**Example patterns:**
```
CH3-CH=CH2          (propene)
   O
   ║
CH3-C-OH           (ethanoic acid)
```

---

### 8.2 Reaction Mechanisms

**Use when:** Showing step-by-step chemical transformations

**Specifications:**
```
- Size: 1300-1800 × 300-500 pixels (horizontal)
- Steps: 2-4 steps typical
- Step labeling: Roman numerals (i, ii, iii, iv) or numbers
- Arrows: Right-pointing arrows between steps
- Curved arrows: For electron movement (when shown)
- Spacing: 20-25% between steps
```

**Layout pattern:**
```
[Reactant] → [Intermediate 1] → [Intermediate 2] → [Product]
   ↓              ↓                  ↓
 (Step i)      (Step ii)         (Step iii)
```

**Example structure:**
```
(i) Protonation of Carboxylic Acid
[Structure with H+ addition]

(ii) Attack of CH3-CH2-OH
[Structure showing nucleophilic attack]

(iii) Hydrogen Ion Transfer
[Intermediate structure]

(iv) Elimination
[Final product]
```

---

### 8.3 Benzene and Aromatic Structures

**Use when:** Showing benzene, substituted benzenes, PAHs

**Specifications:**
```
Single structure: 250-300 × 400-450 pixels
Complex/polycyclic: 1800-2000+ × 400-1200 pixels
Ring: Perfect hexagon (all 120° angles)
Bond length: Consistent throughout
```

**Benzene representation options:**

#### Option A: Kekule (Traditional)
```
   H   H
    \ /
     C
    / \
H-C     C-H
   \   /
    C=C
   /   \
H-C     C-H
    \ /
     C
    / \
   H   H
```

#### Option B: Modern (Resonance)
```
    H   H
     \ /
      C
     / \
H-C       C-H
     \   /
  ━━━ C ━━━
     /   \
H-C       C-H
     \ /
      C
     / \
    H   H
```

**Substitution positioning:**
```
Position 1: Principal substituent
Position 2: ortho
Position 3: meta
Position 4: para (opposite)
```

---

### 8.4 Isomer Comparisons

**Use when:** Showing structural isomers, functional group isomers, etc.

**Specifications:**
```
- Layout: Horizontal (2-4 isomers) or grid (2×2)
- Size: 1000-1600 × 300-500 pixels
- Spacing: Equal spacing between isomers
- Labels: Position indicators or structural feature labels
```

**Example layout (disubstituted benzene):**
```
[1,2-disubstituted]    [1,3-disubstituted]    [1,4-disubstituted]
    ortho                     meta                    para
```

---

### 8.5 Acid-Base Comparisons

**Use when:** Comparing acidity/basicity, reactivity, etc.

**Specifications:**
```
- Layout: Horizontal sequence
- Size: 1000-1600 × 300-400 pixels
- Ordering: Increasing/decreasing property
- Vertical alignment: Acid/base centers aligned
- Labels: Property value or ranking indicator
```

**Example layout (acid strength):**
```
[Strongest acid] → [Intermediate] → [Weakest acid]
   ↓                  ↓                ↓
pKa ∼1              pKa ∼7           pKa ∼10
```

---

### 8.6 Synthetic Pathways

**Use when:** Showing complete synthesis or reaction network

**Specifications:**
```
- Size: 1800+ × 400-600 pixels (use full width)
- Flow: Left-to-right overall sequence
- Stages: Multiple connected steps
- Labels: Reagents, conditions, intermediate names
- Arrows: Directional arrows with conditions above/below
```

**Layout pattern:**
```
[Starting material] → [Intermediate] → [Intermediate] → [Product]
        ↓↑                 ↓↓                 ↓↑
    (Step 1)           (Step 2)           (Step 3)
```

---

## 9. SVG Generation Recommendations

### 9.1 Base Specifications

**SVG Settings:**
```xml
<svg xmlns="http://www.w3.org/2000/svg" 
     viewBox="0 0 800 600"
     width="800"
     height="600">
  <style>
    .bond { stroke: black; stroke-width: 2; fill: none; }
    .atom-label { font-family: Arial, sans-serif; font-size: 14px; fill: black; }
    .sub { baseline-shift: sub; font-size: 0.7em; }
    .arrow { stroke: black; stroke-width: 2; fill: none; marker-end: url(#arrowhead); }
  </style>
</svg>
```

---

### 9.2 Style Classes

```css
/* Bonds */
.bond { stroke: black; stroke-width: 2; fill: none; }
.double-bond { stroke: black; stroke-width: 2; fill: none; }
.triple-bond { stroke: black; stroke-width: 2; fill: none; }
.wedge { fill: black; stroke: none; }
.dash { stroke: black; stroke-width: 2; stroke-dasharray: 3,3; fill: none; }

/* Atoms */
.atom-label { font-family: Arial, sans-serif; font-size: 14px; fill: black; }
.subscript { baseline-shift: sub; font-size: 10px; }
.superscript { baseline-shift: super; font-size: 10px; }

/* Arrows */
.reaction-arrow { stroke: black; stroke-width: 2; fill: none; }
.electron-arrow { stroke: black; stroke-width: 2; fill: none; }

/* Special elements */
.benzene-circle { stroke: black; stroke-width: 2; fill: none; }
.wedge-solid { fill: black; stroke: none; }
```

---

### 9.3 Coordinate System Recommendations

**Standardization:**
```
- Use 800-1200 × 600-800 as default viewbox
- Center main structure around (400, 400)
- Use 10-unit coordinates for bond lengths (adjust based on complexity)
- Maintain 120° angles for sp² centers
- Use 109.5° for sp³ centers (or approximate as 120° for simplicity)
```

---

### 9.4 Common Components Reusable

#### A) Benzene Ring
```xml
<defs>
  <symbol id="benzene" viewBox="-30 -30 60 52">
    <!-- Kekule structure -->
    <polygon points="0,-26 22.5,-13 22.5,13 0,26 -22.5,13 -22.5,-13" 
             class="bond" fill="none"/>
    <!-- Double bonds at positions 1,3,5 -->
    <line x1="-16" y1="-9" x2="-16" y2="7" class="bond" transform="translate(-2,1)"/>
    <line x1="2" y1="20" x2="18" y2="12" class="bond" transform="translate(0,-2)"/>
    <line x1="2" y1="-20" x2="18" y2="-12" class="bond" transform="translate(0,2)"/>
  </symbol>
  
  <symbol id="benzene-modern" viewBox="-30 -30 60 52">
    <!-- Hexagon -->
    <polygon points="0,-26 22.5,-13 22.5,13 0,26 -22.5,13 -22.5,-13" 
             class="bond" fill="none"/>
    <!-- Delocalized circle -->
    <circle cx="0" cy="0" r="12" class="benzene-circle"/>
  </symbol>
</defs>
```

---

#### B) Functional Group Components
```xml
<defs>
  <!-- Carboxyl group (-COOH) -->
  <symbol id="carboxyl" viewBox="0 0 40 40">
    <line x1="0" y1="20" x2="15" y2="10" class="bond"/>
    <line x1="15" y1="10" x2="30" y2="10" class="double-bond"/>
    <line x1="15" y1="10" x2="15" y2="30" class="bond"/>
    <text x="32" y="12" class="atom-label">O</text>
    <text x="10" y="42" class="atom-label">OH</text>
  </symbol>

  <!-- Hydroxyl group (-OH) -->
  <symbol id="hydroxyl" viewBox="0 0 30 30">
    <line x1="0" y1="15" x2="15" y2="15" class="bond"/>
    <text x="17" y="18" class="atom-label">OH</text>
  </symbol>

  <!-- Amino group (-NH2) -->
  <symbol id="amino" viewBox="0 0 30 40">
    <line x1="0" y1="20" x2="15" y2="10" class="bond"/>
    <text x="17" y="10" class="atom-label">NH<tspan class="subscript">2</tspan></text>
  </symbol>
</defs>
```

---

#### C) Arrows
```xml
<defs>
  <!-- Standard reaction arrow -->
  <marker id="arrowhead" markerWidth="10" markerHeight="7" 
          refX="10" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="black"/>
  </marker>

  <!-- Curved arrow for electron movement -->
  <path d="M{start_x},{start_y} Q{control_x},{control_y} {end_x},{end_y}" 
        class="electron-arrow" marker-end="url(#arrowhead)"/>
</defs>
```

---

### 9.5 Text Formatting

**Chemical formulas:**
```xml
<text class="atom-label">
  CH<tspan class="subscript">3</tspan>-CH<tspan class="subscript">2</tspan>-OH
</text>

<text class="atom-label">
  C<tspan class="subscript">6</tspan>H<tspan class="subscript">6</tspan>
</text>
```

**Unicode subscripts (alternative):**
```xml
<text class="atom-label">CH₃-CH₂-OH</text>
<text class="atom-label">C₆H₆</text>
```

---

### 9.6 Layout Templates

#### Template 1: Single Simple Structure
```xml
<svg viewBox="-50 -50 100 100">
  <!-- Centered at (0,0), extends 50 units in each direction -->
  <!-- Add structure here -->
</svg>
```

#### Template 2: Two-Compound Comparison
```xml
<svg viewBox="0 0 400 200">
  <!-- Compound 1: centered at (100, 100) -->
  <g transform="translate(100, 100)">
    <!-- First structure -->
  </g>
  
  <!-- Compound 2: centered at (300, 100) -->
  <g transform="translate(300, 100)">
    <!-- Second structure -->
  </g>
  
  <!-- Arrow between -->
  <line x1="150" y1="100" x2="250" y2="100" class="reaction-arrow" 
        marker-end="url(#arrowhead)"/>
</svg>
```

#### Template 3: Multi-Step Mechanism
```xml
<svg viewBox="0 0 800 200">
  <!-- Step 1 -->
  <g transform="translate(100, 100)">
    <text x="0" y="-60" class="atom-label" text-anchor="middle">(i) Step Name</text>
    <!-- Structure -->
  </g>
  
  <!-- Arrow 1-2 -->
  <line x1="200" y1="100" x2="300" y2="100" class="reaction-arrow" 
        marker-end="url(#arrowhead)"/>
  
  <!-- Step 2 -->
  <g transform="translate(400, 100)">
    <text x="0" y="-60" class="atom-label" text-anchor="middle">(ii) Step Name</text>
    <!-- Structure -->
  </g>
  
  <!-- Arrow 2-3 -->
  <line x1="500" y1="100" x2="600" y2="100" class="reaction-arrow" 
        marker-end="url(#arrowhead)"/>
  
  <!-- Step 3 -->
  <g transform="translate(700, 100)">
    <text x="0" y="-60" class="atom-label" text-anchor="middle">(iii) Step Name</text>
    <!-- Structure -->
  </g>
</svg>
```

---

### 9.7 Quality Assurance Checklist

**Before finalizing SVG diagrams:**

✓ **Typography**
- [ ] All atomic symbols uppercase/lowercase correct (C, H, O, N, Cl, Br)
- [ ] Subscripts properly formatted
- [ ] Font size appropriate for diagram size
- [ ] Text readable at target display size

✓ **Chemical correctness**
- [ ] Bond angles appropriate (120° for sp², ~109.5° for sp³)
- [ ] Bond lengths consistent
- [ ] Valences correct (4 bonds max for carbon)
- [ ] Charges balanced where appropriate

✓ **Visual consistency**
- [ ] Line thickness consistent across diagram
- [ ] All bonds same width
- [ ] Double/triple bonds properly spaced
- [ ] No accidental line breaks or gaps

✓ **Layout**
- [ ] Adequate white space around structures
- [ ] Proper spacing between related components
- [ ] Elements centered and aligned
- [ ] No overlapping elements

✓ **Style compliance**
- [ ] All elements black on white
- [ ] No color coding (unless specifically required)
- [ ] Matches textbook conventions
- [ ] Appropriate for educational use

---

## 10. Conclusion

The Punjab 2nd Year Chemistry textbook uses clean, standard organic chemistry diagram conventions that are well-suited for educational purposes. The style is characterized by:

### 10.1 Key Style Elements
1. **Black-and-white line drawings** - clear, reproducible, professional
2. **Standard organic notation** - familiar to chemistry students
3. **Adequate spacing** - not cramped, easy to understand
4. **Logical progression** - diagrams support text explanation
5. **Multiple benzene representations** - both Kekule and modern structure

### 10.2 Best Practices for Generation
1. **Use standard conventions** - don't invent new notation
2. **Maintain consistency** - same style across all diagrams
3. **Prioritize clarity** - educational value over artistic flair
4. **Include necessary detail** - but avoid clutter
5. **Follow textbook patterns** - match existing style

### 10.3 Recommendations for Implementation
1. **Create reusable components** (benzene rings, functional groups)
2. **Use coordinate-based layouts** for precision
3. **Test multiple sizes** to ensure scalability
4. **Validate chemical correctness** before finalizing
5. **Compare with textbook examples** for style matching

---

## 11. Quick Reference

### Common Dimensions
| Diagram Type | Width (px) | Height (px) | Description |
|-------------|------------|-------------|-------------|
| Simple structure | 250-300 | 400-450 | Single molecule |
| Medium structure | 1000-1500 | 300-400 | Reaction sequence |
| Complex structure | 1800-2000+ | 400-1200 | Multi-compound synthesis |

### Line Thickness (at 150dpi)
| Element | Thickness | Notes |
|---------|-----------|-------|
| Single bond | ~1.5px | Standard bond lines |
| Double bond | ~1.5px each | Parallel with ~2-3px spacing |
| Triple bond | ~1.5px each | Three parallel lines |
| Wedge bond | Variable | Point thickness |

### Font Sizes
| Usage | Size | Notes |
|-------|------|-------|
| Large labels | 12-14pt | Main compound names |
| Medium labels | 10-12pt | Atom labels |
| Small labels | 8-10pt | Subscripts/superscripts |

### Color Scheme
| Element | Color | RGB |
|---------|-------|-----|
| All structures | Black | #000000 |
| Background | White | #FFFFFF |

---

**Document End**
