### PDFProcessor
Functions:

    extract_images_from_pdf(pdf_path, output_folder):
        Extracts all images from each page of the provided PDF and saves them as .png files in the specified output folder.

    split_sentences(text):
        Splits the provided text into sentences using regular expressions. The splitting takes into account periods, abbreviations, and question marks.

    extract_text_from_pdf(pdf_path, keyword, output_folder, num_sentences, direction):
        Searches for a keyword in the text of a PDF, extracts a specific number of sentences before or after the keyword, and saves the result as a .txt file.

    sanitize_filename(title):
        Sanitizes a string (like a PDF chapter title) by removing special characters, leaving only alphanumeric characters, spaces, underscores, and hyphens. Used for naming output files.

    divide_pdf_into_chapters(pdf_path, output_folder):
        Divides a PDF into chapters based on its table of contents (TOC) and saves each chapter as a separate PDF file in the specified output folder.

Class:

    PDFProcessingApp(QtWidgets.QWidget):

        Represents the main GUI application for processing PDFs.

        __init__(self):
            Initializes the GUI by calling init_ui() to set up the interface.

        init_ui(self):
            Sets up the layout and elements (input fields, checkboxes, buttons, etc.) of the application's user interface.

        browse_input_folder(self):
            Opens a file dialog to select an input folder, setting the selected folder's path in the input folder field.

        browse_output_folder(self):
            Opens a file dialog to select an output folder, setting the selected folder's path in the output folder field.

        browse_input_file(self):
            Opens a file dialog to select a PDF file, setting the selected file's path in the input file field.

        search_keyword(self):
            Searches for the keyword in the selected PDF file using the user-provided direction and number of sentences. Displays the results in the output text area.

        search_keyword_in_pdf(self, pdf_path, keyword, num_sentences, direction):
            Searches for occurrences of a keyword in a PDF file and extracts a certain number of sentences based on the specified direction. Returns the results as text.

        process_pdfs(self):
            Processes one or more PDF files (from a folder or single file) based on user-selected options. It can extract text, extract images, or divide the PDF into chapters, saving the results in the specified output folder.