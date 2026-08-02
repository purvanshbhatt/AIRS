import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';

export default function ClinicLayout() {
  const location = useLocation();
  const navItems = [
    { path: '/clinic', label: 'Home' },
    { path: '/clinic/integrations', label: 'Integrations' },
    { path: '/clinic/settings', label: 'Settings' }
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-64 bg-white border-r border-gray-200">
        <div className="p-6">
          <h1 className="text-xl font-bold text-gray-900">ResilAI</h1>
          <p className="text-sm text-gray-500">Clinic Safety Manager</p>
        </div>
        <nav className="mt-6">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`block px-6 py-3 text-sm ${location.pathname === item.path ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto p-8">
        <Outlet />
      </main>
    </div>
  );
}
