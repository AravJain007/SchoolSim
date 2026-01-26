# SIMS Teacher - Final Plan (Human-Readable)

**Last Updated:** January 26, 2026

---

## What is SIMS Teacher?

A simulation tool where teachers upload their course material (PDF, PPT, etc.) and watch AI-powered "digital twins" of their students interact with it. The goal: find out where students will get confused *before* the real class happens.

---

## The Three Agents

### 1. Teacher Agent
- Takes the real teacher's Big Five personality test results.
- Teaches the material in a style matching that personality (patient vs. rushed, detailed vs. concise).

### 2. Student Agents
- Each student has a unique personality (Big Five) and a short biography from their resume.
- **After every teaching chunk**, each student rates their understanding from 1-5.
- Students with low scores (1 or 2) are prioritized to ask doubts.
- Students get **tired over time** (Fatigue increases every chunk). Tired students ask fewer/simpler questions.

### 3. Principal Agent
- Silently observes the entire session.
- Checks **alignment**: Is the teaching method right for this type of content? (e.g., "A lecture won't work for a coding exercise").
- Suggests improvements to the material.

---

## How the Simulation Runs

1. **Setup**: Teacher selects class, uploads material, sets number of runs.
2. **Chunking**: Material is split into small pieces based on "mental difficulty" (not just paragraphs).
3. **Teaching Loop** (per chunk):
   - Teacher explains the chunk.
   - All students rate their understanding (1-5).
   - Confused students (score 1-2) may ask a doubt.
   - Teacher answers. We check if the asker's understanding improved.
   - Principal notes any misalignment.
4. **Repeat** for all chunks, then repeat for multiple runs with different student subsets.
5. **Aggregation**: Combine results from all runs. Topics that confuse 40%+ of students are flagged as "Gaps".

---

## The Output

- **Heatmap**: The original PDF/PPT is colored Red/Yellow/Green showing exactly where students struggled.
- **Gap Report**: A list of topics that consistently caused confusion.
- **Principal's Notes**: Suggestions for restructuring content.

---

## What's NOT Included (Future Work)

- Mirror Teacher Cloning (copying exact speech patterns via fine-tuning).
- Stress-Testing (simulating distracted students, time pressure).
