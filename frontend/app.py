
import streamlit as st
import httpx

from frontend.services.api_client import ApiClient


st.set_page_config(
    page_title="Tamil Nadu Agriculture AI Search",
    page_icon="🌾",
    layout="wide",
)

st.markdown("""
<style>
.block-container {
    max-width: 1150px;
    padding-top: 2rem;
}
.main-heading {
    color: #176b40;
    font-weight: 750;
    margin-bottom: 0;
}
.result-card {
    border: 1px solid #d8e5dc;
    border-radius: 12px;
    padding: 0.4rem 1rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)


def get_api():
    return ApiClient()


if "search_history" not in st.session_state:
    st.session_state.search_history = []

if "results" not in st.session_state:
    st.session_state.results = None


with st.sidebar:
    st.title("🌾 Agriculture Search")
    st.caption("Tamil Nadu Government Scheme Explorer")

    st.divider()

    st.subheader("API Status")
    try:
        api = get_api()
        health = api.health()
        api.close()

        if health["vector_db"] == "connected":
            st.success("FAISS Connected")
        else:
            st.warning("FAISS index unavailable")

        st.metric(
            "Indexed Vectors",
            health["indexed_vectors"],
        )

    except (httpx.HTTPError, ValueError):
        st.error("FastAPI server unavailable")

    st.divider()
    st.subheader("Search History")

    for item in reversed(
        st.session_state.search_history[-10:]
    ):
        st.caption(item)


st.markdown(
    '<h1 class="main-heading">'
    '🌾 Tamil Nadu Agriculture Scheme AI Search'
    '</h1>',
    unsafe_allow_html=True,
)

st.write(
    "Discover agriculture subsidies, government schemes, "
    "farmer benefits, and eligibility information using "
    "AI-powered semantic search."
)

st.divider()

with st.form("search_form"):
    query = st.text_input(
        "Ask your question",
        placeholder=(
            "Ask about agriculture schemes, subsidies, "
            "crop insurance, or farmer eligibility..."
        ),
        key="agriculture_semantic_query",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        language = st.selectbox(
            "Language filter",
            ["all", "en", "ta"],
            format_func=lambda value: {
                "all": "All languages",
                "en": "English",
                "ta": "Tamil",
            }[value],
        )

    with col2:
        top_k = st.selectbox(
            "Results",
            [5, 10, 20],
        )

    with col3:
        use_distance_filter = st.checkbox(
            "Set maximum L2 distance"
        )

        max_distance = None

        if use_distance_filter:
            max_distance = st.number_input(
                "Maximum distance",
                min_value=0.0,
                value=1.5,
                step=0.1,
            )

    search_clicked = st.form_submit_button(
        "🔍 Search Agriculture Schemes",
        use_container_width=True,
        type="primary",
    )

if search_clicked:
    if not query.strip():
        st.warning("Please enter a search question.")
    else:
        with st.spinner("Searching government documents..."):
            api = get_api()

            try:
                response = api.search(
                    query.strip(),
                    top_k,
                    language,
                    max_distance,
                )

                st.session_state.results = response
                st.session_state.search_history.append(
                    query.strip()
                )

            except httpx.HTTPStatusError as exc:
                st.session_state.results = None
                st.error(
                    f"Search API returned HTTP "
                    f"{exc.response.status_code}"
                )

            except httpx.RequestError:
                st.session_state.results = None
                st.error(
                    "Cannot connect to FastAPI. "
                    "Check that the backend is running."
                )

            finally:
                api.close()


response = st.session_state.results

if response is not None:
    st.subheader("Search Results")

    metric1, metric2 = st.columns(2)

    metric1.metric(
        "Matching Chunks",
        response["total_results"],
    )

    metric2.metric(
        "Search Duration",
        f'{response["execution_time_ms"]:.0f} ms',
    )

    if not response["results"]:
        st.info(
            "No results found. Try another search phrase "
            "or remove the language/distance filter."
        )

    for index, result in enumerate(
        response["results"], start=1
    ):
        with st.container(border=True):
            st.subheader(
                f'{index}. {result["title"]}'
            )

            st.caption(
                f'Page: {result.get("page") or "N/A"}'
                f' | Language: {result.get("language") or "Unknown"}'
                f' | L2 distance: {result["distance"]:.4f}'
            )

            content = result["content"]

            st.write(content[:450])

            if len(content) > 450:
                with st.expander("View full matching passage"):
                    st.write(content)

            source_url = result.get("source_url")

            if source_url:
                st.link_button(
                    "View Original Source",
                    source_url,
                )
            else:
                st.caption(
                    "Original public URL not available "
                    "in document metadata."
                )

            reference = (
                f'{result["title"]}\n'
                f'Document ID: {result["document_id"]}\n'
                f'Source: {source_url or "Not recorded"}\n'
                f'Page: {result.get("page")}'
            )

            st.code(reference, language=None)

st.divider()
st.caption(
    "Results are retrieved from indexed documents. "
    "They are not AI-generated answers. Verify "
    "current scheme rules with official sources."
)
if st.button("Clear Search Results"):
    st.session_state.results = None
    st.rerun()
