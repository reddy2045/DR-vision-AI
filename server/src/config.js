import 'dotenv/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
function required(name) { const value = process.env[name]; if (!value) throw new Error(`${name} is required`); return value; }

export const config = {
  port: Number(process.env.NODE_PORT || 4000),
  jwtSecret: required('JWT_SECRET'),
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || '8h',
  uploadDir: path.resolve(process.env.MEDIA_ROOT || path.join(root, 'media')),
  bridgeUrl: process.env.AI_BRIDGE_URL || 'http://127.0.0.1:5050',
  db: { host: process.env.DB_HOST || '127.0.0.1', port: Number(process.env.DB_PORT || 3306), user: process.env.DB_USER || 'root', password: process.env.DB_PASSWORD || '', database: process.env.DB_NAME || 'phc_db', waitForConnections: true, connectionLimit: Number(process.env.DB_CONNECTION_LIMIT || 10), charset: 'utf8mb4' },
};