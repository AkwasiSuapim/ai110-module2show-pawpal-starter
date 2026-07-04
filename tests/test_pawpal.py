"""Tests for the PawPal+ backend (pawpal_system.py).

These tests only exercise the backend classes (Task, Pet, Owner, Scheduler).
The Streamlit UI in app.py is not tested here.
"""

from pawpal_system import Owner, Pet, Scheduler, Task, load_data, save_data


def test_mark_complete_changes_status():
    task = Task(title="Feeding", time="08:00")
    assert not task.is_complete()

    task.mark_complete()

    assert task.is_complete()


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="Dog")
    assert len(pet.get_tasks()) == 0

    pet.add_task(Task(title="Walk", time="08:00"))

    assert len(pet.get_tasks()) == 1


def test_sort_by_time_returns_chronological_order():
    pet = Pet(name="Mochi", species="Dog")
    pet.add_task(Task(title="Dinner", time="18:00"))
    pet.add_task(Task(title="Morning Walk", time="08:00"))
    pet.add_task(Task(title="Lunch", time="12:00"))

    owner = Owner(name="Jordan")
    owner.add_pet(pet)

    scheduler = Scheduler()
    entries = scheduler.sort_by_time(scheduler.get_all_tasks(owner))

    times = [task.time for _, task in entries]
    assert times == ["08:00", "12:00", "18:00"]


def test_filter_tasks_by_pet_name():
    mochi = Pet(name="Mochi", species="Dog")
    mochi.add_task(Task(title="Walk", time="08:00"))
    luna = Pet(name="Luna", species="Cat")
    luna.add_task(Task(title="Medication", time="08:00"))

    owner = Owner(name="Jordan")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler()
    entries = scheduler.filter_tasks(scheduler.get_all_tasks(owner), pet_name="Luna")

    assert len(entries) == 1
    assert entries[0][0].name == "Luna"


def test_filter_tasks_by_completion_status():
    pet = Pet(name="Mochi", species="Dog")
    pet.add_task(Task(title="Walk", time="08:00", completed=True))
    pet.add_task(Task(title="Feeding", time="09:00", completed=False))

    owner = Owner(name="Jordan")
    owner.add_pet(pet)

    scheduler = Scheduler()
    pending = scheduler.filter_tasks(scheduler.get_all_tasks(owner), completed=False)

    assert len(pending) == 1
    assert pending[0][1].title == "Feeding"


def test_completing_daily_task_creates_next_occurrence():
    pet = Pet(name="Mochi", species="Dog")
    task = Task(title="Feeding", time="09:00", frequency="daily")
    pet.add_task(task)
    task.mark_complete()

    owner = Owner(name="Jordan")
    owner.add_pet(pet)

    scheduler = Scheduler()
    schedule = scheduler.generate_schedule(owner)

    assert any(e.task.title == "Feeding" and not e.task.completed for e in schedule.entries)
    assert len(schedule.recurring_updates) == 1


def test_generate_schedule_does_not_duplicate_recurring_task_on_repeat_calls():
    pet = Pet(name="Mochi", species="Dog")
    task = Task(title="Feeding", time="09:00", frequency="daily")
    pet.add_task(task)
    task.mark_complete()

    owner = Owner(name="Jordan")
    owner.add_pet(pet)

    scheduler = Scheduler()
    scheduler.generate_schedule(owner)
    scheduler.generate_schedule(owner)

    feeding_tasks = [t for t in pet.get_tasks() if t.title == "Feeding"]
    assert len(feeding_tasks) == 2  # the original (completed) plus exactly one new occurrence


def test_detect_conflicts_flags_same_time_tasks():
    mochi = Pet(name="Mochi", species="Dog")
    mochi.add_task(Task(title="Morning Walk", time="08:00"))
    luna = Pet(name="Luna", species="Cat")
    luna.add_task(Task(title="Medication", time="08:00"))

    owner = Owner(name="Jordan")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler()
    schedule = scheduler.generate_schedule(owner)

    assert len(schedule.conflicts) == 1
    assert "08:00" in schedule.conflicts[0]


def test_scheduler_handles_owner_with_no_tasks():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="Dog"))

    scheduler = Scheduler()
    schedule = scheduler.generate_schedule(owner)

    assert schedule.entries == []
    assert schedule.conflicts == []


def test_get_pet_returns_none_for_missing_pet():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="Dog"))

    assert owner.get_pet("NoSuchPet") is None


def test_generate_schedule_with_unknown_pet_name_returns_empty_schedule():
    pet = Pet(name="Mochi", species="Dog")
    pet.add_task(Task(title="Walk", time="08:00"))

    owner = Owner(name="Jordan")
    owner.add_pet(pet)

    scheduler = Scheduler()
    schedule = scheduler.generate_schedule(owner, pet_name="SomeNameThatDoesNotExist")

    assert schedule.entries == []
    assert schedule.conflicts == []


def test_generate_schedule_handles_owner_with_no_pets_at_all():
    owner = Owner(name="Jordan")

    scheduler = Scheduler()
    schedule = scheduler.generate_schedule(owner)

    assert schedule.entries == []
    assert schedule.conflicts == []


def test_sort_by_time_handles_boundary_times_correctly():
    pet = Pet(name="Mochi", species="Dog")
    pet.add_task(Task(title="Midnight Snack", time="00:00"))
    pet.add_task(Task(title="Late Night Check", time="23:59"))
    pet.add_task(Task(title="Lunch", time="12:00"))

    owner = Owner(name="Jordan")
    owner.add_pet(pet)

    scheduler = Scheduler()
    entries = scheduler.sort_by_time(scheduler.get_all_tasks(owner))

    times = [task.time for _, task in entries]
    assert times == ["00:00", "12:00", "23:59"]


def test_daily_start_time_filter_is_inclusive_of_exact_match():
    pet = Pet(name="Mochi", species="Dog")
    pet.add_task(Task(title="Morning Walk", time="08:00"))

    owner = Owner(name="Jordan", daily_start_time="08:00")
    owner.add_pet(pet)

    scheduler = Scheduler()
    schedule = scheduler.generate_schedule(owner)

    assert any(e.task.title == "Morning Walk" for e in schedule.entries)


def test_detect_conflicts_flags_overlapping_different_start_times():
    mochi = Pet(name="Mochi", species="Dog")
    mochi.add_task(Task(title="Morning Walk", time="08:00", duration_minutes=20))
    luna = Pet(name="Luna", species="Cat")
    luna.add_task(Task(title="Feeding", time="08:15", duration_minutes=10))

    owner = Owner(name="Jordan")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler()
    schedule = scheduler.generate_schedule(owner)

    assert len(schedule.conflicts) == 1
    assert "Morning Walk" in schedule.conflicts[0]
    assert "Feeding" in schedule.conflicts[0]
    assert "08:00-08:20" in schedule.conflicts[0]
    assert "08:15-08:25" in schedule.conflicts[0]


def test_detect_conflicts_does_not_flag_back_to_back_tasks():
    mochi = Pet(name="Mochi", species="Dog")
    mochi.add_task(Task(title="Morning Walk", time="08:00", duration_minutes=30))
    luna = Pet(name="Luna", species="Cat")
    luna.add_task(Task(title="Feeding", time="08:30", duration_minutes=15))

    owner = Owner(name="Jordan")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler()
    schedule = scheduler.generate_schedule(owner)

    assert schedule.conflicts == []


def test_detect_conflicts_does_not_flag_tasks_with_a_real_gap():
    mochi = Pet(name="Mochi", species="Dog")
    mochi.add_task(Task(title="Morning Walk", time="08:00", duration_minutes=15))
    luna = Pet(name="Luna", species="Cat")
    luna.add_task(Task(title="Feeding", time="09:00", duration_minutes=15))

    owner = Owner(name="Jordan")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler()
    schedule = scheduler.generate_schedule(owner)

    assert schedule.conflicts == []


def test_detect_conflicts_identifies_only_the_overlapping_pair_among_three():
    mochi = Pet(name="Mochi", species="Dog")
    mochi.add_task(Task(title="Morning Walk", time="08:00", duration_minutes=20))
    luna = Pet(name="Luna", species="Cat")
    luna.add_task(Task(title="Feeding", time="08:15", duration_minutes=10))
    rex = Pet(name="Rex", species="Dog")
    rex.add_task(Task(title="Evening Walk", time="18:00", duration_minutes=20))

    owner = Owner(name="Jordan")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    owner.add_pet(rex)

    scheduler = Scheduler()
    schedule = scheduler.generate_schedule(owner)

    assert len(schedule.conflicts) == 1
    assert "Morning Walk" in schedule.conflicts[0]
    assert "Feeding" in schedule.conflicts[0]
    assert "Evening Walk" not in schedule.conflicts[0]


def test_category_weight_returns_correct_weight_for_known_categories():
    assert Task(title="Pills", category="Medication").category_weight() == 3
    assert Task(title="Walk", category="Walking / Exercise").category_weight() == 2
    assert Task(title="Brush", category="Grooming").category_weight() == 1


def test_category_weight_falls_back_to_zero_for_unrecognized_or_missing_category():
    assert Task(title="Mystery", category="Not A Real Category").category_weight() == 0
    assert Task(title="No Category").category_weight() == 0


def test_combined_score_sums_priority_score_and_category_weight():
    task = Task(title="Walk", priority="high", category="Walking / Exercise")

    assert task.priority_score() == 3
    assert task.category_weight() == 2
    assert task.combined_score() == 5


def test_sort_by_priority_and_need_ranks_medication_above_higher_priority_other_task():
    pet = Pet(name="Mochi", species="Dog")
    medication = Task(title="Pills", time="09:00", priority="medium", category="Medication")
    other = Task(title="Misc Task", time="08:00", priority="high", category="Other")
    pet.add_task(medication)
    pet.add_task(other)

    owner = Owner(name="Jordan")
    owner.add_pet(pet)

    scheduler = Scheduler()
    entries = scheduler.sort_by_priority_and_need(scheduler.get_all_tasks(owner))

    assert medication.combined_score() == 5  # medium (2) + Medication (3)
    assert other.combined_score() == 3  # high (3) + Other (0)
    assert [task.title for _, task in entries] == ["Pills", "Misc Task"]


def test_generate_schedule_with_priority_sort_reorders_entries_versus_default_time_sort():
    pet = Pet(name="Mochi", species="Dog")
    pet.add_task(Task(title="Pills", time="09:00", priority="medium", category="Medication"))
    pet.add_task(Task(title="Misc Task", time="08:00", priority="high", category="Other"))

    owner = Owner(name="Jordan")
    owner.add_pet(pet)

    scheduler = Scheduler()
    time_sorted = scheduler.generate_schedule(owner)
    priority_sorted = scheduler.generate_schedule(owner, sort_by="priority")

    assert [e.task.title for e in time_sorted.entries] == ["Misc Task", "Pills"]
    assert [e.task.title for e in priority_sorted.entries] == ["Pills", "Misc Task"]


def test_save_and_load_data_round_trips_owner_pets_and_tasks(tmp_path):
    filepath = str(tmp_path / "data.json")

    mochi = Pet(name="Mochi", species="Dog", breed="Shiba Inu", age=36)
    mochi.add_task(
        Task(
            title="Morning Walk",
            time="08:00",
            duration_minutes=20,
            frequency="daily",
            priority="high",
            category="Walking / Exercise",
            completed=True,
            recurrence_handled=True,
        )
    )
    mochi.add_task(
        Task(
            title="Dinner",
            time="18:00",
            duration_minutes=10,
            frequency="once",
            priority="medium",
            category="Feeding",
        )
    )

    luna = Pet(name="Luna", species="Cat", breed="Tabby", age=24)
    luna.add_task(
        Task(
            title="Medication",
            time="09:00",
            duration_minutes=5,
            frequency="daily",
            priority="high",
            category="Medication",
        )
    )

    owner = Owner(name="Jordan")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    save_data(owner, filepath)
    loaded_owner = load_data(filepath)

    assert loaded_owner is not None
    assert isinstance(loaded_owner, Owner)
    assert loaded_owner.name == owner.name
    assert len(loaded_owner.pets) == 2

    loaded_mochi = loaded_owner.get_pet("Mochi")
    assert isinstance(loaded_mochi, Pet)
    assert loaded_mochi.name == "Mochi"
    assert loaded_mochi.species == "Dog"
    assert loaded_mochi.breed == "Shiba Inu"
    assert loaded_mochi.age == 36
    assert len(loaded_mochi.tasks) == 2

    loaded_walk = next(t for t in loaded_mochi.tasks if t.title == "Morning Walk")
    assert isinstance(loaded_walk, Task)
    assert loaded_walk.time == "08:00"
    assert loaded_walk.duration_minutes == 20
    assert loaded_walk.frequency == "daily"
    assert loaded_walk.priority == "high"
    assert loaded_walk.category == "Walking / Exercise"
    assert loaded_walk.completed is True
    assert loaded_walk.recurrence_handled is True

    loaded_dinner = next(t for t in loaded_mochi.tasks if t.title == "Dinner")
    assert loaded_dinner.time == "18:00"
    assert loaded_dinner.duration_minutes == 10
    assert loaded_dinner.frequency == "once"
    assert loaded_dinner.priority == "medium"
    assert loaded_dinner.category == "Feeding"
    assert loaded_dinner.completed is False
    assert loaded_dinner.recurrence_handled is False

    loaded_luna = loaded_owner.get_pet("Luna")
    assert loaded_luna.species == "Cat"
    assert loaded_luna.breed == "Tabby"
    assert loaded_luna.age == 24
    assert len(loaded_luna.tasks) == 1

    loaded_med = loaded_luna.tasks[0]
    assert loaded_med.title == "Medication"
    assert loaded_med.time == "09:00"
    assert loaded_med.duration_minutes == 5
    assert loaded_med.frequency == "daily"
    assert loaded_med.priority == "high"
    assert loaded_med.category == "Medication"
    assert loaded_med.completed is False
    assert loaded_med.recurrence_handled is False

    # Reloaded objects should be real dataclass instances with working methods.
    loaded_med.mark_complete()
    assert loaded_med.is_complete()
    loaded_luna.add_task(Task(title="Extra", time="10:00"))
    assert len(loaded_luna.tasks) == 2


def test_load_data_returns_none_when_file_does_not_exist(tmp_path):
    filepath = str(tmp_path / "does_not_exist.json")

    assert load_data(filepath) is None


def test_load_data_returns_none_for_invalid_json(tmp_path):
    filepath = tmp_path / "corrupt.json"
    filepath.write_text("not valid json")

    assert load_data(str(filepath)) is None
