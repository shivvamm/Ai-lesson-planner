import os
import requests
from io import BytesIO
from PIL import Image as PILImage
import base64
import fitz  # PyMuPDF
from reportlab.platypus import ListFlowable, ListItem
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib import colors
from reportlab.lib.units import inch
from app import app


# Function to extract text from PDF
def extract_text_from_pdf(pdf_file: bytes) -> str:
    try:
        doc = fitz.open(stream=pdf_file, filetype="pdf")
        text = "".join([page.get_text("text") for page in doc])
        return text
    except Exception as e:
        app.logger.error(f"Error during PDF text extraction: {e}")
        return ""


# Function to extract key concepts using DeepInfra API
def extract_key_concepts(text: str, chapter_name: str) -> list:
    try:
        deep_infra_api_key = app.config['DEEP_INFRA_API_KEY']
        base_url = "https://api.deepinfra.com/v1/openai"
        
        messages = [
            {"role": "user", "content": 
             (
                 f"Please extract only the most relevant and important key concepts from the  {chapter_name} text content, which is from a class 6 "
                    f"NCERT Social Science book titled 'Exploring Society: India and Beyond'. Focus on key important events, "
                    f"important geographical features, societal structures, cultural aspects, and critical terms that will help a teacher "
                    f"to prepare a lesson plan. The extracted concepts should be concise and directly related to teaching the chapter, "
                    f"and should exclude unnecessary background details or non-essential information. Please provide a list of the key "
                    f"concepts and terms for teaching the chapter:\n\n{text}"
             )}
        ]
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {deep_infra_api_key}"},
            json={
                "model": "mistralai/Mistral-7B-Instruct-v0.1",
                "messages": messages,
                "response_format": {"type": "json_object"},
                "tool_choice": "auto"
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get('choices', [])[0].get('message', {}).get('content', [])
    except Exception as e:
        app.logger.error(f"Error extracting key concepts: {e}")
        return []


# Function to generate a lesson plan
def generate_lesson_plan(extracted_text: str, key_concepts: str) -> str:
    try:
        deep_infra_api_key = app.config['DEEP_INFRA_API_KEY']
        base_url = "https://api.deepinfra.com/v1/openai"
        
        prompt = f"""
        Based on the following textbook chapter content:

        {extracted_text}

        And the following key concepts:

        {key_concepts}

        Please generate a comprehensive lesson plan for teachers, structured into three distinct sections:

Introduction: Chapter name and Create an engaging introduction that captures students' attention and effectively introduces the key concepts of the chapter.
Output Format:
Paragraph: Start with a brief introduction to the key concept(s) of the chapter.
Key Question: Pose an open-ended question to engage students and spark curiosity.
Transition: Summarize the introduction and link it to the main body of the lesson.

Main Body: Present the core lesson material in a clear and organized manner. Focus on detailed explanations and relevant real-world examples that facilitate student understanding of the chapter's content. Ensure the material is logically sequenced.
Output Format:
Paragraph: Provide a detailed explanation of the key concept(s).
Bullet Points: List the critical components, definitions, or facts.
Detailed Explanation: Describe the process or concept step-by-step.
Transition: Conclude the main body and prepare the students for the class activity.

Class Activity: Design an interactive class activity that reinforces the lesson objectives and promotes active participation. The activity should seamlessly connect back to both the introduction and the main body of the lesson.
Output Format:

Activity Name: Provide a creative name for the activity.
Bullet Points: Describe the steps or materials required for the activity.
Objective: Explain how the activity supports learning and connects to the chapter’s content.
Debrief: Summarize the activity and link it back to the key concepts learned in the lesson.
        """
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {deep_infra_api_key}"},
            json={"model": "meta-llama/Meta-Llama-3.1-70B-Instruct", "messages": [{"role": "user", "content": prompt}]}
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        app.logger.error(f"Error generating lesson plan: {e}")
        return ""


# Function to generate an image based on text
def generate_image_from_text(text: str) -> BytesIO:
    try:
        deep_infra_api_key = app.config['DEEP_INFRA_API_KEY']
        url = "https://api.deepinfra.com/v1/inference/black-forest-labs/FLUX-1-schnell"
        payload = {"prompt": text}
        headers = {"Authorization": f"Bearer {deep_infra_api_key}"}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        image_data_base64 = response.json()['images'][0].split(",")[1]
        image_data = base64.b64decode(image_data_base64)
        image = PILImage.open(BytesIO(image_data))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer
    except Exception as e:
        app.logger.error(f"Error generating image: {e}")
        return BytesIO()


# Function to create the PDF from the lesson plan
def create_pdf(introduction, main_body, class_activity, illustration_1, illustration_2) -> BytesIO:

   
    buffer = BytesIO()
    
   
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
   
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    bullet_style = styles['Bullet']
    body_style = styles['BodyText']
    
   
    body_style.alignment = 4  # Justify the text
    body_style.leading = 14    # Line spacing
    heading_style.alignment = 1  # Center the headings
    
    
    story = []
    
    
    story.append(Paragraph("Lesson Plan", title_style))
    story.append(Spacer(1, 24))  # Add space after the title
    
    
    sections = lesson_plan.split("\n\n")
    
    for section in sections:
        if ':' in section:
            # Separate heading and content
            heading, content = section.split(":", 1)
            
            # Add heading to story with heading style (bold)
            story.append(Paragraph(f"<b>{heading.strip()}:</b>", heading_style))
            story.append(Spacer(1, 12))  # Add a small space after each heading
            
            # Check for bullet points and format appropriately
            if "\n" in content.strip():
                # If content contains line breaks, convert them into bullet points
                bullet_points = content.strip().split("\n")
                bullet_items = [ListItem(Paragraph(point.strip(), bullet_style)) for point in bullet_points]
                story.append(ListFlowable(bullet_items, bulletType='bullet'))
            else:
                # Add body text to story with body text style for paragraphs
                story.append(Paragraph(content.strip(), body_style))
            
            story.append(Spacer(1, 12))  # Add a small space after each section of text
            
            # Generate and add image based on the content (optional for visualization)
            image_buffer = generate_image_from_text(content.strip())
            img = ReportLabImage(image_buffer, width=8 * inch, height=3 * inch)
            img.hAlign = 'CENTER'  # Center align the image
            story.append(img)
            story.append(Spacer(1, 24))  # Add space after the image
    
    # Build the PDF document
    doc.build(story)
    
    # Move buffer pointer to start so it can be returned as a response
    buffer.seek(0)
    
    return buffer




def generate_introduction(extracted_text, key_concepts):
    deep_infra_api_key = app.config['DEEP_INFRA_API_KEY']
    base_url = "https://api.deepinfra.com/v1/openai"
    prompt = f"""
    Based on the following chapter content and key concepts, generate a well-structured and clear Introduction for a lesson plan on the chapter. The Introduction should:
    - Briefly introduce the subject matter and main themes of the lesson.
    - Explain the key concepts that will be covered in the lesson in a simple and engaging way.
    - Set expectations for what students will learn in the class.
    - Provide context for why these concepts are important for students to understand.
    
    Chapter Content: {extracted_text}
    Key Concepts: {key_concepts}
    """
    # Send the prompt to your model and get the response for the introduction
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {deep_infra_api_key}"},
        json={"model": "meta-llama/Meta-Llama-3.1-70B-Instruct", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1000}
    )
    response.raise_for_status()
    introduction = response.json()['choices'][0]['message']['content'].strip()
    return introduction


def generate_main_body(extracted_text, key_concepts):
    deep_infra_api_key = app.config['DEEP_INFRA_API_KEY']
    base_url = "https://api.deepinfra.com/v1/openai"
    prompt = f"""
    Based on the following chapter content and key concepts, generate the main body of the lesson plan. The Main Body should:
    - Provide detailed explanations of the key concepts, including definitions and relevant examples.
    - Include step-by-step processes or methodologies for teaching the concepts in a clear, structured manner.
    - Offer suggestions for how the teacher can engage students with real-world examples or historical data related to the chapter.
    - Ensure that the content is accessible and easy to follow for class 6 students, with age-appropriate language and explanations.
    - Include possible visuals, case studies, or resources that may enhance the lesson (optional).
    
    Chapter Content: {extracted_text}
    Key Concepts: {key_concepts}
    """
    # Send the prompt to your model and get the response for the main body
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {deep_infra_api_key}"},
        json={"model": "meta-llama/Meta-Llama-3.1-70B-Instruct", "messages": [{"role": "user", "content": prompt}]}
    )
    response.raise_for_status()
    main_body = response.json()['choices'][0]['message']['content'].strip()
    return main_body


def generate_class_activity(extracted_text, key_concepts):
    deep_infra_api_key = app.config['DEEP_INFRA_API_KEY']
    base_url = "https://api.deepinfra.com/v1/openai"
    prompt = f"""
    Based on the following chapter content and key concepts, generate a class activity for the lesson plan. The activity should:
    - Reinforce learning through hands-on engagement, critical thinking, or interactive participation.
    - Encourage collaboration among students, and foster discussion or problem-solving skills.
    - Be simple, engaging, and achievable within the time frame of a typical class.
    - Connect directly to the key concepts covered in the lesson and offer students a way to apply what they’ve learned.
    - If possible, suggest materials or resources (e.g., charts, maps, worksheets) that could support the activity.
    
    Chapter Content: {extracted_text}
    Key Concepts: {key_concepts}
    """
    # Send the prompt to your model and get the response for the class activity
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {deep_infra_api_key}"},
        json={"model": "meta-llama/Meta-Llama-3.1-70B-Instruct", "messages": [{"role": "user", "content": prompt}]}
    )
    response.raise_for_status()
    class_activity = response.json()['choices'][0]['message']['content'].strip()
    return class_activity



def generate_image_from_text(description: str):
    """
    Function to generate an image based on a description using DeepInfra's API.
    This will send the request to the provided API endpoint and return the image URL.
    """
    url = 'https://api.deepinfra.com/v1/inference/black-forest-labs/FLUX-1-schnell'
    headers = {
        "Authorization": f"bearer {app.config['DEEP_INFRA_API_KEY']}",  
        "Content-Type": "application/json"
    }
    
    # Prepare the payload
    payload = {
        "prompt": description
    }
    
    # Make the POST request to generate the image
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        # Assuming the API returns a URL to the generated image in the response
        data = response.json()
        image_base64 = data.get("images")[0]  # Assuming the first image in the list
        return image_base64
    else:
        # Handle any errors from the API
        response.raise_for_status()


def generate_illustration_descriptions(prompt: str) -> list:
    try:
        deep_infra_api_key = app.config['DEEP_INFRA_API_KEY']
        base_url = "https://api.deepinfra.com/v1/openai"
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {deep_infra_api_key}"},
            json={
                "model": "mistralai/Mistral-7B-Instruct-v0.1",
                "messages": messages,
                "response_format": {"type": "json_object"},
                "tool_choice": "auto"
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get('choices', [])[0].get('message', {}).get('content', [])
    except Exception as e:
        app.logger.error(f"Error extracting key concepts: {e}")
        return []
    


def create_html(introduction, main_body, class_activity, illustration_1, illustration_2):
    html_content = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    height: 100%;
                }}
                .container {{
                    width: 210mm;  /* A4 page width */
                    height: 297mm; /* A4 page height */
                    margin: auto;
                    padding: 20px;
                    box-sizing: border-box;
                }}
                .title {{
                    font-size: 24px;
                    font-weight: bold;
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .content {{
                    font-size: 14px;
                    line-height: 1.6;
                }}
                .image {{
                    width: 100%;
                    height: auto;
                    margin-top: 20px;
                    page-break-before: always;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="title">Lesson Plan</div>
                <div class="content">
                    <h2>Introduction</h2>
                    <p>{introduction}</p>
                    
                    <h2>Main Body</h2>
                    <p>{main_body}</p>
                    
                    <h2>Class Activity</h2>
                    <p>{class_activity}</p>
                </div>
                
                <img class="image" src="{illustration_1}" alt="Illustration 1">
                <img class="image" src="{illustration_2}" alt="Illustration 2">
            </div>
        </body>
    </html>
    """
    return html_content
