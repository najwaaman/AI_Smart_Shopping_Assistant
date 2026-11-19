import streamlit as st


def render_brand_footer():
    st.sidebar.markdown(
        """
        <div style="padding:.35rem .5rem 1rem">
          <div style="font-size:1.02rem;font-weight:850;letter-spacing:.01em">AI Smart Shopping</div>
          <div style="color:#91A1B7;font-size:.76rem;margin-top:.22rem">Retail intelligence platform</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_footer():
    st.sidebar.markdown("---")
    st.sidebar.caption("AI Shopping Assistant · v1.0")
