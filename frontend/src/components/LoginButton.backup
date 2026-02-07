import { useAuth0 } from '@auth0/auth0-react';
import React from 'react';

const LoginButton = () => {
  const { loginWithRedirect } = useAuth0();

  return (
    <button
      onClick={() => loginWithRedirect()}
      className="px-5 py-2 bg-white text-black font-medium text-sm rounded-full hover:bg-gray-100 transition-all hover:shadow-[0_0_20px_rgba(255,255,255,0.3)]"
    >
      Sign In
    </button>
  );
};

export default LoginButton;
