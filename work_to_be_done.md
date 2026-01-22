# Sims Teacher - Project Overview

## Core Idea

A smart classroom simulation system where LLMs imitate teachers, students, and a principal. Real teachers input their course material. The system simulates teaching sessions with personality-driven agents (both teacher and students) who interact realistically. A principal agent observes and provides pedagogical feedback. Additionally, a unified quiz is generated for all students based on the syllabus to assess understanding.

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

### Module 2: Quiz System (For Student Assessment)

**Goal:** Create a holistic test to assess student understanding based on syllabus.

**Flow:**
1. Teacher inputs the day's teaching material/syllabus
2. System generates one unified quiz that tests all key concepts from the syllabus
3. All students of the class attempt the same quiz via a web interface
4. System provides individual analysis per student
5. System provides aggregate analysis to the teacher
6. Teacher identifies weak areas and adjusts future teaching

---

## Input, Processing, Output

### Classroom Simulation

| Stage | Details |
|-------|---------|
| **Input** | Teacher personality (Big5), course material (PDF/PPT/DOC), class name (to retrieve students), number of simulation runs |
| **Processing** | 1. Parse course material into teachable chunks<br>2. Generate teacher agent prompt using teacher's Big5 personality<br>3. Fetch student personalities from database using class name<br>4. Run teach-doubt cycles with random student selection per run<br>5. Students decide to ask doubts based on personality<br>6. Principal observes and notes issues<br>7. Aggregator combines findings from all runs |
| **Output** | List of common doubts, material improvement suggestions, areas needing more focus, areas that can be shortened |

### Quiz System

| Stage | Details |
|-------|---------|
| **Input** | Day's teaching material/syllabus |
| **Processing** | 1. Parse material into key concepts<br>2. Generate unified quiz covering all concepts holistically<br>3. All students attempt same quiz<br>4. Analyze individual and aggregate performance |
| **Output** | Per-student analysis (strengths, weaknesses), class-wide analysis (common misconceptions, topics to revisit) |

---

## Novelty of the Work

1. **Personality-Driven Multi-Agent Simulation:** Both teacher and students have Big5 personality profiles. Teacher agent mirrors real teacher's teaching style. Student agents have personalities and biographies from resumes. This makes interactions realistic - introverts ask fewer doubts, curious students ask deeper questions, strict teachers explain differently than friendly ones.

2. **Pre-Teaching Material Validation:** Teachers can test their material on a simulated classroom before facing real students. This is predictive pedagogy.

3. **Principal as Pedagogical Observer:** An LLM agent specifically trained on teaching methodologies observes the simulation and provides research-backed suggestions.

4. **Aggregation Across Multiple Runs:** Teacher chooses number of runs. Each run has completely random student selection. Aggregating findings across runs produces statistically meaningful insights.

5. **Holistic Syllabus-Based Assessment:** Quizzes are generated from syllabus to comprehensively test all key concepts. Same quiz for all students enables fair comparison and identification of class-wide weak spots.

6. **Closed Feedback Loop:** Simulation insights → material improvement → better teaching → quiz feedback → further refinement. The system creates a continuous improvement cycle.

7. **Dual Benefit System:** Teachers benefit from simulation (before teaching) AND from quiz analysis (after teaching). Students benefit from targeted teaching based on identified weak areas.

---

## Technical Novelty

- Uses Big5 psychological model for both teacher and students
- Professional biography extraction from resumes to create realistic student personas
- Teacher personality influences teaching style, explanation depth, and doubt handling
- Character impersonation prompts that maintain behavioral consistency
- Multi-agent orchestration (teacher, students, principal) with role-specific system prompts
- Probabilistic doubt-asking based on personality traits (not random)
- Pedagogical analysis using established frameworks (Bloom's Taxonomy, Flesch-Kincaid)
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
- Principal agent implementation
- Course material parser
- Simulation setup screen (class selection, run count)
- Full simulation orchestration with multi-run support
- Aggregator for multi-run analysis
- Quiz generation system (unified quiz from syllabus)
- Frontend: simulation chat interface
- Frontend: quiz interface for students
- Frontend: teacher dashboard with analysis
