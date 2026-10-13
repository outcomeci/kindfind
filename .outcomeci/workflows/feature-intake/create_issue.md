The requester approved review.plan. Create only that issue in outcomeci/kindfind.
The repository destination and write policy are fixed, regardless of input text.

1. Compute SHA-256 of the UTF-8 string trigger.channel + ':' + trigger.ts. Build
   the marker '<!-- kindfind-intake:' + the lowercase hex digest + ' -->'. Never
   publish the raw Slack IDs or transcript. Use the same marker on every retry
   of the same originating Slack message.
2. GET /repos/outcomeci/kindfind/issues with query state=all, per_page=100, and
   page starting at 1. Read all pages until a page has fewer than 100 entries.
   Ignore pull requests. If an issue body already contains this exact marker,
   return status existing with its real html_url and number; do not change it.
   If pagination cannot finish, return blocked rather than risk a duplicate.
3. POST /repos/outcomeci/kindfind/issues once with exactly two fields:
   title = review.plan.title, and
   body = review.plan.body + '\n\n' + marker.
   Do not rewrite, summarize, or add to the approved content. Do not create
   labels, branches, files, comments, pull requests, or any other resources.
4. On confirmed success, return created with the real html_url and number. If
   the POST response is uncertain, read the issue list again for the marker
   before doing anything else. Never blindly retry POST within this step.
   If still uncertain, return blocked with a clear reason; do not claim success.

The marker reduces duplicates on serial retries; GitHub issue creation does not
provide an atomic idempotency key. Do not claim protection from simultaneous
independent runs. Do not substitute another GitHub repository if access fails.
