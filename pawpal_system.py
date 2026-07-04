import json
import os
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple

PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}

CATEGORY_WEIGHTS = {
    "Medication": 3,
    "Feeding": 3,
    "Vet / Health": 3,
    "Walking / Exercise": 2,
    "Cleaning": 2,
    "Grooming": 1,
    "Enrichment / Play": 1,
    "Training": 1,
    "Rest / Comfort": 1,
    "Other": 0,
}


def _format_minutes(total_minutes: int) -> str:
    """Format minutes-since-midnight back into an "HH:MM" string for display."""
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours:02d}:{minutes:02d}"


@dataclass
class Task:
    """A single pet care activity scheduled for a specific time of day."""

    title: str
    time: str = "08:00"  # "HH:MM", 24-hour
    duration_minutes: int = 15
    frequency: str = "once"  # "once", "daily", "weekly"
    priority: str = "medium"  # "low", "medium", "high"
    category: Optional[str] = None
    notes: Optional[str] = None
    completed: bool = False
    recurrence_handled: bool = False  # internal flag so a task only recurs once

    def priority_score(self) -> int:
        """Return a numeric score so tasks can be sorted by priority."""
        return PRIORITY_SCORES.get(self.priority, 2)

    def category_weight(self) -> int:
        """Return a numeric "need" weight for this task's category, defaulting to 0."""
        return CATEGORY_WEIGHTS.get(self.category, 0)

    def combined_score(self) -> int:
        """Return priority urgency plus category need, for combined-priority scheduling."""
        return self.priority_score() + self.category_weight()

    def start_minutes(self) -> int:
        """Parse self.time ("HH:MM") into minutes since midnight (e.g. "08:30" -> 510)."""
        try:
            hours_str, minutes_str = self.time.split(":")
            hours, minutes = int(hours_str), int(minutes_str)
        except (AttributeError, ValueError):
            raise ValueError(
                f"Task {self.title!r} has an unparseable time {self.time!r}; expected \"HH:MM\"."
            )
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError(
                f"Task {self.title!r} has an out-of-range time {self.time!r}; expected \"HH:MM\"."
            )
        return hours * 60 + minutes

    def end_minutes(self) -> int:
        """Return this task's start time in minutes plus its duration."""
        return self.start_minutes() + self.duration_minutes

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def is_complete(self) -> bool:
        """Return whether this task has been completed."""
        return self.completed

    def display(self) -> str:
        """Return a short human-readable summary of this task."""
        status = "done" if self.completed else "pending"
        return f"{self.time} - {self.title} | {self.priority} priority | {self.duration_minutes} min ({status})"

    def next_occurrence(self) -> Optional["Task"]:
        """If this is a completed recurring task, return a fresh copy for its next occurrence."""
        if not self.completed or self.frequency not in ("daily", "weekly"):
            return None
        return Task(
            title=self.title,
            time=self.time,
            duration_minutes=self.duration_minutes,
            frequency=self.frequency,
            priority=self.priority,
            category=self.category,
            notes=self.notes,
            completed=False,
        )


@dataclass
class Pet:
    """A pet belonging to an owner, along with its own list of care tasks."""

    name: str
    species: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None  # age in months
    food_preference: Optional[str] = None
    notes: Optional[str] = None
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """Remove the first task matching the given title. Return True if one was removed."""
        for i, task in enumerate(self.tasks):
            if task.title == title:
                self.tasks.pop(i)
                return True
        return False

    def get_tasks(self) -> List[Task]:
        """Return this pet's list of tasks."""
        return self.tasks


@dataclass
class Owner:
    """The pet owner, who can have multiple pets."""

    name: str
    pets: List[Pet] = field(default_factory=list)
    preferences: Optional[str] = None
    daily_start_time: Optional[str] = None  # "HH:MM"; tasks earlier than this are hidden

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove the first pet matching the given name. Return True if one was removed."""
        for i, pet in enumerate(self.pets):
            if pet.name == pet_name:
                self.pets.pop(i)
                return True
        return False

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Return the pet with the given name, or None if not found."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return (pet, task) pairs for every task across every pet this owner has."""
        pairs = []
        for pet in self.pets:
            for task in pet.get_tasks():
                pairs.append((pet, task))
        return pairs


def save_data(owner: Owner, filepath: str = "data.json") -> None:
    """Serialize an owner (and its pets and tasks) to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(asdict(owner), f, indent=2)


def load_data(filepath: str = "data.json") -> Optional[Owner]:
    """Load an owner (and its pets and tasks) from a JSON file, or return None if missing/invalid."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return None

    pets = []
    for pet_data in data.get("pets", []):
        tasks = [Task(**task_data) for task_data in pet_data.get("tasks", [])]
        pet_kwargs = {k: v for k, v in pet_data.items() if k != "tasks"}
        pets.append(Pet(tasks=tasks, **pet_kwargs))

    owner_kwargs = {k: v for k, v in data.items() if k != "pets"}
    return Owner(pets=pets, **owner_kwargs)


@dataclass
class ScheduleEntry:
    """A task paired with the pet it belongs to, ready for display."""

    pet: Pet
    task: Task

    def display(self) -> str:
        """Return a short human-readable summary of this entry."""
        return self.task.display()


@dataclass
class Schedule:
    """The result of running the scheduler: sorted tasks plus any warnings."""

    owner: Owner
    entries: List[ScheduleEntry] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    recurring_updates: List[str] = field(default_factory=list)

    def by_pet(self) -> Dict[str, List[ScheduleEntry]]:
        """Group schedule entries by pet name, preserving schedule order."""
        grouped: Dict[str, List[ScheduleEntry]] = {}
        for entry in self.entries:
            grouped.setdefault(entry.pet.name, []).append(entry)
        return grouped


class Scheduler:
    """Retrieves, sorts, filters, and organizes tasks across an owner's pets."""

    def get_all_tasks(self, owner: Owner) -> List[Tuple[Pet, Task]]:
        """Collect every (pet, task) pair for the owner."""
        return owner.get_all_tasks()

    def sort_by_time(self, entries: List[Tuple[Pet, Task]]) -> List[Tuple[Pet, Task]]:
        """Sort (pet, task) pairs chronologically by the task's time."""
        return sorted(entries, key=lambda pair: pair[1].time)

    def sort_by_priority_then_time(self, entries: List[Tuple[Pet, Task]]) -> List[Tuple[Pet, Task]]:
        """Sort (pet, task) pairs by priority first (high to low), then by time."""
        return sorted(entries, key=lambda pair: (-pair[1].priority_score(), pair[1].time))

    def sort_by_priority_and_need(self, entries: List[Tuple[Pet, Task]]) -> List[Tuple[Pet, Task]]:
        """Sort (pet, task) pairs by combined priority+category score (high to low), then by time."""
        return sorted(entries, key=lambda pair: (-pair[1].combined_score(), pair[1].time))

    def filter_tasks(
        self,
        entries: List[Tuple[Pet, Task]],
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Tuple[Pet, Task]]:
        """Filter (pet, task) pairs by pet name and/or completion status."""
        result = list(entries)
        if pet_name is not None:
            result = [(pet, task) for pet, task in result if pet.name == pet_name]
        if completed is not None:
            result = [(pet, task) for pet, task in result if task.completed == completed]
        return result

    def detect_conflicts(self, entries: List[Tuple[Pet, Task]]) -> List[str]:
        """Return a warning for each pair of tasks whose time ranges overlap.

        Two tasks overlap when one starts before the other ends, in both
        directions (the standard half-open interval overlap test). Tasks
        that are merely back-to-back (one ends exactly when the next
        starts) do not count as overlapping. Any task with a time string
        that can't be parsed is skipped for that pair rather than raising,
        so one bad task doesn't crash conflict detection for everyone else.
        """
        tasks = [task for _, task in entries]

        conflicts = []
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                task_a, task_b = tasks[i], tasks[j]
                try:
                    a_start, a_end = task_a.start_minutes(), task_a.end_minutes()
                    b_start, b_end = task_b.start_minutes(), task_b.end_minutes()
                except ValueError:
                    continue

                if a_start < b_end and b_start < a_end:
                    conflicts.append(
                        f"Overlap detected: '{task_a.title}' ({task_a.time}-{_format_minutes(a_end)}) "
                        f"overlaps with '{task_b.title}' ({task_b.time}-{_format_minutes(b_end)})."
                    )
        return conflicts

    def handle_recurring_task(self, task: Task) -> Optional[Task]:
        """Return the next occurrence of a completed recurring task, if any."""
        return task.next_occurrence()

    def generate_schedule(
        self,
        owner: Owner,
        pet_name: Optional[str] = None,
        include_completed: bool = False,
        sort_by: str = "time",
    ) -> Schedule:
        """Build a full Schedule: roll forward recurring tasks, then sort and filter for display."""
        schedule = Schedule(owner=owner)

        # Roll forward any recurring tasks that were just completed.
        for pet, task in self.get_all_tasks(owner):
            if task.completed and task.frequency in ("daily", "weekly") and not task.recurrence_handled:
                next_task = self.handle_recurring_task(task)
                if next_task:
                    pet.add_task(next_task)
                    task.recurrence_handled = True
                    when = "tomorrow" if task.frequency == "daily" else "in 7 days"
                    schedule.recurring_updates.append(
                        f'{task.frequency.capitalize()} task "{task.title}" was completed and rescheduled for {when}.'
                    )

        entries = self.get_all_tasks(owner)
        if owner.daily_start_time is not None:
            entries = [(pet, task) for pet, task in entries if task.time >= owner.daily_start_time]
        entries = self.filter_tasks(entries, pet_name=pet_name, completed=None if include_completed else False)
        entries = self.sort_by_time(entries)
        schedule.conflicts = self.detect_conflicts(entries)

        if sort_by == "priority":
            entries = self.sort_by_priority_and_need(entries)

        schedule.entries = [ScheduleEntry(pet=pet, task=task) for pet, task in entries]
        return schedule
