import { useState, useEffect, useRef } from 'react';
import { auth, signInWithEmailAndPassword, signOut, onAuthStateChanged } from './firebase';
import Onboarding from './pages/Onboarding';
import Memory from './components/Memory';
import Dashboard from './components/Dashboard';
import Settings from './components/Settings';

const API_BASE_URL = import.meta.env.VITE_BUDDY_API_BASE_URL || 'http://localhost:8000';

function ActionCard({ actionRaw, onConfirm }) {
  // Parses [OPEN: xxx] or [BROWSE: yyy]
  const match = actionRaw.match(/\[(OPEN|BROWSE):\s*(.+?)\]/i);
  if (!match) return null;
  const type = match[1].toUpperCase();
  const target = match[2];
  
  const icon = type === 'BROWSE' ? '🌐' : '🖥️';
  const actionText = type === 'BROWSE' ? `Open website: ${target}` : `Launch application: ${target}`;

  return (
    <div style={{ marginTop: '12px', background: 'rgba(0,0,0,0.4)', borderRadius: '12px', border: '1px solid var(--glass-border)', padding: '16px', overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <span style={{ fontSize: '1.2rem' }}>{icon}</span>
        <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Buddy wants to act</span>
      </div>
      <div style={{ marginBottom: '16px', fontSize: '0.95rem' }}>
        {actionText}
      </div>
      <div style={{ display: 'flex', gap: '8px' }}>
        <button onClick={() => onConfirm(true)} style={{ background: 'var(--success)', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, flex: 1 }}>Allow</button>
        <button onClick={() => onConfirm(false)} style={{ background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--glass-border)', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', flex: 1 }}>Deny</button>
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  
  const [view, setView] = useState('login'); 
  const [companionId, setCompanionId] = useState(null);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');

  // Dashboard State
  const [profile, setProfile] = useState({ name: "Loading...", species: "Unknown", rarity: "Unknown", energy: 0, mood: "Unknown", bond: 0, experience: 0 });
  const [stats, setStats] = useState({});
  const [chatMessage, setChatMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [messageState, setMessageState] = useState('idle'); // 'idle', 'sending', 'streaming', 'failed'
  
  const [threads, setThreads] = useState([]);
  const [activeThreadId, setActiveThreadId] = useState(null);
  
  const scrollRef = useRef(null);
  const wsRef = useRef(null);
  const streamingMessageRef = useRef(""); // Buffer for streaming text
  const actionBufferRef = useRef(null); // Buffer for detected action tags

  // Memory State
  const [memories, setMemories] = useState([]);
  const [showMemoryUI, setShowMemoryUI] = useState(false);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setAuthLoading(false);
    });
    return () => unsubscribe();
  }, []);

  // Effect removed, handled in Memory component

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory, messageState]);

  useEffect(() => {
    if (user) {
      setView('loading');
      user.getIdToken().then(async token => {
        try {
          const headers = { Authorization: `Bearer ${token}` };
          const res = await fetch(`${API_BASE_URL}/api/companions`, { headers });
          if (res.ok) {
            const data = await res.json();
            if (data.companions && data.companions.length > 0) {
              setCompanionId(data.companions[0].id);
              setView('dashboard');
            } else {
              setView('onboarding');
            }
          } else {
            setView('onboarding');
          }
        } catch(err) {
          console.error("Failed to fetch companions", err);
          setView('onboarding');
        }
      });
    } else {
      setView('login');
    }
  }, [user]);

  const loadThreadHistory = async (threadId, token) => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const chatRes = await fetch(`${API_BASE_URL}/api/chat/history?companion_id=${companionId}&thread_id=${threadId}`, { headers });
      if (chatRes.ok) {
        setChatHistory(await chatRes.json());
      }
    } catch(err) {
      console.error("Failed to load history", err);
    }
  };

  useEffect(() => {
    if (view === 'dashboard' && user && companionId) {
      user.getIdToken().then(async token => {
        try {
          const headers = { Authorization: `Bearer ${token}` };
          
          // Idempotent greeting
          await fetch(`${API_BASE_URL}/api/chat/greeting`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...headers },
            body: JSON.stringify({ message: "init", companion_id: companionId })
          }).catch(console.error);

          const [profRes, statsRes, threadsRes] = await Promise.all([
            fetch(`${API_BASE_URL}/api/profile?companion_id=${companionId}`, { headers }),
            fetch(`${API_BASE_URL}/api/stats?companion_id=${companionId}`, { headers }),
            fetch(`${API_BASE_URL}/api/chat/threads?companion_id=${companionId}`, { headers })
          ]);
          
          if (profRes.ok) setProfile(await profRes.json());
          if (statsRes.ok) setStats(await statsRes.json());
          
          if (threadsRes.ok) {
            const data = await threadsRes.json();
            setThreads(data.threads || []);
            if (data.threads && data.threads.length > 0) {
              setActiveThreadId(data.threads[0].id);
              loadThreadHistory(data.threads[0].id, token);
            }
          }
        } catch (err) {
          console.error("Failed to load dashboard data:", err);
        }

        // Initialize WebSocket
        const wsUrl = API_BASE_URL.replace(/^http/, 'ws') + `/ws`;
        wsRef.current = new WebSocket(wsUrl);
        
        wsRef.current.onopen = () => {
          wsRef.current.send(JSON.stringify({ type: "auth", token: token, companion_id: companionId }));
        };
        
        wsRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === "stream_chunk") {
              setMessageState('streaming');
              streamingMessageRef.current += data.chunk;
              
              // Frontend Action Parser: intercept [OPEN:...] and strip from UI
              let displayStr = streamingMessageRef.current;
              const match = displayStr.match(/\[(OPEN|BROWSE):\s*.+?\]/i);
              if (match) {
                actionBufferRef.current = match[0];
                displayStr = displayStr.replace(match[0], '');
              } else if (displayStr.includes('[')) {
                 // Partially typed tag? Let's aggressively strip incomplete tags if they look like an action
                 if (displayStr.match(/\[(O|OP|OPE|B|BR|BRO|BROW|BROWS)/i)) {
                    // Hide the typing bracket entirely until resolved
                    const idx = displayStr.lastIndexOf('[');
                    displayStr = displayStr.substring(0, idx);
                 }
              }

              setChatHistory(prev => {
                const newHist = [...prev];
                if (newHist.length > 0 && newHist[newHist.length-1].streaming) {
                  newHist[newHist.length-1].text = displayStr;
                  newHist[newHist.length-1].actionRaw = actionBufferRef.current;
                } else {
                  newHist.push({ sender: 'pet', text: displayStr, streaming: true, actionRaw: actionBufferRef.current });
                }
                return newHist;
              });
            } else if (data.type === "stream_complete") {
              setMessageState('idle');
              setChatHistory(prev => {
                const newHist = [...prev];
                if (newHist.length > 0 && newHist[newHist.length-1].streaming) {
                  newHist[newHist.length-1].streaming = false;
                  if (data.token) {
                    newHist[newHist.length-1].actionToken = data.token;
                  }
                }
                return newHist;
              });
              streamingMessageRef.current = "";
              actionBufferRef.current = null;
            } else if (data.type === "stream_error") {
              setMessageState('failed');
              setChatHistory(prev => [...prev, { sender: "pet", text: "[System: Connection error occurred.]" }]);
            }
          } catch(e) {
            console.error("WS Parse error", e);
          }
        };
        
        wsRef.current.onclose = () => {
          setMessageState('failed');
        };
      });
    }
    return () => { if (wsRef.current) wsRef.current.close(); };
  }, [view, user, companionId]);

  const handleCreateThread = async () => {
    try {
      const token = await user.getIdToken();
      const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
      const res = await fetch(`${API_BASE_URL}/api/chat/threads`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ message: "New Conversation", companion_id: companionId })
      });
      if (res.ok) {
        const data = await res.json();
        setThreads([{ id: data.thread_id, title: data.title }, ...threads]);
        setActiveThreadId(data.thread_id);
        setChatHistory([]); // Clear local chat feed
      }
    } catch(err) {
      console.error(err);
    }
  };

  const handleSelectThread = async (id) => {
    setActiveThreadId(id);
    setChatHistory([]);
    try {
      const token = await user.getIdToken();
      loadThreadHistory(id, token);
    } catch(e) {}
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (err) {
      setLoginError(err.message);
    }
  };

  const handleLogout = async () => {
    await signOut(auth);
    localStorage.removeItem('buddy_access_token');
    setView('login');
  };

  const sendChat = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim() || !activeThreadId) return;
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const userMsg = chatMessage.trim();
      setChatHistory(prev => [...prev, { sender: "user", text: userMsg }]);
      setChatMessage("");
      setMessageState('sending');
      streamingMessageRef.current = "";
      actionBufferRef.current = null;
      
      wsRef.current.send(JSON.stringify({ 
        type: "chat", 
        message: userMsg, 
        thread_id: activeThreadId 
      }));
      setProfile(prev => ({...prev, bond: prev.bond + 1, energy: Math.max(0, prev.energy - 1.5)}));
    } else {
      setChatHistory(prev => [...prev, { sender: "pet", text: "[System: WebSocket is disconnected. Please refresh.]" }]);
    }
  };

  const handleActionConfirm = async (allowed, index) => {
    const msg = chatHistory[index];
    if (!allowed) {
      setChatHistory(prev => {
        const newHist = [...prev];
        newHist[index].actionResult = "Action denied by user.";
        return newHist;
      });
      return;
    }

    try {
      const token = await user.getIdToken();
      const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
      const res = await fetch(`${API_BASE_URL}/api/chat/confirm_action`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          companion_id: companionId,
          token: msg.actionToken,
          action_raw: msg.actionRaw
        })
      });
      const data = await res.json();
      setChatHistory(prev => {
        const newHist = [...prev];
        if (res.ok) {
           newHist[index].actionResult = `Action permitted: ${data.message || 'Executed successfully'}`;
        } else {
           newHist[index].actionResult = `Action failed: ${data.detail || data.error || 'Unknown error'}`;
        }
        return newHist;
      });
    } catch (err) {
      setChatHistory(prev => {
        const newHist = [...prev];
        newHist[index].actionResult = `Action failed: Network error`;
        return newHist;
      });
    }
  };

  if (authLoading || view === 'loading') {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: 'white' }}>Initializing System...</div>;
  }

  if (view === 'login') {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div className="glass" style={{ padding: '40px', width: '100%', maxWidth: '400px', borderRadius: '16px' }}>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', textAlign: 'center', marginBottom: '8px' }}>FORGE <span style={{ color: 'var(--primary-accent)' }}>AI</span></h1>
          <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '32px' }}>Authentication Required</p>
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {loginError && <div style={{ color: 'var(--danger)', fontSize: '0.9rem', textAlign: 'center', background: 'rgba(255,50,50,0.1)', padding: '10px', borderRadius: '8px' }}>{loginError}</div>}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required style={{ width: '100%', padding: '12px', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', color: 'white' }} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required style={{ width: '100%', padding: '12px', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', color: 'white' }} />
            </div>
            <button type="submit" style={{ marginTop: '16px', padding: '14px', background: 'var(--primary-accent)', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>Initialize Connection</button>
          </form>
        </div>
      </div>
    );
  }

  if (view === 'onboarding') {
    return <Onboarding user={user} API_BASE_URL={API_BASE_URL} onComplete={(id) => {
      setCompanionId(id);
      setView('dashboard');
    }} />;
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1600px', margin: '0 auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2.5rem', fontWeight: 700, letterSpacing: '-1px' }}>
            FORGE <span style={{ color: 'var(--primary-accent)' }}>AI</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>DevBuddy Unified Web Control Center</p>
        </div>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div className="glass" style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)' }}></div>
            <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>System Active: {user.email}</span>
          </div>
          <button onClick={() => setShowMemoryUI(true)} className="glass" style={{ padding: '8px 16px', color: 'white', background: 'transparent', cursor: 'pointer', border: '1px solid var(--glass-border)' }}>
            Memory
          </button>
          <button onClick={handleLogout} className="glass" style={{ padding: '8px 16px', color: 'var(--danger)', background: 'transparent', cursor: 'pointer', border: '1px solid var(--danger)' }}>
            Disconnect
          </button>
        </div>
      </header>

      {/* Memory UI Overlay */}
      {showMemoryUI && (
        <Memory 
          user={user} 
          companionId={companionId} 
          API_BASE_URL={API_BASE_URL} 
          onClose={() => setShowMemoryUI(false)} 
        />
      )}

      {view === 'dashboard' && (
        <Dashboard 
          user={user} 
          companionId={companionId} 
          API_BASE_URL={API_BASE_URL} 
          profile={profile} 
          stats={stats} 
          threads={threads}
          onSelectThread={handleSelectThread}
          onNavigate={(newView) => {
            if (newView === 'memory') setShowMemoryUI(true);
            else setView(newView);
          }}
        />
      )}

      {view === 'settings' && (
        <Settings 
          user={user} 
          companionId={companionId} 
          API_BASE_URL={API_BASE_URL} 
          profile={profile} 
          onNavigate={(newView) => {
            if (newView === 'memory') setShowMemoryUI(true);
            else setView(newView);
          }}
        />
      )}

      {view === 'chat' && (
        <main style={{ display: 'grid', gridTemplateColumns: '240px 1fr 1.5fr', gap: '24px', height: '650px' }}>
          
          {/* Left Sidebar: Threads List */}
          <section className="glass" style={{ display: 'flex', flexDirection: 'column', padding: '20px', overflow: 'hidden' }}>
            <div style={{ borderBottom: '1px solid var(--glass-border)', paddingBottom: '12px', marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button onClick={() => setView('dashboard')} style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: 'none', borderRadius: '8px', padding: '4px 8px', cursor: 'pointer', fontSize: '0.8rem' }}>← Home</button>
              <span style={{ fontSize: '0.95rem', fontWeight: 600, letterSpacing: '0.5px', color: 'white' }}>Conversations</span>
              <button onClick={handleCreateThread} style={{ background: 'var(--primary-accent)', color: 'white', border: 'none', borderRadius: '50%', width: '28px', height: '28px', cursor: 'pointer', fontWeight: 'bold' }}>+</button>
            </div>
          
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', paddingRight: '4px' }}>
            {threads.map(t => (
              <div 
                key={t.id} 
                onClick={() => handleSelectThread(t.id)}
                style={{ 
                  padding: '12px', 
                  background: activeThreadId === t.id ? 'rgba(127, 90, 240, 0.2)' : 'transparent',
                  border: `1px solid ${activeThreadId === t.id ? 'var(--primary-accent)' : 'transparent'}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
              >
                <div style={{ fontSize: '0.9rem', color: activeThreadId === t.id ? 'white' : 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {t.title}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Center: Profile / Stats */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="glass" style={{ padding: '24px', position: 'relative', overflow: 'hidden' }}>
            <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
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
                <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.8rem', fontWeight: 600 }}>{profile.name}</h2>
                <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                  <span style={{ fontSize: '0.8rem', background: 'rgba(255,255,255,0.05)', padding: '3px 8px', borderRadius: '12px', color: 'var(--text-secondary)' }}>{profile.species}</span>
                </div>
                <div style={{ marginTop: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Energy</span>
                    <span style={{ fontWeight: 600 }}>{Math.round(profile.energy)}%</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${profile.energy}%`, height: '100%', background: 'var(--primary-accent)', borderRadius: '4px', transition: 'width 0.5s ease-in-out' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="glass" style={{ padding: '24px', flex: 1, overflowY: 'auto' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', marginBottom: '16px', fontWeight: 600 }}>Core Traits</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {Object.entries(stats).map(([key, val]) => (
                <div key={key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{key}</span>
                    <span style={{ fontWeight: 600 }}>{val}/100</span>
                  </div>
                  <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px' }}>
                    <div style={{ width: `${val}%`, height: '100%', background: 'linear-gradient(90deg, #7f5af0, #aa88ff)', borderRadius: '3px' }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Right: Chat Feed */}
        <section className="glass" style={{ display: 'flex', flexDirection: 'column', padding: '20px', overflow: 'hidden' }}>
          <div style={{ borderBottom: '1px solid var(--glass-border)', paddingBottom: '10px', marginBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 600, letterSpacing: '1px', color: 'var(--text-secondary)' }}>CONVERSATION FEED</span>
            {messageState === 'failed' && <span style={{ fontSize: '0.8rem', color: 'var(--danger)' }}>Connection Lost</span>}
          </div>
          
          <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px', paddingRight: '4px', marginBottom: '16px' }}>
            {chatHistory.map((msg, i) => (
              <div key={i} style={{ alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start', maxWidth: '85%' }}>
                <div style={{ 
                  padding: '12px 16px',
                  borderRadius: msg.sender === 'user' ? '12px 12px 0 12px' : '12px 12px 12px 0',
                  background: msg.sender === 'user' ? 'var(--primary-accent)' : 'rgba(255,255,255,0.05)',
                  fontSize: '0.95rem',
                  lineHeight: '1.4'
                }}>
                  {msg.text}
                </div>
                
                {/* Action Card Rendering */}
                {msg.sender === 'pet' && msg.actionRaw && !msg.actionResult && (
                  <ActionCard actionRaw={msg.actionRaw} onConfirm={(allowed) => handleActionConfirm(allowed, i)} />
                )}
                {msg.sender === 'pet' && msg.actionResult && (
                  <div style={{ marginTop: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    ↳ {msg.actionResult}
                  </div>
                )}
              </div>
            ))}
            
            {messageState === 'sending' && (
              <div style={{ alignSelf: 'flex-start', background: 'rgba(255,255,255,0.05)', padding: '10px 14px', borderRadius: '12px 12px 12px 0', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                <span className="typing-dots">Sending</span>
              </div>
            )}
          </div>

          <form onSubmit={sendChat} style={{ display: 'flex', gap: '12px' }}>
            <input 
              type="text" 
              value={chatMessage} 
              onChange={(e) => setChatMessage(e.target.value)} 
              placeholder={messageState === 'failed' ? 'Reconnecting...' : 'Talk to Buddy...'}
              disabled={messageState === 'failed' || messageState === 'sending' || messageState === 'streaming'}
              style={{
                flex: 1,
                background: 'rgba(0,0,0,0.2)',
                border: '1px solid var(--glass-border)',
                borderRadius: '12px',
                padding: '12px',
                color: 'white',
                fontFamily: 'var(--font-body)',
                fontSize: '0.95rem',
                outline: 'none',
                opacity: (messageState === 'failed' || messageState === 'sending') ? 0.5 : 1
              }}
            />
            <button 
              type="submit" 
              disabled={messageState === 'failed' || messageState === 'sending' || messageState === 'streaming'}
              style={{
                background: 'var(--primary-accent)',
                border: 'none',
                borderRadius: '12px',
                padding: '12px 24px',
                color: 'white',
                fontWeight: 600,
                cursor: 'pointer',
                opacity: (messageState === 'failed' || messageState === 'sending') ? 0.5 : 1
              }}>
              Send
            </button>
          </form>
        </section>
        </main>
      )}
    </div>
  );
}
