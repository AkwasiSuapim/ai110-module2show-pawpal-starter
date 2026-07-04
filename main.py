"""Command-line demo for the PawPal+ backend (see pawpal_system.py).

Run with: python main.py
"""

from pawpal_system import Owner, Pet, Scheduler, Task

PET_ICONS = {
    "Dog": "🐶",
    "Cat": "🐱",
    "Bird": "🐦",
    "Rabbit": "🐰",
    "Hamster": "🐹",
    "Fish": "🐟",
    "Guinea Pig": "🐹",
    "Turtle": "🐢",
}


def get_pet_icon(species):
    return PET_ICONS.get(species, "🐾")


def build_demo_owner():
    owner = Owner(name="Jordan")

    mochi = Pet(name="Mochi", species="Dog", breed="Shih Tzu", age=24)
    mochi.add_task(
        Task(title="Morning Walk", time="08:00", duration_minutes=20, priority="high",
             category="Walking / Exercise", frequency="daily")
    )
    mochi.add_task(
        Task(title="Feeding", time="09:00", duration_minutes=10, priority="high",
             category="Feeding", frequency="daily", completed=True)
    )

    luna = Pet(name="Luna", species="Cat", breed="Tabby", age=36)
    luna.add_task(
        Task(title="Medication", time="08:00", duration_minutes=5, priority="high",
             category="Medication", frequency="daily")
    )
    luna.add_task(
        Task(title="Grooming", time="18:00", duration_minutes=30, priority="low", category="Grooming")
    )

    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner


def print_schedule(schedule):
    print(f"Today's Schedule for {schedule.owner.name}\n")

    grouped = schedule.by_pet()
    if not grouped:
        print("No tasks scheduled.")

    for pet_name, entries in grouped.items():
        pet = entries[0].pet
        print(f"Pet: {pet_name} {get_pet_icon(pet.species)}")
        for entry in entries:
            print(entry.display())
        print()

    if schedule.conflicts:
        print("Warnings:")
        for warning in schedule.conflicts:
            print(f"- {warning}")
        print()

    if schedule.recurring_updates:
        print("Recurring Updates:")
        for update in schedule.recurring_updates:
            print(f"- {update}")
        print()


def main():
    owner = build_demo_owner()
    scheduler = Scheduler()

    print("=== Today's Schedule (sorted by time) ===\n")
    schedule = scheduler.generate_schedule(owner)
    print_schedule(schedule)

    print("=== Sorted by priority, then time ===\n")
    entries = scheduler.sort_by_priority_then_time(scheduler.get_all_tasks(owner))
    for pet, task in entries:
        print(f"{get_pet_icon(pet.species)} {pet.name}: {task.display()}")
    print()

    print("=== Filtered: Mochi's tasks only ===\n")
    mochi_schedule = scheduler.generate_schedule(owner, pet_name="Mochi")
    print_schedule(mochi_schedule)


if __name__ == "__main__":
    main()
