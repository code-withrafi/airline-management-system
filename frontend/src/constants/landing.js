import { FiZap, FiShield, FiDollarSign } from 'react-icons/fi';

export const DESTINATIONS = [
  { code: 'CXB', city: "Cox's Bazar", country: 'Bangladesh', color: '#38bdf8', image: '/destinations/cxb.png' },
  { code: 'SIN', city: 'Singapore',       country: 'Singapore', color: '#a78bfa', image: '/destinations/dac.png' },
  { code: 'BKK', city: 'Bangkok',     country: 'Thailand',   color: '#fb7185', image: '/destinations/bkk.png' },
  { code: 'CAN', city: 'Guangzhou',   country: 'China',      color: '#facc15', image: '/destinations/can.png' },
];

export const FEATURES = [
  { icon: FiZap,        title: 'Lightning fast', text: 'Search hundreds of flights in under a second.' },
  { icon: FiShield,     title: 'Secure booking', text: 'Your data is protected end-to-end.' },
  { icon: FiDollarSign, title: 'Best prices',    text: 'Transparent fares. No hidden fees. Ever.' },
];

export const HERO_STATS = [
  { number: '40+',  label: 'Destinations' },
  { number: '1M+',  label: 'Happy travelers' },
  { number: '4.9★', label: 'Average rating' },
];