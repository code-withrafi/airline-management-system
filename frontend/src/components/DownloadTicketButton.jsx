// src/components/DownloadTicketButton.jsx
import { useState } from 'react';
import { motion } from 'framer-motion';
import { FiDownload, FiCheck } from 'react-icons/fi';
import { downloadTicket } from '../api/tickets';

/**
 * variant: 'primary' | 'outline' | 'small'
 */
export default function DownloadTicketButton({
  bookingId,
  reference,
  variant = 'primary',
  label = 'Download ticket',
}) {
  const [state, setState] = useState('idle');  // 'idle' | 'loading' | 'done' | 'error'
  const [error, setError] = useState('');

  const handleClick = async () => {
    setError('');
    setState('loading');
    try {
      await downloadTicket(bookingId, reference);
      setState('done');
      setTimeout(() => setState('idle'), 2200);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'Could not download the ticket.'
      );
      setState('error');
      setTimeout(() => setState('idle'), 3000);
    }
  };

  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    transition: 'background .15s, color .15s',
  };

  const variantStyles = {
    primary: {
      padding: '14px 24px',
      fontSize: 15,
      fontWeight: 600,
      background: '#2563eb',
      color: '#fff',
      border: 'none',
      borderRadius: 8,
      cursor: 'pointer',
    },
    outline: {
      padding: '14px 24px',
      fontSize: 15,
      fontWeight: 600,
      background: '#fff',
      color: '#2563eb',
      border: '1px solid #bfdbfe',
      borderRadius: 8,
      cursor: 'pointer',
    },
    small: {
      padding: '9px 14px',
      fontSize: 13,
      fontWeight: 600,
      background: '#fff',
      color: '#2563eb',
      border: '1px solid #bfdbfe',
      borderRadius: 8,
      cursor: 'pointer',
    },
  };

  const isDone = state === 'done';

  return (
    <div>
      <motion.button
        type="button"
        onClick={handleClick}
        disabled={state === 'loading'}
        whileHover={state === 'idle' ? { scale: 1.02 } : {}}
        whileTap={state === 'idle' ? { scale: 0.98 } : {}}
        style={{
          ...baseStyles,
          ...variantStyles[variant],
          ...(isDone ? { background: '#dcfce7', color: '#166534', borderColor: '#bbf7d0' } : {}),
        }}
      >
        {isDone ? (
          <>
            <FiCheck size={variant === 'small' ? 13 : 16} /> Downloaded
          </>
        ) : state === 'loading' ? (
          <>
            <motion.span
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              style={{
                display: 'inline-block',
                width: variant === 'small' ? 12 : 14,
                height: variant === 'small' ? 12 : 14,
                border: '2px solid currentColor',
                borderTopColor: 'transparent',
                borderRadius: '50%',
              }}
            />
            Preparing…
          </>
        ) : (
          <>
            <FiDownload size={variant === 'small' ? 13 : 16} /> {label}
          </>
        )}
      </motion.button>

      {error && (
        <div style={{
          color: '#991b1b', fontSize: 12,
          marginTop: 6, textAlign: 'center',
        }}>
          {error}
        </div>
      )}
    </div>
  );
}