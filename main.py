import fitz  # PyMuPDF
import os
import re
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk

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
            image_filename = os.path.join(images_folder, f"page_{page_number+1}_image_{image_index+1}.png")
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
    
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        text = page.get_text()
        sentences += split_sentences(text)
    
    keyword_indices = [i for i, s in enumerate(sentences) if keyword.lower() in s.lower()]

    for index in keyword_indices:
        if direction == "Forward":
            selected_sentences = sentences[index:index + num_sentences]
        elif direction == "Backward":
            selected_sentences = sentences[max(0, index - num_sentences + 1):index + 1]

        extracted_text.append(f"Keyword found in Sentence {index+1}:\n{' '.join(selected_sentences)}")

    pdf_document.close()

    if extracted_text:
        text_filename = os.path.join(output_folder, "extracted_text.txt")
        with open(text_filename, "w", encoding="utf-8") as text_file:
            text_file.write("\n\n".join(extracted_text))

def sanitize_filename(title):
    # Remove or replace invalid characters for filenames
    return "".join(c for c in title if c.isalnum() or c in (" ", "_", "-"))

def divide_pdf_into_chapters(pdf_path, output_folder):
    pdf_document = fitz.open(pdf_path)
    outline = pdf_document.get_toc()  # Get the table of contents

    if not outline:
        messagebox.showwarning("Outline Error", "No document outline found.")
        return

    # Filter out only top-level entries (level == 1)
    top_level_entries = [entry for entry in outline if entry[0] == 1]

    if not top_level_entries:
        messagebox.showwarning("Outline Error", "No top-level outline entries found.")
        return

    chapter_pages = {}
    for i, entry in enumerate(top_level_entries):
        level, title, page = entry
        if page >= 0:  # Valid page number
            # Sanitize title to be a valid filename
            sanitized_title = sanitize_filename(title)
            chapter_pages[page] = sanitized_title

    sorted_pages = sorted(chapter_pages.keys())

    for i in range(len(sorted_pages)):
        start_page = sorted_pages[i]
        end_page = sorted_pages[i+1] if i+1 < len(sorted_pages) else len(pdf_document)
        
        # Adjust start_page by subtracting 1 to include the correct range
        start_page_adjusted = start_page - 1
        end_page_adjusted = end_page

        chapter_title = chapter_pages[start_page]
        chapter_pdf = fitz.open()  # New PDF

        for page_number in range(start_page_adjusted, end_page_adjusted):
            chapter_pdf.insert_pdf(pdf_document, from_page=page_number, to_page=page_number)

        # Ensure filename is unique and valid
        chapter_filename = os.path.join(output_folder, f"{chapter_title}.pdf")
        # Truncate filename to avoid excessive length
        if len(chapter_filename) > 255:
            chapter_filename = chapter_filename[:255]
        try:
            chapter_pdf.save(chapter_filename)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save chapter '{chapter_title}': {e}")
        finally:
            chapter_pdf.close()

    pdf_document.close()

def browse_input_folder():
    folder_selected = filedialog.askdirectory()
    input_folder_var.set(folder_selected)

def browse_output_folder():
    folder_selected = filedialog.askdirectory()
    output_folder_var.set(folder_selected)

def process_pdfs():
    input_folder = input_folder_var.get()
    output_folder = output_folder_var.get()
    extract_text = text_var.get()
    extract_images = image_var.get()
    divide_chapters = chapter_var.get()

    if not input_folder or not output_folder:
        messagebox.showwarning("Input Error", "Please select both folders.")
        return

    if extract_text:
        keyword = simpledialog.askstring("Keyword", "Enter the keyword to search:")
        if not keyword:
            messagebox.showwarning("Keyword Error", "Please enter a keyword for text extraction.")
            return
        try:
            num_sentences = simpledialog.askinteger("Number of Sentences", "Enter the number of sentences to extract:")
        except ValueError:
            messagebox.showwarning("Sentence Number Error", "Please enter a valid number of sentences.")
            return
        direction = direction_var.get()
        if direction not in ["Forward", "Backward"]:
            messagebox.showwarning("Direction Error", "Please select a valid direction from the dropdown.")
            return

    if not extract_text and not extract_images and not divide_chapters:
        messagebox.showwarning("Selection Error", "Please select at least one option to extract.")
        return

    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(input_folder, filename)
            pdf_output_folder = os.path.join(output_folder, os.path.splitext(filename)[0])
            os.makedirs(pdf_output_folder, exist_ok=True)
            
            if extract_images:
                extract_images_from_pdf(pdf_path, pdf_output_folder)
            
            if extract_text:
                extract_text_from_pdf(pdf_path, keyword, pdf_output_folder, num_sentences, direction)
            
            if divide_chapters:
                divide_pdf_into_chapters(pdf_path, pdf_output_folder)
    
    messagebox.showinfo("Success", "Processing completed.")

# GUI setup
app = tk.Tk()
app.title("PDF Processing Tool")

input_folder_var = tk.StringVar()
output_folder_var = tk.StringVar()
text_var = tk.BooleanVar()
image_var = tk.BooleanVar()
chapter_var = tk.BooleanVar()
direction_var = tk.StringVar(value="Forward")

tk.Label(app, text="Input Folder:").pack(pady=5)
tk.Entry(app, textvariable=input_folder_var, width=50).pack(pady=5)
tk.Button(app, text="Browse", command=browse_input_folder).pack(pady=5)

tk.Label(app, text="Output Folder:").pack(pady=5)
tk.Entry(app, textvariable=output_folder_var, width=50).pack(pady=5)
tk.Button(app, text="Browse", command=browse_output_folder).pack(pady=5)

tk.Checkbutton(app, text="Extract Text", variable=text_var).pack(pady=5)
tk.Checkbutton(app, text="Extract Images", variable=image_var).pack(pady=5)
tk.Checkbutton(app, text="Divide into Chapters", variable=chapter_var).pack(pady=5)

tk.Label(app, text="Extract Text Direction:").pack(pady=5)
direction_dropdown = ttk.Combobox(app, textvariable=direction_var, values=["Forward", "Backward"])
direction_dropdown.pack(pady=5)

tk.Button(app, text="Process PDFs", command=process_pdfs).pack(pady=20)

app.mainloop()
