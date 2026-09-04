import { useState, useEffect, useCallback } from 'react';

export default function Memory({ user, companionId, API_BASE_URL, onClose }) {
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [adding, setAdding] = useState(false);
  const [newFact, setNewFact] = useState('');
  
  const [editingId, setEditingId] = useState(null);
  const [editFact, setEditFact] = useState('');

  const [confirmClear, setConfirmClear] = useState(false);

  const loadMemories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await user.getIdToken();
      const res = await fetch(`${API_BASE_URL}/api/memory/${companionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMemories(data.memories || []);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to load memories');
      }
    } catch(err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [user, companionId, API_BASE_URL]);

  useEffect(() => {
    // eslint-disable-next-line
    loadMemories();
  }, [loadMemories]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newFact.trim()) return;
    try {
      const token = await user.getIdToken();
      const res = await fetch(`${API_BASE_URL}/api/memory/${companionId}`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ fact: newFact.trim() })
      });
      if (res.ok) {
        setNewFact('');
        setAdding(false);
        loadMemories();
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to add memory');
      }
    } catch(err) {
      setError(err.message);
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    if (!editFact.trim() || !editingId) return;
    try {
      const token = await user.getIdToken();
      const res = await fetch(`${API_BASE_URL}/api/memory/${companionId}/${editingId}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ fact: editFact.trim() })
      });
      if (res.ok) {
        setEditingId(null);
        setEditFact('');
        loadMemories();
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to edit memory');
      }
    } catch(err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      const token = await user.getIdToken();
      const res = await fetch(`${API_BASE_URL}/api/memory/${companionId}/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setMemories(prev => prev.filter(m => m.id !== id));
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to delete memory');
      }
    } catch(err) {
      setError(err.message);
    }
  };

  const handleClearAll = async () => {
    try {
      const token = await user.getIdToken();
      const res = await fetch(`${API_BASE_URL}/api/memory/${companionId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setMemories([]);
        setConfirmClear(false);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to clear memories');
      }
    } catch(err) {
      setError(err.message);
    }
  };

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 100 }}>
      <div className="glass" style={{ width: '90%', maxWidth: '600px', maxHeight: '80vh', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', borderRadius: '16px' }}>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--glass-border)', paddingBottom: '12px' }}>
          <h2 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: '1.5rem' }}>Memory Center</h2>
          <button onClick={onClose} style={{ background: 'transparent', color: 'white', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
        </div>
        
        {error && (
          <div style={{ color: 'var(--danger)', fontSize: '0.9rem', background: 'rgba(255,50,50,0.1)', padding: '10px', borderRadius: '8px' }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button onClick={() => setAdding(!adding)} style={{ background: 'var(--primary-accent)', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer' }}>
            {adding ? 'Cancel' : '+ Add Memory'}
          </button>
          {memories.length > 0 && (
            confirmClear ? (
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span style={{ fontSize: '0.9rem', color: 'var(--danger)' }}>Are you sure?</span>
                <button onClick={handleClearAll} style={{ background: 'var(--danger)', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer' }}>Yes, clear all</button>
                <button onClick={() => setConfirmClear(false)} style={{ background: 'transparent', color: 'white', border: '1px solid var(--glass-border)', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
              </div>
            ) : (
              <button onClick={() => setConfirmClear(true)} style={{ background: 'transparent', color: 'var(--danger)', border: '1px solid var(--danger)', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer' }}>
                Clear All
              </button>
            )
          )}
        </div>

        {adding && (
          <form onSubmit={handleAdd} style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <input 
              type="text" 
              value={newFact} 
              onChange={e => setNewFact(e.target.value)} 
              placeholder="E.g., User prefers dark mode" 
              autoFocus
              style={{ flex: 1, padding: '10px', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', color: 'white' }} 
            />
            <button type="submit" style={{ background: 'var(--success)', color: 'white', border: 'none', padding: '10px 16px', borderRadius: '8px', cursor: 'pointer' }}>Save</button>
          </form>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1, overflowY: 'auto', marginTop: '12px' }}>
          {loading ? (
            <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '20px 0' }}>Loading memories...</p>
          ) : memories.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-secondary)' }}>
              <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🧠</div>
              <p>Buddy hasn't learned anything yet.</p>
              <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>Start chatting and Buddy can remember the things you choose to share.</p>
            </div>
          ) : (
            memories.sort((a,b) => b.created_at - a.created_at).map(m => (
              <div key={m.id} style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', border: '1px solid var(--glass-border)' }}>
                {editingId === m.id ? (
                  <form onSubmit={handleEdit} style={{ display: 'flex', gap: '8px' }}>
                    <input 
                      type="text" 
                      value={editFact} 
                      onChange={e => setEditFact(e.target.value)} 
                      autoFocus
                      style={{ flex: 1, padding: '8px', borderRadius: '6px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--primary-accent)', color: 'white' }} 
                    />
                    <button type="submit" style={{ background: 'var(--success)', color: 'white', border: 'none', padding: '8px 12px', borderRadius: '6px', cursor: 'pointer' }}>Save</button>
                    <button type="button" onClick={() => setEditingId(null)} style={{ background: 'transparent', color: 'white', border: '1px solid var(--glass-border)', padding: '8px 12px', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
                  </form>
                ) : (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <span style={{ fontSize: '0.95rem', lineHeight: '1.4' }}>{m.fact}</span>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button onClick={() => { setEditingId(m.id); setEditFact(m.fact); }} style={{ background: 'transparent', border: '1px solid var(--glass-border)', color: 'white', cursor: 'pointer', fontSize: '0.8rem', padding: '4px 8px', borderRadius: '4px' }}>Edit</button>
                        <button onClick={() => handleDelete(m.id)} style={{ background: 'transparent', border: '1px solid var(--danger)', color: 'var(--danger)', cursor: 'pointer', fontSize: '0.8rem', padding: '4px 8px', borderRadius: '4px' }}>Delete</button>
                      </div>
                    </div>
                    {m.created_at && (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        {new Date(m.created_at * 1000).toLocaleString()}
                      </span>
                    )}
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
