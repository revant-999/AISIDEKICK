import os
from langchain_core.tools import tool
from unstructured.partition.pptx import partition_pptx

@tool
def read_presentation(file_path: str) -> str:
    """
    Reads the text content from a PowerPoint (.pptx) file.
    Use this tool whenever the user asks you to summarize, read, or extract notes from a PPT or PPTX file.
    Only pass the file name (e.g. 'sample_presentation.pptx') if it's in the sandbox folder.
    """
    base_path = "sandbox"
    # Ensure it's looking in the right folder based on the file tools setup
    full_path = file_path if file_path.startswith("sandbox") else os.path.join(base_path, file_path)
    
    if not os.path.exists(full_path):
        return f"Error: File {full_path} not found."
    
    try:
        elements = partition_pptx(filename=full_path)
        text_content = "\n".join([str(el) for el in elements])
        return f"Successfully extracted text from presentation. Content:\n\n{text_content}"
    except Exception as e:
        return f"Failed to extract text from {file_path}. Error: {str(e)}"
