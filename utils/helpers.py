import hashlib

def get_file_id(uploaded_file):
    if uploaded_file is not None:
        file_content = uploaded_file.read()
        uploaded_file.seek(0)
        return hashlib.md5(f"{uploaded_file.name}{len(file_content)}".encode()).hexdigest()[:8]
    return None

def clean_column_names(df):
    df.columns = df.columns.str.replace(r'[()"\']', '', regex=True)
    df.columns = df.columns.str.replace(r'\s+', '_', regex=True)
    df.columns = df.columns.str.strip()
    return df
