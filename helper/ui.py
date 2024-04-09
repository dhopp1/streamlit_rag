from datetime import datetimefrom streamlit_server_state import server_stateimport streamlit as stfrom helper.user_management import clear_models, record_use, update_server_statedef import_styles():    "import styles sheet and determine avatars of users"    with open( "styles/style.css" ) as css:        st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)            st.session_state["user_avatar"] = "https://www.svgrepo.com/show/524211/user.svg"    st.session_state["assistant_avatar"] = "https://www.svgrepo.com/show/375527/ai-platform.svg"def streamed_response(streamer):    "stream the LLM's response"    with st.spinner('Thinking...'):        for token in streamer.response_gen:            yield token                        def export_chat_history():    "export chat history"    chat_history = f'*{st.session_state["user_name"]}\'s chat history from {str(datetime.now().date())}*\n\n'        counter = 1    for message in st.session_state.messages:        if "source_string" not in message["content"]:            role = message["role"]            if role == "user":                chat_history += f'### {[counter]} {st.session_state["user_name"]}\n\n'            else:                chat_history += f'### {[counter]} LLM\n\n'                            chat_history += f'{message["content"]}\n\n'        # sources        else:            if message["content"] != "source_string:NA":                source_content = message["content"]                source_content = source_content.replace("source_string:", "").replace("### Metadata:", "\n### Metadata:\n").replace("### Text:", "\n### Text:\n").replace(" ```", "```").replace("# Source", f"### {[counter]} Source")                                chat_history += "_**Sources**_:\n"                chat_history += "<details>\n"                chat_history += source_content                chat_history += "</details>\n\n"            counter += 1                return chat_historydef ui_upload_docs():    "UI section for uploading your own documents"        # upload your own documents        st.sidebar.markdown("# Upload your own documents", help = "Enter the name of your corpus in the `Corpus name` field. If named `temporary`, it will be able to be written over after your session.")        # paste a list of web urls    st.session_state["own_urls"] = st.sidebar.text_input(       "URLs",       value="" if "own_urls" not in st.session_state else st.session_state["own_urls"],       help="A comma separated list of URLs."    )        st.session_state["uploaded_file"] = st.sidebar.file_uploader("Upload your own documents",type=[".zip", ".docx", ".doc", ".txt", ".pdf", ".csv"], help="Upload either a single `metadata.csv` file, with at least one column named `web_filepath` with the web addresses of the .html or .pdf documents, or upload a .zip file that contains a folder named `corpus` with the .csv, .doc, .docx, .txt, or .pdf files inside. You can optionally include a `metadata.csv` file in the zip file at the same level as the `corpus` folder, with at least a column named `filename` with the names of the files. If you want to only include certain page numbers of PDF files, in the metadata include a column called 'page_numbers', with the pages formatted as e.g., '1,6,9:12'.")        st.session_state["process_corpus_button"] = st.sidebar.button('Process corpus', help="Click if you uploaded your own documents or pasted your own URLs.")        def ui_model_params():    "UI section for selected LLM and corpus model parameters"        # model params    st.sidebar.markdown("# Model parameters", help="Click the `Reinitialize model` button if you change any of these parameters.")    # which_llm    st.session_state["selected_llm"] = st.sidebar.selectbox(       "Which LLM",       options=st.session_state["llm_dict"].name,       index=tuple(st.session_state["llm_dict"].name).index("mistral-docsgpt") if "selected_llm" not in st.session_state else tuple(st.session_state["llm_dict"].name).index(st.session_state["selected_llm"]),       help="Which LLM to use."    )    # which corpus    st.session_state["selected_corpus"] = st.sidebar.selectbox(       "Which corpus",       options=["None"] + sorted([x for x in list(st.session_state["corpora_dict"].name) if "temporary" not in x or x == f"temporary_{st.session_state['db_name']}"]), # don't show others' temporary corpora       index=0 if "selected_corpus" not in st.session_state else tuple(["None"] + sorted([x for x in list(st.session_state["corpora_dict"].name) if "temporary" not in x or x == f"temporary_{st.session_state['db_name']}"])).index(st.session_state["selected_corpus"]),       help="Which corpus to contextualize on."    )        def ui_advanced_model_params():    "UI section for advanced model parameters"        with st.sidebar.expander("Advanced model parameters"):        # renaming new corpus        st.session_state["new_corpus_name"] = st.text_input(           "Uploaded corpus name",           value=f"temporary_{st.session_state['db_name']}" if "new_corpus_name" not in st.session_state else st.session_state["new_corpus_name"],           help="The name of the new corpus you are processing. It must be able to be a SQL database name, so only lower case, no special characters, no spaces. Use underscores."        )                # similarity top k        st.session_state["similarity_top_k"] = st.slider(           "Similarity top K",           min_value=1,           max_value=20,           step=1,           value=4 if "similarity_top_k" not in st.session_state else st.session_state["similarity_top_k"],           help="The number of contextual document chunks to retrieve for RAG."        )                # n_gpu layers        st.session_state["n_gpu_layers"] = 100 if "n_gpu_layers" not in st.session_state else st.session_state["n_gpu_layers"]                # temperature        st.session_state["temperature"] = st.slider(           "Temperature",           min_value=0,           max_value=100,           step=1,           value=0 if "temperature" not in st.session_state else st.session_state["temperature"],           help="How much leeway/creativity to give the model, 0 = least creativity, 100 = most creativity."        )                # max_new tokens        st.session_state["max_new_tokens"] = st.slider(           "Max new tokens",           min_value=16,           max_value=16000,           step=8,           value=512 if "max_new_tokens" not in st.session_state else st.session_state["max_new_tokens"],           help="How long to limit the responses to (token ≈ word)."        )                # context window        st.session_state["context_window"] = st.slider(           "Context window",           min_value=500,           max_value=50000,           step=100,           value=4000 if "context_window" not in st.session_state else st.session_state["context_window"],           help="How large to make the context window for the LLM. The maximum depends on the model, a higher value might result in context window too large errors."        )                # memory limit        st.session_state["memory_limit"] = st.slider(           "Memory limit",           min_value=80,           max_value=80000,           step=8,           value=2048 if "memory_limit" not in st.session_state else st.session_state["memory_limit"],           help="How many tokens (words) memory to give the chatbot."        )                # system prompt        st.session_state["system_prompt"] = st.text_input(           "System prompt",           value=""  if "system_prompt" not in st.session_state else st.session_state["system_prompt"],           help="What prompt to initialize the chatbot with."        )        # params that affect the vector_db        st.markdown("# Vector DB parameters", help="Changing these parameters will require remaking the vector database and require a bit longer to run. Push the `Reinitialize model and remake DB` button if you change one of these.")                # chunk overlap        st.session_state["chunk_overlap"] = st.slider(           "Chunk overlap",           min_value=0,           max_value=1000,           step=1,           value=200 if "chunk_overlap" not in st.session_state else st.session_state["chunk_overlap"],           help="How many tokens to overlap when chunking the documents."        )                # chunk size        st.session_state["chunk_size"] = st.slider(           "Chunk size",           min_value=64,           max_value=6400,           step=8,           value=512 if "chunk_size" not in st.session_state else st.session_state["chunk_size"],           help="How many tokens per chunk when chunking the documents."        )                st.session_state["reinitialize_remake"] = st.button('Reinitialize model and remake DB', help="Click if you make any changes to the vector DB parameters.")            st.session_state["reinitialize"] = st.sidebar.button('Reinitialize model', help="Click if you change the `Which LLM` or `Which corpus` options, or any of the advanced parameters.")        def ui_lockout_reset():    "UI lockout dropdown and reset button"        lockout_options = [3, 10, 15, 20]    st.session_state["last_used_threshold"] = st.sidebar.selectbox(       "Lockout duration",       options=lockout_options,       index=0 if "last_used_threshold" not in st.session_state else lockout_options.index(st.session_state["last_used_threshold"]),       help="How many minutes after each interaction to continue reserving your session."    )    st.session_state["reset_memory"] = st.sidebar.button("Reset model's memory", help="Reset the model's short-term memory to start with a fresh model")                def ui_export_chat_end_session():    "UI elements, export chat end session and help contact"    if "messages" in st.session_state:        st.session_state["export_chat_button"] = st.sidebar.download_button(            label="Export chat history",            data=export_chat_history(),            file_name="chat_history.MD",            help="Export the session's chat history to a formatted Markdown file. If you don't have a Markdown reader on your computer, post the contents to a [web app](http://editor.md.ipandao.com/en.html)"        )        # end session button    end_session = st.sidebar.button("End session", help="End your session and free your spot.")    if end_session:        clear_models()        record_use(free_up=True)        update_server_state("queue", [x for x in server_state["queue"] if x != st.session_state["user_name"]])        st.session_state["password_correct"] = False        st.rerun()        st.stop()            # help contact    st.sidebar.markdown("*For questions on how to use this application or its methodology, please write [Author](mailto:someone@example.com)*", unsafe_allow_html=True)