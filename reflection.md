# Final Reflection: PawPal+

## Design Choices

The idea behind PawPal+ came from thinking about how a busy pet owner actually manages their day. I didn't want to just dump a list of tasks on the user — I wanted the app itself to be the one doing the thinking. So the rule I kept coming back to was: the user's job is to give the app information, and it's the scheduler's job to turn that information into something useful. I tried to keep that boundary clean the whole way through.

I ended up with four main classes: `Owner`, `Pet`, `Task`, and `Scheduler`. I gave each one exactly one job, mostly because I've learned the hard way that once a Streamlit app starts doing logic inside the UI code, it gets messy fast and becomes annoying to debug.

### Owner

I made `Owner` because someone has to actually own the pets and be the person the schedule is built for. Once I realized a person could easily have more than one pet — which is honestly the more common case — it made sense for `Owner` to just hold a list of `Pet` objects rather than assuming there's only ever one.

The owner isn't the one figuring out the schedule, though. It just holds the pets and hands off access to their tasks. I wanted to resist the urge to cram scheduling logic in here just because it was convenient.

### Pet

Each `Pet` holds its own info — name, species, breed, age — and its own list of tasks. A dog needs walks, a cat needs litter cleaning, a bird needs something else entirely, so it made sense to let each pet carry its own task list instead of lumping everything into one big list and filtering constantly.

I also liked that this leaves room to grow later. If I ever wanted to add species-specific suggestions (like reminding a dog owner about walks more than a fish owner), `Pet` is already the right place to hang that logic.

### Task

`Task` represents one actual thing that needs to get done — feeding, medication, a walk, grooming, whatever. Every task type is different, but they all share the same shape: a name, a time, a duration, a priority, a category, and whether it's done yet.

I made completion status part of the `Task` itself instead of something the UI just tracks on its own, because completing a task is a real state change in the data, not just a visual checkbox. That distinction mattered to me — it's the difference between "the app looks like it's tracking something" and "the app is actually tracking something."

### Scheduler

`Scheduler` is where all the actual decision-making lives, and it was the class I was most protective of while building this. Streamlit's job is to collect input and show output — it should not be deciding how tasks get sorted, filtered, checked for conflicts, or repeated. That decision-making needed its own home.

So `Scheduler` is responsible for:

* pulling tasks from all of an owner's pets
* sorting tasks by time
* filtering by pet or by completion status
* catching scheduling conflicts
* handling recurring tasks
* putting all of that together into one schedule

Splitting it out this way made testing so much easier. I can test whether the scheduler actually works without ever touching Streamlit, which also means when something breaks, I know pretty quickly whether it's a UI problem or a logic problem.

The overall flow ended up being:

```text
User provides information
        ↓
Owner stores pets
        ↓
Pets store tasks
        ↓
Scheduler organizes the tasks
        ↓
Streamlit displays the result
```

Keeping that flow in my head the whole time is what kept the project from turning into a tangle.

---

## 2b. Tradeoffs

The tradeoff I think about the most is how conflict detection actually works.

Right now the scheduler only checks for conflicts when two tasks land on the exact same time — like if I have two tasks both set for `08:00`. That's the whole check. I know that's not a complete solution: a task from `08:00` to `08:30` and another from `08:15` to `08:25` genuinely overlap, but my scheduler wouldn't catch that because their start times are different. A "real" version of this would need to compare start and end times across every pair of tasks, not just match on the time string.

I went with the simpler version on purpose. At this stage, I'd rather have a conflict check that's obviously correct and easy to test than one that's technically more thorough but harder for me (or anyone reviewing this) to reason about. It felt like the right call for where this project is right now.

The second tradeoff is recurrence. When a daily or weekly task gets marked done, the app creates the next occurrence for you — but that's about as far as it goes. There's no real calendar behind it, so something like "every Monday and Thursday" or "every other week" just isn't supported. I decided that was fine for now; a full recurrence engine felt like a different, much bigger project.

The third one is that I'm using Streamlit's session state instead of any kind of database. That's what let me build this quickly and keep it simple to run locally, but it also means nothing sticks around once the session ends unless I add something like a `data.json` file later. I knew that going in and accepted it as a fair trade for keeping things simple.

Since I wrote that last paragraph, I actually went and added the `data.json` file, and there was a real tradeoff hiding inside "just add persistence." A real database would have made a couple of things easier — I wouldn't have to think as hard about two processes writing to the same file at the same time — but it also would have meant a schema, a new dependency, and a bunch of setup that has nothing to do with what this project is actually about. A flat file that I read once on startup and overwrite on every save is easy to open, easy to read, easy to delete and start over with, and it doesn't need anything beyond the standard library. For an app that's meant to run locally for one person, that felt like the right amount of infrastructure, not the maximum amount I could technically bolt on.

The other new tradeoff is how I ended up fixing conflict detection. I went back and made it compare real start/end time ranges instead of just matching exact start times, which is the thing I said above I'd get to eventually. The straightforward way to check that is to compare every pair of tasks against each other, which is completely fine when someone has ten tasks in a day but would slow down fast with hundreds of them. A more "correct" version would use something like an interval tree so it isn't comparing every single pair. I didn't build that. At the scale this app actually runs at — one person's daily pet care tasks — the simple pairwise version is plenty fast, and it's a lot easier for me to look at and know it's right. I'd rather ship the version I can fully explain than the version that's technically faster but that I'd just have to take on faith.

---

## AI Strategy

I used AI a lot while building this, but I tried to stay in the driver's seat the whole time. I still see myself as the one who decided what PawPal+ should actually do — AI was more like a very fast pair programmer than a co-designer.

### Where AI actually helped

A few things stood out as genuinely useful:

1. **Explaining how the pieces should talk to each other.** Working through how `Scheduler` should reach into `Owner` and grab tasks from each `Pet` helped me actually understand the object relationships instead of just copying structure.

2. **Turning a plan into code.** Once I had the UML and the responsibilities worked out in my head, AI was great at converting that into actual Python classes and methods quickly. But the thinking still had to happen first — it couldn't do that part for me.

3. **Drafting test cases.** It suggested pytest cases for things like completing a task, adding a task, sorting, recurrence, and conflicts. That was useful less for the code itself and more because it made me actually confront whether the system worked, not just whether it looked finished.

4. **Debugging.** When something failed, it helped explain why, and more importantly, helped me figure out whether the bug was in my test or in the actual backend logic — which isn't always obvious at first glance.

5. **Writing things up.** Organizing the README and this reflection so someone else could actually follow the project was something AI was helpful for, mostly because after staring at my own code for hours I'm not always the best judge of what's actually clear to a reader.

### What I pushed back on

Honestly, the biggest thing I rejected was scope creep. AI kept nudging toward "bigger" ideas — a database, authentication, a full calendar system, external APIs. None of that belonged in this project. I wanted something that worked cleanly at the size it needed to be, not something that looked impressive but was fragile or half-finished.

I also stuck with plain emojis for pet icons instead of letting it talk me into real images or icon files. It's a small thing, but it kept the app dead simple to run — no file paths, no downloads, nothing that could break on someone else's machine.

### Why splitting the work into separate sessions helped

I found it a lot easier to keep separate conversations for different phases of the project instead of trying to do design, coding, UI, testing, and writing all in one continuous thread. When I split it up — one phase for the UML and system design, one for the backend classes, one for hooking up Streamlit, one for the algorithms, one for tests, one for docs and this reflection — everything stayed a lot more focused. Each phase had one job, and I could build on top of the last one instead of everything blurring together.

### What this taught me about actually being in charge of the project

The biggest thing I took away from this is that AI can write code fast, but it still needs me to know what I actually want. If I don't have a clear picture of the design, AI will happily generate something that looks polished but doesn't actually match what the assignment (or I) needed.

Being the one actually responsible for this project meant I had to:

* understand the problem before asking for code
* decide on the classes and what each one owns
* figure out what belongs in a first version and what doesn't
* say no to complexity that wasn't earning its place
* make sure what got built actually matched what was asked
* test the parts that mattered
* be able to explain my own decisions afterward

The clearer I was going in, the better the output I got back. AI sped things up and helped me debug, but the decisions were mine.

---

## Optional Extensions Considered

I kept the required features as the priority and only thought about extras once the core system was actually working.

Some things I considered for later:

* saving/loading data from a `data.json` file
* stronger priority-based scheduling
* nicer formatted tables in the CLI output
* color-coded task status in Streamlit
* an `ai_interactions.md` file to log prompts and how I used AI suggestions

I didn't want to chase any of these at the expense of stability. My main goal was to end up with something that actually works, that I understand, and that I can explain — not a pile of half-built extras.

---

## Final Verification Plan

Before I call this done, I want to run:

```bash
python main.py
python -m pytest
streamlit run app.py
```

Each one checks a different layer:

* `python main.py` — confirms the backend logic actually works outside of any UI.
* `python -m pytest` — confirms the automated tests still pass.
* `streamlit run app.py` — confirms the app actually runs and behaves right in the browser.

---

## Git Commit Plan

Once everything checks out, I can commit it all at once:

```bash
git add .
git commit -m "feat: complete PawPal+ scheduler integration and tests"
git push origin main
```

Or, if I want a cleaner history to look back on, I can break it up:

```bash
git add .
git commit -m "feat: implement PawPal+ core classes"

git add .
git commit -m "feat: connect Streamlit UI to scheduler"

git add .
git commit -m "feat: add sorting filtering recurrence and conflict detection"

git add .
git commit -m "test: add automated tests for PawPal+"

git add .
git commit -m "docs: update README UML and reflection"

git push origin main
```

---

## Final Deliverables Checklist

Before I submit, I want to double check I have:

* a summary of what actually changed
* the final code pushed to GitHub
* my `python -m pytest` results
* the CLI output from `python main.py`
* known limitations written down honestly
* next steps if I had more time
* README updated
* this reflection updated
* UML updated
* the repo set to public if that's required
* everything committed and pushed before the deadline

---

## Known Limitations

I think of what I built as a solid, practical student project — not a finished pet-care platform someone could actually run a business on. It does what it needs to do for this assignment, but I'm not pretending it's more than that.

Here's what it doesn't do yet:

* Data doesn't stick around after the Streamlit session ends unless I add JSON persistence.
* Conflict detection only catches exact-time matches, not every kind of overlap.
* Recurring tasks are handled simply — there's no real calendar logic behind them.
* There are no reminders or notifications of any kind.
* There's no database and no user accounts.
* I didn't write automated tests for the Streamlit UI itself — just the backend logic.

I'm okay with these limitations for now. The point of this version was to show that I could design the classes cleanly, build working scheduling logic, wire it into Streamlit, and back it up with real tests — not to build a production-ready app in one pass.

---

## Suggested Next Steps

If I kept working on this past the assignment, here's what I'd actually want to do next:

1. Add JSON persistence so pets and tasks don't disappear between sessions.
2. Make conflict detection compare actual time ranges instead of just exact start times.
3. Build out real priority-based scheduling that weighs urgency and pet needs together.
4. Add a cleaner, more visual daily timeline in the Streamlit UI.
5. Write up an `ai_interactions.md` file documenting how I actually used AI throughout this.
6. Add more tests around edge cases — bad time inputs, missing pets, empty schedules, that kind of thing.

Looking back, this project taught me a lot more than just Python syntax. I practiced actually designing a system before writing code, thinking through tradeoffs instead of just picking the first solution, testing the parts that mattered instead of just eyeballing whether it "looked right," and using AI as a tool I was directing rather than one that was directing me. That last part is probably the thing I'll carry forward the most.
