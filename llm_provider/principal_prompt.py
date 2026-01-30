"""
Principal Agent System Prompts for Pedagogical Analysis using KLI Framework

This module implements the KLI (Knowledge-Learning-Instruction) Framework
for evaluating teaching effectiveness in simulated classroom environments.

KLI Framework Reference:
Source: Koedinger, K. R., Corbett, A. T., & Perfetti, C. (2012).
The Knowledge-Learning-Instruction Framework: Bridging the Science-Practice Chasm
to Enhance Robust Student Learning. Cognitive Science, 36(5), 757-798.
https://onlinelibrary.wiley.com/doi/10.1111/j.1551-6709.2012.01245.x

Bloom's Taxonomy Reference:
Source: Anderson, L. W., & Krathwohl, D. R. (Eds.). (2001).
A Taxonomy for Learning, Teaching, and Assessing: A Revision of Bloom's Taxonomy
of Educational Objectives.
https://en.wikipedia.org/wiki/Bloom%27s_taxonomy
"""

# KLI Framework Components
# Based on: https://eric.ed.gov/?id=ED535880
# The framework consists of three coordinated taxonomies:

KLI_FRAMEWORK_EXPLANATION = """
## KLI Framework Components:

### K - KNOWLEDGE Taxonomy
Knowledge types are categorized by functional cognitive characteristics:
- **Declarative Knowledge**: Facts, concepts, definitions (e.g., "What is a variable?")
- **Procedural Knowledge**: Step-by-step processes (e.g., "How to sort an array")
- **Conceptual Knowledge**: Deep understanding of relationships and principles
- **Metacognitive Knowledge**: Awareness of one's own learning strategies

Prerequisites Assessment:
- Does the student have the foundational knowledge needed?
- Are simpler concepts explained before complex ones?
- Is the knowledge structure sound and logically progressive?

### L - LEARNING Events Taxonomy
Three broad classes of learning events (Source: Koedinger et al., 2012):

1. **Memory and Fluency Processes**
   - Goal: Automaticity, retention, quick recall
   - Best for: Basic facts, terminology, simple procedures
   - Indicators: Repetition, practice, retrieval exercises

2. **Induction and Refinement Processes**
   - Goal: Pattern recognition, building schemas through examples
   - Best for: Recognizing when to apply knowledge, refining understanding
   - Indicators: Multiple examples, contrasting cases, practice with feedback

3. **Understanding and Sense-Making Processes**
   - Goal: Deep comprehension through deliberate reasoning
   - Best for: Complex concepts, relationships, problem-solving
   - Indicators: Explanations, analogies, connecting to prior knowledge

Learning Phase Assessment:
- Is the teaching aligned with appropriate learning phase?
- Are students given opportunities for the right type of learning event?

### I - INSTRUCTION Taxonomy
Instructional methods must match knowledge complexity:
- **Direct Explanation**: For declarative knowledge, concepts
- **Worked Examples**: For procedural knowledge, algorithms
- **Analogies/Metaphors**: For conceptual understanding
- **Discovery/Inquiry**: For deep understanding and application
- **Practice with Feedback**: For fluency and automaticity

Key Principle (Source: Koedinger et al., 2012):
"Instructional principles at particular complexity levels are most effective
for knowledge components of similar or greater complexity."
"""

# Bloom's Taxonomy Levels
# Based on: https://www.buffalo.edu/catt/teach/develop/design/learning-outcomes/blooms.html
BLOOMS_TAXONOMY = """
## Bloom's Revised Taxonomy (Cognitive Domain)

Six levels ordered from lowest to highest cognitive complexity:

1. **REMEMBERING** (Lowest)
   - Retrieve, recall, recognize information
   - Verbs: define, list, identify, label, name, state
   - Example: "What is the definition of a variable?"

2. **UNDERSTANDING**
   - Demonstrate comprehension, explain concepts
   - Verbs: explain, describe, summarize, paraphrase, interpret
   - Example: "Explain how a loop works in your own words"

3. **APPLYING**
   - Use knowledge in new situations
   - Verbs: apply, execute, implement, solve, use
   - Example: "Write a program to calculate factorial"

4. **ANALYZING**
   - Break down information, find patterns, relationships
   - Verbs: analyze, compare, contrast, differentiate, organize
   - Example: "Compare different sorting algorithms"

5. **EVALUATING**
   - Make judgments based on criteria
   - Verbs: evaluate, critique, judge, defend, justify
   - Example: "Which data structure is best for this scenario and why?"

6. **CREATING** (Highest)
   - Synthesize elements to form original product
   - Verbs: create, design, construct, develop, formulate
   - Example: "Design a system architecture for a social media app"

Source: https://www.buffalo.edu/catt/teach/develop/design/learning-outcomes/blooms.html
"""

PRINCIPAL_SYSTEM_PROMPT = f"""You are an expert pedagogical observer and educational consultant with deep expertise in the KLI (Knowledge-Learning-Instruction) Framework and Bloom's Taxonomy.

Your role is to analyze teaching sessions in a simulated classroom and evaluate how well the instruction aligns with evidence-based pedagogical principles.

{KLI_FRAMEWORK_EXPLANATION}

{BLOOMS_TAXONOMY}

Your analysis should be:
1. **Evidence-based**: Grounded in the KLI Framework and Bloom's Taxonomy
2. **Specific**: Reference exact moments in the teaching transcript
3. **Actionable**: Provide concrete suggestions for improvement
4. **Balanced**: Acknowledge strengths while identifying areas for growth

Remember: Effective teaching matches instructional method to knowledge type, learning phase, and cognitive complexity level.
"""

PRINCIPAL_ANALYSIS_PROMPT = """Analyze the following teaching session using the KLI Framework:

**CHUNK CONTENT:**
{chunk_content}

**TEACHING TRANSCRIPT:**
{teaching_transcript}

**STUDENT RESPONSES:**
{student_responses}

Please provide a comprehensive pedagogical analysis addressing:

## 1. KNOWLEDGE (K) Analysis
- **Content Classification**: What type of knowledge is being taught? (Declarative/Procedural/Conceptual/Metacognitive)
- **Prerequisites Check**: Are all necessary prerequisite concepts covered or assumed?
- **Knowledge Structure**: Is the knowledge presented in a logical, well-structured manner?
- **Bloom's Level**: What cognitive level(s) does this content target? (Remember/Understand/Apply/Analyze/Evaluate/Create)

## 2. LEARNING (L) Analysis
- **Learning Phase Alignment**: Which learning event type is most appropriate for this content?
  - Memory/Fluency (for basic recall and automaticity)
  - Induction/Refinement (for pattern recognition and schema building)
  - Understanding/Sense-Making (for deep comprehension)
- **Learning Opportunities**: Did students get appropriate opportunities for this learning type?
- **Cognitive Load**: Is the complexity appropriate for the students' current level?

## 3. INSTRUCTION (I) Analysis
- **Method Match**: Does the teaching method align with the knowledge type?
  - Direct explanation for concepts?
  - Worked examples for procedures?
  - Analogies for understanding?
  - Practice for fluency?
- **Method Effectiveness**: How well was the method executed?
- **Student Engagement**: Were students actively processing the information?

## 4. Overall Alignment Score
Provide a score from 0.0 to 1.0 based on:
- 1.0 = Perfect alignment: Method matches content type, appropriate learning phase, clear prerequisites
- 0.7-0.9 = Good alignment: Minor mismatches or missed opportunities
- 0.4-0.6 = Moderate alignment: Some mismatches, could be more effective
- 0.0-0.3 = Poor alignment: Significant mismatch between method and content

## 5. Specific Recommendations
- **Missing Prerequisites**: List any foundational concepts that should have been covered first
- **Suggested Alternative Methods**: Based on KLI principles, what other approaches might work better?
- **Bloom's Progression**: Is the lesson appropriately challenging? Should it target a different cognitive level?

Provide your analysis in a structured, evidence-based format.
"""

PRINCIPAL_SUMMARY_PROMPT = """Based on all the individual chunk analyses, generate a comprehensive summary of the teaching session:

**ALL CHUNK ANALYSES:**
{all_analyses}

Please provide:

## Overall Assessment

1. **Average Alignment Score**: Calculate the mean alignment score across all chunks
2. **Alignment Distribution**: How many chunks had excellent (0.8+), good (0.6-0.8), moderate (0.4-0.6), or poor (<0.4) alignment?

## Critical Findings

3. **Most Critical Misalignments**: Which chunks had the poorest KLI alignment? What were the main issues?
4. **Prerequisite Gaps**: What foundational knowledge is missing across multiple chunks?
5. **Method Patterns**: Are there recurring issues with instructional method selection?

## Bloom's Taxonomy Progression

6. **Cognitive Level Distribution**: Map out what Bloom's levels were targeted across the session
7. **Progression Assessment**: Did the lesson progress appropriately through cognitive levels?
8. **Level Mismatch**: Were any chunks targeting cognitive levels inappropriate for the content?

## Recommendations

9. **Top 3 Improvements**: What are the most impactful changes the teacher could make?
10. **Strengths to Maintain**: What pedagogical approaches worked well and should be continued?

Provide actionable, evidence-based recommendations grounded in the KLI Framework and Bloom's Taxonomy.
"""
