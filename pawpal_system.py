from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta


@dataclass
class CareTask:
    title: str
    category: Optional[str] = None
    duration_minutes: int = 0
    priority: str = "medium"  # "low", "medium", "high"
    notes: Optional[str] = None
    recurring: bool = False

    def priority_score(self) -> int:
        mapping = {"low": 1, "medium": 2, "high": 3}
        return mapping.get(self.priority, 2)


@dataclass
class Pet:
    name: str
    species: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None
    food_preference: Optional[str] = None
    care_tasks: List[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        self.care_tasks.append(task)


@dataclass
class Owner:
    name: str
    available_minutes: int = 60
    preferred_start_time: Optional[datetime] = None
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)


@dataclass
class ScheduledTask:
    task: CareTask
    start_time: datetime
    end_time: datetime

    def display(self) -> str:
        return f"{self.start_time.strftime('%H:%M')} — {self.task.title} ({self.task.duration_minutes} min)"


@dataclass
class DailyPlan:
    owner: Owner
    pet: Pet
    scheduled_tasks: List[ScheduledTask] = field(default_factory=list)
    skipped_tasks: List[CareTask] = field(default_factory=list)
    explanations: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = []
        for s in self.scheduled_tasks:
            lines.append(s.display())
        return "\n".join(lines)


class Scheduler:
    def __init__(self):
        pass

    def generate_plan(self, owner: Owner, pet: Pet) -> DailyPlan:
        start = owner.preferred_start_time or datetime.now().replace(second=0, microsecond=0)
        remaining = owner.available_minutes
        plan = DailyPlan(owner=owner, pet=pet)

        tasks = list(pet.care_tasks)
        tasks.sort(key=lambda t: (-t.priority_score(), t.duration_minutes))

        cursor = start
        for task in tasks:
            if task.duration_minutes <= remaining:
                end = cursor + timedelta(minutes=task.duration_minutes)
                plan.scheduled_tasks.append(ScheduledTask(task=task, start_time=cursor, end_time=end))
                plan.explanations.append(f"Scheduled '{task.title}' because priority {task.priority} and fits.")
                cursor = end
                remaining -= task.duration_minutes
            else:
                plan.skipped_tasks.append(task)
                plan.explanations.append(f"Skipped '{task.title}' because only {remaining} minutes remain.")
        return plan

    # helpers for future refinement
    def sort_tasks(self, tasks: List[CareTask]) -> List[CareTask]:
        return sorted(tasks, key=lambda t: (-t.priority_score(), t.duration_minutes))

    def can_fit(self, task: CareTask, remaining_minutes: int) -> bool:
        return task.duration_minutes <= remaining_minutes
