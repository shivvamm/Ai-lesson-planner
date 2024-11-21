import os
import requests
from io import BytesIO
from PIL import Image as PILImage
import base64
import markdown2
import fitz  # PyMuPDF
from app import app



def markdown_to_html(md_text):
    html_output = markdown2.markdown(md_text)
    return html_output

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






def generate_introduction(extracted_text, key_concepts):
    deep_infra_api_key = app.config['DEEP_INFRA_API_KEY']
    base_url = "https://api.deepinfra.com/v1/openai"
    prompt = f"""
    Based on the following chapter content and key concepts, generate a well-structured and clear Introduction for a lesson plan on the chapter and make it engaging and intresting it should be short and precise. The Introduction should:
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
    Based on the following chapter content and key concepts, generate the main body of the lesson plan and make it engaging precise and clear. The Main Body should:
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
    Based on the following chapter content and key concepts, generate a class activity for the lesson plan and make it engaging precise and clear. The activity should:
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
    introduction_html_output = markdown_to_html(introduction)
    main_body_html_output = markdown_to_html(main_body)
    class_activity_html_output = markdown_to_html(class_activity)
    html_content = f"""
   <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your PDF Title</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            padding: 0;
            line-height: 1.6;
        }}
        .content {{
            max-width: 800px;
            margin: auto;
        }}
        h1 {{
            text-align: center;
            color: #333;
        }}
        p {{
            margin-bottom: 15px;
            text-align: justify;
        }}
        .image-container {{
            text-align: center;
            margin: 20px 0;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        .section {{
            margin-bottom: 30px;
        }}
         .page-break {{
            page-break-before: always; /* Forces a page break before the section */
            page-break-inside: avoid;  /* Prevents a break inside the section */
        }}
    </style>
</head>
<body>
    <div class="content">
        <h1>Lesson Plan</h1>
        <div class="section">
        <h2>Introduction</h2>
            <p>{introduction_html_output}</p>
        </div>
        <div class="section image-container">
            <img src="{illustration_1}" alt="First Image Description">
        </div>
        <div class="section page-break">
          <h2>Main Body</h2>
            <p>{main_body_html_output}</p>
        </div>
        <div class="section image-container">
            <img src="{illustration_2}" alt="Second Image Description">
        </div>
        <div class="section page-break">
        <h2>Class Activity</h2>
            <p>{class_activity_html_output}</p>
        </div>
    </div>
</body>
</html>
    """
    return html_content
