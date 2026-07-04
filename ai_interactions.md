# AI Interactions Log

I used Claude as my coding assistant for pretty much this whole project, but I never ran it as one
giant conversation. I split the work into separate chat sessions, one per phase — system design and
UML, the backend classes, wiring up Streamlit, the scheduling algorithms, tests, and now this latest
round of persistence/overlap/priority work plus these docs. That's the same split I talk about in
`reflection.md`, and it held up again this round: I opened one fresh session just for "add real
overlap detection, priority scoring, and JSON saving," and a separate one for writing up this file
and the README.

## What actually drove the work

Early on, most of my requests were about turning a plan into code — I'd already worked out in the
UML that `Scheduler` should own sorting, filtering, conflicts, and recurrence, and I asked AI to help
turn that shape into real `Task`/`Pet`/`Owner`/`Scheduler` classes. Partway through, I ended up
pivoting the scheduler itself: my first instinct was to think about tasks in terms of "does this fit
into a block of free time," like a duration-fitting problem, but that's not actually how a pet owner
thinks about their day. So I asked for help reworking it around time-of-day scheduling instead — a
task happens at 08:00, not "sometime after breakfast" — plus conflict warnings and daily/weekly
recurrence layered on top of that.

This latest round was narrower and more specific. I went in already knowing the three things I
wanted: (1) `data.json` persistence so the app stops forgetting everything on refresh, (2) conflict
detection that actually compares time ranges instead of just matching exact start times, and (3) a
priority + category scoring system so a `Medication` task at medium priority can outrank a `high`
priority `Other` task. Describing each of those as its own scoped request, instead of something vague
like "make the scheduler smarter," made a real difference in how usable the first draft of the code
was.

## What AI actually produced

Concretely, AI helped write: the `start_minutes()`/`end_minutes()` methods and the rewritten
`detect_conflicts()` that uses them, the `CATEGORY_WEIGHTS` dict plus `category_weight()` and
`combined_score()`, `sort_by_priority_and_need()` and the new `sort_by` parameter on
`generate_schedule()`, the `save_data()`/`load_data()` functions, the Daily Timeline section and the
Time / Priority + Need sort toggle in `app.py`, the whole batch of new pytest tests for all of the
above, and this file plus the README updates alongside it.

## What I checked myself

Two things I didn't just take on faith:

1. **The overlap boundary math.** It would be really easy for an overlap check to accidentally flag
   every back-to-back pair too — like a walk that ends at 08:30 and a feeding that starts at 08:30 —
   because on paper those times "touch." I walked through the actual comparison
   (`a_start < b_end and b_start < a_end`) by hand with that exact case and confirmed it comes out
   false right at the boundary, then made sure there was a dedicated test
   (`test_detect_conflicts_does_not_flag_back_to_back_tasks`) locking that in, separate from the test
   that checks two tasks that genuinely overlap.

2. **Recurring tasks not piling up.** Once `generate_schedule()` started creating a fresh occurrence
   for a completed daily/weekly task, my first worry was: what happens if I generate the schedule
   twice in a row — does it create a second new occurrence, then a third, every time the page reruns?
   I ran it by hand, then wrote
   `test_generate_schedule_does_not_duplicate_recurring_task_on_repeat_calls` to check that the pet's
   task list stayed at exactly two tasks (the original completed one, plus one new occurrence) after
   calling `generate_schedule()` twice. That's what the `recurrence_handled` flag on `Task` is
   actually for.

## What I said no to

AI's first pass at persistence suggested a lot more than I needed — a real embedded database
(SQLite), or at least a schema and migrations, and while we were at it, maybe user accounts so
multiple people could each have their own saved data. Same story with recurrence: there was a
suggestion to build out a proper recurrence engine that could handle things like "every Monday and
Thursday" or "every other week." I said no to all of it. A flat `data.json` file that gets read once
and overwritten on every save, no login system, and recurrence that only understands "daily" or
"weekly" is genuinely all this project needs. Reaching for a database or auth here would have added a
lot of surface area to build, test, and explain without actually making the app better at the thing
it's supposed to do.

## What this round taught me

The thing that stuck with me this time is that "more accurate" isn't automatically "more correct" —
it's just more surface area I'm now responsible for checking myself. Real overlap detection is
objectively better than exact-time matching, but it also introduces boundary cases (does "touching"
count as overlapping?) that didn't exist before, and nobody was going to verify those for me except
me. Persistence was the same kind of decision: choosing JSON over a database wasn't really a
technical call, it was a judgment about what this project actually needs to be, and I had to be able
to defend that choice on my own. Adding capability doesn't get me out of deciding what "correct" even
means for this app — if anything, every new feature just adds one more place where that decision has
to happen, and I can't outsource it.
