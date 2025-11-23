# Infinite Bible – Core Model, Modes, and Status

## 1. Purpose and current status

- Infinite Bible is a single workspace with two primary modes built on the same board model: **Bible mode** (chapter boards) and **Boards mode** (free-form note boards).
- All data is stored locally in the browser (`localStorage`); there are no accounts or sync in v1.
- Code pieces:
  - UI shell (header, toolbar, navigator, workspace, mode switching, theme toggle) in `infinite-bible.html` + `infinite-bible.css`.
  - Core storage and board logic in `infinite-bible-core.js` (`window.IBT`).
  - Shared Scripture loading in `scripture-core.js` (`window.ScriptureCore`).
- Current implementation:
  - Renders the full app shell with toolbar, sidebar, and workspace.
  - Supports mode switching (Bible / Boards), theme switching (light/dark), and navigator toggle.
  - Sidebar and workspace content are placeholders; there is not yet a real canvas, no real boards UI, and no verse loading from Scripture Core.

This document replaces older Infinite Bible notes and summarizes the unified board model plus the current 2-in-1 Bible/Boards implementation.

## 2. Storage keys and global settings

LocalStorage keys:

- `IBT_SETTINGS_V1` – global settings object.
- `IBT_BOARDS_V1` – boards index and payloads.

`IBT_SETTINGS_V1` shape (schemaVersion 1):

- `schemaVersion: number` – currently `1`.
- `lastMode: "bible" | "notes"` – last active primary mode.
- `lastBoardId: string | null` – last board opened (e.g. `bible:kjv:GEN:1` or `notes:proverbs-web`).
- `canvasTheme: "light" | "dark"` – current canvas/workspace theme.
- `sidebarCollapsed: boolean` – whether the navigator sidebar is collapsed in the layout.

`IBT_BOARDS_V1` shape:

- Root object: `{ schemaVersion: 1, boards: { [boardId]: Board } }`.

## 3. Board identity and core fields

Two board types share one structure:

- `type: "bible"` – chapter boards  
  - `boardId` format: `bible:{translation}:{BOOK3}:{chapter}`  
    - Examples: `bible:kjv:GEN:1`, `bible:kjv:JHN:3`.
- `type: "notes"` – free-form named boards  
  - `boardId` format: `notes:{slugOrId}`  
    - Examples: `notes:proverbs-web`, `notes:2025-retreat-plan`, `notes:uuid-abc123`.

Each `Board` object:

- `id: string` – the `boardId`.
- `type: "bible" | "notes"`.
- `label: string` – user-facing name, e.g. `Genesis 1 (KJV)` or `Proverbs Web – January`.
- Bible-board fields (required when `type: "bible"`):
  - `translation: string` – translation code, e.g. `"kjv"`.
  - `book: string` – 3-letter book code, e.g. `"GEN"`, `"JHN"`.
  - `chapter: number` – chapter number.
- `viewState` – canvas/view configuration; v1:
  - `viewState: { panX: number, panY: number, zoom: number }`.
- `items: Item[]` – verse blocks, notes, etc. (see §4).
- `createdAt: string` – ISO timestamp.
- `updatedAt: string` – ISO timestamp.
- Internal field used by the core:
  - `_dirty?: boolean` – if true, considered for persistence.

Verse text is never stored in boards; boards only store references and layout. Verse text is always resolved via Scripture Core and Bible Tools v1 data at render time.

## 4. Item types

`items[]` is a heterogeneous list, keyed by `kind`:

### 4.1 Implemented in v1

- `kind: "verse-block"`
  - `translation: string` – translation code.
  - `book: string` – 3-letter book code.
  - `chapter: number`.
  - `verses: number[]` – one or more verse numbers.
  - `layout: { x: number, y: number, width?: number, height?: number }`.
  - Optional: `style`, `decorations` (reserved for future use).

- `kind: "note"`
  - `text: string` – note content.
  - `layout: { x: number, y: number, width?: number, height?: number }`.
  - Optional: `decorations`.

Any non-`verse-block` item is treated as “user content” for persistence decisions.

### 4.2 Planned

- `kind: "bookmark"`
  - References a verse (`translation/book/chapter/verses[]`) or a board region.
- `kind: "highlight"` / `kind: "section"`
  - Visual or semantic spans tied to verses or canvas regions.

Boards may mix any item kinds.

## 5. Modes, views, and the 2-in-1 workspace

Infinite Bible is a single workspace with two primary modes that share the same underlying boards and items:

### 5.1 Bible mode

- Shows only `type: "bible"` boards.
- Navigator (left sidebar) will list books and chapters for the current translation using Scripture Core’s book metadata.
- Opening a chapter:
  - Uses an `IBT.ensureBibleBoard(translation, bookCode3, chapter)`-style helper to get/create the chapter board.
  - Creates a default empty board in memory if none exists yet for the chapter.
  - The caller is responsible for adding verse-block items for the chapter layout and marking the board dirty.

### 5.2 Boards mode

- Shows only `type: "notes"` boards.
- Navigator lists named boards with affordances to create, rename, duplicate, and archive.
- The active board can contain any mix of verse-blocks and notes and can reference any books/chapters.

### 5.3 Views (filters)

Secondary “views” are filters over the current mode’s boards:

- Notes
- Bookmarks
- Sections
- Highlights

In the current v1 shell, these appear as toolbar buttons; their data views are not yet wired to the board model.

## 6. Persistence rules

All data is stored per-browser via `localStorage`:

- Settings are saved whenever the user changes mode, theme, or sidebar state.
- Boards index is saved via `IBT.saveBoards()`.

Board-level rules:

- Boards are only kept in `IBT_BOARDS_V1` if they contain user content:
  - At least one non-`verse-block` item (note, bookmark, highlight, section), or
  - Later: non-default layout or other signals.
- Opening a Bible chapter with no edits:
  - Creates an in-memory board for that chapter for the session.
  - If the user leaves without adding any notes/highlights/etc., the board is not persisted.
- When saving:
  - Mark the board dirty whenever the user changes items or layout.
  - A save pass:
    - If `hasUserContent(board)` is true, clears `_dirty` and stores the board.
    - Otherwise removes the board from the index and writes the pruned index.

This keeps storage small while preserving every chapter or notes board where the user has actually worked.

## 7. Scripture Core integration

Infinite Bible does not fetch Bible JSON directly. It uses the shared Bible Tools v1 Scripture Core API.

Data and index:

- Index path: `/data/v1/tools/bible-viewer/index.json`.
- Scripture Core configuration:
  - `DEFAULT_DATA_VERSION = "v1"`.
  - `loadIndex(dataVersion?)` loads and caches the index JSON.
  - `getLoadedIndex()` returns the already-loaded index.

Core API used by Infinite Bible:

- `listBooks(translationCode)`  
  Returns `{ code3, title, chapters }[]` for building the book/chapter navigator.
- `getChapter(translationCode, bookCode3, chapterNumber)`  
  Returns a normalized `[{ verse, text }]` array for a chapter.
- `getPassage(translationCode, bookCode3, chapterNumber, versesArray)`  
  Returns only the specified verses.
- `parseReference(input)`  
  Parses human-friendly references like `Proverbs 1:7–9` or `LUK 12:31` into `{ bookCode3, chapter, verses }`.

Boards store only `{ translation, book, chapter, verses[] }`. When rendering a `verse-block`, Infinite Bible calls the Scripture Core functions to obtain `{ verse, text }` for display.

## 8. UI shell and behavior snapshot (current implementation)

Current UI pieces wired in `infinite-bible.html`:

- Header with title, “mode pill” (Bible/Boards), and intro text explaining the 2-in-1 workspace.
- Sticky toolbar with:
  - Navigator toggle (controls the sidebar open/closed state).
  - Primary mode buttons (Bible / Boards).
  - Secondary view buttons (Notes, Bookmarks, Sections, Highlights – UI only for now).
  - Theme toggle (light/dark workspace).
  - “More” and “Help” dropdown stubs.
- Layout:
  - Left sidebar (`Navigator`) whose visibility is tied to the toolbar Navigator button and sidebar-collapsed/visible state.
  - Main workspace area that receives `ib-mode-bible` / `ib-mode-boards` classes for mode-specific styling.
  - Sidebar currently displays placeholder copy indicating that content is still being developed.

Behavior snapshot:

- Mode switching updates:
  - Button styles for Bible vs Boards.
  - Workspace mode classes on the main app container.
  - Mode pill text and description.
  - Stored `lastMode` in settings.
- Theme toggle updates:
  - Workspace theme classes (light/dark).
  - Corresponding `canvasTheme` setting.
- Navigator toggle updates:
  - Sidebar open/closed class on the layout container.
  - Button pressed state.
  - Stored sidebar state in settings.

Not yet implemented:

- Rendering actual chapter text onto the canvas from Scripture Core.
- Creating, editing, and persisting board items (verse-blocks and notes).
- Populating the Navigator with real books/chapters and notes-board lists.
- Wiring the Notes/Bookmarks/Sections/Highlights buttons to filtered views.

These are the main next steps to turn the layout shell into a fully functional v1 Infinite Bible workspace.
