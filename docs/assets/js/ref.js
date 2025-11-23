export const BOOKS = [
['Genesis', ['Gen','Ge','Gn']], ['Exodus', ['Exod','Ex','Exo']], ['Leviticus', ['Lev','Lv']],
['Numbers', ['Num','Nm','Nb']], ['Deuteronomy', ['Deut','Dt','Deu']], ['Joshua', ['Josh','Jos']],
['Judges', ['Judg','Jdg']], ['Ruth', ['Rth','Ru']], ['1 Samuel', ['1Sam','1 Sa','1Sm','I Sam','1Samuel']],
['2 Samuel', ['2Sam','2 Sa','2Sm','II Sam','2Samuel']], ['1 Kings', ['1Kgs','1Ki','I Kgs']],
['2 Kings', ['2Kgs','2Ki','II Kgs']], ['1 Chronicles', ['1Chr','1Ch']], ['2 Chronicles', ['2Chr','2Ch']],
['Ezra', ['Ezr']], ['Nehemiah', ['Neh','Ne']], ['Esther', ['Est','Es']], ['Job', ['Jb']],
['Psalms', ['Ps','Psa','Psm','Pss']], ['Proverbs', ['Prov','Pr','Prv']], ['Ecclesiastes', ['Eccl','Ecc','Qoheleth']],
['Song of Solomon', ['Song','Sng','Cant']], ['Isaiah', ['Isa','Is']], ['Jeremiah', ['Jer','Je','Jr']],
['Lamentations', ['Lam','La']], ['Ezekiel', ['Ezek','Eze','Ez']], ['Daniel', ['Dan','Da','Dn']],
['Hosea', ['Hos','Ho']], ['Joel', ['Jl','Joe']], ['Amos', ['Am']], ['Obadiah', ['Obad','Ob']],
['Jonah', ['Jon','Jnh']], ['Micah', ['Mic','Mc']], ['Nahum', ['Nah','Na']], ['Habakkuk', ['Hab','Hb']],
['Zephaniah', ['Zeph','Zep','Zp']], ['Haggai', ['Hag','Hg']], ['Zechariah', ['Zech','Zec','Zc']], ['Malachi', ['Mal','Ml']],
['Matthew', ['Matt','Mt','Mat']], ['Mark', ['Mrk','Mk','Mr']], ['Luke', ['Lk','Lu']], ['John', ['Jn','Jhn']],
['Acts', ['Ac']], ['Romans', ['Rom','Ro','Rm']], ['1 Corinthians', ['1Cor','1 Co','I Cor']],
['2 Corinthians', ['2Cor','2 Co','II Cor']], ['Galatians', ['Gal','Ga']], ['Ephesians', ['Eph','Ephes','Ep']],
['Philippians', ['Phil','Php','Pp']], ['Colossians', ['Col','Co']], ['1 Thessalonians', ['1Thess','1 Th','I Thes']],
['2 Thessalonians', ['2Thess','2 Th','II Thes']], ['1 Timothy', ['1Tim','1 Ti','I Tim']],
['2 Timothy', ['2Tim','2 Ti','II Tim']], ['Titus', ['Tit','Ti']], ['Philemon', ['Phlm','Phm','Pm']],
['Hebrews', ['Heb','He']], ['James', ['Jas','Jm']], ['1 Peter', ['1Pet','1 Pe','I Pet']],
['2 Peter', ['2Pet','2 Pe','II Pet']], ['1 John', ['1Jn','1 Jn','I Jn']], ['2 John', ['2Jn','2 Jn','II Jn']],
['3 John', ['3Jn','3 Jn','III Jn']], ['Jude', ['Jud']], ['Revelation', ['Rev','Re','Apocalypse']]
];


const BOOK_MAP = (() => {
const m = new Map();
for (const [name, alts] of BOOKS) { m.set(name.toLowerCase(), name); for (const a of alts) m.set(a.toLowerCase(), name); }
return m;
})();


export function parseRef(input){
const s = input.trim().replace(/\s+/g,' ');
const m = s.match(/^(.*?)(\s+)([0-9].*)$/) || [null, s, '', ''];
let bookPart = m[1].trim();
let rest = m[3].trim();
const bk = BOOK_MAP.get(bookPart.toLowerCase()) || BOOK_MAP.get(bookPart.replace(/\./g,'').toLowerCase());
const book = bk || null; if (!book) return null;
if (!rest) return { book, chapter: 1, verses: null };
const chapVerse = rest.split(':');
const chapter = parseInt(chapVerse[0], 10); if (!Number.isFinite(chapter)) return null;
let verses = null;
if (chapVerse[1]) {
const v = chapVerse[1].split('-').map(t => parseInt(t,10));
if (v.length === 1 && Number.isFinite(v[0])) verses = [v[0], v[0]];
else if (v.length === 2 && Number.isFinite(v[0]) && Number.isFinite(v[1])) verses = [v[0], v[1]];
else return null;
}
return { book, chapter, verses };
}