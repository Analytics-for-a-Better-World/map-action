##### THIS FILE EXTRACTS AND CLEANS TABLES FROM A PDF FILE USING THE gmft PACKAGE.#####

# NOTES regarding the code:
# 1. The gmft package has a function which can extract the caption of a table. However this function does not work yet for 
# the examples we've tried it on. But, since the package is under development, it might be possible that this function will work in the future.
# Thus it might be something to keep in mind for future use.

# 2. A strange problem was encountered when trying to save the tables in a different function then where they have been extracted.
# Thus it was chosen to save the tables in the same function as where they were extracted (extract_tables_captions_and_save), 
# even though this does not help the readability of the code.
# -------------------------------------------------------------- 
import fitz  # PyMuPDF
import os
import pandas as pd
import re
from datetime import datetime
from gmft.pdf_bindings import PyPDFium2Document
from gmft import CroppedTable, TableDetector
from gmft import AutoTableFormatter
from gmft import AutoFormatConfig
from gmft import TATRFormatConfig
from IPython.display import display
from unidecode import unidecode

# Set the configuration for the table extraction
config = AutoFormatConfig()
config.enable_multi_header = True
config.semantic_spanning_cells = True
TATRFormatConfig.force_large_table_assumption = False
TATRFormatConfig.total_overlap_reject_threshold = 0.3
config.large_table_assumption = False

detector = TableDetector()

formatter = AutoTableFormatter()

def obtain_pdf_path(pdf_name: str) -> str:
    """"
    Obtain the path of the PDF file to extract tables from.
    
    Args:
        pdf_name (str): The name of the PDF document to extract tables from.
        
    Returns:
    pdf_path (str): The file path of the PDF document to extract tables from.
    """
    # Get the absolute path of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Create a path to the input_pdf folder relative to the script's location
    input_pdf_path = os.path.join(script_dir, 'input_pdf')

    # Choose the PDF document to extract tables from
    pdf_path = os.path.join(input_pdf_path, pdf_name)
    return pdf_path

def ingest_pdf(pdf_path) -> list[CroppedTable]:
    """
    Ingests a PDF document and extracts tables from it.

    Args:
        pdf_path (str): The file path of the PDF document to extract tables from.

    Returns:
        A list of CroppedTable objects representing the tables extracted from the PDF document.
    """

    doc = PyPDFium2Document(pdf_path)

    tables = []
    for page in doc:
        tables += detector.extract(page)
    return tables, doc

def extract_tables_captions_and_save(pdf_path, pdf_name, confidence_threshold = 0.995) -> list:
    """
    Extracts tables and their corresponding captions from a PDF document.

    Args:
        pdf_path (str): The file path of the PDF document to extract tables from.

    Returns:
        A list of tuples, where each tuple contains a table caption (str) and a pandas DataFrame object representing the
        table data.
    """
    tables, doc = ingest_pdf(pdf_path)

    pdf_document = fitz.open(pdf_path)
    tables_and_possible_captions = []
    tables_and_captions = []

    # Loop through each page in the PDF document
    for page_number in range(pdf_document.page_count):
        # Load the current page using PyMuPDF
        page = pdf_document.load_page(page_number)
        # Extract the text content of the page
        page_text = page.get_text("text")
        # Split the text content into individual lines
        page_lines = page_text.split("\n")

        # Find the bounding box on the current page that contain table content
        table_bboxs = []
        page_tables = [table for table in tables if table.page.page_number == page_number]
        for table in page_tables:
            table_bboxs.append((table.bbox, table))

        # Iterate over each table and its bounding box to find captions
        for bbox_table, table in table_bboxs:
            # Iterate over each line in the page to search for possible captions
            for i in range(len(page_lines)):
                candidate_caption = page_lines[i].strip()
                candidate_caption_original = candidate_caption

                # Make candidate caption lowercase and remove any leading or trailing punctuation
                candidate_caption = candidate_caption.lower().strip(".,;:!?")

                # Convert candidate caption to only letters without accents
                candidate_caption = unidecode(candidate_caption)

                # Check if the candidate caption is a valid table caption
                if candidate_caption.startswith(("table", "tableau", "table", "quadro", "tabela")) \
                    and 'below shows' not in candidate_caption\
                    and 'above shows' not in candidate_caption\
                    and 'shows' not in candidate_caption\
                    and 'table des matieres' not in candidate_caption\
                    and 'indice' not in candidate_caption\
                    and 'índice' not in candidate_caption\
                    and re.search('\d', candidate_caption):
                    tables_and_possible_captions.append((candidate_caption_original, table, page_number))

            # Check if there are multiple possible captions for this table
            possible_captions = [combi[0] for combi in tables_and_possible_captions if table == combi[1]]

            # If there is exactly one caption, add it to the list
            if len(possible_captions) == 1:
                tables_and_captions.append((possible_captions[0], table, page_number))

            # If there are multiple captions, find the closest one to the table    
            elif len(possible_captions) > 1:
                bbox_candidates = []
                # Find bounding boxes for all possible captions
                for possible_caption in possible_captions:
                    bbox_candidate_caption = page.search_for(possible_caption)
                    if bbox_candidate_caption:
                        bbox_candidate_caption = bbox_candidate_caption[0]
                        bbox_candidates.append((possible_caption, bbox_candidate_caption))

                # Find the caption closest to the table based on bounding box distance
                min_distance = float('inf')
                closest_caption = None
                for possible_caption, bbox_candidate_caption in bbox_candidates:
                    distance = abs(bbox_candidate_caption.y1 - bbox_table[1])
                    if distance < min_distance:
                        min_distance = distance
                        closest_caption = possible_caption
                tables_and_captions.append((closest_caption, table, page_number))

            # Continue to the next table if no possible captions were found    
            else:
                continue


    # Close the PDF document 
    pdf_document.close()

    # # # Create a folder to save the CSV files
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{pdf_name}_{current_time}"
    folder_path = os.path.join(os.path.dirname(__file__), 'output_csv',folder_name)

    os.makedirs(folder_path, exist_ok=True)

    tables_and_captions_above_threshold = [(caption, table, page_number) for caption, table, page_number in tables_and_captions if table.confidence_score >= confidence_threshold]  

    # Save each table as a CSV file
    for caption, table, page_number in tables_and_captions_above_threshold:
        # Remove any invalid characters from the filename
        sanitized_filename = "".join([c if c.isalnum() else "_" for c in caption])
        sanitized_filename = f"{sanitized_filename}_PAGE_NUMBER_{page_number+1}.csv"

        # Extract the table from the formatted text using the extractor function
        ft = formatter.extract(table)
        
        # Try/except is included such that in case of an error, the code will not stop and it outputs which table caused the error
        try:
            # Set an option to display the DataFrame without multi-level indexing
            with pd.option_context('display.multi_sparse', False):
                # Convert the formatted text to a pandas DataFrame
                df_table = ft.df()
                # Replace any NaN values in the DataFrame with an empty string
                df_table.fillna("", inplace=True)

            # Save the table as a CSV file in the folder, choose encoding="ANSI" for French characters
            df_table.to_csv(os.path.join(folder_path, sanitized_filename), index=False, sep=";", encoding="utf-8")
        except:
            print(f"Error in saving table: {caption}")

    return tables_and_captions

# Main function
def main():
    # Define the name of the PDF you want to extract tables from
    pdf_name = 'Madagascar - DHS Health 2021 - FR.pdf'

    # Obtain the path of the PDF file to extract tables from
    pdf_path = obtain_pdf_path(pdf_name)
    
    # Extract the tables and captions from the PDF document
    tables_and_captions = extract_tables_captions_and_save(pdf_path, pdf_name)
    
    # # In case tables and captions are found, save them as CSV files and clean them
    if not tables_and_captions:
        print("No tables and captions found.")

if __name__ == '__main__':
    main()
