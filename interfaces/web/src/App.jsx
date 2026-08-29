import React, { useState, useEffect, useRef } from 'react';

const API_BASE_URL = import.meta.env.VITE_BUDDY_API_BASE_URL || 'http://localhost:8000';
const COMPANION_ID = import.meta.env.VITE_BUDDY_COMPANION_ID || 'default_pet';

export default function App() {
  const [companionName, setCompanionName] = useState("Daemon");
  const [species, setSpecies] = useState("Ghost");
  const [rarity, setRarity] = useState("Rare");
  const [energy, setEnergy] = useState(85);
  const [mood, setMood] = useState("Happy");
  const [bond, setBond] = useState(45);
  const [experience, setExperience] = useState(12);
  const [chatMessage, setChatMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([
    { sender: "pet", text: "…I’m here. What are we building today?" }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef(null);

  // Stats
  const stats = {
    DEBUGGING: 75,
    PATIENCE: 30,
    CHAOS: 85,
    WISDOM: 90,
    SNARK: 95
  };

  // Hourly Productivity Mock Data
  const productivityData = [
    { hour: "9 AM", mins: 20, type: "coding" },
    { hour: "11 AM", mins: 45, type: "coding" },
    { hour: "1 PM", mins: 15, type: "browsing" },
    { hour: "3 PM", mins: 80, type: "coding" },
    { hour: "5 PM", mins: 60, type: "chatting" },
    { hour: "7 PM", mins: 90, type: "coding" },
    { hour: "9 PM", mins: 10, type: "other" }
  ];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory, isTyping]);

  // Handle Chat Input
  const sendChat = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;

    const userMsg = chatMessage.trim();
    setChatHistory(prev => [...prev, { sender: "user", text: userMsg }]);
    setChatMessage("");
    setIsTyping(true);

    try {
      const token = localStorage.getItem('buddy_access_token');
      if (!token) throw new Error("Authentication required");
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ message: userMsg, companion_id: COMPANION_ID })
      });
      if (response.ok) {
        const data = await response.json();
        setChatHistory(prev => [...prev, { sender: "pet", text: data.response }]);
        setBond(prev => prev + 1);
        setEnergy(prev => Math.max(0, prev - 1.5));
      } else {
        throw new Error("Offline");
      }
    } catch (err) {
      // Mock Fallback responses if server is offline
      setTimeout(() => {
        const mockResponses = [
          "Hmm… that looks like a subtle logic error.",
          "You're doing great. Don't forget to stretch.",
          "DELETE THE CODE 😈 (Just kidding, or am I?)",
          "Quiet suits you. Keep coding.",
          "Let's check the logs before changing anything else."
        ];
        const randomResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)];
        setChatHistory(prev => [...prev, { sender: "pet", text: randomResponse }]);
        setBond(prev => prev + 1);
      }, 1000);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto' }}>
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2.5rem', fontWeight: 700, letterSpacing: '-1px' }}>
            FORGE <span style={{ color: 'var(--primary-accent)' }}>AI</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>DevBuddy Unified Web Control Center</p>
        </div>
        <div className="glass" style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)' }}></div>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>System Active</span>
        </div>
      </header>

      {/* Main Grid */}
      <main style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        
        {/* Left Column: Pet Center & Stats */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Pet Center Widget */}
          <div className="glass" style={{ padding: '24px', position: 'relative', overflow: 'hidden' }}>
            <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
              
              {/* Animated CSS Ghost Avatar */}
              <div className="floating" style={{ position: 'relative', width: '120px', height: '140px' }}>
                <svg viewBox="0 0 100 120" style={{ width: '100%', height: '100%', fill: 'var(--primary-accent)', opacity: 0.85 }}>
                  <path d="M20,50 C20,20 80,20 80,50 C80,70 85,90 80,100 C75,95 70,105 60,100 C50,105 40,95 30,100 C20,105 25,95 20,100 C15,90 20,70 20,50 Z" />
                  <ellipse cx="40" cy="50" rx="6" ry="6" fill="#fff" />
                  <ellipse cx="60" cy="50" rx="6" ry="6" fill="#fff" />
                  <ellipse cx="40" cy="50" rx="3" ry="3" fill="#0f0c20" />
                  <ellipse cx="60" cy="50" rx="3" ry="3" fill="#0f0c20" />
                  <path d="M45,70 Q50,75 55,70" stroke="#fff" strokeWidth="3" fill="none" />
                </svg>
              </div>

              {/* Pet Info */}
              <div style={{ flex: 1 }}>
                <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.8rem', fontWeight: 600 }}>{companionName}</h2>
                <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                  <span style={{ fontSize: '0.8rem', background: 'rgba(255,255,255,0.05)', padding: '3px 8px', borderRadius: '12px', color: 'var(--text-secondary)' }}>
                    Species: {species}
                  </span>
                  <span style={{ fontSize: '0.8rem', background: 'rgba(127, 90, 240, 0.15)', color: 'var(--primary-accent)', padding: '3px 8px', borderRadius: '12px', fontWeight: 600 }}>
                    {rarity}
                  </span>
                </div>

                {/* Energy Bar */}
                <div style={{ marginTop: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Energy Meter</span>
                    <span style={{ fontWeight: 600 }}>{Math.round(energy)}%</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${energy}%`, height: '100%', background: 'var(--primary-accent)', borderRadius: '4px', transition: 'width 0.5s ease-in-out' }}></div>
                  </div>
                </div>
              </div>

            </div>

            {/* Quick Status Badges */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginTop: '24px', borderTop: '1px solid var(--glass-border)', paddingTop: '20px' }}>
              <div style={{ textAlign: 'center' }}>
                <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Mood</span>
                <span style={{ fontWeight: 600, color: 'var(--warning)', marginTop: '4px', display: 'block' }}>{mood}</span>
              </div>
              <div style={{ textAlign: 'center' }}>
                <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Affection Level</span>
                <span style={{ fontWeight: 600, color: 'var(--danger)', marginTop: '4px', display: 'block' }}>♥️ {bond}</span>
              </div>
              <div style={{ textAlign: 'center' }}>
                <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Level (XP)</span>
                <span style={{ fontWeight: 600, color: 'var(--success)', marginTop: '4px', display: 'block' }}>{experience}</span>
              </div>
            </div>
          </div>

          {/* Personality Stats Widget */}
          <div className="glass" style={{ padding: '24px' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', marginBottom: '16px', fontWeight: 600 }}>Core Traits</h3>
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

        {/* Right Column: Chat Console & Productivity Analytics */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Chat Console */}
          <div className="glass" style={{ height: '380px', display: 'flex', flexDirection: 'column', padding: '20px' }}>
            <div style={{ borderBottom: '1px solid var(--glass-border)', paddingBottom: '10px', marginBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 600, letterSpacing: '1px', color: 'var(--text-secondary)' }}>CONVERSATION FEED</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--primary-accent)' }}>Local Link</span>
            </div>
            
            {/* Message History */}
            <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', paddingRight: '4px', marginBottom: '16px' }}>
              {chatHistory.map((msg, i) => (
                <div key={i} style={{ 
                  alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '80%',
                  padding: '10px 14px',
                  borderRadius: msg.sender === 'user' ? '12px 12px 0 12px' : '12px 12px 12px 0',
                  background: msg.sender === 'user' ? 'var(--primary-accent)' : 'rgba(255,255,255,0.05)',
                  fontSize: '0.95rem'
                }}>
                  {msg.text}
                </div>
              ))}
              {isTyping && (
                <div style={{ alignSelf: 'flex-start', background: 'rgba(255,255,255,0.05)', padding: '10px 14px', borderRadius: '12px 12px 12px 0', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Daemon is typing...
                </div>
              )}
            </div>

            {/* Chat Input form */}
            <form onSubmit={sendChat} style={{ display: 'flex', gap: '12px' }}>
              <input 
                type="text" 
                value={chatMessage} 
                onChange={(e) => setChatMessage(e.target.value)} 
                placeholder="Talk to Daemon..." 
                style={{
                  flex: 1,
                  background: 'rgba(0,0,0,0.2)',
                  border: '1px solid var(--glass-border)',
                  borderRadius: '12px',
                  padding: '12px',
                  color: 'white',
                  fontFamily: 'var(--font-body)',
                  fontSize: '0.95rem',
                  outline: 'none'
                }}
              />
              <button type="submit" style={{
                background: 'var(--primary-accent)',
                border: 'none',
                borderRadius: '12px',
                padding: '12px 24px',
                color: 'white',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'background 0.2s'
              }}>
                Send
              </button>
            </form>
          </div>

          {/* Productivity Stats Widget */}
          <div className="glass" style={{ padding: '24px' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', marginBottom: '20px', fontWeight: 600 }}>Today's Productivity Metrics</h3>
            <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', height: '140px', paddingBottom: '10px' }}>
              {productivityData.map((data, i) => (
                <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '12%' }}>
                  <div style={{ 
                    height: `${(data.mins / 100) * 120}px`, 
                    width: '100%', 
                    background: data.type === 'coding' ? 'var(--primary-accent)' : data.type === 'browsing' ? 'var(--warning)' : 'var(--success)', 
                    borderRadius: '4px',
                    position: 'relative'
                  }}>
                    <span style={{ position: 'absolute', top: '-20px', left: '50%', transform: 'translateX(-50%)', fontSize: '0.75rem', fontWeight: 600 }}>{data.mins}m</span>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '8px' }}>{data.hour}</span>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '16px', marginTop: '16px', fontSize: '0.8rem', justifyContent: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '10px', height: '10px', background: 'var(--primary-accent)', borderRadius: '2px' }}></div>
                <span style={{ color: 'var(--text-secondary)' }}>Coding Work</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '10px', height: '10px', background: 'var(--warning)', borderRadius: '2px' }}></div>
                <span style={{ color: 'var(--text-secondary)' }}>Research / Browse</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '10px', height: '10px', background: 'var(--success)', borderRadius: '2px' }}></div>
                <span style={{ color: 'var(--text-secondary)' }}>Discussion</span>
              </div>
            </div>
          </div>

        </section>

      </main>
    </div>
  );
}
