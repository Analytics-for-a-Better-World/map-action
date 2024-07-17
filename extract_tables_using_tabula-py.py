##### THIS FILE EXTRACTS AND CLEANS TABLES FROM A PDF FILE #####

# -------------------------------------------------------------- 
#### PROBLEMS ####

# Different type of problems with current extraction
# 1. In case there are multiple tables on a page, it extracts all tables and names them separately, however in the separate 
#    files you see all of the tables from that page
# 2. If the lay-out of the table is not standard, it does not extract the table well
# 2.a It considers comma's as seperators, while they are decimal seperators
# 3. The content page is considered a table 

#### SOLUTIONS ####

# 1. None yet
# 2. 1. Using clean_csv.ipynb I tried, after extracting to clean up the csv's 
# 2. 2. Using extract_pdf_tabula.py I tried, after extracting to figure out the ratio of seperators to rows, to determine of 
#       the table is wrongly split
# 2.a. 1. set the locale to French Madagascar
#       2. set the java options to French Madagascar
#       3. set the encoding to UTF-8 or ANSI
#       4. set the delimiter to a semicolon
#       5. different packages, but it also did not work
# 3. Fixed by deleting the tables called table des matieres, however other languages should be included later as well

# -------------------------------------------------------------- 
import fitz  # PyMuPDF
import os
import pandas as pd
import re
import tabula
from datetime import datetime
from tabula.io import read_pdf
from unidecode import unidecode

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

def extract_tables_and_captions(pdf_path) -> list:
    """
    Extracts tables and their corresponding captions from a PDF document.

    Args:
        pdf_path (str): The file path of the PDF document to extract tables from.

    Returns:
        A list of tuples, where each tuple contains a table caption (str) and a pandas DataFrame object representing the
        table data.
    """
    # Open the PDF document using PyMuPDF (formerly fitz)
    pdf_document = fitz.open(pdf_path)
    tables_and_captions = []

    # Loop through each page in the PDF document
    for page_number in range(pdf_document.page_count):
        # Load the current page using PyMuPDF
        page = pdf_document.load_page(page_number)
        # Extract the text content of the page
        page_text = page.get_text("text")
        # Split the text content into individual lines
        page_lines = page_text.split("\n")

        # Extract tables on the current page using tabula
        try:
            tables = tabula.read_pdf(pdf_path, pages=page_number + 1, multiple_tables=True) # , java_options=java_options
        except:
            continue
        # Find the lines on the current page that contain table content
        table_lines = []
        for i, line in enumerate(page_lines):
            for table in tables:
                # Check if any cell in the table is present in the current line
                if any(cell in line for cell in table.astype(str).values.flatten()):
                    # Add the line index and corresponding table to the list
                    table_lines.append((i, table))
                    break

        # Find the captions for each table and add them to the output list
        for line_index, table in table_lines:
            # Search for the caption above the table
            for i in range(line_index - 1, -1, -1):
                candidate_caption = page_lines[i].strip()

                candidate_caption_original = candidate_caption

                # Make candidate caption lowercase and remove any leading or trailing punctuation
                candidate_caption = candidate_caption.lower().strip(".,;:!?")

                # Set candidate caption to only letters without accents
                candidate_caption = unidecode(candidate_caption)

                # Check if the candidate caption is not empty and starts with "Table"
                if candidate_caption.startswith(("table", "tableau", "table", "quadro", "tabela")) \
                    and 'below shows' not in candidate_caption\
                    and 'above shows' not in candidate_caption\
                    and 'table des matieres' not in candidate_caption\
                    and 'indice' not in candidate_caption\
                    and 'índice' not in candidate_caption\
                    and re.search('\d', candidate_caption):
                    tables_and_captions.append((candidate_caption_original, table))
                    break

    # Close the PDF document and return the list of tables and captions
    pdf_document.close()

    return tables_and_captions

def save_tables_as_csv(tables_and_captions, pdf_name) -> str:
    """
    Saves tables extracted from a PDF document as CSV files.

    Args:
        tables_and_captions (list): A list of tuples, where each tuple contains a table caption (str) and a pandas
        DataFrame object representing the table data.
        pdf_name (str): The name of the PDF document from which the tables were extracted.

    Returns:
        folder_name (str): the name of the folder in which the tables are saved.
    """

    # Create a folder to save the CSV files
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{pdf_name}_{current_time}"
    folder_path = os.path.join(os.path.dirname(__file__), 'output_csv',folder_name)

    os.makedirs(folder_path, exist_ok=True)

    # Save each table as a CSV file
    for caption, table in tables_and_captions:
        # Remove any invalid characters from the filename
        sanitized_filename = "".join([c if c.isalnum() else "_" for c in caption])
        sanitized_filename = f"{sanitized_filename}.csv"
        # Save the table as a CSV file in the folder, choose encoding="ANSI" for French characters
        table.to_csv(os.path.join(folder_path, sanitized_filename), index=False, sep=";", encoding="utf-8")

    return folder_path

def split_columns(csv_file: str) -> None:
    """ This function reads a CSV file, searches for columns that contain specific patterns of data, 
    splits these columns into two new columns based on the contents of the original column, 
    drops the original column, and saves the modified CSV file.

    :param csv_file: The file path of the CSV file to be modified.
    :return: None
    """
    csv = pd.read_csv(csv_file, delimiter=';')
    csv = csv.fillna('')
    # create an empty list to store column names
    matching_columns = []

    # loop through each column and search for the pattern
    for col in csv.columns:
        pattern = r'^$|\d+,\d+|\w+\s+\w+'
        matches = csv[col].apply(lambda x: bool(re.search(pattern, str(x))))
        if matches.all():
            matching_columns.append(col)

    if len(matching_columns) > 0 :
        for column_to_split in matching_columns:
            # create new columns based on the contents of the original column
            csv[f'{column_to_split}_1'] = csv[column_to_split].apply(lambda x: '' if not x else x.split()[0] if len(x.split()) > 1 else x.split(',')[0] if ',' in x else '')
            csv[f'{column_to_split}_2'] = csv[column_to_split].apply(lambda x: '' if not x else ' '.join(x.split()[1:]) if len(x.split()) > 1 else x.split(',')[1] if ',' in x else '')

            # drop the original column
            csv.drop(column_to_split, axis=1, inplace=True)

            # Alter the original name of the csv file such that after the word 'Tableau' and the number, the word CHANGED is added
            csv_name = os.path.splitext(os.path.basename(csv_file))[0]
            # Add the word CHANGED to the csv name in front of the csv_name
            new_csv_name = "CHANGED_" + csv_name

            # new_csv_name = re.sub(r'(Tableau_\d_\d+)', r'\1_CHANGED', csv_name)
            csv_file_changed = os.path.join(os.path.dirname(csv_file), new_csv_name + '.csv')

            # save the modified CSV file
            csv.to_csv(csv_file_changed, index=False, sep=";")

def fix_commas(csv_file: str) -> None:
    """ This function reads a CSV file, checks whether it contains only one column, and if it does, fixes the commas in the data and saves the modified CSV file.

    :param csv_file: The file path of the CSV file to be modified.
    :return: None
    """
    csv = pd.read_csv(csv_file, delimiter=';')

    # If the csv only exists of one column, perform the following
    if len(csv.columns) == 1:
        csv = csv.fillna('')

        def split_and_join(string_to_split):
            # Split the string into words
            words = string_to_split.split()

            # Join the first word with a semicolon
            try:
                new_string = words[0] + ';'
            except:
                return string_to_split
            # Loop through the remaining words
            for word in words[:]:
                # If the word contains a comma, join it with a semicolon
                try:
                    if ',' in word:
                        new_string += word + ';'
                    # Elif the next word contains a comma, join it with a semicolon
                    elif ',' in words[words.index(word) + 1]:
                        new_string += word + ';'
                    # Otherwise, just join the word with a space
                    else:
                        new_string += word + ' '
                except:
                    new_string += word + ' '

            # Remove the trailing whitespace
            new_string = new_string.strip()
            
            return new_string

        # apply function to first column of dataframe
        first_col_name = csv.columns[0]
        csv[first_col_name] = csv[first_col_name].apply(split_and_join)

        # Now the first column should be split on all semicolons
        max_count = 0

        # Loop over all rows
        for index, row in csv.iterrows():
            # Count the number of semicolons in the row
            count = row[first_col_name].count(';')
            # Update the max count if the current count is greater
            if count > max_count:
                max_count = count

        # Determine the number of columns needed
        num_cols = max_count + 1

        # Split the column into new columns
        csv[['col{}'.format(i) for i in range(1, num_cols+1)]] = csv[first_col_name].str.split(';', expand=True)

        # Now replace all None values with ''
        csv = csv.fillna('')

        # Now delete the initial column first_col_name
        csv = csv.drop(columns=[first_col_name, 'col1'])
        
        # Alter the original name of the csv file such that after the word 'Tableau' and the number, the word CHANGED is added
        csv_name = os.path.splitext(os.path.basename(csv_file))[0]

        # Add the word CHANGED to the csv name in front of the csv_name
        new_csv_name = "CHANGED_" + csv_name

        # new_csv_name = re.sub(r'(Tableau_\d_\d+)', r'\1_CHANGED', csv_name)
        csv_file_changed = os.path.join(os.path.dirname(csv_file), new_csv_name + '.csv')

        # save the modified CSV file
        csv.to_csv(csv_file_changed, index=False, sep=";")

# Main function
def main():
    # Define the name of the PDF you want to extract tables from
    pdf_name = '.'

    # Obtain the path of the PDF file to extract tables from
    pdf_path = obtain_pdf_path(pdf_name)

    # Extract the tables and captions from the PDF document
    tables_and_captions = extract_tables_and_captions(pdf_path)
    
    # In case tables and captions are found, save them as CSV files and clean them
    if tables_and_captions:
        # Save the tables and captions as CSV files
        folder_name = save_tables_as_csv(tables_and_captions, pdf_name)
        # After extracting all the tables, clean them
        for csv in os.listdir(folder_name):
            csv_file = os.path.join(folder_name, csv)
            split_columns(csv_file)
            fix_commas(csv_file)
    else:
        print("No tables and captions found.")

if __name__ == '__main__':
    main()
