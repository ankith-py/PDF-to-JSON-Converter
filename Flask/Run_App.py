from flask import Flask, render_template, request, Response
from Text_Extraction import section_text
import requests
import json
import os
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

filename = ''
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Set as home page
@app.route('/')
# Allow user to choose and upload research article PDF
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    global filename

    if request.method == 'POST':
        # When user directly uploads file
        if 'file' in request.files:
            file = request.files['file']
            filename = file.filename
            # Check if uploaded file is a PDF
            if filename.endswith('.pdf'):
                # Get file and save to 'uploads' folder
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return render_template('output_success.html')
            else:
                return render_template('output_error.html')

        # When user inputs URL
        elif 'url' in request.form:
            url = request.form['url']
            response = requests.get(url)

            # Check if URL leads to a PDF
            if response.headers.get('content-type') == 'application/pdf':
                filename = url.split('/')[-1]
                # Add '.pdf' to end if content is a PDF and does not end in '.pdf'
                if not filename.endswith('.pdf'):
                    
                    filename += '.pdf'
                # Save to 'uploads' folder
                with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'wb') as pdf_file:
                    pdf_file.write(response.content)
                return render_template('output_success.html')
            else:
                #print(response.content)
                # Handle HTML content
                try:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # Extract text sections from HTML (use your existing function)
                    extracted_sections = extract_text_sections_from_html(soup)
                    print(extracted_sections)
                    filename = url.split('/')[-1]
                    # Add '.pdf' to end if content is a PDF and does not end in '.pdf'
                    if not filename.endswith('.pdf'):
                        filename += '.pdf'
                    # Save to 'uploads' folder
                    generate_pdf(extracted_sections, filename)

                    return render_template('output_success.html')
                except Exception as e:
                    print("Error processing HTML content:", e)
                    return render_template('output_error.html')

    return render_template('upload.html')

# Function to generate a PDF file
def generate_pdf(sections, output_file):
    doc = SimpleDocTemplate("uploads/"+output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    for section_name, section_content in sections.items():
        story.append(Paragraph(section_name, styles['Heading1']))
        story.append(Paragraph(section_content, styles['Normal']))

    doc.build(story)



def extract_text_sections_from_html(soup):
    # Define a dictionary with section names as keys and CSS classes as values
    section_classes = {
        'Background': 'background',  # Example CSS class for the 'Abstract' section
        'Introduction': 'introduction',  # Example CSS class for the 'Introduction' section
        # ... (add other section names and corresponding CSS classes)
    }

    # Initialize the dictionary to hold extracted sections
    extracted_sections = {}

    # Loop through the section names and corresponding CSS classes
    for section_name, css_class in section_classes.items():
        # Find elements with the specified CSS class using the lxml parser
        section_elements = soup.find_all(class_=css_class)
        if section_elements:
            # Extract text content from each section element
            section_content = ''
            for element in section_elements:
                section_content += str(element)  # Preserve HTML tags
            extracted_sections[section_name] = section_content
        

    return extracted_sections



@app.route('/preview')
# Neatly display extracted text with appropriate section titles and line breaks
def preview():
    filepath = rf"C:\Flask\uploads\{filename}"
    output, new_sections = section_text(filepath)

    dict_data = dict(zip(new_sections, output))
    content = []
    for key, value in dict_data.items():
        content.append(f'<b>{key}</b>:<br>{value}')

    response = '<br><br>'.join(content)
    return response


@app.route('/convert')
# Download newly converted JSON file with sections
def convert():
    filepath = rf"C:\Flask\uploads\{filename}"
    output, new_sections = section_text(filepath)
    dict_data = dict(zip(new_sections, output))

    json_data = json.dumps(dict_data, ensure_ascii=False)
    response = Response(json_data, mimetype='application/json')
    json_file_name = filename.replace('.pdf', '.json')
    response.headers["Content-Disposition"] = f'attachment; filename = {json_file_name}'
    return response


if __name__ == '__main__':
    app.run(debug=True)
