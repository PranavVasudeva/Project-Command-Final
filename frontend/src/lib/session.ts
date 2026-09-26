// Session boundary: auth is an httpOnly cookie the backend owns; the frontend's one
// duty is wiping the react-query cache so one account's data never renders for the next.
import { queryClient } from "./queryClient";
import { apiPost } from "./api";

// Call after every successful login/signup.
export function beginSession(): void {
  queryClient.clear();
}

// Call from every sign-out control; the hard redirect resets all in-memory state.
export async function endSession(redirectTo: string = "/login"): Promise<void> {
  window.dispatchEvent(new Event("kiit:signout"));
  if (import.meta.env.PROD) localStorage.removeItem("kiit-demo-user");
  // Stop live dashboard polling before the server revokes the cookie, otherwise a
  // refetch can race the logout response and briefly surface an expected 401.
  await queryClient.cancelQueries();
  try {
    await apiPost("/auth/logout");
  } finally {
    queryClient.clear();
    window.location.assign(redirectTo);
  }
}
