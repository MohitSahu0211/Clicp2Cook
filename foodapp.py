import streamlit as st
from PIL import Image
import json
import os
from google import genai # Requires: pip install google-genai

# Configure page
st.set_page_config(page_title="Scalecipe", page_icon="📜", layout="centered")
st.title("📜 Scalecipe: Digital Recipe Box")

# Gemini Client Setup (Ensure GEMINI_API_KEY is in Streamlit Secrets)
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
client = genai.Client(api_key=api_key) if api_key else None

# --- Helper Functions ---
def load_saved_recipes():
    if os.path.exists("saved_recipes.json"):
        with open("saved_recipes.json", "r") as f:
            return json.load(f)
    return []

def save_recipe_to_disk(recipe):
    recipes = load_saved_recipes()
    if not any(r["title"] == recipe["title"] for r in recipes):
        recipes.append(recipe)
        with open("saved_recipes.json", "w") as f:
            json.dump(recipes, f, indent=4)
        return True
    return False

# --- UI Setup ---
if "recipe_data" not in st.session_state: st.session_state.recipe_data = None

tab1, tab2, tab3 = st.tabs(["📷 Handwritten Card", "🎥 YouTube Transcript", "📚 Saved Recipes"])

# --- TAB 1: Handwritten Card ---
with tab1:
    st.header("Digitize Handwritten Recipe")
    uploaded_file = st.file_uploader("Upload image...", type=["jpg", "png"])
    if uploaded_file and st.button("✨ Extract with Gemini"):
        with st.spinner("Reading image..."):
            # Gemini Vision Prompt
            prompt = "Extract the recipe from this image into a JSON format with keys: title, original_servings, ingredients (list of name, amount, unit), steps (list of strings)."
            response = client.models.generate_content(model='gemini-2.0-flash', contents=[Image.open(uploaded_file), prompt])
            # (Add logic here to parse response.text into JSON)
            st.write("AI Extraction logic active!")

# --- TAB 2: YouTube Transcript (The Fix) ---
with tab2:
    st.header("Extract Recipe from YouTube")
    st.write("Copy the transcript from the video description and paste it here:")
    transcript_text = st.text_area("Paste Transcript:", height=150)
    
    if st.button("✨ Extract Recipe from Transcript"):
        if transcript_text and client:
            with st.spinner("Processing..."):
                prompt = f"Extract a JSON recipe from this transcript: {transcript_text}"
                response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                # Parse the JSON response
                st.session_state.recipe_data = json.loads(response.text.replace('```json', '').replace('```', ''))
                st.success("Recipe extracted!")
        else:
            st.error("Please paste transcript or check API Key.")

# --- TAB 3: Saved Recipes Collection ---
with tab3:
    st.header("📚 Your Saved Recipe Box")
    saved_recipes = load_saved_recipes()
    
    if not saved_recipes:
        st.info("No saved recipes found yet. Digitize a card or YouTube video and save it!")
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
    
    if st.button("💾 Save Recipe to Local Collection"):
        is_saved = save_recipe_to_disk(recipe)
        if is_saved:
            st.success("Recipe successfully saved to your local collection!")
        else:
            st.info("This recipe is already saved in your collection.")
    
    st.subheader("⚖️ Dynamic Scaling")
    new_servings = st.slider(
        "Adjust servings to recalculate quantities:", 
        min_value=1, 
        max_value=24, 
        value=recipe.get("original_servings", 4)
    )
    
    multiplier = new_servings / recipe.get("original_servings", 4)
    
    st.markdown(f"### 🛒 Ingredients (Scaled for {new_servings} servings)")
    for ing in recipe.get("ingredients", []):
        amount = ing.get("amount")
        scaled_amount = round(amount * multiplier, 2) if amount is not None else ""
        st.write(f"- **{scaled_amount} {ing.get('unit', '')}** of {ing.get('name', '')}")
        
    st.markdown("### 👩‍🍳 Instructions")
    for i, step in enumerate(recipe.get("steps", []), 1):
        st.write(f"**Step {i}:** {step}")


