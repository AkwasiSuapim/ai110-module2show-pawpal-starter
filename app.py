from datetime import time as dtime

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task, load_data, save_data

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

PET_SPECIES = ["Dog", "Cat", "Bird", "Rabbit", "Hamster", "Fish", "Guinea Pig", "Turtle", "Other"]

PET_ICONS = {
    "Dog": "🐶",
    "Cat": "🐱",
    "Bird": "🐦",
    "Rabbit": "🐰",
    "Hamster": "🐹",
    "Fish": "🐟",
    "Guinea Pig": "🐹",
    "Turtle": "🐢",
    "Other": "🐾",
}

TASK_CATEGORIES = [
    "Feeding",
    "Medication",
    "Walking / Exercise",
    "Grooming",
    "Enrichment / Play",
    "Cleaning",
    "Training",
    "Vet / Health",
    "Rest / Comfort",
    "Other",
]

FREQUENCIES = ["once", "daily", "weekly"]


def get_pet_icon(species: str) -> str:
    """Return an emoji icon for a pet species, falling back to a paw print."""
    return PET_ICONS.get(species, "🐾")


# --- Session state setup ---------------------------------------------------
# The Owner object holds its own pets, and each Pet holds its own tasks, so
# keeping `owner` (plus the generated `schedule`) in session_state is enough
# to make pets, tasks, conflicts, and recurring updates all survive reruns.

if "owner" not in st.session_state:
    st.session_state.owner = load_data() or Owner(name="Jordan")

if "selected_pet_name" not in st.session_state:
    st.session_state.selected_pet_name = None

if "schedule" not in st.session_state:
    st.session_state.schedule = None

owner = st.session_state.owner


def get_selected_pet():
    return owner.get_pet(st.session_state.selected_pet_name)


# --- Welcome / Scenario -----------------------------------------------------

st.title("🐾 PawPal+")
st.markdown(
    "PawPal+ helps a busy pet owner plan daily care tasks for their pets — sorted by time, "
    "checked for scheduling conflicts, and rescheduled automatically when they recur."
)

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
A busy pet owner needs help staying consistent with pet care. PawPal+ acts as an assistant that:

- Tracks pet care tasks (walks, feeding, meds, enrichment, grooming, etc.) with a scheduled time
- Sorts tasks chronologically and flags tasks scheduled at the same time
- Automatically reschedules daily/weekly tasks once they're completed
"""
    )

st.divider()

# --- 1. Owner Info -----------------------------------------------------

st.header("1. Owner Info")

col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    start_time_input = st.time_input("Day starts at", value=dtime(0, 0))
    owner.daily_start_time = start_time_input.strftime("%H:%M")

owner.preferences = st.text_input("Preferences / notes (optional)", value=owner.preferences or "") or None

st.divider()

# --- 2. Add Pets -----------------------------------------------------

st.header("2. Add Pets")

with st.form("add_pet_form", clear_on_submit=True):
    pet_col1, pet_col2 = st.columns(2)
    with pet_col1:
        new_pet_name = st.text_input("Pet name")
        new_pet_species = st.selectbox("Species", PET_SPECIES)
    with pet_col2:
        new_pet_breed = st.text_input("Breed / type")
        new_pet_age = st.number_input("Age (months)", min_value=0, max_value=360, value=12)
    new_pet_food = st.text_input("Food preference (optional)")
    new_pet_notes = st.text_input("Notes (optional)")

    pet_submitted = st.form_submit_button("Add Pet")
    if pet_submitted:
        if not new_pet_name.strip():
            st.warning("Please give the pet a name before adding it.")
        else:
            new_pet = Pet(
                name=new_pet_name.strip(),
                species=new_pet_species,
                breed=new_pet_breed or None,
                age=int(new_pet_age),
                food_preference=new_pet_food or None,
                notes=new_pet_notes or None,
            )
            owner.add_pet(new_pet)
            st.session_state.selected_pet_name = new_pet.name
            save_data(owner)
            st.success(f"Added {new_pet.name} the {new_pet.species}.")

st.divider()

# --- 3. Pet List -----------------------------------------------------

st.header("3. Pet List")

selected_pet = None

if not owner.pets:
    st.info("No pets yet. Add one above.")
else:
    for i, pet in enumerate(owner.pets):
        info_col, remove_col = st.columns([5, 1])
        with info_col:
            st.markdown(
                f"{get_pet_icon(pet.species)} **{pet.name}** — {pet.species}, "
                f"{pet.breed or 'unknown breed'}, age {pet.age if pet.age is not None else '?'} months "
                f"· {len(pet.get_tasks())} task(s)"
            )
        with remove_col:
            if st.button("Remove", key=f"remove_pet_{i}"):
                owner.remove_pet(pet.name)
                if st.session_state.selected_pet_name == pet.name:
                    st.session_state.selected_pet_name = None
                save_data(owner)
                st.rerun()

    pet_names = [pet.name for pet in owner.pets]
    if st.session_state.selected_pet_name not in pet_names:
        st.session_state.selected_pet_name = pet_names[0]

    selected_name = st.selectbox(
        "Which pet are you managing?",
        pet_names,
        index=pet_names.index(st.session_state.selected_pet_name),
    )
    st.session_state.selected_pet_name = selected_name
    selected_pet = get_selected_pet()

st.divider()

# --- 4. Add Care Tasks -----------------------------------------------------

st.header("4. Add Care Tasks")

if not selected_pet:
    st.info("Add and select a pet above before adding care tasks.")
else:
    st.caption(f"Adding tasks for {get_pet_icon(selected_pet.species)} {selected_pet.name}")
    with st.form("add_task_form", clear_on_submit=True):
        task_col1, task_col2, task_col3 = st.columns(3)
        with task_col1:
            task_title = st.text_input("Task title")
        with task_col2:
            task_time = st.time_input("Time", value=dtime(8, 0))
        with task_col3:
            task_duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=15)

        task_col4, task_col5, task_col6 = st.columns(3)
        with task_col4:
            task_priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
        with task_col5:
            task_frequency = st.selectbox("Frequency", FREQUENCIES)
        with task_col6:
            task_category = st.selectbox("Category", TASK_CATEGORIES)

        task_notes = st.text_input("Notes (optional)")

        task_submitted = st.form_submit_button("Add Task")
        if task_submitted:
            if not task_title.strip():
                st.warning("Please give the task a title before adding it.")
            else:
                new_task = Task(
                    title=task_title.strip(),
                    time=task_time.strftime("%H:%M"),
                    duration_minutes=int(task_duration),
                    frequency=task_frequency,
                    priority=task_priority,
                    category=task_category,
                    notes=task_notes or None,
                )
                selected_pet.add_task(new_task)
                save_data(owner)
                st.success(f"Added '{new_task.title}' for {selected_pet.name}.")

st.divider()

# --- 5. Task List -----------------------------------------------------

st.header("5. Task List")

if not selected_pet:
    st.info("Select a pet above to see their tasks.")
elif not selected_pet.get_tasks():
    st.info(f"No tasks yet for {selected_pet.name}. Add one above.")
else:
    for i, task in enumerate(selected_pet.get_tasks()):
        task_col, complete_col = st.columns([5, 1])
        with task_col:
            status = "✅ done" if task.completed else "pending"
            st.write(
                f"- **{task.time}** {task.title} ({task.duration_minutes} min, {task.priority} priority, "
                f"{task.category or 'Other'}, {task.frequency}) — {status}"
            )
        with complete_col:
            if not task.completed:
                if st.button("Mark done", key=f"complete_{i}"):
                    task.mark_complete()
                    save_data(owner)
                    st.rerun()

st.divider()

# --- 6. Build Schedule -----------------------------------------------------

st.header("6. Build Schedule")

schedule_col1, schedule_col2 = st.columns(2)
with schedule_col1:
    filter_pet_only = st.checkbox("Only show the selected pet's tasks", value=False)
with schedule_col2:
    include_completed = st.checkbox("Include completed tasks", value=False)

sort_choice = st.radio("Sort schedule by", ["Time", "Priority + Need"], horizontal=True)
sort_by = "priority" if sort_choice == "Priority + Need" else "time"

if st.button("Generate schedule", type="primary"):
    if not owner.pets:
        st.warning("Add at least one pet first.")
    elif not owner.get_all_tasks():
        st.warning("Add at least one care task first.")
    else:
        scheduler = Scheduler()
        pet_filter = selected_pet.name if (filter_pet_only and selected_pet) else None
        st.session_state.schedule = scheduler.generate_schedule(
            owner, pet_name=pet_filter, include_completed=include_completed, sort_by=sort_by
        )

st.divider()

# --- 7. Today's Schedule -----------------------------------------------------

st.header("7. Today's Schedule")

schedule = st.session_state.schedule

if not schedule:
    st.info("Generate a schedule above to see today's plan here.")
else:
    if not schedule.entries:
        st.write("No tasks match the current filters.")
    else:
        st.subheader("Daily Timeline")
        for entry in schedule.entries:
            task = entry.task
            pet = entry.pet
            with st.container():
                st.markdown(
                    f"⏰ **{task.time}** — {get_pet_icon(pet.species)} **{pet.name}**: "
                    f"*{task.title}* ({task.priority} priority, {task.duration_minutes} min, "
                    f"{task.category or 'Other'})"
                )

    st.caption("By pet")
    grouped = schedule.by_pet()
    if not grouped:
        st.write("No tasks match the current filters.")
    for pet_name, entries in grouped.items():
        pet = entries[0].pet
        st.subheader(f"{get_pet_icon(pet.species)} {pet_name}")
        rows = [
            {
                "Time": e.task.time,
                "Task": e.task.title,
                "Priority": e.task.priority,
                "Duration (min)": e.task.duration_minutes,
                "Category": e.task.category or "Other",
                "Status": "done" if e.task.completed else "pending",
            }
            for e in entries
        ]
        st.table(rows)

st.divider()

# --- 8. Conflict Warnings -----------------------------------------------------

st.header("8. Conflict Warnings")

if not schedule:
    st.info("Conflicts will appear here once a schedule is generated.")
elif schedule.conflicts:
    for warning in schedule.conflicts:
        st.warning(warning)
else:
    st.success("No time conflicts detected.")

st.divider()

# --- 9. Explanations / Recurring Updates -----------------------------------------------------

st.header("9. Explanations / Recurring Updates")

if not schedule:
    st.info("Recurring task updates will appear here once a schedule is generated.")
elif schedule.recurring_updates:
    for update in schedule.recurring_updates:
        st.info(update)
else:
    st.write("No recurring tasks were completed yet.")
