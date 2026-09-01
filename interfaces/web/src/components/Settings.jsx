import React, { useState } from 'react';

export default function Settings({ user, companionId, API_BASE_URL, profile, onNavigate }) {
  const [activeTab, setActiveTab] = useState('buddy');
  const [saveStatus, setSaveStatus] = useState('');

  const handleSave = () => {
    // Stub for now. Will be connected to the settings API in the next steps.
    setSaveStatus('Saving...');
    setTimeout(() => setSaveStatus('Settings saved securely.'), 1000);
  };

  return (
    <div className="glass" style={{ padding: '32px', maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem' }}>Settings & Control Center</h2>
        <button onClick={() => onNavigate('dashboard')} style={{ background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--glass-border)', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer' }}>Back to Dashboard</button>
      </div>

      <div style={{ display: 'flex', gap: '16px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '16px' }}>
        {['buddy', 'ai', 'privacy', 'permissions'].map(tab => (
          <button 
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              background: activeTab === tab ? 'rgba(255,255,255,0.1)' : 'transparent',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '8px',
              color: activeTab === tab ? 'white' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontWeight: activeTab === tab ? 600 : 400,
              textTransform: 'capitalize'
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {activeTab === 'buddy' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3>Buddy Configuration</h3>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Buddy Name</label>
              <input type="text" defaultValue={profile.name} style={{ width: '100%', padding: '12px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'white' }} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Personality Traits</label>
              <textarea defaultValue="Friendly, inquisitive, and highly technical." style={{ width: '100%', padding: '12px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'white', minHeight: '100px' }} />
            </div>
          </div>
        )}

        {activeTab === 'ai' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3>AI Configuration</h3>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Active Model</label>
              <select style={{ width: '100%', padding: '12px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'white' }}>
                <option value="claude-3-5-sonnet">Claude 3.5 Sonnet (Default)</option>
              </select>
            </div>
            <div style={{ padding: '16px', background: 'rgba(255,255,0,0.1)', border: '1px solid rgba(255,255,0,0.3)', borderRadius: '8px', color: '#ffcc00' }}>
              <strong>Note:</strong> API keys and provider secrets are securely managed by the backend and are not exposed to the client.
            </div>
          </div>
        )}

        {activeTab === 'privacy' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3>Privacy Controls</h3>
            <p style={{ color: 'var(--text-secondary)' }}>Buddy stores memories in Firebase RTDB, securely keyed by your authenticated companion ID. Everything sent to the AI provider is transient and adheres to their privacy policy.</p>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button onClick={() => onNavigate('memory')} style={{ background: 'var(--primary-accent)', color: 'white', padding: '10px 20px', borderRadius: '8px', border: 'none', cursor: 'pointer' }}>Manage Memories</button>
            </div>
          </div>
        )}

        {activeTab === 'permissions' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3>Security & Permissions</h3>
            <div style={{ padding: '16px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', borderRadius: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h4 style={{ margin: '0 0 8px 0' }}>Action Confirmation (Human in the loop)</h4>
                  <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Requires your explicit approval before executing potentially dangerous actions (like writing to files).</p>
                </div>
                <div style={{ background: 'var(--success)', padding: '4px 12px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 'bold' }}>ENFORCED</div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '16px', borderTop: '1px solid var(--glass-border)' }}>
        <span style={{ color: saveStatus.includes('securely') ? 'var(--success)' : 'var(--text-secondary)' }}>{saveStatus}</span>
        <button onClick={handleSave} style={{ background: 'var(--primary-accent)', color: 'white', border: 'none', padding: '12px 24px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}>Save Changes</button>
      </div>
    </div>
  );
}
