import streamlit as st
from PIL import Image
import json
import os
import time
from google import genai
from google.genai import types

# Page Configuration
st.set_page_config(page_title="Click2Cook", page_icon="📜", layout="centered")

st.title("📜 Click2Cook: Digital Recipe Box & Smart Scaler")
st.write("Extract recipes directly from YouTube links or handwritten cards, save them, and scale portions instantly!")

# API Key Setup
api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# File to store recipes locally
RECIPES_FILE = "saved_recipes.json"

def load_saved_recipes():
    if os.path.exists(RECIPES_FILE):
        with open(RECIPES_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_recipe_to_disk(recipe):
    recipes = load_saved_recipes()
    if not any(r["title"].lower() == recipe["title"].lower() for r in recipes):
        recipes.append(recipe)
        with open(RECIPES_FILE, "w") as f:
            json.dump(recipes, f, indent=4)
        return True
    return False

# Helper function with automatic retry for server busy (503) errors
def generate_recipe_with_retry(contents, prompt_config):
    max_retries = 3
    wait_time = 2
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=contents,
                config=prompt_config
            )
            return response
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    wait_time *= 2  # Exponential backoff
                    continue
            raise e

# Initialize session state
if "recipe_data" not in st.session_state:
    st.session_state.recipe_data = None

# Create Tabs for Input Methods & Saved Collection
tab1, tab2, tab3 = st.tabs(["📷 Handwritten Card", "🎥 YouTube Video Link", "📚 Saved Recipes"])

# --- TAB 1: Handwritten Card ---
with tab1:
    st.header("Digitize Handwritten Recipe")
    uploaded_file = st.file_uploader("Choose a photo of your recipe card...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Original Recipe Card", width='stretch')
        
        if st.button("✨ Extract Recipe from Image"):
            if not client:
                st.error("Gemini API key is missing! Set it in environment variables or Streamlit secrets.")
            else:
                with st.spinner("Gemini is reading your recipe card (retrying if servers are busy)..."):
                    try:
                        prompt = """
                        You are a strict data-entry parser. Look at this image and extract the recipe verbatim.
                        Map the extracted recipe strictly into the requested JSON schema. Do not invent or substitute ingredients.
                        """
                        config = {
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
                        response = generate_recipe_with_retry([image, prompt], config)
                        st.session_state.recipe_data = json.loads(response.text)
                        st.success("Successfully extracted recipe from image!")
                    except Exception as e:
                        st.error(f"Failed to process image due to server load: {e}. Please try clicking the button again in a few seconds.")

# --- TAB 2: YouTube Video Link ---
with tab2:
    st.header("Extract Recipe from YouTube Link")
    yt_url = st.text_input("Paste YouTube Video URL here:", placeholder="https://www.youtube.com/watch?v=...")

    if st.button("✨ Extract Recipe from Video"):
        if not yt_url:
            st.warning("Please enter a valid YouTube URL.")
        elif not client:
            st.error("Gemini API key is missing! Set it in environment variables or Streamlit secrets.")
        else:
            with st.spinner("Gemini is analyzing the cooking video directly (retrying if servers are busy)..."):
                try:
                    prompt = """
                    You are a strict data-entry parser. Watch this cooking video and extract the recipe verbatim.
                    Map the extracted recipe strictly into the requested JSON schema. Do not invent or substitute ingredients.
                    """
                    config = {
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
                    contents = [
                        types.Part.from_uri(file_uri=yt_url, mime_type="video/mp4"),
                        types.Part.from_text(text=prompt)
                    ]
                    response = generate_recipe_with_retry(contents, config)
                    st.session_state.recipe_data = json.loads(response.text)
                    st.success("Successfully extracted recipe from video!")
                except Exception as e:
                    st.error(f"Failed to process video due to server load: {e}. Please try clicking the button again in a few seconds.")

# --- TAB 3: Saved Recipes Collection ---
with tab3:
    st.header("📚 Your Saved Recipe Box")
    saved_recipes = load_saved_recipes()
    
    if not saved_recipes:
        st.info("No saved recipes found yet. Extract a recipe from an image or video and save it to your collection!")
    else:
        recipe_titles = [r["title"] for r in saved_recipes]
        selected_title = st.selectbox("Select a recipe to view and scale:", recipe_titles)
        
        if st.button("📂 Load Selected Recipe"):
            for r in saved_recipes:
                if r["title"] == selected_title:
                    st.session_state.recipe_data = r
                    st.success(f"Loaded '{selected_title}' successfully!")

# --- SHARED DASHBOARD: Scaler, Display & Save ---
if st.session_state.recipe_data:
    recipe = st.session_state.recipe_data
    
    st.markdown("---")
    st.header(recipe["title"])
    
    # Save Button
    if st.button("💾 Save Recipe to Local Collection"):
        is_saved = save_recipe_to_disk(recipe)
        if is_saved:
            st.success("Recipe successfully saved to your collection!")
        else:
            st.info("This recipe is already saved in your collection.")
    
    # Interactive Servings Slider
    st.subheader("⚖️ Dynamic Scaling")
    orig_servings = recipe.get("original_servings", 4)
    new_servings = st.slider(
        "Adjust servings to recalculate quantities:", 
        min_value=1, 
        max_value=24, 
        value=orig_servings
    )
    
    # Calculate multiplier safely
    multiplier = new_servings / orig_servings if orig_servings else 1
    
    # Display Scaled Ingredients
    st.markdown(f"### 🛒 Ingredients (Scaled for {new_servings} servings)")
    for ing in recipe.get("ingredients", []):
        amount = ing.get("amount", 0)
        scaled_amount = round(amount * multiplier, 2)
        st.write(f"- **{scaled_amount} {ing.get('unit', '')}** of {ing.get('name', '')}")
        
    # Display Steps
    st.markdown("### 👩‍🍳 Instructions")
    for i, step in enumerate(recipe.get("steps", []), 1):
        st.write(f"**Step {i}:** {step}")
