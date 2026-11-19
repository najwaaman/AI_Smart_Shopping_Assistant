from html import escape

import streamlit as st


def escape_html_text(value):
    """Escape dynamic text before inserting it into an HTML fragment."""
    return escape(str(value), quote=True)


def render_page_header(eyebrow, title, subtitle):
    st.markdown(f'<div class="app-eyebrow">{escape_html_text(eyebrow)}</div><h1 class="app-title">{escape_html_text(title)}</h1><div class="app-subtitle">{escape_html_text(subtitle)}</div>', unsafe_allow_html=True)


def render_kpi_card(label, value, note="", accent="#3568FF"):
    st.markdown(
        f'<div class="kpi-card"><div style="width:34px;height:3px;background:{escape_html_text(accent)};border-radius:2px;margin-bottom:.8rem"></div><div class="kpi-label">{escape_html_text(label)}</div><div class="kpi-value">{escape_html_text(value)}</div><div class="kpi-note">{escape_html_text(note)}</div></div>',
        unsafe_allow_html=True,
    )


def render_section_heading(title, copy=""):
    st.markdown(f'<div class="section-card"><div class="section-title">{escape_html_text(title)}</div><div class="section-copy">{escape_html_text(copy)}</div></div>', unsafe_allow_html=True)


def render_status_label(status="Upcoming"):
    css = "status-live" if status.lower() == "live" else "status-upcoming"
    st.markdown(f'<span class="{css}">{escape_html_text(status)}</span>', unsafe_allow_html=True)


def upcoming_page(title, subtitle, features):
    render_page_header("Module", title, subtitle)
    render_status_label("Upcoming in a later phase")
    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.subheader("Planned capabilities")
    for feature in features:
        st.markdown(f"- {feature}")
    st.markdown('</div>', unsafe_allow_html=True)
