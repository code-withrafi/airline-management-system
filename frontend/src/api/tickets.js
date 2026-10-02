// src/api/tickets.js
import { api } from './client';

/**
 * Fetch the ticket PDF for a booking and trigger a browser download.
 * Uses axios so the JWT interceptor attaches the Authorization header.
 */
export async function downloadTicket(bookingId, reference = 'booking') {
  const response = await api.get(`/api/bookings/${bookingId}/ticket`, {
    responseType: 'blob',
  });

  // Try to honor a filename from Content-Disposition
  let filename = `ticket-${reference}.pdf`;
  const cd = response.headers['content-disposition'] || '';
  const match = cd.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
  if (match && match[1]) {
    filename = decodeURIComponent(match[1]);
  }

  // Turn the blob into a download
  const blob = new Blob([response.data], { type: 'application/pdf' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}