import React from 'react';
import { motion } from 'framer-motion';
import { Network } from 'lucide-react';
import { NetworkMap } from '../../components/network/NetworkMap';

/**
 * Network Map: one page, one job. Everything drawn here comes from the
 * organisation's connected systems (see `app/services/network_topology.py`);
 * nothing on this page is illustrative.
 */
export function NetworkPage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-5 text-left"
    >
      <header className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-ready-emerald/30 bg-ready-emerald/15 text-ready-emerald">
          <Network className="h-5 w-5" aria-hidden />
        </div>
        <div className="min-w-0">
          <h1 className="text-2xl font-extrabold tracking-tight text-on-surface">Network Map</h1>
          <p className="mt-0.5 max-w-3xl text-sm text-on-surface-variant">
            Every device, network and VPN your connected systems can see, and how they join up. Turn it around, zoom
            in, and click anything to see what it is, what it is connected to and whether it needs attention.
          </p>
        </div>
      </header>

      <NetworkMap />
    </motion.div>
  );
}

export default NetworkPage;
