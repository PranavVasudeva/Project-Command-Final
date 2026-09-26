import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

export function useDispatchEvents() {
  const queryClient = useQueryClient();
  const [connected, setConnected] = useState(false);
  useEffect(() => {
    const source = new EventSource("/api/dispatch/events");
    source.addEventListener("connected", () => setConnected(true));
    source.addEventListener("dispatch", () => {
      setConnected(true);
      queryClient.invalidateQueries({ queryKey: ["dispatch"] });
    });
    source.onerror = () => setConnected(false);
    const closeForSignout = () => source.close();
    window.addEventListener("kiit:signout", closeForSignout);
    return () => { window.removeEventListener("kiit:signout", closeForSignout); source.close(); setConnected(false); };
  }, [queryClient]);
  return connected;
}