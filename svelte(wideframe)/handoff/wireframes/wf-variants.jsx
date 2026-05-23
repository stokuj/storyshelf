// === Variant A: Classic catalog + AI side panel ==============================
const VariantA = () => (
  <>
    <div className="variant-head">
      <h2>A. Classic + AI side panel</h2>
      <div className="why">
        Smallest change from today's Goodreads pattern. <b>Book list and book page stay</b> —
        but the right rail of the book page hosts a "Meet the cast" panel that, on demand,
        extracts characters, relations, and short bios. Easy adoption for existing users.
      </div>
    </div>

    <div className="grid cols-2">
      <Sheet label="01 · Catalog" caption="grid of cards + a new 'contains character' filter">
        <BrowserFrame url="storyshelf.app/discover">
          <Nav active="Discover" />
          <div className="row" style={{justifyContent:'space-between', marginBottom: 10}}>
            <div style={{fontFamily:'Caveat', fontSize: 28, fontWeight:700}}>Discover books <span style={{color:'var(--muted)', fontSize:16}}>· 1,248 titles</span></div>
            <div className="row">
              <Chip>Genre ▾</Chip>
              <Chip>Sort ▾</Chip>
              <Chip acc>✨ Filter: contains character…</Chip>
            </div>
          </div>

          <div className="catalog-grid">
            {SAMPLE_BOOKS.slice(0, 10).map((b, i) => (
              <div className="book" key={i}>
                <Cover>{b.t}</Cover>
                <div className="t">{b.t}</div>
                <div className="a">{b.a}</div>
                <div style={{marginTop:4}}><Chip>{b.g}</Chip></div>
              </div>
            ))}
          </div>

          <div className="annotation-row">
            <span className="lead">new ↗</span>
            <div style={{fontSize:15, color:'var(--ink-2)'}}>
              the "<b>contains character</b>" filter finds every book featuring Sherlock, Frodo, etc. —
              fed by the model's extracted index.
            </div>
          </div>
        </BrowserFrame>
      </Sheet>

      <Sheet label="02 · Book page + AI panel" caption="right rail expands on demand" tilt="r">
        <BrowserFrame url="storyshelf.app/book/dune">
          <Nav active="Discover" />
          <div style={{display:'grid', gridTemplateColumns:'140px 1fr 220px', gap: 14, alignItems:'flex-start'}}>
            <div>
              <Cover style={{aspectRatio:'2/3'}}>Dune</Cover>
              <div style={{marginTop:8}}><Btn full>Want to read ▾</Btn></div>
              <div style={{marginTop:6, fontSize:13, color:'var(--muted)', textAlign:'center'}}>★ 4.7 · 891,200 ratings</div>
            </div>
            <div>
              <div style={{fontFamily:'Caveat', fontSize:34, fontWeight:700, lineHeight:1}}>Dune</div>
              <div style={{color:'var(--muted)', marginBottom:6}}>Frank Herbert · 1965</div>
              <div className="row" style={{gap:6}}>
                <Chip>Sci-Fi</Chip><Chip>Space Opera</Chip><Chip>#classics</Chip>
              </div>
              <Hr />
              <div style={{fontFamily:'Patrick Hand', fontSize:13, letterSpacing:1, color:'var(--muted)'}}>SUMMARY</div>
              <Line w="full" /><Line w="full" /><Line w="long" /><Line w="mid" />
              <Hr />
              <div className="row" style={{justifyContent:'space-between'}}>
                <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Reviews · 218</div>
                <Chip>write a review</Chip>
              </div>
              <div className="card" style={{marginTop:6}}>
                <div className="row"><Avatar initials="MK" /><div><b style={{fontFamily:'Caveat', fontSize:18}}>Martha K.</b> <span style={{color:'var(--muted)'}}>★★★★★</span></div></div>
                <Line w="long" /><Line w="mid" thin />
              </div>
            </div>

            {/* AI panel */}
            <div style={{
              border:'2.5px dashed var(--accent)', borderRadius: 12,
              padding: 10, background: '#fffaf2'
            }}>
              <div className="row" style={{justifyContent:'space-between', marginBottom: 6}}>
                <div style={{fontFamily:'Caveat', fontWeight:700, fontSize:20, color:'var(--accent)'}}>✨ Meet the cast</div>
                <div style={{fontSize:11, color:'var(--muted)'}}>AI</div>
              </div>
              <div style={{fontSize:13, color:'var(--ink-2)', marginBottom: 8}}>
                We'll extract 8–20 characters and the relations between them.
              </div>
              <Btn kind="acc" full>Generate ✨</Btn>

              <Hr />
              <div style={{fontFamily:'Patrick Hand', fontSize:13, letterSpacing:1, color:'var(--muted)'}}>PREVIEW</div>
              <div className="stack-tight" style={{marginTop: 6}}>
                {DUNE_CHARS.slice(0,5).map(c => (
                  <div key={c.id} className="row" style={{gap:8}}>
                    <Avatar initials={c.name.split(' ').map(w=>w[0]).join('').slice(0,2)} />
                    <div className="stack-tight" style={{gap:0}}>
                      <div style={{fontSize:14, fontWeight:700}}>{c.name}</div>
                      <div style={{fontSize:12, color:'var(--muted)'}}>{c.role}</div>
                    </div>
                  </div>
                ))}
                <div style={{fontSize:13, color:'var(--muted)', textAlign:'center', marginTop:4}}>+3 more</div>
              </div>
              <Hr />
              <div className="row" style={{gap:6, flexWrap:'wrap'}}>
                <Chip dot>📊 Relation graph</Chip>
                <Chip dot>📝 Spoiler-safe summary</Chip>
                <Chip dot>💬 Ask about this book</Chip>
              </div>
            </div>
          </div>
        </BrowserFrame>
      </Sheet>
    </div>

    {/* Profile sheet */}
    <div style={{marginTop: 22}}>
      <Sheet label="03 · Profile" caption="classic Goodreads-style profile + AI history block" tilt="0">
        <BrowserFrame url="storyshelf.app/u/alex-k">
          <Nav />
          <div style={{display:'grid', gridTemplateColumns:'220px 1fr 240px', gap: 18, alignItems:'flex-start'}}>
            {/* left: avatar + bio */}
            <div className="col" style={{alignItems:'center', textAlign:'center'}}>
              <Avatar initials="AK" size="xl" acc />
              <div style={{fontFamily:'Caveat', fontSize:28, fontWeight:700, marginTop:6, lineHeight:1}}>Alex Kowalski</div>
              <div style={{color:'var(--muted)', fontSize:13}}>@alex-k · joined Mar 2024</div>
              <Line w="long" /><Line w="mid" thin />
              <div className="row" style={{gap:6, marginTop:6, justifyContent:'center', flexWrap:'wrap'}}>
                <Chip>sci-fi</Chip><Chip>literary</Chip><Chip>memoir</Chip>
              </div>
              <Hr />
              <div className="row" style={{gap: 18, justifyContent:'center'}}>
                <div><b style={{fontSize:18}}>148</b><div style={{fontSize:12, color:'var(--muted)'}}>read</div></div>
                <div><b style={{fontSize:18}}>23</b><div style={{fontSize:12, color:'var(--muted)'}}>reviews</div></div>
                <div><b style={{fontSize:18}}>2.1k</b><div style={{fontSize:12, color:'var(--muted)'}}>followers</div></div>
              </div>
            </div>

            {/* middle: shelves + activity */}
            <div>
              <div style={{fontFamily:'Caveat', fontSize: 22, fontWeight:700}}>2026 reading challenge</div>
              <div style={{
                height: 10, border:'1.5px solid var(--rule)', borderRadius:999,
                overflow:'hidden', marginTop:4, background:'#fff'
              }}>
                <div style={{width:'62%', height:'100%', background:'var(--accent)'}}/>
              </div>
              <div style={{fontSize:13, color:'var(--muted)', marginTop:3}}>31 / 50 books · on track</div>

              <Hr />

              <div className="row" style={{justifyContent:'space-between'}}>
                <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Recently read</div>
                <Chip>see all</Chip>
              </div>
              <div className="row" style={{gap:8, marginTop: 6}}>
                {SAMPLE_BOOKS.slice(0,6).map((b,i)=>(
                  <div key={i} style={{flex:1}}>
                    <Cover style={{aspectRatio:'2/3'}}>{b.t}</Cover>
                    <div style={{fontSize:11, marginTop:3, color:'var(--muted)', textAlign:'center'}}>★★★★☆</div>
                  </div>
                ))}
              </div>

              <Hr />

              <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Activity</div>
              <div className="stack-tight" style={{gap:6, marginTop:4}}>
                <div className="card">
                  <div style={{fontSize:14}}><b>Alex</b> rated <b>Dune Messiah</b> ★★★★★</div>
                  <div style={{fontSize:12, color:'var(--muted)'}}>2 days ago</div>
                </div>
                <div className="card">
                  <div style={{fontSize:14}}><b>Alex</b> wrote a review of <b>The Trial</b></div>
                  <Line w="long" /><Line w="mid" thin />
                  <div style={{fontSize:12, color:'var(--muted)'}}>5 days ago</div>
                </div>
              </div>
            </div>

            {/* right: AI sidecar */}
            <div style={{
              border:'2.5px dashed var(--accent)', borderRadius: 12,
              padding: 10, background: '#fffaf2'
            }}>
              <div style={{fontFamily:'Caveat', fontWeight:700, fontSize:20, color:'var(--accent)'}}>✨ Your AI history</div>
              <div style={{fontSize:13, color:'var(--ink-2)', marginBottom: 8}}>
                28 extractions · 14 conversations
              </div>
              <div className="stack-tight" style={{gap:4}}>
                <div className="card" style={{padding:'6px 8px'}}>
                  <div style={{fontSize:13}}><b>Dune</b> · cast extracted</div>
                  <div style={{fontSize:11, color:'var(--muted)'}}>23 chars · today</div>
                </div>
                <div className="card" style={{padding:'6px 8px'}}>
                  <div style={{fontSize:13}}><b>1984</b> · relations map</div>
                  <div style={{fontSize:11, color:'var(--muted)'}}>11 chars · 3 days</div>
                </div>
                <div className="card" style={{padding:'6px 8px'}}>
                  <div style={{fontSize:13}}><b>The Trial</b> · chat (12 msgs)</div>
                  <div style={{fontSize:11, color:'var(--muted)'}}>1 week</div>
                </div>
              </div>
              <Hr />
              <div style={{fontFamily:'Patrick Hand', fontSize:13, letterSpacing:1, color:'var(--muted)'}}>SETTINGS</div>
              <div className="stack-tight" style={{gap:4, marginTop:4}}>
                <div className="row" style={{justifyContent:'space-between', fontSize:13}}>
                  <span>auto-extract on add</span>
                  <Chip>on</Chip>
                </div>
                <div className="row" style={{justifyContent:'space-between', fontSize:13}}>
                  <span>spoiler shield</span>
                  <Chip acc>strict</Chip>
                </div>
                <div className="row" style={{justifyContent:'space-between', fontSize:13}}>
                  <span>share extractions</span>
                  <Chip>off</Chip>
                </div>
              </div>
              <Hr />
              <Btn kind="ghost" full>Manage AI settings →</Btn>
            </div>
          </div>
        </BrowserFrame>
      </Sheet>
    </div>

    <div className="footnote">
      <span className="label">NOTES</span>
      <div>
        Low risk, fast to ship. AI is opt-in — the user clicks "Generate" and can accept/reject
        characters, so the database grows with humans in the loop. Downside: AI gets visually lost
        next to the classic layout.
      </div>
    </div>
  </>
);

// === Variant B: Graph-first ==================================================
const Graph = () => {
  const cx = 240, cy = 200, R = 150;
  const nodes = DUNE_CHARS.map((c, i) => {
    const a = (i / DUNE_CHARS.length) * Math.PI * 2 - Math.PI / 2;
    return { ...c, x: cx + Math.cos(a) * R, y: cy + Math.sin(a) * R };
  });
  const byId = Object.fromEntries(nodes.map(n => [n.id, n]));
  const kindColor = { family: '#2a6fdb', romance: '#c8417a', ally: '#1f8a5b', enemy: '#d94f1e' };
  return (
    <svg viewBox="0 0 480 400">
      {DUNE_RELS.map(([a, b, label, kind], i) => {
        const A = byId[a], B = byId[b];
        return (
          <line key={i} x1={A.x} y1={A.y} x2={B.x} y2={B.y}
            stroke={kindColor[kind]} strokeWidth="2"
            strokeDasharray={kind === 'enemy' ? '5 4' : '0'}
            opacity="0.85" />
        );
      })}
      {nodes.map(n => (
        <g key={n.id}>
          <circle cx={n.x} cy={n.y} r={n.id === 'paul' ? 26 : 20}
            fill={n.id === 'paul' ? 'var(--accent)' : '#fffdf7'}
            stroke="var(--rule)" strokeWidth="2.2" />
          <text x={n.x} y={n.y + 4} textAnchor="middle"
            fontFamily="Caveat" fontSize={n.id === 'paul' ? 18 : 15}
            fontWeight="700"
            fill={n.id === 'paul' ? '#fffdf7' : 'var(--ink)'}>
            {n.name.split(' ').map(w => w[0]).join('').slice(0,2)}
          </text>
          <text x={n.x} y={n.y + (n.id === 'paul' ? 44 : 36)} textAnchor="middle"
            fontFamily="Patrick Hand" fontSize="12" fill="var(--ink-2)">
            {n.name.split(' ')[0]}
          </text>
        </g>
      ))}
    </svg>
  );
};

// Personal graph for profile — books and characters as a galaxy
const PersonalGraph = () => {
  // 3 book clusters with their characters
  const clusters = [
    { id: 'dune',    x: 120, y: 90,  label: 'Dune',         chars: ['Paul','Chani','Leto','Jess'], color: '#c47a14' },
    { id: 'sherlock',x: 320, y: 110, label: 'Sherlock H.',  chars: ['Holmes','Watson','Moriarty'], color: '#2a6fdb' },
    { id: 'handmaid',x: 220, y: 260, label: "Handmaid's T.",chars: ['Offred','Serena','Nick'],     color: '#c8417a' },
  ];
  const nodes = [];
  clusters.forEach(c => {
    c.chars.forEach((name, i) => {
      const angle = (i / c.chars.length) * Math.PI * 2;
      nodes.push({
        x: c.x + Math.cos(angle) * 42,
        y: c.y + Math.sin(angle) * 42,
        name, parent: c
      });
    });
  });
  // cross-book bridge (same archetype)
  const bridges = [
    ['Paul', 'Offred'], // both protagonists in dystopian-ish
    ['Holmes', 'Paul'], // both followed by user
  ];
  const find = n => nodes.find(x => x.name === n);

  return (
    <svg viewBox="0 0 440 360">
      {/* book hub circles */}
      {clusters.map(c => (
        <g key={c.id}>
          <circle cx={c.x} cy={c.y} r="50" fill="none" stroke={c.color}
            strokeWidth="1.5" strokeDasharray="3 3" opacity="0.5"/>
          <text x={c.x} y={c.y - 56} textAnchor="middle"
            fontFamily="Caveat" fontWeight="700" fontSize="14" fill="var(--ink-2)">
            {c.label}
          </text>
        </g>
      ))}
      {/* bridges */}
      {bridges.map(([a,b], i) => {
        const A = find(a), B = find(b);
        if (!A || !B) return null;
        return <line key={i} x1={A.x} y1={A.y} x2={B.x} y2={B.y}
          stroke="var(--accent)" strokeWidth="2.5" strokeDasharray="6 4" opacity="0.7"/>;
      })}
      {/* lines from hub to nodes */}
      {nodes.map((n, i) => (
        <line key={i} x1={n.parent.x} y1={n.parent.y} x2={n.x} y2={n.y}
          stroke={n.parent.color} strokeWidth="1.5" opacity="0.5"/>
      ))}
      {/* nodes */}
      {nodes.map((n, i) => (
        <g key={i}>
          <circle cx={n.x} cy={n.y} r="14" fill="#fffdf7"
            stroke={n.parent.color} strokeWidth="2"/>
          <text x={n.x} y={n.y + 4} textAnchor="middle"
            fontFamily="Caveat" fontWeight="700" fontSize="11" fill="var(--ink)">
            {n.name.slice(0,2)}
          </text>
          <text x={n.x} y={n.y + 26} textAnchor="middle"
            fontFamily="Patrick Hand" fontSize="10" fill="var(--ink-2)">
            {n.name}
          </text>
        </g>
      ))}
    </svg>
  );
};

const VariantB = () => (
  <>
    <div className="variant-head">
      <h2>B. Graph-first</h2>
      <div className="why">
        The book page is rebuilt around the <b>character-relation graph as the hero</b>. Summary
        and reviews hide behind tabs; the first thing you see is the network you can filter
        (family / enemies / romance), and clicking a node opens the character page.
      </div>
    </div>

    <div className="grid cols-2">
      <Sheet label="01 · Book page / GRAPH" caption="hero = graph, summary moved to a tab">
        <BrowserFrame url="storyshelf.app/book/dune">
          <Nav active="Discover" />
          <div className="row" style={{gap: 14, marginBottom: 8, alignItems:'flex-start'}}>
            <Cover style={{width: 84, flexShrink: 0}}>Dune</Cover>
            <div style={{flex:1}}>
              <div style={{fontFamily:'Caveat', fontSize:30, fontWeight:700, lineHeight:1}}>Dune</div>
              <div style={{color:'var(--muted)'}}>Frank Herbert · ★ 4.7</div>
              <div className="row" style={{gap:6, marginTop:6}}>
                <Chip>Sci-Fi</Chip><Chip>Space Opera</Chip>
              </div>
            </div>
            <div className="col" style={{alignItems:'flex-end'}}>
              <Btn kind="primary">+ Shelf</Btn>
              <Btn kind="ghost" style={{marginTop:6}}>★ Rate</Btn>
            </div>
          </div>

          <div className="row" style={{gap: 0, borderBottom: '2px dashed var(--rule)', marginBottom: 10}}>
            {['Cast', 'Relations', 'Summary', 'Reviews', 'Quotes'].map((t, i) => (
              <div key={t} style={{
                padding:'5px 12px',
                fontFamily:'Patrick Hand', fontSize: 15,
                background: i === 0 ? 'var(--accent)' : 'transparent',
                color: i === 0 ? '#fffdf7' : 'var(--ink-2)',
                fontWeight: i === 0 ? 700 : 400,
                borderRadius: '8px 8px 0 0'
              }}>{t}</div>
            ))}
          </div>

          <div style={{display:'grid', gridTemplateColumns:'1.3fr 0.9fr', gap: 12, alignItems:'flex-start'}}>
            <div className="graph-wrap" style={{
              border:'1.8px dashed var(--rule)', borderRadius: 8,
              background: 'repeating-linear-gradient(90deg, rgba(0,0,0,.03) 0 1px, transparent 1px 30px), repeating-linear-gradient(rgba(0,0,0,.03) 0 1px, transparent 1px 30px)'
            }}>
              <Graph />
              <div style={{position:'absolute', top: 6, right: 8, fontFamily:'Caveat', fontSize: 16, color:'var(--muted)'}}>drag · scroll = zoom</div>
            </div>
            <div>
              <div className="row" style={{gap: 6, marginBottom: 6, flexWrap:'wrap'}}>
                <Chip acc>all</Chip>
                <Chip>family</Chip>
                <Chip>romance</Chip>
                <Chip>ally</Chip>
                <Chip>enemy</Chip>
              </div>
              <div className="card" style={{borderColor:'var(--accent)', background:'#fffaf2'}}>
                <div className="row" style={{gap: 10}}>
                  <Avatar initials="PA" size="lg" acc />
                  <div>
                    <div style={{fontFamily:'Caveat', fontSize:24, fontWeight:700, lineHeight:1}}>Paul Atreides</div>
                    <div style={{fontSize:13, color:'var(--muted)'}}>protagonist · enters ch. 1</div>
                  </div>
                </div>
                <Line w="long" /><Line w="mid" thin />
                <Hr />
                <div style={{fontFamily:'Patrick Hand', fontSize:13, color:'var(--muted)', letterSpacing:1}}>
                  RELATIONS (6)
                </div>
                <div className="stack-tight" style={{gap:2, marginTop:4}}>
                  <div style={{fontSize:14}}>↔ <b>Chani</b> <span style={{color:'var(--muted)'}}>love</span></div>
                  <div style={{fontSize:14}}>↔ <b>Leto I</b> <span style={{color:'var(--muted)'}}>son / father</span></div>
                  <div style={{fontSize:14}}>↔ <b>Stilgar</b> <span style={{color:'var(--muted)'}}>ally</span></div>
                  <div style={{fontSize:14}}>↔ <b>Baron H.</b> <span style={{color:'var(--accent)'}}>conflict</span></div>
                </div>
              </div>
              <div className="legend">
                <span><span className="swatch" style={{background:'#2a6fdb'}}/>family</span>
                <span><span className="swatch" style={{background:'#c8417a'}}/>romance</span>
                <span><span className="swatch" style={{background:'#1f8a5b'}}/>ally</span>
                <span><span className="swatch" style={{background:'#d94f1e'}}/>enemy</span>
              </div>
            </div>
          </div>
        </BrowserFrame>
      </Sheet>

      <Sheet label="02 · Character page" caption="after clicking a node in the graph" tilt="r">
        <BrowserFrame url="storyshelf.app/book/dune/c/paul-atreides">
          <Nav active="Characters" />
          <div style={{fontFamily:'Patrick Hand', fontSize:13, color:'var(--muted)', marginBottom: 6}}>
            ← Dune / Cast / <b style={{color:'var(--ink)'}}>Paul Atreides</b>
          </div>
          <div className="row" style={{gap: 14, alignItems:'flex-start'}}>
            <Avatar initials="PA" size="xl" acc />
            <div style={{flex:1}}>
              <div style={{fontFamily:'Caveat', fontSize:38, fontWeight:700, lineHeight:1}}>Paul Atreides</div>
              <div style={{color:'var(--muted)'}}>aka Muad'Dib · protagonist</div>
              <div className="row" style={{gap:6, marginTop:6, flexWrap:'wrap'}}>
                <Chip>duke</Chip><Chip>Bene Gesserit</Chip><Chip>Fremen</Chip><Chip dot>POV</Chip>
              </div>
            </div>
            <Btn kind="ghost">✎ edit</Btn>
          </div>

          <Hr />

          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap: 14}}>
            <div>
              <div style={{fontFamily:'Caveat', fontSize: 22, fontWeight:700}}>Bio</div>
              <div style={{fontSize: 13.5, color:'var(--ink-2)'}}>
                <Line w="full" /><Line w="full" /><Line w="long" />
                <Line w="full" /><Line w="mid" />
              </div>
              <div style={{marginTop:8, fontFamily:'Patrick Hand', fontSize:12, color:'var(--muted)'}}>
                ✨ AI-generated · <u>source: ch. 1–6</u>
              </div>

              <div style={{marginTop: 14, fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Quotes</div>
              <div style={{borderLeft:'3px solid var(--accent)', paddingLeft: 10, fontSize:14, fontFamily:'Patrick Hand'}}>
                "Fear is the mind-killer…"
                <div style={{color:'var(--muted)', fontSize:12, marginTop:2}}>p. 18 · ch. 1</div>
              </div>
            </div>
            <div>
              <div style={{fontFamily:'Caveat', fontSize: 22, fontWeight:700}}>Relations · 6</div>
              <div className="stack-tight" style={{gap:6}}>
                {[
                  ['Chani', 'love', '#c8417a'],
                  ['Leto I', 'father', '#2a6fdb'],
                  ['Jessica', 'mother', '#2a6fdb'],
                  ['Stilgar', 'ally', '#1f8a5b'],
                  ['Gurney H.', 'mentor', '#1f8a5b'],
                  ['Baron H.', 'house feud', '#d94f1e'],
                ].map(([n, r, c], i) => (
                  <div key={i} className="card row" style={{gap:8, padding:'6px 10px'}}>
                    <Avatar initials={n.split(' ').map(w=>w[0]).join('').slice(0,2)} />
                    <div style={{flex:1}}>
                      <div style={{fontSize:14, fontWeight:700}}>{n}</div>
                      <div style={{fontSize:12, color:'var(--muted)'}}>{r}</div>
                    </div>
                    <div style={{width:10, height:10, borderRadius:'50%', background:c, border:'1.5px solid var(--rule)'}}/>
                  </div>
                ))}
              </div>
              <Hr />
              <div style={{fontFamily:'Caveat', fontSize:20, fontWeight:700}}>Also appears in</div>
              <div className="row" style={{gap:6, marginTop:4}}>
                <Cover style={{width: 36, aspectRatio:'2/3'}}>Messiah</Cover>
                <Cover style={{width: 36, aspectRatio:'2/3'}}>Children</Cover>
                <Cover style={{width: 36, aspectRatio:'2/3'}}>God Emp.</Cover>
              </div>
            </div>
          </div>
        </BrowserFrame>
      </Sheet>
    </div>

    {/* Profile sheet — personal galaxy */}
    <div style={{marginTop: 22}}>
      <Sheet label="03 · Profile = personal book-galaxy" caption="your reading mapped as one big graph" tilt="0">
        <BrowserFrame url="storyshelf.app/u/alex-k">
          <Nav />
          <div className="row" style={{gap: 14, alignItems:'flex-start'}}>
            <Avatar initials="AK" size="xl" acc />
            <div style={{flex:1}}>
              <div style={{fontFamily:'Caveat', fontSize:32, fontWeight:700, lineHeight:1}}>Alex Kowalski</div>
              <div style={{color:'var(--muted)'}}>148 books read · 612 characters discovered · 1.9k relations</div>
              <div className="row" style={{gap:6, marginTop:6}}>
                <Chip>sci-fi</Chip><Chip>literary</Chip><Chip acc>graph view</Chip>
                <Chip>shelves view</Chip>
              </div>
            </div>
            <Btn kind="ghost">⚙ settings</Btn>
          </div>

          <Hr />

          <div style={{display:'grid', gridTemplateColumns:'1.4fr 1fr', gap: 14, alignItems:'flex-start'}}>
            <div>
              <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Your book galaxy</div>
              <div style={{color:'var(--muted)', fontSize:13, marginBottom:6}}>
                each cluster is a book · dashed lines bridge characters across books (archetype, relation, theme)
              </div>
              <div className="graph-wrap" style={{
                aspectRatio:'1.3/1',
                border:'1.8px dashed var(--rule)', borderRadius: 8,
                background:'repeating-linear-gradient(90deg, rgba(0,0,0,.03) 0 1px, transparent 1px 30px), repeating-linear-gradient(rgba(0,0,0,.03) 0 1px, transparent 1px 30px)'
              }}>
                <PersonalGraph />
              </div>
              <div className="row" style={{gap:6, marginTop:6, flexWrap:'wrap'}}>
                <Chip acc>all books (148)</Chip>
                <Chip>this year</Chip>
                <Chip>favorites</Chip>
                <Chip dot>bridges only</Chip>
              </div>
            </div>

            <div>
              <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Patterns AI sees in your reading</div>
              <div className="card" style={{borderStyle:'dashed', borderColor:'var(--accent)', background:'#fffaf2'}}>
                <div style={{fontFamily:'Patrick Hand', fontSize:12, color:'var(--muted)', letterSpacing:1}}>FAVORITE ARCHETYPE</div>
                <div style={{fontFamily:'Caveat', fontWeight:700, fontSize:22, lineHeight:1, marginBottom:4}}>The reluctant chosen one</div>
                <div style={{fontSize:13}}>found across <b>14 books</b> on your shelf — Paul (Dune), Lyra (Compass), Frodo, Kvothe…</div>
              </div>

              <Hr />

              <div style={{fontFamily:'Caveat', fontSize:20, fontWeight:700}}>Characters you've followed</div>
              <div className="stack-tight" style={{gap:6, marginTop:4}}>
                {[
                  ['Sherlock Holmes', '60 stories'],
                  ['Geralt of Rivia', '7 books'],
                  ['Hermione Granger', '7 books'],
                  ['Atticus Finch', '2 books'],
                ].map(([n,b],i)=>(
                  <div key={i} className="card row" style={{gap:8, padding:'6px 10px'}}>
                    <Avatar initials={n.split(' ').map(w=>w[0]).join('').slice(0,2)} />
                    <div style={{flex:1}}>
                      <div style={{fontSize:14, fontWeight:700}}>{n}</div>
                      <div style={{fontSize:12, color:'var(--muted)'}}>{b}</div>
                    </div>
                    <Chip>♥</Chip>
                  </div>
                ))}
              </div>

              <Hr />

              <div style={{fontFamily:'Caveat', fontSize:20, fontWeight:700}}>Settings</div>
              <div className="stack-tight" style={{gap:3, fontSize:13}}>
                <div className="row" style={{justifyContent:'space-between'}}><span>cross-book bridges</span><Chip acc>on</Chip></div>
                <div className="row" style={{justifyContent:'space-between'}}><span>show enemy edges</span><Chip>on</Chip></div>
                <div className="row" style={{justifyContent:'space-between'}}><span>graph privacy</span><Chip>friends</Chip></div>
                <div className="row" style={{justifyContent:'space-between'}}><span>spoiler shield</span><Chip>strict</Chip></div>
              </div>
            </div>
          </div>
        </BrowserFrame>
      </Sheet>
    </div>

    <div className="footnote">
      <span className="label">NOTES</span>
      <div>
        Graph-as-hero strongly differentiates from Goodreads. The profile leans into it: your
        reading life becomes a personal galaxy. Risk: needs a strong extractor and curation —
        and books with 50+ characters need a "top 10" mode with progressive expansion.
      </div>
    </div>
  </>
);

window.VariantA = VariantA;
window.VariantB = VariantB;

// === Variant C: Companion / Chat =============================================
const VariantC = () => (
  <>
    <div className="variant-head">
      <h2>C. AI Companion (chat)</h2>
      <div className="why">
        Whole UI built around a <b>conversation with a reading assistant</b>. You ask about
        a character, a relation, a motif — AI answers with cards (character, graph, quote).
        The book is a left rail; chat takes the right 60%. More "research", less "social".
      </div>
    </div>

    <div className="grid cols-2">
      <Sheet label="01 · Book + companion" caption="chat keeps book context">
        <BrowserFrame url="storyshelf.app/book/dune?ai=on">
          <Nav active="Discover" />
          <div style={{display:'grid', gridTemplateColumns:'210px 1fr', gap: 14, alignItems:'flex-start'}}>
            <div>
              <Cover>Dune</Cover>
              <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700, marginTop:6}}>Dune</div>
              <div style={{color:'var(--muted)', fontSize:13}}>Frank Herbert</div>
              <Hr />
              <div style={{fontFamily:'Patrick Hand', fontSize:13, color:'var(--muted)', letterSpacing:1}}>PROGRESS</div>
              <div style={{
                height: 8, border:'1.5px solid var(--rule)', borderRadius:999,
                overflow:'hidden', marginTop:4, background:'#fff'
              }}>
                <div style={{width:'42%', height:'100%', background:'var(--accent)'}}/>
              </div>
              <div style={{fontSize:12, color:'var(--muted)', marginTop:3}}>ch. 6 of 14 · 42%</div>
              <Hr />
              <div style={{fontFamily:'Patrick Hand', fontSize:13, color:'var(--muted)', letterSpacing:1}}>CAST (8)</div>
              <div className="stack-tight" style={{gap:4, marginTop: 4}}>
                {DUNE_CHARS.slice(0,5).map(c => (
                  <div key={c.id} className="row" style={{gap:6, fontSize:13}}>
                    <Avatar initials={c.name.split(' ').map(w=>w[0]).join('').slice(0,2)} />
                    {c.name.split(' ')[0]}
                  </div>
                ))}
                <div style={{fontSize:12, color:'var(--muted)'}}>+3</div>
              </div>
            </div>

            <div style={{
              border:'2px solid var(--rule)', borderRadius: 12,
              padding: 12, background:'#fffdf7',
              display:'flex', flexDirection:'column', gap: 8, minHeight: 460
            }}>
              <div className="row" style={{justifyContent:'space-between', borderBottom:'1.5px dashed var(--rule)', paddingBottom: 6, marginBottom:4}}>
                <div style={{fontFamily:'Caveat', fontWeight:700, fontSize:22}}>✨ Reading companion</div>
                <Chip>spoilers: up to ch. 6</Chip>
              </div>

              <div className="bubble me">Who is Chani and how does she meet Paul?</div>
              <div className="bubble ai">
                Chani is a young Fremen, daughter of Liet-Kynes. She first appears in Paul's
                visions, then they meet in person after he escapes into the desert.
                <span className="src">source: ch. 1, ch. 4, ch. 6 · 3 quotes</span>
              </div>

              <div className="bubble ai" style={{padding: 6, maxWidth: '78%'}}>
                <div className="card row" style={{gap:8, borderColor:'var(--accent)', padding:'8px 10px'}}>
                  <Avatar initials="Ch" acc />
                  <div style={{flex:1}}>
                    <div style={{fontFamily:'Caveat', fontSize:20, fontWeight:700, lineHeight:1}}>Chani</div>
                    <div style={{fontSize:12, color:'var(--muted)'}}>Fremen · Paul's lover</div>
                  </div>
                  <Chip>open →</Chip>
                </div>
              </div>

              <div className="bubble me">Show me the conflicts between houses</div>
              <div className="bubble ai" style={{padding: 6, maxWidth: '88%'}}>
                <div style={{padding: '4px 6px 8px'}}>
                  <div style={{fontFamily:'Caveat', fontWeight:700, fontSize:18}}>Atreides ↔ Harkonnens</div>
                </div>
                <div style={{
                  border:'1.5px dashed var(--rule)', borderRadius:6, padding: 6, background:'#fffaf2'
                }}>
                  <svg viewBox="0 0 360 130" style={{width:'100%', height:110}}>
                    <line x1="60" y1="40" x2="180" y2="40" stroke="#2a6fdb" strokeWidth="2"/>
                    <line x1="60" y1="40" x2="180" y2="100" stroke="#2a6fdb" strokeWidth="2"/>
                    <line x1="300" y1="40" x2="300" y2="100" stroke="#2a6fdb" strokeWidth="2"/>
                    <line x1="180" y1="40" x2="300" y2="40" stroke="#d94f1e" strokeWidth="2.5" strokeDasharray="5 4"/>
                    <line x1="180" y1="100" x2="300" y2="100" stroke="#d94f1e" strokeWidth="2.5" strokeDasharray="5 4"/>
                    {[['Leto',60,40],['Paul',180,40],['Jessica',60,100],['Baron',300,40],['Feyd',300,100],['Chani',180,100]].map(([n,x,y],i)=>(
                      <g key={i}>
                        <circle cx={x} cy={y} r="16" fill="#fffdf7" stroke="var(--rule)" strokeWidth="2"/>
                        <text x={x} y={y+4} textAnchor="middle" fontFamily="Caveat" fontWeight="700" fontSize="14">{n}</text>
                      </g>
                    ))}
                  </svg>
                </div>
                <span className="src">click a node to open the character</span>
              </div>

              <div style={{flex:1}} />

              <div style={{
                border:'2px solid var(--rule)', borderRadius:10, padding: 6,
                display:'flex', gap: 6, alignItems:'center'
              }}>
                <div className="field" style={{flex:1, border:'none', padding: '4px 6px'}}>ask about a character, relation, motif…</div>
                <Btn kind="acc">↑</Btn>
              </div>
              <div className="row" style={{gap: 6, flexWrap:'wrap'}}>
                <Chip dot>who fights whom?</Chip>
                <Chip dot>summarize ch. 5</Chip>
                <Chip dot>what don't I know about Jessica?</Chip>
              </div>
            </div>
          </div>
        </BrowserFrame>
      </Sheet>

      <Sheet label="02 · Library with AI dock" caption="assistant always available, bottom-right" tilt="r">
        <BrowserFrame url="storyshelf.app/library">
          <Nav active="My shelf" />
          <div style={{fontFamily:'Caveat', fontSize:28, fontWeight:700}}>My shelf</div>
          <div style={{color:'var(--muted)', marginBottom:8}}>34 read · 7 in progress · 102 want</div>

          <div className="row" style={{gap:6, marginBottom: 10, flexWrap:'wrap'}}>
            <Chip acc>all</Chip>
            <Chip>reading (7)</Chip>
            <Chip>read (34)</Chip>
            <Chip>want (102)</Chip>
          </div>

          <div className="catalog-grid" style={{gridTemplateColumns:'repeat(6, 1fr)', gap: 10}}>
            {SAMPLE_BOOKS.map((b, i) => (
              <div className="book" key={i}>
                <Cover style={{aspectRatio:'2/3'}}>{b.t}</Cover>
                <div className="t" style={{fontSize:12}}>{b.t}</div>
              </div>
            ))}
            {[...Array(2)].map((_,i)=>(
              <div className="book" key={'x'+i}>
                <Cover style={{aspectRatio:'2/3', opacity:.5}}>?</Cover>
              </div>
            ))}
          </div>

          <div style={{
            marginTop: 14, marginLeft: 'auto', width: '60%',
            border:'2.5px solid var(--accent)', borderRadius: 14,
            padding: 10, background:'#fffaf2', position:'relative'
          }}>
            <div style={{position:'absolute', top:-12, left:14, background:'var(--accent)', color:'#fffdf7', padding:'1px 10px', borderRadius:999, fontFamily:'Caveat', fontWeight:700, border:'2px solid var(--rule)'}}>
              ✨ Library assistant
            </div>
            <div className="bubble me" style={{marginBottom:6}}>which of my books has the most leading female characters?</div>
            <div className="bubble ai">
              From your shelf: <b>The Handmaid's Tale</b> (8), <b>100 Years of Solitude</b> (6),
              <b> Golden Compass</b> (5). Show cards?
              <span className="src">analyzed 41 books · 6 s</span>
            </div>
            <div style={{display:'flex', gap:6, marginTop: 6}}>
              <Chip>yes, show</Chip>
              <Chip>filter shelf</Chip>
              <Chip>save as list</Chip>
            </div>
          </div>
        </BrowserFrame>
      </Sheet>
    </div>

    {/* Profile sheet — chat history + persona */}
    <div style={{marginTop: 22}}>
      <Sheet label="03 · Profile = AI history" caption="your conversations become your reading log" tilt="0">
        <BrowserFrame url="storyshelf.app/u/alex-k">
          <Nav />
          <div style={{display:'grid', gridTemplateColumns:'1fr 1.2fr', gap: 18, alignItems:'flex-start'}}>
            <div>
              <div className="row" style={{gap: 12, alignItems:'flex-start'}}>
                <Avatar initials="AK" size="xl" acc />
                <div>
                  <div style={{fontFamily:'Caveat', fontSize:30, fontWeight:700, lineHeight:1}}>Alex Kowalski</div>
                  <div style={{color:'var(--muted)'}}>@alex-k · since 2024</div>
                  <div className="row" style={{gap:6, marginTop:6, flexWrap:'wrap'}}>
                    <Chip dot>148 books</Chip><Chip dot>312 chats</Chip>
                  </div>
                </div>
              </div>

              <Hr />

              <div className="card" style={{borderStyle:'dashed', borderColor:'var(--accent)', background:'#fffaf2'}}>
                <div style={{fontFamily:'Patrick Hand', fontSize:12, color:'var(--muted)', letterSpacing:1}}>YOUR READER PERSONA · AI</div>
                <div style={{fontFamily:'Caveat', fontWeight:700, fontSize:22, lineHeight:1, marginBottom:4}}>The Character Cartographer</div>
                <div style={{fontSize:13.5}}>You ask 4× more about relationships than plot. You favor morally grey antagonists. You finish dystopias 23% faster than the average reader.</div>
                <div className="row" style={{gap:6, marginTop:6}}>
                  <Chip>share persona</Chip>
                  <Chip>regenerate</Chip>
                </div>
              </div>

              <Hr />

              <div style={{fontFamily:'Caveat', fontSize:20, fontWeight:700}}>AI preferences</div>
              <div className="stack-tight" style={{gap:4, fontSize:13.5}}>
                <div className="row" style={{justifyContent:'space-between'}}><span>assistant tone</span><Chip>scholarly</Chip></div>
                <div className="row" style={{justifyContent:'space-between'}}><span>default spoiler limit</span><Chip acc>current chapter</Chip></div>
                <div className="row" style={{justifyContent:'space-between'}}><span>cite quotes</span><Chip>always</Chip></div>
                <div className="row" style={{justifyContent:'space-between'}}><span>language</span><Chip>English</Chip></div>
                <div className="row" style={{justifyContent:'space-between'}}><span>save chat history</span><Chip>30 days</Chip></div>
              </div>
            </div>

            <div>
              <div className="row" style={{justifyContent:'space-between'}}>
                <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Recent conversations</div>
                <Chip>search</Chip>
              </div>
              <div className="stack-tight" style={{gap:8, marginTop:6}}>
                {[
                  ['Dune', 'who really betrays Leto?', 14, 'today'],
                  ["1984", "is O'Brien sincere in Part 2?", 22, 'yesterday'],
                  ['The Trial', 'why does K. accept the trial?', 8, '3 days'],
                  ['Wuthering Heights', 'is Heathcliff redeemable?', 31, '1 week'],
                  ['100 Years of Solitude', 'map the Buendía tree', 6, '2 weeks'],
                ].map(([book, q, msgs, when], i) => (
                  <div key={i} className="card">
                    <div className="row" style={{justifyContent:'space-between'}}>
                      <div style={{fontSize:14, fontWeight:700}}>{book}</div>
                      <div style={{fontSize:12, color:'var(--muted)'}}>{when}</div>
                    </div>
                    <div style={{fontSize:13, color:'var(--ink-2)', fontFamily:'Patrick Hand'}}>"{q}"</div>
                    <div className="row" style={{gap:6, marginTop:4}}>
                      <Chip>{msgs} msgs</Chip>
                      <Chip>resume</Chip>
                      <Chip>delete</Chip>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </BrowserFrame>
      </Sheet>
    </div>

    <div className="footnote">
      <span className="label">NOTES</span>
      <div>
        Strongest "LLM-native" signal. Risk: chat-only alienates users who want classic browsing.
        That's why the assistant is an <em>addition</em> to views, not a replacement. The spoiler
        slider (per-chapter) is critical here.
      </div>
    </div>
  </>
);

window.VariantC = VariantC;
