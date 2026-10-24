# Tal's Mandarin: handover notes

Everything a new Claude session needs to continue this project. Written 2026-10-22.

## What this is

A Duolingo-style web app for **Tal Shmuely** (GitHub `Shmuely456`), who is learning to **speak** Mandarin
with a private tutor (**老师**, Chinese, UTC+8). She uses a VPN, so Google, Supabase, GitHub and Claude all work for her;
no China-specific workarounds are needed. They have one class a week,
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
- The Mandarin must be **exactly standard modern Mandarin from reliable sources** (asked 2026-10-24, after the old
  voice said "ooh" before words). Check characters, pinyin, tones and meanings against CC-CEDICT and the HSK textbook
  conventions, and keep the audio on a standard Putonghua voice that reads the app's own pinyin (see step 5 below).
- Feedback should feel **Apple-designed**: soft sounds in the spirit of iOS, a vibration on every correct answer and
  spring animations. Right: a rising two-note glass chime, two haptic taps and a check mark that draws itself.
  Wrong: a soft falling wooden knock, three taps and the wrong choice shakes. Taps on answers tick.
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

- **Live and syncing.** The app runs at the GitHub Pages address. Practice, homework, notes and messages sync through
  Supabase project `tals-mandarin` (ref `giuumcebqctbkrccxepn`, Frankfurt), and a copy stays on each device for offline use.
- **Personal links:** the access key in `?k=` decides the role. `student` is Tal: English UI and the Learn tab first.
  `tutor` is 老师: Chinese UI and the 老师 tab first. She can write notes, homework, feedback and words, but not
  practice. **Never commit the keys.** Read them with SQL (`select role, key from access_keys`) through the Management
  API using `SUPABASE_ACCESS_TOKEN`, and rotate one by updating that table.
- **Server:** `supabase/schema.sql` has the tables (`docs`, `access_keys`) and the `api(k, op, payload)` function.
  RLS is on with no policies, so the public key can only call `api()`.
  - `docs` collections: `progress`, `sessions`, `homework`, `messages`, `items` (words added in the app), plus two
    private ones: `notes` (class notes for each lesson id: `summary`, `strengths`, `struggles`, and `_zh`) and
    `profile` (`student`: full name, goal, cadence, focus, wants_zh).
  - The app merges `notes` into the lessons, and the server `profile` over `content/profile.json`.
- **App sync** (`index.html`, boot section): pulls on start, every 20 seconds while open, and when the app returns to
  the foreground. Writes go into a queue (`tm-queue`) that uploads in order, so offline changes upload later. The first
  sync from a student device uploads anything practiced before the link was used. `config.js` holds the project URL
  and the publishable key (public by design).
- Unit 1 (class of 2026-10-20, "Reading characters: 你叫什么名字？"): 30 words, 6 phrases, 11 sentences and 5 grammar
  tips in 10 lesson steps, plus 57 audio clips. Step 10 comes from the class handout Tal sent (the textbook's 生词 page):
  its word building (中国老师, 美国学生, 中国人…) and 这是什么书？. When a handout arrives, check the unit against it.
- The old Claude-artifact version (https://claude.ai/artifact/XW1ccyfvBHyjUZc6MypL3S) is retired. Its data has
  been copied over.

### Adding a lesson's private class notes

Use the Management API SQL endpoint, upserting into `docs` with collection `notes` and the lesson id as the id. Use
dollar-quoted JSON (`$tm$...$tm$::jsonb`) and set `updated_at = now()` so devices pull it.

## Weekly lesson import

1. Wispr Flow: `search_meetings`, then `get_meeting` with `view_transcript`. Read the **whole** transcript.
2. Keep only learning content (see the rules above). The tutor calls Tal 糖 (Táng). The textbook appears to be
   HSK Standard Course 1 (lesson 3 dialogues with 李月).
3. Lesson id `l-YYYYMMDD`. Public fields go in `content/lessons.json`: `n`, `date`, `endAt`, `title`,
   `title_zh`, `topics`, `topics_zh`, `next`, `next_zh`. Class notes (summary, strengths, struggles, in English and
   Chinese) are **private**, so they go to the sync server.
4. Items go in `content/items.json`. Each one has `lessonId`, `step` (about 5 items per lesson circle, with sentences
   in later steps), `order`, `type` (word, phrase, sentence or grammar), `hanzi`, `pinyin`, `syl` (numbered
   tones, e.g. `["ni3","hao3"]`), `english`, `notes` (the tutor's memory tricks), `lookalikes`
   (characters Tal confuses), `focus: true` if he struggled with it in class, and `tokens` (`[{h, p}]`) for
   sentences. Grammar items also have `pattern` and `explain`.
   Pinyin follows the textbook (HSK Standard Course) and CC-CEDICT: simplified characters; neutral tone as `5`
   (学生 xuésheng `xue2 sheng5`); 不 and 一 written with their changed tone (不是 bú shì `bu2 shi4`, 一个 yí gè);
   3rd + 3rd written as two 3rd tones (你好 nǐ hǎo), because that's how it's printed. The tone exercise explains
   the 3rd + 3rd change, and the audio applies it.
5. Audio: `python3 tools/gen_audio.py <models dir>` (download links in the script). The voice is Matcha-TTS trained
   on the Baker corpus (a professional female speaker reading standard Putonghua; licensed for non-commercial use),
   chosen because its tones follow the textbook shapes; the Kokoro voice used before blurred 1st/4th and 2nd/3rd
   tones and hummed an "ooh" before short words. Every take is transcribed by two speech recognizers (SenseVoice,
   Paraformer) and single syllables also have their pitch shape checked; listen to any clip printed with
   "check by ear". A lone particle like 吗 always gets flagged: without a sentence it can't show its neutral tone.
   GitHub release downloads work from the session, but Hugging Face is blocked.
6. Fonts: `python3 tools/subset_fonts.py <folder with source ttf>`. Sources come from the Google Fonts css2 API:
   Fredoka wght 500..700, Nunito wght 500..800, Noto Serif SC 500 and 700.
7. Bump `VERSION` in `sw.js`, commit and push to `main`. GitHub Pages redeploys in about a minute.

## Notes

- Speaking practice is self-checked: there is no microphone access.
- Sound effects are synthesized in `SFX` in `index.html` (no audio files), in A major: right answers rise A5 to E6,
  mistakes fall E4 to C4. Haptics (`haptic()`) follow Apple's patterns: one tick for a selection, two taps for success,
  three for an error. iPhones only allow a light tap from websites (the iOS 18 switch trick, and only with System
  Haptics on); Android vibrates fully. The display panel has switches for both.
- Animations use springs and run once per event (`#practice[data-fx]`); all of them respect Reduce Motion.
- Hearts reset every lesson.
- Practice-session doc fields: `startedAt`, `endedAt`, `date`, `mode`, `node`, `lessonId`, `passed`, `hearts`,
  `maxCombo`, `total`, `correct`, `xp`, `durationSec`, `skills`, `misses`, `tones`, `toneErrors`, `items`.
  Progress docs (one per item, Leitner boxes 0–6): `box`, `due`, `seen`, `correct`, `wrong`, `lastSeen`,
  `lastResult`, `firstSeen`.
