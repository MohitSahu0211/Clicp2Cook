import streamlit as st
from PIL import Image
import json
import os
from google import genai

# Page Configuration
st.set_page_config(page_title="Scalecipe", page_icon="📜", layout="centered")

st.title("📜 Scalecipe: Digital Recipe Box & Smart Scaler")
st.write("Turn traditional handwritten cards or YouTube text transcripts into clean, scaled recipes!")

# Safe API Key loading for both Local PC and Streamlit Cloud
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = None

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

# Initialize session state
if "recipe_data" not in st.session_state:
    st.session_state.recipe_data = None

# Create Tabs for Input Methods & Saved Collection
tab1, tab2, tab3 = st.tabs(["📷 Handwritten Card", "🎥 YouTube Transcript", "📚 Saved Recipes"])

# --- TAB 1: Handwritten Card ---
with tab1:
    st.header("Digitize Handwritten Recipe")
    uploaded_file = st.file_uploader("Choose a photo of your recipe card...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Original Recipe Card", width='stretch')
        
        if st.button("✨ Extract Recipe from Image"):
            if not client:
                st.error("Gemini API Key is missing! Set GEMINI_API_KEY environment variable or in Streamlit secrets.")
            else:
                with st.spinner("Processing image strictly with AI..."):
                    try:
                        prompt = """
                        You are a strict data transcription tool. Transcribe the recipe from this image verbatim. 
                        Do not invent, swap, or alter ingredients or steps. Extract only what is written.
                        """
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=[image, prompt],
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
                        st.success("Recipe successfully extracted from image!")
                    except Exception as e:
                        st.error(f"Failed to parse recipe from image: {e}")

# --- TAB 2: YouTube Video URL ---
with tab2:
  st.header("Extract Recipe from YouTube Link")
  st.write(
      "Paste the public YouTube video link below (supports English, Hindi, or"
      " Marathi cooking videos):"
  )

  yt_url = st.text_input(
      "YouTube Video URL:",
      placeholder="https://www.youtube.com/watch?v=...",
  )

  if st.button("✨ Extract Recipe from YouTube Video"):
    if yt_url:
      if not client:
        st.error(
            "Gemini API Key is missing! Set GEMINI_API_KEY environment variable"
            " or in Streamlit secrets."
        )
      else:
        with st.spinner(
            "Gemini is analyzing the cooking video directly (this may take a"
            " moment)..."
        ):
          try:
            prompt = """
                        You are a strict data transcription tool. Watch this cooking video and extract the recipe verbatim.
                        CRITICAL RULES:
                        1. Do not invent, substitute, or alter ingredients or steps. Extract only what is shown or spoken in the video.
                        2. Map the extracted recipe strictly into the requested JSON schema.
                        """
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[
                    types.Content(
                        parts=[
                            types.Part(
                                file_data=types.FileData(file_uri=yt_url)
                            ),
                            types.Part(text=prompt),
                        ]
                    )
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
                                    "unit": {"type": "STRING"},
                                },
                                "required": ["name", "amount", "unit"],
                            },
                        },
                        "steps": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                        },
                    },
                    "required": [
                        "title",
                        "original_servings",
                        "ingredients",
                        "steps",
                    ],
                },
            },
        )
        st.session_state.recipe_data = json.loads(response.text)
        st.success("Successfully extracted recipe from YouTube video!")
      except Exception as e:
        st.error(f"Failed to parse recipe from video: {e}")
  else:
    st.warning("Please enter a YouTube video URL first.")
# --- TAB 3: Saved Recipes Collection ---
with tab3:
    st.header("📚 Your Saved Recipe Box")
    saved_recipes = load_saved_recipes()
    
    if not saved_recipes:
        st.info("No saved recipes found yet. Digitize a card or transcript and save it to your collection!")
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
    new_servings = st.slider(
        "Adjust servings to recalculate quantities:", 
        min_value=1, 
        max_value=24, 
        value=recipe.get("original_servings", 4)
    )
    
    # Calculate multiplier safely
    orig_servings = recipe.get("original_servings", 4)
    multiplier = new_servings / orig_servings if orig_servings else 1
    
    # Display Scaled Ingredients
    st.markdown(f"### 🛒 Ingredients (Scaled for {new_servings} servings)")
    for ing in recipe.get("ingredients", []):
        amount = ing.get("amount")
        scaled_amount = round(amount * multiplier, 2) if amount is not None else ""
        st.write(f"- **{scaled_amount} {ing.get('unit', '')}** of {ing.get('name', '')}")
        
    # Display Steps
    st.markdown("### 👩‍🍳 Instructions")
    for i, step in enumerate(recipe.get("steps", []), 1):
        st.write(f"**Step {i}:** {step}")
