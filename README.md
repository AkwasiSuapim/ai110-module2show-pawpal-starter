# PawPal+ (Module 2 Project)

## Project Overview

**PawPal+** is a Streamlit app that helps a busy pet owner stay on top of daily pet care. An owner
can manage multiple pets, add care tasks with a scheduled time, priority, category, and recurrence,
then generate today's schedule. The scheduler sorts tasks chronologically, flags tasks that land on
the same time slot, and automatically reschedules daily/weekly tasks once they're marked complete.

The system is built around one idea:

> The user provides the information, the `Scheduler` makes the decisions, and the `Schedule` presents the result.

This keeps the Streamlit UI thin — it only collects input and displays output. All scheduling logic
(sorting, filtering, conflict detection, recurrence) lives in `pawpal_system.py`.

## Features

- Multiple pets per owner, each with its own species icon, breed, age, food preference, and notes
- Care tasks with a scheduled time, duration, priority, category, frequency, and optional notes
- Chronological scheduling via `Scheduler.sort_by_time()`, plus a combined priority + category
  ("need") view via `Scheduler.sort_by_priority_and_need()`
- Filtering by pet and/or completion status
- Real overlap-based conflict detection — flags tasks whose `[start, end]` time ranges actually
  overlap (via `Task.start_minutes()`/`end_minutes()`), not just tasks that share an exact start time
- Automatic rescheduling of daily/weekly tasks once they're marked complete
- A Daily Timeline view: a flat, chronological, cross-pet list of today's tasks, shown above the
  per-pet schedule tables
- Simple JSON persistence — an owner's pets and tasks are saved to `data.json` and reloaded
  automatically the next time the app starts
- A Streamlit UI organized into clear, scrollable sections backed by `st.session_state`, auto-saving
  to disk after every pet or task change

## System Design / UML

The final class diagram lives at [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) (earlier drafts are
kept in the same folder for reference). It shows four core classes — `Task`, `Pet`, `Owner`, and
`Scheduler` — plus two small result classes, `Schedule` and `ScheduleEntry`, that the scheduler
returns:

```text
Owner "1" --> "0..*" Pet          : owns
Pet   "1" --> "0..*" Task         : has
Scheduler --> Schedule            : creates
Schedule "1" --> "0..*" ScheduleEntry : contains
```

`ScheduleEntry` pairs a `Task` with the `Pet` it belongs to, which is what lets the UI and CLI group
today's schedule by pet.

## How to Run the App

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app automatically loads `data.json` (if one exists in the project folder) on startup, and saves
to it after every pet or task change, so your data survives a page refresh or restart. Delete
`data.json` (or just don't create one) to start from a clean slate.

## How to Run the CLI Demo

```bash
python main.py
```

## How to Run Tests

```bash
python -m pytest
```

## Sample CLI Output

`python main.py` builds a demo owner ("Jordan") with two pets — Mochi (a dog with a completed daily
feeding task) and Luna (a cat with a task at the same time as Mochi's walk) — then prints:

```text
=== Today's Schedule (sorted by time) ===

Today's Schedule for Jordan

Pet: Mochi 🐶
08:00 - Morning Walk | high priority | 20 min (pending)
09:00 - Feeding | high priority | 10 min (pending)

Pet: Luna 🐱
08:00 - Medication | high priority | 5 min (pending)
18:00 - Grooming | low priority | 30 min (pending)

Warnings:
- Overlap detected: 'Morning Walk' (08:00-08:20) overlaps with 'Medication' (08:00-08:05).

Recurring Updates:
- Daily task "Feeding" was completed and rescheduled for tomorrow.

=== Sorted by priority, then time ===

🐶 Mochi: 08:00 - Morning Walk | high priority | 20 min (pending)
🐱 Luna: 08:00 - Medication | high priority | 5 min (pending)
🐶 Mochi: 09:00 - Feeding | high priority | 10 min (done)
🐶 Mochi: 09:00 - Feeding | high priority | 10 min (pending)
🐱 Luna: 18:00 - Grooming | low priority | 30 min (pending)

=== Filtered: Mochi's tasks only ===

Today's Schedule for Jordan

Pet: Mochi 🐶
08:00 - Morning Walk | high priority | 20 min (pending)
09:00 - Feeding | high priority | 10 min (pending)
```

Note the recurring "Feeding" task: the original was already marked `completed=True` in the demo
data, so `generate_schedule()` created its next daily occurrence automatically and reported it under
"Recurring Updates" — that new, pending occurrence is what shows up in "Today's Schedule" instead of
the completed one.

## Smarter Scheduling

| Feature | Method | Notes |
|---|---|---|
| Sorting by time | `Scheduler.sort_by_time()` | Orders (pet, task) pairs chronologically by `Task.time` |
| Priority sorting | `Scheduler.sort_by_priority_then_time()` | Optional: high → medium → low, then by time |
| Priority + category scoring | `Task.category_weight()`, `Task.combined_score()` | Combines priority with a per-category "need" weight, via a module-level `CATEGORY_WEIGHTS` dict (Medication/Feeding/Vet-Health = 3, Walking-Exercise/Cleaning = 2, Grooming/Enrichment/Training/Rest-Comfort = 1, Other = 0) |
| Priority + category sorting | `Scheduler.sort_by_priority_and_need()` | Sorts by `Task.combined_score()` (high to low), then by time; selected via the `sort_by="priority"` option on `generate_schedule()` |
| Filtering | `Scheduler.filter_tasks()` | Filters by pet name and/or completion status |
| Conflict detection | `Scheduler.detect_conflicts()` | Flags tasks whose real `[start, end]` time ranges overlap, using `Task.start_minutes()`/`end_minutes()` — back-to-back tasks that merely touch are correctly not flagged |
| Recurring tasks | `Scheduler.handle_recurring_task()` | Creates the next daily/weekly occurrence once a task is completed |
| Persistence | `save_data()`, `load_data()` | Serializes/reloads an `Owner` (with its pets and tasks) to/from `data.json`, using only `json` + `dataclasses.asdict` from the standard library |
| Full schedule | `Scheduler.generate_schedule()` | Combines all of the above into one `Schedule` result; accepts `sort_by="time"` (default) or `sort_by="priority"` |

## Demo Walkthrough

1. Enter owner information (name, the time your day starts, optional preferences).
2. Add one or more pets — name, species (with an emoji icon), breed, age in months, food preference, and notes.
3. Select a pet from the Pet List to manage their tasks.
4. Add care tasks with a time, duration, priority, frequency (once/daily/weekly), category, and optional notes.
5. Generate today's schedule — optionally filter to just the selected pet, include completed tasks, and choose to sort by Time or by Priority + Need.
6. Review the Daily Timeline (a flat, chronological, cross-pet list) at the top of Today's Schedule, then the same tasks grouped by pet in the tables below.
7. Check Conflict Warnings for any tasks whose time ranges actually overlap — not just tasks that happen to start at the exact same minute.
8. Mark tasks complete from the Task List — daily/weekly tasks automatically reschedule, and that shows up under Explanations / Recurring Updates.
9. Refresh or restart the app whenever you like — your pets and tasks were auto-saved to `data.json` and reload automatically.

## Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output (`python -m pytest -v`, captured 2026-07-04):

```text
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0 -- .venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/mac/Desktop/codepath/AI110/w4/ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collecting ... collected 26 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  3%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED   [  7%]
tests/test_pawpal.py::test_sort_by_time_returns_chronological_order PASSED [ 11%]
tests/test_pawpal.py::test_filter_tasks_by_pet_name PASSED               [ 15%]
tests/test_pawpal.py::test_filter_tasks_by_completion_status PASSED      [ 19%]
tests/test_pawpal.py::test_completing_daily_task_creates_next_occurrence PASSED [ 23%]
tests/test_pawpal.py::test_generate_schedule_does_not_duplicate_recurring_task_on_repeat_calls PASSED [ 26%]
tests/test_pawpal.py::test_detect_conflicts_flags_same_time_tasks PASSED [ 30%]
tests/test_pawpal.py::test_scheduler_handles_owner_with_no_tasks PASSED  [ 34%]
tests/test_pawpal.py::test_get_pet_returns_none_for_missing_pet PASSED   [ 38%]
tests/test_pawpal.py::test_generate_schedule_with_unknown_pet_name_returns_empty_schedule PASSED [ 42%]
tests/test_pawpal.py::test_generate_schedule_handles_owner_with_no_pets_at_all PASSED [ 46%]
tests/test_pawpal.py::test_sort_by_time_handles_boundary_times_correctly PASSED [ 50%]
tests/test_pawpal.py::test_daily_start_time_filter_is_inclusive_of_exact_match PASSED [ 53%]
tests/test_pawpal.py::test_detect_conflicts_flags_overlapping_different_start_times PASSED [ 57%]
tests/test_pawpal.py::test_detect_conflicts_does_not_flag_back_to_back_tasks PASSED [ 61%]
tests/test_pawpal.py::test_detect_conflicts_does_not_flag_tasks_with_a_real_gap PASSED [ 65%]
tests/test_pawpal.py::test_detect_conflicts_identifies_only_the_overlapping_pair_among_three PASSED [ 69%]
tests/test_pawpal.py::test_category_weight_returns_correct_weight_for_known_categories PASSED [ 73%]
tests/test_pawpal.py::test_category_weight_falls_back_to_zero_for_unrecognized_or_missing_category PASSED [ 76%]
tests/test_pawpal.py::test_combined_score_sums_priority_score_and_category_weight PASSED [ 80%]
tests/test_pawpal.py::test_sort_by_priority_and_need_ranks_medication_above_higher_priority_other_task PASSED [ 84%]
tests/test_pawpal.py::test_generate_schedule_with_priority_sort_reorders_entries_versus_default_time_sort PASSED [ 88%]
tests/test_pawpal.py::test_save_and_load_data_round_trips_owner_pets_and_tasks PASSED [ 92%]
tests/test_pawpal.py::test_load_data_returns_none_when_file_does_not_exist PASSED [ 96%]
tests/test_pawpal.py::test_load_data_returns_none_for_invalid_json PASSED [100%]

============================== 26 passed in 0.06s ===============================
```

**Confidence: ★★★★☆ (4/5)**

All backend behaviors required by the spec are covered and passing, including regression tests for
two bugs caught during manual testing (recurring tasks duplicating on repeated schedule generation,
and conflict detection needing to compare real time ranges rather than exact start times), plus
isolated, disposable `save_data()`/`load_data()` round-trip tests built on pytest's `tmp_path`
fixture, including a corrupt-JSON case. One star held back because the Streamlit UI itself still
isn't covered by automated tests — only the backend in `pawpal_system.py` is.

## Known Limitations

- **Recurrence doesn't track calendar dates.** A "next occurrence" is a fresh, uncompleted `Task`
  with the same time-of-day — the app doesn't store an actual date per task, so "tomorrow" and "in 7
  days" are just labels used in the explanation text, not persisted values.
- **`data.json` is a single flat file.** Persistence is intentionally simple: one JSON file holding
  one owner, no multi-user support, and no protection against two processes writing to it at the same
  time. That's fine for one person running the app locally, but it isn't a real data layer. This
  tradeoff is documented in `reflection.md`.
- **Conflict detection is a simple pairwise comparison.** `Scheduler.detect_conflicts()` now compares
  real `[start, end]` time ranges (via `Task.start_minutes()`/`end_minutes()`) instead of just exact
  start times, but it does so by checking every pair of tasks, which is O(n²). That's fast enough for
  the handful of tasks a pet owner would realistically schedule in a day, but it wouldn't scale
  cleanly to hundreds of tasks — a real interval-tree or sweep-line approach would be needed at that
  size. This tradeoff is also documented in `reflection.md`.

## Future Improvements

- Track an actual calendar date per task so recurring tasks can be viewed across multiple days
- Let the owner reorder or edit existing tasks instead of only adding/removing them
- Move persistence from a single flat `data.json` file to a real database if multi-user support is
  ever needed
- Replace the pairwise overlap check with a more efficient interval-tree or sweep-line approach if the
  task list ever grows large
