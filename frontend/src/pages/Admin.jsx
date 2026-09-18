import { Edit3, Plus, RefreshCw, Search, ShieldCheck, UserCheck, UserX, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import PageHeader from '../components/PageHeader';
import { api } from '../services/api';

const emptyForm = { employee_id: '', full_name: '', role: 'PHC Worker', department: 'PHC', phone: '', email: '', is_active: true };

export default function Admin() {
  const [employees, setEmployees] = useState([]);
  const [stats, setStats] = useState({ total: 0, active: 0, inactive: 0, registered: 0, pending: 0 });
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function loadEmployees() {
    setLoading(true);
    setError('');
    try {
      const result = await api.adminEmployees({ q: query, status });
      setEmployees(result.employees);
      setStats(result.stats);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEmployees();
  }, [query, status]);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  function startEdit(employee) {
    setEditingId(employee.id);
    setForm({ ...employee });
    setNotice('');
  }

  function resetForm() {
    setEditingId(null);
    setForm(emptyForm);
  }

  function openAddModal() {
    resetForm();
    setShowAddModal(true);
  }

  async function saveEmployee(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setNotice('');
    try {
      if (editingId) {
        await api.updateEmployee(editingId, form);
        setNotice('Employee details updated.');
      } else {
        await api.createEmployee(form);
        setNotice('Employee added successfully.');
      }
      resetForm();
      setShowAddModal(false);
      await loadEmployees();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function toggleStatus(employee) {
    setError('');
    setNotice('');
    try {
      await api.updateEmployee(employee.id, { is_active: !employee.is_active });
      setNotice(`${employee.full_name} is now ${employee.is_active ? 'inactive' : 'active'}.`);
      await loadEmployees();
    } catch (err) {
      setError(err.message);
    }
  }

  return <>
    <PageHeader
      eyebrow="Administration"
      title="Employee management"
      description="Manage approved staff identities and access status for this PHC."
      action={<button className="button primary" onClick={openAddModal}><Plus size={17} /> Add employee</button>}
    />

    {error && <div className="form-error admin-feedback">{error}</div>}
    {notice && <div className="admin-success">{notice}</div>}

    <section className="admin-stats">
      <div><small>Total employees</small><strong>{stats.total}</strong></div>
      <div><small>Active</small><strong>{stats.active}</strong></div>
      <div><small>Registered</small><strong>{stats.registered}</strong></div>
      <div><small>Pending registration</small><strong>{stats.pending}</strong></div>
    </section>

    {showAddModal && <button type="button" className="admin-modal-backdrop" onClick={() => setShowAddModal(false)} aria-label="Close add employee dialog" />}

    <div className={`admin-layout ${!editingId && !showAddModal ? 'directory-only' : ''}`}>
      <form className={`card admin-form ${showAddModal ? 'admin-modal' : ''} ${!editingId && !showAddModal ? 'admin-form-hidden' : ''}`} onSubmit={saveEmployee} role={showAddModal ? 'dialog' : undefined} aria-modal={showAddModal ? 'true' : undefined}>
        <div className="section-heading compact-heading"><div><span className="eyebrow">{editingId ? 'Update record' : 'New record'}</span><h3>{editingId ? 'Edit employee' : 'Add employee'}</h3></div><div className="admin-form-heading-actions"><ShieldCheck size={20} />{showAddModal && <button type="button" className="icon-button" onClick={() => setShowAddModal(false)} aria-label="Close add employee dialog"><X size={17} /></button>}</div></div>
        <div className="admin-form-grid">
          <label>Employee ID<input name="employee_id" value={form.employee_id} onChange={updateField} required disabled={Boolean(editingId)} /></label>
          <label>Full name<input name="full_name" value={form.full_name} onChange={updateField} required /></label>
          <label>Role<input name="role" value={form.role} onChange={updateField} /></label>
          <label>Department<input name="department" value={form.department} onChange={updateField} /></label>
          <label>Phone<input name="phone" value={form.phone} onChange={updateField} /></label>
          <label>Email<input type="email" name="email" value={form.email} onChange={updateField} /></label>
        </div>
        <div className="button-row admin-form-actions"><button className="button primary" disabled={saving}>{saving ? 'Saving...' : editingId ? 'Save changes' : 'Create employee'}</button>{(editingId || showAddModal) && <button type="button" className="button secondary" onClick={() => { resetForm(); setShowAddModal(false); }}>Cancel</button>}</div>
      </form>

      <section className="card admin-directory">
        <div className="section-heading compact-heading"><div><span className="eyebrow">Directory</span><h3>Approved employees</h3></div><button className="icon-button" onClick={loadEmployees} aria-label="Refresh employees"><RefreshCw size={16} /></button></div>
        <div className="admin-filters"><label className="admin-search"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search employees" /></label><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All status</option><option value="active">Active</option><option value="inactive">Inactive</option><option value="registered">Registered</option><option value="pending">Pending registration</option></select></div>
        {loading ? <div className="admin-empty">Loading employees...</div> : employees.length === 0 ? <div className="admin-empty">No employees match this filter.</div> : <div className="employee-list">{employees.map((employee) => <div className="employee-row" key={employee.id}><div className="employee-avatar">{employee.full_name.split(' ').map((part) => part[0]).join('').slice(0, 2)}</div><div className="employee-main"><strong>{employee.full_name}</strong><small>{employee.employee_id} · {employee.role}</small></div><span className={`employee-state ${employee.is_active ? 'active' : 'inactive'}`}>{employee.is_active ? 'Active' : 'Inactive'}</span><span className={`employee-registration ${employee.is_registered ? 'registered' : ''}`}>{employee.is_registered ? 'Registered' : 'Pending'}</span><button className="icon-link" onClick={() => startEdit(employee)} aria-label={`Edit ${employee.full_name}`}><Edit3 size={16} /></button><button className="icon-link" onClick={() => toggleStatus(employee)} aria-label={`${employee.is_active ? 'Deactivate' : 'Activate'} ${employee.full_name}`}>{employee.is_active ? <UserX size={16} /> : <UserCheck size={16} />}</button></div>)}</div>}
      </section>
    </div>
  </>;
}
