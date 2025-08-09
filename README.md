# SIMS Teacher

Teachers can use this to test their materials for the class they are about to teach. These will help a lot as all the students arent equal and all the teachers are not experienced with the new generation and dont know how they will learn better. So this sim will run with the course material (pdf, pptx, word docs, etc.) or class notes that the teacher will use. So this will help the teacher understand how the students learn and understand everything.

### Characters to be played:

1.  Teacher:
    As a teacher the LLMs job will be to teach the class a particular topic (on the basis of material provided). Now the teacher will teach and have momentary pauses in the middle for the children to ask doubts. He will explain those doubts and move on with the session. The teacher may choose any appropriate timings for doubt clarification.

2.  Students:
    Now the students will have multiple fascinating things like:

    - Each student will have their own unique personality.
    - Not every student will ask doubts and not each doubt is going to be same. So some students will ask silly doubts and others will ask really good doubts (as it is in all the classrooms)

3.  Pricipal:
    The job of the principal is to take notes while the teacher is teaching and when the children are asking doubts. It will then use its knowledge of psychological tricks and tips which help students become better students and then write points on how to improve the material to the teacher.

### Flow of the Entire Simulation:

- User gives input to the simulation. The input is the student names and information and then the teaching material.
- Then the professor enters the number of students in the class (ranging from 10 to 100).
- Then we spin up the simulation for the entire class. This is going to be a web based interface.
- It is going to be a classroom-esque setup where the students will be able to hear each other within a vicinity and they will be able to hear the doubts they asked to the teacher.
- The user can check the characteristics of every student (by hovering over the student).
- As soon as the teaching begins the teacher starts to teach and that context will be provided to all the students.
- Each student will make their own notes and try to understand concepts on their own. Each students notes will differ based on their characteristics.
- So after teaching for sometime the teacher will pause and ask for doubts. Randomnly we will decide how many students (0-10) want to ask doubt and who are going to be those students.
- Again the quality of the doubts will be on the basis of the student characteristics and the teacher should try to explain it to them to the best of his / her capabilities.
- The teaching and the doubt taking continues till the class is over.
- During every doubt taking session the principal will make notes of how the teacher taught and what could have improved.
- The principal will update these notes during every doubt session.
- At the end of the class the principal will use these notes and psychology to give the teacher suggestions about all of their content.
- The final output will be the things that need to be changed in the course material and the doubts that the teacher should be expecting in the class.
- This will help the teacher to improve based on proven pedagogies for all types of students.

### Parts of the project

1. Frontend:

   - Make a classroom-esque environment for all the agents and show communication live as it is happening.
   - Hovering over a student reveals their characteristics. Also there will be an option to click and view the kids notes.
   - It does not need to be very fancy. I am just imagining the students be grid based.

2. Backend:

   - Python.
   - Need to find a character based library for making LLMs do roleplay.

3. Deployment:
   - Docker

### Metrics that I plan on using:

1. Flesch‑Kincaid Score - For Clarity & Readability
2. Bloom’s Taxonomy - Hierarchy of cognitive skills (Knowledge → Comprehension → Application → Analysis → Synthesis → Evaluation) – useful for “Depth & Breadth” metrics.
3. Pedagogical Soundness - ADDIE could also be taken into consideration if entire course creation is in question.
4.
