import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import multer from 'multer';
import { config } from './config.js';
import { pool, withTransaction } from './db.js';
import { authenticate, bcrypt, createUser, findUserByLogin, issueToken } from './auth.js';
import { predict } from './aiBridge.js';

const app = express();
const upload = multer({
  storage: multer.diskStorage({
    destination: path.join(config.uploadDir, 'fundus'),
    filename: (_req, file, callback) => callback(null, `${crypto.randomUUID()}${path.extname(file.originalname).toLowerCase()}`),
  }),
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (_req, file, callback) => callback(null, ['image/jpeg', 'image/png'].includes(file.mimetype)),
});
app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN?.split(',').map((value) => value.trim()) || true }));
app.use(express.json({ limit: '1mb' }));
app.use('/media', express.static(config.uploadDir));

const publicFileUrl = (filePath) => filePath ? `/media/${path.relative(config.uploadDir, filePath).replaceAll(path.sep, '/')}` : null;
const asPatient = (row) => ({ id: row.id, first_name: row.first_name, last_name: row.last_name, patient_id: row.patient_id, age: row.age, gender: row.gender });

app.get('/health', async (_req, res) => {
  try {
    await pool.query('SELECT 1');
    const bridge = await fetch(`${config.bridgeUrl}/health`, { signal: AbortSignal.timeout(3000) });
    if (!bridge.ok) throw new Error('AI bridge is unavailable');
    res.json({ status: 'ok', database: 'ok', ai: 'ok' });
  } catch { res.status(503).json({ status: 'unavailable', database: 'or AI bridge unavailable' }); }
});
app.post('/api/auth/register', async (req, res, next) => { try { const { employee_id: employeeId, full_name: fullName, email, password } = req.body; if (!employeeId || !fullName || !email || !password || password.length < 8) return res.status(400).json({ error: 'employee_id, full_name, email and an 8-character password are required.' }); const user = await createUser({ employeeId, fullName, email, password }); res.status(201).json({ user, token: issueToken(user) }); } catch (error) { next(error); } });
app.post('/api/auth/login', async (req, res, next) => { try { const user = await findUserByLogin(String(req.body.login || '').trim()); if (!user || !user.is_active || !(await bcrypt.compare(String(req.body.password || ''), user.password_hash))) return res.status(401).json({ error: 'Invalid credentials.' }); const safeUser = { id: user.id, employee_id: user.employee_id, full_name: user.full_name, email: user.email, role: user.role }; res.json({ user: safeUser, token: issueToken(safeUser) }); } catch (error) { next(error); } });
app.get('/api/patients', authenticate, async (_req, res, next) => { try { const [rows] = await pool.query('SELECT id, first_name, last_name, patient_id, age, gender FROM api_patients ORDER BY created_at DESC'); res.json(rows.map(asPatient)); } catch (error) { next(error); } });
app.get('/api/screening/:patientId', authenticate, async (req, res, next) => { try { const [rows] = await pool.execute('SELECT p.*, s.* FROM api_screenings s JOIN api_patients p ON p.id = s.patient_id WHERE p.patient_id = ? ORDER BY s.created_at DESC LIMIT 1', [req.params.patientId]); if (!rows[0]) return res.status(404).json({ error: 'No screening found' }); res.json(formatScreening(rows[0])); } catch (error) { next(error); } });
app.post('/api/create_screening', authenticate, upload.single('fundus_image'), async (req, res, next) => {
  if (!req.file) return res.status(400).json({ error: 'A JPG, JPEG, or PNG fundus_image is required.' });
  const imagePath = req.file.path;
  let gradcamPath;
  try {
    const quality = await predictQuality(imagePath); if (!quality.passed) { await fs.rm(imagePath, { force: true }); return res.status(422).json({ error: quality.message, quality_metrics: quality.metrics || {} }); }
    const result = await predict(imagePath); gradcamPath = result.gradcam_path || null; const patientName = String(req.body.patientName || '').trim(); const names = patientName ? patientName.split(/\s+/, 2) : [req.body.first_name, req.body.last_name];
    if (!names[0] || !req.body.patient_id) { await fs.rm(imagePath, { force: true }); return res.status(400).json({ error: 'patientName and patient_id are required.' }); }
    const saved = await withTransaction(async (connection) => { const [patientResult] = await connection.execute('INSERT INTO api_patients (first_name, last_name, patient_id, age, gender, diabetes_duration, hba1c) VALUES (?, ?, ?, ?, ?, ?, ?)', [names[0], names[1] || '', req.body.patient_id, Number(req.body.age || 0), req.body.gender || 'M', Number(req.body.diabetes_duration || 0), Number(req.body.hba1c || 0)]); const [screeningResult] = await connection.execute('INSERT INTO api_screenings (patient_id, eye_side, fundus_path, gradcam_path, predicted_class, dr_level, confidence, referable, low_confidence, quality_passed, quality_metrics, quality_message, referral_urgency) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [patientResult.insertId, req.body.eye_side || 'OD', imagePath, gradcamPath, result.predicted_class, result.dr_level, result.confidence, result.referable, result.low_confidence, true, JSON.stringify(quality.metrics), quality.message, result.referral_urgency]); return { id: screeningResult.insertId }; });
    res.status(201).json({ id: saved.id, screening_id: saved.id, patient_id: req.body.patient_id, image_url: publicFileUrl(imagePath), gradcam_url: publicFileUrl(gradcamPath), ...result });
  } catch (error) { await fs.rm(imagePath, { force: true }); if (gradcamPath) await fs.rm(gradcamPath, { force: true }); next(error); }
});
app.get('/api/referral/:screeningId', authenticate, async (req, res, next) => { try { const [rows] = await pool.execute('SELECT p.*, s.* FROM api_screenings s JOIN api_patients p ON p.id = s.patient_id WHERE s.id = ?', [req.params.screeningId]); if (!rows[0]) return res.status(404).json({ error: 'Screening not found' }); res.json({ ...formatScreening(rows[0]), slip_number: `REF-${Number(req.params.screeningId).toString().padStart(4, '0')}` }); } catch (error) { next(error); } });

async function predictQuality(imagePath) { const response = await fetch(`${config.bridgeUrl}/quality`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ image_path: imagePath }), signal: AbortSignal.timeout(30000) }); const body = await response.json().catch(() => ({})); if (!response.ok) { const error = new Error(body.error || 'Python AI bridge failed.'); error.statusCode = response.status >= 500 ? 503 : 422; throw error; } return body; }
function formatScreening(row) { return { screening_id: row.id, screening_date: row.created_at, patient_name: `${row.first_name} ${row.last_name}`.trim(), patient_id: row.patient_id, age: row.age, gender: row.gender, diabetes_duration: row.diabetes_duration, hba1c: Number(row.hba1c), eye_side: row.eye_side, predicted_class: row.predicted_class, ai_diagnosis: row.predicted_class, dr_level: row.dr_level, confidence: Number(row.confidence), referable: Boolean(row.referable), low_confidence: Boolean(row.low_confidence), quality_passed: Boolean(row.quality_passed), quality_metrics: typeof row.quality_metrics === 'string' ? JSON.parse(row.quality_metrics) : row.quality_metrics, quality_message: row.quality_message, findings: {}, referral_urgency: row.referral_urgency, image_url: publicFileUrl(row.fundus_path), gradcam_url: publicFileUrl(row.gradcam_path), fov: '45°' }; }
app.use((error, _req, res, _next) => { const status = error.statusCode || (error.code === 'ER_DUP_ENTRY' ? 409 : 500); res.status(status).json({ error: status === 500 ? 'Internal server error.' : error.message }); });
app.listen(config.port, () => console.log(`PHC REST API listening on http://127.0.0.1:${config.port}`));