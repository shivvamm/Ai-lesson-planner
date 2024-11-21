# AI Lesson Planner Project

This repository contains the code for the **AI Lesson Planner** project. Below are the steps to set up the environment, install dependencies, and run the project.

## Setup Instructions

Follow these steps to set up the project on your local machine.

### 1. Clone the repository

First, clone the repository to your local machine using the following command:

```bash
git clone https://github.com/shivvamm/Ai-lesson-planner.git
```

### 2. Set up the environment

This project uses a Python virtual environment to manage dependencies. You will need to create and activate the virtual environment.

#### 2.1 Create a Virtual Environment

Navigate to the project folder and create a new virtual environment:

```bash
cd Ai-lesson-planner
python3 -m venv venv
```

This will create a folder called `venv` where all the dependencies will be installed.

#### 2.2 Activate the Virtual Environment

To activate the virtual environment, run:

- On **Linux/Mac**:

```bash
source venv/bin/activate
```

- On **Windows**:

```bash
venv\Scripts\activate
```

You should now see `(venv)` at the beginning of your terminal prompt, indicating that the virtual environment is activated.

### 3. Install the Required Dependencies

With the virtual environment activated, install the required dependencies by running:

```bash
pip install -r requirements.txt
```

This will install all necessary Python packages for the project.

### 4. Add Deep Infra Pi Configuration

In order to run the project, you need to add the **Deep Infra Pi** configuration to the `config.py` file. Follow these steps:

1. Open the `config.py` file in the `app` directory.
2. Add the following configuration to the file:

```python
# config.py

DEEP_INFRA_API_KEY = os.getenv("DEEP_INFRA_API_KEY", "YOUR_API_KEY")
```

Make sure to replace `your_deep_infra_api_key_here` with your actual API key from Deep Infra. You can obtain an API key by signing up at [Deep Infra](https://www.deepinfra.com/).

### 5. Run the Project

Once everything is set up, you can run the project using the following command:

```bash
python run.py
```

This will start the application, and it should now be running with the Deep Infra Pi configuration successfully integrated.

### 6. Troubleshooting

If you encounter any issues, please check the following:

- Ensure that you are using the correct Python version (Python 3.7 or higher is recommended).
- Make sure all dependencies are installed correctly by running `pip install -r requirements.txt` again.
- Verify your API key for Deep Infra Pi is valid and correctly added in the `config.py` file.

### 7. Additional Notes

- Make sure to deactivate your virtual environment once you are done working on the project by running:

```bash
deactivate
```

- The project is set up to use `PyMuPDF` for PDF processing. If you encounter any issues with `fitz` or other dependencies, refer to the troubleshooting section or check the related GitHub issues.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
