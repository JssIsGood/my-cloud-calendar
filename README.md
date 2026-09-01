# Job Calendar Sync (OneDrive CSV -> ICS -> Google Calendar)

A Power Automate flow watches a OneDrive (Business) folder. Whenever a CSV is
added, changed, or deleted, it pushes that change straight to GitHub, which
rebuilds a single `docs/calendar.ics` file that any calendar app can
subscribe to by URL.

**No Azure AD app registration, no premium Power Automate connectors, no
credit card required anywhere in this pipeline.** Everything uses connectors
already included with your Microsoft 365 Business license (OneDrive for
Business) plus a free GitHub account (GitHub connector).

Because `docs/calendar.ics` is fully **rebuilt from scratch** on every run:
- Delete a CSV from OneDrive -> its events vanish from the next build.
- Edit a CSV -> its events are rebuilt with the same UID, so the calendar
  app updates them in place instead of duplicating.
- Add a CSV -> its events appear in the next build.

---

## How it fits together

1. **Power Automate flow(s)** - triggered by OneDrive for Business the
   moment a CSV in your folder is created, modified, or deleted.
2. The flow sends the file's name (and content, for create/modify) to
   GitHub using the built-in **GitHub connector's "Create a repository
   dispatch event"** action - a standard, free connector.
3. That fires a **GitHub Actions workflow** in this repo, which writes the
   file into `data/`, rebuilds `docs/calendar.ics` from everything in
   `data/`, and commits the result.
4. **GitHub Pages** serves `docs/calendar.ics` at a stable URL.
5. **Google Calendar** subscribes to that URL.

```
OneDrive folder --(Power Automate trigger)--> GitHub repository_dispatch
        --> GitHub Actions writes data/<job>.csv --> rebuilds calendar.ics
        --> commits --> GitHub Pages serves it --> Google Calendar subscribes
```

---

## One-time setup

### 1. Create the GitHub repository

1. Create a new **public** repo (e.g. `job-calendar-sync`) and commit all
   the files from this project (generated for you - see file list below).
2. **Settings -> Pages -> Source -> Deploy from a branch -> `main` / `docs`.**
   Your calendar URL will be:
   `https://<your-username>.github.io/<repo-name>/calendar.ics`
3. Create a GitHub **Personal Access Token** (Settings -> Developer settings
   -> Fine-grained tokens): scope it to this one repository, with
   **read/write access to "Contents"**. You'll use this to sign in to the
   GitHub connector inside Power Automate in step 2 - it's a normal GitHub
   login, not an Azure resource, so there's no billing involved.

### 2. Build the Power Automate flow(s)

Go to [make.powerautomate.com](https://make.powerautomate.com), signed in
with your Microsoft 365 Business account.

**Flow A - "OneDrive CSV added or changed"**

| Step | Action |
|---|---|
| Trigger | OneDrive for Business -> **When a file is created or modified (properties only)**, pointed at your job-CSV folder |
| Step 2 | OneDrive for Business -> **Get file content**, using the file identifier from the trigger |
| Step 3 | Condition: file name ends with `.csv` (skip everything else) |
| Step 4 | GitHub -> **Create a repository dispatch event**: Repository Owner = your GitHub username, Repository Name = your repo, Event Name = `csv-sync`, Event Payload = `{"action": "upsert", "file_name": "<file name from trigger>", "content": "@{base64(body('Get_file_content'))}"}` |

The first time you add the GitHub action, Power Automate will ask you to
sign in to GitHub - use the Personal Access Token from step 1.

**Flow B - "OneDrive CSV deleted"**

| Step | Action |
|---|---|
| Trigger | OneDrive for Business -> **When a file is deleted**, pointed at the same folder |
| Step 2 | Condition: file name ends with `.csv` |
| Step 3 | GitHub -> **Create a repository dispatch event**: Event Name = `csv-sync`, Event Payload = `{"action": "delete", "file_name": "<deleted file name>"}` |

Test both flows manually (Power Automate's "Test" button lets you trigger
off a real recent file event), confirm a commit shows up in your repo's
Actions tab, then turn both flows **On**. OneDrive for Business triggers in
Power Automate typically detect changes within a few minutes.

### 3. Seed the repo with your existing CSVs

The flows above only fire on *future* changes. To get the CSVs that already
exist in the folder into the repo the first time, the easiest way is: open
your local OneDrive-synced copy of the folder, copy the CSVs into a local
clone of the repo's `data/` folder, and commit/push once manually. After
that, the flows keep everything in sync automatically - no more manual
steps needed.

---

## Important limitation: refresh speed on the calendar-app side

Power Automate -> GitHub -> `calendar.ics` typically updates within a few
minutes of a OneDrive change. However, **Google Calendar controls its own
polling schedule for subscribed ICS URLs, typically once every 12-24
hours, and there's no setting to speed this up.** This is a Google
limitation, not something this pipeline can fix, and it applies to Apple
Calendar and Outlook subscriptions too.

If near-real-time updates on the phone matter more than staying entirely
inside free tooling, let me know and I can look at alternatives (e.g. a
two-way sync app instead of a passive ICS subscription) - but wanted to
flag this now rather than have it be a surprise later.

## Other limitation: GitHub's dispatch payload size

GitHub caps the `client_payload` used in step 4 above at roughly 10KB. Your
example CSV (6 rows) is under 1KB, so ordinary job schedules are fine. If a
job ever grows into hundreds of task rows in one CSV, that single file could
approach the limit - if that happens, say so and I'll adjust the flow (e.g.
splitting large files across two dispatch events).

---

## File overview

- `scripts/apply_event.py` - decodes the incoming Power Automate event and
  writes/deletes the corresponding file in `data/`.
- `scripts/generate_ics.py` - rebuilds `docs/calendar.ics` from every CSV
  currently in `data/`.
- `.github/workflows/sync.yml` - runs on each `repository_dispatch` from
  Power Automate (plus a daily safety-net rebuild) and commits the result.
- `requirements.txt` - Python dependency (`icalendar`).
- `data/` - mirror of your OneDrive folder's CSVs, kept in sync by Power
  Automate.
- `docs/calendar.ics` - the generated calendar (this is the file your phone
  subscribes to).

## CSV format assumed

Based on `JN090.csv`:

```
Task ID,Subject,Start Date,End Date,Start Time,End Time
JN090-001,[JN090] Signed acceptance proposal,09/09/26,09/09/26,14:30,15:30
```

- Dates are `DD/MM/YY` (Australian format).
- Times are 24-hour `HH:MM`.
- `Task ID` becomes the event's unique ID (UID) - this is what lets edits
  replace the old event instead of duplicating it.
- The CSV's filename (without `.csv`) becomes the event's **category**, so
  you can filter/color by job in calendar apps that support ICS categories.
- All 6 columns map into the ICS event as described in the script's docstring.
