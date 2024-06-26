import streamlit as st
from streamlit_server_state import server_state

from helper.modelling import (
    determine_rerun_reinitialize,
    initialize_llm,
    load_rag_pipeline,
    set_static_model_params,
)

from helper.ui import (
    import_chat,
    import_styles,
    initial_placeholder,
    ui_advanced_model_params,
    ui_export_chat_end_session,
    ui_header,
    ui_reset,
    ui_model_params,
    ui_tab,
    ui_upload_docs,
)
from helper.user_management import (
    check_password,
    determine_availability,
    setup_local_files,
)

# parameters/authentication
setup_local_files()

# tab icon and text
ui_tab()


### session initialization/login

determine_availability()

if not check_password():
    st.stop()


### initial setup

# header
ui_header()

# styles sheets
import_styles()

# placeholder on initial load
initial_placeholder()


### sidebar


# upload your own documents section
ui_upload_docs()

st.sidebar.divider()

# model parameters
ui_model_params()

# advanced model parameters
ui_advanced_model_params()

st.sidebar.divider()

# reset memory button
ui_reset()


### model


# load the LLM
initialize_llm()

# static model params
set_static_model_params()

# determine if the database needs to be reinitialized
determine_rerun_reinitialize()

# loading model
load_rag_pipeline()


### chat logic


import_chat()


### final UI elements


ui_export_chat_end_session()
