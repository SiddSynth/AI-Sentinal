import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import time

# Import local backend modules
import evaluator
import pdf_generator

# =====================================================================
# STREAMLIT PAGE SETUP & CUSTOM STYLING
# =====================================================================

st.set_page_config(
    page_title="AI Sentinel — Enterprise AI Agent Validation Suite",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern enterprise look (light theme, charcoal texts, red/cobalt accents)
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        
        /* Font Family Overrides */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #1a202c;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', sans-serif;
            font-weight: 700 !important;
            color: #1a202c !important;
        }

        /* Force Sidebar Background to White for consistent Light Mode */
        [data-testid="stSidebar"], [data-testid="stSidebar"] > div {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0 !important;
        }

        /* Force label, markdown, checkmark label, and helper text colors to remain dark for light bg */
        label, .stMarkdown, p, span, [data-testid="stWidgetLabel"], [data-testid="stMarkdownContainer"] {
            color: #1a202c !important;
        }

        /* Keep sidebar text elements colored dark grey */
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
            color: #2d3748 !important;
        }

        /* Set App Background */
        .stApp {
            background-color: #f7fafc !important;
        }
        
        /* Premium Textarea / Input styling */
        .stTextArea textarea, [data-testid="stTextArea"] textarea {
            background-color: #ffffff !important;
            color: #1a202c !important;
            border: 1px solid #cbd5e0 !important;
            border-radius: 8px !important;
        }
        .stTextInput input, [data-testid="stTextInput"] input {
            background-color: #ffffff !important;
            color: #1a202c !important;
            border: 1px solid #cbd5e0 !important;
            border-radius: 8px !important;
        }
        
        /* Card Container styling */
        .enterprise-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
            margin-bottom: 1.25rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .enterprise-card:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.03);
            transform: translateY(-2px);
        }
        
        /* Metric Styling */
        .metric-title {
            color: #718096 !important;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            margin-bottom: 0.25rem;
        }
        .metric-value {
            font-size: 1.85rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .metric-sub {
            color: #718096 !important;
            font-size: 0.75rem;
            margin-top: 0.25rem;
        }
        
        /* Force all code blocks to have a light theme background and dark text */
        [data-testid="stCodeBlock"], 
        [data-testid="stCodeBlock"] div, 
        [data-testid="stCodeBlock"] pre, 
        [data-testid="stCodeBlock"] code, 
        [data-testid="stCodeBlock"] span,
        pre,
        code {
            background-color: #ffffff !important;
            color: #1a202c !important;
        }
        [data-testid="stCodeBlock"], .stCodeBlock {
            border: 1px solid #cbd5e0 !important;
            border-radius: 8px !important;
            padding: 0.5rem !important;
        }

        /* Custom Button Styling */
        div.stButton > button {
            background-color: #e11a2f; /* Crimson Red */
            color: #ffffff !important;
            border: none;
            border-radius: 8px;
            padding: 0.55rem 1.5rem;
            font-size: 0.95rem;
            font-weight: 600;
            box-shadow: 0 4px 6px -1px rgba(225, 26, 47, 0.2);
            transition: all 0.2s ease;
            width: 100%;
        }
        div.stButton > button:hover {
            background-color: #b90e1f;
            box-shadow: 0 10px 15px -3px rgba(225, 26, 47, 0.3);
            color: #ffffff !important;
            transform: translateY(-1px);
        }
        div.stButton > button:active {
            transform: translateY(1px);
        }

        /* Custom Download Button Styling (to match primary red button) */
        div.stDownloadButton > button {
            background-color: #e11a2f !important; /* Crimson Red */
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.55rem 1.5rem !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 6px -1px rgba(225, 26, 47, 0.2) !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
        }
        div.stDownloadButton > button:hover {
            background-color: #b90e1f !important;
            box-shadow: 0 10px 15px -3px rgba(225, 26, 47, 0.3) !important;
            color: #ffffff !important;
            transform: translateY(-1px) !important;
        }
        div.stDownloadButton > button:active {
            transform: translateY(1px) !important;
        }
        /* Force all children inside the download button (spans, labels) to be white */
        div.stDownloadButton > button * {
            color: #ffffff !important;
        }
        
        /* Custom Alerts */
        .alert-box {
            padding: 1rem;
            border-radius: 8px;
            border-left: 5px solid #cbd5e0;
            margin-bottom: 1.25rem;
        }
        .alert-danger {
            background-color: #fff5f5;
            border-left-color: #e53e3e;
            color: #9b2c2c !important;
        }
        .alert-warning {
            background-color: #fffdf5;
            border-left-color: #d69e2e;
            color: #744210 !important;
        }
        .alert-success {
            background-color: #f0fff4;
            border-left-color: #38a169;
            color: #22543d !important;
        }
        .alert-info {
            background-color: #ebf8ff;
            border-left-color: #3182ce;
            color: #2b6cb0 !important;
        }
        
        /* Sidebar Logo */
        .sidebar-header {
            font-family: 'Outfit', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            color: #e11a2f;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.2rem;
        }
        .sidebar-sub {
            font-size: 0.75rem;
            color: #718096 !important;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# =====================================================================
# SESSION STATE INITIALIZATION
# =====================================================================

if "validation_results" not in st.session_state:
    st.session_state.validation_results = None

if "agent_prompt" not in st.session_state:
    st.session_state.agent_prompt = ""

if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = ""

if "use_sample" not in st.session_state:
    st.session_state.use_sample = False

if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("GEMINI_API_KEY", "")

# Sync sidebar api key to session state
def update_api_key():
    st.session_state.api_key = st.session_state.sidebar_api_key

# =====================================================================
# SIDEBAR NAVIGATION
# =====================================================================

with st.sidebar:
    st.markdown('<div class="sidebar-header">🛡️ AI Sentinel</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Enterprise AI Agent Validation Suite</div>', unsafe_allow_html=True)
    
    # Page select
    page = st.radio(
        "Navigation",
        ["🎯 Home & Configuration", "📊 Evaluation Dashboard", "🔍 Failure Explorer", "⚡ Prompt Optimizer", "📐 Architecture Diagram"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### 🔑 API Authentication")
    api_key_input = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help="Provide a Gemini API Key to run live simulations. Omit to run in 'Sample Agent' mode.",
        key="sidebar_api_key",
        on_change=update_api_key
    )
    
    st.markdown("---")
    st.markdown(
        '<div style="font-size: 0.7rem; color: #718096; text-align: center;">'
        'AI Sentinel v1.0.0<br/>'
        '<i>Inspired by challenges faced by enterprise conversational AI platforms.</i>'
        '</div>',
        unsafe_allow_html=True
    )

# =====================================================================
# PAGE 1: HOME & CONFIGURATION
# =====================================================================

if page == "🎯 Home & Configuration":
    st.markdown("## 🎯 AI Agent Pre-Deployment Validation")
    st.markdown(
        "AI Sentinel acts as a validation suite for conversational AI systems. It dynamically generates adversarial "
        "customer personas based on selected scenario categories, simulates complete multi-turn dialogues against "
        "your system instructions, evaluates compliance utilizing an AI Evaluation Engine, and outputs diagnostic "
        "improvements before your agent is deployed to customers."
    )
    
    st.markdown("---")
    
    # Use Sample Agent Button
    col_sample, col_spacer = st.columns([2, 5])
    with col_sample:
        if st.button("👉 Load Sample Agent Template", use_container_width=True):
            st.session_state.agent_prompt = evaluator.SAMPLE_PROMPT
            st.session_state.knowledge_base = evaluator.SAMPLE_KB
            st.session_state.use_sample = True
            st.success("Sample Retail Assistant template loaded! Ready for simulation.")
            
    # Form Layout
    col_left, col_right = st.columns([4, 3])
    
    with col_left:
        st.markdown("### 📝 Agent Definitions")
        
        # System Prompt Input
        agent_prompt = st.text_area(
            "System Prompt / Instruction Set",
            value=st.session_state.agent_prompt,
            placeholder="Define the behavior, tone, limits, and rules of your support assistant...",
            height=280,
            help="This is the primary instruction set governing the AI agent under test."
        )
        st.session_state.agent_prompt = agent_prompt
        
        # Knowledge Base Input
        kb_text = st.text_area(
            "Knowledge Base / FAQ Context (Optional)",
            value=st.session_state.knowledge_base,
            placeholder="Add relevant shipping policies, refund values, product details, or FAQs...",
            height=180,
            help="External knowledge constraints that the agent should adhere to."
        )
        st.session_state.knowledge_base = kb_text
        
    with col_right:
        st.markdown("### 🧬 Stress Test Scenarios")
        st.write("Select adversarial user behaviors to validate your agent against:")
        
        # Scenario Categories checkboxes
        scenarios = {
            "Angry Customer": st.checkbox("😡 Angry Customer", value=True, help="Hostile, impatient customer demanding immediate refund."),
            "Hindi + English": st.checkbox("🗣️ Hindi + English (Hinglish)", value=True, help="Bilingual phrasing and vocabulary switching."),
            "Off-topic": st.checkbox("⛺ Off-topic Wanderer", value=True, help="Prompts that deviate from support topics to test guardrails."),
            "Policy Exception": st.checkbox("💸 Policy Exception Pressure", value=True, help="Attempts to bypass return windows or restocking fees."),
            "Abuse": st.checkbox("🤬 Verbal Abuse Handling", value=True, help="Insulting behavior to test safety triggers and warnings."),
            "Long Conversation": st.checkbox("🔒 Security Audit / Prompt Injection", value=True, help="Direct prompt extraction attacks (jailbreaking).")
        }
        
        selected_cats = [cat for cat, checked in scenarios.items() if checked]
        
        st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)
        
        # RUN BUTTON
        run_label = "🚀 Run Pre-Deployment Validation"
        if not st.session_state.api_key:
            run_label = "🚀 Run Simulation (Use Sample Agent)"
            
        if st.button(run_label, key="run_validation"):
            if not agent_prompt:
                st.error("Please provide a System Prompt to validate.")
            elif len(selected_cats) == 0:
                st.error("Please select at least one Stress Test Scenario.")
            else:
                # Progress animation
                st.markdown("---")
                progress_container = st.container()
                
                with progress_container:
                    status_text = st.empty()
                    progress_bar = st.progress(0)
                    
                    def handle_progress(stage, percent):
                        status_text.markdown(f"**⚙️ {stage}**")
                        progress_bar.progress(percent)
                    
                    # Execution
                    is_sample_agent = not st.session_state.api_key or st.session_state.use_sample
                    try:
                        results = evaluator.run_validation_pipeline(
                            api_key=st.session_state.api_key,
                            agent_prompt=agent_prompt,
                            knowledge_base=kb_text,
                            selected_categories=selected_cats,
                            use_sample_agent=is_sample_agent,
                            progress_callback=handle_progress
                        )
                        
                        st.session_state.validation_results = results
                        st.success("🎉 Validation Suite Complete! Go to the 'Evaluation Dashboard' tab to inspect findings.")
                        
                        # Navigation trigger options
                        col_nav1, col_nav2 = st.columns(2)
                        with col_nav1:
                            st.info("👈 Navigate using the sidebar to view results.")
                    except Exception as err:
                        st.error(f"Validation failed: {err}")
                        st.warning("Ensure your GEMINI_API_KEY is correct or use 'Sample Agent' mode.")

# =====================================================================
# PAGE 2: EVALUATION DASHBOARD
# =====================================================================

elif page == "📊 Evaluation Dashboard":
    st.markdown("## 📊 Agent Validation Dashboard")
    st.markdown("Assess the robustness of your AI agent across critical behavioral dimensions.")
    
    if st.session_state.validation_results is None:
        st.markdown(
            '<div class="alert-box alert-warning">'
            '⚠️ <b>No validation data found.</b> Go to <b>Home & Configuration</b> to trigger a validation pipeline, or load the Sample Agent.'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        results = st.session_state.validation_results["results"]
        total_scenarios = len(results)
        
        # Calculators
        reliability_scores = [r["evaluation"]["reliability_score"] for r in results.values()]
        avg_reliability = sum(reliability_scores) / total_scenarios
        
        failures = sum(1 for r in results.values() if r["evaluation"]["failed_safety_or_policy"])
        failure_rate = (failures / total_scenarios) * 100
        
        instruct_avg = sum(r["evaluation"]["instruction_following"] for r in results.values()) / total_scenarios
        safety_avg = sum(r["evaluation"]["safety_score"] for r in results.values()) / total_scenarios
        hallucination_avg = sum(r["evaluation"]["hallucination_score"] for r in results.values()) / total_scenarios
        policy_avg = sum(r["evaluation"]["policy_compliance"] for r in results.values()) / total_scenarios
        recovery_avg = sum(r["evaluation"]["conversation_recovery"] for r in results.values()) / total_scenarios
        consistency_avg = sum(r["evaluation"]["consistency_score"] for r in results.values()) / total_scenarios
        quality_avg = sum(r["evaluation"]["overall_quality"] for r in results.values()) / total_scenarios
        
        # Color coding for reliability
        rel_color = "#e53e3e" if avg_reliability < 60 else "#d69e2e" if avg_reliability < 80 else "#38a169"
        
        # Score Columns Block
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="enterprise-card">
                    <div class="metric-title">Overall Reliability</div>
                    <div class="metric-value" style="color: {rel_color};">{avg_reliability:.1f}%</div>
                    <div class="metric-sub">Average validation score</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class="enterprise-card">
                    <div class="metric-title">Prompt Robustness</div>
                    <div class="metric-value" style="color: #2d3748;">{((instruct_avg + consistency_avg)/10)*100:.1f}%</div>
                    <div class="metric-sub">Rules adherence & stability</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
                <div class="enterprise-card">
                    <div class="metric-title">Critical Failures</div>
                    <div class="metric-value" style="color: {'#e53e3e' if failures > 0 else '#38a169'};">{failures} / {total_scenarios}</div>
                    <div class="metric-sub">{failure_rate:.1f}% fail rate under pressure</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col4:
            # Risk Level Card
            if avg_reliability >= 80 and failures == 0:
                risk_lvl = "LOW RISK"
                risk_col = "#38a169"
            elif avg_reliability >= 60 and failures <= 2:
                risk_lvl = "MEDIUM RISK"
                risk_col = "#d69e2e"
            else:
                risk_lvl = "HIGH RISK"
                risk_col = "#e53e3e"
                
            st.markdown(f"""
                <div class="enterprise-card">
                    <div class="metric-title">Deployment Risk</div>
                    <div class="metric-value" style="color: {risk_col};">{risk_lvl}</div>
                    <div class="metric-sub">Based on safety & policy checks</div>
                </div>
            """, unsafe_allow_html=True)
            
        # Scenario Performance Table & Charts
        col_table, col_chart = st.columns([5, 4])
        
        with col_table:
            st.markdown("### 📋 Stress Test Scenario Breakdown")
            
            records = []
            for name, r in results.items():
                ev = r["evaluation"]
                records.append({
                    "Persona": name,
                    "Category": r["persona"]["category"],
                    "Reliability": f"{ev['reliability_score']}%",
                    "Safety Check": "❌ Fail" if ev["failed_safety_or_policy"] else "✅ Pass",
                    "Failure Category": ev["failure_category"]
                })
            
            df = pd.DataFrame(records)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Best / Worst Cards
            sorted_res = sorted(results.items(), key=lambda x: x[1]["evaluation"]["reliability_score"])
            worst_name, worst_info = sorted_res[0]
            best_name, best_info = sorted_res[-1]
            
            col_b, col_w = st.columns(2)
            with col_b:
                st.markdown(f"""
                    <div style="background-color: #f0fff4; border: 1px solid #c6f6d5; border-radius: 8px; padding: 1rem;">
                        <span style="font-size: 0.75rem; color: #22543d; font-weight: 700; text-transform: uppercase;">Best Performing Persona</span>
                        <h4 style="margin: 0.25rem 0; color: #22543d;">{best_name}</h4>
                        <p style="margin: 0; font-size: 0.8rem; color: #4a5568;">Category: {best_info['persona']['category']}<br/>Score: <b>{best_info['evaluation']['reliability_score']}%</b></p>
                    </div>
                """, unsafe_allow_html=True)
            with col_w:
                st.markdown(f"""
                    <div style="background-color: #fff5f5; border: 1px solid #fed7d7; border-radius: 8px; padding: 1rem;">
                        <span style="font-size: 0.75rem; color: #9b2c2c; font-weight: 700; text-transform: uppercase;">Worst Performing Persona</span>
                        <h4 style="margin: 0.25rem 0; color: #9b2c2c;">{worst_name}</h4>
                        <p style="margin: 0; font-size: 0.8rem; color: #4a5568;">Category: {worst_info['persona']['category']}<br/>Score: <b>{worst_info['evaluation']['reliability_score']}%</b></p>
                    </div>
                """, unsafe_allow_html=True)
                
        with col_chart:
            st.markdown("### 📊 Metrics Matrix")
            
            # Radar-like Bar chart for dimension averages
            metrics_labels = ["Instruction Following", "Safety Score", "Hallucination Control", "Policy Compliance", "Conversation Recovery", "Consistency"]
            metrics_vals = [instruct_avg, safety_avg, hallucination_avg, policy_avg, recovery_avg, consistency_avg]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=metrics_vals,
                    y=metrics_labels,
                    orientation='h',
                    marker_color=['#e11a2f' if v < 3.5 else '#3182ce' for v in metrics_vals],
                    text=[f"{v:.2f} / 5" for v in metrics_vals],
                    textposition='auto',
                )
            ])
            
            fig.update_layout(
                xaxis_title="Score (1-5)",
                yaxis=dict(autorange="reversed"),
                margin=dict(l=20, r=20, t=20, b=20),
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        # Bottom charts: Failure categories and Score distribution
        st.markdown("---")
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            st.markdown("#### 🚨 Failure Categories Distribution")
            fail_cats = [r["evaluation"]["failure_category"] for r in results.values() if r["evaluation"]["failure_category"] != "None"]
            if fail_cats:
                cat_df = pd.DataFrame(fail_cats, columns=["Category"]).value_counts().reset_index()
                fig_pie = px.pie(cat_df, values='count', names='Category', color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No failure states triggered. Great job! The agent complied with safety boundaries.")
                
        with col_f2:
            st.markdown("#### 📈 Reliability Scores by Persona")
            persona_scores = pd.DataFrame([
                {"Persona": name, "Score": r["evaluation"]["reliability_score"]}
                for name, r in results.items()
            ])
            fig_bar = px.bar(persona_scores, x="Score", y="Persona", orientation="h", color="Score",
                             color_continuous_scale=["#e53e3e", "#d69e2e", "#38a169"])
            fig_bar.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10), yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_bar, use_container_width=True)

# =====================================================================
# PAGE 3: FAILURE EXPLORER
# =====================================================================

elif page == "🔍 Failure Explorer":
    st.markdown("## 🔍 Failure Explorer")
    st.markdown("Drill down into simulated dialogues to examine vulnerabilities and read step-by-step evaluations.")
    
    if st.session_state.validation_results is None:
        st.markdown(
            '<div class="alert-box alert-warning">'
            '⚠️ <b>No validation data found.</b> Go to <b>Home & Configuration</b> to trigger a validation pipeline, or load the Sample Agent.'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        results = st.session_state.validation_results["results"]
        
        # Selectbox to pick a customer persona dialogue
        selected_name = st.selectbox(
            "Select Customer Scenario Transcript:",
            options=list(results.keys()),
            help="Choose a persona to explore their multi-turn conversation and LLM evaluations."
        )
        
        if selected_name:
            res = results[selected_name]
            persona = res["persona"]
            transcript = res["transcript"]
            ev = res["evaluation"]
            
            # Persona Metadata header
            st.markdown(f"### 👤 Customer Profile: {selected_name}")
            col_p1, col_p2, col_p3 = st.columns([1, 2, 2])
            with col_p1:
                st.write(f"**Scenario Category:**\n{persona['category']}")
            with col_p2:
                st.write(f"**Context Background:**\n{persona['background']}")
            with col_p3:
                st.write(f"**Core Goal:**\n{persona['goal']}")
                
            st.markdown("---")
            
            # Layout: Left side Transcript, Right side AI Evaluation Engine report
            col_chat, col_eval = st.columns([4, 3])
            
            with col_chat:
                st.markdown("#### 💬 Conversation Transcript")
                
                # Render using Streamlit's official chat bubbles for premium feel
                for msg in transcript:
                    if msg["role"] == "customer":
                        with st.chat_message("user", avatar="👤"):
                            st.markdown(f"**{selected_name}** (Customer)")
                            st.write(msg["content"])
                    else:
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown("**AI Agent under Test**")
                            st.write(msg["content"])
                            
            with col_eval:
                st.markdown("#### 🧠 AI Evaluation Engine Diagnosis")
                
                # Check status box
                if ev["failed_safety_or_policy"]:
                    st.markdown(f"""
                        <div class="alert-box alert-danger">
                            🚨 <b>VALIDATION FAILED</b><br/>
                            <b>Vulnerability Category:</b> {ev['failure_category']}<br/>
                            <b>Issue:</b> {ev['failure_reason']}
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div class="alert-box alert-success">
                            ✅ <b>VALIDATION PASSED</b><br/>
                            The assistant adhered to policies and successfully navigated the adversarial conversation.
                        </div>
                    """, unsafe_allow_html=True)
                
                # Scores Card
                st.markdown('<div class="enterprise-card">', unsafe_allow_html=True)
                st.write(f"🏆 **Reliability Score:** `{ev['reliability_score']}/100`")
                st.write(f"• Instruction Following: `{ev['instruction_following']}/5`")
                st.write(f"• Safety Compliance: `{ev['safety_score']}/5`")
                st.write(f"• Hallucination Control: `{ev['hallucination_score']}/5`")
                st.write(f"• Policy Adherence: `{ev['policy_compliance']}/5`")
                st.write(f"• Conversational Recovery: `{ev['conversation_recovery']}/5`")
                st.write(f"• Tone Consistency: `{ev['consistency_score']}/5`")
                st.write(f"• Overall Turn Quality: `{ev['overall_quality']}/5`")
                st.write(f"• Human Escalation: `{'Yes (Transfered)' if ev['is_escalated'] else 'No (Resolved by AI)'}`")
                st.write(f"• Escalation Appropriateness: `{'Correct Action' if ev['was_escalation_appropriate'] else 'Incorrect Action'}`")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Recommendation Card
                if ev["failed_safety_or_policy"]:
                    st.markdown(f"""
                        <div style="background-color: #fffdf5; border: 1px solid #fbd38d; border-radius: 8px; padding: 1.25rem;">
                            <h4 style="margin: 0 0 0.5rem 0; color: #b7791f;">⚡ Recommended Prompt Repair</h4>
                            <p style="font-size: 0.85rem; line-height: 1.4; color: #744210;">
                                <b>Required Guardrail:</b><br/>
                                <code style="background-color: #fffaf0; padding: 2px 4px; border-radius: 4px; font-size: 0.8rem; border: 1px solid #feebc8; color: #c05621; display: block; margin-top: 5px;">
                                {ev['suggested_prompt_improvement']}
                                </code>
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

# =====================================================================
# PAGE 4: PROMPT OPTIMIZER
# =====================================================================

elif page == "⚡ Prompt Optimizer":
    st.markdown("## ⚡ Prompt Optimizer")
    st.markdown(
        "AI Sentinel analyzes behavioral failure points and automatically optimizes system prompts, inserting "
        "defensive instructions, safety filters, and explicit policy constraints."
    )
    
    if st.session_state.validation_results is None:
        st.markdown(
            '<div class="alert-box alert-warning">'
            '⚠️ <b>No validation data found.</b> Go to <b>Home & Configuration</b> to trigger a validation pipeline, or load the Sample Agent.'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        results = st.session_state.validation_results["results"]
        optimization = st.session_state.validation_results["optimization"]
        original_prompt = st.session_state.validation_results["original_prompt"]
        
        # Calculate Current Score
        reliability_scores = [r["evaluation"]["reliability_score"] for r in results.values()]
        avg_reliability = sum(reliability_scores) / len(results)
        
        # Dashboard Score Upgrade Card
        col_sc1, col_sc2, col_pdf = st.columns([2, 2, 3])
        with col_sc1:
            st.markdown(f"""
                <div class="enterprise-card" style="text-align: center;">
                    <div class="metric-title">Current Reliability</div>
                    <div class="metric-value" style="color: #e53e3e;">{avg_reliability:.1f}%</div>
                    <div class="metric-sub">With original system prompt</div>
                </div>
            """, unsafe_allow_html=True)
        with col_sc2:
            st.markdown(f"""
                <div class="enterprise-card" style="text-align: center;">
                    <div class="metric-title">Projected Reliability</div>
                    <div class="metric-value" style="color: #38a169;">{optimization['expected_score']:.1f}%</div>
                    <div class="metric-sub">Estimated post-repair v2 score</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col_pdf:
            st.markdown("#### 📄 Executive Reporting")
            # PDF Download Button
            try:
                pdf_bytes = pdf_generator.generate_pdf_report(st.session_state.validation_results)
                st.download_button(
                    label="📥 Download Executive Validation PDF Report",
                    data=pdf_bytes,
                    file_name=f"AI_Sentinel_Validation_Report_{int(time.time())}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.write("Generates a stakeholder-ready evaluation dossier including executive summaries, risk metrics, and prompt revision logs.")
            except Exception as e:
                st.error(f"Error compiling PDF: {e}")
                
        st.markdown("### 🛠️ Synthesized Enhancements")
        cols_imp = st.columns(2)
        for idx, imp in enumerate(optimization["improvements"]):
            col_target = cols_imp[idx % 2]
            col_target.markdown(f"✔ **{imp}**")
            
        st.markdown("---")
        
        # Code Comparison View
        st.markdown("### 💻 Prompt Comparison (Version 1.0 vs Version 2.0)")
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown("#### Original System Instructions (v1.0)")
            st.code(original_prompt, language="text", wrap_lines=True)
        with col_v2:
            st.markdown("#### Optimized System Instructions (v2.0)")
            st.code(optimization["prompt_v2"], language="text", wrap_lines=True)

# =====================================================================
# PAGE 5: ARCHITECTURE DIAGRAM
# =====================================================================

elif page == "📐 Architecture Diagram":
    st.markdown("## 📐 Validation Pipeline Architecture")
    st.markdown("AI Sentinel uses a closed-loop validation architecture to stress-test and improve agent instructions.")
    
    st.markdown("---")
    
    # Render custom SVG layout for recruiters
    svg_layout = """
    <svg width="100%" height="220" viewBox="0 0 1000 220" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#718096" />
        </marker>
        <linearGradient id="primaryGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#e11a2f;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#9b0c1b;stop-opacity:1" />
        </linearGradient>
        <linearGradient id="secondaryGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#2d3748;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#1a202c;stop-opacity:1" />
        </linearGradient>
      </defs>
      
      <!-- Nodes -->
      <rect x="10" y="60" width="120" height="70" rx="10" fill="url(#secondaryGrad)" />
      <text x="70" y="95" fill="white" font-family="'Outfit', sans-serif" font-size="12" font-weight="bold" text-anchor="middle">Agent Prompt</text>
      <text x="70" y="112" fill="#cbd5e0" font-family="sans-serif" font-size="9" text-anchor="middle">(System Config)</text>
      
      <path d="M 130 95 L 165 95" stroke="#718096" stroke-width="2" marker-end="url(#arrow)" />
      
      <rect x="175" y="60" width="130" height="70" rx="10" fill="url(#primaryGrad)" />
      <text x="240" y="95" fill="white" font-family="'Outfit', sans-serif" font-size="12" font-weight="bold" text-anchor="middle">Persona Generator</text>
      <text x="240" y="112" fill="#fed7d7" font-family="sans-serif" font-size="9" text-anchor="middle">(Gemini 2.5 Flash)</text>
      
      <path d="M 305 95 L 340 95" stroke="#718096" stroke-width="2" marker-end="url(#arrow)" />
      
      <rect x="350" y="60" width="130" height="70" rx="10" fill="url(#secondaryGrad)" />
      <text x="415" y="95" fill="white" font-family="'Outfit', sans-serif" font-size="12" font-weight="bold" text-anchor="middle">Conversation Simulator</text>
      <text x="415" y="112" fill="#cbd5e0" font-family="sans-serif" font-size="9" text-anchor="middle">(Adversarial Loop)</text>
      
      <path d="M 480 95 L 515 95" stroke="#718096" stroke-width="2" marker-end="url(#arrow)" />
      
      <rect x="525" y="60" width="130" height="70" rx="10" fill="url(#primaryGrad)" />
      <text x="590" y="95" fill="white" font-family="'Outfit', sans-serif" font-size="12" font-weight="bold" text-anchor="middle">AI Eval Engine</text>
      <text x="590" y="112" fill="#fed7d7" font-family="sans-serif" font-size="9" text-anchor="middle">(LLM Judge)</text>
      
      <path d="M 655 95 L 690 95" stroke="#718096" stroke-width="2" marker-end="url(#arrow)" />
      
      <rect x="700" y="60" width="120" height="70" rx="10" fill="url(#secondaryGrad)" />
      <text x="760" y="95" fill="white" font-family="'Outfit', sans-serif" font-size="12" font-weight="bold" text-anchor="middle">Metrics Engine</text>
      <text x="760" y="112" fill="#cbd5e0" font-family="sans-serif" font-size="9" text-anchor="middle">(Reliability Matrix)</text>
      
      <path d="M 820 95 L 855 95" stroke="#718096" stroke-width="2" marker-end="url(#arrow)" />
      
      <rect x="865" y="60" width="125" height="70" rx="10" fill="url(#primaryGrad)" />
      <text x="927" y="95" fill="white" font-family="'Outfit', sans-serif" font-size="12" font-weight="bold" text-anchor="middle">Dashboard & PDF</text>
      <text x="927" y="112" fill="#fed7d7" font-family="sans-serif" font-size="9" text-anchor="middle">(Prompt v2 / Report)</text>
      
      <!-- Feedback loop dashed arrow -->
      <path d="M 927 130 C 927 200, 70 200, 70 135" fill="none" stroke="#e11a2f" stroke-width="1.5" stroke-dasharray="5,5" marker-end="url(#arrow)" />
      <text x="500" y="188" fill="#e11a2f" font-family="'Outfit', sans-serif" font-size="10.5" font-weight="bold" text-anchor="middle">Optimization & Instruction Re-Injection Loop (Prompt v2)</text>
    </svg>
    """
    
    st.write("### 🔁 Pipeline Process Flow")
    st.markdown(svg_layout, unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
    
    # Detail cards explaining each pipeline node
    col_e1, col_e2, col_e3 = st.columns(3)
    
    with col_e1:
        st.markdown(f"""
            <div class="enterprise-card" style="min-height: 250px;">
                <h4 style="color: #e11a2f; margin-bottom: 0.5rem;">1. Persona Generator</h4>
                <p style="font-size: 0.85rem; line-height: 1.4; color: #4a5568;">
                    Queries Gemini with the Target Agent's system context. It generates specific customer profiles (names, backgrounds, goals, linguistic traits, and psychological postures) to stress-test defined scenario boundaries.
                </p>
                <span style="font-size: 0.75rem; color: #718096; font-weight: 700;">ENGINE: Gemini 2.5 Flash</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="enterprise-card" style="min-height: 250px;">
                <h4 style="color: #2d3748; margin-bottom: 0.5rem;">4. Metrics Engine</h4>
                <p style="font-size: 0.85rem; line-height: 1.4; color: #4a5568;">
                    Aggregates turn-by-turn evaluations into standard enterprise dimensions (Policy Compliance, Safety, Hallucination Control). It identifies the overall reliability percentage and isolates the worst-performing personas.
                </p>
                <span style="font-size: 0.75rem; color: #718096; font-weight: 700;">ENGINE: Python Pandas / NumPy</span>
            </div>
        """, unsafe_allow_html=True)
        
    with col_e2:
        st.markdown(f"""
            <div class="enterprise-card" style="min-height: 250px;">
                <h4 style="color: #2d3748; margin-bottom: 0.5rem;">2. Conversation Simulator</h4>
                <p style="font-size: 0.85rem; line-height: 1.4; color: #4a5568;">
                    Orchestrates a parallel dialogue session between the target agent and the generated personas. The simulation runs for 3-5 turns per persona, ensuring a natural but strict boundary test of the agent's instructions.
                </p>
                <span style="font-size: 0.75rem; color: #718096; font-weight: 700;">ENGINE: concurrent.futures Threading</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="enterprise-card" style="min-height: 250px;">
                <h4 style="color: #e11a2f; margin-bottom: 0.5rem;">5. Prompt Optimizer</h4>
                <p style="font-size: 0.85rem; line-height: 1.4; color: #4a5568;">
                    Extracts raw conversation failures, correlates them with system constraints, and synthesizes a prompt version 2.0. This new prompt injects specific defensive rules to prevent similar failures in future deployments.
                </p>
                <span style="font-size: 0.75rem; color: #718096; font-weight: 700;">ENGINE: Gemini Prompt Synthesis</span>
            </div>
        """, unsafe_allow_html=True)
        
    with col_e3:
        st.markdown(f"""
            <div class="enterprise-card" style="min-height: 250px;">
                <h4 style="color: #e11a2f; margin-bottom: 0.5rem;">3. AI Evaluation Engine</h4>
                <p style="font-size: 0.85rem; line-height: 1.4; color: #4a5568;">
                    Functions as a judge, analyzing the dialogue logs. It scores each conversation, detects policy deviations, registers safety violations, and writes a detailed diagnosis along with a suggested repair string.
                </p>
                <span style="font-size: 0.75rem; color: #718096; font-weight: 700;">ENGINE: Structured Output LLM</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="enterprise-card" style="min-height: 250px;">
                <h4 style="color: #2d3748; margin-bottom: 0.5rem;">6. Reporting Dossier</h4>
                <p style="font-size: 0.85rem; line-height: 1.4; color: #4a5568;">
                    Compiles the entire stress-test metrics history into a downloadable PDF document, presenting Risk Assessments, Critical Vulnerabilities, Action Items, and comparative Prompt improvements for stakeholders.
                </p>
                <span style="font-size: 0.75rem; color: #718096; font-weight: 700;">ENGINE: ReportLab PDF Framework</span>
            </div>
        """, unsafe_allow_html=True)
