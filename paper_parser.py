import re
import fitz
import pathlib
import docx2txt
import concurrent.futures
from subprocess import PIPE, Popen
from config import REPLACEMENTS
from typing import List, Iterator


def clean_text(text: str, lower_case: bool) -> Iterator[str]:
    """
    Clean a text by performing several pre-processing steps and returning an iterator of individual characters.

    Args:
        text (str): The input text to be cleaned.
        lower_case (bool): If True, the text is converted to lowercase.

    Returns:
        An iterator that yields individual characters of the cleaned text.
    """
    if lower_case:
        text = text.lower()

    text = "\n".join(line.strip() for line in text.splitlines())

    for old, new in REPLACEMENTS.items():
        text = re.sub(old, new, text)

    text = text.encode("ascii", errors="ignore").decode("utf-8")
    regex = re.compile(r"\b(a|an|the)\b", re.UNICODE)
    text = re.sub(regex, " ", text)

    yield from text


def read_file_pdf(file_path: str, lower_case: bool) -> Iterator[str]:
    """
    Returns an iterator that yields cleaned text strings from the specified PDF file

    Args:
        file_path (str): The file path of the PDF file to read
        lower_case (bool): Whether or not to convert the text to lowercase before cleaning.

    Yields:
        Iterator[str]: An iterator that yields cleaned text strings from the PDF file
    
    Raises:
        Exception: If there is an error opening or reading the PDF file
    """
    
    try:
        doc = fitz.open(file_path)
        number_of_pages = doc.page_count
        for i in range(0, number_of_pages):
            content = doc.load_page(i).get_text("text", sort=True, flags=16)
            content += content
        content = "".join(list(clean_text(content, lower_case)))
        yield from content
    except Exception as e:
        raise Exception(f"Error reading PDF file: {str(e)}")

def read_file_docx(file_path: str, lower_case: bool) -> Iterator[str]:
    """
    Returns an iterator that yields cleaned text strings from the specified DOCX file.

    Args:
        file_path (str): The file path of the DOCX file to read
        lower_case (bool): Whether or not to convert the text to lowercase before cleaning

    Yields:
        Iterator[str]: An iterator that yields cleaned text strings from the DOCX file.

    """
    
    try:
        paragraphs = docx2txt.process(file_path)
        content = clean_text(paragraphs, lower_case)
        yield from content
    except Exception as e:
        raise Exception(f"Error reading DOCX file: {str(e)}")

def read_file_txt(file_path: str, lower_case: bool) -> Iterator[str]:
    """
    Returns an iterator that yields cleaned text strings from the specified TEXT file.

    Args:
        file_path (str): The file path of the DOCX file to read
        lower_case (bool): Whether or not to convert the text to lowercase before cleaning

    Yields:
        Iterator[str]: An iterator that yields cleaned text strings from the DOCX file.

    """
    try:
        content = open(file_path, 'r', encoding="unicode_escape", errors="strict", buffering=1).read()
        content = clean_text(content, lower_case)
        yield from content
    except Exception as e:
        raise Exception(f"Error reading TEXT file: {str(e)}")
        
def read_file_doc(file_path: str, lower_case: bool) -> Iterator[str]:
    """
    Returns an iterator that yields cleaned text strings from the specified DOC file.

    Args:
        file_path (str): The file path of the DOCX file to read
        lower_case (bool): Whether or not to convert the text to lowercase before cleaning

    Yields:
        Iterator[str]: An iterator that yields cleaned text strings from the DOCX file.

    """
    try:
        text = ""
        cmd = ["antiword", file_path]
        p = Popen(cmd, stdout=PIPE)
        stdout, stderr = p.communicate()
        text += stdout.decode("utf-8", "ignore")
        text = clean_text(text, lower_case)
        yield from text
    except Exception as e:
        raise Exception(f"Error reading TEXT file: {str(e)}")
    
def read_file(file_path: str, lower_case: bool) -> Iterator[str]:
    """
    Reads a file and returns an iterator that yields each line of text in the file.

    Args:
        file_path (str): The path to the file to be read.
        lower_case (bool): If True, the text will be converted to lowercase.

    Yields:
        Iterator[str]: An iterator that yields each line of text in the file.
    """
    
    suffix = pathlib.Path(file_path).suffix
    match suffix:
        case ".docx":
            return read_file_docx(file_path, lower_case)
        case ".pdf":
            return read_file_pdf(file_path, lower_case)
        case ".txt":
            return read_file_txt(file_path, lower_case)
        case ".doc":
            return read_file_doc(file_path, lower_case)
            

def read(file_path: List[str], lower_case: bool) -> Iterator[str]:
    """
    Reads a file and returns an iterator that yields each line of text in the file.

    If the specified location is a file, the function calls the "read_file" function to read the file. If the specified location is not a file, a ValueError is raised.
    
    Args:
        file_path (str): The path to the file to be read.
        lower_case (bool): If True, the text will be converted to lowercase.

    Raises:
        ValueError: _description_

    Returns:
        _type_: An iterator that yields each line of text in the file.

    Raises:
        ValueError: If the specified location is not a file.
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(read_file, f, lower_case): f for f in file_path}
        for future in concurrent.futures.as_completed(future_to_file):
            f = future_to_file[future]
            try:
                yield (f, future.result())
            except Exception as e:
                raise ValueError(f"Error processing file {f}: {e}")

if __name__ == "__main__":
    final_result = {}
    location = ["data/manish.doc", "data/jd.pdf"]
    for file_key, file_value in read(location, True):
        final_result[file_key] = file_value
    print(final_result)