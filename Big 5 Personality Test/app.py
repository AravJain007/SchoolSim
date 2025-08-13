from datetime import UTC, datetime
from uuid import uuid4

import gridfs
import streamlit as st
from big5_results import BIG5_RESULTS
from choices_weights import CHOICES
from pymongo import MongoClient
from questions import QUESTION_LIST


@st.cache_resource(show_spinner=False)
def get_db():
    """Return a MongoDB database handle using cached client.

    Reads configuration from Streamlit secrets first, then environment variables.
    """
    mongo_uri = "mongodb://localhost:27017/"

    if not mongo_uri:
        return None

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db_name = "b5"
    return client[db_name]


def main():
    st.set_page_config(
        page_title="Big 5 Personality Test", page_icon="🧠", layout="centered"
    )
    st.markdown(
        """
        <style>
        /* Subtle layout polish */
        .block-container {padding-top: 2rem; padding-bottom: 3rem;}
        .big5-card {background: #ffffff; padding: 1.25rem 1.0rem; border-radius: 10px; border: 1px solid rgba(0,0,0,0.06);}
        .big5-hero {background: linear-gradient(135deg, #eef6ff 0%, #ffffff 60%); padding: 1.25rem 1.0rem; border-radius: 12px; border: 1px solid rgba(0,0,0,0.05);}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Big 5 Personality Test")

    # --- Questions ---
    questions = QUESTION_LIST

    # --- Choices ---
    choices = CHOICES

    # --- Results ---
    results = BIG5_RESULTS

    # --- App Logic ---
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid4())

    if "user_name" not in st.session_state:
        st.session_state.user_name = ""

    if "college_id" not in st.session_state:
        st.session_state.college_id = ""

    if "resume_info" not in st.session_state:
        st.session_state.resume_info = {
            "filename": None,
            "size": 0,
            "bytes": None,
            "file_id": None,
        }

    if "teacher_name" not in st.session_state:
        st.session_state.teacher_name = ""

    if "class_location" not in st.session_state:
        st.session_state.class_location = ""

    if "page" not in st.session_state:
        st.session_state.page = 0

    if "answers" not in st.session_state:
        st.session_state.answers = {}

    if "saved" not in st.session_state:
        st.session_state.saved = False

    if not st.session_state.user_name:
        with st.container(border=True):
            st.subheader("Welcome 👋")
            st.write("Please provide a few details before starting the assessment.")

            name = st.text_input("Full name", placeholder="Jane Doe")
            college_id = st.text_input("College ID", placeholder="e.g., 22CSE001")
            teacher_name = st.selectbox(
                "Class Teacher",
                ["Dr. B. Ashok", "Dr. Indiragandhi V."],
            )
            class_location = st.text_input(
                "Class location",
                placeholder="SJT301, CDMM102, MB101, etc",
            )
            uploaded = st.file_uploader(
                "Upload your resume (PDF, up to 2 MB)",
                type=["pdf"],
                accept_multiple_files=False,
            )

            file_ok = True
            file_error = ""
            resume_bytes = None
            resume_filename = None
            resume_size = 0
            if uploaded is not None:
                resume_bytes = uploaded.getvalue()
                resume_size = len(resume_bytes)
                resume_filename = uploaded.name
                if resume_size > 2 * 1024 * 1024:
                    file_ok = False
                    file_error = "File too large. Please upload a PDF up to 2 MB."
            else:
                file_ok = False
                file_error = "Please upload your resume as a single PDF (max 2 MB)."

            cols = st.columns([1, 1, 1])
            with cols[0]:
                st.caption(
                    "Your information is used to save your results and resume in a secure database."
                )
            with cols[1]:
                pass
            with cols[2]:
                pass

            # Validate class location as strictly alphanumeric
            location_ok = bool(class_location) and class_location.isalnum()
            if class_location and not class_location.isalnum():
                st.error(
                    "Class location must be alphanumeric (letters and numbers only)."
                )

            start_disabled = (
                not name or not college_id or not file_ok or not location_ok
            )
            if not file_ok and uploaded is not None:
                st.error(file_error)

            if st.button("Start Test", type="primary", disabled=start_disabled):
                st.session_state.user_name = name.strip()
                st.session_state.college_id = college_id.strip()
                st.session_state.teacher_name = teacher_name.strip()
                st.session_state.class_location = class_location.strip()
                st.session_state.resume_info = {
                    "filename": resume_filename,
                    "size": resume_size,
                    "bytes": resume_bytes,
                    "file_id": None,
                }
                st.session_state.page = 0
                st.session_state.answers = {}
                st.rerun()
    else:
        # Progress bar
        total_questions = len(questions)
        answered_count = len(st.session_state.answers)
        progress_ratio = min(
            max(answered_count / total_questions if total_questions else 0.0, 0.0), 1.0
        )
        st.progress(
            progress_ratio,
            text=f"Progress: {answered_count}/{total_questions} answered",
        )

        if st.session_state.page * 5 < len(questions):
            st.header(f"Section {st.session_state.page + 1}")
            for i in range(
                st.session_state.page * 5,
                min((st.session_state.page + 1) * 5, len(questions)),
            ):
                question = questions[i]
                with st.container():
                    st.subheader(question["text"])
                    keyed_choices = choices[question["keyed"]]
                    choice_texts = [c["text"] for c in keyed_choices]
                    answer = st.radio("", choice_texts, key=i, horizontal=True)
                    st.session_state.answers[i] = keyed_choices[
                        choice_texts.index(answer)
                    ]["score"]

            if st.button("Next"):
                st.session_state.page += 1
                st.rerun()
        else:
            st.header(f"Results for {st.session_state.user_name}")

            # --- Scoring (aligned with packages/score/src/index.ts) ---
            def calculate_result(total_score: float, count: int) -> str:
                avg_score = total_score / count if count else 0.0
                if avg_score > 3.5:
                    return "high"
                elif avg_score < 2.5:
                    return "low"
                return "neutral"

            # Aggregate per domain and facet like the TS implementation
            processed: dict = {}
            for i, answer_score in st.session_state.answers.items():
                q = questions[i]
                d = q["domain"]
                f = q.get("facet")
                if d not in processed:
                    processed[d] = {
                        "score": 0,
                        "count": 0,
                        "result": "neutral",
                        "facet": {},
                    }
                processed[d]["score"] += answer_score
                processed[d]["count"] += 1
                if f is not None:
                    if f not in processed[d]["facet"]:
                        processed[d]["facet"][f] = {
                            "score": 0,
                            "count": 0,
                            "result": "neutral",
                        }
                    processed[d]["facet"][f]["score"] += answer_score
                    processed[d]["facet"][f]["count"] += 1

            # Compute categorical results
            for domain_data in processed.values():
                domain_data["result"] = calculate_result(
                    domain_data["score"], domain_data["count"]
                )
                for facet_data in domain_data["facet"].values():
                    facet_data["result"] = calculate_result(
                        facet_data["score"], facet_data["count"]
                    )

            # Build lookup from domain letter to detailed metadata
            results_by_domain_letter = {v["domain"]: v for v in results.values()}

            # Display results (domain title + short description + domain-level result text)
            for d in ["N", "E", "O", "A", "C"]:
                if d not in processed:
                    continue
                domain_meta = results_by_domain_letter.get(d)
                if not domain_meta:
                    continue
                st.subheader(domain_meta["title"])
                st.write(domain_meta["shortDescription"])
                domain_label = processed[d]["result"]
                for r in domain_meta.get("results", []):
                    if r.get("score") == domain_label:
                        st.write(r.get("text", ""))
                        break

            # --- Persist to MongoDB ---
            db = get_db()
            collection_name = "results"

            if db is None:
                st.info(
                    "Database not configured. Set MONGODB_URI (and optionally MONGODB_DB, MONGODB_COLLECTION) in .streamlit/secrets.toml or environment variables to enable saving results."
                )
            else:
                if not st.session_state.saved:
                    if st.button("Save results to database"):
                        try:
                            # Store resume in GridFS first (if present and not already stored)
                            resume_file_id = st.session_state.resume_info.get("file_id")
                            if (
                                st.session_state.resume_info.get("bytes")
                                and resume_file_id is None
                            ):
                                fs = gridfs.GridFS(db)
                                resume_file_id = fs.put(
                                    st.session_state.resume_info["bytes"],
                                    filename=st.session_state.resume_info.get(
                                        "filename"
                                    )
                                    or "resume.pdf",
                                    contentType="application/pdf",
                                    metadata={
                                        "sessionId": st.session_state.session_id,
                                        "userName": st.session_state.user_name,
                                        "collegeId": st.session_state.college_id,
                                        "teacherName": st.session_state.teacher_name,
                                        "classLocation": st.session_state.class_location,
                                        "size": st.session_state.resume_info.get(
                                            "size", 0
                                        ),
                                    },
                                )
                                st.session_state.resume_info["file_id"] = resume_file_id

                            # Prepare a detailed, text-based result summary for domains and facets
                            domain_facet_details = {}
                            for d_letter, meta in results_by_domain_letter.items():
                                facet_detail_map = {
                                    f["facet"]: {
                                        "title": f.get("title"),
                                        "description": f.get("text"),
                                    }
                                    for f in meta.get("facets", [])
                                }
                                domain_facet_details[d_letter] = {
                                    "title": meta.get("title"),
                                    "shortDescription": meta.get("shortDescription"),
                                    "facets": facet_detail_map,
                                }

                            result_summary = {}
                            for d_letter, d_data in processed.items():
                                meta = results_by_domain_letter.get(d_letter, {})
                                # Pick the domain result text matching the categorical label
                                domain_label = d_data["result"]
                                domain_text = ""
                                for r in meta.get("results", []):
                                    if r.get("score") == domain_label:
                                        domain_text = r.get("text", "")
                                        break
                                # Assemble facet breakdown
                                facet_breakdown = {}
                                facet_details_map = domain_facet_details.get(
                                    d_letter, {}
                                ).get("facets", {})
                                for f_num, f_data in d_data.get("facet", {}).items():
                                    avg = (
                                        (f_data["score"] / f_data["count"])
                                        if f_data["count"]
                                        else 0.0
                                    )
                                    facet_breakdown[str(f_num)] = {
                                        "score": f_data["score"],
                                        "count": f_data["count"],
                                        "average": avg,
                                        "result": f_data["result"],
                                        "title": facet_details_map.get(f_num, {}).get(
                                            "title"
                                        ),
                                        "description": facet_details_map.get(
                                            f_num, {}
                                        ).get("description"),
                                    }

                                avg_domain = (
                                    (d_data["score"] / d_data["count"])
                                    if d_data["count"]
                                    else 0.0
                                )
                                result_summary[d_letter] = {
                                    "title": meta.get("title"),
                                    "shortDescription": meta.get("shortDescription"),
                                    "score": d_data["score"],
                                    "count": d_data["count"],
                                    "average": avg_domain,
                                    "result": domain_label,
                                    "resultText": domain_text,
                                    "facets": facet_breakdown,
                                }

                            doc = {
                                "sessionId": st.session_state.session_id,
                                "userName": st.session_state.user_name,
                                "collegeId": st.session_state.college_id,
                                "teacherName": st.session_state.teacher_name,
                                "classLocation": st.session_state.class_location,
                                "answers": [
                                    {
                                        "index": i,
                                        "domain": questions[i]["domain"],
                                        "facet": questions[i].get("facet"),
                                        "score": answer_score,
                                    }
                                    for i, answer_score in st.session_state.answers.items()
                                ],
                                "resultSummary": result_summary,
                                "resume": {
                                    "fileId": str(
                                        st.session_state.resume_info.get("file_id")
                                    )
                                    if st.session_state.resume_info.get("file_id")
                                    else None,
                                    "filename": st.session_state.resume_info.get(
                                        "filename"
                                    ),
                                    "size": st.session_state.resume_info.get("size"),
                                    "contentType": "application/pdf"
                                    if st.session_state.resume_info.get("filename")
                                    else None,
                                },
                                "dateStamp": datetime.now(UTC),
                                "app": "streamlit-big5",
                                "version": 1,
                            }
                            inserted = db[collection_name].insert_one(doc)
                            st.session_state.saved = True
                            st.success(f"Saved with id: {inserted.inserted_id}")
                        except Exception as e:
                            st.error(f"Failed to save results: {e}")
                else:
                    st.success("Results already saved for this session.")


if __name__ == "__main__":
    main()
