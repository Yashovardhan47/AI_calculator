import { useEffect, useRef, useState } from "react";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

export default function GoogleSignIn({ onCredential, disabled }) {
  const container = useRef(null);
  const credentialHandler = useRef(onCredential);
  const [unavailable, setUnavailable] = useState(!GOOGLE_CLIENT_ID);
  credentialHandler.current = onCredential;

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || disabled) return undefined;
    let cancelled = false;
    function render() {
      if (cancelled || !window.google?.accounts?.id || !container.current) return;
      window.google.accounts.id.initialize({ client_id: GOOGLE_CLIENT_ID, callback: (response) => credentialHandler.current(response.credential) });
      container.current.innerHTML = "";
      window.google.accounts.id.renderButton(container.current, { theme: "filled_black", size: "large", shape: "pill", width: 320, text: "continue_with" });
      setUnavailable(false);
    }
    if (window.google?.accounts?.id) {
      render();
      return () => { cancelled = true; };
    }
    let script = document.getElementById("google-identity-services");
    const handleError = () => setUnavailable(true);
    if (!script) {
      script = document.createElement("script");
      script.id = "google-identity-services";
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    }
    script.addEventListener("load", render);
    script.addEventListener("error", handleError);
    return () => {
      cancelled = true;
      script.removeEventListener("load", render);
      script.removeEventListener("error", handleError);
    };
  }, [disabled]);

  if (unavailable) return <p className="google-unavailable">Google sign-in becomes available after adding the Google Client ID.</p>;
  return <div className="google-button" ref={container} aria-label="Continue with Google" />;
}
