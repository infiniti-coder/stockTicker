import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

/** Past turns for this browser's session — restored on every load, which is
 * what makes the chat panel "remember" a user across visits (see
 * app/session.py: same browser -> same session_id -> same history). */
export function useChatHistory() {
  return useQuery({
    queryKey: ["chat-history"],
    queryFn: api.getChatHistory,
  });
}
