# SIMS Teacher

Teachers can use this to test their materials for the class they are about to teach. All students aren't equal and all teachers are not experienced with the new generation. This simulation runs with the course material (PDF, PPT, Word docs, etc.) that the teacher will use. It helps teachers understand how students will learn and where they might struggle.

### Characters

1. **Teacher:**
   The teacher agent has a personality (from Big5 test taken by the real teacher). It teaches the material, pauses for doubts, and explains based on its personality traits. Teaching style, patience, and explanation depth vary based on personality.

2. **Students:**
   Each student has a unique Big5 personality and a biography from their resume. Not every student asks doubts. Some ask basic questions, others ask insightful ones. Behavior is driven by personality traits.

3. **Principal:**
   Observes the entire session silently. Takes notes on teaching effectiveness and student confusion points. Uses pedagogical knowledge to suggest improvements to the course material.

### Flow of the Simulation

1. Teacher takes Big5 personality test (if not already taken).
2. Teacher goes to setup screen:
   - Selects class name (to fetch student data from database)
   - Uploads course material (PDF, PPT, DOC)
   - Specifies number of simulation runs
3. Simulation runs in the background. Each run:
   - Randomly selects students from the class
   - Teacher agent teaches the material
   - Students decide whether to ask doubts based on their personality
   - Teacher answers doubts
   - Principal observes and takes notes
4. Teacher can monitor via a chat interface showing the simulation in real-time.
5. After all runs complete, aggregator analyzes patterns across runs.
6. Final output: common doubts, material improvement suggestions, focus areas.

### Parts of the Project

1. **Frontend (React):**
   - Setup page: class selection, material upload, run count
   - Chat interface: shows simulation in real-time as messages
   - Results page: aggregated findings
   - Quiz interface: for students to take tests
   - Teacher dashboard: analysis of quiz results

2. **Backend (Python):**
   - FastAPI for endpoints
   - LLM providers (Gemini, Lightning, LMStudio)
   - Character prompts for teacher, students, principal
   - Quiz generation from syllabus

3. **Deployment:**
   - Docker

### Metrics that I plan on using:

1. Flesch‑Kincaid Score - For Clarity & Readability
2. Bloom’s Taxonomy - Hierarchy of cognitive skills (Knowledge → Comprehension → Application → Analysis → Synthesis → Evaluation) – useful for “Depth & Breadth” metrics.
3. Pedagogical Soundness - ADDIE could also be taken into consideration if entire course creation is in question.
4.
