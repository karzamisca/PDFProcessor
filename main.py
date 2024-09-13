import fitz  # Also know as PyMuPDF, v1.24.10
import os #Built-in for Python 3.12.6
import re #Built-in for Python 3.12.6
from PyQt5 import QtWidgets, QtCore, QtGui #v5.15.11 


def extract_images_from_pdf(pdf_path, output_folder):
    pdf_document = fitz.open(pdf_path)
    images_folder = os.path.join(output_folder, 'images')
    os.makedirs(images_folder, exist_ok=True)

    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        image_list = page.get_images(full=True)
        for image_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_filename = os.path.join(images_folder, f"page_{page_number + 1}_image_{image_index + 1}.png")
            with open(image_filename, "wb") as image_file:
                image_file.write(image_bytes)
    pdf_document.close()


def split_sentences(text):
    sentence_endings = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s')
    return sentence_endings.split(text)


def extract_text_from_pdf(pdf_path, keyword, output_folder, num_sentences, direction):
    pdf_document = fitz.open(pdf_path)
    extracted_text = []
    sentences = []
    sentence_page_map = {}

    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        text = page.get_text()
        page_sentences = split_sentences(text)
        sentences.extend(page_sentences)
        sentence_page_map.update({i: page_number + 1 for i, _ in enumerate(page_sentences, start=len(sentences) - len(page_sentences))})

    keyword_indices = [i for i, s in enumerate(sentences) if keyword.lower() in s.lower()]

    for index in keyword_indices:
        if direction == "Forward":
            selected_sentences = sentences[index:index + num_sentences]
        elif direction == "Backward":
            selected_sentences = sentences[max(0, index - num_sentences + 1):index + 1]

        page_number = sentence_page_map.get(index, 1)

        extracted_text.append(f"Keyword found on Page {page_number}, Sentence {index + 1}:\n{' '.join(selected_sentences)}")

    pdf_document.close()

    if extracted_text:
        text_filename = os.path.join(output_folder, "extracted_text.txt")
        with open(text_filename, "w", encoding="utf-8") as text_file:
            text_file.write("\n\n".join(extracted_text))


def sanitize_filename(title):
    return "".join(c for c in title if c.isalnum() or c in (" ", "_", "-"))


def divide_pdf_into_chapters(pdf_path, output_folder):
    pdf_document = fitz.open(pdf_path)
    outline = pdf_document.get_toc()

    if not outline:
        QtWidgets.QMessageBox.warning(None, "Outline Error", "No document outline found.")
        return

    top_level_entries = [entry for entry in outline if entry[0] == 1]

    if not top_level_entries:
        QtWidgets.QMessageBox.warning(None, "Outline Error", "No top-level outline entries found.")
        return

    chapter_pages = {}
    for i, entry in enumerate(top_level_entries):
        level, title, page = entry
        if page >= 0:
            sanitized_title = sanitize_filename(title)
            chapter_pages[page] = sanitized_title

    sorted_pages = sorted(chapter_pages.keys())

    for i in range(len(sorted_pages)):
        start_page = sorted_pages[i]
        end_page = sorted_pages[i + 1] if i + 1 < len(sorted_pages) else len(pdf_document)

        start_page_adjusted = start_page - 1
        end_page_adjusted = end_page

        chapter_title = chapter_pages[start_page]
        chapter_pdf = fitz.open()

        for page_number in range(start_page_adjusted, end_page_adjusted):
            chapter_pdf.insert_pdf(pdf_document, from_page=page_number, to_page=page_number)

        chapter_filename = os.path.join(output_folder, f"{chapter_title}.pdf")
        if len(chapter_filename) > 255:
            chapter_filename = chapter_filename[:255]
        try:
            chapter_pdf.save(chapter_filename)
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Save Error", f"Failed to save chapter '{chapter_title}': {e}")
        finally:
            chapter_pdf.close()

    pdf_document.close()


class PDFProcessingApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("PDF Processing Tool")
        self.setGeometry(100, 100, 600, 600)

        self.input_folder_var = QtWidgets.QLineEdit(self)
        self.output_folder_var = QtWidgets.QLineEdit(self)
        self.input_file_var = QtWidgets.QLineEdit(self)
        self.text_var = QtWidgets.QCheckBox("Extract Text", self)
        self.image_var = QtWidgets.QCheckBox("Extract Images", self)
        self.chapter_var = QtWidgets.QCheckBox("Divide into Chapters", self)
        self.direction_var = QtWidgets.QComboBox(self)
        self.direction_var.addItems(["Forward", "Backward"])
        self.num_sentences_var = QtWidgets.QSpinBox(self)
        self.num_sentences_var.setMinimum(1)
        self.num_sentences_var.setValue(5)
        self.search_keyword_var = QtWidgets.QLineEdit(self)
        self.search_results_var = QtWidgets.QTextEdit(self)
        self.search_results_var.setReadOnly(True)

        input_folder_label = QtWidgets.QLabel("Input Folder:", self)
        output_folder_label = QtWidgets.QLabel("Output Folder:", self)
        input_file_label = QtWidgets.QLabel("Or Input File:", self)
        direction_label = QtWidgets.QLabel("Search/Extract Text Direction:", self)
        num_sentences_label = QtWidgets.QLabel("Number of Sentences:", self)
        search_keyword_label = QtWidgets.QLabel("Search/Extract Keyword:", self)

        browse_input_folder_btn = QtWidgets.QPushButton("Browse Folder", self)
        browse_output_folder_btn = QtWidgets.QPushButton("Browse", self)
        browse_input_file_btn = QtWidgets.QPushButton("Browse File", self)
        process_btn = QtWidgets.QPushButton("Process PDFs", self)
        search_btn = QtWidgets.QPushButton("Search Keyword", self)

        browse_input_folder_btn.clicked.connect(self.browse_input_folder)
        browse_output_folder_btn.clicked.connect(self.browse_output_folder)
        browse_input_file_btn.clicked.connect(self.browse_input_file)
        process_btn.clicked.connect(self.process_pdfs)
        search_btn.clicked.connect(self.search_keyword)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(input_folder_label)
        layout.addWidget(self.input_folder_var)
        layout.addWidget(browse_input_folder_btn)
        layout.addWidget(input_file_label)
        layout.addWidget(self.input_file_var)
        layout.addWidget(browse_input_file_btn)
        layout.addWidget(output_folder_label)
        layout.addWidget(self.output_folder_var)
        layout.addWidget(browse_output_folder_btn)
        layout.addWidget(self.text_var)
        layout.addWidget(self.image_var)
        layout.addWidget(self.chapter_var)
        layout.addWidget(direction_label)
        layout.addWidget(self.direction_var)
        layout.addWidget(num_sentences_label)
        layout.addWidget(self.num_sentences_var)
  
        layout.addWidget(search_keyword_label)
        layout.addWidget(self.search_keyword_var)
        layout.addWidget(process_btn)
        layout.addWidget(search_btn)
        layout.addWidget(self.search_results_var)

        self.setLayout(layout)

    def browse_input_folder(self):
        folder_selected = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Input Folder")
        self.input_folder_var.setText(folder_selected)

    def browse_output_folder(self):
        folder_selected = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Folder")
        self.output_folder_var.setText(folder_selected)

    def browse_input_file(self):
        file_selected = QtWidgets.QFileDialog.getOpenFileName(self, "Select Input File", filter="PDF files (*.pdf)")[0]
        self.input_file_var.setText(file_selected)

    def search_keyword(self):
        input_file = self.input_file_var.text()
        keyword = self.search_keyword_var.text()
        num_sentences = self.num_sentences_var.value()
        direction = self.direction_var.currentText()
        if not input_file or not keyword:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please select an input file and enter a keyword.")
            return
        results = self.search_keyword_in_pdf(input_file, keyword, num_sentences, direction)
        self.search_results_var.setPlainText(results)

    def search_keyword_in_pdf(self, pdf_path, keyword, num_sentences, direction):
        pdf_document = fitz.open(pdf_path)
        results = []
        sentences = []
        sentence_page_map = {}

        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)
            text = page.get_text()
            page_sentences = split_sentences(text)
            sentences.extend(page_sentences)
            sentence_page_map.update({i: page_number + 1 for i, _ in enumerate(page_sentences, start=len(sentences) - len(page_sentences))})

        keyword_indices = [i for i, s in enumerate(sentences) if keyword.lower() in s.lower()]

        for index in keyword_indices:
            if direction == "Forward":
                selected_sentences = sentences[index:index + num_sentences]
            elif direction == "Backward":
                selected_sentences = sentences[max(0, index - num_sentences + 1):index + 1]

            page_number = sentence_page_map.get(index, 1)
            results.append(f"Keyword found on Page {page_number}, Sentence {index + 1}:\n{' '.join(selected_sentences)}")

        pdf_document.close()
        return "\n\n".join(results)

    def process_pdfs(self):
        input_folder = self.input_folder_var.text()
        output_folder = self.output_folder_var.text()
        input_file = self.input_file_var.text()
        extract_text = self.text_var.isChecked()
        extract_images = self.image_var.isChecked()
        divide_chapters = self.chapter_var.isChecked()

        if not input_folder and not input_file:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please select either an input folder or an input file.")
            return
        if not output_folder:
            QtWidgets.QMessageBox.warning(self, "Output Error", "Please select an output folder.")
            return
        if not extract_text and not extract_images and not divide_chapters:
            QtWidgets.QMessageBox.warning(self, "Selection Error", "Please select at least one processing option.")
            return

        keyword = self.search_keyword_var.text()
        num_sentences = self.num_sentences_var.value()
        direction = self.direction_var.currentText()

        if input_file:
            pdf_paths = [input_file]
        else:
            pdf_paths = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith(".pdf")]

        for pdf_path in pdf_paths:
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            pdf_output_folder = os.path.join(output_folder, pdf_name)
            os.makedirs(pdf_output_folder, exist_ok=True)
            if extract_text and keyword:
                extract_text_from_pdf(pdf_path, keyword, pdf_output_folder, num_sentences, direction)
            if extract_images:
                extract_images_from_pdf(pdf_path, pdf_output_folder)
            if divide_chapters:
                divide_pdf_into_chapters(pdf_path, pdf_output_folder)

        QtWidgets.QMessageBox.information(self, "Processing Complete", "Processing has been completed successfully.")


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = PDFProcessingApp()
    window.show()
    app.exec_()