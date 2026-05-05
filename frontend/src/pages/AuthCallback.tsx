import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/client';
import toast from 'react-hot-toast';

export function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setToken } = useAuth();

  useEffect(() => {
    const code = searchParams.get('code');
    
    if (!code) {
      toast.error('No authorization code found');
      navigate('/login');
      return;
    }

    async function handleCallback() {
      try {
        const response = await authApi.googleCallback(code!);
        setToken(response.data.access_token);
        toast.success('Successfully logged in!');
        navigate('/');
      } catch (err) {
        console.error('OAuth callback failed:', err);
        toast.error('Authentication failed. Please try again.');
        navigate('/login');
      }
    }

    handleCallback();
  }, [searchParams, navigate, setToken]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-black">
      <div className="w-12 h-12 border-4 border-wonder-lime border-t-transparent rounded-full animate-spin mb-4" />
      <h1 className="text-xl font-bold text-white">Completing login...</h1>
    </div>
  );
}
