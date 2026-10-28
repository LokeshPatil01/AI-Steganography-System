# Project Documentation & Academic Research Package

This directory contains research papers, IEEE LaTeX manuscripts, architecture specifications, security analyses, and academic defense preparation materials for the **AI-Based Adaptive Steganography System with Automated Key Generation and Multi-Objective Pareto Optimization**.

## Academic Publications & Manuscripts
* `RESEARCH_PAPER.md`: Complete, publication-ready research paper draft formatted in Markdown with mathematical formulas, architecture mermaid diagrams, and empirical benchmark tables.
* `research_paper.tex`: Standard **IEEEtran two-column conference/journal LaTeX template**, ready for direct submission or compilation on Overleaf or local LaTeX engines (`pdflatex`).
* `references.bib`: Standard BibTeX bibliography containing citations across steganography, deep learning steganalysis, cryptography, and multi-objective evolutionary computation.

### How to Compile the LaTeX Research Paper
1. **Overleaf (Recommended)**:
   - Create a **New Project** $\to$ **Upload Project**.
   - Upload `research_paper.tex` and `references.bib`.
   - Set Compiler to `pdfLaTeX` and click **Recompile**.
2. **Local TeX Live / MiKTeX**:
   ```bash
   pdflatex research_paper.tex
   bibtex research_paper
   pdflatex research_paper.tex
   pdflatex research_paper.tex
   ```

## Technical Architecture & Viva Materials
* `ARCHITECTURE.md`: High-level and component architecture, data flow diagrams, network boundaries.
* `AI_MODEL.md`: Mathematical formulations, Random Forest training methodology, PyTorch CNN steganalyzer architecture, and feedback loop mechanics.
* `SECURITY.md`: Cryptographic analysis (AES-256-GCM, RSA-4096-OAEP), threat modeling, key storage security, and limitations.
* `EXPERIMENTS.md`: Experimental setups, benchmarks against baseline LSB, dataset distributions, and performance graphs.
* `VIVA_QUESTIONS.md`: Comprehensive defense questions (basic, technical, tricky) with detailed academic answers.

