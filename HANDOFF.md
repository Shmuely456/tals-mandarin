# Tal's Mandarin: handover notes

Everything a new Claude session needs to continue this project. Written 2026-10-22.

## What this is

A Duolingo-style web app for **Tal Shmuely** (GitHub `Shmuely456`), who is learning to **speak** Mandarin
with a private tutor (**老师**, Chinese, appears to be in mainland China, UTC+8). They have one class a week,
recorded with **Wispr Flow** (connected to Claude as a connector). After each class Claude turns the recording
into a new unit of lessons.

Two sides:

- **Tal (English UI):** a lesson path with hearts, XP, streaks, sounds, a panda mascot, a Guidebook and a Words list.
- **Tutor (Chinese UI, the 老师 tab):** Tal's profile, practice between classes, most-missed words with the wrong
  answers, accuracy for each skill, a tone mix-up grid, homework, notes to Tal and Tal's questions for class.

## What Tal asked for (keep these)

- The learning experience should feel **exactly like Duolingo**.
- The tutor's side must be **in Chinese**. She should see Tal's name, goals and progress, what's going well,
  and where he's struggling between classes. She can send notes back.
- **When importing a Wispr Flow transcript:** read all of it and keep **only learning content** (words, sentences,
  grammar, corrections, mistakes, homework, what went well). Leave out life talk, health, scheduling small talk,
  payments and anything unrelated. Never link to the full Wispr Flow notes.
- Every word and sentence needs **recorded audio**. The phone's speech voice was silent on Tal's iPhone, so clips
  play through a media element, which also works in silent mode.
- Correct answers chime and give a light vibration. Wrong answers buzz, shake the screen and vibrate.
- It has to be a **real installable app**: full screen with its own icon and no browser or Claude bars.

## Where things are

| Thing | Location |
|---|---|
| App (single file: HTML, CSS, JS) | `index.html` |
| Public lesson content | `content/lessons.json`, `content/items.json`, `content/audio.json`, `content/profile.json` |
| Audio clips (AAC) | `audio/zhNNN.m4a` |
| Fonts, trimmed to the characters in use | `fonts/*.woff2` (rebuild with `tools/subset_fonts.py`) |
| Offline support | `sw.js` (**bump `VERSION` on every change**) |
| Install metadata | `manifest.webmanifest` (no `start_url` on purpose: iOS keeps the `?k=` access key from the URL) |
| Icons | `icons/` (design B "cinnabar seal" in use; A and C are in `icons/design-*-1024.png`) |
| Live site | https://shmuely456.github.io/tals-mandarin/ (GitHub Pages from `main`) |
| Old version (Claude artifact) | https://claude.ai/artifact/XW1ccyfvBHyjUZc6MypL3S |

The repo is **public**, so private things stay out of it. That covers Tal's full name, class notes (summary, what
went well, struggles), progress and messages. The old artifact's database still holds the private class notes for
lesson `l-20261020` (fields `summary`, `strengths`, `struggles`, each also with `_zh`) and the full profile
(`profile/student`). Read them with the ArtifactData tool when moving them to the sync server.

## Current state

- The app works fully **on one device**: progress, sessions, homework and messages are saved in `localStorage`
  (`tm-progress`, `tm-sessions`, `tm-homework`, `tm-messages`, `tm-items`).
- The 老师 tab is a preview on Tal's phone. The tutor doesn't have her own link yet.
- Unit 1 (class of 2026-10-20, "Reading characters: 你叫什么名字？"): 30 words, 11 sentences and 4 grammar tips
  in 9 lesson steps, plus 52 audio clips.

## Next step: connect the sync server (Supabase)

Tal created a Supabase project named **tals-mandarin** (region Central EU, Frankfurt). The session environment has:

- `SUPABASE_ACCESS_TOKEN`: a personal access token for the Supabase Management API.
- Network access to `api.supabase.com` and `*.supabase.co`.

Plan:

1. `GET https://api.supabase.com/v1/projects` with `Authorization: Bearer $SUPABASE_ACCESS_TOKEN` to find the
   project ref, then `GET /v1/projects/{ref}/api-keys` for the publishable (anon) and secret (service_role) keys.
2. Create the schema with `POST /v1/projects/{ref}/database/query` (`{"query": "..."}`):
   - `docs(collection text, id text, data jsonb, updated_at timestamptz default now(), primary key (collection, id))`
   - `access_keys(key text primary key, role text check (role in ('student','tutor')), label text)`
   - RLS **on** for both, with **no** policies, so the anon key can't touch the tables directly.
   - A `security definer` function `api(k text, op text, payload jsonb) returns jsonb`. It looks up the role for
     `k` and does `pull` (everything changed since a timestamp), `put`, `patch` and `delete`.
     - Student writes: `progress`, `sessions`, `homework` (status, studentNote), `messages`.
     - Tutor writes: `messages`, `homework` (tutorFeedback, status, new tasks), `items` (words she adds).
     - Both read everything, including `notes` (private class notes) and `profile`.
     - Grant execute to `anon`.
3. Create two random keys (32+ bytes, base64url): one for Tal (student) and one for the tutor.
4. Add `config.js` with the project URL and the **publishable** key (public by design), and load it from
   `index.html`. In the storage layer (`persist`, `loadContent`, `subscribe`), keep the local copy and add sync:
   - Read the key from `?k=` (then remember it in `localStorage`).
   - Pull on start, when the app comes back to the foreground, and every 30 seconds.
   - Push every write, and queue writes made offline.
   - On first sync, upload anything already saved locally.
   - Role `tutor` means Chinese UI by default, the 老师 tab first, and `S.isOwner = false`.
5. Move the private data from the old artifact into `docs` (the `notes` collection and `profile/student`), and show
   class notes in the Guidebook and the 老师 tab again (`summary`, `strengths`, `struggles` and the `_zh` versions).
6. Give Tal two links:
   - His: `https://shmuely456.github.io/tals-mandarin/?k=STUDENT_KEY`. He opens it in Safari, then
     Share › Add to Home Screen. If his old local progress is in the installed app, it uploads on first sync.
   - The tutor's: `https://shmuely456.github.io/tals-mandarin/?k=TUTOR_KEY#teacher`, sent over WeChat. Also
     give him a short Chinese message to send with it.
7. Remove the "preview of your tutor's page" notice (`syncNotice()`) once sync works.

## Weekly lesson import

1. Wispr Flow: `search_meetings`, then `get_meeting` with `view_transcript`. Read the **whole** transcript.
2. Keep only learning content (see the rules above). The tutor calls Tal 糖 (Táng). The textbook appears to be
   HSK Standard Course 1 (lesson 3 dialogues with 李月).
3. Lesson id `l-YYYYMMDD`. Public fields go in `content/lessons.json`: `n`, `date`, `endAt`, `title`,
   `title_zh`, `topics`, `topics_zh`, `next`, `next_zh`. Class notes (summary, strengths, struggles, in English and
   Chinese) are **private**, so they go to the sync server.
4. Items go in `content/items.json`. Each one has `lessonId`, `step` (about 5 items per lesson circle, with sentences
   in later steps), `order`, `type` (word, phrase, sentence or grammar), `hanzi`, `pinyin`, `syl` (numbered
   citation tones, e.g. `["ni3","hao3"]`), `english`, `notes` (the tutor's memory tricks), `lookalikes`
   (characters Tal confuses), `focus: true` if he struggled with it in class, and `tokens` (`[{h, p}]`) for
   sentences. Grammar items also have `pattern` and `explain`.
5. Audio: `python3 tools/gen_audio.py <models dir>` (Kokoro v1.1 voice 55 through sherpa-onnx; download link in
   the script). GitHub release downloads work from the session, but Hugging Face is blocked.
6. Fonts: `python3 tools/subset_fonts.py <folder with source ttf>`. Sources come from the Google Fonts css2 API:
   Fredoka wght 500..700, Nunito wght 500..800, Noto Serif SC 500 and 700.
7. Bump `VERSION` in `sw.js`, commit and push to `main`. GitHub Pages redeploys in about a minute.

## Notes

- Speaking practice is self-checked: there is no microphone access.
- iPhones only allow a light haptic tap from websites (the iOS 18 switch trick). Android vibrates fully.
- Hearts reset every lesson.
- Practice-session doc fields: `startedAt`, `endedAt`, `date`, `mode`, `node`, `lessonId`, `passed`, `hearts`,
  `maxCombo`, `total`, `correct`, `xp`, `durationSec`, `skills`, `misses`, `tones`, `toneErrors`, `items`.
  Progress docs (one per item, Leitner boxes 0–6): `box`, `due`, `seen`, `correct`, `wrong`, `lastSeen`,
  `lastResult`, `firstSeen`.
