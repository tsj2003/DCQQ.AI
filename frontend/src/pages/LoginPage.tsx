/**
 * Login page with Google OAuth sign-in.
 * Revamped with 'Wonder Makers' aesthetic.
 */

import { useAuth } from '../context/AuthContext';
import { Sparkles, FileText, MessageSquare, Play, Shield, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

export function LoginPage() {
  const { login, guestLogin } = useAuth();

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-black selection:bg-wonder-lime selection:text-black">
      {/* Dynamic Background Orbs */}
      <div className="absolute inset-0 z-0">
        <motion.div 
          animate={{ 
            scale: [1, 1.2, 1],
            x: [0, 50, 0],
            y: [0, -30, 0]
          }}
          transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
          className="orb orb-lime w-[500px] h-[500px] -top-20 -right-20 opacity-20" 
        />
        <motion.div 
          animate={{ 
            scale: [1.2, 1, 1.2],
            x: [0, -40, 0],
            y: [0, 40, 0]
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
          className="orb bg-wonder-accent w-[400px] h-[400px] -bottom-20 -left-20 opacity-20" 
        />
      </div>

      <div className="relative z-10 w-full max-w-[1200px] px-6 py-12 flex flex-col md:flex-row items-center gap-16">
        {/* Hero Section */}
        <div className="flex-1 text-center md:text-left">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-wonder-lime/10 border border-wonder-lime/20 text-wonder-lime text-xs font-bold uppercase tracking-widest mb-6">
              <Sparkles size={14} />
              <span>Future of Documentation</span>
            </div>
            <h1 className="text-6xl md:text-8xl font-black mb-8 leading-[0.9] tracking-tighter">
              HIGH-END DESIGN.<br />
              <span className="text-wonder-lime">CRAFTED CODE.</span>
            </h1>
            <p className="text-xl text-white/60 max-w-lg mb-10 font-medium">
              Interact with your PDFs, audio, and video files like never before. 
              Powered by GPT-4o & Whisper.
            </p>
            
            <div className="flex flex-wrap gap-4 justify-center md:justify-start">
              <div className="flex items-center gap-2 text-white/40 text-sm font-semibold">
                <Shield size={16} className="text-wonder-lime" />
                Enterprise Secure
              </div>
              <div className="w-1 h-1 rounded-full bg-white/20 my-auto" />
              <div className="flex items-center gap-2 text-white/40 text-sm font-semibold">
                <Play size={16} className="text-wonder-lime" />
                Instant Playback
              </div>
            </div>
          </motion.div>
        </div>

        {/* Login Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="w-full max-w-[420px]"
        >
          <div className="glass-panel p-10 rounded-[2rem] shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-wonder-lime/10 blur-3xl -mr-10 -mt-10 group-hover:bg-wonder-lime/20 transition-colors" />
            
            <div className="mb-10 text-center">
              <h2 className="text-3xl font-extrabold mb-2">Get Started</h2>
              <p className="text-white/50 text-sm">Sign in to your account to continue</p>
            </div>

            <div className="space-y-4 mb-10">
              {[
                { icon: <FileText size={18} />, text: "Analyze complex PDFs" },
                { icon: <MessageSquare size={18} />, text: "Smart Chat Q&A" },
                { icon: <Play size={18} />, text: "Timestamped sources" },
              ].map((f, i) => (
                <div key={i} className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-white/10 transition-all">
                  <div className="text-wonder-lime">{f.icon}</div>
                  <span className="text-sm font-semibold text-white/80">{f.text}</span>
                </div>
              ))}
            </div>

            <div className="space-y-4">
              <button 
                className="w-full h-14 rounded-2xl flex items-center px-4 gap-3 bg-white hover:bg-gray-50 transition-all shadow-lg group relative overflow-hidden active:scale-[0.98]"
                onClick={login}
                id="google-login-btn"
              >
                <div className="flex items-center justify-center w-8 h-8">
                  <svg viewBox="0 0 24 24" width="22" height="22">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                </div>
                <span className="text-black text-lg font-bold">Sign in with Google</span>
                <ArrowRight size={20} className="ml-auto text-black/20 group-hover:text-black group-hover:translate-x-1 transition-all" />
              </button>

              <button 
                className="btn btn-outline w-full h-14 rounded-2xl normal-case text-lg font-black gap-3 text-white border-white/20 hover:bg-white/10 hover:border-white/30"
                onClick={guestLogin}
                id="guest-login-btn"
              >
                Continue as Guest
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
