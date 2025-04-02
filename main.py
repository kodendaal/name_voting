import gradio as gr
import pandas as pd
import openpyxl
import os
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive 'Agg'
import matplotlib.pyplot as plt

# Set your desired voting start date and time
VOTING_START = datetime(2025, 4, 2, 20, 38, 0)  # Example: April 5, 2025, at 12:00 PM

# Initialize data file if it doesn't exist, including Tag and Timestamp columns.
if not os.path.exists("submissions.xlsx"):
    pd.DataFrame(columns=["Name", "Tag", "Timestamp"]).to_excel("submissions.xlsx", index=False)

if not os.path.exists("votes.xlsx"):
    pd.DataFrame(columns=["Name"]).to_excel("votes.xlsx", index=False)


def add_name(name, tag):
    """Append a new team name to submissions.xlsx with an optional tag and a timestamp."""
    name = str(name).strip()
    tag = str(tag).strip()  # optional tag
    if name == "":
        return "⚠️ Please enter a team name."
    if tag == "":
        return "⚠️ Please include an anonymous tag."

    # Read existing submissions, or create a new DataFrame if file doesn't exist.
    try:
        sub_df = pd.read_excel("submissions.xlsx")
    except Exception:
        sub_df = pd.DataFrame(columns=["Name", "Tag", "Timestamp"])
    
    # Ensure necessary columns exist.
    for col in ["Name", "Tag", "Timestamp"]:
        if col not in sub_df.columns:
            sub_df[col] = None

    # Normalize the new name for comparison.
    normalized_name = name.lower()

    # Check against lower-case versions of existing names.
    if normalized_name in sub_df["Name"].astype(str).str.lower().values:
        return f"⚠️ The name '{name}' has already been submitted."

    # Record current timestamp.
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    # Append the new entry.
    new_entry = pd.DataFrame({"Name": [name], "Tag": [tag], "Timestamp": [timestamp]})
    sub_df = pd.concat([sub_df, new_entry], ignore_index=True)
    sub_df.to_excel("submissions.xlsx", index=False)
    
    return f"✅ Team name '{name}' with tag '{tag}' submitted successfully at {timestamp}!"


def cast_votes(selected_names, votes_remaining):
    # Check if the current time is before the allowed voting start time
    if datetime.now() < VOTING_START:
        return votes_remaining, f"⚠️ Voting is not open yet. Please come back after {VOTING_START.strftime('%Y-%m-%d %H:%M:%S')}."
    
    # Proceed with the existing voting logic if voting is allowed
    if selected_names is None or selected_names == []:
        return votes_remaining, "⚠️ No names selected. Please choose up to 3."
    
    if isinstance(selected_names, str):
        selected_names = [selected_names]

    if votes_remaining <= 0:
        return votes_remaining, "⚠️ You have no votes remaining."
    
    if len(selected_names) > votes_remaining:
        return votes_remaining, f"⚠️ You can only vote for {votes_remaining} more name(s)."
    
    # Record votes in the Excel file
    try:
        votes_df = pd.read_excel("votes.xlsx")
    except Exception:
        votes_df = pd.DataFrame(columns=["Name"])

    new_votes = pd.DataFrame({"Name": [str(name) for name in selected_names]})
    votes_df = pd.concat([votes_df, new_votes], ignore_index=True)
    votes_df.to_excel("votes.xlsx", index=False)
    
    new_remaining = votes_remaining - len(selected_names)
    message = "✅ Vote recorded!" if len(selected_names) == 1 else "✅ Votes recorded!"

    if new_remaining > 0:
        message += f" You have {new_remaining} vote(s) left."
    else:
        message += " You have no votes left."

    return new_remaining, message


def get_leaderboard():
    """Generate a leaderboard DataFrame of team names and vote counts."""
    try:
        sub_df = pd.read_excel("submissions.xlsx")
    except Exception:
        sub_df = pd.DataFrame(columns=["Name"])

    try:
        votes_df = pd.read_excel("votes.xlsx")
    except Exception:
        votes_df = pd.DataFrame(columns=["Name"])

    # List of all submitted names (remove any NaN or duplicates)
    if "Name" in sub_df.columns:
        all_names = sub_df["Name"].astype(str).dropna().tolist()
    else:
        all_names = []
    all_names = list(dict.fromkeys(all_names))  # preserve order and make unique

    # Count votes per name
    vote_counts = {}
    if "Name" in votes_df.columns and not votes_df.empty:
        vote_counts = votes_df["Name"].astype(str).value_counts().to_dict()

    # Prepare leaderboard data as list of [Name, Votes]
    leaderboard_data = []
    for name in all_names:
        count = vote_counts.get(name, 0)
        leaderboard_data.append([name, int(count)])

    # Include any voted names not in submissions (edge case)
    if "Name" in votes_df.columns:
        for name in votes_df["Name"].astype(str).unique():
            if name not in all_names:
                count = vote_counts.get(name, 0)
                leaderboard_data.append([name, int(count)])

    # Sort by votes (descending)
    leaderboard_data.sort(key=lambda x: x[1], reverse=True)

    # Create DataFrame for display
    leader_df = pd.DataFrame(leaderboard_data, columns=["Team Name", "Votes"])

    return leader_df

def refresh_name_list():
    """Refresh the list of team names for the voting checkbox group."""
    try:
        sub_df = pd.read_excel("submissions.xlsx")
        names_list = sub_df["Name"].astype(str).dropna().tolist()
    except Exception:
        names_list = []

    # Update the checkbox choices (clear any current selections)

    return gr.update(choices=names_list, value=[])


def generate_leaderboard_chart():
    # Get the leaderboard DataFrame using our existing function
    leader_df = get_leaderboard()

    # If no data is available, create a simple message figure.
    if leader_df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'No data available', horizontalalignment='center', verticalalignment='center', fontsize=14)
        ax.axis('off')
        plt.close()  # Close the figure to free memory
        return fig

    # Create the bar chart
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(leader_df["Team Name"], leader_df["Votes"], color="skyblue")
    ax.set_xlabel("Team Name")
    ax.set_ylabel("Votes")
    ax.set_title("Leaderboard Votes")
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    plt.close()  # Close the figure to free memory
    
    return fig


# Build the Gradio interface with an extra field for the anonymous tag.
with gr.Blocks() as demo:
    gr.Markdown("## 🏆 **Team Name Voting App**\nSubmit ideas and vote for your favorite team name.")
    with gr.Tab("Submit Team Name"):
        gr.Markdown("**Propose a New Team Name**")
        with gr.Row():
            name_input = gr.Textbox(label="Team Name", placeholder="Enter a team name idea")
            tag_input = gr.Textbox(label="Anonymous Tag", placeholder="e.g., your initials")
        submit_btn = gr.Button("Submit")
        submit_msg = gr.Markdown()  # for feedback message
        submit_btn.click(fn=add_name, inputs=[name_input, tag_input], outputs=submit_msg)
    
    with gr.Tab("Vote for Name"):
        gr.Markdown("**Vote for Your Top 3 Choices** (each user can vote for up to 3 names in total)")
        # Initialize checkbox options from current submissions
        try:
            initial_names = pd.read_excel("submissions.xlsx")["Name"].astype(str).dropna().tolist()
        except Exception:
            initial_names = []
        vote_group = gr.CheckboxGroup(choices=initial_names, label="Select up to 3 names")
        vote_btn = gr.Button("Vote")
        vote_msg = gr.Markdown()  # feedback message for voting
        votes_state = gr.State(3)  # state to track remaining votes for the session
        vote_btn.click(fn=cast_votes, inputs=[vote_group, votes_state], outputs=[votes_state, vote_msg])
        # Optional refresh button to update the list of names (in case new names were added)
        refresh_btn = gr.Button("🔄 Refresh Names List")
        refresh_btn.click(fn=refresh_name_list, inputs=None, outputs=vote_group)

    with gr.Tab("Leaderboard"):
        gr.Markdown("**Current Vote Leaderboard** (names sorted by votes)")
        leader_display = gr.Dataframe(value=pd.DataFrame(columns=["Team Name", "Votes"]), headers=["Team Name", "Votes"], interactive=False)
        refresh_leader_btn = gr.Button("🔄 Refresh Leaderboard")
        
        # New component for the bar chart visualization
        leader_plot = gr.Plot(label="Leaderboard Chart")
        
        # When refresh is clicked, update both the table and the chart
        refresh_leader_btn.click(fn=get_leaderboard, inputs=None, outputs=leader_display)
        refresh_leader_btn.click(fn=generate_leaderboard_chart, inputs=None, outputs=leader_plot)
        
        # Load initial data on app launch
        demo.load(fn=get_leaderboard, inputs=None, outputs=leader_display)
        demo.load(fn=generate_leaderboard_chart, inputs=None, outputs=leader_plot)
        
    # Load current leaderboard on app launch for real-time update
    demo.load(fn=get_leaderboard, inputs=None, outputs=leader_display)

# Launch the app (for a real deployment, remove debug flags as needed)
demo.launch(pwa=True)
