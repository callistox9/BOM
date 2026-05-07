import os
from crewai import Agent, Task, Crew

os.environ["GOOGLE_API_KEY"] = "AIzaSyB7IrpyY3fEFF9jgVsgJD_4U8t_JTWH-E4"
party_planner = Agent(
    role="Party Planner",
    goal="Create the party plan, including the theme, timeline, and guest list.",
    backstory=(
        "You organize the vision for the party, create a timeline, and ensure all aspects are planned. "
        "You send out invitations and coordinate with the other agents."
    ),
    allow_delegation=False,
    verbose=True,
    llm="gemini/gemini-2.5-flash" 
)

food_beverage_coordinator = Agent(
    role="Food & Beverage Coordinator",
    goal="Organize the food and drinks for the party, ensuring there’s enough variety for all guests.",
    backstory=(
        "You handle the food and drink preparations, whether it’s cooking, ordering, or working with caterers. "
        "You make sure guests have plenty to eat and drink throughout the event."
    ),
    allow_delegation=False,
    verbose=True,
    llm="gemini/gemini-2.5-flash" 
)

decorator = Agent(
    role="Decorator",
    goal="Make the party venue look great, fitting the theme and making it fun for guests.",
    backstory=(
        "You decorate the venue to match the theme and create a welcoming and festive environment. "
        "You ensure the venue is ready when the guests arrive."
    ),
    allow_delegation=False,
    verbose=True,
    llm="gemini/gemini-2.5-flash" 
)

entertainment_guest_relations = Agent(
    role="Entertainment & Guest Relations Coordinator",
    goal="Organize entertainment, games, and manage guest interactions to ensure a fun party.",
    backstory=(
        "You make sure the guests have fun, whether it’s through music, games, or other activities. "
        "You also help guests with seating and ensure the event flows smoothly."
    ),
    allow_delegation=False,
    verbose=True,
    llm="gemini/gemini-2.5-flash" 
)