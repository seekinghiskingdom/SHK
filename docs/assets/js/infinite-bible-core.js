// Infinite Bible core (boards + settings, unified Bible/Boards model)
// Content and wording assisted by AI (-AI)
(function (window) {
  "use strict";

  var STORAGE_KEYS = {
    settings: "IBT_SETTINGS_V1",
    boards: "IBT_BOARDS_V1"
  };

  var DEFAULT_SETTINGS = {
    schemaVersion: 1,
    lastMode: "bible",     // "bible" | "notes"
    lastBoardId: null,     // e.g. "bible:kjv:GEN:1" or "notes:proverbs-web"
    canvasTheme: "light",  // "light" | "dark"
    sidebarCollapsed: false
  };

  function safeParseJSON(raw, fallback) {
    if (!raw) return fallback;
    try {
      return JSON.parse(raw);
    } catch (e) {
      console.warn("[IBT] Failed to parse JSON from localStorage:", e);
      return fallback;
    }
  }

  function loadSettings() {
    var raw = window.localStorage.getItem(STORAGE_KEYS.settings);
    var data = safeParseJSON(raw, null);
    if (!data || typeof data !== "object") return Object.assign({}, DEFAULT_SETTINGS);
    // Shallow merge with defaults in case we add new fields later
    return Object.assign({}, DEFAULT_SETTINGS, data);
  }

  function saveSettings(settings) {
    try {
      window.localStorage.setItem(
        STORAGE_KEYS.settings,
        JSON.stringify(settings)
      );
    } catch (e) {
      console.warn("[IBT] Failed to save settings:", e);
    }
  }

  function loadBoardsIndex() {
    var raw = window.localStorage.getItem(STORAGE_KEYS.boards);
    var data = safeParseJSON(raw, null);
    if (!data || typeof data !== "object" || !data.boards) {
      return { schemaVersion: 1, boards: {} };
    }
    if (!data.schemaVersion) data.schemaVersion = 1;
    if (!data.boards || typeof data.boards !== "object") data.boards = {};
    return data;
  }

  function saveBoardsIndex(index) {
    try {
      window.localStorage.setItem(
        STORAGE_KEYS.boards,
        JSON.stringify(index)
      );
    } catch (e) {
      console.warn("[IBT] Failed to save boards index:", e);
    }
  }

  function makeBibleBoardId(translation, bookCode3, chapterNumber) {
    return "bible:" + translation + ":" + bookCode3 + ":" + String(chapterNumber);
  }

  function createEmptyBibleBoard(opts) {
    var now = new Date().toISOString();
    return {
      id: opts.id,
      type: "bible",
      label: opts.label || (opts.bookCode3 + " " + opts.chapter + " (" + opts.translation.toUpperCase() + ")"),
      translation: opts.translation,
      book: opts.bookCode3,
      chapter: opts.chapter,
      createdAt: now,
      updatedAt: now,
      viewState: {
        panX: 0,
        panY: 0,
        zoom: 1
      },
      items: [],
      _dirty: false
    };
  }

  function hasUserContent(board) {
    if (!board || !Array.isArray(board.items)) return false;
    // v1 policy: only verse-blocks are considered "automatic".
    // Any non-verse-block item (note, bookmark, highlight, section, etc.)
    // counts as user content and should cause persistence.
    return board.items.some(function (item) {
      return item && item.kind && item.kind !== "verse-block";
    });
  }

  var IBT = {
    settings: loadSettings(),
    boardsIndex: loadBoardsIndex(),

    saveSettings: function () {
      saveSettings(this.settings);
    },

    saveBoards: function () {
      saveBoardsIndex(this.boardsIndex);
    },

    getBoard: function (boardId) {
      return this.boardsIndex.boards[boardId] || null;
    },

    /**
     * Returns a bible board from memory if it exists; otherwise creates
     * a new in-memory board with no items. The caller decides when to
     * populate it with verse blocks and when to persist.
     */
    ensureBibleBoard: function (translation, bookCode3, chapterNumber) {
      var id = makeBibleBoardId(translation, bookCode3, chapterNumber);
      var existing = this.boardsIndex.boards[id];
      if (existing) return existing;

      var board = createEmptyBibleBoard({
        id: id,
        translation: translation,
        bookCode3: bookCode3,
        chapter: chapterNumber
      });

      // Do NOT persist yet; caller should mark dirty and save when appropriate
      this.boardsIndex.boards[id] = board;
      return board;
    },

    /**
     * Marks a board as dirty so it will be considered for persistence.
     */
    markBoardDirty: function (board) {
      if (!board) return;
      board._dirty = true;
      board.updatedAt = new Date().toISOString();
    },

    /**
     * Persists a single board if it has user content.
     * If the board has no user content, it is removed from storage.
     */
    saveBoardIfNeeded: function (board) {
      if (!board) return;
      var id = board.id;
      if (!id) return;

      if (hasUserContent(board)) {
        delete board._dirty;
        this.boardsIndex.boards[id] = board;
      } else {
        // No user content: do not keep it in persistent storage
        delete this.boardsIndex.boards[id];
      }
      this.saveBoards();
    },

    /**
     * Convenience: set last mode + board and persist settings.
     */
    setLastContext: function (mode, boardId) {
      this.settings.lastMode = mode;
      this.settings.lastBoardId = boardId || null;
      this.saveSettings();
    }
  };

  window.IBT = IBT;
})(window);
