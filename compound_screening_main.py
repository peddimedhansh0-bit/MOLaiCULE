import streamlit as st
import requests
import pandas as pd
import os
import html
from datetime import datetime
from io import BytesIO

from dotenv import load_dotenv
from google import genai

from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem import rdMolDescriptors
from rdkit.Contrib.SA_Score import sascorer

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)
from urllib.parse import quote

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "screening_results" not in st.session_state:
    st.session_state["screening_results"] = None

if "screening_target" not in st.session_state:
    st.session_state["screening_target"] = None

if "screening_goal" not in st.session_state:
    st.session_state["screening_goal"] = ""

if "screening_criteria" not in st.session_state:
    st.session_state["screening_criteria"] = []

if "screening_ai_explanation" not in st.session_state:
    st.session_state["screening_ai_explanation"] = None

if "screening_chat_history" not in st.session_state:
    st.session_state["screening_chat_history"] = []

if "screening_history" not in st.session_state:
    st.session_state["screening_history"] = []


# ============================================================
# PUBCHEM NAME → SMILES
# ============================================================

from urllib.parse import quote

def get_smiles_from_pubchem(name):
    try:
        encoded_name = quote(name.strip())

        url = (
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
            f"{encoded_name}/property/CanonicalSMILES/JSON"
        )

        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        properties = data.get("PropertyTable", {}).get("Properties", [])

        if not properties:
            return None

        return properties[0]["CanonicalSMILES"]

    except Exception as e:
        st.error(f"PubChem lookup failed: {e}")  # temporary for debugging
        return None

# ============================================================
# COMPUTATIONAL INDICATORS
# ============================================================

def calculate_drug_likeness_score(molecule):
    """0-10 rule-based drug-likeness indicator; not drug probability."""
    mw = Descriptors.MolWt(molecule)
    logp = Descriptors.MolLogP(molecule)
    hbd = Descriptors.NumHDonors(molecule)
    hba = Descriptors.NumHAcceptors(molecule)
    tpsa = Descriptors.TPSA(molecule)
    score = 10.0
    if mw > 500:
        score -= min(2.0, (mw - 500) / 250)
    elif mw < 150:
        score -= min(1.5, (150 - mw) / 100)
    if logp > 5:
        score -= min(2.0, (logp - 5) / 2)
    elif logp < -1:
        score -= min(1.5, (-1 - logp) / 2)
    if hbd > 5:
        score -= min(1.5, (hbd - 5) * 0.5)
    if hba > 10:
        score -= min(1.5, (hba - 10) * 0.3)
    if tpsa > 140:
        score -= min(1.5, (tpsa - 140) / 50)
    elif tpsa < 20:
        score -= min(1.0, (20 - tpsa) / 30)
    return round(max(0.0, min(10.0, score)), 1)


def calculate_environmental_hazard_indicator(molecule):
    """0-10 descriptor-only heuristic flag; NOT an ecotoxicity prediction."""
    mw = Descriptors.MolWt(molecule)
    logp = Descriptors.MolLogP(molecule)
    tpsa = Descriptors.TPSA(molecule)
    lipophilicity_component = max(0.0, min(6.0, logp * 1.2))
    polarity_component = 2.0 if tpsa < 40 else (1.0 if tpsa < 80 else 0.0)
    size_component = 1.0 if mw > 500 else (0.5 if mw > 300 else 0.0)
    return round(max(0.0, min(10.0, lipophilicity_component + polarity_component + size_component)), 1)


def calculate_synthetic_accessibility_score(molecule):
    """0-10 ease indicator derived from RDKit's SA score; higher = easier."""
    sa_score = sascorer.calculateScore(molecule)
    ease_score = 10.0 - ((sa_score - 1.0) / 9.0 * 10.0)
    return round(max(0.0, min(10.0, ease_score)), 1)


# ============================================================
# MOLECULE ANALYSIS
# ============================================================

def analyze_molecule(identifier):

    identifier = identifier.strip()

    if not identifier:
        return None

    molecule = None

    # --------------------------------------------------------
    # First try as SMILES
    # --------------------------------------------------------

    molecule = Chem.MolFromSmiles(identifier)

    # --------------------------------------------------------
    # If not SMILES, try PubChem name
    # --------------------------------------------------------

    if molecule is None:

        smiles = get_smiles_from_pubchem(
            identifier   
        )
        
        if smiles:

            molecule = Chem.MolFromSmiles(
                smiles
            )

    # --------------------------------------------------------
    # Invalid molecule
    # --------------------------------------------------------

    if molecule is None:
        return None

    # --------------------------------------------------------
    # Calculate descriptors
    # --------------------------------------------------------

    formula = rdMolDescriptors.CalcMolFormula(
        molecule
    )

    molecular_weight = Descriptors.MolWt(
        molecule
    )

    logp = Descriptors.MolLogP(
        molecule
    )

    hbd = Descriptors.NumHDonors(
        molecule
    )

    hba = Descriptors.NumHAcceptors(
        molecule
    )

    tpsa = Descriptors.TPSA(
        molecule
    )

    rotatable_bonds = Descriptors.NumRotatableBonds(
        molecule
    )

    canonical_smiles = Chem.MolToSmiles(
        molecule
    )

    drug_likeness_score = calculate_drug_likeness_score(molecule)
    environmental_hazard_indicator = calculate_environmental_hazard_indicator(molecule)
    synthetic_accessibility_score = calculate_synthetic_accessibility_score(molecule)

    return {

        "input": identifier,

        "smiles": canonical_smiles,

        "formula": formula,

        "molecular_weight": molecular_weight,

        "logp": logp,

        "hbd": hbd,

        "hba": hba,

        "tpsa": tpsa,

        "rotatable_bonds": rotatable_bonds,

        "drug_likeness_score": drug_likeness_score,

        "environmental_hazard_indicator": environmental_hazard_indicator,

        "synthetic_accessibility_score": synthetic_accessibility_score
    }


# ============================================================
# TARGET-GUIDED SIMILARITY CALCULATION
# ============================================================

def calculate_target_similarity(
    target,
    candidates,
    selected_criteria
):

    # --------------------------------------------------------
    # Calculate maximum difference for each descriptor
    # --------------------------------------------------------

    maximum_differences = {}

    for criterion in selected_criteria:

        differences = []

        for candidate in candidates:

            difference = abs(
                candidate[criterion]
                -
                target[criterion]
            )

            differences.append(
                difference
            )

        maximum_differences[
            criterion
        ] = max(
            differences
        )

    results = []

    # --------------------------------------------------------
    # Calculate candidate scores
    # --------------------------------------------------------

    for candidate in candidates:

        property_scores = {}

        property_differences = {}

        for criterion in selected_criteria:

            difference = abs(
                candidate[criterion]
                -
                target[criterion]
            )

            property_differences[
                criterion
            ] = difference

            maximum_difference = (
                maximum_differences[
                    criterion
                ]
            )

            if maximum_difference == 0:

                score = 100.0

            else:

                score = (
                    100
                    *
                    (
                        1
                        -
                        (
                            difference
                            /
                            maximum_difference
                        )
                    )
                )

                score = max(
                    0,
                    min(
                        100,
                        score
                    )
                )

            property_scores[
                criterion
            ] = score

        # ----------------------------------------------------
        # Overall similarity
        # ----------------------------------------------------

        final_score = sum(
            property_scores.values()
        ) / len(
            property_scores
        )

        results.append({

            "candidate":
                candidate,

            "score":
                final_score,

            "property_scores":
                property_scores,

            "differences":
                property_differences
        })

    # --------------------------------------------------------
    # Highest score first
    # --------------------------------------------------------

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results


# ============================================================
# AI OVERVIEW
# ============================================================

def generate_ai_explanation(
    target,
    screening_results,
    research_goal,
    selected_criteria
):

    if client is None:

        return (
            "⚠️ Gemini AI is not configured.\n\n"
            "Please check your GEMINI_API_KEY "
            "in the .env file."
        )

    # --------------------------------------------------------
    # Target information
    # --------------------------------------------------------

    target_information = f"""
TARGET MOLECULE

Input:
{target["input"]}

Formula:
{target["formula"]}

SMILES:
{target["smiles"]}

Molecular Weight:
{target["molecular_weight"]:.2f}

LogP:
{target["logp"]:.2f}

H-Bond Donors:
{target["hbd"]}

H-Bond Acceptors:
{target["hba"]}

TPSA:
{target["tpsa"]:.2f}

Rotatable Bonds:
{target["rotatable_bonds"]}

Drug-likeness Indicator:
{target["drug_likeness_score"]:.1f}/10

Environmental Hazard Indicator (heuristic):
{target["environmental_hazard_indicator"]:.1f}/10

Synthetic Accessibility / Ease Indicator:
{target["synthetic_accessibility_score"]:.1f}/10
"""

    # --------------------------------------------------------
    # Candidate information
    # --------------------------------------------------------

    candidate_information = ""

    for rank, result in enumerate(
        screening_results,
        start=1
    ):

        candidate = result["candidate"]

        candidate_information += f"""

CANDIDATE RANK #{rank}

Input:
{candidate["input"]}

Formula:
{candidate["formula"]}

SMILES:
{candidate["smiles"]}

Molecular Weight:
{candidate["molecular_weight"]:.2f}

LogP:
{candidate["logp"]:.2f}

H-Bond Donors:
{candidate["hbd"]}

H-Bond Acceptors:
{candidate["hba"]}

TPSA:
{candidate["tpsa"]:.2f}

Rotatable Bonds:
{candidate["rotatable_bonds"]}

Drug-likeness Indicator:
{candidate["drug_likeness_score"]:.1f}/10

Environmental Hazard Indicator (heuristic):
{candidate["environmental_hazard_indicator"]:.1f}/10

Synthetic Accessibility / Ease Indicator:
{candidate["synthetic_accessibility_score"]:.1f}/10

Computational Similarity Score:
{result["score"]:.1f}/100

Descriptor Differences From Target:
"""

        for property_name, difference in (
            result["differences"].items()
        ):

            candidate_information += (
                f"- {property_name}: "
                f"{difference:.2f}\n"
            )

    # --------------------------------------------------------
    # Gemini prompt
    # --------------------------------------------------------

    prompt = f"""
You are an AI scientific research assistant.

You are helping a researcher interpret a computational
molecular screening experiment.

The application calculated molecular descriptors and
similarity scores using RDKit.

Use ONLY the supplied computational data as the factual
basis for your analysis.

Do not invent experimental results.

Do not change or recalculate the screening scores.

============================================================
RESEARCH OBJECTIVE
============================================================

{research_goal}

============================================================
SELECTED COMPARISON CRITERIA
============================================================

{", ".join(selected_criteria)}

============================================================
TARGET
============================================================

{target_information}

============================================================
SCREENING RESULTS
============================================================

{candidate_information}

============================================================
ANALYSIS REQUIREMENTS
============================================================

Structure your answer using these sections:

1. Overall interpretation

Explain what the computational screening indicates.

2. Why the top candidates ranked highly

Use the actual descriptor values and calculated
similarity scores.

3. Important molecular differences

Explain the most important descriptor differences
between the candidates and the target.

4. Candidate trade-offs

Explain situations where one candidate has a better
match for one property but another candidate has a
better match for another property.

5. Research takeaway

Summarize what can reasonably be concluded from
this computational screening.

============================================================
IMPORTANT SCIENTIFIC LIMITATIONS
============================================================

Do NOT claim that a candidate:

- is an effective drug
- is safe
- is toxic
- will bind successfully
- has therapeutic activity
- will work experimentally
- is biologically equivalent to the target
- is the best drug candidate

Computational descriptor similarity is NOT proof of
biological similarity or experimental performance.

Clearly distinguish computational property similarity
from biological activity.

The drug-likeness, environmental-hazard, and synthetic-accessibility
values are heuristic computational indicators, not validated
measurements or predictions. Do not present them as proof that a
molecule is a drug, environmentally hazardous, or easy to synthesize.

Experimental validation, expert scientific review,
and appropriate computational/experimental methods
are required for practical research conclusions.

Use clear scientific language that is understandable
to researchers and students.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text

    except Exception as error:

        error_message = str(error)

        if (
            "503" in error_message
            or
            "UNAVAILABLE"
            in error_message.upper()
        ):

            return (
                "⚠️ Gemini is temporarily unavailable "
                "because the AI service is under high demand. "
                "Please try again in a moment."
            )

        return (
            "⚠️ Gemini could not generate the analysis.\n\n"
            f"Technical message: {error_message}"
        )


# ============================================================
# FOLLOW-UP CHAT RESPONSE
# ============================================================

def generate_followup_response(
    question,
    target,
    screening_results,
    research_goal,
    selected_criteria,
    chat_history
):

    if client is None:

        return (
            "⚠️ Gemini AI is not configured.\n\n"
            "Please check your GEMINI_API_KEY."
        )

    # --------------------------------------------------------
    # Target information
    # --------------------------------------------------------

    target_information = f"""
TARGET MOLECULE

Input:
{target["input"]}

Formula:
{target["formula"]}

SMILES:
{target["smiles"]}

Molecular Weight:
{target["molecular_weight"]:.2f}

LogP:
{target["logp"]:.2f}

H-Bond Donors:
{target["hbd"]}

H-Bond Acceptors:
{target["hba"]}

TPSA:
{target["tpsa"]:.2f}

Rotatable Bonds:
{target["rotatable_bonds"]}

Drug-likeness Indicator:
{target["drug_likeness_score"]:.1f}/10

Environmental Hazard Indicator (heuristic):
{target["environmental_hazard_indicator"]:.1f}/10

Synthetic Accessibility / Ease Indicator:
{target["synthetic_accessibility_score"]:.1f}/10
"""

    # --------------------------------------------------------
    # Candidate information
    # --------------------------------------------------------

    candidate_information = ""

    for rank, result in enumerate(
        screening_results,
        start=1
    ):

        candidate = result["candidate"]

        candidate_information += f"""

CANDIDATE #{rank}

Input:
{candidate["input"]}

Formula:
{candidate["formula"]}

SMILES:
{candidate["smiles"]}

Molecular Weight:
{candidate["molecular_weight"]:.2f}

LogP:
{candidate["logp"]:.2f}

H-Bond Donors:
{candidate["hbd"]}

H-Bond Acceptors:
{candidate["hba"]}

TPSA:
{candidate["tpsa"]:.2f}

Rotatable Bonds:
{candidate["rotatable_bonds"]}

Drug-likeness Indicator:
{candidate["drug_likeness_score"]:.1f}/10

Environmental Hazard Indicator (heuristic):
{candidate["environmental_hazard_indicator"]:.1f}/10

Synthetic Accessibility / Ease Indicator:
{candidate["synthetic_accessibility_score"]:.1f}/10

Computational Similarity Score:
{result["score"]:.1f}/100

Descriptor Differences From Target:
"""

        for property_name, difference in (
            result["differences"].items()
        ):

            candidate_information += (
                f"- {property_name}: "
                f"{difference:.2f}\n"
            )

    # --------------------------------------------------------
    # Previous conversation
    # --------------------------------------------------------

    conversation = ""

    for message in chat_history:

        conversation += (
            f'{message["role"].upper()}: '
            f'{message["content"]}\n\n'
        )

    # --------------------------------------------------------
    # Gemini prompt
    # --------------------------------------------------------

    prompt = f"""
You are an AI scientific research assistant.

You are helping a researcher understand a computational
molecular screening experiment.

The application calculated all molecular descriptors and
similarity scores using RDKit.

Use the supplied data as the factual basis for your answer.

Do not invent experimental results.

Do not change or recalculate the screening scores.

============================================================
RESEARCH OBJECTIVE
============================================================

{research_goal}

============================================================
SELECTED COMPARISON CRITERIA
============================================================

{", ".join(selected_criteria)}

============================================================
TARGET MOLECULE
============================================================

{target_information}

============================================================
SCREENING RESULTS
============================================================

{candidate_information}

============================================================
PREVIOUS CONVERSATION
============================================================

{conversation}

============================================================
CURRENT USER QUESTION
============================================================

{question}

============================================================
INSTRUCTIONS
============================================================

Answer the user's question directly.

Use actual molecular values from the supplied data
whenever relevant.

If the user asks why one candidate ranked above another,
explain the comparison using the calculated descriptors,
descriptor differences, and similarity scores.

If the user asks about a particular property such as
LogP, TPSA, molecular weight, H-bond donors, or
H-bond acceptors, explain what that descriptor means
and how it relates to the current screening.

If the user asks about biological activity, drug efficacy,
toxicity, safety, experimental success, therapeutic effect,
or binding, explain that the current application does not
calculate or establish those properties.

Do not present computational similarity as proof of
biological similarity.

Do not invent mechanisms, experimental findings,
literature results, or laboratory observations.

Do not claim that a candidate is the "best drug",
"most effective drug", or experimentally superior.

Keep the answer useful for a scientific researcher
while making it understandable.

============================================================
SCIENTIFIC LIMITATION
============================================================

These results are computational molecular-descriptor
measurements.

The drug-likeness, environmental-hazard, and synthetic-accessibility
values are heuristic computational indicators, not validated
measurements or predictions.

Experimental validation and expert scientific review
are required before drawing practical biochemical,
medical, or experimental conclusions.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text

    except Exception as error:

        error_message = str(error)

        if (
            "503" in error_message
            or
            "UNAVAILABLE"
            in error_message.upper()
        ):

            return (
                "⚠️ Gemini is temporarily unavailable "
                "because the AI service is under high demand. "
                "Please try again in a moment."
            )

        return (
            "⚠️ Gemini could not answer the question.\n\n"
            f"Technical message: {error_message}"
        )


# ============================================================
# PDF REPORT GENERATOR
# ============================================================

def create_pdf_report(
    target,
    screening_results,
    research_goal,
    selected_criteria,
    ai_explanation,
    chat_history
):

    buffer = BytesIO()

    document = SimpleDocTemplate(

        buffer,

        pagesize=A4,

        rightMargin=40,

        leftMargin=40,

        topMargin=40,

        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=20
    )

    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        spaceAfter=7
    )

    small_style = ParagraphStyle(
        "ReportSmall",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        spaceAfter=5
    )

    story = []

    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        Paragraph(
            "molAIcule - Computational Molecular Screening Report",
            title_style
        )
    )

    story.append(
        Paragraph(
            f"Generated: "
            f"{datetime.now().strftime('%d %B %Y, %I:%M %p')}",
            small_style
        )
    )

    story.append(
        Spacer(
            1,
            10
        )
    )

    # ========================================================
    # RESEARCH OBJECTIVE
    # ========================================================

    story.append(
        Paragraph(
            "1. Research Objective",
            heading_style
        )
    )

    objective_text = (
        research_goal
        if research_goal.strip()
        else
        "No research objective was specified."
    )

    story.append(
        Paragraph(
            html.escape(objective_text).replace(
                "\n",
                "<br/>"
            ),
            body_style
        )
    )

    # ========================================================
    # TARGET MOLECULE
    # ========================================================

    story.append(
        Paragraph(
            "2. Target Molecule",
            heading_style
        )
    )

    target_data = [

        ["Property", "Value"],

        ["Input", target["input"]],

        ["Formula", target["formula"]],

        ["SMILES", target["smiles"]],

        [
            "Molecular Weight",
            f'{target["molecular_weight"]:.2f}'
        ],

        [
            "LogP",
            f'{target["logp"]:.2f}'
        ],

        [
            "H-Bond Donors",
            str(target["hbd"])
        ],

        [
            "H-Bond Acceptors",
            str(target["hba"])
        ],

        [
            "TPSA",
            f'{target["tpsa"]:.2f}'
        ],

        [
            "Rotatable Bonds",
            str(target["rotatable_bonds"])
        ],
        [
            "Drug-likeness Indicator (heuristic)",
            f'{target["drug_likeness_score"]:.1f}/10'
        ],
        [
            "Environmental Hazard Indicator (heuristic)",
            f'{target["environmental_hazard_indicator"]:.1f}/10'
        ],
        [
            "Synthetic Accessibility / Ease Indicator",
            f'{target["synthetic_accessibility_score"]:.1f}/10'
        ]
    ]

    target_table = Table(
        target_data,
        colWidths=[
            2.0 * inch,
            4.5 * inch
        ]
    )

    target_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#eeeeee")
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )

    story.append(
        target_table
    )

    # ========================================================
    # CRITERIA
    # ========================================================

    story.append(
        Paragraph(
            "3. Selected Comparison Criteria",
            heading_style
        )
    )

    criteria_text = ", ".join(
        selected_criteria
    )

    story.append(
        Paragraph(
            html.escape(criteria_text),
            body_style
        )
    )

    # ========================================================
    # SCREENING RESULTS
    # ========================================================

    story.append(
        Paragraph(
            "4. Computational Screening Results",
            heading_style
        )
    )

    result_data = [

        [
            "Rank",
            "Candidate",
            "MW",
            "LogP",
            "HBD",
            "HBA",
            "TPSA",
            "Drug-like",
            "Env. Hazard",
            "Synthesis Ease",
            "Score"
        ]
    ]

    for rank, result in enumerate(
        screening_results,
        start=1
    ):

        candidate = result["candidate"]

        result_data.append([

            str(rank),

            candidate["input"],

            f'{candidate["molecular_weight"]:.2f}',

            f'{candidate["logp"]:.2f}',

            str(candidate["hbd"]),

            str(candidate["hba"]),

            f'{candidate["tpsa"]:.2f}',

            f'{candidate["drug_likeness_score"]:.1f}',

            f'{candidate["environmental_hazard_indicator"]:.1f}',

            f'{candidate["synthetic_accessibility_score"]:.1f}',

            f'{result["score"]:.1f}'
        ])

    result_table = Table(
        result_data,
        repeatRows=1
    )

    result_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#eeeeee")
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            )
        ])
    )

    story.append(
        result_table
    )

    # ========================================================
    # DETAILED DIFFERENCES
    # ========================================================

    story.append(
        Paragraph(
            "5. Descriptor Differences",
            heading_style
        )
    )

    for rank, result in enumerate(
        screening_results,
        start=1
    ):

        candidate = result["candidate"]

        story.append(
            Paragraph(
                f'<b>Rank {rank}: '
                f'{html.escape(candidate["input"])}</b>',
                body_style
            )
        )

        difference_data = [
            ["Property", "Difference"]
        ]

        for (
            property_name,
            difference
        ) in result["differences"].items():

            difference_data.append([

                property_name,

                f"{difference:.2f}"
            ])

        difference_table = Table(
            difference_data,
            colWidths=[
                3.0 * inch,
                2.0 * inch
            ]
        )

        difference_table.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#eeeeee")
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8
                )
            ])
        )

        story.append(
            difference_table
        )

        story.append(
            Spacer(
                1,
                8
            )
        )

    # ========================================================
    # AI ANALYSIS
    # ========================================================

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "6. AI Research Analysis",
            heading_style
        )
    )

    if ai_explanation:

        # Convert basic Markdown formatting into
        # simple PDF-friendly formatting.

        ai_text = html.escape(
            ai_explanation
        )

        ai_text = ai_text.replace(
            "\n\n",
            "<br/><br/>"
        )

        ai_text = ai_text.replace(
            "\n",
            "<br/>"
        )

        story.append(
            Paragraph(
                ai_text,
                body_style
            )
        )

    # ========================================================
    # CHAT HISTORY
    # ========================================================

    if chat_history:

        story.append(
            Paragraph(
                "7. AI Research Copilot Conversation",
                heading_style
            )
        )

        for message in chat_history:

            role = (
                "Researcher"
                if message["role"] == "user"
                else
                "AI Research Copilot"
            )

            content = html.escape(
                message["content"]
            )

            content = content.replace(
                "\n",
                "<br/>"
            )

            story.append(
                Paragraph(
                    f"<b>{role}:</b><br/>{content}",
                    body_style
                )
            )

    # ========================================================
    # SCIENTIFIC LIMITATIONS
    # ========================================================

    story.append(
        Paragraph(
            "8. Scientific Limitations",
            heading_style
        )
    )

    limitations = """
This report contains computational molecular-descriptor
measurements and AI-assisted interpretation.

Similarity scores are based on the selected molecular
descriptors and should not be interpreted as proof of
biological similarity, biological activity, binding
affinity, therapeutic efficacy, safety, toxicity, or
experimental success.

Drug-likeness, environmental-hazard, and synthetic-accessibility
values are heuristic computational indicators and are not
validated measurements of drug status, ecotoxicity, or
laboratory synthesis feasibility.

Experimental validation, appropriate computational
methods, and expert scientific review are required
before drawing practical biochemical or medical
conclusions.
"""

    story.append(
        Paragraph(
            limitations.replace(
                "\n",
                "<br/>"
            ),
            body_style
        )
    )

    # ========================================================
    # FOOTER
    # ========================================================

    story.append(
        Spacer(
            1,
            20
        )
    )

    story.append(
        Paragraph(
            "Generated by molAIcule Computational Research Platform",
            small_style
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(
        story
    )

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# SAVE SCREENING TO HISTORY
# ============================================================

def save_to_history():

    target = st.session_state[
        "screening_target"
    ]

    results = st.session_state[
        "screening_results"
    ]

    if (
        target is None
        or
        results is None
    ):
        return

    history_item = {

        "timestamp":
            datetime.now().strftime(
                "%d %b %Y, %I:%M %p"
            ),

        "target":
            target,

        "results":
            results,

        "research_goal":
            st.session_state[
                "screening_goal"
            ],

        "criteria":
            st.session_state[
                "screening_criteria"
            ],

        "ai_explanation":
            st.session_state[
                "screening_ai_explanation"
            ],

        "chat_history":
            list(
                st.session_state[
                    "screening_chat_history"
                ]
            )
    }

    # --------------------------------------------------------
    # Add newest analysis to beginning
    # --------------------------------------------------------

    st.session_state[
        "screening_history"
    ].insert(
        0,
        history_item
    )

    # --------------------------------------------------------
    # Keep only latest 20
    # --------------------------------------------------------

    st.session_state[
        "screening_history"
    ] = (
        st.session_state[
            "screening_history"
        ][:20]
    )


# ============================================================
# LOAD HISTORY ITEM
# ============================================================

def load_history_item(index):

    history_item = (
        st.session_state[
            "screening_history"
        ][index]
    )

    st.session_state[
        "screening_target"
    ] = history_item[
        "target"
    ]

    st.session_state[
        "screening_results"
    ] = history_item[
        "results"
    ]

    st.session_state[
        "screening_goal"
    ] = history_item[
        "research_goal"
    ]

    st.session_state[
        "screening_criteria"
    ] = history_item[
        "criteria"
    ]

    st.session_state[
        "screening_ai_explanation"
    ] = history_item[
        "ai_explanation"
    ]

    st.session_state[
        "screening_chat_history"
    ] = list(
        history_item[
            "chat_history"
        ]
    )


# ============================================================
# SIDEBAR HISTORY
# ============================================================

def render_screening_history_sidebar():
    if "screening_history" not in st.session_state:
     st.session_state["screening_history"] = []

    if "screening_chat_history" not in st.session_state:
        st.session_state["screening_chat_history"] = []

    if "screening_results" not in st.session_state:
        st.session_state["screening_results"] = None

    if "screening_target" not in st.session_state:
        st.session_state["screening_target"] = None

    if "screening_goal" not in st.session_state:
        st.session_state["screening_goal"] = ""

    if "screening_criteria" not in st.session_state:
        st.session_state["screening_criteria"] = []

    if "screening_ai_explanation" not in st.session_state:
        st.session_state["screening_ai_explanation"] = None

    with st.sidebar:

        st.title(
            "🕘 Screening History"
        )

        st.caption(
            "Your recent computational screening analyses."
        )

        history = st.session_state[
            "screening_history"
        ]

        if not history:

            st.info(
                "No previous screenings yet.\n\n"
                "Run a screening to create your first "
                "history entry."
            )

        else:

            for index, item in enumerate(
                history
            ):

                target_name = item[
                    "target"
                ][
                    "input"
                ]

                results = item[
                    "results"
                ]

                if results:

                    top_candidate = results[0][
                        "candidate"
                    ][
                        "input"
                    ]

                    score = results[0][
                        "score"
                    ]

                else:

                    top_candidate = "N/A"

                    score = 0

                button_text = (
                    f"🧪 {target_name}\n"
                    f"📅 {item['timestamp']}\n"
                    f"Top: {top_candidate} "
                    f"({score:.1f})"
                )

                if st.button(
                    button_text,
                    key=f"history_button_{index}",
                    use_container_width=True
                ):

                    load_history_item(
                        index
                    )

                    st.rerun()

            st.divider()

            if st.button(
                "🗑️ Clear History",
                use_container_width=True
            ):

                st.session_state[
                    "screening_history"
                ] = []

                st.rerun()


# ============================================================
# MAIN COMPOUND SCREENING APPLICATION
# ============================================================

def compound_screening():

    render_screening_history_sidebar()

    # ========================================================
    # HEADER
    # ========================================================

    st.title(
        "🧪 Target-Guided Compound Screening"
    )

    st.write(
        "Compare candidate molecules against a target "
        "using computational molecular descriptors and "
        "AI-assisted interpretation."
    )

    st.info(
        "This tool performs computational molecular "
        "screening. Similarity scores do not establish "
        "biological activity, drug efficacy, safety, "
        "toxicity, or experimental suitability."
    )

    # ========================================================
    # TARGET MOLECULE
    # ========================================================

    st.header(
        "🎯 1. Define Your Target"
    )

    target_input = st.text_input(
        "Target molecule name or SMILES",
        placeholder="Example: ATP or a valid SMILES"
    )

    research_goal = st.text_area(
        "Research objective",
        placeholder=(
            "Example: Compare candidate molecules "
            "with the target based on selected "
            "physicochemical properties."
        ),
        height=100
    )

    # ========================================================
    # CANDIDATE MOLECULES
    # ========================================================

    st.header(
        "🧪 2. Enter Candidate Compounds"
    )

    st.write(
        "Enter between 5 and 10 molecule names or SMILES."
    )

    candidate_inputs = []

    for i in range(10):

        value = st.text_input(
            f"Candidate {i + 1}",
            key=f"candidate_input_{i}",
            placeholder="Molecule name or SMILES"
        )

        if value.strip():

            candidate_inputs.append(
                value.strip()
            )

    # ========================================================
    # COMPARISON CRITERIA
    # ========================================================

    st.header(
        "🔬 3. Select Comparison Criteria"
    )

    selected_criteria = st.multiselect(

        "Properties used for computational similarity",

        options=[

            "molecular_weight",

            "logp",

            "hbd",

            "hba",

            "tpsa"
        ],

        default=[

            "molecular_weight",

            "logp",

            "hbd",

            "hba",

            "tpsa"
        ],

        format_func=lambda x: {

            "molecular_weight":
                "Molecular Weight",

            "logp":
                "LogP",

            "hbd":
                "H-Bond Donors",

            "hba":
                "H-Bond Acceptors",

            "tpsa":
                "TPSA"

        }[x]
    )

    # ========================================================
    # RUN SCREENING
    # ========================================================

    run_screening = st.button(
        "🔬 Run Target-Guided Screening",
        type="primary",
        use_container_width=True
    )

    if run_screening:

        # ----------------------------------------------------
        # Clear current result
        # ----------------------------------------------------

        st.session_state[
            "screening_results"
        ] = None

        st.session_state[
            "screening_target"
        ] = None

        st.session_state[
            "screening_ai_explanation"
        ] = None

        st.session_state[
            "screening_chat_history"
        ] = []

        # ----------------------------------------------------
        # Validate target
        # ----------------------------------------------------

        if not target_input.strip():

            st.error(
                "Please enter a target molecule."
            )

            return

        # ----------------------------------------------------
        # Validate candidates
        # ----------------------------------------------------

        if len(candidate_inputs) < 5:

            st.error(
                "Please enter at least 5 candidate compounds."
            )

            return

        if len(candidate_inputs) > 10:

            st.error(
                "Please enter no more than 10 candidates."
            )

            return

        # ----------------------------------------------------
        # Validate criteria
        # ----------------------------------------------------

        if not selected_criteria:

            st.error(
                "Please select at least one "
                "comparison criterion."
            )

            return

        # ----------------------------------------------------
        # Analyze target
        # ----------------------------------------------------

        with st.spinner(
            "Analyzing target molecule..."
        ):

            target = analyze_molecule(
                target_input
            )

        if target is None:

            st.error(
                "Could not identify the target molecule. "
                "Please check the name or SMILES."
            )

            return

        # ----------------------------------------------------
        # Analyze candidates
        # ----------------------------------------------------

        candidates = []

        progress = st.progress(
            0
        )

        for index, candidate_input in enumerate(
            candidate_inputs
        ):

            candidate = analyze_molecule(
                candidate_input
            )

            if candidate is None:

                st.warning(
                    f"Could not identify candidate: "
                    f"{candidate_input}"
                )

                continue

            candidates.append(
                candidate
            )

            progress.progress(
                (index + 1)
                /
                len(candidate_inputs)
            )

        progress.empty()

        # ----------------------------------------------------
        # Validate candidates
        # ----------------------------------------------------

        if len(candidates) < 2:

            st.error(
                "Not enough valid candidate molecules "
                "were identified."
            )

            return

        # ----------------------------------------------------
        # Calculate screening
        # ----------------------------------------------------

        with st.spinner(
            "Calculating molecular similarity..."
        ):

            screening_results = (
                calculate_target_similarity(

                    target,

                    candidates,

                    selected_criteria
                )
            )

        # ----------------------------------------------------
        # Save results to session state
        # ----------------------------------------------------

        st.session_state[
            "screening_target"
        ] = target

        st.session_state[
            "screening_results"
        ] = screening_results

        st.session_state[
            "screening_goal"
        ] = research_goal

        st.session_state[
            "screening_criteria"
        ] = selected_criteria

        # ----------------------------------------------------
        # Generate AI overview
        # ----------------------------------------------------

        with st.spinner(
            "Gemini is analyzing the screening results..."
        ):

            explanation = generate_ai_explanation(

                target=target,

                screening_results=screening_results,

                research_goal=research_goal,

                selected_criteria=selected_criteria
            )

        st.session_state[
            "screening_ai_explanation"
        ] = explanation

        # ----------------------------------------------------
        # Save this screening to history
        # ----------------------------------------------------

        save_to_history()

        st.success(
            "Screening completed successfully!"
        )

    # ========================================================
    # RETRIEVE CURRENT RESULTS
    # ========================================================

    target = st.session_state[
        "screening_target"
    ]

    screening_results = st.session_state[
        "screening_results"
    ]

    saved_research_goal = st.session_state[
        "screening_goal"
    ]

    saved_selected_criteria = st.session_state[
        "screening_criteria"
    ]

    ai_explanation = st.session_state[
        "screening_ai_explanation"
    ]

    # ========================================================
    # SHOW RESULTS
    # ========================================================

    if (
        target is not None
        and
        screening_results is not None
    ):

        st.divider()

        # ====================================================
        # TARGET SUMMARY
        # ====================================================

        st.header(
            "🎯 Target Molecule"
        )

        target_col1, target_col2, target_col3 = (
            st.columns(3)
        )

        with target_col1:

            st.metric(
                "Formula",
                target["formula"]
            )

        with target_col2:

            st.metric(
                "Molecular Weight",
                f'{target["molecular_weight"]:.2f}'
            )

        with target_col3:

            st.metric(
                "LogP",
                f'{target["logp"]:.2f}'
            )

        st.write(
            f'**SMILES:** `{target["smiles"]}`'
        )

        # ====================================================
        # TOP 3
        # ====================================================

        st.header(
            "🏆 Top Computational Matches"
        )

        top_results = screening_results[:3]

        metric_columns = st.columns(
            len(top_results)
        )

        for index, result in enumerate(
            top_results
        ):

            candidate = result[
                "candidate"
            ]

            with metric_columns[index]:

                st.metric(
                    f"Rank {index + 1}",
                    candidate["input"],
                    f'{result["score"]:.1f}/100'
                )

        # ====================================================
        # COMPARISON TABLE
        # ====================================================

        st.header(
            "📊 Candidate Comparison"
        )

        table_data = []

        for rank, result in enumerate(
            screening_results,
            start=1
        ):

            candidate = result[
                "candidate"
            ]

            table_data.append({

                "Rank":
                    rank,

                "Candidate":
                    candidate["input"],

                "Formula":
                    candidate["formula"],

                "Molecular Weight":
                    round(
                        candidate[
                            "molecular_weight"
                        ],
                        2
                    ),

                "LogP":
                    round(
                        candidate[
                            "logp"
                        ],
                        2
                    ),

                "HBD":
                    candidate["hbd"],

                "HBA":
                    candidate["hba"],

                "TPSA":
                    round(
                        candidate[
                            "tpsa"
                        ],
                        2
                    ),

                "Drug-likeness /10":
                    candidate["drug_likeness_score"],

                "Environmental Hazard /10":
                    candidate["environmental_hazard_indicator"],

                "Synthetic Ease /10":
                    candidate["synthetic_accessibility_score"],

                "Similarity Score":
                    round(
                        result["score"],
                        1
                    )
            })

        comparison_df = pd.DataFrame(
            table_data
        )

        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Indicator scales: Drug-likeness 0-10 (higher = more drug-like by this heuristic); "
            "Environmental Hazard 0-10 (higher = stronger heuristic hazard flag); "
            "Synthetic Ease 0-10 (higher = computationally easier according to the SA heuristic)."
        )

        st.warning(
            "⚠️ These three 0-10 indicators are computational heuristics, not experimental measurements. "
            "Drug-likeness is not a probability of being a drug; environmental hazard is not a validated ecotoxicity assessment; "
            "and synthetic ease is not a laboratory synthesis guarantee."
        )

        # ====================================================
        # DETAILED CANDIDATE RESULTS
        # ====================================================

        st.header(
            "🔎 Detailed Candidate Analysis"
        )

        for rank, result in enumerate(
            screening_results,
            start=1
        ):

            candidate = result[
                "candidate"
            ]

            with st.expander(

                f"Rank {rank}: "
                f'{candidate["input"]} '
                f'— {result["score"]:.1f}/100'

            ):

                detail_col1, detail_col2 = (
                    st.columns(2)
                )

                with detail_col1:

                    st.write(
                        f'**Formula:** '
                        f'{candidate["formula"]}'
                    )

                    st.write(
                        f'**SMILES:** '
                        f'`{candidate["smiles"]}`'
                    )

                    st.write(
                        f'**Molecular Weight:** '
                        f'{candidate["molecular_weight"]:.2f}'
                    )

                    st.write(
                        f'**LogP:** '
                        f'{candidate["logp"]:.2f}'
                    )

                with detail_col2:

                    st.write(
                        f'**H-Bond Donors:** '
                        f'{candidate["hbd"]}'
                    )

                    st.write(
                        f'**H-Bond Acceptors:** '
                        f'{candidate["hba"]}'
                    )

                    st.write(
                        f'**TPSA:** '
                        f'{candidate["tpsa"]:.2f}'
                    )

                    st.write(
                        f'**Rotatable Bonds:** '
                        f'{candidate["rotatable_bonds"]}'
                    )

                    st.write(
                        f'**Drug-likeness Indicator:** '
                        f'{candidate["drug_likeness_score"]:.1f}/10'
                    )

                    st.write(
                        f'**Environmental Hazard Indicator:** '
                        f'{candidate["environmental_hazard_indicator"]:.1f}/10'
                    )

                    st.write(
                        f'**Synthetic Accessibility / Ease:** '
                        f'{candidate["synthetic_accessibility_score"]:.1f}/10'
                    )

                st.write(
                    "**Descriptor differences from target:**"
                )

                difference_table = []

                for (
                    property_name,
                    difference
                ) in result[
                    "differences"
                ].items():

                    difference_table.append({

                        "Property":
                            property_name,

                        "Difference":
                            round(
                                difference,
                                2
                            )
                    })

                st.dataframe(

                    pd.DataFrame(
                        difference_table
                    ),

                    use_container_width=True,

                    hide_index=True
                )

        st.info(
            "📌 **Scientific disclaimer:** Ranking reflects only descriptor information and computational heuristics, not experimental validity. "
            "The displayed indicators do not establish drug efficacy, safety, environmental toxicity, or laboratory synthesis feasibility."
        )

        # ====================================================
        # AI OVERVIEW
        # ====================================================

        st.divider()

        st.header(
            "🤖 AI Research Analysis"
        )

        if ai_explanation:

            st.markdown(
                ai_explanation
            )

        st.caption(
            "AI-generated interpretation based on the "
            "computational molecular descriptors calculated "
            "by this application. It is not a substitute "
            "for experimental validation or expert "
            "scientific review."
        )

        # ====================================================
        # DOWNLOAD REPORT
        # ====================================================

        st.divider()

        st.header(
            "📥 Download Research Report"
        )

        st.write(
            "Download the complete computational screening "
            "analysis as a PDF report."
        )

        pdf_data = create_pdf_report(

            target=
                target,

            screening_results=
                screening_results,

            research_goal=
                saved_research_goal,

            selected_criteria=
                saved_selected_criteria,

            ai_explanation=
                ai_explanation,

            chat_history=
                st.session_state[
                    "screening_chat_history"
                ]
        )

        safe_target_name = (
            target["input"]
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
        )

        st.download_button(

            label=
                "📄 Download Complete PDF Report",

            data=
                pdf_data,

            file_name=
                f"molAIcule_Report_{safe_target_name}.pdf",

            mime=
                "application/pdf",

            use_container_width=True
        )

        # ====================================================
        # FOLLOW-UP AI CHAT
        # ====================================================

        st.divider()

        st.header(
            "💬 Ask the AI Research Copilot"
        )

        st.write(
            "Ask follow-up questions about the target, "
            "candidate compounds, molecular properties, "
            "or the computational ranking."
        )

        st.info(
            "The AI Research Copilot is grounded in the "
            "current screening results and the previous "
            "conversation."
        )

        # ----------------------------------------------------
        # CLEAR CHAT
        # ----------------------------------------------------

        clear_chat_col1, clear_chat_col2 = (
            st.columns([5, 1])
        )

        with clear_chat_col2:

            if st.button(
                "🗑️ Clear Chat",
                use_container_width=True
            ):

                st.session_state[
                    "screening_chat_history"
                ] = []

                st.rerun()

        # ----------------------------------------------------
        # DISPLAY PREVIOUS CHAT
        # ----------------------------------------------------

        for message in st.session_state[
            "screening_chat_history"
        ]:

            with st.chat_message(
                message["role"]
            ):

                st.markdown(
                    message["content"]
                )

        # ----------------------------------------------------
        # CHAT INPUT
        # ----------------------------------------------------

        user_question = st.chat_input(
            "Ask a follow-up question about your screening..."
        )

        if user_question:

            # ------------------------------------------------
            # Display user message
            # ------------------------------------------------

            with st.chat_message(
                "user"
            ):

                st.markdown(
                    user_question
                )

            # ------------------------------------------------
            # Save user message
            # ------------------------------------------------

            st.session_state[
                "screening_chat_history"
            ].append({

                "role":
                    "user",

                "content":
                    user_question
            })

            # ------------------------------------------------
            # Previous conversation
            # ------------------------------------------------

            previous_conversation = (
                st.session_state[
                    "screening_chat_history"
                ][:-1]
            )

            # ------------------------------------------------
            # Generate AI response
            # ------------------------------------------------

            with st.chat_message(
                "assistant"
            ):

                with st.spinner(
                    "🧠 AI Research Copilot is thinking..."
                ):

                    answer = generate_followup_response(

                        question=
                            user_question,

                        target=
                            target,

                        screening_results=
                            screening_results,

                        research_goal=
                            saved_research_goal,

                        selected_criteria=
                            saved_selected_criteria,

                        chat_history=
                            previous_conversation
                    )

                st.markdown(
                    answer
                )

            # ------------------------------------------------
            # Save AI response
            # ------------------------------------------------

            st.session_state[
                "screening_chat_history"
            ].append({

                "role":
                    "assistant",

                "content":
                    answer
            })

            # ------------------------------------------------
            # Update latest history item with chat
            # ------------------------------------------------

            if st.session_state[
                "screening_history"
            ]:

                st.session_state[
                    "screening_history"
                ][0][
                    "chat_history"
                ] = list(
                    st.session_state[
                        "screening_chat_history"
                    ]
                )


