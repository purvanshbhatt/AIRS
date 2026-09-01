import re

with open(r'P:\projects\AIRS\frontend\src\pages\Landing.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace colors
content = content.replace('blue-', 'primary-')
content = content.replace('cyan-', 'emerald-')

# Replace texts
content = content.replace('AI Security Readiness', 'Operational Readiness Platform')
content = content.replace('Cybersecurity Posture', 'Operational Readiness Posture')
content = content.replace('Launch Sandbox Demo', 'Enter Sandbox')
content = content.replace('Start Free Assessment', 'Enter Sandbox')

# Import useAuth and useNavigate
if 'import { useAuth }' not in content:
    content = content.replace("import { Link } from 'react-router-dom';", "import { Link, useNavigate } from 'react-router-dom';\nimport { useAuth } from '../contexts/AuthContext';")

# Add handleEnterSandbox to Landing component
hook_str = '''
export default function Landing() {
  const navigate = useNavigate();
  const { signInWithGoogle, clearError } = useAuth();

  const handleEnterSandbox = async () => {
    clearError();
    try {
      await signInWithGoogle();
      navigate("/dashboard", { replace: true });
    } catch {
      // Error handled by AuthContext
    }
  };
'''
content = content.replace('export default function Landing() {', hook_str)

# Replace the specific links with buttons
content = content.replace('<Link\n                to="/dashboard"', '<button\n                onClick={handleEnterSandbox}')
content = content.replace('<Link\n              to="/assessment/quick"', '<button\n              onClick={handleEnterSandbox}')

# In React, change </Link> to </button> for those specific buttons
content = content.replace('Enter Sandbox\n                <ArrowRight className="w-4 h-4 text-slate-400" />\n              </Link>', 'Enter Sandbox\n                <ArrowRight className="w-4 h-4 text-slate-400" />\n              </button>')
content = content.replace('Enter Sandbox\n              <ArrowRight className="w-5 h-5" />\n            </Link>', 'Enter Sandbox\n              <ArrowRight className="w-5 h-5" />\n            </button>')

# For the top right "Get Started" link
content = content.replace('<Link\n                to="/assessment/quick"\n                className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-950 text-sm font-semibold rounded-xl hover:bg-slate-800 dark:hover:bg-slate-200 transition-all shadow-sm"\n              >\n                Get Started\n                <ArrowRight className="w-4 h-4" />\n              </Link>', '<button\n                onClick={handleEnterSandbox}\n                className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-950 text-sm font-semibold rounded-xl hover:bg-slate-800 dark:hover:bg-slate-200 transition-all shadow-sm"\n              >\n                Enter Sandbox\n                <ArrowRight className="w-4 h-4" />\n              </button>')

with open(r'P:\projects\AIRS\frontend\src\pages\Landing.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
