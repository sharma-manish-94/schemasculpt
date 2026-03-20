import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { authAPI } from "../api/authAPI";

function OAuth2RedirectHandler() {
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    const getTokenAndRedirect = async () => {
      try {
        // Call backend to get JWT token
        const data = await authAPI.getToken();

        // Login via context (stores token and user)
        login(data.token, {
          id: data.userId,
          username: data.username,
          email: data.email,
          avatarUrl: data.avatarUrl,
        });

        // Redirect to home page
        navigate("/");
      } catch (error) {
        console.error("OAuth redirect error:", error);
        navigate("/login?error=true");
      }
    };

    getTokenAndRedirect();
  }, [navigate, login]);

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
      }}
    >
      <div>Completing login...</div>
    </div>
  );
}

export default OAuth2RedirectHandler;
