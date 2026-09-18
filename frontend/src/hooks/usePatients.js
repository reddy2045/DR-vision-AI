import { useCallback, useEffect, useState } from 'react';
import { api } from '../services/api';

export function usePatients() {
  const [patients, setPatients] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const refresh = useCallback(async () => { setLoading(true); setError(''); try { setPatients(await api.patients()); } catch (err) { setError(err.message); } finally { setLoading(false); } }, []);
  useEffect(() => { refresh(); }, [refresh]);
  return { patients, loading, error, refresh };
}
