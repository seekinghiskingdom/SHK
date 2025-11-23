// scripture-core.js
// Shared Scripture Core API for SHK Bible tools (Bible Viewer, Infinite Bible, etc.)
// Content and wording assisted by AI (-AI)

(function (global) {
  "use strict";

  /**
   * Configuration
   */
  var DEFAULT_DATA_VERSION = "v1";
  var INDEX_PATH_TEMPLATE = "/data/{dataVersion}/tools/bible-viewer/index.json";

  /**
   * Internal state
   */
  var indexPromise = null;
  var indexDataVersion = null;
  var indexCache = null;

  /**
   * Book metadata: canonical Protestant order with book code, title, and chapter count.
   * This is used for listBooks and simple UI helpers.
   * If you ever support a different canon, you can branch on translation or dataVersion.
   */
  var BOOKS_META = [
    { code3: "GEN", title: "Genesis", chapters: 50 },
    { code3: "EXO", title: "Exodus", chapters: 40 },
    { code3: "LEV", title: "Leviticus", chapters: 27 },
    { code3: "NUM", title: "Numbers", chapters: 36 },
    { code3: "DEU", title: "Deuteronomy", chapters: 34 },
    { code3: "JOS", title: "Joshua", chapters: 24 },
    { code3: "JDG", title: "Judges", chapters: 21 },
    { code3: "RUT", title: "Ruth", chapters: 4 },
    { code3: "1SA", title: "1 Samuel", chapters: 31 },
    { code3: "2SA", title: "2 Samuel", chapters: 24 },
    { code3: "1KI", title: "1 Kings", chapters: 22 },
    { code3: "2KI", title: "2 Kings", chapters: 25 },
    { code3: "1CH", title: "1 Chronicles", chapters: 29 },
    { code3: "2CH", title: "2 Chronicles", chapters: 36 },
    { code3: "EZR", title: "Ezra", chapters: 10 },
    { code3: "NEH", title: "Nehemiah", chapters: 13 },
    { code3: "EST", title: "Esther", chapters: 10 },
    { code3: "JOB", title: "Job", chapters: 42 },
    { code3: "PSA", title: "Psalms", chapters: 150 },
    { code3: "PRO", title: "Proverbs", chapters: 31 },
    { code3: "ECC", title: "Ecclesiastes", chapters: 12 },
    { code3: "SNG", title: "Song of Solomon", chapters: 8 }, // Song of Songs
    { code3: "ISA", title: "Isaiah", chapters: 66 },
    { code3: "JER", title: "Jeremiah", chapters: 52 },
    { code3: "LAM", title: "Lamentations", chapters: 5 },
    { code3: "EZK", title: "Ezekiel", chapters: 48 },
    { code3: "DAN", title: "Daniel", chapters: 12 },
    { code3: "HOS", title: "Hosea", chapters: 14 },
    { code3: "JOL", title: "Joel", chapters: 3 },
    { code3: "AMO", title: "Amos", chapters: 9 },
    { code3: "OBA", title: "Obadiah", chapters: 1 },
    { code3: "JON", title: "Jonah", chapters: 4 },
    { code3: "MIC", title: "Micah", chapters: 7 },
    { code3: "NAM", title: "Nahum", chapters: 3 },
    { code3: "HAB", title: "Habakkuk", chapters: 3 },
    { code3: "ZEP", title: "Zephaniah", chapters: 3 },
    { code3: "HAG", title: "Haggai", chapters: 2 },
    { code3: "ZEC", title: "Zechariah", chapters: 14 },
    { code3: "MAL", title: "Malachi", chapters: 4 },
    { code3: "MAT", title: "Matthew", chapters: 28 },
    { code3: "MRK", title: "Mark", chapters: 16 },
    { code3: "LUK", title: "Luke", chapters: 24 },
    { code3: "JHN", title: "John", chapters: 21 },
    { code3: "ACT", title: "Acts", chapters: 28 },
    { code3: "ROM", title: "Romans", chapters: 16 },
    { code3: "1CO", title: "1 Corinthians", chapters: 16 },
    { code3: "2CO", title: "2 Corinthians", chapters: 13 },
    { code3: "GAL", title: "Galatians", chapters: 6 },
    { code3: "EPH", title: "Ephesians", chapters: 6 },
    { code3: "PHP", title: "Philippians", chapters: 4 },
    { code3: "COL", title: "Colossians", chapters: 4 },
    { code3: "1TH", title: "1 Thessalonians", chapters: 5 },
    { code3: "2TH", title: "2 Thessalonians", chapters: 3 },
    { code3: "1TI", title: "1 Timothy", chapters: 6 },
    { code3: "2TI", title: "2 Timothy", chapters: 4 },
    { code3: "TIT", title: "Titus", chapters: 3 },
    { code3: "PHM", title: "Philemon", chapters: 1 },
    { code3: "HEB", title: "Hebrews", chapters: 13 },
    { code3: "JAS", title: "James", chapters: 5 },
    { code3: "1PE", title: "1 Peter", chapters: 5 },
    { code3: "2PE", title: "2 Peter", chapters: 3 },
    { code3: "1JN", title: "1 John", chapters: 5 },
    { code3: "2JN", title: "2 John", chapters: 1 },
    { code3: "3JN", title: "3 John", chapters: 1 },
    { code3: "JUD", title: "Jude", chapters: 1 },
    { code3: "REV", title: "Revelation", chapters: 22 }
  ];

  /**
   * Map of normalized book names to 3-letter codes for parseReference.
   * This focuses on full English names and the 3-letter codes; you can add more aliases later.
   */
  var BOOK_NAME_TO_CODE3 = (function buildBookNameLookup() {
    var map = Object.create(null);

    function add(name, code3) {
      map[name.toLowerCase()] = code3;
    }

    BOOKS_META.forEach(function (b) {
      // 3-letter code itself
      add(b.code3, b.code3);

      // Full title (e.g., "Proverbs")
      add(b.title, b.code3);

      // Basic numeric prefixes for numbered books (e.g., "1 Samuel", "2 Samuel").
      if (/^[12]/.test(b.code3) || /^3/.test(b.code3)) {
        // Titles in BOOKS_META already include prefix (e.g., "1 Samuel").
        // You can add more variants if you want (e.g., "First Samuel").
      }
    });

    // Extra common synonyms / variations
    add("psalms", "PSA");
    add("psalm", "PSA");
    add("song of solomon", "SNG");
    add("song of songs", "SNG");
    add("canticles", "SNG");
    add("song", "SNG");

    return map;
  })();

  /**
   * Utility: best-effort base URL detection.
   * You should set window.SHK_BASEURL = '{{ site.baseurl }}' on pages that use this,
   * or provide <meta name="shk-baseurl" content="{{ site.baseurl }}">.
   */
  function getBaseUrl() {
    if (typeof window !== "undefined") {
      if (window.SHK_BASEURL) {
        return window.SHK_BASEURL;
      }
      if (typeof document !== "undefined") {
        var meta = document.querySelector('meta[name="shk-baseurl"]');
        if (meta && meta.content) {
          return meta.content;
        }
        if (document.body && document.body.dataset && document.body.dataset.baseurl) {
          return document.body.dataset.baseurl;
        }
      }
    }
    // Fallback: empty for root
    return "";
  }

  /**
   * Utility: pad a positive integer to 3 digits for chapter filenames.
   */
  function padChapter(chapterNumber) {
    var n = Number(chapterNumber) || 0;
    if (n < 0) n = 0;
    var s = String(n);
    while (s.length < 3) s = "0" + s;
    return s;
  }

  /**
   * Load and cache the index JSON for a given data version.
   * @param {string} [dataVersion="v1"]
   * @returns {Promise<object>} index JSON
   */
  function loadIndex(dataVersion) {
    if (dataVersion === void 0) dataVersion = DEFAULT_DATA_VERSION;

    if (indexPromise && indexDataVersion === dataVersion) {
      return indexPromise;
    }

    indexDataVersion = dataVersion;

    var baseUrl = getBaseUrl();
    var path = INDEX_PATH_TEMPLATE.replace("{dataVersion}", dataVersion);
    var url = baseUrl + path;

    indexPromise = fetch(url, { cache: "no-cache" })
      .then(function (res) {
        if (!res.ok) {
          throw new Error("Failed to load Bible index: " + res.status + " " + res.statusText);
        }
        return res.json();
      })
      .then(function (json) {
        indexCache = json;
        return json;
      });

    return indexPromise;
  }

  /**
   * Get the already-loaded index synchronously.
   * Throws if loadIndex has not completed yet.
   * @returns {object}
   */
  function getLoadedIndex() {
    if (!indexCache) {
      throw new Error("Bible index not loaded. Call loadIndex() first.");
    }
    return indexCache;
  }

  /**
   * Find a translation object by code (e.g., "kjv"), case-insensitive.
   * @param {string} translationCode
   * @returns {object}
   */
  function findTranslation(translationCode) {
    var idx = getLoadedIndex();
    var code = String(translationCode || "").toLowerCase();
    if (!code) {
      throw new Error("translationCode is required");
    }

    var langs = idx.languages || [];
    for (var i = 0; i < langs.length; i++) {
      var tlist = langs[i].translations || [];
      for (var j = 0; j < tlist.length; j++) {
        var t = tlist[j];
        if (String(t.code || "").toLowerCase() === code) {
          return t;
        }
      }
    }

    throw new Error("Translation not found in index: " + translationCode);
  }

  /**
   * List books (code, title, chapter count) for a translation.
   * Currently uses a canonical table; if you support different canons per translation,
   * you can branch on translationCode or dataVersion here.
   * @param {string} translationCode
   * @returns {Array<{ code3: string, title: string, chapters: number }>}
   */
  function listBooks(translationCode) {
    // We call findTranslation() mainly to validate that the translation exists.
    // BOOKS_META is currently canon-agnostic; you can specialize later if needed.
    findTranslation(translationCode);
    return BOOKS_META.slice(); // shallow copy
  }

  /**
   * Build a chapter URL for a given translation and book/chapter.
   * @param {object} translationObj
   * @param {string} bookCode3
   * @param {number} chapterNumber
   * @returns {string}
   */
  function buildChapterUrl(translationObj, bookCode3, chapterNumber) {
    var baseUrl = getBaseUrl();
    var pathRoot = translationObj.path; // e.g., /data/v1/lit/bible/en/kjv
    var chaptersDir = translationObj.chapters_dir || "chapters";
    var chapStr = padChapter(chapterNumber);
    var book = bookCode3;

    if (!pathRoot) {
      throw new Error("Translation object is missing 'path' property.");
    }
    if (!book) {
      throw new Error("bookCode3 is required.");
    }

    var url =
      baseUrl +
      pathRoot +
      "/" +
      chaptersDir +
      "/" +
      book +
      "/" +
      chapStr +
      ".json";

    return url;
  }

  /**
   * Normalize a raw chapter JSON into [{ verse: number, text: string }].
   * Supports the shapes described in the Bible Tools v1 contract.
   * @param {any} raw
   * @returns {Array<{ verse: number, text: string }>}
   */
  function normalizeChapterData(raw) {
    if (!raw) return [];

    var versesArray = [];

    // Case 1: { verses: [ { verse, text }, ... ] }
    if (raw.verses && Array.isArray(raw.verses)) {
      versesArray = raw.verses;
    }
    // Case 2: [ { verse, text }, ... ]
    else if (Array.isArray(raw)) {
      versesArray = raw;
    }
    // Case 3: { "1": "First verse text", "2": "Second verse text", ... }
    else if (typeof raw === "object") {
      var tmp = [];
      Object.keys(raw).forEach(function (k) {
        if (/^\d+$/.test(k)) {
          var vnum = parseInt(k, 10);
          var text = raw[k];
          tmp.push({ verse: vnum, text: String(text == null ? "" : text) });
        }
      });
      if (tmp.length > 0) {
        tmp.sort(function (a, b) {
          return a.verse - b.verse;
        });
        versesArray = tmp;
      }
    }

    // Normalize each verse object to { verse: number, text: string }
    var out = [];

    versesArray.forEach(function (entry) {
      if (entry == null) return;

      var verseNum;
      var text;

      if (typeof entry === "string") {
        // If we only have text and no explicit verse numbers, we can't infer verseNum reliably.
        // In practice, v1 data should provide verse numbers; if not, we skip or set to NaN.
        return;
      } else if (typeof entry === "object") {
        if (typeof entry.verse === "number") {
          verseNum = entry.verse;
        } else if (typeof entry.verse === "string" && /^\d+$/.test(entry.verse)) {
          verseNum = parseInt(entry.verse, 10);
        }

        if (typeof entry.text === "string") {
          text = entry.text;
        } else if (entry.text != null) {
          text = String(entry.text);
        } else if (typeof entry.value === "string") {
          text = entry.value;
        } else {
          // As a last resort, try first string-like property
          var picked = null;
          for (var key in entry) {
            if (Object.prototype.hasOwnProperty.call(entry, key)) {
              var val = entry[key];
              if (typeof val === "string") {
                picked = val;
                break;
              }
            }
          }
          text = picked || "";
        }
      } else {
        return;
      }

      if (typeof verseNum !== "number" || isNaN(verseNum)) {
        return;
      }

      out.push({ verse: verseNum, text: text });
    });

    // Sort by verse number just in case
    out.sort(function (a, b) {
      return a.verse - b.verse;
    });

    return out;
  }

  /**
   * Fetch and normalize a full chapter for a translation / book / chapter.
   * @param {string} translationCode
   * @param {string} bookCode3
   * @param {number} chapterNumber
   * @returns {Promise<Array<{ verse: number, text: string }>>}
   */
  function getChapter(translationCode, bookCode3, chapterNumber) {
    var translation = findTranslation(translationCode);
    var url = buildChapterUrl(translation, bookCode3, chapterNumber);

    return fetch(url, { cache: "no-cache" })
      .then(function (res) {
        if (!res.ok) {
          throw new Error(
            "Failed to load chapter JSON: " +
              url +
              " (" +
              res.status +
              " " +
              res.statusText +
              ")"
          );
        }
        return res.json();
      })
      .then(function (json) {
        return normalizeChapterData(json);
      });
  }

  /**
   * Fetch and normalize a passage (subset of verses within a chapter).
   * If versesArray is empty or omitted, this is equivalent to getChapter.
   * @param {string} translationCode
   * @param {string} bookCode3
   * @param {number} chapterNumber
   * @param {number[]} versesArray
   * @returns {Promise<Array<{ verse: number, text: string }>>}
   */
  function getPassage(translationCode, bookCode3, chapterNumber, versesArray) {
    var versesFilter = Array.isArray(versesArray) ? versesArray.slice() : null;

    return getChapter(translationCode, bookCode3, chapterNumber).then(function (
      verses
    ) {
      if (!versesFilter || versesFilter.length === 0) {
        return verses;
      }

      var set = Object.create(null);
      versesFilter.forEach(function (v) {
        var n = Number(v);
        if (!isNaN(n)) {
          set[n] = true;
        }
      });

      return verses.filter(function (v) {
        return !!set[v.verse];
      });
    });
  }

  /**
   * Parse a human-friendly reference string into { bookCode3, chapter, verses[] }.
   * Supported:
   *   "Proverbs 1"
   *   "Proverbs 1:7"
   *   "Proverbs 1:7-9"
   *   "Proverbs 1:7–9" (en dash)
   *   "LUK 12:31"
   *
   * Returns an object:
   *   { bookCode3: string, chapter: number, verses: number[] | null }
   * Verses will be null if the whole chapter is implied.
   *
   * Throws an Error if parsing fails.
   *
   * @param {string} input
   * @returns {{ bookCode3: string, chapter: number, verses: number[] | null }}
   */
  function parseReference(input) {
    if (!input || typeof input !== "string") {
      throw new Error("Reference input must be a non-empty string.");
    }

    var raw = input.trim();
    if (!raw) {
      throw new Error("Reference input is empty after trimming.");
    }

    // Normalize whitespace and dash types
    raw = raw.replace(/\u2013|\u2014/g, "-"); // en/em dash → hyphen
    raw = raw.replace(/\s+/g, " ");

    // Split book vs the rest (chapter/verses)
    // Pattern: "<book words> <chapter[:verses]>"
    var match = raw.match(/^(.+?)\s+(\d+(?::[\d\-]+)?)$/);
    if (!match) {
      // Try case where user supplies only book code and chapter, e.g. "PRO 1"
      match = raw.match(/^([1-3]?\s*[A-Za-z]+)\s+(\d+(?::[\d\-]+)?)$/);
      if (!match) {
        throw new Error("Could not parse reference: \"" + input + "\"");
      }
    }

    var bookPart = match[1].trim();
    var chapVersPart = match[2].trim();

    var normalizedBookKey = bookPart.toLowerCase();

    // Try direct lookup
    var bookCode3 = BOOK_NAME_TO_CODE3[normalizedBookKey];
    if (!bookCode3) {
      // Try removing spaces in things like "1 Samuel" → "1samuel"
      var collapsed = normalizedBookKey.replace(/\s+/g, "");
      bookCode3 = BOOK_NAME_TO_CODE3[collapsed];
    }
    if (!bookCode3) {
      throw new Error("Unknown book in reference: \"" + bookPart + "\"");
    }

    // Parse chapter and optional verses
    var chapter = null;
    var verses = null;

    if (chapVersPart.indexOf(":") === -1) {
      // Only chapter
      chapter = parseInt(chapVersPart, 10);
      if (isNaN(chapter) || chapter <= 0) {
        throw new Error("Invalid chapter in reference: \"" + chapVersPart + "\"");
      }
      verses = null; // full chapter
    } else {
      var parts = chapVersPart.split(":");
      if (parts.length !== 2) {
        throw new Error("Invalid chapter/verse portion: \"" + chapVersPart + "\"");
      }
      var chapStr = parts[0];
      var versePart = parts[1];

      chapter = parseInt(chapStr, 10);
      if (isNaN(chapter) || chapter <= 0) {
        throw new Error("Invalid chapter in reference: \"" + chapStr + "\"");
      }

      // Could be "7" or "7-9"
      var rangeParts = versePart.split("-");
      var startVerse = parseInt(rangeParts[0], 10);
      if (isNaN(startVerse) || startVerse <= 0) {
        throw new Error("Invalid verse in reference: \"" + versePart + "\"");
      }

      if (rangeParts.length === 1) {
        verses = [startVerse];
      } else if (rangeParts.length === 2) {
        var endVerse = parseInt(rangeParts[1], 10);
        if (isNaN(endVerse) || endVerse < startVerse) {
          throw new Error("Invalid verse range in reference: \"" + versePart + "\"");
        }
        verses = [];
        for (var v = startVerse; v <= endVerse; v++) {
          verses.push(v);
        }
      } else {
        throw new Error("Invalid verse range format: \"" + versePart + "\"");
      }
    }

    return {
      bookCode3: bookCode3,
      chapter: chapter,
      verses: verses
    };
  }

  /**
   * Public API
   */
  var ScriptureCore = {
    // Core
    loadIndex: loadIndex,
    getLoadedIndex: getLoadedIndex,
    findTranslation: findTranslation,

    // Books / metadata
    listBooks: listBooks,

    // Scripture retrieval
    getChapter: getChapter,
    getPassage: getPassage,

    // Reference parsing
    parseReference: parseReference,

    // Expose metadata + helpers for advanced uses if needed
    _BOOKS_META: BOOKS_META,
    _BOOK_NAME_TO_CODE3: BOOK_NAME_TO_CODE3,
    _getBaseUrl: getBaseUrl,
    _buildChapterUrl: buildChapterUrl,
    _normalizeChapterData: normalizeChapterData
  };

  // Attach to global
  if (typeof module !== "undefined" && module.exports) {
    module.exports = ScriptureCore;
  } else {
    global.ScriptureCore = ScriptureCore;
  }
})(typeof window !== "undefined" ? window : this);
