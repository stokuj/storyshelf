// Shared Settings sheet — used by every variant.
// Same account-settings form everywhere; the variant-specific extras
// (AI / graph / notebook / character preferences) live on each variant's
// own Profile sheet, so Settings stays focused on the account itself.

const SettingsScreen = ({ accent = 'default' }) => {
  // little helper for the visibility radio
  const VisibilityCard = ({ value, label, sub, selected, color }) => (
    <div className="card" style={{
      borderColor: selected ? color : 'var(--rule)',
      borderWidth: selected ? '2.5px' : '1.8px',
      background: selected ? '#fffaf2' : '#fffdf7',
      padding: '10px 12px',
      cursor: 'default'
    }}>
      <div className="row" style={{gap: 8, alignItems:'flex-start'}}>
        <div style={{
          width: 18, height: 18, borderRadius: '50%',
          border: `2px solid ${selected ? color : 'var(--rule)'}`,
          background: '#fffdf7',
          flexShrink: 0, marginTop: 2,
          display:'flex', alignItems:'center', justifyContent:'center'
        }}>
          {selected && <div style={{width: 9, height: 9, borderRadius:'50%', background: color}}/>}
        </div>
        <div>
          <div style={{fontFamily:'Caveat', fontSize: 19, fontWeight:700, lineHeight: 1}}>{label}</div>
          <div style={{fontSize: 12.5, color:'var(--muted)', marginTop: 2}}>{sub}</div>
        </div>
      </div>
    </div>
  );

  const FormField = ({ label, value, hint, action }) => (
    <div style={{marginBottom: 10}}>
      <div className="row" style={{justifyContent:'space-between', marginBottom: 3}}>
        <div style={{fontFamily:'Patrick Hand', fontSize: 13, letterSpacing: 1, color:'var(--muted)'}}>
          {label}
        </div>
        {action && <span style={{fontSize: 12, color:'var(--accent)', textDecoration:'underline'}}>{action}</span>}
      </div>
      <div className="field" style={{color: 'var(--ink)', display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <span>{value}</span>
        {hint && <span style={{fontSize: 12, color:'var(--muted)', fontStyle:'italic'}}>{hint}</span>}
      </div>
    </div>
  );

  return (
    <BrowserFrame url="storyshelf.app/settings">
      <Nav />
      <div className="row" style={{gap: 18, alignItems:'flex-start'}}>
        {/* left nav */}
        <div style={{width: 180, flexShrink: 0}}>
          <div style={{fontFamily:'Caveat', fontSize: 26, fontWeight: 700, lineHeight: 1, marginBottom: 8}}>
            Settings
          </div>
          <div className="stack-tight" style={{gap: 4}}>
            {[
              ['Account', true],
              ['Profile & privacy', false],
              ['Notifications', false],
              ['AI preferences', false],
              ['Reading & shelves', false],
              ['Connected apps', false],
              ['Data & export', false],
              ['Danger zone', false],
            ].map(([l, on], i) => (
              <div key={i} style={{
                padding: '5px 10px',
                borderRadius: 8,
                background: on ? 'var(--ink)' : 'transparent',
                color: on ? '#fffdf7' : 'var(--ink-2)',
                fontWeight: on ? 700 : 400,
                fontSize: 14,
                border: on ? '2px solid var(--ink)' : '1.8px dashed transparent'
              }}>
                {l}
              </div>
            ))}
          </div>
          <Hr />
          <div style={{fontSize: 12, color: 'var(--muted)', fontFamily: 'Patrick Hand'}}>
            All changes auto-save unless marked otherwise.
          </div>
        </div>

        {/* main column */}
        <div style={{flex: 1, minWidth: 0}}>
          {/* === Avatar block === */}
          <div style={{fontFamily:'Caveat', fontSize: 24, fontWeight:700, marginBottom: 6}}>
            Avatar
          </div>
          <div className="row" style={{gap: 14, alignItems:'flex-start'}}>
            <Avatar initials="AK" size="xl" acc />
            <div style={{flex: 1}}>
              <div style={{
                border: '2px dashed var(--rule)', borderRadius: 10,
                padding: '14px 16px', background: '#fffdf7',
                display:'flex', alignItems:'center', gap: 12
              }}>
                <div style={{fontFamily:'Caveat', fontSize: 28, color:'var(--muted)'}}>⤴</div>
                <div style={{flex:1}}>
                  <div style={{fontFamily:'Caveat', fontSize: 18, fontWeight: 700, lineHeight: 1}}>
                    Drag a photo, or click to upload
                  </div>
                  <div style={{fontSize: 12, color:'var(--muted)', marginTop: 3}}>
                    PNG / JPG · square crop · max 4 MB
                  </div>
                </div>
                <div className="col" style={{gap: 4, alignItems:'flex-end'}}>
                  <Btn kind="primary">Upload</Btn>
                  <span style={{fontSize: 12, color:'var(--accent)', textDecoration:'underline'}}>or generate ✨</span>
                </div>
              </div>
            </div>
          </div>

          <Hr />

          {/* === Account === */}
          <div style={{fontFamily:'Caveat', fontSize: 24, fontWeight:700, marginBottom: 6}}>
            Account
          </div>
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap: 14}}>
            <div>
              <FormField label="DISPLAY NAME" value="Alex Kowalski" />
              <FormField label="USERNAME" value="@alex-k" hint="storyshelf.app/u/alex-k" />
              <FormField label="EMAIL" value="alex.k@gmail.com" action="change · verify" hint="verified ✓" />
            </div>
            <div>
              <FormField label="CURRENT PASSWORD" value="••••••••••••" />
              <FormField label="NEW PASSWORD" value="(at least 12 characters)" />
              <FormField label="CONFIRM NEW PASSWORD" value="(retype)" />
              <div className="row" style={{justifyContent:'space-between', alignItems:'center', marginTop: 4}}>
                <span style={{fontSize: 12.5, color:'var(--muted)'}}>2FA: <b style={{color:'var(--ink)'}}>app-based · on</b></span>
                <Btn>Save password</Btn>
              </div>
            </div>
          </div>

          <Hr />

          {/* === Profile visibility === */}
          <div className="row" style={{justifyContent:'space-between', marginBottom: 6}}>
            <div style={{fontFamily:'Caveat', fontSize: 24, fontWeight:700}}>Profile visibility</div>
            <span style={{fontSize: 12, color:'var(--muted)', fontFamily:'Patrick Hand'}}>
              applies to your profile page, shelves, reviews, and AI artifacts
            </span>
          </div>
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap: 10}}>
            <VisibilityCard
              value="public"
              label="🌐 Public"
              sub="Anyone can view your profile and follow you. Appears in search."
              selected={false}
              color="#1f8a5b"
            />
            <VisibilityCard
              value="friends"
              label="👥 Friends only"
              sub="Visible to people you've approved. Search shows your name but not your shelf."
              selected={true}
              color="var(--accent)"
            />
            <VisibilityCard
              value="private"
              label="🔒 Private"
              sub="Nobody but you can see your profile, shelves, or AI history."
              selected={false}
              color="var(--rule)"
            />
          </div>

          <div style={{marginTop: 10}}>
            <div style={{fontFamily:'Patrick Hand', fontSize: 13, letterSpacing: 1, color:'var(--muted)', marginBottom: 4}}>
              MORE GRANULAR
            </div>
            <div className="stack-tight" style={{gap: 4}}>
              <div className="row" style={{justifyContent:'space-between', fontSize: 13.5}}>
                <span>Show my real name</span>
                <Chip>visible to friends</Chip>
              </div>
              <div className="row" style={{justifyContent:'space-between', fontSize: 13.5}}>
                <span>Show my reading activity in the feed</span>
                <Chip acc>on</Chip>
              </div>
              <div className="row" style={{justifyContent:'space-between', fontSize: 13.5}}>
                <span>Let other readers see characters I follow</span>
                <Chip>off</Chip>
              </div>
              <div className="row" style={{justifyContent:'space-between', fontSize: 13.5}}>
                <span>Allow AI to learn from my notes (anonymized)</span>
                <Chip>off</Chip>
              </div>
              <div className="row" style={{justifyContent:'space-between', fontSize: 13.5}}>
                <span>Indexed by search engines</span>
                <Chip>off</Chip>
              </div>
            </div>
          </div>

          <Hr />

          {/* === Danger zone === */}
          <div style={{
            border: '2px solid #c8417a', borderRadius: 10,
            padding: '10px 14px', background: 'rgba(200, 65, 122, 0.06)'
          }}>
            <div className="row" style={{justifyContent:'space-between'}}>
              <div>
                <div style={{fontFamily:'Caveat', fontSize: 20, fontWeight:700, color: '#c8417a', lineHeight: 1}}>
                  Danger zone
                </div>
                <div style={{fontSize: 13, color: 'var(--ink-2)', marginTop: 2}}>
                  Export everything · pause your account · or permanently delete it.
                </div>
              </div>
              <div className="row" style={{gap: 6}}>
                <Btn>Export data</Btn>
                <Btn>Pause</Btn>
                <Btn style={{borderColor:'#c8417a', color:'#c8417a'}}>Delete account</Btn>
              </div>
            </div>
          </div>

          <div style={{marginTop: 14}} className="row">
            <div style={{flex: 1, fontSize: 12.5, color:'var(--muted)', fontFamily:'Patrick Hand'}}>
              Last saved 2 minutes ago.
            </div>
            <Btn>Cancel</Btn>
            <Btn kind="primary" style={{marginLeft: 6}}>Save changes</Btn>
          </div>
        </div>
      </div>
    </BrowserFrame>
  );
};

window.SettingsScreen = SettingsScreen;
