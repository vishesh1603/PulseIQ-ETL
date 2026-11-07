"""
PulseIQ Theme Utilities: Dark / Light Mode Switch & Styling Manager
Provides dynamic theme switching with synchronized Plotly templates and CSS styles.
"""
import streamlit as st

def render_theme_toggle():
    """
    Renders a Dark / Light Mode switch toggle in the sidebar.
    Applies comprehensive responsive CSS styling and returns the appropriate Plotly template name.
    """
    # Initialize session state for theme if not present
    if "dark_mode" not in st.session_state:
        # Default to False (Light Mode) or detect state
        st.session_state["dark_mode"] = False

    st.sidebar.markdown("---")
    dark_mode = st.sidebar.toggle(
        "🌙 Dark Mode" if st.session_state["dark_mode"] else "☀️ Light Mode",
        value=st.session_state["dark_mode"],
        key="global_theme_toggle_switch"
    )
    st.session_state["dark_mode"] = dark_mode

    if dark_mode:
        css = """
        <style>
            /* Dark Theme Overrides */
            .stApp {
                background-color: #0F172A !important;
                color: #F8FAFC !important;
            }
            section[data-testid="stSidebar"] {
                background-color: #1E293B !important;
            }
            section[data-testid="stSidebar"] * {
                color: #F1F5F9 !important;
            }
            .metric-card, .scorecard-card {
                background-color: #1E293B !important;
                border: 1px solid #334155 !important;
                color: #F8FAFC !important;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4) !important;
            }
            .kpi-title, .kpi-num {
                color: #94A3B8 !important;
                font-weight: 600 !important;
            }
            .kpi-name {
                color: #F8FAFC !important;
            }
            .kpi-value, .kpi-main-val {
                color: #FFFFFF !important;
            }
            .kpi-sub {
                color: #CBD5E1 !important;
            }
            .insight-box {
                background-color: #1E293B !important;
                color: #E2E8F0 !important;
                border: 1px solid #334155 !important;
                border-left: 4px solid #0072B2 !important;
            }
            .insight-box strong, .insight-box em {
                color: #F8FAFC !important;
            }
            .policy-banner, .rule-banner, .sign-convention-box, .arch-banner, .reconciliation-banner {
                background-color: #1E293B !important;
                color: #E2E8F0 !important;
                border: 1px solid #334155 !important;
                border-left: 6px solid #3B82F6 !important;
            }
            .policy-banner p, .rule-banner p, .sign-convention-box p, .arch-banner p, .reconciliation-banner p {
                color: #CBD5E1 !important;
            }
            .policy-banner h4, .policy-banner h5, .rule-banner h5, .sign-convention-box h4, .arch-banner h5, .reconciliation-banner h4 {
                color: #60A5FA !important;
            }
            .kpi-target-tag {
                background-color: #334155 !important;
                color: #F1F5F9 !important;
            }
            .ai-badge {
                background-color: #334155 !important;
                color: #F8FAFC !important;
                border-left: 3px solid #E69F00 !important;
            }
            /* Table & Dataframe enhancements */
            div[data-testid="stDataFrame"] {
                background-color: #1E293B !important;
                border-radius: 6px !important;
            }
        </style>
        """
        plotly_template = "plotly_dark"
    else:
        css = """
        <style>
            /* Light Theme Overrides */
            .stApp {
                background-color: #FFFFFF !important;
                color: #111111 !important;
            }
            .metric-card, .scorecard-card {
                background-color: #F8F9FA !important;
                border: 1px solid #E2E8F0 !important;
                color: #111111 !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
            }
            .kpi-title, .kpi-num {
                color: #555555 !important;
            }
            .kpi-name {
                color: #1A202C !important;
            }
            .kpi-value, .kpi-main-val {
                color: #111111 !important;
            }
            .kpi-sub {
                color: #777777 !important;
            }
            .insight-box {
                background-color: #EDF2F7 !important;
                color: #2D3748 !important;
                border-left: 4px solid #4A5568 !important;
            }
            .policy-banner {
                background-color: #FEFCBF !important;
                color: #2D3748 !important;
                border-left: 6px solid #D69E2E !important;
            }
            .rule-banner {
                background-color: #EBF8FF !important;
                color: #2D3748 !important;
                border-left: 6px solid #3182CE !important;
            }
            .arch-banner {
                background-color: #F0FFF4 !important;
                color: #2D3748 !important;
                border-left: 6px solid #38A169 !important;
            }
            .sign-convention-box {
                background-color: #EDF2F7 !important;
                color: #2D3748 !important;
                border-left: 6px solid #4A5568 !important;
            }
            .kpi-target-tag {
                background-color: #EDF2F7 !important;
                color: #4A5568 !important;
            }
            .ai-badge {
                background-color: #E2E8F0 !important;
                color: #2D3748 !important;
                border-left: 3px solid #E69F00 !important;
            }
        </style>
        """
        plotly_template = "simple_white"

    st.markdown(css, unsafe_allow_html=True)
    return plotly_template
