from PyPDF2 import PdfReader
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTChar
import re

pdf_file_reader = ''


# Retrieve the largest text on first page of pdf (usually the title)
def get_title(pdf_path):
    largest_font_size = 0
    largest_font_text = ""

    for page in extract_pages(pdf_path):
        for element in page:
            if isinstance(element, LTTextBox):
                text = element.get_text().strip()
                if text:
                    for text_line in element:
                        for char in text_line:
                            if isinstance(char, LTChar):
                                if char.size > largest_font_size:
                                    largest_font_size = char.size
                                    largest_font_text = text
        break
    return largest_font_text


# Parse PDF and use a newline to separate text between pages
def parse_pdf(pdf_path):
    global pdf_file_reader
    pdf_file_reader = PdfReader(pdf_path)
    return '\n'.join(page.extract_text() for page in pdf_file_reader.pages)



# Check if a line resembles a reference pattern
def is_reference_like(line):
    # Implement your own logic to check if a line resembles a reference pattern
    reference_patterns = ['[0-9]+\.', 'et al.', 'DOI:', 'References']
    return any(pattern in line for pattern in reference_patterns)

# Retrieve corresponding text between major section titles
def section_text(pdf_path):
    text = parse_pdf(pdf_path)
    lines = list(text.split('\n'))
    new_lines = []

    section_bank = ['Abstract', 'Introduction', 'Literature', 'Literature Survey', 'Literature Review', 'Methodology', 'Methods', 'Method', 'Materials and Methods',
                    'Materials and Method', 'Material and Methods', 'Material and Method', 'Methods and Materials',
                    'Methods and Material', 'Method and Materials', 'Method and Material', 'Experimental design, materials and methods', 'Findings', 'Results',
                    'Discussion', 'Discussions', 'Statistical Analysis', 'Conclusion', 'Conclusions', 
                    'Related Work', 'Background', 'Objective', 'Scope', 'Research Questions', 'Hypothesis', 'Research Design', 'Research Method',
                    'Data Collection', 'Data Analysis', 'Results and Discussion', 'Implications', 'Limitations', 'Future Work',
                    'Introduction and Background', 'Theoretical Framework', 'Research Methodology', 'Research Design and Methodology', 'Experimental Setup', 'Data Collection and Analysis',
                    'Experimental Results', 'Discussion and Analysis', 'Case Study', 'Model and Algorithms', 'Model Description',
                    'Algorithm Description', 'Empirical Evaluation', 'Case Analysis', 'Evaluation Metrics', 'Comparison with Related Work', 'Limitations and Future Work', 'Future Directions',
                    'Conclusion and Future Work', 'Practical Implications', 'Theoretical Implications', 'Significance of the Study', 'Summary', 'Summary and Conclusion', 'Summary and Future Outlook', 'Summary and Recommendations',
                   'Evaluation and Results','Discussion and Conclusion','Contribution','Contributions','Basic Structure and Operation Principle','Relevant Work','Foundations and Methods'
                   ]

    new_sections = ['Title']
    output = []

    # Use title.metadata() or get_title() for title depending on the case
    if new_sections[0] == 'Title':
        try:
            metadata_title = pdf_file_reader.metadata.title
        except ValueError:
            metadata_title = ''

        if len(str(metadata_title)) >= len(get_title(pdf_path)):
            output.append(metadata_title)
        else:
            output.append(get_title(pdf_path))

    # Find matches in PDF and section bank that are on a newline. Exclude reference-like lines.
    in_references_section = False  # Flag to indicate if we're in the References section
    for i in range(len(lines)):
        if 'References' in lines[i]:
            in_references_section = True
        if (re.sub(r'[^A-Za-z ]', '', lines[i]).strip().upper() in list(map(str.upper, section_bank))) and not is_reference_like(lines[i]) and not in_references_section:
            new_lines.append(lines[i])
            new_sections.append(re.sub(r'[^A-Za-z ]', '', lines[i]).strip())

    new_sections = [' '.join([word.capitalize() for word in element.split()]) for element in new_sections]

    start = 0
    for i, line in enumerate(new_lines):
        start = text.index(line, start) + len(line)
        if i == len(new_lines) - 1:
            if 'References' in text[start:]:
                end = text.index('References', start)
                output.append(text[start:end].replace('\n', ' ').strip())
            else:
                rest = text.split(line)
                output.append(rest[1].replace('\n', ' ').strip())
        else:
            end = text.index(new_lines[i + 1], start)
            output.append(text[start:end].replace('\n', ' ').strip())
    return output, new_sections
