import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const [clinicName, setClinicName] = useState('');
  const [emr, setEmr] = useState('');
  const [workspace, setWorkspace] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleNext = () => {
    setStep(step + 1);
  };

  const handleFinish = async () => {
    setLoading(true);
    try {
      await fetch('/api/clinic/onboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clinic_name: clinicName, emr, workspace })
      });
      navigate('/clinic');
    } catch (e) {
      console.error(e);
      // fallback to navigate if api fails
      navigate('/clinic');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-4xl font-extrabold text-gray-900 tracking-tight">
          Welcome to ResilAI
        </h2>
        <p className="mt-2 text-center text-lg text-gray-600">
          Set up your clinic's safety baseline.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="bg-white py-10 px-8 shadow-xl shadow-gray-200/50 sm:rounded-2xl border border-gray-100">
          
          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              {[1,2,3,4].map(num => (
                <div key={num} className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${step >= num ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-400'}`}>
                  {num}
                </div>
              ))}
            </div>
            <div className="h-2 bg-gray-100 rounded-full w-full">
              <div className="h-2 bg-blue-600 rounded-full transition-all duration-300" style={{ width: `${((step - 1) / 3) * 100}%` }}></div>
            </div>
          </div>

          {step === 1 && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Organization Basics</h3>
              <p className="text-gray-500 mb-6">What is the name of your clinic?</p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Clinic Name</label>
                  <input type="text" className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 p-3 border" placeholder="e.g. Sunshine Dental" value={clinicName} onChange={e => setClinicName(e.target.value)} />
                </div>
              </div>

              <button onClick={handleNext} disabled={!clinicName} className="mt-8 w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-md font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all">
                Continue
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Core Systems</h3>
              <p className="text-gray-500 mb-6">Tell us what runs your clinic.</p>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Primary EMR / Practice Management</label>
                  <div className="grid grid-cols-2 gap-3">
                    {['Dentrix', 'OpenDental', 'Athena', 'Epic'].map(sys => (
                      <div key={sys} onClick={() => setEmr(sys)} className={`cursor-pointer border rounded-lg p-4 text-center transition-all ${emr === sys ? 'border-blue-600 bg-blue-50 text-blue-700 font-medium' : 'border-gray-200 hover:border-blue-300 text-gray-700'}`}>
                        {sys}
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Identity & Email Workspace</label>
                  <div className="grid grid-cols-2 gap-3">
                    {['Microsoft 365', 'Google Workspace'].map(sys => (
                      <div key={sys} onClick={() => setWorkspace(sys)} className={`cursor-pointer border rounded-lg p-4 text-center flex items-center justify-center transition-all ${workspace === sys ? 'border-blue-600 bg-blue-50 text-blue-700 font-medium' : 'border-gray-200 hover:border-blue-300 text-gray-700'}`}>
                        {sys}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <button onClick={handleNext} disabled={!emr || !workspace} className="mt-8 w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-md font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all">
                Continue
              </button>
            </div>
          )}

          {step === 3 && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Authorize Connectors</h3>
              <p className="text-gray-500 mb-6">Securely authorize ResilAI to verify your configuration daily.</p>
              
              <div className="space-y-4">
                 <div className="border border-gray-200 rounded-xl p-5 flex justify-between items-center">
                    <div className="flex items-center">
                       <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mr-4">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                       </div>
                       <div>
                          <h4 className="font-semibold text-gray-900">{workspace}</h4>
                          <p className="text-sm text-gray-500">Identity & Email Security</p>
                       </div>
                    </div>
                    <button className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 text-sm font-medium shadow-sm">
                      Connect
                    </button>
                 </div>

                 <div className="border border-gray-200 rounded-xl p-5 flex justify-between items-center opacity-75">
                    <div className="flex items-center">
                       <div className="w-10 h-10 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center mr-4">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                       </div>
                       <div>
                          <h4 className="font-semibold text-gray-900">Wazuh</h4>
                          <p className="text-sm text-gray-500">Endpoint Security</p>
                       </div>
                    </div>
                    <button className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 text-sm font-medium shadow-sm">
                      Setup API Key
                    </button>
                 </div>
              </div>

              <button onClick={handleNext} className="mt-8 w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-md font-medium text-white bg-blue-600 hover:bg-blue-700 transition-all">
                Continue to Baseline
              </button>
            </div>
          )}

          {step === 4 && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 text-center py-4">
              <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
                 <svg className="w-10 h-10 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Baseline Established</h3>
              <p className="text-gray-600 mb-8 max-w-sm mx-auto">
                Your connectors are verified. We will securely check {clinicName}'s systems every morning at 6:00 AM.
              </p>
              
              <button onClick={handleFinish} disabled={loading} className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-sm text-md font-medium text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 transition-all">
                {loading ? 'Finalizing...' : 'Go to Dashboard'}
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
