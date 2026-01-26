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

## 3. Material Processing (Semantic Density Chunking)

**Goal:** Split material by cognitive load, not just structure.

**Algorithm (Sliding Window):**
```python
def chunk_by_cognitive_load(document, max_load=50):
    chunks = []
    current_chunk = []
    current_load = 0

    for paragraph in document.paragraphs:
        para_load = calculate_load(paragraph)
        # Load factors:
        # - New terminology count (+5 per new term)
        # - Formula/code presence (+10)
        # - Abstract concepts (+8)
        # - Flesch-Kincaid difficulty (+scaled)

        if current_load + para_load > max_load:
            chunks.append(current_chunk)
            current_chunk = [paragraph]
            current_load = para_load
        else:
            current_chunk.append(paragraph)
            current_load += para_load

    chunks.append(current_chunk)  # Don't forget last chunk
    return chunks
```

**Output:**
```json
{
  "chunk_id": "C003",
  "content": "...",
  "semantic_density": 45,
  "new_terms": ["recursion", "base_case"],
  "page_range": "Slide 5-6"
}
```

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
       -> cognitive_load += chunk.semantic_density * 0.2
END FOR
```

### 4.2 Multi-Run Aggregation
```
FOR each run (1 to N):
    - Randomly sample subset of students from class
    - Execute Single Run Flow
    - Store all outputs
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

        overlay_on_original(material_file, chunk.page_range, color)

        if annotation:
            # Feasibility: Adding text to bottom of existing PDF/PPT slide
            # is standard. Can use reportlab to draw a white box + text
            # at bottom coordinates (x=50, y=50).
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
