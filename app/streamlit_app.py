from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.answering import answer
from src.retrieval import HybridRetriever, SemanticIndex
from src.store import safe_load


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="AwanSolveAi | FG Wilson",
    page_icon="âš™ï¸",
    layout="wide",
)

st.title("AwanSolveAi · FG Wilson")

st.caption(
    "FG Wilson Generator Operations, Preventive Maintenance & "
    "Basic Fault-Finding AI"
)


# =============================================================================
# SESSION STATE
# =============================================================================

if "question_input" not in st.session_state:
    st.session_state.question_input = ""

if "history" not in st.session_state:
    st.session_state.history = []


# =============================================================================
# CORPUS / BUILD VALIDATION
# =============================================================================

state = safe_load(ROOT)


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.header("Manufacturer evidence")

    if state["ok"]:
        d = state["manifest"]["documents"][0]

        st.success("Corpus integrity verified")

        st.write(d["title"])

        st.caption(
            d["document_number"]
            + " · "
            + d["revision"]
        )

        st.write(d["applicability"])

        st.metric(
            "Source pages",
            state["build"]["page_count"],
        )

        st.caption(
            "Individual generator models are not established "
            "by this family manual."
        )

        with st.expander("Source identity"):
            st.json(
                {
                    k: d[k]
                    for k in (
                        "filename",
                        "sha256",
                        "language",
                        "approved",
                        "approval_basis",
                    )
                }
            )

        if st.session_state.history:
            st.divider()

            if st.button(
                "Clear session history",
                use_container_width=True,
            ):
                st.session_state.history = []
                st.session_state.question_input = ""
                st.rerun()

    else:
        st.error("Corpus unavailable")
        st.caption(state["error"])


# =============================================================================
# RETRIEVER
# =============================================================================

@st.cache_resource
def retriever(build_identity, semantic):
    """
    Revalidate the build immediately before constructing the retriever.
    Cached chunk files are never trusted without build validation.
    """

    checked = safe_load(ROOT)

    if not checked["ok"]:
        raise ValueError(
            checked["error"]
        )

    vector = (
        SemanticIndex(
            ROOT / "data/processed",
            ROOT / "data/models/all-MiniLM-L6-v2",
        )
        if semantic
        else None
    )

    return HybridRetriever(
        checked["chunks"],
        vector,
    )


# =============================================================================
# EXAMPLE QUESTIONS
# =============================================================================

EXAMPLE_QUESTIONS = {
    "Not specified / general guidance":
        "What pre-start inspections are required before starting the generator set?",

    "PowerWizard 1.1":
        "What does the manual say about PowerWizard 1.1 controls and indications?",

    "PowerWizard 1.1+":
        "What happens when PowerWizard reports an over-voltage shutdown?",

    "PowerWizard 2.1":
        "What happens when PowerWizard reports an over-voltage shutdown?",

    "PowerWizard 2.1+":
        "What does the ACKNOWLEDGE key do on PowerWizard 2.1+?",

    "PowerWizard 4.1":
        "What controls and indications are described for PowerWizard 4.1?",

    "DeepSea (model unspecified)":
        "What should be checked if the DeepSea unit shuts down?",

    "FG100":
        "What FG100 functions are supported by the available manufacturer evidence?",
}


GENERAL_SUGGESTIONS = (
    "What pre-start inspections are required before starting the generator set?",
    "What preventative maintenance intervals are described in the manual?",
    "What safety precautions apply before maintenance?",
)


# =============================================================================
# EXAMPLE BUTTON CALLBACKS
# =============================================================================

def use_example_question():
    """
    Put the currently selected controller's example into the question field.
    """

    controller_name = st.session_state.get(
        "controller_select",
        "Not specified / general guidance",
    )

    st.session_state.question_input = (
        EXAMPLE_QUESTIONS.get(
            controller_name,
            EXAMPLE_QUESTIONS[
                "Not specified / general guidance"
            ],
        )
    )


def use_suggested_question(question):
    """
    General example questions must use general guidance rather than
    accidentally inheriting a controller-specific retrieval filter.
    """

    st.session_state.controller_select = (
        "Not specified / general guidance"
    )

    st.session_state.question_input = question


# =============================================================================
# RESULT RENDERER
# =============================================================================

def render_response(record, latest=False):
    """
    Render one answer record from session history.
    """

    if latest:
        st.markdown("## Latest response")

    st.markdown(
        f"### Question\n{record['question']}"
    )

    st.caption(
        f"Controller: {record['controller']}"
    )

    result = record["result"]

    # -------------------------------------------------------------------------
    # Answer
    # -------------------------------------------------------------------------

    st.markdown("### Answer")

    st.write(
        result["answer"]
    )

    if result.get("reason"):
        st.caption(
            result["reason"]
        )

    if result.get("qualified_service"):
        st.warning(
            "This evidence includes work reserved for trained "
            "personnel or referral to the dealer. Check the cited "
            "scope before acting."
        )

    # -------------------------------------------------------------------------
    # Manufacturer procedure
    # -------------------------------------------------------------------------

    st.markdown(
        "### Manufacturer procedure"
    )

    for step in result["steps"]:
        st.text(step)

    if not result["steps"]:
        st.caption(
            "No supported procedural sequence returned."
        )

    # -------------------------------------------------------------------------
    # Warnings / Cautions
    # -------------------------------------------------------------------------

    st.markdown(
        "### Warnings / Cautions"
    )

    for warning in result["warnings"]:
        st.warning(warning)

    if not result["warnings"]:
        st.caption(
            "No additional warning text was attached "
            "to this answer."
        )

    # -------------------------------------------------------------------------
    # Sources
    # -------------------------------------------------------------------------

    st.markdown("### Source")

    if result["sources"]:
        for source in result["sources"]:
            st.write(
                source["manual"]
                + " · "
                + source["revision"]
            )

            st.caption(
                f"{source['section']} | "
                f"PDF {source['pdf_page']} | "
                f"Printed {source['printed_page']} | "
                f"{source['chunk_id']}"
            )

            st.caption(
                source["applicability"]
            )

            if source["warning_pdf_pages"]:
                st.caption(
                    "Inherited safety context: PDF pages "
                    + ", ".join(
                        map(
                            str,
                            source[
                                "warning_pdf_pages"
                            ],
                        )
                    )
                )

    else:
        st.caption(
            "No manufacturer source was accepted "
            "for this response."
        )

    # -------------------------------------------------------------------------
    # Retrieved evidence
    # -------------------------------------------------------------------------

    with st.expander(
        "Retrieved manufacturer evidence"
    ):
        evidence = record.get(
            "evidence",
            [],
        )

        if evidence:
            for item in evidence:
                st.caption(
                    item["section"]
                    + " · "
                    + item["chunk_id"]
                )

                st.text(
                    item["text"]
                )

        else:
            st.caption(
                "No eligible manufacturer evidence retrieved."
            )

    st.caption(
        f"Response time: "
        f"{record['response_time']:.2f} s"
    )


# =============================================================================
# CORPUS FAILURE MODE
# =============================================================================

if not state["ok"]:
    st.error(
        "Technical answering is disabled until the corpus "
        "and build pass validation."
    )

    st.text_input(
        "Search manufacturer guidance",
        disabled=True,
    )

    st.button(
        "Search evidence",
        disabled=True,
    )


# =============================================================================
# MAIN APPLICATION
# =============================================================================

else:
    st.info(
        "Operator guidance and qualified-technician maintenance reference. "
        "Confirm the fitted equipment; model-specific service diagnosis "
        "requires additional manuals."
    )

    st.caption(
        "Supports safety, pre-start checks, operation, descriptive "
        "PowerWizard and DeepSea indications, routine maintenance, "
        "service intervals and cited basic symptom/remedy guidance. "
        "Numerical fault-code dictionaries, SPN/FMI diagnostics, "
        "controller internal service, wiring-level diagnosis, engine "
        "overhaul, component disassembly and unstated model-specific "
        "repair specifications require additional approved manuals."
    )

    controller_options = [
        "Not specified / general guidance"
    ] + list(
        d["controllers"]
    )

    # -------------------------------------------------------------------------
    # Controller selection
    # -------------------------------------------------------------------------

    st.subheader(
        "Ask the manufacturer evidence"
    )

    controller = st.selectbox(
        "Fitted controller",
        controller_options,
        key="controller_select",
        help=(
            "Select the fitted controller when known. "
            "Use general guidance when the controller is not relevant "
            "or has not been confirmed."
        ),
    )

    # -------------------------------------------------------------------------
    # Controller-specific example
    # -------------------------------------------------------------------------

    example_question = (
        EXAMPLE_QUESTIONS.get(
            controller,
            EXAMPLE_QUESTIONS[
                "Not specified / general guidance"
            ],
        )
    )

    st.markdown(
        "**Example question for this selection**"
    )

    example_col, button_col = st.columns(
        [4, 1]
    )

    with example_col:
        st.info(
            example_question
        )

    with button_col:
        st.write("")

        st.button(
            "Use this question",
            key="use_controller_example",
            on_click=use_example_question,
            use_container_width=True,
        )

    # -------------------------------------------------------------------------
    # General examples
    # -------------------------------------------------------------------------

    with st.expander(
        "More example questions"
    ):
        st.caption(
            "These examples use general manufacturer guidance. "
            "Selecting one automatically changes the controller to "
            "'Not specified / general guidance'."
        )

        example_columns = st.columns(
            len(GENERAL_SUGGESTIONS)
        )

        for index, suggestion in enumerate(
            GENERAL_SUGGESTIONS
        ):
            example_columns[index].button(
                suggestion,
                key=f"general_example_{index}",
                on_click=use_suggested_question,
                args=(suggestion,),
                use_container_width=True,
            )

    # -------------------------------------------------------------------------
    # Question input
    # -------------------------------------------------------------------------

    query = st.text_input(
        "Fault, symptom, inspection or maintenance question",
        key="question_input",
        placeholder=(
            "Describe the observed condition or the maintenance task"
        ),
    )

    selected = (
        None
        if controller.startswith(
            "Not specified"
        )
        else controller
    )

    search_clicked = st.button(
        "Search evidence",
        type="primary",
    )

    # -------------------------------------------------------------------------
    # Execute search
    # -------------------------------------------------------------------------

    if search_clicked:
        if not query.strip():
            st.warning(
                "Enter a question or select an example question first."
            )

        else:
            try:
                start_time = (
                    time.perf_counter()
                )

                r = retriever(
                    state["build"]["code_fingerprint"]
                    + state["build"]["artifacts"][
                        "chunks.json"
                    ],
                    state["build"]["semantic"],
                )

                hits = r.search(
                    query,
                    5,
                    controller=selected,
                )

                grounded_query = (
                    query
                    + (
                        " " + selected
                        if selected
                        else ""
                    )
                )

                result = answer(
                    grounded_query,
                    hits
                    + (
                        r.safety_evidence(
                            hits[0]
                        )
                        if hits
                        else []
                    ),
                )

                elapsed = (
                    time.perf_counter()
                    - start_time
                )

                evidence = []

                for hit in hits:
                    evidence.append(
                        {
                            "section":
                                hit.chunk.section,
                            "chunk_id":
                                hit.chunk.chunk_id,
                            "text":
                                hit.chunk.text,
                        }
                    )

                record = {
                    "question":
                        query,
                    "controller":
                        controller,
                    "result":
                        result,
                    "response_time":
                        elapsed,
                    "evidence":
                        evidence,
                }

                # Newest response appears first.
                st.session_state.history.insert(
                    0,
                    record,
                )

            except Exception as exc:
                st.error(
                    "Technical answering disabled: corpus or retrieval "
                    "could not be loaded."
                )

                st.caption(
                    str(exc)
                )

    # =========================================================================
    # LATEST RESPONSE
    # =========================================================================

    if st.session_state.history:
        st.divider()

        render_response(
            st.session_state.history[0],
            latest=True,
        )

    # =========================================================================
    # PREVIOUS SESSION HISTORY
    # =========================================================================

    if len(
        st.session_state.history
    ) > 1:
        st.divider()

        st.markdown(
            "## Previous questions"
        )

        for record in st.session_state.history[1:]:
            with st.expander(
                record["question"],
                expanded=False,
            ):
                render_response(
                    record,
                    latest=False,
                )


# =============================================================================
# FOOTER
# =============================================================================

st.divider()

st.caption(
    "Source-limited reference · FG Wilson P Series and PRO rental series · "
    "Consult the supplying dealer for equipment-specific service documents."
)
