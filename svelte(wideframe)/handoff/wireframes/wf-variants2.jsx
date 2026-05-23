// === Variant D: Character-first ==============================================
const VariantD = () => (
  <>
    <div className="variant-head">
      <h2>D. Character-first</h2>
      <div className="why">
        Characters are <b>first-class citizens</b>, not book metadata. The main browse grid is
        a wall of faces. You can "follow a character", see them across books (e.g. Sherlock in 60 stories),
        compare archetypes. A book becomes one of many lenses on a character.
      </div>
    </div>

    <div className="grid cols-2">
      <Sheet label="01 · Character feed" caption="instead of a grid of books — a grid of people">
        <BrowserFrame url="storyshelf.app/characters">
          <Nav active="Characters" />
          <div className="row" style={{justifyContent:'space-between', marginBottom: 8}}>
            <div style={{fontFamily:'Caveat', fontSize:28, fontWeight:700}}>Characters</div>
            <div className="row" style={{gap:6}}>
              <Chip>archetype ▾</Chip>
              <Chip>era ▾</Chip>
              <Chip>only from my shelf</Chip>
              <Chip acc>+ random</Chip>
            </div>
          </div>

          <div style={{display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap: 10}}>
            {[
              {n:'Paul Atreides', r:'protagonist', b:'Dune'},
              {n:'Geralt of Rivia', r:'witcher', b:'The Saga'},
              {n:'Sherlock Holmes', r:'detective', b:'60 stories'},
              {n:'Hermione Granger', r:'protagonist', b:'HP 1–7'},
              {n:'Atticus Finch', r:'lawyer', b:'To Kill…'},
              {n:'Lyra Belacqua', r:'protagonist', b:'His Dark M.'},
              {n:'Offred', r:'narrator', b:"Handmaid's T."},
              {n:'Stilgar', r:'Fremen naib', b:'Dune'},
            ].map((c, i) => (
              <div key={i} className="char-card">
                <Avatar initials={c.n.split(' ').map(w=>w[0]).join('').slice(0,2)} size="lg" acc={i===0}/>
                <div className="meta-lines">
                  <div className="role">{c.r}</div>
                  <div className="name">{c.n}</div>
                  <div className="books">in <b>{c.b}</b></div>
                  <div className="row" style={{gap:4, marginTop:2}}>
                    <Chip>follow</Chip>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="annotation-row">
            <span className="lead">idea ↗</span>
            <div style={{fontSize:15, color:'var(--ink-2)'}}>
              cards show <b>how many books</b> a character appears in. Click = full profile with
              every work they're in.
            </div>
          </div>
        </BrowserFrame>
      </Sheet>

      <Sheet label="02 · Character profile (cross-book)" caption="one character, many books" tilt="r">
        <BrowserFrame url="storyshelf.app/c/sherlock-holmes">
          <Nav active="Characters" />
          <div className="row" style={{gap: 14, alignItems:'flex-start', marginBottom: 8}}>
            <Avatar initials="SH" size="xl" acc />
            <div style={{flex:1}}>
              <div style={{fontFamily:'Caveat', fontSize:38, fontWeight:700, lineHeight:1}}>Sherlock Holmes</div>
              <div style={{color:'var(--muted)'}}>consulting detective · 221B Baker Street</div>
              <div className="row" style={{gap:6, marginTop:6, flexWrap:'wrap'}}>
                <Chip>literary icon</Chip><Chip>detective</Chip><Chip>19th c.</Chip>
                <Chip dot>Conan Doyle canon</Chip>
              </div>
            </div>
            <div className="col" style={{alignItems:'flex-end'}}>
              <Btn kind="acc">+ follow</Btn>
              <div style={{fontSize:12, color:'var(--muted)', marginTop:4}}>4,829 followers</div>
            </div>
          </div>

          <Hr />

          <div style={{display:'grid', gridTemplateColumns:'1.2fr 1fr', gap: 14, alignItems:'flex-start'}}>
            <div>
              <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Appears in</div>
              <div style={{color:'var(--muted)', fontSize:13, marginBottom:6}}>60 works · 4 novels, 56 short stories</div>
              <div style={{display:'grid', gridTemplateColumns:'repeat(6,1fr)', gap: 6}}>
                {[...Array(12)].map((_,i)=>(
                  <Cover key={i} style={{aspectRatio:'2/3', fontSize:11}}>vol {i+1}</Cover>
                ))}
              </div>
              <div style={{textAlign:'center', marginTop:4, fontSize:13, color:'var(--muted)'}}>+48 more</div>

              <Hr />

              <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Recurring relations</div>
              <div className="stack-tight" style={{gap:6, marginTop:4}}>
                {[
                  ['Dr. Watson', 'flatmate, friend', 60],
                  ['Mrs. Hudson', 'landlady', 47],
                  ['Inspector Lestrade', 'Scotland Yard contact', 28],
                  ['Prof. Moriarty', 'arch-enemy', 9],
                  ['Mycroft Holmes', 'elder brother', 4],
                ].map(([n, r, c], i) => (
                  <div key={i} className="card row" style={{gap:8, padding:'6px 10px'}}>
                    <Avatar initials={n.split(' ').map(w=>w[0]).join('').slice(0,2)} />
                    <div style={{flex:1}}>
                      <div style={{fontSize:14, fontWeight:700}}>{n}</div>
                      <div style={{fontSize:12, color:'var(--muted)'}}>{r}</div>
                    </div>
                    <div style={{fontSize:12, color:'var(--muted)'}}>{c} works</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700}}>✨ AI · what drives this character</div>
              <div className="card" style={{borderStyle:'dashed', borderColor:'var(--accent)', background:'#fffaf2'}}>
                <div className="stack-tight" style={{gap:2}}>
                  <div style={{fontSize:13, color:'var(--muted)', letterSpacing:1}}>ARCHETYPE</div>
                  <div style={{fontFamily:'Caveat', fontWeight:700, fontSize:20, lineHeight:1}}>The brilliant misanthrope</div>
                </div>
                <Line w="full" /><Line w="long" /><Line w="mid" thin />
              </div>

              <div style={{marginTop: 10, fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Similar characters</div>
              <div className="stack-tight" style={{gap:6}}>
                {[['Gregory House', '94%'],['L (Death Note)', '88%'],['Hercule Poirot', '81%'],['C. Auguste Dupin', '76%']].map(([n,p],i)=>(
                  <div key={i} className="card row" style={{gap:8, padding:'6px 10px'}}>
                    <Avatar initials={n.split(' ').map(w=>w[0]).join('').slice(0,2)} />
                    <div style={{flex:1}}>
                      <div style={{fontSize:14, fontWeight:700}}>{n}</div>
                    </div>
                    <Chip>{p}</Chip>
                  </div>
                ))}
              </div>

              <div style={{marginTop: 10, fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Quotes</div>
              <div style={{borderLeft:'3px solid var(--accent)', paddingLeft:10, fontSize:13.5, fontFamily:'Patrick Hand', color:'var(--ink-2)'}}>
                <Line w="long" /><Line w="mid" />
                <div style={{fontSize:12, color:'var(--muted)', marginTop:2}}>A Study in Scarlet · ch. 2</div>
              </div>
            </div>
          </div>
        </BrowserFrame>
      </Sheet>
    </div>

    {/* Profile sheet — character collector */}
    <div style={{marginTop: 22}}>
      <Sheet label="03 · Profile = character collector" caption="people you follow, archetype affinity" tilt="0">
        <BrowserFrame url="storyshelf.app/u/alex-k">
          <Nav />
          <div className="row" style={{gap: 14, alignItems:'flex-start'}}>
            <Avatar initials="AK" size="xl" acc />
            <div style={{flex:1}}>
              <div style={{fontFamily:'Caveat', fontSize:32, fontWeight:700, lineHeight:1}}>Alex Kowalski</div>
              <div style={{color:'var(--muted)'}}>following 47 characters · 148 books · joined 2024</div>
              <div className="row" style={{gap:6, marginTop:6, flexWrap:'wrap'}}>
                <Chip acc>character collector</Chip>
                <Chip>reluctant chosen one fan</Chip>
                <Chip>antihero spotter</Chip>
              </div>
            </div>
            <Btn kind="ghost">⚙ settings</Btn>
          </div>

          <Hr />

          <div style={{display:'grid', gridTemplateColumns:'1.3fr 1fr', gap: 14, alignItems:'flex-start'}}>
            <div>
              <div className="row" style={{justifyContent:'space-between'}}>
                <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700}}>People you follow · 47</div>
                <Chip>sort: recent ▾</Chip>
              </div>

              <div style={{display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap: 8, marginTop:6}}>
                {[
                  {n:'Sherlock Holmes', l:'arch-enemy of M.', d:'new ch. 14d ago'},
                  {n:'Geralt of Rivia', l:'witcher', d:'rumored prequel'},
                  {n:'Paul Atreides', l:'Muad\'Dib', d:'now in Messiah'},
                  {n:'Lyra Belacqua', l:'Pan\'s witch', d:'—'},
                  {n:'Offred', l:'narrator', d:'sequel: Testaments'},
                  {n:'Atticus Finch', l:'attorney', d:'—'},
                ].map((c, i) => (
                  <div key={i} className="char-card" style={{flexDirection:'column', alignItems:'flex-start', gap:4}}>
                    <div className="row" style={{gap:8, width:'100%'}}>
                      <Avatar initials={c.n.split(' ').map(w=>w[0]).join('').slice(0,2)} acc={i===0}/>
                      <div style={{flex:1}}>
                        <div className="name" style={{fontSize:18}}>{c.n}</div>
                        <div className="role">{c.l}</div>
                      </div>
                    </div>
                    <div style={{fontSize:12, color:'var(--accent)'}}>✨ {c.d}</div>
                  </div>
                ))}
              </div>
              <div style={{textAlign:'center', marginTop:6, fontSize:13, color:'var(--muted)'}}>+41 more</div>
            </div>

            <div>
              <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Your archetype affinity</div>
              <div style={{color:'var(--muted)', fontSize:13, marginBottom:6}}>which kinds of people you keep coming back to</div>
              <div className="stack-tight" style={{gap:8}}>
                {[
                  ['Reluctant chosen one', 28, '#c47a14'],
                  ['Brilliant misanthrope', 19, '#2a6fdb'],
                  ['Tragic patriarch',      14, '#c8417a'],
                  ['Loyal companion',       12, '#1f8a5b'],
                  ['Charismatic villain',    8, '#d94f1e'],
                ].map(([label, pct, color], i) => (
                  <div key={i}>
                    <div className="row" style={{justifyContent:'space-between', fontSize:13, marginBottom:2}}>
                      <span>{label}</span>
                      <span style={{color:'var(--muted)'}}>{pct}</span>
                    </div>
                    <div style={{
                      height: 9, border:'1.5px solid var(--rule)', borderRadius:999, background:'#fff', overflow:'hidden'
                    }}>
                      <div style={{width:`${pct*3}%`, height:'100%', background: color}}/>
                    </div>
                  </div>
                ))}
              </div>

              <Hr />

              <div style={{fontFamily:'Caveat', fontSize:20, fontWeight:700}}>Settings</div>
              <div className="stack-tight" style={{gap:3, fontSize:13.5}}>
                <div className="row" style={{justifyContent:'space-between'}}><span>notify on character updates</span><Chip acc>weekly</Chip></div>
                <div className="row" style={{justifyContent:'space-between'}}><span>archetype labels</span><Chip>show</Chip></div>
                <div className="row" style={{justifyContent:'space-between'}}><span>followers can see follows</span><Chip>on</Chip></div>
                <div className="row" style={{justifyContent:'space-between'}}><span>contribute to canon</span><Chip>on</Chip></div>
              </div>
            </div>
          </div>
        </BrowserFrame>
      </Sheet>
    </div>

    <div className="footnote">
      <span className="label">NOTES</span>
      <div>
        Radical re-conceptualization. Great for character-driven readers, weak for one-shot
        readers. A perfect pretext for LLMs: archetypes, similarities, quotes, bridges between
        books. Needs a sizeable corpus to feel alive.
      </div>
    </div>
  </>
);

// === Variant E: Reader + AI margins ==========================================
const VariantE = () => (
  <>
    <div className="variant-head">
      <h2>E. Reader with AI marginalia</h2>
      <div className="why">
        You open the book and <b>read a passage inside the app</b>. On the right, like margin notes,
        AI drops in observations: "new character X", "relation X–Y established", "desert motif".
        Closest to the human notebook metaphor — best for lit students and book clubs.
      </div>
    </div>

    <div className="grid cols-2">
      <Sheet label="01 · Reading mode" caption="left = text, right = AI marginalia">
        <BrowserFrame url="storyshelf.app/book/dune/read?ch=1">
          <Nav active="My shelf" />
          <div className="row" style={{justifyContent:'space-between', marginBottom: 8}}>
            <div className="row" style={{gap:6}}>
              <Chip>← Dune</Chip>
              <Chip>Chapter 1 · p. 14</Chip>
            </div>
            <div className="row" style={{gap:6}}>
              <Chip dot>characters</Chip>
              <Chip dot>relations</Chip>
              <Chip>motifs</Chip>
              <Chip>🅰 font</Chip>
            </div>
          </div>

          <div style={{display:'grid', gridTemplateColumns:'1.3fr 1fr', gap: 14, alignItems:'flex-start'}}>
            <div className="reader-page">
              <p>
                The woman in the black robe stood in the doorway, looking at the boy.
                The room was stuffy with the muggy heat of a summer night on <span className="hl">Caladan</span>,
                the planet that <span className="hl b">House Atreides</span> had ruled for twenty-six generations.
              </p>
              <p>
                "<span className="hl">Paul</span>," the old woman said. "Do you know why I've come?"
              </p>
              <p>
                The boy did not answer. He knew only that this was <span className="hl">Reverend Mother Gaius Helen Mohiam</span>,
                of whom his mother — <span className="hl">Lady Jessica</span> — had told him.
                He knew she was of the <span className="hl b">Bene Gesserit</span>.
              </p>
              <p>
                <span className="hl">Duke Leto</span> closed the door behind her. His father's eyes
                met his own for a moment before he turned and left them alone.
              </p>
              <p>
                "Your mother wrote to me about you," the old woman said. "She told me
                you have seen her as no one ever does."
              </p>
              <div className="row" style={{justifyContent:'space-between', marginTop: 18}}>
                <Chip>← prev</Chip>
                <div style={{fontSize:12, color:'var(--muted)'}}>p. 14 of 698 · 2%</div>
                <Chip>next →</Chip>
              </div>
            </div>

            <div>
              <div style={{fontFamily:'Caveat', fontWeight:700, fontSize:22, marginBottom: 4}}>
                ✨ AI marginalia
              </div>
              <div style={{fontSize:13, color:'var(--muted)', marginBottom:8}}>
                what's happening on this page. <b>spoilers off</b> — we only know what you've read.
              </div>

              <div className="margin-note">
                <div className="tag">NEW CHARACTER</div>
                <b>Paul Atreides</b> — first appearance. A boy, son of Duke Leto and Lady Jessica.
              </div>
              <div className="margin-note">
                <div className="tag">NEW CHARACTER</div>
                <b>Rev. Mother Mohiam</b> — Bene Gesserit, comes to the boy at night. Purpose: unclear.
              </div>
              <div className="margin-note b">
                <div className="tag">RELATION</div>
                Jessica ↔ Mohiam: <b>pupil / teacher</b> (Bene Gesserit). Jessica wrote about her son.
              </div>
              <div className="margin-note b">
                <div className="tag">RELATION</div>
                Leto ↔ Paul: <b>father / son</b>. Leto exits the room — leaving his son to a test.
              </div>
              <div className="margin-note">
                <div className="tag">MOTIF</div>
                The secret witches' test. Tension builds: the mother is hiding something from the son.
              </div>

              <div style={{borderTop:'1.5px dashed var(--rule)', marginTop: 10, paddingTop: 8}}>
                <Btn full>💬 ask AI about this page</Btn>
              </div>
            </div>
          </div>
        </BrowserFrame>
      </Sheet>

      <Sheet label="02 · Book club mode" caption="share marginalia with a group" tilt="r">
        <BrowserFrame url="storyshelf.app/clubs/wednesday/ch-1">
          <Nav active="My shelf" />
          <div className="row" style={{justifyContent:'space-between', marginBottom: 8}}>
            <div>
              <div style={{fontFamily:'Caveat', fontWeight:700, fontSize:26}}>Wednesday Club · Dune</div>
              <div style={{color:'var(--muted)', fontSize:13}}>5 members · ch. 1–3 by Mar 15</div>
            </div>
            <div className="row" style={{gap:6}}>
              {['MK','JN','AT','PS','DL'].map((x,i)=>(
                <Avatar key={i} initials={x} acc={i===0}/>
              ))}
            </div>
          </div>

          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap: 14}}>
            <div>
              <div style={{fontFamily:'Caveat', fontSize: 22, fontWeight:700, marginBottom:4}}>What AI saw</div>

              <div className="card" style={{marginBottom: 8}}>
                <div className="row" style={{justifyContent:'space-between'}}>
                  <div style={{fontFamily:'Caveat', fontSize:20, fontWeight:700}}>Characters introduced</div>
                  <Chip acc>5 new</Chip>
                </div>
                <div className="row" style={{gap:6, flexWrap:'wrap', marginTop: 4}}>
                  <Chip dot>Paul</Chip>
                  <Chip dot>Jessica</Chip>
                  <Chip dot>Leto I</Chip>
                  <Chip dot>Mohiam</Chip>
                  <Chip dot>Yueh</Chip>
                </div>
              </div>

              <div className="card" style={{marginBottom: 8}}>
                <div className="row" style={{justifyContent:'space-between'}}>
                  <div style={{fontFamily:'Caveat', fontSize:20, fontWeight:700}}>New relations</div>
                  <Chip>3</Chip>
                </div>
                <div className="stack-tight" style={{gap:3, marginTop: 4, fontSize:14}}>
                  <div>• Paul ↔ Jessica · son / mother</div>
                  <div>• Jessica ↔ Mohiam · pupil / mistress</div>
                  <div>• Leto ↔ Jessica · partners (informal)</div>
                </div>
              </div>

              <div className="card">
                <div style={{fontFamily:'Caveat', fontSize:20, fontWeight:700}}>Open questions (AI)</div>
                <div className="stack-tight" style={{gap:3, marginTop:4, fontSize:14}}>
                  <div>1. What was Mohiam testing in Paul?</div>
                  <div>2. Why did Jessica write about her son?</div>
                  <div>3. What is Dr. Yueh hiding?</div>
                </div>
              </div>
            </div>

            <div>
              <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700, marginBottom:4}}>Member notes</div>

              <div className="card" style={{marginBottom: 8}}>
                <div className="row"><Avatar initials="MK" acc/><b style={{fontFamily:'Caveat', fontSize:18}}>Martha</b></div>
                <div style={{fontSize:14}}>"AI mislabeled Mohiam as a <s>witch</s> — Bene Gesserit are sisters."</div>
                <div className="row" style={{gap:6, marginTop:4}}><Chip>👍 3</Chip><Chip>reply</Chip></div>
              </div>

              <div className="card" style={{marginBottom: 8}}>
                <div className="row"><Avatar initials="JN" /><b style={{fontFamily:'Caveat', fontSize:18}}>Jan</b></div>
                <div style={{fontSize:14}}>"Why does Leto leave? A conscious matriarchal plot?"</div>
                <div className="row" style={{gap:6, marginTop:4}}><Chip>👍 1</Chip><Chip>2 replies</Chip></div>
              </div>

              <Btn full>+ add note</Btn>
            </div>
          </div>
        </BrowserFrame>
      </Sheet>
    </div>

    {/* Profile sheet — notebook */}
    <div style={{marginTop: 22}}>
      <Sheet label="03 · Profile = your notebook" caption="every margin note you've made, plus clubs" tilt="0">
        <BrowserFrame url="storyshelf.app/u/alex-k">
          <Nav />
          <div className="row" style={{gap: 14, alignItems:'flex-start'}}>
            <Avatar initials="AK" size="xl" acc />
            <div style={{flex:1}}>
              <div style={{fontFamily:'Caveat', fontSize:32, fontWeight:700, lineHeight:1}}>Alex Kowalski</div>
              <div style={{color:'var(--muted)'}}>1,283 notes · 412 highlights · 4 active clubs</div>
              <div className="row" style={{gap:6, marginTop:6, flexWrap:'wrap'}}>
                <Chip>annotator</Chip><Chip>book-clubber</Chip><Chip acc>3-streak this month</Chip>
              </div>
            </div>
            <Btn kind="ghost">⚙ settings</Btn>
          </div>

          <Hr />

          <div style={{display:'grid', gridTemplateColumns:'1.3fr 1fr', gap: 14, alignItems:'flex-start'}}>
            <div>
              <div className="row" style={{justifyContent:'space-between'}}>
                <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Recent margin notes</div>
                <div className="row" style={{gap:6}}>
                  <Chip>mine</Chip>
                  <Chip acc>mine + AI</Chip>
                  <Chip>club</Chip>
                </div>
              </div>

              <div className="stack-tight" style={{gap:8, marginTop:6}}>
                <div className="card">
                  <div className="row" style={{justifyContent:'space-between'}}>
                    <div style={{fontSize:13, fontWeight:700}}>Dune · ch. 1, p. 14</div>
                    <div style={{fontSize:12, color:'var(--muted)'}}>today</div>
                  </div>
                  <div className="margin-note" style={{marginBottom:0, marginTop:4}}>
                    <div className="tag">YOU</div>
                    Mohiam shows up alone with the boy — first sign that Jessica isn't fully in charge.
                  </div>
                </div>
                <div className="card">
                  <div className="row" style={{justifyContent:'space-between'}}>
                    <div style={{fontSize:13, fontWeight:700}}>The Trial · ch. 4</div>
                    <div style={{fontSize:12, color:'var(--muted)'}}>3 days</div>
                  </div>
                  <div className="margin-note b" style={{marginBottom:0, marginTop:4}}>
                    <div className="tag">RELATION · AI</div>
                    K. ↔ Leni: opportunist romance? Note: confirmed in your highlight, p. 87.
                  </div>
                </div>
                <div className="card">
                  <div className="row" style={{justifyContent:'space-between'}}>
                    <div style={{fontSize:13, fontWeight:700}}>100 Years of Solitude · ch. 6</div>
                    <div style={{fontSize:12, color:'var(--muted)'}}>1 week</div>
                  </div>
                  <div className="margin-note" style={{marginBottom:0, marginTop:4}}>
                    <div className="tag">YOU</div>
                    Names repeat across generations on purpose — read the family tree once before continuing.
                  </div>
                </div>
              </div>
              <div style={{textAlign:'center', marginTop:8}}><Chip>see all 1,283 notes →</Chip></div>
            </div>

            <div>
              <div style={{fontFamily:'Caveat', fontSize:22, fontWeight:700}}>Your book clubs · 4</div>
              <div className="stack-tight" style={{gap:6, marginTop:4}}>
                {[
                  ['Wednesday Club', 'Dune', 5, 'reading ch. 1–3'],
                  ['Antihero Society', 'The Trial', 11, 'discussion Fri'],
                  ['Latin Lit', '100 Years of Solitude', 7, 'idle'],
                  ['Office Book Club', 'Catcher in the Rye', 4, 'finished'],
                ].map(([name, book, people, status], i) => (
                  <div key={i} className="card">
                    <div className="row" style={{justifyContent:'space-between'}}>
                      <div style={{fontSize:14, fontWeight:700}}>{name}</div>
                      <Chip>{people}p</Chip>
                    </div>
                    <div style={{fontSize:13, color:'var(--ink-2)'}}>now: <b>{book}</b></div>
                    <div style={{fontSize:12, color:'var(--muted)'}}>{status}</div>
                  </div>
                ))}
              </div>

              <Hr />

              <div style={{fontFamily:'Caveat', fontSize:20, fontWeight:700}}>Settings</div>
              <div className="stack-tight" style={{gap:3, fontSize:13.5}}>
                <div className="row" style={{justifyContent:'space-between'}}><span>AI marginalia by default</span><Chip acc>on</Chip></div>
                <div className="row" style={{justifyContent:'space-between'}}><span>auto-detect new characters</span><Chip>on</Chip></div>
                <div className="row" style={{justifyContent:'space-between'}}><span>share notes with club</span><Chip>club only</Chip></div>
                <div className="row" style={{justifyContent:'space-between'}}><span>export notes</span><Chip>markdown</Chip></div>
              </div>
            </div>
          </div>
        </BrowserFrame>
      </Sheet>
    </div>

    <div className="footnote">
      <span className="label">NOTES</span>
      <div>
        Strongest pitch for education / book clubs. Requires either an in-app reader or a browser
        extension — both hard. A lighter MVP: skip the reader, ship "summarize chapter X" + manual
        note-taking, layer the reader on later.
      </div>
    </div>
  </>
);

window.VariantD = VariantD;
window.VariantE = VariantE;
