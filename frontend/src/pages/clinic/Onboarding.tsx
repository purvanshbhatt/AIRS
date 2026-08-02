import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const navigate = useNavigate();

  const handleNext = () => {
    if (step < 5) {
      setStep(step + 1);
    } else {
      // Finish onboarding and go to dashboard
      navigate('/clinic');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Welcome to ResilAI
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          The Morning Clinic Safety Check
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {step === 1 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Step 1: Create Account</h3>
              <p className="text-gray-500 mb-6">Let's get your clinic set up in just 2 minutes.</p>
              <button onClick={handleNext} className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                Continue
              </button>
            </div>
          )}

          {step === 2 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Step 2: Connect Email</h3>
              <p className="text-gray-500 mb-6">Connect Microsoft 365 or Google Workspace to monitor staff accounts.</p>
              <button onClick={handleNext} className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 mb-3">
                <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" className="w-5 h-5 mr-2" alt="Google" /> Connect Google Workspace
              </button>
              <button onClick={handleNext} className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                <img src="https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg" className="w-5 h-5 mr-2" alt="Microsoft" /> Connect Microsoft 365
              </button>
            </div>
          )}

          {step === 3 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Step 3: Install PC Checker</h3>
              <p className="text-gray-500 mb-6">Download this small app on your main clinic computers to monitor updates and encryption.</p>
              <button onClick={handleNext} className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                Download Installer
              </button>
            </div>
          )}

          {step === 4 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Step 4: Run First Scan</h3>
              <p className="text-gray-500 mb-6">We are analyzing your connected systems to build your first Morning Check...</p>
              <div className="flex justify-center mb-6">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
              <button onClick={handleNext} className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                Simulate Completion
              </button>
            </div>
          )}

          {step === 5 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">You're connected!</h3>
              <p className="text-gray-500 mb-6">Your first Morning Safety Check is ready. You will receive an email every morning at 7:30 AM.</p>
              <button onClick={handleNext} className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700">
                Go to Dashboard
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
