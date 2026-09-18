import { config } from './config.js';
export async function predict(imagePath) {
  const response = await fetch(`${config.bridgeUrl}/predict`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ image_path: imagePath }), signal: AbortSignal.timeout(Number(process.env.AI_BRIDGE_TIMEOUT_MS || 300000)) });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) { const error = new Error(body.error || 'Python AI bridge failed.'); error.statusCode = response.status >= 500 ? 503 : 422; throw error; }
  return body;
}