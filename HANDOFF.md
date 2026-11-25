# Tal's Mandarin: handover notes

Everything a new Claude session needs to continue this project. Written 2026-10-22.

## What this is

A Duolingo-style web app for **Tal** (GitHub `Shmuely456`), who is learning to **speak** Mandarin
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
  API, and rotate one by updating that table.
- **Management API access:** Tal's Supabase personal access token is saved on the cloud environment as a network
  secret for `api.supabase.com`, and the session's proxy adds it to every request. So call
  `https://api.supabase.com/v1/projects/giuumcebqctbkrccxepn/database/query` (POST `{"query": "..."}`) with no
  Authorization header of your own; the old `SUPABASE_ACCESS_TOKEN` variable is stale and not needed. Tokens expire
  (Supabase's default is 30 days). On 401 "Invalid access token", Tal makes a new one (supabase.com, Account →
  Access Tokens → Generate new token, Database read and write, a long expiry) and saves it through the
  credential form. Never ask him to paste it in chat.
- **Server:** `supabase/schema.sql` has the tables (`docs`, `access_keys`) and the `api(k, op, payload)` function.
  RLS is on with no policies, so the public key can only call `api()`.
  - `docs` collections: `progress`, `sessions`, `homework`, `messages`, `items` (words added in the app), plus two
    private ones: `notes` (class notes for each lesson id: `summary` as text, `strengths` and `struggles` as lists
    of short strings, and the same with `_zh`; the app also splits a text at semicolons) and
    `profile` (`student`: full name, goal, cadence, focus, wants_zh).
  - The app merges `notes` into the lessons, and the server `profile` over `content/profile.json`.
- **App sync** (`index.html`, boot section): pulls on start, every 20 seconds while open, and when the app returns to
  the foreground. Writes go into a queue (`tm-queue`) that uploads in order, so offline changes upload later. The first
  sync from a student device uploads anything practiced before the link was used. `config.js` holds the project URL
  and the publishable key (public by design).
- Unit 1 (class of 2026-10-20, "Reading characters: 你叫什么名字？"): 30 words, 6 phrases, 11 sentences and 5 grammar
  tips in 10 lesson steps, plus 57 audio clips. Step 10 comes from the class handout Tal sent (the textbook's 生词 page):
  its word building (中国老师, 美国学生, 中国人…) and 这是什么书？. When a handout arrives, check the unit against it.
- Unit 2 (class of 2026-10-26, "She's my Chinese teacher: 谁 · 哪 · 的", textbook Lesson 4): 15 words, 5 phrases,
  10 sentences and 5 grammar tips in 7 steps, from the handout (生词 page and the 谁/哪 notes) plus what was practiced
  in class (不客气, 喜欢, 也, 咖啡, 女朋友, 本/个, and Tal's corrected sentences). Private notes are in `notes/l-20261026`.
  老师 tested Tal with the app in class and liked that it drills tones and the lesson's own words.
- Unit 3 (class of 2026-11-12, "Introduce yourself: 几岁 · 有 · 多少钱"; not recorded in Wispr Flow): 19 words,
  7 phrases, 37 sentences and 3 grammar tips in 13 steps, plus 66 audio clips. Steps 1–7 come from 老师's worksheet
  (her Google Doc "Tal Chinese"): her fill-in-the-blank questions (with her own answer choices where she gave them), age
  (你今年几岁？), 有 (我有一个中国朋友。), polite words and 很高兴认识你！. Names in her examples were changed to
  the textbook's 李月. The parts where Tal writes about himself (his own sentences, his self-introduction) stay on
  paper. Steps 8–13 come from the class handout 11.12.pdf: her notes (年 and 今年是二零二六年, 多少钱, 元, 美元,
  一百, 字 vs 学) and Tal's corrected workbook pages for textbook Lesson 4 (picture words, question-and-answer
  matching, fill-in-the-blank with the book's word banks). Fill-in-the-blank was also added to 你叫什么名字？ and
  你是学生吗？ in Unit 1. 谁 stays shuí as on 老师's 10.26 slides, although the workbook prints shéi (both are right;
  the 谁 note says so). Private notes (from the handout) are in `notes/l-20261112`.
- Unit 4 (class of 2026-11-16, "My family: 几口人 · 两 · 多 · 大", textbook Lesson 5 她女儿今年二十岁): 12 words,
  2 phrases, 13 sentences and 4 grammar tips in 6 steps, plus 34 audio clips. 老师 went through the lesson's
  character cards (家, 有, 口, 女儿, 几, 岁, 了, 今年, 多, 大) with memory tricks, then practiced describing pictures and
  families: 她今年多大？ (no 是 before an age), 你的家有几口人？ (口 counts family members), 两 before a measure word,
  几 with a measure word and no 吗, 很多, 在 for where, and adjectives without 是 (你的家大吗？不大). Tricks for words
  already in the app went into their notes (有, 几, 今年, 字). Real ages and the talk that wasn't the lesson are left
  out. Private notes are in `notes/l-20261116`.
- Unit 5 (class of 2026-11-24, "Ages and counting: 几岁了 · 多大了 · 几口人"; not recorded in Wispr Flow): 4 words,
  2 phrases, 14 sentences and 2 grammar tips in 5 steps, from the handout 11.24.pdf: the textbook Lesson 5 生词 page
  examples (我家有五口人, 她是谁的女儿？), its notes on 几 + measure word, 了 for a change (李老师今年五十岁了) and
  多大了, and 老师's typed notes (你今年多大了？, 个 and 口, 你的学校有几个学生？, 在 in/on/at). Her example age
  (28) is replaced with 二十. "Pick the right answer" pairs each question with its answer.
- The old Claude-artifact version (https://claude.ai/artifact/XW1ccyfvBHyjUZc6MypL3S) is retired. Its data has
  been copied over.

### Adding a lesson's private class notes

Use the Management API SQL endpoint, upserting into `docs` with collection `notes` and the lesson id as the id. Use
dollar-quoted JSON (`$tm$...$tm$::jsonb`) and set `updated_at = now()` so devices pull it.

## Weekly lesson import

A fresh container has none of the tools: first run `bash tools/setup_tools.sh <scratch folder>`, which installs the
Python packages and downloads the voice, the two recognizers, CC-CEDICT and the font sources (about 1.3 GB).

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
   A sentence can also have `fill` (`[{blank, choices}]`), which adds a fill-in-the-blank exercise. `blank` must be
   one of its tokens, and `choices` are 3 different words that include it. Use 老师's own choices when she gives
   them, and make sure no wrong choice also makes a correct sentence (你学谁？ is fine Chinese, so 谁 can't be a wrong
   choice for 你学什么？).
   An answer can have `reply` (`{to, choices}`), which adds "pick the right answer": the app plays and shows the
   question `to` and offers 3 `choices`, one of them the item itself. The question and every choice must be items
   (for their pinyin and audio). Pick wrong choices that can't answer the question, even loosely: 她 and 他 sound the
   same, so "不是，她是…" also answers 他是你的朋友吗？ out loud.
   Pinyin follows the textbook (HSK Standard Course) and CC-CEDICT: simplified characters; neutral tone as `5`
   (学生 xuésheng `xue2 sheng5`); 不 and 一 written with their changed tone (不是 bú shì `bu2 shi4`, 一个 yí gè);
   3rd + 3rd written as two 3rd tones (你好 nǐ hǎo), because that's how it's printed. The tone exercise explains
   the 3rd + 3rd change, and the audio applies it.
5. Audio: `python3 tools/gen_audio.py <folder>/models` (download links in the script). The voice is Matcha-TTS trained
   on the Baker corpus (a professional female speaker reading standard Putonghua; licensed for non-commercial use),
   chosen because its tones follow the textbook shapes; the Kokoro voice used before blurred 1st/4th and 2nd/3rd
   tones and hummed an "ooh" before short words. Every take is transcribed by two speech recognizers (SenseVoice,
   Paraformer) and single syllables also have their pitch shape checked; listen to any clip printed with
   "check by ear" and redo it with `--redo <text>`. A lone particle (的, 吗, 呢) is checked in a short phrase (我的, 你好吗,
   你呢), because recognizers can't tell it apart alone. Some misses are fine: 她 and 他 sound the same (tā), and a lone
   哪 is often written 那 by recognizers even though its tone is checked as 3rd. A run of 3rd tones turns all but the
   last into 2nd tones, except a subject 我/你 in front of two more (你有几个 nǐ yóu jǐ gè), which otherwise sounds
   like 您. Recognizers also tend to hear a lone 3rd tone as 2nd (百 as 白) and a lone 字 as 四, so trust the pitch shape
   there.
   GitHub release downloads work from the session, but Hugging Face is blocked.
6. Fonts: `python3 tools/subset_fonts.py <folder>/fonts-src`. Sources come from the Google Fonts css2 API:
   Fredoka wght 500..700, Nunito wght 500..800, Noto Serif SC 500 and 700.
7. Bump `VERSION` in `sw.js`, commit and push to `main`. GitHub Pages redeploys in about a minute.

### Worksheets and handouts from 老师

- A **handout** for a class (like 10.20.pdf) adds to that class's unit: check the unit against it and add what's missing.
  Handouts are named by class date (10.20, 10.26, 11.12), so a handout for a day with no unit means there was a class
  that day, even if Wispr Flow didn't record it: make it a class unit with the next `n`.
- A **worksheet** that comes with a class goes into that class's unit (her Nov 12 Google Doc came with 11.12.pdf, so
  both are Unit 3). A worksheet on its own gets its own unit: a lesson in `content/lessons.json` with
  `kind: "worksheet"`, `id`, `date`, `title`, `title_zh`, `topics` and `topics_zh`, but no `n`, `endAt` or `next`.
  It isn't a class, so it has no class day, the next-class card and "since last class" ignore it, and it shows as
  "Worksheet from 老师" (练习) instead of a unit number. Classes keep their own `n`, so the class after a worksheet is
  still numbered correctly.
- Turn her questions into exercises; leave out what Tal should write about himself, and don't fill in his answers.

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
