import { useState, useEffect } from 'react';

export default function Dashboard({ user, companionId, API_BASE_URL, profile, threads, onNavigate, onSelectThread }) {
  const [activity, setActivity] = useState([]);
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user && companionId) {
      user.getIdToken().then(async token => {
        try {
          const headers = { Authorization: `Bearer ${token}` };
          const [actRes, goalsRes] = await Promise.all([
            fetch(`${API_BASE_URL}/api/activity?companion_id=${companionId}`, { headers }),
            fetch(`${API_BASE_URL}/api/goals?companion_id=${companionId}`, { headers })
          ]);
          
          if (actRes.ok) setActivity(await actRes.json());
          if (goalsRes.ok) {
            const data = await goalsRes.json();
            setGoals(data.goals || []);
          }
        } catch (err) {
          console.error("Failed to load dashboard data:", err);
        } finally {
          setLoading(false);
        }
      });
    }
  }, [user, companionId, API_BASE_URL]);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
      {/* Profile Card */}
      <div className="glass" style={{ padding: '24px', gridColumn: '1 / -1', display: 'flex', gap: '24px', alignItems: 'center' }}>
        <div className="floating" style={{ position: 'relative', width: '100px', height: '120px' }}>
          <svg viewBox="0 0 100 120" style={{ width: '100%', height: '100%', fill: 'var(--primary-accent)', opacity: 0.85 }}>
            <path d="M20,50 C20,20 80,20 80,50 C80,70 85,90 80,100 C75,95 70,105 60,100 C50,105 40,95 30,100 C20,105 25,95 20,100 C15,90 20,70 20,50 Z" />
            <ellipse cx="40" cy="50" rx="6" ry="6" fill="#fff" />
            <ellipse cx="60" cy="50" rx="6" ry="6" fill="#fff" />
            <ellipse cx="40" cy="50" rx="3" ry="3" fill="#0f0c20" />
            <ellipse cx="60" cy="50" rx="3" ry="3" fill="#0f0c20" />
            <path d="M45,70 Q50,75 55,70" stroke="#fff" strokeWidth="3" fill="none" />
          </svg>
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 600 }}>{profile.name}</h2>
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <span style={{ fontSize: '0.85rem', background: 'rgba(255,255,255,0.1)', padding: '4px 10px', borderRadius: '12px', color: 'var(--text-secondary)' }}>{profile.species}</span>
            <span style={{ fontSize: '0.85rem', background: 'rgba(255,255,255,0.1)', padding: '4px 10px', borderRadius: '12px', color: 'var(--text-secondary)' }}>Mood: {profile.mood}</span>
            <span style={{ fontSize: '0.85rem', background: 'rgba(255,255,255,0.1)', padding: '4px 10px', borderRadius: '12px', color: 'var(--text-secondary)' }}>Bond: {profile.bond}</span>
          </div>
          <div style={{ marginTop: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '8px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Energy</span>
              <span style={{ fontWeight: 600 }}>{Math.round(profile.energy)}%</span>
            </div>
            <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: `${profile.energy}%`, height: '100%', background: 'var(--primary-accent)', borderRadius: '4px', transition: 'width 0.5s ease-in-out' }}></div>
            </div>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <button onClick={() => onNavigate('chat')} style={{ background: 'var(--primary-accent)', color: 'white', padding: '16px', borderRadius: '12px', border: 'none', cursor: 'pointer', fontWeight: 600 }}>💬 Chat with Buddy</button>
          <button onClick={() => { onSelectThread(null); onNavigate('chat'); }} style={{ background: 'rgba(255,255,255,0.1)', color: 'white', padding: '16px', borderRadius: '12px', border: 'none', cursor: 'pointer', fontWeight: 600 }}>+ New Conversation</button>
          <button onClick={() => onNavigate('memory')} style={{ background: 'rgba(255,255,255,0.1)', color: 'white', padding: '16px', borderRadius: '12px', border: 'none', cursor: 'pointer', fontWeight: 600 }}>🧠 Memories</button>
          <button onClick={() => onNavigate('settings')} style={{ background: 'rgba(255,255,255,0.1)', color: 'white', padding: '16px', borderRadius: '12px', border: 'none', cursor: 'pointer', fontWeight: 600 }}>⚙️ Settings</button>
        </div>
      </div>

      {/* Activity Timeline */}
      <div className="glass" style={{ padding: '24px' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', marginBottom: '16px' }}>Recent Activity</h3>
        {loading ? (
          <div style={{ color: 'var(--text-secondary)' }}>Loading activity...</div>
        ) : activity.length === 0 ? (
          <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic', padding: '20px', textAlign: 'center', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>Buddy hasn't seen much activity yet. Talk to them!</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {activity.map((act, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                <span style={{ fontWeight: 500 }}>{act.title || act.type}</span>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{new Date(act.timestamp || act.hour).toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Active Goals */}
      <div className="glass" style={{ padding: '24px', gridColumn: '1 / -1' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', marginBottom: '16px' }}>Active Goals</h3>
        {loading ? (
          <div style={{ color: 'var(--text-secondary)' }}>Loading goals...</div>
        ) : goals.length === 0 ? (
          <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic', padding: '20px', textAlign: 'center', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>Buddy has no active goals right now. Give them something to do!</div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
            {goals.map((g, i) => (
              <div key={g.id || i} style={{ padding: '16px', background: 'rgba(0,0,0,0.4)', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontWeight: 600, color: 'white' }}>{g.title}</span>
                  <span style={{ fontSize: '0.8rem', padding: '2px 8px', borderRadius: '12px', background: g.status === 'active' ? 'var(--primary-accent)' : 'rgba(255,255,255,0.1)' }}>{g.status}</span>
                </div>
                {g.description && <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>{g.description}</div>}
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Progress</span>
                  <span>{Math.round(g.progress)}%</span>
                </div>
                <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px' }}>
                  <div style={{ width: `${g.progress}%`, height: '100%', background: 'var(--success)', borderRadius: '3px' }}></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Conversations */}
      <div className="glass" style={{ padding: '24px' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', marginBottom: '16px' }}>Recent Conversations</h3>
        {threads.length === 0 ? (
          <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic', padding: '20px', textAlign: 'center', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>No conversations yet.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {threads.slice(0, 5).map(t => (
              <div key={t.id} onClick={() => { onSelectThread(t.id); onNavigate('chat'); }} style={{ padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'white', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{t.title}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
