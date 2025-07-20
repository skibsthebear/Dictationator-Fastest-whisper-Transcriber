## How to Request Structured JSON Text Reformatting from Gemini 2.5 Flash (Python Tutorial)

This comprehensive guide teaches you how to use the Gemini 2.5 Flash API to send a large body of text (“wall of text”) for automatic reformatting. The task: get a structured `.json` response containing the improved text (with spelling, grammar, and formatting fixes) in a field called `"formatted-text"`. The guide assumes you are new to API programming and Python.

### Table of Contents

1. **Overview: Gemini 2.5 Flash and Structured Output**
2. **Prerequisites**
3. **Get a Gemini API Key**
4. **Python Environment Setup**
5. **Defining the JSON Schema for Response**
6. **Preparing Your Prompt for Reformatting**
7. **Example Python Code for a JSON Response**
8. **Extracting the `"formatted-text"` Output**
9. **Troubleshooting**
10. **Best Practices for JSON Output Generation**

### 1. Overview: Gemini 2.5 Flash and Structured Output

Gemini 2.5 Flash is a high-speed Google generative model that can process and transform text, offering output in plain text or structured formats (like JSON) [1][2]. You can control the response format by telling the model your required schema.

You can instruct Gemini to output JSON with improved and reformatted text by:

- Explicitly specifying a `response_schema` or
- Requesting JSON (with a certain structure) in your prompt and the API configuration

### 2. Prerequisites

- Python 3.9 or higher installed
- Google `genai` SDK (the Python client for Gemini)
- Internet connection
- Your Gemini API key (see below)

### 3. Get a Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/) and sign in with your Google account.
2. Find or generate a new API key in the dashboard (usually labeled “Get API Key”). Copy and keep it safe [3].
3. Store your key securely (as an environment variable is recommended).

**Example:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```
Or on Windows Command Prompt:
```cmd
set GEMINI_API_KEY=your-api-key-here
```

### 4. Python Environment Setup

1. **Install Google’s Gemini client SDK:**
   ```bash
   pip install google-generativeai
   ```

2. **(Optional) Install Pydantic if you want strong schema validation:**
   ```bash
   pip install pydantic
   ```

3. **Verify installation:**
   ```python
   import google.generativeai as genai
   ```

### 5. Defining the JSON Schema for Response

To ensure Gemini replies in your desired structure (e.g., with a `"formatted-text"` field), you must specify a schema using `response_schema` in the request configuration [2].

**Example Pydantic Schema:**
```python
from pydantic import BaseModel

class FormattedText(BaseModel):
    formatted_text: str
```
This class enforces the JSON structure:
```json
{"formatted_text": "Your improved, formatted text here"}
```

### 6. Preparing Your Prompt for Reformatting

Be *explicit* in your instruction. Example:
> "Reformat the following text. Add appropriate new lines, insert quotes when needed, and fix all spelling, tense, and grammatical errors. Return ONLY the corrected text as 'formatted_text' in a JSON object."

### 7. Example Python Code for a JSON Response

```python
import os
from google import generativeai as genai
from pydantic import BaseModel

# --- Step 1: Set up your key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=api_key)

# --- Step 2: Specify model and schema
class FormattedText(BaseModel):
    formatted_text: str

model = genai.Client()
wall_of_text = """
your original wall of text goes here. it might have bad grammar runon sentences no punctuation or typos.
"""

# --- Step 3: Prepare prompt
prompt = (
    "Reformat the following text. Add new lines, place quotations where appropriate, "
    "and correct spelling, tense, and grammar errors. Respond only with a JSON object "
    "formatted as {\"formatted_text\": \"...\"} that contains the improved text in the 'formatted_text' field:\n\n"
    f"{wall_of_text}"
)

# --- Step 4: Make the request
response = model.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_schema": FormattedText
    }
)
# Step 5: Print JSON response
print(response.text)        # As JSON string
print(response.parsed)      # Directly as a Python object
```
**Note:**
- `response.text` gives you the raw JSON string.
- `response.parsed` gives you an object validated by Pydantic (`FormattedText`) [2][4].
- Replace `your original wall of text goes here...` with your actual input.

### 8. Extracting the `"formatted-text"` Output

If you use the code above, you can directly access the improved text with:
```python
print(response.parsed.formatted_text)
```
If working with raw JSON:
```python
import json

resp_json = json.loads(response.text)
print(resp_json["formatted_text"])
```

### 9. Troubleshooting

- If Gemini wraps the output in backticks (```) or includes extra text, you may need to clean the response. See [discussion of this workaround][12].
- Make sure your API key is valid and set in the environment.
- Ensure you use a supported version of Google’s generativeai SDK.

---

### 10. Best Practices for JSON Output Generation

- Always validate the API’s response against your schema, especially if you intend to automate downstream tasks.
- Give clear, precise instructions in prompts and schema.
- Use structured response configuration whenever possible, as this is more robust than relying on prompt wording alone [9][21].
- For larger-scale or enterprise use, explore the Vertex AI platform’s enhanced controls [14][17].
