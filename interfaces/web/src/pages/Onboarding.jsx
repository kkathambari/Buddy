import { useState } from 'react';

export default function Onboarding({ user, onComplete, API_BASE_URL }) {
  const [step, setStep] = useState(1);

  // Companion Data
  const [onboardName, setOnboardName] = useState('Buddy');
  const [onboardSpecies, setOnboardSpecies] = useState('Ghost');
  const [onboardStats, setOnboardStats] = useState({
    Friendly: 50,
    Playful: 50,
    Curious: 50,
    Formal: 10,
    Sarcastic: 20,
    Energetic: 50
  });

  const nextStep = () => setStep(s => s + 1);
  const prevStep = () => setStep(s => Math.max(1, s - 1));

  const submitCompanion = async (e) => {
    e.preventDefault();
    try {
      const token = await user.getIdToken();
      const res = await fetch(`${API_BASE_URL}/api/companions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          name: onboardName,
          species: onboardSpecies,
          stats: onboardStats
        })
      });
      if (res.ok) {
        const data = await res.json();
        onComplete(data.id);
      } else {
        alert("Failed to create companion.");
      }
    } catch(err) {
      console.error(err);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', padding: 'var(--space-4)' }}>
      <div className="glass" style={{ padding: 'var(--space-6)', width: '100%', maxWidth: '500px', borderRadius: 'var(--radius-lg)', maxHeight: '90vh', overflowY: 'auto' }}>
        
        {step === 1 && (
          <div style={{ textAlign: 'center', animation: 'float 4s ease-in-out infinite' }}>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2.5rem', marginBottom: 'var(--space-2)' }}>Meet Buddy 🐾</h1>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-5)', lineHeight: 1.6 }}>
              Your personal AI companion that learns, remembers, and helps you get things done. 
              Buddy is highly secure, runs directly on your machine, and adapts to your workflow.
            </p>
            <button onClick={nextStep} style={{ padding: 'var(--space-3) var(--space-5)', background: 'var(--primary-accent)', color: 'white', border: 'none', borderRadius: 'var(--radius-sm)', fontWeight: 'bold', cursor: 'pointer', fontSize: '1.1rem' }}>
              Get Started →
            </button>
          </div>
        )}

        {step === 2 && (
          <div>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', textAlign: 'center', marginBottom: 'var(--space-2)' }}>Your Companion</h1>
            <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: 'var(--space-5)' }}>Create a new companion to journey with you.</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div>
                <label style={{ display: 'block', marginBottom: 'var(--space-2)', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>What's my name?</label>
                <input type="text" value={onboardName} onChange={(e) => setOnboardName(e.target.value)} required style={{ width: '100%', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', color: 'white' }} />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: 'var(--space-2)', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>What am I? (Species/Type)</label>
                <input type="text" value={onboardSpecies} onChange={(e) => setOnboardSpecies(e.target.value)} placeholder="e.g. Ghost, Robot, Dog" required style={{ width: '100%', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', color: 'white' }} />
              </div>
              <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
                <button onClick={prevStep} style={{ flex: 1, padding: 'var(--space-3)', background: 'transparent', color: 'white', border: '1px solid var(--glass-border)', borderRadius: 'var(--radius-sm)', cursor: 'pointer' }}>Back</button>
                <button onClick={nextStep} style={{ flex: 2, padding: 'var(--space-3)', background: 'var(--primary-accent)', color: 'white', border: 'none', borderRadius: 'var(--radius-sm)', fontWeight: 'bold', cursor: 'pointer' }}>Next</button>
              </div>
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', textAlign: 'center', marginBottom: 'var(--space-2)' }}>Make Buddy Yours</h1>
            <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: 'var(--space-5)' }}>Configure personality and communication style.</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              {Object.keys(onboardStats).map(stat => (
                <div key={stat}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-1)' }}>
                    <label style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{stat}</label>
                    <span style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>{onboardStats[stat]}</span>
                  </div>
                  <input 
                    type="range" 
                    min="0" max="100" 
                    value={onboardStats[stat]} 
                    onChange={(e) => setOnboardStats({...onboardStats, [stat]: parseInt(e.target.value)})}
                    style={{ width: '100%', accentColor: 'var(--primary-accent)' }}
                  />
                </div>
              ))}
              <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-3)' }}>
                <button onClick={prevStep} style={{ flex: 1, padding: 'var(--space-3)', background: 'transparent', color: 'white', border: '1px solid var(--glass-border)', borderRadius: 'var(--radius-sm)', cursor: 'pointer' }}>Back</button>
                <button onClick={nextStep} style={{ flex: 2, padding: 'var(--space-3)', background: 'var(--primary-accent)', color: 'white', border: 'none', borderRadius: 'var(--radius-sm)', fontWeight: 'bold', cursor: 'pointer' }}>Next</button>
              </div>
            </div>
          </div>
        )}

        {step === 4 && (
          <div>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', textAlign: 'center', marginBottom: 'var(--space-2)' }}>What Buddy Can Do</h1>
            <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: 'var(--space-5)' }}>Your companion has advanced capabilities.</p>
            
            <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', marginBottom: 'var(--space-5)' }}>
              <li style={{ background: 'rgba(255,255,255,0.05)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                <strong>💬 Conversation:</strong> Natural chat that adapts to your mood and energy.
              </li>
              <li style={{ background: 'rgba(255,255,255,0.05)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                <strong>🧠 Memory:</strong> Buddy remembers what's important to you over time.
              </li>
              <li style={{ background: 'rgba(255,255,255,0.05)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)' }}>
                <strong>🔐 Safe Automation:</strong> Buddy can control apps or the terminal, but <em>only when you explicitly approve</em>.
              </li>
            </ul>

            <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                <button onClick={prevStep} style={{ flex: 1, padding: 'var(--space-3)', background: 'transparent', color: 'white', border: '1px solid var(--glass-border)', borderRadius: 'var(--radius-sm)', cursor: 'pointer' }}>Back</button>
                <button onClick={submitCompanion} className="glowing" style={{ flex: 2, padding: 'var(--space-3)', background: 'var(--success)', color: 'white', border: 'none', borderRadius: 'var(--radius-sm)', fontWeight: 'bold', cursor: 'pointer' }}>Initialize Companion</button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
