import streamlit as st
from rdkit import Chem
from rdkit.Chem import Descriptors, Draw
from rdkit.Chem import rdMolDescriptors
from dotenv import load_dotenv
from google import genai
import os
import requests
import time

from compound_screening_main import compound_screening
from stylesmain import apply_molai_cule_style


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="molAIcule",
    page_icon="🧬",
    layout="wide"
)

apply_molai_cule_style()


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# GEMINI SETUP
# ============================================================

api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    client = genai.Client(
        api_key=api_key
    )
else:
    client = None


# ============================================================
# MODULE 1
# MOLECULE ANALYZER
# ============================================================

def molecule_analyzer():

    # ========================================================
    # HEADER
    # ========================================================

    st.title("🧪 molAIcule")
    st.subheader("Molecule Analyzer")
    st.write(
        "Explore molecular structure and computational properties "
        "using RDKit, with AI-assisted scientific interpretation."
    )
    st.caption("● COMPUTATIONAL ANALYSIS")

    # ========================================================
    # USER INPUTS
    # ========================================================

    molecule_name = st.text_input(
        "Enter molecule name",
        placeholder="Example: Caffeine",
        key="module1_molecule_name"
    )

    smiles_input = st.text_input(
        "Or enter SMILES",
        placeholder=(
            "Example: "
            "Cn1c(=O)c2c(ncn2C)n(C)c1=O"
        ),
        key="module1_smiles_input"
    )

    # ========================================================
    # PUBCHEM LOOKUP
    # ========================================================

    def get_smiles_from_pubchem(name):

        try:

            encoded_name = requests.utils.quote(
                name.strip(),
                safe=""
            )

            url = (
                "https://pubchem.ncbi.nlm.nih.gov/rest/pug/"
                f"compound/name/{encoded_name}/property/"
                "CanonicalSMILES/JSON"
            )

            response = requests.get(
                url,
                timeout=10
            )

            if response.status_code == 200:

                data = response.json()

                return (
                    data[
                        "PropertyTable"
                    ][
                        "Properties"
                    ][0][
                        "ConnectivitySMILES"
                    ]
                )

        except Exception:
            pass

        return None

    # ========================================================
    # AI QUESTION
    # ========================================================

    question = st.text_input(
        "Ask a scientific question",
        placeholder=(
            "Example: What are the important "
            "properties of this molecule?"
        ),
        key="module1_question"
    )

    # ========================================================
    # ANALYZE BUTTON
    # ========================================================

    if st.button(
        "Analyze",
        key="module1_analyze"
    ):

        # ----------------------------------------------------
        # Use SMILES directly if provided
        # ----------------------------------------------------

        if smiles_input:

            smiles = smiles_input

        # ----------------------------------------------------
        # Otherwise search PubChem
        # ----------------------------------------------------

        elif molecule_name:

            with st.spinner(
                "Searching PubChem..."
            ):

                smiles = get_smiles_from_pubchem(
                    molecule_name
                )

            if smiles is None:

                st.error(
                    "Molecule not found in PubChem. "
                    "Try another name or enter the "
                    "SMILES directly."
                )

                return

        else:

            st.warning(
                "Please enter a molecule name or SMILES."
            )

            return

        # ----------------------------------------------------
        # Convert SMILES to molecule
        # ----------------------------------------------------

        molecule = Chem.MolFromSmiles(
            smiles
        )

        if molecule is None:

            st.error(
                "Invalid SMILES. "
                "Please check your input."
            )

            return

        # ----------------------------------------------------
        # Molecule recognized
        # ----------------------------------------------------

        st.success(
            "Molecule successfully recognized!"
        )

        # ----------------------------------------------------
        # Calculate molecular properties
        # ----------------------------------------------------

        formula = (
            rdMolDescriptors.CalcMolFormula(
                molecule
            )
        )

        molecular_weight = (
            Descriptors.MolWt(
                molecule
            )
        )

        logp = (
            Descriptors.MolLogP(
                molecule
            )
        )

        h_donors = (
            rdMolDescriptors.CalcNumHBD(
                molecule
            )
        )

        h_acceptors = (
            rdMolDescriptors.CalcNumHBA(
                molecule
            )
        )

        # ----------------------------------------------------
        # Display structure and properties
        # ----------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            st.subheader(
                "Molecular Structure"
            )

            image = Draw.MolToImage(
                molecule
            )

            st.image(
                image
            )

        with col2:

            st.subheader(
                "Molecular Properties"
            )

            st.write(
                f"**Formula:** {formula}"
            )

            st.write(
                f"**Molecular Weight:** "
                f"{molecular_weight:.2f} g/mol"
            )

            st.write(
                f"**LogP:** {logp:.2f}"
            )

            st.write(
                f"**H-Bond Donors:** "
                f"{h_donors}"
            )

            st.write(
                f"**H-Bond Acceptors:** "
                f"{h_acceptors}"
            )

        # ----------------------------------------------------
        # AI RESEARCH ASSISTANT
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "🤖 AI Research Assistant"
        )

        if not question:

            st.info(
                "Enter a question above to ask "
                "the AI about this molecule."
            )

        elif client is None:

            st.error(
                "Gemini API key was not found. "
                "Check your .env file."
            )

        else:

            # ------------------------------------------------
            # Give Gemini actual RDKit results
            # ------------------------------------------------

            prompt = f"""
You are molAIcule, an AI-augmented
scientific research assistant.

Analyze the following computational molecular data.

Molecular formula: {formula}
Molecular weight: {molecular_weight:.2f} g/mol
LogP: {logp:.2f}
Hydrogen bond donors: {h_donors}
Hydrogen bond acceptors: {h_acceptors}

User question:
{question}

Instructions:
1. Explain the result clearly.
2. Base your response on the provided molecular data.
3. Do not invent experimental results.
4. Clearly distinguish calculated information
   from scientific hypotheses.
5. Keep the explanation understandable to
   a college-level science student.
"""

            try:

                response = None

                # ------------------------------------------------
                # Gemini retry logic
                # ------------------------------------------------

                for attempt in range(3):

                    try:

                        response = (
                            client.models.generate_content(
                                model="gemini-3.6-flash",
                                contents=prompt
                            )
                        )

                        break

                    except Exception as e:

                        if (
                            "503" in str(e)
                            and attempt < 2
                        ):

                            time.sleep(
                                2 ** attempt
                            )

                        else:

                            raise e

                st.markdown(
                    "### 🔬 AI Analysis"
                )

                st.write(
                    response.text
                )

            except Exception as e:

                st.error(
                    f"Gemini API error: {e}"
                )


# ============================================================
# molAIcule SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🧬 molAIcule")
    st.caption("Research Copilot")

    st.subheader("WORKSPACE")

    selected_module = st.radio(
        "WORKSPACE",
        [
            "🧪 Molecule Analyzer",
            "🔬 Compound Screening"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.subheader("LIBRARY")
    st.caption("History")
    st.caption("Reports")
    st.divider()
    st.caption("⚙ Settings")
    st.caption("molAIcule • v1.0 MVP")


# ============================================================
# DISPLAY SELECTED MODULE
# ============================================================

if selected_module == "🧪 Molecule Analyzer":

    molecule_analyzer()

elif selected_module == "🔬 Compound Screening":

    compound_screening()