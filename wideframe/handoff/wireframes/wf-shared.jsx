// Shared atoms used by every wireframe variant.
// Exposed on window so multiple babel script files can share them.

const Nav = ({ active = 'Discover' }) => (
  <div className="wf-nav">
    <div className="logo">Storyshelf<span style={{color:'var(--accent)'}}>~</span></div>
    {['Discover', 'Characters', 'My shelf', 'AI'].map(l => (
      <div key={l} className="link" style={{
        fontWeight: l === active ? 700 : 400,
        borderBottom: l === active ? '2px solid var(--ink)' : 'none',
        paddingBottom: 2
      }}>{l}</div>
    ))}
    <div className="spacer" />
    <div className="field" style={{minWidth: 140, fontSize: 13}}>🔍 search a book…</div>
    <div className="pill solid">Alex K.</div>
  </div>
);

const BrowserFrame = ({ url, children }) => (
  <div className="bw">
    <div className="bw-head">
      <div className="bw-dot" />
      <div className="bw-dot" />
      <div className="bw-dot" />
      <div className="bw-url">{url}</div>
    </div>
    <div className="bw-body">{children}</div>
  </div>
);

const Sheet = ({ label, caption, tilt = 'l', children, style }) => (
  <div className={`sheet ${tilt === 'r' ? 'tilt-r' : tilt === '0' ? 'tilt-0' : ''}`} style={style}>
    {label && <div className="sheet-label">{label}</div>}
    {children}
    {caption && <div className="sheet-cap">{caption}</div>}
  </div>
);

const Cover = ({ children, style }) => (
  <div className="cover" style={style}>{children}</div>
);

const Chip = ({ children, acc, dot, style }) => (
  <span className={`chip ${acc ? 'acc' : ''} ${dot ? 'dot' : ''}`} style={style}>{children}</span>
);

const Btn = ({ children, kind = '', full, style }) => (
  <span className={`btn ${kind} ${full ? 'full' : ''}`} style={style}>{children}</span>
);

const Avatar = ({ initials, size = 'md', acc, style }) => (
  <div className={`avatar ${size === 'lg' ? 'lg' : size === 'xl' ? 'xl' : ''} ${acc ? 'acc' : ''}`} style={style}>
    {initials}
  </div>
);

const Line = ({ w = 'full', faint, thin, style }) => (
  <div className={`line ${w} ${faint ? 'faint' : ''} ${thin ? 'thin' : ''}`} style={style} />
);

const Hr = () => <div className="hr" />;

const Annot = ({ children, dir = 'left' }) => (
  <span className="annot">
    {dir === 'left' && <span className="arrow">↰</span>}
    {children}
    {dir === 'right' && <span className="arrow">↱</span>}
    {dir === 'down' && <span className="arrow">↴</span>}
  </span>
);

// Sample book covers (titles only — covers are striped placeholders)
const SAMPLE_BOOKS = [
  { t: 'Dune', a: 'Frank Herbert', g: 'Sci-Fi' },
  { t: 'The Witcher', a: 'A. Sapkowski', g: 'Fantasy' },
  { t: 'Cyberiad', a: 'Stanisław Lem', g: 'Satire' },
  { t: 'Golden Compass', a: 'P. Pullman', g: 'Fantasy' },
  { t: "Handmaid's Tale", a: 'M. Atwood', g: 'Dystopia' },
  { t: 'Interview Vampire', a: 'Anne Rice', g: 'Gothic' },
  { t: '100 Yrs Solitude', a: 'G. G. Márquez', g: 'Lit.' },
  { t: 'Little Prince', a: 'A. de S.-Exupéry', g: 'Classic' },
  { t: 'The Trial', a: 'F. Kafka', g: 'Absurd' },
  { t: 'Catcher in Rye', a: 'J. D. Salinger', g: 'Classic' },
];

// Sample characters for Dune
const DUNE_CHARS = [
  { id: 'paul',  name: 'Paul Atreides', role: 'protagonist',         col: 1 },
  { id: 'leto',  name: 'Leto I',        role: 'father',              col: 2 },
  { id: 'jess',  name: 'Jessica',       role: 'mother, Bene G.',     col: 2 },
  { id: 'chani', name: 'Chani',         role: 'lover',               col: 3 },
  { id: 'stilg', name: 'Stilgar',       role: 'Fremen naib',         col: 3 },
  { id: 'baron', name: 'Baron Harkonnen', role: 'antagonist',        col: 4 },
  { id: 'feyd',  name: 'Feyd-Rautha',   role: 'baron\'s heir',       col: 4 },
  { id: 'gurney',name: 'Gurney Halleck',role: 'master-at-arms',      col: 2 },
];

// Sample relations for Dune (id1, id2, label, kind)
const DUNE_RELS = [
  ['paul', 'leto',   'son',         'family'],
  ['paul', 'jess',   'son',         'family'],
  ['leto', 'jess',   'partners',    'romance'],
  ['paul', 'chani',  'love',        'romance'],
  ['paul', 'stilg',  'ally',        'ally'],
  ['paul', 'gurney', 'mentor',      'ally'],
  ['paul', 'feyd',   'rival/duel',  'enemy'],
  ['paul', 'baron',  'house feud',  'enemy'],
  ['baron','feyd',   'uncle/heir',  'family'],
];

Object.assign(window, {
  Nav, BrowserFrame, Sheet, Cover, Chip, Btn, Avatar, Line, Hr, Annot,
  SAMPLE_BOOKS, DUNE_CHARS, DUNE_RELS,
});
