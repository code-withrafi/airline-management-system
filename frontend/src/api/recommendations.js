// src/api/recommendations.js
import { api } from './client';

/**
 * Fetch route recommendations.
 * Sends the JWT automatically if the user is logged in (via client.js interceptor).
 * Returns anonymous popular routes when there's no valid token.
 */
export async function getRecommendations(topK = 3) {
  const { data } = await api.get('/api/ml/recommendations', {
    params: { top_k: topK },
  });
  return data;
}