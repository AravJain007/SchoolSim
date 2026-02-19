# SIMS Teacher - Final Plan (Agent/Technical Specification)

**Last Updated:** January 26, 2026

---

## 1. Project Overview

**One-Line Pitch:** A multi-agent classroom simulation that stress-tests course materials before the real class.

**Problem:** Teachers don't know where students will struggle until the class is over.

**Solution:** Run the class in a simulation with AI students and a silent Principal observer. Output a heatmap of confusion zones and actionable suggestions.

---

## 2. Agent Specifications

### 2.1 Teacher Agent

**Inputs:**
- Big Five personality scores (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- Course material (chunked)

**Behavior Mapping:**
| Trait | Low Score Behavior | High Score Behavior |
|-------|-------------------|---------------------|
| Openness | Sticks to textbook examples | Uses creative analogies |
| Conscientiousness | Summarizes quickly | Covers every detail |
| Extraversion | Minimal interaction, lecture-heavy | Asks class questions frequently |
| Agreeableness | Dismisses "silly" questions | Patiently re-explains |
| Neuroticism | Calm under repeated questions | Gets flustered if doubts persist |

**Output per Chunk:**
```json
{
  "chunk_id": "C003",
  "teaching_transcript": "...",
  "teaching_method_used": "direct_explanation | analogy | example | question"
}
```

---

### 2.2 Student Agent

**Inputs:**
- Big Five personality scores
- Biography (generated from resume)
- Current cognitive state (Fatigue, Cognitive Load)

**Cognitive State Variables (CIE Architecture):**
```python
cognitive_state = {
    "fatigue": 0,           # Increases by +5 after each chunk
    "cognitive_load": 0,    # Increases based on chunk difficulty
    "understanding": 3      # 1-5 scale, updated after each chunk
}
```

**State Update Rules:**
- After each chunk: `fatigue += 5`
- After difficult chunk (semantic density > threshold): `cognitive_load += 10`
- After teacher explanation: LLM outputs new `understanding` score (1-5)

**Behavior Logic:**
```python
def should_ask_doubt(student):
    if student.cognitive_state["understanding"] <= 2:
        if student.cognitive_state["fatigue"] < 80:
            return True  # Confused and not too tired -> ask
        else:
            return False  # Too tired to engage
    elif student.cognitive_state["understanding"] == 5:
        if student.big5["openness"] > 70:
            return maybe_curiosity_question()  # Smart question
    return False
```

**Output per Chunk:**
```json
{
  "student_id": "S007",
  "chunk_id": "C003",
  "understanding_before": 2,
  "understanding_after": 4,
  "doubt_asked": "What happens if the base case is never reached?",
  "doubt_resolved": true
}
```

---

### 2.3 Principal Agent

**Inputs:**
- Full transcript of Teacher-Student interaction per chunk
- Knowledge structure of the material (extracted during chunking)

**KLI Framework Analysis:**

| Layer | What Principal Checks |
|-------|----------------------|
| **Knowledge (K)** | Are prerequisites covered before advanced topics? |
| **Learning (L)** | Is the learning phase appropriate? (Exposure → Practice → Application) |
| **Instruction (I)** | Does the teaching method match the content type? |

**Alignment Check Example:**
```
Content Type: Coding Exercise (requires Practice)
Teaching Method Used: Direct Explanation (Lecture)
Alignment Score: 0.3 (LOW)
Principal Note: "Consider adding a live coding demo or practice problem."
```

**Output per Chunk:**
```json
{
  "chunk_id": "C003",
  "alignment_score": 0.3,
  "missing_prerequisites": ["stack_memory"],
  "suggested_methods": ["live_coding", "worked_example"],
  "notes": "Explanation assumes students know call stack. Add visual diagram."
}
```

---

## 3. Material Processing (Structural Chunking)

**Goal:** Split material by structure for easy annotation mapping. Semantic density will be discovered empirically through simulation.

**Chunking Logic:**
- **For PPTs:** 1 slide = 1 chunk
- **For PDFs/DOCs:** 1 page or 1 paragraph = 1 chunk

**Rationale:** This structural approach ensures that when we identify difficult parts where students had doubts, we can easily map those remarks back to specific slides or pages for annotation. The simulation will empirically discover difficulty through student understanding scores, rather than pre-computing semantic density via NLP.

**Algorithm:**
```python
def parse_document(file_path: str) -> List[ChunkDetails]:
    # For PPTs: Extract each slide as a separate chunk
    # For PDFs: Extract each page as a separate chunk
    # For DOCs: Extract each paragraph as a separate chunk

    chunks = []
    for idx, content_unit in enumerate(document_units, start=1):
        chunk = ChunkDetails(
            chunk_id=f"chunk_{idx}",
            content=content_unit,
            page_range=f"Slide {idx}" if is_ppt else (f"Paragraph {idx}" if is_doc else f"Page {idx}"),
            difficulty_index=0.0,  # Placeholder - populated post-simulation
            has_formula=detect_formulas(content_unit),
            has_code=detect_code(content_unit)
        )
        chunks.append(chunk)
    return chunks
```

**Output:**
```json
{
  "chunk_id": "chunk_3",
  "content": "...",
  "difficulty_index": 0.0,
  "page_range": "Slide 3",
  "has_formula": true,
  "has_code": false
}
```

**Note:** The `difficulty_index` field in chunk output will be populated **after simulation** based on student understanding scores, not pre-computed via NLP. This allows the simulation to empirically discover which chunks are difficult rather than making assumptions upfront.

---

## 4. Simulation Loop

### 4.1 Single Run Flow
```
FOR each chunk in material:
    1. Teacher Agent teaches chunk
       -> Output: teaching_transcript, method_used

    2. ALL Student Agents rate understanding (1-5)
       -> Output: understanding_score per student

    3. SELECT students with understanding <= 2
       -> Filter by fatigue < 80
       -> Randomly pick 1-2 to ask doubts

    4. Teacher Agent responds to doubt
       -> Output: response_transcript

    5. Asker re-rates understanding (IRF Check)
       -> IF understanding_after > understanding_before: R+ = 1
       -> ELSE: R+ = 0

    6. Principal Agent analyzes chunk
       -> Output: alignment_score, notes

    7. UPDATE all student cognitive states
       -> fatigue += 5
       -> cognitive_load += chunk.difficulty_index * 0.2
END FOR
```

### 4.2 Multi-Run Aggregation

**Random Student Subset Selection:**

Each run uses a randomly selected subset of students (NOT the full class). This ensures statistical variance and exposes different failure modes across runs.

```python
# Subset Selection Rules:
# - Sample between 50-100% of class size per run
# - Minimum 5 students regardless of class size

def calculate_sample_range(total_students: int) -> tuple[int, int]:
    min_sample = max(5, int(total_students * 0.5))
    max_sample = total_students
    return (min_sample, max_sample)

# Example: Class of 100 students → sample 50-100 students per run
# Example: Class of 20 students  → sample 10-20 students per run
```

**Multi-Run Loop:**
```
FOR each run (1 to N):
    1. Calculate sample range: (min, max) = calculate_sample_range(class_size)
    2. Pick random sample_size between min and max
    3. Randomly select sample_size students from class
    4. Execute Single Run Flow with selected students
    5. Record students_selected in SimulationRun output
    6. Store all outputs
END FOR

AGGREGATE:
    - Per chunk: average understanding, total doubts, common doubt themes
    - Gap Detection: IF avg_understanding < 3 for 40%+ runs -> FLAG as Gap
    - Per chunk: average R+ score (teaching effectiveness)
    - Per chunk: average alignment score from Principal
```

---

## 5. Output Generation

### 5.1 Heatmap Visualization

**Annotation Granularity by File Type:**
- **PDF**: Full-page color overlay (1 page = 1 chunk)
- **PPT/PPTX**: Full-slide color overlay (1 slide = 1 chunk)
- **DOC/DOCX**: Paragraph-level text highlighting (1 paragraph = 1 chunk) — *finer granularity*

```python
def generate_heatmap(material_file, aggregation_results):
    for chunk in aggregation_results:
        if chunk.avg_understanding < 2:
            color = RED      # Critical confusion
            annotation = f"⚠️ GAP: {chunk.failure_rate*100}% failed. Note: {chunk.principal_notes}"
        elif chunk.avg_understanding < 3:
            color = ORANGE   # Caution
            annotation = f"⚠️ Warning: {chunk.principal_notes}"
        else:
            color = GREEN    # Clear
            annotation = None

        # page_range may be "Page 5", "Slide 3", or "Paragraph 7"
        overlay_on_original(material_file, chunk.page_range, color)

        if annotation:
            # PDF/PPT: Footer text box at bottom
            # DOCX: Word comment anchored to paragraph
            add_footer_note(material_file, chunk.page_range, annotation)

    return annotated_material
```

### 5.2 Gap Report
```json
{
  "gaps": [
    {
      "chunk_id": "C005",
      "topic": "Recursive Case Explanation",
      "avg_understanding": 2.1,
      "failure_rate": 0.45,
      "common_doubts": ["What triggers the recursive call?", "How does the stack unwind?"],
      "principal_notes": "Missing visual diagram of call stack."
    }
  ]
}
```

### 5.3 Principal Summary
```json
{
  "overall_alignment": 0.72,
  "critical_misalignments": [
    {
      "chunk_id": "C005",
      "issue": "Used lecture for practice-required content",
      "suggestion": "Add live coding demonstration"
    }
  ],
  "missing_prerequisites": ["stack_memory", "function_scope"],
  "bloom_progression": "Covers Remember/Understand, missing Apply/Analyze"
}
```

---

## 6. Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React |
| Backend | Python + FastAPI |
| LLM | Gemini / Lightning / LMStudio |
| Document Parsing | PyMuPDF, python-pptx, python-docx |
| Heatmap Generation | ReportLab / PyMuPDF overlay |
| Deployment | Docker |

---

## 7. Future Work (Out of Scope for MVP)

- **Mirror Teacher Cloning:** Fine-tune LLM on real teacher transcripts to copy exact linguistic patterns.
- **Stress-Testing Mode:** Inject adversarial conditions (distracted students, time pressure) to find material breaking points.
- **Full Class Comprehension Check:** After every doubt, poll ALL students for understanding (token-expensive).
