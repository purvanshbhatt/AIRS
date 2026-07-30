import React from 'react';

export default function Settings() {
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Clinic Settings</h1>
      
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Clinic Profile</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Clinic Name</label>
            <input type="text" className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" defaultValue="Main Street Clinic" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">IT / MSP Email Contact</label>
            <input type="email" className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" defaultValue="support@localmsp.com" />
          </div>
        </div>
      </div>
    </div>
  );
}
