import os
import uuid
import asyncio
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from agents import (
    Agent,
    Runner,
    WebSearchTool,
    function_tool,
    handoff,
    trace,
)
from pydantic import BaseModel
import PyPDF2

# Load environment variables
load_dotenv()

# Set up page configuration
st.set_page_config(
    page_title="Enhanced Research Assistant",
    page_icon="📚",
    layout="wide",
)

# Check API key
if not os.environ.get("OPENAI_API_KEY"):
    st.error("Please set your OPENAI_API_KEY environment variable")
    st.stop()

st.title("📚 Enhanced Research Assistant")
st.markdown("---")


# DATA MODELS
class ResearchGaps(BaseModel):
    gaps: list[str]
    improvements: list[str]
    areas_to_expand: list[str]


class ResearchPlan(BaseModel):
    topic: str
    search_queries: list[str]
    focus_areas: list[str]


class ResearchReport(BaseModel):
    title: str
    outline: list[str]
    report: str
    sources: list[str]
    word_count: int


class Comparison(BaseModel):
    original_summary: str
    improvements_made: list[str]
    quality_assessment: str
    depth_increase: str
    new_insights: list[str]


# UTILITY FUNCTIONS
def extract_pdf_text(pdf_file):
    """Extract text from uploaded PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error extracting PDF: {str(e)}")
        return None


def extract_text_file(text_file):
    """Extract text from uploaded text file"""
    try:
        return text_file.read().decode("utf-8")
    except Exception as e:
        st.error(f"Error reading text file: {str(e)}")
        return None


# CUSTOM TOOLS
@function_tool
def save_important_fact(fact: str, source: str = None) -> str:
    """Save an important fact discovered during research"""
    if "collected_facts" not in st.session_state:
        st.session_state.collected_facts = []
    st.session_state.collected_facts.append(
        {
            "fact": fact,
            "source": source or "Not specified",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
    )
    return f"Fact saved: {fact}"


# DEFINE AGENTS
gap_analysis_agent = Agent(
    name="Gap Analysis Agent",
    instructions="""You are a research analyst. Given a research document and a research query, you will:
    1. Identify gaps in the existing research
    2. List areas that need more depth
    3. Suggest improvements and expansions
    
    Be specific and actionable. Return your findings in a structured format.""",
    model="gpt-4o-mini",
    output_type=ResearchGaps,
)

planning_agent = Agent(
    name="Research Planning Agent",
    instructions="""You are a research coordinator. Based on the research topic and any gaps identified:
    1. Create specific search queries to fill the gaps
    2. Define key focus areas
    3. Structure the research approach
    
    Provide 3-5 targeted search queries and focus areas.""",
    model="gpt-4o-mini",
    output_type=ResearchPlan,
)

research_agent = Agent(
    name="Research Agent",
    instructions="""You are a research assistant. Search the web for your assigned queries.
    Produce concise 2-3 paragraph summaries (less than 300 words) of the results.
    Focus on main points, be succinct. Ignore fluff.
    This will be used to build a comprehensive report.""",
    model="gpt-4o-mini",
    tools=[WebSearchTool(), save_important_fact],
)

editor_agent = Agent(
    name="Editor Agent",
    instructions="""You are a senior researcher. Write a comprehensive research report based on:
    1. The original research query
    2. Research findings from the Research Agent
    
    Create a detailed, well-structured report in markdown.
    Aim for 5-10 pages, at least 1500 words.
    Use clear sections, headings, and formatting.""",
    model="gpt-4o-mini",
    output_type=ResearchReport,
)

comparison_agent = Agent(
    name="Comparison Agent",
    instructions="""You are a research analyst comparing two research documents.
    Given the original research and the new research:
    1. Summarize the original research
    2. List specific improvements made
    3. Assess quality increase
    4. Highlight new insights found
    
    Be objective and detailed in your comparison.""",
    model="gpt-4o-mini",
    output_type=Comparison,
)

# SESSION STATE INITIALIZATION
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4().hex[:16])
if "collected_facts" not in st.session_state:
    st.session_state.collected_facts = []
if "research_done" not in st.session_state:
    st.session_state.research_done = False
if "report_result" not in st.session_state:
    st.session_state.report_result = None
if "original_content" not in st.session_state:
    st.session_state.original_content = None
if "comparison_result" not in st.session_state:
    st.session_state.comparison_result = None
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "step_completed" not in st.session_state:
    st.session_state.step_completed = {
        "upload": False,
        "planning": False,
        "research": False,
        "report": False,
        "comparison": False,
    }

# ============================================================================
# INPUT SECTION - BEFORE TABS
# ============================================================================
st.subheader("📄 Step 1: Upload Source Material (Optional)")
st.markdown("Upload an existing research document to compare against new research.")

uploaded_file = st.file_uploader(
    "Choose a PDF or TXT file",
    type=["pdf", "txt"],
    help="Upload existing research to compare against",
    key="file_uploader",
)

if uploaded_file:
    st.session_state.step_completed["upload"] = True
    st.success(f"✅ {uploaded_file.name} uploaded")

st.subheader("🔍 Step 2: Enter Your Research Topic")

research_query = st.text_input(
    "What do you want to research?",
    placeholder="e.g., Latest developments in quantum computing",
    value=st.session_state.get("quick_example", ""),
)

start_button = st.button(
    "Start Research",
    type="primary",
    use_container_width=True,
    disabled=not research_query,
)

st.subheader("💡 Example Topics")
example_cols = st.columns(3)
with example_cols[0]:
    if st.button("🚀 Quantum Computing 2024-2025", use_container_width=True):
        st.session_state.quick_example = (
            "Latest developments in quantum computing 2024-2025"
        )
        st.rerun()
with example_cols[1]:
    if st.button("🌍 Climate Tech Solutions", use_container_width=True):
        st.session_state.quick_example = "Innovative climate technology solutions"
        st.rerun()
with example_cols[2]:
    if st.button("🤖 AI in Healthcare", use_container_width=True):
        st.session_state.quick_example = "Applications of AI in healthcare diagnostics"
        st.rerun()

if "quick_example" in st.session_state and st.session_state.quick_example:
    del st.session_state.quick_example

st.markdown("---")


# ============================================================================
# MAIN RESEARCH WORKFLOW
# ============================================================================
async def run_research(query, original_content=None):
    """Main research workflow"""
    st.session_state.collected_facts = []
    st.session_state.research_done = False
    st.session_state.report_result = None
    st.session_state.comparison_result = None

    with trace("Enhanced Research", group_id=st.session_state.conversation_id):
        # ====================================================================
        # STEP 1: Analyze existing research (if provided)
        # ====================================================================
        if original_content:
            st.write("### 📊 Step 1: Analyzing Existing Research")

            gap_prompt = f"""Original Research Content:
{original_content}
Research Query: {query}
Analyze this research for gaps and improvements needed."""

            try:
                gap_result = await Runner.run(gap_analysis_agent, gap_prompt)
                gaps_data = (
                    gap_result.final_output
                    if hasattr(gap_result.final_output, "gaps")
                    else None
                )

                if gaps_data:
                    st.write("**🔍 Research Gaps Found:**")
                    for gap in gaps_data.gaps:
                        st.write(f"• {gap}")
                    st.write("**💡 Improvement Areas:**")
                    for imp in gaps_data.improvements:
                        st.write(f"• {imp}")
            except Exception as e:
                st.error(f"Error in gap analysis: {str(e)}")
                return

        # ====================================================================
        # STEP 2: Plan research
        # ====================================================================
        st.write("### 📋 Step 2: Planning Research")

        if original_content:
            plan_prompt = f"""Research Query: {query}
Gaps to fill: {gap_result.final_output if gaps_data else 'General research needed'}
Create a research plan with targeted search queries and focus areas."""
        else:
            plan_prompt = f"Create a comprehensive research plan for: {query}"

        try:
            plan_result = await Runner.run(planning_agent, plan_prompt)
            research_plan = plan_result.final_output

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Search Queries:**")
                for q in research_plan.search_queries:
                    st.write(f"• {q}")
            with col2:
                st.write("**Focus Areas:**")
                for a in research_plan.focus_areas:
                    st.write(f"• {a}")
            st.session_state.step_completed["planning"] = True
        except Exception as e:
            st.error(f"Error in planning: {str(e)}")
            return

        # ====================================================================
        # STEP 3: Conduct research
        # ====================================================================
        st.write("### 🔎 Step 3: Conducting Research")
        st.info("🔄 Searching and collecting information")

        research_prompt = f"""Research queries to investigate:
{', '.join(research_plan.search_queries)}
Focus areas:
{', '.join(research_plan.focus_areas)}
Research these thoroughly and compile findings."""

        try:
            research_result = await Runner.run(research_agent, research_prompt)

            st.write("**📚 Collected Facts:**")
            if st.session_state.collected_facts:
                for fact in st.session_state.collected_facts:
                    with st.expander(f"📌 {fact['fact'][:60]}..."):
                        st.write(f"**Fact:** {fact['fact']}")
                        st.write(f"**Source:** {fact['source']}")
            st.session_state.step_completed["research"] = True
        except Exception as e:
            st.error(f"Error in research: {str(e)}")
            return

        # ====================================================================
        # STEP 4: Generate comprehensive report
        # ====================================================================
        st.write("### ✍️ Step 4: Generating Comprehensive Report")

        report_prompt = f"""Research Query: {query}
Research Findings:
{research_result.final_output if research_result else 'Research completed'}
Write a comprehensive, detailed research report (5-10 pages, 1500+ words).
Use clear sections, headings, and professional formatting."""

        try:
            report_result = await Runner.run(editor_agent, report_prompt)
            st.session_state.report_result = report_result.final_output

            st.write("✅ **Report Generated Successfully!**")
            st.session_state.step_completed["report"] = True
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")
            return

        # ====================================================================
        # STEP 5: Create comparison (if original content provided)
        # ====================================================================
        if original_content:
            st.write("### 🔄 Step 5: Comparing Research Quality")

            comparison_prompt = f"""Original Research:
{original_content}
New Research Generated:
{report_result.final_output.report if hasattr(report_result.final_output, 'report') else str(report_result.final_output)}
Provide a detailed comparison of both research pieces."""

            try:
                comparison_result = await Runner.run(
                    comparison_agent, comparison_prompt
                )
                st.session_state.comparison_result = comparison_result.final_output
                st.session_state.step_completed["comparison"] = True
            except Exception as e:
                st.error(f"Error in comparison: {str(e)}")

    st.session_state.research_done = True


# ============================================================================
# RUN RESEARCH
# ============================================================================
if start_button:
    original_content = None

    # Extract content from uploaded file
    if uploaded_file:
        try:
            if uploaded_file.type == "application/pdf":
                original_content = extract_pdf_text(uploaded_file)
                if original_content:
                    st.success(
                        f"✅ PDF uploaded: {len(original_content)} characters extracted"
                    )
            else:
                original_content = extract_text_file(uploaded_file)
                if original_content:
                    st.success(
                        f"✅ Text file uploaded: {len(original_content)} characters extracted"
                    )
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            original_content = None

    st.session_state.original_content = original_content

    # Run the research
    try:
        asyncio.run(run_research(research_query, original_content))
    except Exception as e:
        st.error(f"An error occurred during research: {str(e)}")
        st.session_state.research_done = True

# ============================================================================
# DISPLAY RESULTS (3 Tabs Layout)
# ============================================================================
if st.session_state.research_done:
    tab1, tab2, tab3 = st.tabs(
        ["🧭 Research Workflow", "📄 Final Report", "📌 Collected Facts"]
    )

    # -------------------------------------------------------
    # TAB 1 — FULL WORKFLOW (All steps with progress)
    # -------------------------------------------------------
    with tab1:
        st.subheader("🧭 Full Research Workflow")
        # Show step completion progress
        st.write("### ✅ Step Completion Status")
        for step, done in st.session_state.step_completed.items():
            status = "🟢 Done" if done else "⚪ Pending"
            st.write(f"- **{step.capitalize()}**: {status}")
        st.markdown("---")
        # Optional: Show extracted original content summary
        if st.session_state.original_content:
            with st.expander("📄 Original Research Content", expanded=False):
                st.write(st.session_state.original_content[:2000] + " ...")
        st.markdown("---")
        st.info("Scroll up to view each step as it happened in real time above.")

    # -------------------------------------------------------
    # TAB 2 — FINAL REPORT
    # -------------------------------------------------------
    with tab2:
        st.subheader("📄 Final Research Report")
        if st.session_state.report_result:
            report = st.session_state.report_result
            if hasattr(report, "report"):
                if hasattr(report, "title"):
                    st.title(report.title)
                if hasattr(report, "outline"):
                    with st.expander("📑 Report Outline", expanded=True):
                        for i, section in enumerate(report.outline, 1):
                            st.markdown(f"{i}. {section}")
                if hasattr(report, "word_count"):
                    st.caption(f"📊 Word Count: {report.word_count} words")
                st.markdown(report.report)
                if hasattr(report, "sources"):
                    with st.expander("📚 Sources"):
                        for i, source in enumerate(report.sources, 1):
                            st.markdown(f"{i}. {source}")
                st.download_button(
                    label="⬇️ Download Report (Markdown)",
                    data=report.report,
                    file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                )
        else:
            st.info("Report will appear here after research is completed.")

    # -------------------------------------------------------
    # TAB 3 — COLLECTED FACTS
    # -------------------------------------------------------
    with tab3:
        st.subheader("📌 Collected Facts")
        if st.session_state.collected_facts:
            for fact in st.session_state.collected_facts:
                with st.expander(f"📌 {fact['fact'][:60]}..."):
                    st.write(f"**Fact:** {fact['fact']}")
                    st.write(f"**Source:** {fact['source']}")
                    st.write(f"**Timestamp:** {fact['timestamp']}")
        else:
            st.info("No facts collected yet.")
