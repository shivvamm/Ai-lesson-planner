from flask import render_template, request, send_file, jsonify, redirect, url_for
from app import app
import os
import io
import weasyprint
import logging
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib import colors
from PIL import Image as PILImage
import base64
import fitz  # PyMuPDF
from app.utils import extract_text_from_pdf, extract_key_concepts, generate_lesson_plan, generate_image_from_text, create_pdf, generate_class_activity,generate_introduction,generate_main_body,generate_illustration_descriptions,create_html

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

pdf_folder_path = "storage"


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/extract_key_concepts', methods=["POST"])
def extract_key_concepts_route():
    try:
        print("hit")
        chapter_name = request.form.get("chapter_name")
        print("got chapter name")
        chapter_number = int(chapter_name.split()[1])  # Extract chapter number
        pdf_filename = f"fees10{chapter_number}.pdf"
        pdf_path = os.path.join(pdf_folder_path, pdf_filename)

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf_file:
                extracted_text = extract_text_from_pdf(pdf_file.read())

            if extracted_text:
                key_concepts = extract_key_concepts(extracted_text, chapter_name)
                # Now, split the key concepts into a list of concepts for HTML rendering
                formatted_key_concepts = key_concepts.split("\n") if key_concepts else []

                # Render the template with the extracted text and key concepts
                return render_template('keyconcepts.html', key_concepts=formatted_key_concepts, extracted_text=extracted_text)
        return render_template('keyconcepts.html', error="PDF not found or unable to extract text.")
    except Exception as e:
        logger.error(f"Error: {e}")
        return render_template('keyconcepts.html', error=str(e))

@app.route('/confirm_key_concepts', methods=["POST"])
def confirm_key_concepts():
    try:
        # Get the form data: edited key concepts and the extracted text
        edited_key_concepts = request.form.get("key_concepts")  # This will be the user-edited key concepts
        extracted_text = request.form.get("extracted_text")  # Extracted text from PDF

        # Split the key concepts to prepare for passing them to the generation functions
        key_concepts = edited_key_concepts.split("\n")

        # Check which section needs to be regenerated
        regenerate_section = request.form.get('regenerate_section')

        # Initialize variables for each section (default to empty)
        introduction = request.form.get('introduction') or ""
        main_body = request.form.get('main_body') or ""
        class_activity = request.form.get('class_activity') or ""
        illustration_1 = request.form.get('illustration_1') or ""
        illustration_2 = request.form.get('illustration_2') or ""

        # Regenerate only the selected section, if necessary
        if regenerate_section == "introduction":
            introduction = generate_introduction(extracted_text, key_concepts)
        elif regenerate_section == "main_body":
            main_body = generate_main_body(extracted_text, key_concepts)
        elif regenerate_section == "class_activity":
            class_activity = generate_class_activity(extracted_text, key_concepts)
        else:
            # If no section is specified, generate all parts
            introduction = generate_introduction(extracted_text, key_concepts)
            main_body = generate_main_body(extracted_text, key_concepts)
            class_activity = generate_class_activity(extracted_text, key_concepts)
            illustration_1_des = generate_illustration_descriptions(f"Please generate a detailed description for an infographic or diagram that visually represents the key concepts and main ideas of the chapter. The diagram should summarize the most important points of the chapter in a clear and engaging way, using visuals like charts, diagrams, timelines, or flowcharts. It should include the main ideas and concepts, with visual elements designed for educational purposes to help students better understand the core topics of the chapter. The design should be structured in a way that is easy to follow and visually appealing for students. Chapter Content: {extracted_text}")
            illustration_2_des = generate_illustration_descriptions(f"Please generate a detailed description for an image that shows a real-world application or example of the main concepts discussed in the chapter. The image should depict a real-world scene, a specific example, or a practical scenario where the key concepts are applied in everyday life. It should be realistic, educational, and help students connect the chapter's content to practical, real-world situations. The scene should clearly illustrate the relevance of the concepts in daily life, making the connection between theory and practice visible. Chapter Content: {extracted_text}")
            illustration_1 = generate_image_from_text(illustration_1_des)
            illustration_2 = generate_image_from_text(illustration_2_des)

        # Return all sections as part of the response
        # return render_template(
        #     'indexhtml', 
        #     introduction=introduction, 
        #     main_body=main_body,
        #     class_activity=class_activity, 
        #     extracted_text=extracted_text, 
        #     key_concepts=edited_key_concepts.split("\n")
        # )
        if regenerate_section:
            return render_template(
            'lesson.html', 
            introduction=introduction, 
            main_body=main_body,
            class_activity=class_activity, 
            extracted_text=extracted_text, 
            key_concepts=edited_key_concepts.split("\n"),
            illustration_1_base64=illustration_1,
            illustration_2_base64=illustration_2
            )
        return render_template(
        'lesson.html', 
        introduction=introduction, 
        main_body=main_body,
        class_activity=class_activity, 
        extracted_text=extracted_text, 
        key_concepts=edited_key_concepts.split("\n"),
        illustration_1_base64=illustration_1,
        illustration_2_base64=illustration_2
        )
        # return {
        #     'introduction': introduction,
        #     'main_body': main_body,
        #     'class_activity': class_activity,
        #     'extracted_text': extracted_text,
        #     'key_concepts': edited_key_concepts.split("\n")
        # }

    except Exception as e:
        logger.error(f"Error during lesson plan generation: {e}")
        return render_template('lesson.html', error="Error during lesson plan generation.")
    



@app.route('/download_lesson_plan', methods=["POST"])
def download_lesson_plan_route():
    try:
        introduction = request.form.get('introduction') or ""
        main_body = request.form.get('main_body') or ""
        class_activity = request.form.get('class_activity') or ""
        illustration_1 = request.form.get('illustration_1') or ""
        illustration_2 = request.form.get('illustration_2') or ""
        html_content = create_html(introduction, main_body, class_activity, illustration_1, illustration_2)
        pdf = weasyprint.HTML(string=html_content).write_pdf()
        pdf_stream = io.BytesIO(pdf)
        # Send the generated PDF as response
        return send_file(pdf_stream, as_attachment=True, download_name="lesson_plan.pdf", mimetype="application/pdf")
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify(error=str(e)), 500
    
@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.get_json()
    lesson_plan = data.get('lesson_plan')

    if not lesson_plan:
        return {'error': 'No lesson plan content provided'}, 400

    # Create PDF from lesson plan content
    pdf_buffer = create_pdf(lesson_plan)
    
    # Return PDF as a file response
    return send_file(pdf_buffer, as_attachment=True, download_name='lesson_plan.pdf', mimetype='application/pdf')
