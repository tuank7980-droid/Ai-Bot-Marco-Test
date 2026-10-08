/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useState } from 'react';

export default function App() {
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    const checkStatus = async () => {
      try {
        const res = await fetch('/api/state');
        if (res.ok && active) {
          setLoaded(true);
          return;
        }
      } catch {
        // waiting for python backend
      }
      if (active) setTimeout(checkStatus, 600);
    };
    checkStatus();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="w-screen h-screen bg-[#070c14] overflow-hidden flex flex-col m-0 p-0">
      {!loaded ? (
        <div className="flex-1 flex flex-col items-center justify-center text-[#738198] font-mono text-sm gap-3">
          <div className="w-8 h-8 border-2 border-[#62aaff] border-t-transparent rounded-full animate-spin"></div>
          <div>Đang khởi chạy Agent Lab (Spooksville Simulation)...</div>
        </div>
      ) : (
        <iframe
          src="/app-frame"
          className="w-full h-full border-0 flex-1"
          title="Agent Lab - Spooksville Map & Simulation"
        />
      )}
    </div>
  );
}
