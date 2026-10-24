# Tal's Mandarin

A Duolingo-style Mandarin app for Tal and his tutor (老师). Read `HANDOFF.md` first: it has the full history,
Tal's requirements, the data model, the weekly lesson import and the next step (connecting Supabase).

Rules that always apply:

- When importing a class from a Wispr Flow transcript, read all of it and keep **only learning content**. Leave out
  life talk, health, payments and scheduling chat. Never link to the full Wispr Flow notes.
- The repository is public: no private data in it (Tal's full name, class notes, progress, messages).
- The tutor's side (the 老师 tab) stays in Chinese. Tal's side stays in English.
- Check every new word and sentence against CC-CEDICT and the HSK textbook conventions (characters, pinyin, tones,
  meaning) before it goes in; HANDOFF.md step 4 has the pinyin rules.
- Every new word and sentence gets an audio clip from `tools/gen_audio.py` (same voice for every clip). Listen to
  any clip it flags "check by ear".
- After any change to app files, bump `VERSION` in `sw.js` so installed copies update.
