import streamlit as st
import json
import os
from google import genai
from google.genai import types

# Page Configuration
st.set_page_config(page_title="Scalecipe", page_icon="📜", layout="centered")

st.title("📜 Scalecipe: YouTube Video Recipe Extractor")
st.write("Paste a public YouTube cooking link below. Gemini will analyze the video directly and extract the recipe!")

# API Key Setup
api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

if "recipe_data" not in st.session_state:
    st.session_state.recipe_data = None

# YouTube Link Input Form
yt_url = st.text_input("YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("✨ Extract Recipe from Video"):
    if not yt_url:
        st.warning("Please enter a valid YouTube URL.")
    elif not client:
        st.error("Gemini API key is missing!")
    else:
        with st.spinner("Gemini is analyzing the cooking video directly..."):
            try:
                prompt = """
                You are a strict data-entry parser. Watch this cooking video and extract the recipe verbatim.
                Map the extracted recipe strictly into the requested JSON schema. Do not invent or substitute ingredients.
                """
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[
                        types.Part.from_uri(file_uri=yt_url, mime_type="video/mp4"),
                        types.Part.from_text(text=prompt)
                    ],
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": {
                            "type": "OBJECT",
                            "properties": {
                                "title": {"type": "STRING"},
                                "original_servings": {"type": "INTEGER"},
                                "ingredients": {
                                    "type": "ARRAY",
                                    "items": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "name": {"type": "STRING"},
                                            "amount": {"type": "NUMBER"},
                                            "unit": {"type": "STRING"}
                                        },
                                        "required": ["name", "amount", "unit"]
                                    }
                                },
                                "steps": {
                                    "type": "ARRAY",
                                    "items": {"type": "STRING"}
                                }
                            },
                            "required": ["title", "original_servings", "ingredients", "steps"]
                        }
                    }
                )
                st.session_state.recipe_data = json.loads(response.text)
                st.success("Successfully extracted recipe from video!")
            except Exception as e:
                st.error(f"Failed to process video: {e}")

# Display & Scale Dashboard
if st.session_state.recipe_data:
    recipe = st.session_state.recipe_data
    
    st.markdown("---")
    st.header(recipe["title"])
    
    orig_servings = recipe.get("original_servings", 4)
    new_servings = st.slider("Adjust servings:", min_value=1, max_value=24, value=orig_servings)
    multiplier = new_servings / orig_servings if orig_servings else 1
    
    st.markdown(f"### 🛒 Ingredients (Scaled for {new_servings} servings)")
    for ing in recipe.get("ingredients", []):
        amount = ing.get("amount", 0)
        scaled = round(amount * multiplier, 2)
        st.write(f"- **{scaled} {ing.get('unit', '')}** of {ing.get('name', '')}")
        
    st.markdown("### 👩‍🍳 Instructions")
    for i, step in enumerate(recipe.get("steps", []), 1):
        st.write(f"**Step {i}:** {step}")
