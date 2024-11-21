// Function to upload the file and extract text and key concepts
function uploadFile() {
    const fileInput = document.getElementById("file-upload");
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.key_concepts) {
            document.querySelector('.key-concepts-section').style.display = 'block';
            document.getElementById("key-concepts").value = data.key_concepts.join('\n');
        } else {
            alert('Error extracting key concepts');
        }
    })
    .catch(error => {
        console.error('Error uploading file:', error);
    });
}

// Function to confirm the key concepts
function confirmKeyConcepts() {
    const keyConcepts = document.getElementById("key-concepts").value;

    fetch('/generate_lesson_plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ extracted_text: keyConcepts })
    })
    .then(response => response.json())
    .then(data => {
        if (data.lesson_plan) {
            document.querySelector('.lesson-plan-section').style.display = 'block';
            document.getElementById("lesson-plan").value = data.lesson_plan;
        } else {
            alert('Error generating lesson plan');
        }
    })
    .catch(error => {
        console.error('Error generating lesson plan:', error);
    });
}

// Function to generate the full lesson plan
function generateFullLessonPlan() {
    // This function can be extended if needed to compile all parts into a single lesson plan.
    alert('Full lesson plan generated!');
}

// Function to download the PDF
function downloadPDF() {
    alert('Downloading PDF...');
    // Implement logic to generate PDF and allow the user to download it.
}
