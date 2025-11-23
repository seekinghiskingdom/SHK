## Infinite Bible – Unified Board Model (Bible + Boards)

Infinite Bible is a single tool with two primary modes built on the same board model:

- **Bible Mode** – chapter-based “Bible boards” (one board per chapter).
- **Boards Mode** – free-form named boards for topics, projects, or notes.

All data is stored locally in the browser (no accounts, no sync).

### 1. Board identity

Each board has a stable `boardId` and a `type`:

- `type: "bible"` – chapter boards
  - `boardId` format: `bible:{translation}:{BOOK3}:{chapter}`
    - Example: `bible:kjv:GEN:1`, `bible:kjv:JHN:3`.
- `type: "notes"` – free-form named boards
  - `boardId` format: `notes:{slugOrId}`
    - Example: `notes:proverbs-web`, `notes:2025-retreat-plan`, `notes:uuid-abc123`.

Each board object stores:

- `id` – the `boardId`.
- `type` – `"bible"` or `"notes"`.
- `label` – user-facing name, e.g. `"Genesis 1 (KJV)"` or `"Proverbs Web – January"`.
- `translation` – code like `"kjv"` (required for `type: "bible"`).
- `book` – 3-letter book code like `"GEN"`, `"JHN"` (required for `type: "bible"`).
- `chapter` – chapter number (required for `type: "bible"`).
- `viewState` – canvas pan/zoom and other view settings.
- `items` – array of verse blocks, notes, highlights, etc.
- `createdAt`, `updatedAt` – ISO timestamps.

Verse text is never stored inside boards. It is always resolved from the shared Bible Tools v1 data via the Scripture Core helper.

### 2. Item types

Each board `items[]` entry has a `kind` and a minimal payload:

- `kind: "verse-block"`
  - `translation` – code like `"kjv"`.
  - `book` – 3-letter book code.
  - `chapter` – chapter number.
  - `verses` – array of verse numbers (one or many).
  - `layout` – at minimum `{ x, y, width?, height? }`.
  - optional `style` and `decorations` (stickers, connections; empty in early v1).

- `kind: "note"`
  - `text` – note content.
  - `layout` – `{ x, y, width?, height? }`.
  - optional `decorations`.

- `kind: "bookmark"` (planned)
  - Either references a verse (`translation/book/chapter/verses`) or a board region.

- `kind: "highlight"` / `kind: "section"` (planned)
  - Represent semantic groupings or visual spans tied to verses or regions.

Boards can mix any item kinds. All item types are always tied to a board via its `boardId`.

### 3. Modes and filters

Modes are UI filters over the same data:

- **Bible mode**
  - Only shows `type: "bible"` boards.
  - Left sidebar: books and chapters (from Bible Tools v1), where each chapter maps to `boardId = bible:{translation}:{BOOK3}:{chapter}`.
  - Opening a chapter:
    - If the board exists → load its saved layout.
    - If no board exists → generate a default layout (e.g., verse blocks for that chapter, no notes) in memory.

- **Boards mode**
  - Only shows `type: "notes"` boards.
  - Left sidebar: list of named boards, with options to create, rename, duplicate, and archive.

Views like Notes / Bookmarks / Sections / Highlights are also filters:
they list items of that kind from the currently active board type (Bible or Boards).

### 4. Persistence rules

All Infinite Bible data is stored in `localStorage` (per browser, per device).

Global settings (single object):

- `schemaVersion` – integer, e.g. `1`.
- `lastMode` – `"bible"` or `"notes"`.
- `lastBoardId` – last opened board, if any.
- `canvasTheme` – `"light"` or `"dark"` (later additional themes).
- `sidebarCollapsed` – `true`/`false` for the left drawer.

Board storage:

- Boards are **only persisted** if they contain any real user content:
  - At least one non-verse item (e.g., a note, highlight, bookmark), or
  - A non-default layout (later).
- Opening a chapter without adding anything:
  - Creates a default in-memory board for that chapter (for the current session).
  - If the user closes or navigates away without adding notes/highlights/etc., the board is not written to storage.
- This prevents 1,000+ “empty” chapter boards from accumulating while still preserving any chapter where the user has actually worked.

The storage serialization is designed so schema upgrades can migrate data by `schemaVersion` when needed.

### 5. Scripture text resolution

Infinite Bible never reads Bible JSON files directly. It always:

1. Uses the shared Bible Tools v1 index:
   - `/data/v1/tools/bible-viewer/index.json`.
2. Uses the Scripture Core helper functions (see “Scripture Core API” section):
   - `listBooks(translation)`
   - `getChapter(translation, bookCode3, chapterNumber)`
   - `getPassage(translation, bookCode3, chapterNumber, versesArray)`

Verse blocks in boards only store references (`translation`, `book`, `chapter`, `verses[]`).
When rendering, the app resolves those via Scripture Core into `{ verse, text }` for display.
