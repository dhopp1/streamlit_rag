from nlp_pipeline.nlp_pipeline import nlp_processorimport pandas as pdimport osimport shutilfrom zipfile import ZipFile import streamlit as st# set these to the install locations if on Windowswindows_tesseract_path = Nonewindows_poppler_path = Nonedef process_corpus(corpus_name, own_urls, uploaded_document):    "process an uploaded corpus"    temp_directory = "corpora/tmp_helper/"        # make temporary directory to handle files    if not os.path.exists(f"{temp_directory}"):        os.makedirs(f"{temp_directory}")            # if corpus name temporary, delete everything in the temporary files    if corpus_name == "temporary":        if os.path.exists(f"corpora/{corpus_name}/"):            shutil.rmtree(f"corpora/{corpus_name}/")        if os.path.exists(f"corpora/metadata_{corpus_name}.csv"):            os.remove(f"corpora/metadata_{corpus_name}.csv")                # just sent a list of websites    if own_urls != "":        url_list = own_urls.split(",")        metadata = pd.DataFrame({            "text_id": list(range(1, len(url_list)+1)),            "web_filepath": url_list        })                # create the processor        processor = nlp_processor(        	data_path = temp_directory,        	metadata_addt_column_names = [],        	windows_tesseract_path = windows_tesseract_path,        	windows_poppler_path = windows_poppler_path,        )                # sync the object's metadata to the local file        for col in metadata.columns:            processor.metadata[col] = metadata[col]                # download the files        processor.download_text_id(list(processor.metadata.text_id.values))                # convert the files to text        processor.convert_to_text(list(processor.metadata.text_id.values))                # sync to the local metadata file        processor.sync_local_metadata()            else:        # download the document        with open(f"{temp_directory}tmp.{uploaded_document.name.split('.')[-1]}", 'wb') as new_file:            new_file.write(uploaded_document.getbuffer())            new_file.close()                    # only uploaded a metadata CSV        if uploaded_document.name.split('.')[-1] == "csv":            metadata = pd.read_csv(f"{temp_directory}tmp.csv")            if "text_id" not in list(metadata.columns):                metadata["text_id"] = list(range(1, len(metadata) + 1))            metadata_addt_column_names = list(metadata.columns[~metadata.columns.isin(["text_id", "web_filepath", "local_raw_filepath", "local_txt_filepath", "detected_language"])])                        # write metadata out            processor = nlp_processor(            	data_path = temp_directory,            	metadata_addt_column_names = metadata_addt_column_names,            	windows_tesseract_path = windows_tesseract_path,            	windows_poppler_path = windows_poppler_path,            )                        # sync the object's metadata to the local file            for col in metadata.columns:                processor.metadata[col] = metadata[col]                        # download the files            processor.download_text_id(list(processor.metadata.text_id.values))                        # convert the files to text            processor.convert_to_text(list(processor.metadata.text_id.values))                        # sync to the local metadata file            processor.sync_local_metadata()                # uploaded a single .docx, .pdf, or .txt        elif uploaded_document.name.split('.')[-1] in ["pdf", "docx", "doc", "txt"]:            # write metadata out            processor = nlp_processor(            	data_path = temp_directory,            	metadata_addt_column_names = [],            	windows_tesseract_path = windows_tesseract_path,            	windows_poppler_path = windows_poppler_path,            )                        # create metadata            metadata = pd.DataFrame({                "text_id": 1,                "local_raw_filepath": f"{temp_directory}tmp.{uploaded_document.name.split('.')[-1]}",            }, index = [0])                        # sync the object's metadata to the local file            for col in metadata.columns:                processor.metadata[col] = metadata[col]                        # convert the files to text            processor.convert_to_text(list(processor.metadata.text_id.values))                        # sync to the local metadata file            processor.sync_local_metadata()                    # uploaded a zip        else:            with ZipFile(f"{temp_directory}tmp.zip", 'r') as zObject:                 zObject.extractall(path=temp_directory)                         # sync the object's metadata to the local file            provided_metadata = os.path.exists(f"{temp_directory}metadata.csv")                        if provided_metadata:                metadata = pd.read_csv(f"{temp_directory}metadata.csv")                metadata_addt_column_names = list(metadata.columns[~metadata.columns.isin(["text_id", "web_filepath", "local_raw_filepath", "local_txt_filepath", "detected_language"])])                if "text_id" not in list(metadata.columns):                    metadata["text_id"] = list(range(1, len(metadata) + 1))            else:                file_list = [x for x in os.listdir(f"{temp_directory}corpus/") if x.split(".")[-1] in ["txt", "docx", "doc", "pdf"]]                                metadata = pd.DataFrame({                    "text_id": list(range(1, len(file_list) + 1)),                    "filename": file_list                })                metadata_addt_column_names = []                            processor = nlp_processor(            	data_path = temp_directory,            	metadata_addt_column_names = metadata_addt_column_names,            	windows_tesseract_path = windows_tesseract_path,            	windows_poppler_path = windows_poppler_path,            )                        for col in metadata.columns:                processor.metadata[col] = metadata[col]                        # put the files in the right place and update the metadata            shutil.rmtree(f"{temp_directory}raw_files/")            shutil.copytree(f"{temp_directory}corpus/", f"{temp_directory}raw_files/")                        for file in os.listdir(f"{temp_directory}raw_files/"):                processor.metadata.loc[lambda x: x.filename == file, "local_raw_filepath"] = os.path.abspath(f"{temp_directory}raw_files/{file}")                                # convert the files to text            processor.convert_to_text(list(processor.metadata.text_id.values))                        # sync to the local metadata file            processor.sync_local_metadata()                    ### upload type independent actions            # move the .txt files to the appropriate place for RAG    if os.path.exists(f"corpora/{corpus_name}/"):        shutil.rmtree(f"corpora/{corpus_name}/")    shutil.copytree(f"{temp_directory}txt_files/", f"corpora/{corpus_name}/")        # adding file-path for telebot    processor.metadata["file_path"] = [os.path.abspath(f"corpora/{corpus_name}/{x}.txt") for x in processor.metadata["text_id"]]    processor.metadata.to_csv(f"{temp_directory}metadata.csv", index = False)        # move the metadata to the appropriate place for RAG    processor.metadata.to_csv(f"corpora/metadata_{corpus_name}.csv", index = False)    # update the corpora list    tmp_corpus= pd.DataFrame({        "name": corpus_name,        "text_path": f"corpora/{corpus_name}/",        "metadata_path": f"corpora/metadata_{corpus_name}.csv",    }, index = [0])        local_corpora_dict = pd.read_csv("metadata/corpora_list.csv")    new_corpora_dict = pd.concat([local_corpora_dict, tmp_corpus], ignore_index = True).drop_duplicates()    new_corpora_dict.to_csv("metadata/corpora_list.csv", index = False)        # clear out the tmp_helper directory    shutil.rmtree(temp_directory)        return new_corpora_dict                def process_corpus_example(bot, corpus_name, document):    "process an uploaded corpus"    temp_directory = "corpora/tmp_helper/"        # make temporary directory to handle files    if not os.path.exists(f"{temp_directory}"):        os.makedirs(f"{temp_directory}")            # if corpus name temporary, delete everything in the temporary files    if corpus_name == "temporary":        if os.path.exists(f"corpora/{corpus_name}/"):            shutil.rmtree(f"corpora/{corpus_name}/")        if os.path.exists(f"corpora/metadata_{corpus_name}.csv"):            os.remove(f"corpora/metadata_{corpus_name}.csv")        # just sent a list of websites    if type(document) == str:        url_list = document.split(",")        metadata = pd.DataFrame({            "text_id": list(range(1, len(url_list)+1)),            "web_filepath": url_list        })                # create the processor        processor = nlp_processor(        	data_path = temp_directory,        	metadata_addt_column_names = [],        	windows_tesseract_path = windows_tesseract_path,        	windows_poppler_path = windows_poppler_path,        )                # sync the object's metadata to the local file        for col in metadata.columns:            processor.metadata[col] = metadata[col]                # download the files        processor.download_text_id(list(processor.metadata.text_id.values))                # convert the files to text        processor.convert_to_text(list(processor.metadata.text_id.values))                # sync to the local metadata file        processor.sync_local_metadata()            else:        # download the document        file_info = bot.get_file(document.file_id)        downloaded_file = bot.download_file(file_info.file_path)            with open(f"{temp_directory}tmp.{file_info.file_path.split('.')[-1]}", 'wb') as new_file:            new_file.write(downloaded_file)            new_file.close()                    # only uploaded a metadata CSV        if file_info.file_path.split('.')[-1] == "csv":            metadata = pd.read_csv(f"{temp_directory}tmp.csv")            if "text_id" not in list(metadata.columns):                metadata["text_id"] = list(range(1, len(metadata) + 1))            metadata_addt_column_names = list(metadata.columns[~metadata.columns.isin(["text_id", "web_filepath", "local_raw_filepath", "local_txt_filepath", "detected_language"])])                        # write metadata out            processor = nlp_processor(            	data_path = temp_directory,            	metadata_addt_column_names = metadata_addt_column_names,            	windows_tesseract_path = windows_tesseract_path,            	windows_poppler_path = windows_poppler_path,            )                        # sync the object's metadata to the local file            for col in metadata.columns:                processor.metadata[col] = metadata[col]                        # download the files            processor.download_text_id(list(processor.metadata.text_id.values))                        # convert the files to text            processor.convert_to_text(list(processor.metadata.text_id.values))                        # sync to the local metadata file            processor.sync_local_metadata()                # uploaded a single .docx, .pdf, or .txt        elif file_info.file_path.split('.')[-1] in ["pdf", "docx", "doc", "txt"]:            # write metadata out            processor = nlp_processor(            	data_path = temp_directory,            	metadata_addt_column_names = [],            	windows_tesseract_path = windows_tesseract_path,            	windows_poppler_path = windows_poppler_path,            )                        # create metadata            metadata = pd.DataFrame({                "text_id": 1,                "local_raw_filepath": f"{temp_directory}tmp.{file_info.file_path.split('.')[-1]}",            }, index = [0])                        # sync the object's metadata to the local file            for col in metadata.columns:                processor.metadata[col] = metadata[col]                        # convert the files to text            processor.convert_to_text(list(processor.metadata.text_id.values))                        # sync to the local metadata file            processor.sync_local_metadata()                    # uploaded a zip        else:            with ZipFile(f"{temp_directory}tmp.zip", 'r') as zObject:                 zObject.extractall(path=temp_directory)                         # sync the object's metadata to the local file            provided_metadata = os.path.exists(f"{temp_directory}metadata.csv")                        if provided_metadata:                metadata = pd.read_csv(f"{temp_directory}metadata.csv")                metadata_addt_column_names = list(metadata.columns[~metadata.columns.isin(["text_id", "web_filepath", "local_raw_filepath", "local_txt_filepath", "detected_language"])])                if "text_id" not in list(metadata.columns):                    metadata["text_id"] = list(range(1, len(metadata) + 1))            else:                file_list = [x for x in os.listdir(f"{temp_directory}corpus/") if x.split(".")[-1] in ["txt", "docx", "doc", "pdf"]]                                metadata = pd.DataFrame({                    "text_id": list(range(1, len(file_list) + 1)),                    "filename": file_list                })                metadata_addt_column_names = []                            processor = nlp_processor(            	data_path = temp_directory,            	metadata_addt_column_names = metadata_addt_column_names,            	windows_tesseract_path = windows_tesseract_path,            	windows_poppler_path = windows_poppler_path,            )                        for col in metadata.columns:                processor.metadata[col] = metadata[col]                        # put the files in the right place and update the metadata            shutil.rmtree(f"{temp_directory}raw_files/")            shutil.copytree(f"{temp_directory}corpus/", f"{temp_directory}raw_files/")                        for file in os.listdir(f"{temp_directory}raw_files/"):                processor.metadata.loc[lambda x: x.filename == file, "local_raw_filepath"] = os.path.abspath(f"{temp_directory}raw_files/{file}")                                # convert the files to text            processor.convert_to_text(list(processor.metadata.text_id.values))                        # sync to the local metadata file            processor.sync_local_metadata()        # move the .txt files to the appropriate place for RAG    if os.path.exists(f"corpora/{corpus_name}/"):        shutil.rmtree(f"corpora/{corpus_name}/")    shutil.copytree(f"{temp_directory}txt_files/", f"corpora/{corpus_name}/")        # adding file-path for telebot    processor.metadata["file_path"] = [os.path.abspath(f"corpora/{corpus_name}/{x}.txt") for x in processor.metadata["text_id"]]    processor.metadata.to_csv(f"{temp_directory}metadata.csv", index = False)        # move the metadata to the appropriate place for RAG    processor.metadata.to_csv(f"corpora/metadata_{corpus_name}.csv", index = False)    # update the corpora list    tmp_corpus= pd.DataFrame({        "name": corpus_name,        "text_path": f"corpora/{corpus_name}/",        "metadata_path": f"corpora/metadata_{corpus_name}.csv",    }, index = [0])        local_corpora_dict = pd.read_csv("metadata/corpora_list.csv")    new_corpora_dict = pd.concat([local_corpora_dict, tmp_corpus], ignore_index = True).drop_duplicates()    new_corpora_dict.to_csv("metadata/corpora_list.csv", index = False)        # clear out the tmp_helper directory    shutil.rmtree(temp_directory)        return new_corpora_dict