"""
Example usage of the Principal Agent for KLI Framework analysis

This script demonstrates how to use the PrincipalAgent to analyze
teaching effectiveness using the Knowledge-Learning-Instruction Framework.
"""

import asyncio

from pydantic_classes import ChunkDetails, Provider, ReasoningEffort, StudentResponse
from simulation.principal_agent import PrincipalAgent


async def main():
    """
    Example demonstration of Principal Agent analysis.
    """
    # Initialize the Principal Agent
    principal = PrincipalAgent()

    # Example chunk (simulated course material)
    chunk = ChunkDetails(
        chunk_id="chunk_001",
        content="""
        Variables in Python are containers for storing data values. Unlike other programming
        languages, Python has no command for declaring a variable. A variable is created
        the moment you first assign a value to it.

        Example:
        x = 5
        y = "Hello"

        Variables do not need to be declared with any particular type, and can even
        change type after they have been set.
        """,
        difficulty_index=25.0,
        new_terms=["variable", "data type", "assignment"],
        page_range="Slide 3",
        has_formula=False,
        has_code=True,
    )

    # Example teaching transcript
    teaching_transcript = """
    Professor: Good morning class! Today we're going to learn about variables in Python.
    Think of a variable like a box where you can store things. Just like you might have
    a box labeled "toys" to store your toys, in Python we have variables to store data.

    Let me show you an example. When we write x = 5, we're creating a variable called x
    and putting the number 5 inside it. It's that simple! And the cool thing about Python
    is you don't need to tell it what type of data you're storing - it figures it out
    automatically.

    Let me show you another example: y = "Hello". Here we're storing text instead of a
    number. Same syntax, different type of data. Pretty neat, right?

    Does anyone have any questions?
    """

    # Example student responses
    student_responses = [
        StudentResponse(
            student_id="student_001",
            chunk_id="chunk_001",
            understanding_before=2,
            understanding_after=4,
            doubt_asked="Can we change the value of a variable after we create it?",
            doubt_resolved=True,
        ),
        StudentResponse(
            student_id="student_002",
            chunk_id="chunk_001",
            understanding_before=3,
            understanding_after=4,
            doubt_asked=None,
            doubt_resolved=None,
        ),
    ]

    print("=" * 70)
    print("PRINCIPAL AGENT - KLI FRAMEWORK ANALYSIS")
    print("=" * 70)
    print("\nAnalyzing teaching chunk using KLI Framework...")
    print(f"Chunk ID: {chunk.chunk_id}")
    print(f"Content length: {len(chunk.content)} characters")
    print(f"Students analyzed: {len(student_responses)}")
    print("\n" + "-" * 70)

    # Analyze the chunk
    analysis = await principal.analyze_chunk(
        chunk=chunk,
        teaching_transcript=teaching_transcript,
        student_responses=student_responses,
        model_provider=Provider.GEMINI,
        model_name="gemini-2.5-flash",
        reasoning_effort=ReasoningEffort.HIGH,
    )

    # Display results
    print("\n📊 ANALYSIS RESULTS:")
    print(f"\nAlignment Score: {analysis.alignment_score:.2f}/1.0")

    if analysis.alignment_score >= 0.8:
        print("✅ Excellent KLI alignment!")
    elif analysis.alignment_score >= 0.6:
        print("✓ Good alignment with minor improvements possible")
    elif analysis.alignment_score >= 0.4:
        print("⚠️  Moderate alignment - several improvements recommended")
    else:
        print("❌ Poor alignment - significant improvements needed")

    if analysis.missing_prerequisites:
        print("\n📚 Missing Prerequisites:")
        for i, prereq in enumerate(analysis.missing_prerequisites, 1):
            print(f"  {i}. {prereq}")
    else:
        print("\n📚 Missing Prerequisites: None identified")

    if analysis.suggested_methods:
        print("\n💡 Suggested Alternative Methods:")
        for i, method in enumerate(analysis.suggested_methods, 1):
            print(f"  {i}. {method}")
    else:
        print("\n💡 No alternative methods suggested")

    print("\n📝 Detailed Notes:")
    print("-" * 70)
    print(analysis.notes)
    print("-" * 70)

    # Generate a summary (for multiple chunks, you'd pass a list)
    print("\n\n" + "=" * 70)
    print("GENERATING COMPREHENSIVE SUMMARY")
    print("=" * 70)

    summary = await principal.generate_summary(
        all_analyses=[analysis],  # In real use, pass multiple analyses
        model_provider=Provider.GEMINI,
        model_name="gemini-2.5-flash",
        reasoning_effort=ReasoningEffort.HIGH,
    )

    print("\n" + summary)
    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("=" * 70)


if __name__ == "__main__":
    print("\n🎓 Principal Agent Test - KLI Framework Analysis\n")
    print("This test demonstrates the Principal Agent's ability to analyze")
    print("teaching effectiveness using the KLI Framework and Bloom's Taxonomy.\n")

    asyncio.run(main())
