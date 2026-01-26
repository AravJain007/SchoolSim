# Sims Teacher - Project Overview

## Core Idea

A smart classroom simulation system where LLMs imitate teachers, students, and a principal. Real teachers input their course material. The system simulates teaching sessions with personality-driven agents (both teacher and students) who interact realistically. A principal agent observes and provides pedagogical feedback.

---

## Two Main Modules

### Module 1: Classroom Simulation (For Teacher Benefit)

**Goal:** Help teachers identify weak spots in their course material before actual teaching.

**Flow:**
1. Teacher takes Big5 personality test (same as students) to create teacher agent personality
2. Teacher uploads course material (PDF, PPT, DOC, notes)
3. Teacher selects class name (to fetch student data from database) and number of simulation runs
4. System creates a simulated teacher agent with the real teacher's personality
5. System creates student agents from the class, each with unique Big5 personalities and backgrounds
6. Simulated teacher teaches → pauses for doubts → students (based on personality) decide whether to ask doubts and what to ask
7. Principal agent observes the entire session and takes notes
8. Multiple simulation runs happen with completely random student selection each time
9. An aggregator analyzes common patterns across all runs
10. Output: Suggestions to improve material, predicted common doubts, focus areas


---

## Input, Processing, Output

### Classroom Simulation

| Stage | Details |
|-------|---------|
| **Input** | Teacher personality (Big5), course material (PDF/PPT/DOC), class name (to retrieve students), number of simulation runs |
| **Processing** | 1. Parse course material using **Semantic Density Chunking** (splits by cognitive load, not just paragraphs)<br>2. Generate teacher agent prompt using teacher's Big5 personality<br>3. Fetch student personalities from database using class name<br>4. **Initialize student CIE states** (fatigue=0, cognitive_load=0, understanding=3)<br>5. Run teach-doubt cycles: teacher explains chunk → **all students rate understanding (1-5)** → students with score ≤2 and fatigue <80 may ask doubts<br>6. Teacher answers doubt → **check if asker's understanding improved (IRF R+ metric)**<br>7. **Principal checks KLI alignment** per chunk (Knowledge structure, Learning process, Instruction match)<br>8. **Update CIE states** after each chunk (fatigue += 5)<br>9. Aggregator combines findings from all runs, detects **systemic gaps** (40%+ failure rate) |
| **Output** | **Heatmap** (PDF/PPT with Red/Orange/Green overlays + footer remarks), Gap Report, Principal's KLI summary, common doubts |


---

## Novelty of the Work

1. **Personality-Driven Multi-Agent Simulation:** Both teacher and students have Big5 personality profiles. Teacher agent mirrors real teacher's teaching style. Student agents have personalities and biographies from resumes. This makes interactions realistic - introverts ask fewer doubts, curious students ask deeper questions, strict teachers explain differently than friendly ones.

2. **Pre-Teaching Material Validation:** Teachers can test their material on a simulated classroom before facing real students. This is predictive pedagogy.

3. **CIE Architecture (Cognition-Interaction-Evolution):** Students have evolving cognitive states (fatigue, cognitive load, understanding) that change during the session. A tired student stops asking questions even if confused. This models real classroom dynamics.

4. **Expanded Scale Format (1-5):** Every student rates their understanding after every chunk (1=lost, 5=clear). This prevents "acquiescence bias" where LLMs politely claim understanding.

5. **KLI Framework Principal:** The Principal agent checks alignment between Knowledge structure (prerequisites), Learning processes (exposure vs. practice), and Instruction methods (lecture vs. demo). Identifies mismatches like "You used a lecture for a coding exercise."

6. **IRF R+ Metrics:** Measures teaching effectiveness by checking if a student's understanding improved after teacher's response to a doubt. Flags segments where explanations don't resolve confusion.

7. **Semantic Density Chunking:** Material is split by cognitive load (new terms, formulas, abstraction level) rather than just paragraphs. Prevents overwhelming students with dense sections.

8. **Heatmap Visualization with Remarks:** Outputs the original PDF/PPT with color overlays (Red=critical, Orange=caution, Green=clear) AND footer annotations showing the specific issue and improvement suggestion.

9. **Aggregation Across Multiple Runs:** Teacher chooses number of runs. Each run has completely random student selection. Aggregating findings across runs produces statistically meaningful insights. Gaps flagged only if 40%+ of runs show failure.


10. **Closed Feedback Loop:** Simulation insights → material improvement → better teaching → further refinement. The system creates a continuous improvement cycle.

---

## Technical Novelty

- Uses Big5 psychological model for both teacher and students
- Professional biography extraction from resumes to create realistic student personas
- Teacher personality influences teaching style, explanation depth, and doubt handling
- **CIE cognitive state variables** (fatigue, cognitive_load, understanding) with deterministic update rules
- **Expanded Scale (1-5)** for every student after every chunk to prevent acquiescence bias
- Character impersonation prompts that maintain behavioral consistency
- Multi-agent orchestration (teacher, students, principal) with role-specific system prompts
- **Doubt selection based on understanding score + fatigue threshold**, not just personality
- **KLI Framework** for Principal agent (Knowledge-Learning-Instruction alignment checking)
- **IRF R+ metric** to measure if doubts were actually resolved
- **Semantic Density Chunking** algorithm (cognitive load-based material segmentation)
- Pedagogical analysis using established frameworks (Bloom's Taxonomy, Flesch-Kincaid)
- **Heatmap generation with footer annotations** on original course materials
- Randomized multi-run simulations with configurable run count

---

## What's Already Built

- Big5 personality assessment website (works for both students and teachers)
- LLM provider abstraction (Gemini, Lightning, LMStudio)
- Student personality prompt generation (Big5 + resume → character prompt)
- MongoDB storage for personalities and results
- Basic doubt-asking simulation utility

## What Remains

- Teacher personality prompt generation (using existing Big5 infrastructure)
- Teacher agent implementation
- **Student agent with CIE cognitive state management**
- **Principal agent with KLI Framework prompts**
- **Semantic Density Chunker** for course material parsing
- Simulation setup screen (class selection, run count)
- Full simulation orchestration with **1-5 scale collection** and **CIE state updates**
- **IRF R+ metric calculation** in aggregator
- **Gap Detection** (40% threshold) in aggregator
- **Heatmap Generator + Annotation Writer** for output

- Frontend: simulation chat interface

- Frontend: teacher dashboard with analysis + heatmap viewer
