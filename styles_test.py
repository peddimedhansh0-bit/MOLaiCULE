import streamlit as st

from styles import apply_sci_ai_style


st.set_page_config(
    page_title="SciAI",
    page_icon="🧬",
    layout="wide"
)

apply_sci_ai_style()


st.markdown(
    """
    <div class="sci-hero">
        <div class="sci-hero-title">
            🧬 SciAI
        </div>

        <div class="sci-hero-subtitle">
            AI-Augmented Scientific Research Workspace
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown(
    '<div class="sci-section-title">Molecular Profile</div>',
    unsafe_allow_html=True
)


col1, col2, col3, col4 = st.columns(4)


with col1:
    st.markdown(
        """
        <div class="sci-card">
            <div class="sci-label">Molecular Weight</div>
            <div class="sci-value">194.19</div>
            <div class="sci-muted">g/mol</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col2:
    st.markdown(
        """
        <div class="sci-card">
            <div class="sci-label">LogP</div>
            <div class="sci-value-accent">-0.07</div>
            <div class="sci-muted">Calculated</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col3:
    st.markdown(
        """
        <div class="sci-card">
            <div class="sci-label">H-Bond Donors</div>
            <div class="sci-value">0</div>
            <div class="sci-muted">Descriptors</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col4:
    st.markdown(
        """
        <div class="sci-card">
            <div class="sci-label">H-Bond Acceptors</div>
            <div class="sci-value">6</div>
            <div class="sci-muted">Descriptors</div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown(
    """
    <div class="sci-ai-panel">

        <div class="sci-ai-label">
            ✦ AI RESEARCH COPILOT
        </div>

        <h3>
            Computational interpretation
        </h3>

        <p>
            This panel will eventually contain the Gemini-generated
            scientific explanation of your computational results.
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <div class="sci-research-note">

        ⚠️ <strong>Research note</strong><br>

        Rankings reflect descriptor information and computational
        heuristics only; they do not establish experimental validity,
        biological activity, safety, or efficacy.

    </div>
    """,
    unsafe_allow_html=True
)