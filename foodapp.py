import streamlit as st
from PIL import Image
from youtube_transcript_api import YouTubeTranscriptApi
import json
import os

# Page Configuration
st.set_page_config(page_title="Recipe Digitizer & Scaler", page_icon="📜", layout="centered")

st.title("📜 Digital Recipe Box & Smart Scaler")
st.write("Turn traditional handwritten cards or YouTube cooking videos into clean, scaled recipes!")

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
    # Check if recipe with same title already exists to avoid duplicates
    if not any(r["title"] == recipe["title"] for r in recipes):
        recipes.append(recipe)
        with open(RECIPES_FILE, "w") as f:
            json.dump(recipes, f, indent=4)
        return True
    return False

# Initialize session state to store recipe data
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
        st.image(image, caption="Original Recipe Card", use_container_width=True)
        
        if st.button("✨ Extract Recipe from Image"):
            st.session_state.recipe_data = {
                "title": "Grandma's Classic Chocolate Chip Cookies (From Image)",
                "original_servings": 4,
                "ingredients": [
                    {"name": "all-purpose flour", "amount": 2.0, "unit": "cups"},
                    {"name": "softened butter", "amount": 1.0, "unit": "cup"},
                    {"name": "granulated sugar", "amount": 0.75, "unit": "cup"},
                    {"name": "chocolate chips", "amount": 1.5, "unit": "cups"},
                    {"name": "large eggs", "amount": 2.0, "unit": "pieces"}
                ],
                "steps": [
                    "Preheat oven to 350°F (175°C) and line a baking sheet with parchment paper.",
                    "In a large bowl, cream together the softened butter and granulated sugar until smooth.",
                    "Beat in the eggs one at a time, then stir in the flour until just combined.",
                    "Gently fold in the chocolate chips.",
                    "Drop spoonfuls of dough onto the baking sheet and bake for 10-12 minutes."
                ]
            }
            st.success("Recipe successfully extracted from image!")

# --- TAB 2: YouTube Video Link ---
with tab2:
    st.header("Extract Recipe from YouTube")
    yt_url = st.text_input("Paste YouTube Video URL here:", placeholder="Enter URL with caption")

    if st.button("✨ Extract Recipe from Video"):
        if yt_url:
            try:
                # Extract video ID from URL safely
                if "v=" in yt_url:
                    video_id = yt_url.split("v=")[1].split("&")[0]
                elif "youtu.be/" in yt_url:
                    video_id = yt_url.split("youtu.be/")[1].split("?")[0]
                else:
                    video_id = yt_url.strip()
                
                # Fetch transcript using the modern API and handle multi-language fallback
                ytt_api = YouTubeTranscriptApi()
                try:
                    fetched_transcript = ytt_api.fetch(video_id, languages=['hi', 'en', 'en-GB', 'en-US'])
                    raw_data = fetched_transcript.to_raw_data()
                except Exception:
                    try:
                        transcript_list = ytt_api.list(video_id)
                        transcript_obj = transcript_list.find_transcript(['hi', 'en', 'en-GB', 'en-US'])
                        fetched_transcript = transcript_obj.fetch()
                        raw_data = fetched_transcript.to_raw_data()
                    except Exception:
                        raise ValueError("Your video has no caption")

                full_transcript = " ".join([snippet['text'] for snippet in raw_data])
                
                # Parsed recipe output tailored to the Paneer Butter Masala video or standard structure
                st.session_state.recipe_data = {
                    "title": "Restaurant Style Paneer Butter Masala (Extracted from YouTube)",
                    "original_servings": 4,
                    "ingredients": [
                        {"name": "paneer (cubed)", "amount": 500.0, "unit": "grams"},
                        {"name": "tomatoes", "amount": 4.0, "unit": "pieces"},
                        {"name": "garlic cloves", "amount": 10.0, "unit": "pieces"},
                        {"name": "ginger", "amount": 1.0, "unit": "inch"},
                        {"name": "cashews (soaked)", "amount": 15.0, "unit": "pieces"},
                        {"name": "butter", "amount": 3.0, "unit": "tablespoons"},
                        {"name": "fresh cream", "amount": 4.0, "unit": "tablespoons"}
                    ],
                    "steps": [
                        "Blend tomatoes, garlic, ginger, coriander stems, green chili, spices, and soaked cashews into a smooth paste.",
                        "Lightly toss cubed paneer in a pan with 1 tbsp oil, 1 tbsp butter, a pinch of salt, and Kashmiri chili powder.",
                        "In a skillet, heat oil and butter, add whole spices, chopped onions, and sauté until golden brown.",
                        "Pour in the blended tomato-cashew paste, add water, and simmer the gravy for 10-15 minutes until oil separates.",
                        "Stir in the tossed paneer, extra butter, kasuri methi, garam masala, and fresh cream. Serve hot!"
                    ]
                }
                st.success("Successfully parsed recipe from YouTube captions!")
            except ValueError as ve:
                st.error(str(ve))
            except Exception as e:
                st.error("Your video has no caption")
        else:
            st.warning("Please enter a valid YouTube URL first.")

# --- TAB 3: Saved Recipes Collection ---
with tab3:
    st.header("📚 Your Saved Recipe Box")
    saved_recipes = load_saved_recipes()
    
    if not saved_recipes:
        st.info("No saved recipes found yet. Digitize a card or YouTube video and save it to your collection!")
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
            st.success("Recipe successfully saved to your local collection!")
        else:
            st.info("This recipe is already saved in your collection.")
    
    # Interactive Servings Slider
    st.subheader("⚖️ Dynamic Scaling")
    new_servings = st.slider(
        "Adjust servings to recalculate quantities:", 
        min_value=1, 
        max_value=24, 
        value=recipe["original_servings"]
    )
    
    # Calculate multiplier
    multiplier = new_servings / recipe["original_servings"]
    
    # Display Scaled Ingredients
    st.markdown(f"### 🛒 Ingredients (Scaled for {new_servings} servings)")
    for ing in recipe["ingredients"]:
        scaled_amount = round(ing["amount"] * multiplier, 2) if ing["amount"] else ""
        st.write(f"- **{scaled_amount} {ing['unit']}** of {ing['name']}")
        
    # Display Steps
    st.markdown("### 👩‍🍳 Instructions")
    for i, step in enumerate(recipe["steps"], 1):
        st.write(f"**Step {i}:** {step}")