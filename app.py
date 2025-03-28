import streamlit as st
import google.generativeai as genai
from tavily import TavilyClient
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Setup API clients
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
except Exception as e:
    st.error(f"Error setting up API clients: {e}")

# Gemini model
def get_gemini_response(prompt, model="gemini-1.5-flash"):
    try:
        model = genai.GenerativeModel(model)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error calling Gemini API: {e}")
        return "Sorry, I couldn't process that request. Please try again."

# Tavily search
def search_tavily(query):
    try:
        search_result = tavily_client.search(
            query=query,
            search_depth="advanced", 
            include_domains=[], 
            exclude_domains=[]
        )
        return search_result
    except Exception as e:
        st.error(f"Error with Tavily search: {e}")
        return {"results": []}

def format_currency_inr(amount):
    """Convert amount to Indian format with ₹ symbol."""
    s = str(amount)
    l = len(s)
    if l > 3:
        i = l - 3
        while i > 0:
            if i > 2:
                s = s[:i] + ',' + s[i:]
            else:
                s = s[:i] + ',' + s[i:]
            i = i - 2
    return f"₹{s}"

# System prompts
system_prompt_1 = """
You are an AI travel planner powered by Gemini 1.5 Flash. Your task is to gather detailed preferences from the user to create a personalized travel itinerary. Ask clear, concise questions to refine the following if not provided: budget, trip duration, destination, purpose, dietary preferences, specific interests, mobility concerns, and accommodation preferences. If the user provides vague input (e.g., "moderate budget"), ask follow-up questions to clarify (e.g., "Can you specify a range, like $500–$1000?"). Keep the tone friendly and conversational.
"""

system_prompt_2 = """
You are an AI travel planner using Gemini 1.5 Flash and the Tavily API for web search. Based on the user's inputs (budget: {budget}, duration: {duration}, destination: {destination}, purpose: {purpose}, preferences: {preferences}), I've searched the web for top attractions, activities, or hidden gems at the destination. Here are 5-7 suggestions tailored to the user's preferences:

{search_results}

Based on this information, please provide 5-7 activity suggestions tailored to the user's preferences. For each suggestion, include:
1. Name of the activity/attraction
2. Brief description (1-2 sentences)
3. Estimated cost
4. Why it matches the user's preferences

Present suggestions clearly and ask the user to approve or modify them.
"""

system_prompt_3 = """
You are an AI travel planner using Gemini 1.5 Flash. Using the user's refined inputs (budget: {budget}, duration: {duration}, destination: {destination}, purpose: {purpose}, preferences: {preferences}) and approved activity suggestions:

{approved_suggestions}

Create a detailed day-by-day itinerary. Include logical timing (e.g., morning, afternoon, evening), activity durations, meal recommendations (aligned with dietary preferences: {dietary_preferences}), and accommodation suggestions (based on: {accommodation_preferences}). 

Ensure the itinerary fits the budget ({budget}) and mobility constraints ({mobility_concerns}). Format the output as a clear, structured plan with days and times. The total trip duration is {duration}.

Additional notes:
- Start time each day: {start_time}
- End time each day: {end_time}
- Starting location: {starting_location}
"""

# Constants
BUDGET_RANGES = [
    "Under ₹40,000",
    "₹40,000 - ₹80,000",
    "₹80,000 - ₹1,60,000",
    "₹1,60,000 - ₹2,40,000",
    "₹2,40,000 - ₹4,00,000",
    "Above ₹4,00,000"
]

DURATION_RANGES = [
    "1-2 days",
    "3-4 days",
    "5-7 days",
    "1-2 weeks",
    "2+ weeks"
]

TRIP_PURPOSES = [
    "Relaxation",
    "Adventure",
    "Cultural Experience",
    "Food & Cuisine",
    "Business",
    "Family Vacation",
    "Romantic Getaway",
    "Shopping & Entertainment"
]

INTERESTS = [
    "Museums & History",
    "Nature & Outdoors",
    "Food & Dining",
    "Shopping",
    "Art & Culture",
    "Adventure Sports",
    "Beaches & Water Activities",
    "Nightlife & Entertainment",
    "Local Markets",
    "Photography"
]

DIETARY_PREFERENCES = [
    "No Restrictions",
    "Vegetarian",
    "Vegan",
    "Halal",
    "Kosher",
    "Gluten-Free",
    "Dairy-Free",
    "Other"
]

MOBILITY_OPTIONS = [
    "No Restrictions",
    "Prefer Short Walks",
    "Wheelchair Accessible",
    "Minimal Walking Required",
    "No Stairs Preferred"
]

ACCOMMODATION_TYPES = [
    "Luxury Hotel",
    "Mid-range Hotel",
    "Budget Hotel",
    "Hostel",
    "Vacation Rental",
    "Boutique Hotel",
    "Resort",
    "Bed & Breakfast"
]

# Initialize session state
if "stage" not in st.session_state:
    st.session_state.stage = "initial_input"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "preferences" not in st.session_state:
    st.session_state.preferences = {
        "budget": "",
        "duration": "",
        "destination": "",
        "starting_location": "",
        "purpose": "",
        "interests": "",
        "dietary_preferences": "",
        "mobility_concerns": "",
        "accommodation_preferences": "",
        "start_time": "9:00 AM",
        "end_time": "9:00 PM"
    }
if "approved_suggestions" not in st.session_state:
    st.session_state.approved_suggestions = []

# App title
st.title("AI Travel Planner")
st.write("Plan your perfect trip with AI assistance")

# Initial input form
if st.session_state.stage == "initial_input":
    with st.form("travel_form"):
        st.write("### Let's start planning your trip!")
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.preferences["budget"] = st.selectbox(
                "Budget Range",
                options=BUDGET_RANGES,
                key="budget"
            )
            st.session_state.preferences["duration"] = st.selectbox(
                "Trip Duration",
                options=DURATION_RANGES,
                key="duration"
            )
            st.session_state.preferences["destination"] = st.text_input(
                "Destination (e.g., Paris, Tokyo)",
                st.session_state.preferences["destination"]
            )
            st.session_state.preferences["starting_location"] = st.text_input(
                "Starting Location (e.g., New York, London)",
                st.session_state.preferences["starting_location"]
            )
            st.session_state.preferences["purpose"] = st.selectbox(
                "Purpose of Trip",
                options=TRIP_PURPOSES,
                key="purpose"
            )
        
        with col2:
            st.session_state.preferences["interests"] = st.multiselect(
                "Interests (Select multiple)",
                options=INTERESTS,
                default=[],
                key="interests"
            )
            st.session_state.preferences["dietary_preferences"] = st.selectbox(
                "Dietary Preferences",
                options=DIETARY_PREFERENCES,
                key="dietary"
            )
            st.session_state.preferences["mobility_concerns"] = st.selectbox(
                "Mobility Requirements",
                options=MOBILITY_OPTIONS,
                key="mobility"
            )
            st.session_state.preferences["accommodation_preferences"] = st.selectbox(
                "Accommodation Type",
                options=ACCOMMODATION_TYPES,
                key="accommodation"
            )

        # Add time selection with fixed increments
        time_col1, time_col2 = st.columns(2)
        with time_col1:
            st.session_state.preferences["start_time"] = st.select_slider(
                "Daily Start Time",
                options=[f"{i:02d}:00" for i in range(5, 13)],
                value="09:00"
            )
        with time_col2:
            st.session_state.preferences["end_time"] = st.select_slider(
                "Daily End Time",
                options=[f"{i:02d}:00" for i in range(13, 24)],
                value="21:00"
            )

        submitted = st.form_submit_button("Start Planning")
        
        if submitted:
            # Check for required fields
            required_fields = ["budget", "duration", "destination"]
            missing_fields = [field for field in required_fields if not st.session_state.preferences[field]]
            
            if missing_fields:
                st.error(f"Please fill in these required fields: {', '.join(missing_fields)}")
            else:
                # Add initial prompt to chat history
                user_info = "\n".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in st.session_state.preferences.items() if v])
                st.session_state.chat_history.append({"role": "user", "content": f"I want to plan a trip with these details:\n{user_info}"})
                
                # Generate AI response based on initial input
                prompt = f"{system_prompt_1}\n\nUser has provided the following information:\n{user_info}"
                response = get_gemini_response(prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                
                # Move to the refinement stage
                st.session_state.stage = "refine_preferences"
                st.rerun()

# Preference refinement chat interface
elif st.session_state.stage == "refine_preferences":
    st.write("### Refine Your Travel Preferences")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    user_input = st.chat_input("Type your response here...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Check if user wants to move to suggestions
        if "suggestions" in user_input.lower() or "next" in user_input.lower() or "activities" in user_input.lower():
            # Move to suggestions stage
            st.session_state.stage = "generate_suggestions"
            st.rerun()
        else:
            # Continue refining preferences
            # Create context from chat history
            context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history])
            prompt = f"{system_prompt_1}\n\nConversation history:\n{context}"
            
            response = get_gemini_response(prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()
    
    # Button to move to next stage
    if st.button("Ready for Suggestions"):
        st.session_state.stage = "generate_suggestions"
        st.rerun()

# Generate activity suggestions
elif st.session_state.stage == "generate_suggestions":
    st.write("### Activity Suggestions")
    
    with st.status("Searching for activities...", expanded=True) as status:
        # Extract current preferences from chat history
        prefs = st.session_state.preferences
        
        # Create search query for Tavily
        search_query = f"Top tourist attractions and activities in {prefs['destination']} for {prefs['purpose']} trip with {prefs['interests']} interests and {prefs['budget']} budget"
        st.write("Searching for relevant activities...")
        
        # Perform search
        search_results = search_tavily(search_query)
        
        # Format search results for the prompt
        formatted_results = ""
        for i, result in enumerate(search_results.get("results", [])[:5]):
            formatted_results += f"Source {i+1}: {result.get('title', 'No title')}\n"
            formatted_results += f"URL: {result.get('url', 'No URL')}\n"
            formatted_results += f"Content: {result.get('content', 'No content')[:500]}...\n\n"
        
        # Generate suggestions with Gemini
        prompt = system_prompt_2.format(
            budget=prefs["budget"],
            duration=prefs["duration"],
            destination=prefs["destination"],
            purpose=prefs["purpose"],
            preferences=f"{prefs['interests']} with {prefs['mobility_concerns']} mobility concerns",
            search_results=formatted_results
        )
        
        st.write("Generating personalized suggestions...")
        suggestions_response = get_gemini_response(prompt)
        status.update(label="Suggestions ready!", state="complete", expanded=False)
    
    # Display suggestions
    st.write("Based on your preferences, here are some suggested activities:")
    st.write(suggestions_response)
    
    # Let user approve or modify suggestions
    st.write("### Approve Suggestions")
    st.write("Please review the suggestions above. You can approve them or request modifications.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve Suggestions"):
            st.session_state.approved_suggestions = suggestions_response
            st.session_state.stage = "generate_itinerary"
            st.rerun()
    
    with col2:
        if st.button("Request Modifications"):
            st.session_state.chat_history.append({"role": "user", "content": "I'd like to modify the suggestions."})
            st.session_state.chat_history.append({"role": "assistant", "content": "What modifications would you like to make to the suggestions?"})
            st.session_state.stage = "modify_suggestions"
            st.rerun()

# Modify suggestions
elif st.session_state.stage == "modify_suggestions":
    st.write("### Modify Suggestions")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    user_input = st.chat_input("What would you like to change about the suggestions?")
    
    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Create context from chat history
        context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[-4:]])
        
        # Extract current preferences
        prefs = st.session_state.preferences
        
        # Regenerate suggestions with modifications
        prompt = f"""
        {system_prompt_2.format(
            budget=prefs["budget"],
            duration=prefs["duration"],
            destination=prefs["destination"],
            purpose=prefs["purpose"],
            preferences=f"{prefs['interests']} with {prefs['mobility_concerns']} mobility concerns",
            search_results="[Previous search results omitted]"
        )}
        
        The user has requested the following modifications to the suggestions:
        {user_input}
        
        Please revise the suggestions accordingly.
        """
        
        response = get_gemini_response(prompt)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.session_state.modified_suggestions = response
        st.rerun()
    
    # Buttons for approval
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve Modified Suggestions"):
            if "modified_suggestions" in st.session_state:
                st.session_state.approved_suggestions = st.session_state.modified_suggestions
            else:
                last_assistant_message = next((msg["content"] for msg in reversed(st.session_state.chat_history) 
                                             if msg["role"] == "assistant"), "")
                st.session_state.approved_suggestions = last_assistant_message
            st.session_state.stage = "generate_itinerary"
            st.rerun()
    
    with col2:
        if st.button("Request Further Modifications"):
            st.session_state.chat_history.append({"role": "user", "content": "I'd like to make more modifications."})
            st.session_state.chat_history.append({"role": "assistant", "content": "Please let me know what additional changes you'd like to make."})
            st.rerun()

# Generate itinerary
elif st.session_state.stage == "generate_itinerary":
    st.write("### Your Personalized Travel Itinerary")
    
    with st.status("Generating your itinerary...", expanded=True) as status:
        # Extract current preferences
        prefs = st.session_state.preferences
        
        # Generate itinerary with Gemini
        prompt = system_prompt_3.format(
            budget=prefs["budget"],
            duration=prefs["duration"],
            destination=prefs["destination"],
            purpose=prefs["purpose"],
            preferences=prefs["interests"],
            approved_suggestions=st.session_state.approved_suggestions,
            dietary_preferences=prefs["dietary_preferences"],
            accommodation_preferences=prefs["accommodation_preferences"],
            mobility_concerns=prefs["mobility_concerns"],
            start_time=prefs["start_time"],
            end_time=prefs["end_time"],
            starting_location=prefs["starting_location"]
        )
        
        itinerary_response = get_gemini_response(prompt)
        status.update(label="Itinerary ready!", state="complete", expanded=False)
    
    # Display itinerary
    st.write("Here's your personalized travel itinerary:")
    st.markdown(itinerary_response)
    
    # Download option
    st.download_button(
        label="Download Itinerary as Text",
        data=itinerary_response,
        file_name=f"travel_itinerary_{prefs['destination'].replace(' ', '_')}.txt",
        mime="text/plain"
    )
    
    # Restart planning
    if st.button("Plan Another Trip"):
        st.session_state.stage = "initial_input"
        st.session_state.chat_history = []
        st.session_state.preferences = {
            "budget": "",
            "duration": "",
            "destination": "",
            "starting_location": "",
            "purpose": "",
            "interests": "",
            "dietary_preferences": "",
            "mobility_concerns": "",
            "accommodation_preferences": "",
            "start_time": "9:00 AM",
            "end_time": "9:00 PM"
        }
        st.session_state.approved_suggestions = []
        st.rerun()

