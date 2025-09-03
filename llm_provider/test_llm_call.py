from datetime import date

import pytest
from sympy import false, true

from llm_provider.llm_call import LLMCall
from pydantic_classes import LLMCallInput, Provider, ReasoningEffort

pytest_plugins = ("pytest_asyncio",)
llm_call_class = LLMCall()


SYSTEM_PROMPT = f"""You are ChatGPT, a large language model trained by OpenAI.
Knowledge cutoff: 2024-06
Current date: {date.today()}
Reasoning: high
# Valid channels: analysis, commentary, final. Channel must be included for every message."""
DEVELOPER_PROMPT = """You are the following character. Think and respond to situations as the character would.

Name

Arav Jain

Personality Overview

Extraversion: Introverted, reserved, quiet; prefers solitude or small-group interactions and takes time before engaging socially.
Agreeableness: Highly cooperative, pleasant, empathetic; values harmony and others' well-being.
Conscientiousness: Average reliability and organization; generally self-controlled but may not obsess over every detail unless necessary.
Neuroticism: Low; remains calm, composed, unflappable even under stress.
Openness: Average; comfortable with tradition yet open to new ideas; balanced thinking that is neither simplistic nor overly complex.
Professional Background

• B.Tech. in Computer Science & Engineering (IoT specialization) from Vellore Institute of Technology (CGPA 9.14, 2022-present).

• Internships:

- Samsung R&D Institute Bangalore - Fine-tuned large language models and built multilingual orchestration systems (May-July 2025; Oct 2024-May 2025).

- Wadhwani AI - Developed adaptive Retrieval-Augmented Generation (RAG) systems, transitioned architectures to stateless design.

- King Saud University & VIT - ML research on State of Charge estimation for electric vehicles, published in Journal of Energy Storage.

- IIT Indore - Improved ASR models using custom Mamba encoders; managed large-scale data pipelines.

• Leadership & Roles:

- Team Lead, Prometheus (VIT RoboCup) - Leading a 50-member robotics and AI team.

- Editorial Head, Youth Red Cross VIT - Managing event documentation and blogs.

- Vice President Membership, Toastmasters International VIT - Expanded membership by 56 %.

• Achievements: Secured $200k+ funding for Team Prometheus; won Samsung PRISM Hackathon 2024 and national awards at ISRO & KSP Hackathons; multiple conference abstracts accepted.

Skills & Expertise

Programming: Python, C++, JavaScript, SQL, LaTeX
Frameworks/Libraries: PyTorch, HuggingFace, Fairseq, Scikit-learn, Numpy, Pandas, Docker, Kubernetes, Mamba, Megalodon
Data Tools: FAISS, Qdrant, PostgreSQL, Redis, Ollama
OS: Ubuntu, Windows
Soft Skills: Project management, research design, public speaking, team leadership, editorial writing
Certifications: Generative AI, Generative Adversarial Networks, Computer Vision
Communication Style & Decision-Making

• Speaks in clear, concise technical language; prefers structured explanations and visual aids.

• Tone is formal yet friendly when appropriate; avoids slang but remains approachable.

• Prefers written documentation for complex topics.

• Makes decisions through evidence-based analysis: evaluates data, considers alternatives, then selects the most efficient solution.

Strengths & Potential Weaknesses

• Strengths - Deep ML/NLP expertise, calm under pressure, collaborative, research-driven, analytical precision.

• Weaknesses - Introverted nature may slow spontaneous networking; average conscientiousness could lead to occasional procrastination; low extraversion might make large social interactions draining.

---END OF PROFILE---"""
INPUT_PROMPT = """---SITUATION---
You are currently in a classroom and the teacher just finished teaching:
Introduction
• Urban data refers to data that is collected about urban areas, including
cities, towns, and other built-up areas.
• Urban data can include a wide range of information, including demographic
data, economic data, housing data, and data on infrastructure and other
urban systems.
• Urban data is often collected and analyzed by governments, research
institutions, and other organizations in order to
• better understand urban trends and patterns,
• inform policy and planning decisions, and
• measure the performance of urban systems and services.
Contd.,
• Urban data can be collected using a variety of methods, including
censuses, surveys, satellite imagery, and other sources.
• It can be analyzed using statistical and spatial analysis techniques to
identify trends and patterns and to understand the relationships
between different variables.
• Urban data can be used to inform a wide range of decisions and policy
areas, including housing, transportation, economic development, and
environmental management.
• It can also be used to track progress towards urban sustainability goals
and to identify areas where further action is needed.
Quantitative Data: The Census Quantitative Data
• quantitative data is data that can be measured and expressed in
numerical terms.
• It is often used in research and analysis to describe and understand
trends and patterns in data.
• Quantitative data can be collected using a variety of methods,
including surveys, experiments, and observational studies.
• It can be analyzed using statistical and mathematical techniques to
identify patterns and trends and to understand the relationships
between different variables.
• Advantages of using quantitative data in research and analysis
• Measure and compare data: Quantitative data allows for the measurement and
comparison of data in a standardized way.
• Test hypotheses: Quantitative data can be used to test hypotheses and to determine
the statistical significance of relationships between variables.
• Generalize findings: Quantitative data can be used to make generalizations about a
larger population based on a sample. Quantitative data is often contrasted with
qualitative data, which is more subjective and difficult to measure numerically. Both
quantitative and qualitative data can be useful in different contexts and for different
purposes, and many research studies use a combination of both types of data.
Census
• The census is a process of collecting, compiling, and publishing data
about the population and housing of a country or region.
• It is typically conducted by national governments or other official
bodies, and it is typically conducted on a regular basis, such as every
10 years.
• The census is an important source of data that is used for a variety of
purposes, including:
• Planning and policy-making: The census provides data that can be
used by governments, businesses, and other organizations to make
informed decisions about planning and policy.
Contd.,
• Allocating resources: The census can be used to help allocate resources,
such as funding for schools and other public services, based on the needs
of different areas.
• Studying social and economic trends: The census can provide valuable
insights into social and economic trends and patterns, such as changes in
population size and composition, housing patterns, and income levels.
The census typically collects a wide range of data, including information
about age, gender, race and ethnicity, family structure, education,
employment, and housing. It may also collect data on a variety of other
topics, depending on the specific needs and goals of the census.
• Censuses can be conducted using a variety of methods, including mail
surveys, phone surveys, and in-person interviews.
• In recent years, there has been a trend towards the use of digital
technologies to collect and compile census data.
Census contd.,
• few examples of censuses:
• The United States Census is a national census that is conducted by the U.S.
Census Bureau every 10 years. It collects data on a wide range of topics,
including age, gender, race and ethnicity, household composition, education,
employment, and housing.
• The Canadian Census is a national census that is conducted by Statistics
Canada every five years. It collects data on a range of topics, including age,
gender, language, education, employment, and housing.
• The Indian Census is a national census that is conducted by the Office of the
Registrar General and Census Commissioner every 10 years. It collects data
on a wide range of topics, including age, gender, religion, education,
employment, and housing.
• The United Kingdom Census is a national census that is conducted by the
Office for National Statistics every 10 years. It collects data on a range of
topics, including age, gender, race and ethnicity, household composition,
education, employment, and housing.
Racial/Residential Segregation
• Census data, including data on age, race and ethnicity, and household
composition, can be used to create maps that show patterns of
residential and racial segregation in urban areas.
• Residential segregation refers to the separation of different racial or
ethnic groups into different neighborhoods or communities. It can
be the result of a variety of factors, including discriminatory housing
practices, economic inequality, and personal preferences.
• Racial segregation can have a number of negative impacts, including
limiting access to resources and opportunities, aggravating social
and economic inequality, and contributing to racial tensions and
conflict.
• Maps created using census data can help to identify patterns of
residential and racial segregation and can be used to inform policy
and planning decisions aimed at promoting more inclusive and
equitable communities.
• They can also be used by researchers and advocates to raise
awareness about segregation and its impacts and to advocate for
change.
• We can also create maps that look at the average income, or at the
average age of a neighborhood.
• Below
is
a
map
generated
with
data
from
the
2010
Census
about Residential Segregation in New York City.
---END OF SITUATION---

The Response format is:
If you want to ask a doubt: {"ask_doubt": true, "doubt":"The doubt that you have"}
If you dont want to ask a doubt: {"ask_doubt":false, "doubt":"NA"}"""


class TestLLMCall:
    @pytest.mark.asyncio
    async def test_llm_call_lightning(self):
        input_to_function = LLMCallInput(
            system_prompt_provided=True,
            developer_prompt_provided=True,
            system_prompt_to_llm=SYSTEM_PROMPT,
            developer_prompt_to_llm=DEVELOPER_PROMPT,
            user_prompt_to_llm=INPUT_PROMPT,
            model_provider=Provider.LIGHTNING,
            model_name="lightning-ai/gpt-oss-20b",
            reasoning_effort=ReasoningEffort.HIGH,
        )
        response = await llm_call_class.generate(input_to_function)
        print(
            f"""The output from the Lightning is:
            {response.response}"""
        )
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_llm_call_google(self):
        input_to_function = LLMCallInput(
            system_prompt_provided=False,
            developer_prompt_provided=False,
            system_prompt_to_llm=SYSTEM_PROMPT,
            developer_prompt_to_llm=DEVELOPER_PROMPT,
            user_prompt_to_llm="Tell me about yourself",
            model_provider=Provider.GEMINI,
            model_name="gemini-2.5-flash-lite",
        )
        response = await llm_call_class.generate(input_to_function)
        print(
            f"""The output from the Gemini model is:
            {response.response}"""
        )
        assert response.status == 200

    # @pytest.mark.asyncio
    # async def test_llm_call_ollama(self):

    # TODO: Write a test for semaphores type shi on both google and lmstudio
