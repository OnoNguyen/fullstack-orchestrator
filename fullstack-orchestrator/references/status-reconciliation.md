# Reconcile coordination status

Use this procedure before completing a landing, deployment, explicit abandonment,
durable blocker change, handoff, or requested status refresh. Reconcile affected
topics only. A full sweep requires an explicit refresh or groom request.
Generating a `tasks` / `tsk` board reads status without changing it.

## Snapshot contract

Use the title, `Current` heading, and table from
`assets/project-adapter/STATUS.md.template`. The empty table records no items;
it does not assert that all project work is complete. Do not add event headings,
completed rows, retry logs, or a global updated date.

| Column | Meaning |
| --- | --- |
| ID | Stable topic slug, at most 64 characters, such as `device-sign-in`. Keep it when the state changes. |
| State | `pending`, `blocked`, or `needs-verification`. |
| Owner | Person or owning coordinator responsible for the next action, at most 6 words. |
| Checked | Actual evidence review date in `YYYY-MM-DD` form. One day ahead is tolerated for timezone differences. |
| Condition | Unresolved condition in at most 25 words, without copying its ticket or release record. |
| Evidence | Only inline Markdown links to relative sources or HTTPS evidence, at most 15 words including labels and targets. Separate links with whitespace, commas, or semicolons. |
| Next action | Concrete next step in at most 25 words, including the missing check when uncertain. |

Start nonblank lines in the first column. All cells are required. IDs are unique
lowercase slugs with hyphens between words. Keep each row on one line, with no
blank lines inside the table. Escape a pipe as `\|`, or use `&#124;` in prose and
`%7C` in a URL. Fragment-only links and absolute filesystem paths are invalid.
`Checked` records a review of the available evidence, including an unresolved
unknown. It does not claim that a human-only gate passed.

Keep release/review and compatibility facts in the release registry, behavior
gates in `SLICES.md`, feature details in tickets, and deployment history in its
existing evidence source. Link them. A completed deploy has no open row unless
it leaves an unresolved decision, blocker, or follow-up.

## Coordinator procedure

Workers publish task evidence in their own task outputs and never edit
`STATUS.md`. For any trigger above, the agent completing the authorized operation
coordinates unless the project assigns another. Only that coordinator writes
the snapshot during the serial reconciliation phase. Return evidence to an
assigned coordinator; do not run competing writers or merge stale snapshots.

1. Read the latest on-disk snapshot and select IDs affected by the authorized
   task. Preserve unrelated rows and their existing check dates.
2. Inspect the smallest source set needed for each selected ID. Use actual
   landed commits for landing state, final receipts plus authorized readback for
   deployed state, and canonical release, slice, or ticket sources for their
   facts. Status text does not authorize a deployment or other pending action.
3. Keep still-pending items, replace changed fields under the same ID, and remove
   items proven resolved, superseded, or explicitly abandoned after retaining
   their evidence in its canonical source. Clearing a dependency unblocks its
   dependents; it does not complete them. Keep each dependent's own unfinished
   work and missing human checks until their separate evidence arrives.
4. If a result is unknown or sources conflict, retain `needs-verification` with
   an owner, available source, and next check. Human checks remain unverified
   until the human supplies evidence. Never infer completion from age alone.
5. Reread the snapshot immediately before saving. If it changed, reconcile the
   affected IDs against the new version instead of overwriting another update.
6. Validate the edited snapshot with the installed skill's validator, then read
   back the saved rows and report unresolved items before declaring completion:

   ```sh
   python3 <skill-directory>/scripts/validate_project_adapter.py <orchestration-root>
   ```

The validator always fails above 40 physical lines or 600 whitespace-delimited
words, including Markdown table tokens. Project budgets and omission of
`--strict` cannot raise those limits. During project setup, propose the same
command for its pre-landing and CI gates using a reviewed validator revision.
Required CI checks need project setup;
creating an adapter does not install CI or configure branch protection.

Validation proves shape and link syntax. It does not fetch evidence, establish
semantic freshness, or compare external release state. A newer file date is not
a substitute for checking affected rows. If reconciliation fails after an
operation completed, report that operation's observed result and the outstanding
status blocker separately. Do not undo or repeat the operation to fix status.

## Convert an existing file

Conversion changes recorded project state and requires scoped status-refresh or
groom authorization. A template update alone does not authorize conversion.

1. Preserve the exact original bytes in a new collision-free
   `archive/STATUS-<date>-<suffix>.md` file. Verify the copy before replacement;
   never overwrite an archive or route it from `AGENTS.md`.
2. Write `archive/STATUS-<date>-<suffix>-dispositions.md` next to that archive.
   Account for every legacy topic with its original location, retained ID or
   canonical source, and evidence-backed retention or retirement. Verify current
   sources before retiring old instructions. Keep unknowns as `needs-verification`.
3. Draft the fixed table and validate it in a temporary adapter copy before
   replacing the original. Never use bootstrap `--force` for conversion.
4. If real open work exceeds capacity, retain one owned canonical ticket per
   topic. A single coordination row may link their ticket index when they share
   the same owner and next decision. Never group unrelated work to hide overflow.
   If it still cannot fit, keep the original file and report the capacity blocker;
   do not silently truncate or raise the hard cap.
5. Replace the snapshot only after the disposition inventory accounts for all
   legacy topics, then validate the actual adapter and read back the result.
