import React from 'react';
import { motion } from 'framer-motion';
import { usePersona } from '../../contexts/PersonaContext';

export function PersonaSwitcher() {
  const { persona, setPersona } = usePersona();

  return (
    <div className="flex bg-slate-100 dark:bg-slate-900 p-1 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-inner relative">
      <button
        type="button"
        className={`relative z-10 px-4 py-2 rounded-xl text-xs font-bold transition-colors duration-200 ${
          persona === 'EXECUTIVE'
            ? 'text-slate-900 dark:text-slate-100'
            : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-250'
        }`}
        onClick={() => setPersona('EXECUTIVE')}
      >
        {persona === 'EXECUTIVE' && (
          <motion.div
            layoutId="active-view-persona"
            className="absolute inset-0 bg-white dark:bg-slate-800 rounded-xl shadow-md border border-slate-200/50 dark:border-slate-700 -z-10"
            transition={{ type: 'spring', stiffness: 380, damping: 30 }}
          />
        )}
        Executive View
      </button>
      <button
        type="button"
        className={`relative z-10 px-4 py-2 rounded-xl text-xs font-bold transition-colors duration-200 ${
          persona === 'FORENSIC'
            ? 'text-slate-900 dark:text-slate-100'
            : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-255'
        }`}
        onClick={() => setPersona('FORENSIC')}
      >
        {persona === 'FORENSIC' && (
          <motion.div
            layoutId="active-view-persona"
            className="absolute inset-0 bg-white dark:bg-slate-800 rounded-xl shadow-md border border-slate-200/50 dark:border-slate-700 -z-10"
            transition={{ type: 'spring', stiffness: 380, damping: 30 }}
          />
        )}
        Forensic View
      </button>
    </div>
  );
}

export default PersonaSwitcher;
