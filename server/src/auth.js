import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { config } from './config.js';
import { pool } from './db.js';

export function issueToken(user) { return jwt.sign({ sub: user.id, employeeId: user.employee_id, role: user.role }, config.jwtSecret, { expiresIn: config.jwtExpiresIn }); }
export async function authenticate(req, res, next) {
  const header = req.get('authorization') || '';
  if (!header.startsWith('Bearer ')) return res.status(401).json({ error: 'Bearer token is required.' });
  try {
    const claims = jwt.verify(header.slice(7), config.jwtSecret);
    const [rows] = await pool.execute('SELECT id, employee_id, full_name, email, role, is_active FROM api_users WHERE id = ?', [claims.sub]);
    if (!rows[0] || !rows[0].is_active) return res.status(401).json({ error: 'Account is inactive.' });
    req.user = rows[0]; next();
  } catch { return res.status(401).json({ error: 'Invalid or expired token.' }); }
}
export async function createUser({ employeeId, fullName, email, password, role = 'PHC Worker' }) {
  const passwordHash = await bcrypt.hash(password, 12);
  const [result] = await pool.execute('INSERT INTO api_users (employee_id, full_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)', [employeeId, fullName, email, passwordHash, role]);
  return { id: result.insertId, employee_id: employeeId, full_name: fullName, email, role };
}
export async function findUserByLogin(login) { const [rows] = await pool.execute('SELECT * FROM api_users WHERE employee_id = ? OR email = ? LIMIT 1', [login, login]); return rows[0]; }
export { bcrypt };