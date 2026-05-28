// Top-level app: tab switcher + Tweaks panel.
const { useState } = React;

const VARIANTS = [
  { k: 'A', name: 'Classic + AI panel',     C: window.VariantA },
  { k: 'B', name: 'Graph-first',            C: window.VariantB },
  { k: 'C', name: 'AI Companion (chat)',    C: window.VariantC },
  { k: 'D', name: 'Character-first',        C: window.VariantD },
  { k: 'E', name: 'Reader + marginalia',    C: window.VariantE },
];

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "amber",
  "weight": "normal",
  "showAll": false,
  "activeTab": 1
}/*EDITMODE-END*/;

const accentClass = {
  amber: 'acc-amber',
  blue:  'acc-blue',
  green: 'acc-green',
  rose:  'acc-rose',
  brick: ''
};

const App = () => {
  const { TweaksPanel, useTweaks, TweakRadio, TweakToggle } = window;
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const active = t.activeTab ?? 0;

  const rootCls = [
    'app',
    accentClass[t.accent] || '',
    t.weight === 'heavy' ? 'heavy' : ''
  ].join(' ');

  return (
    <div className={rootCls}>
      <div className="topbar">
        <div className="brand">
          Storyshelf<span style={{color:'var(--accent)'}}>~</span>
          <small>WIREFRAMES · 5 DIRECTIONS · v2</small>
        </div>
        <div className="meta">
          A Goodreads clone with LLM features: pulling characters and relations out of books.
          Each direction shows <b>2 key screens + a profile/settings sheet</b>. Toggle "show all"
          in Tweaks to see everything on one long page.
        </div>
      </div>

      {!t.showAll && (
        <div className="tabs">
          {VARIANTS.map((v, i) => (
            <button key={v.k}
              className={`tab ${i === active ? 'active' : ''}`}
              onClick={() => setTweak('activeTab', i)}>
              <span className="k">{v.k}</span>{v.name}
            </button>
          ))}
        </div>
      )}

      {t.showAll
        ? VARIANTS.map((v) => (
            <div key={v.k} style={{marginBottom: 60}}>
              <v.C />
            </div>
          ))
        : React.createElement(VARIANTS[active].C)
      }

      {/* Shared Settings sheet — same for every variant */}
      <div style={{marginTop: 30}}>
        <div className="variant-head">
          <h2>Settings · shared across all variants</h2>
          <div className="why">
            Account, security, and profile-visibility controls live in one place — independent of
            which UI direction wins. Each variant's own profile page hosts the <b>variant-specific</b>
            settings (AI persona, graph privacy, club preferences, etc.).
          </div>
        </div>

        <window.Sheet label="04 · Settings" caption="account · password · email · username · avatar · public/private" tilt="0">
          <window.SettingsScreen />
        </window.Sheet>
      </div>

      <TweaksPanel title="Tweaks">
        <div style={{fontFamily:'Patrick Hand', fontSize:13, color:'#666', marginBottom: 6, letterSpacing:1}}>
          ACCENT COLOR
        </div>
        <div style={{display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:8, marginBottom: 14}}>
          {[
            ['amber', '#c47a14'],
            ['brick', '#d94f1e'],
            ['rose',  '#c8417a'],
            ['green', '#1f8a5b'],
            ['blue',  '#2a6fdb'],
          ].map(([k, c]) => (
            <button key={k}
              onClick={() => setTweak('accent', k)}
              style={{
                border: t.accent === k ? '2.5px solid #000' : '1.5px solid #999',
                background: c, height: 32, borderRadius: 8, cursor:'pointer'
              }}
              title={k} />
          ))}
        </div>

        <TweakRadio
          label="Line weight"
          value={t.weight}
          onChange={(v) => setTweak('weight', v)}
          options={['normal', 'heavy']}
        />

        <TweakToggle
          label="Show all variants stacked"
          value={t.showAll}
          onChange={(v) => setTweak('showAll', v)}
        />
      </TweaksPanel>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
