import React from 'react';
import clsx from 'clsx';

// ── Loading Spinner ───────────────────────────────────────────────────
export default function LoadingSpinner({ fullPage, size = 'md' }) {
  const sizes = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' };
  const spinner = (
    <div className={clsx(
      'border-2 border-primary-200 border-t-primary-600 rounded-full animate-spin',
      sizes[size]
    )} />
  );
  if (fullPage) return (
    <div className="fixed inset-0 flex items-center justify-center bg-white z-50">
      {spinner}
    </div>
  );
  return <div className="flex items-center justify-center p-8">{spinner}</div>;
}
