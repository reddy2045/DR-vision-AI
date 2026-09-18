import mysql from 'mysql2/promise';
import { config } from './config.js';

export const pool = mysql.createPool(config.db);
export async function withTransaction(callback) {
  const connection = await pool.getConnection();
  try { await connection.beginTransaction(); const result = await callback(connection); await connection.commit(); return result; }
  catch (error) { await connection.rollback(); throw error; }
  finally { connection.release(); }
}