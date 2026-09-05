import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";

export function LoginButton() {
  const queryClient = useQueryClient();
  const { data: status } = useQuery({ queryKey: ["auth-status"], queryFn: api.authStatus });

  if (!status) return null;

  if (status.logged_in) {
    return (
      <div className="login-status">
        <span className="badge badge-live">
          {status.is_mock ? "Mock session" : "Logged in to Upstox"}
        </span>
        <button
          onClick={async () => {
            await api.logout();
            queryClient.invalidateQueries({ queryKey: ["auth-status"] });
          }}
        >
          Log out
        </button>
      </div>
    );
  }

  return (
    <a className="login-button" href={api.loginUrl()}>
      Login with Upstox
    </a>
  );
}
