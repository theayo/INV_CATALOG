"use client";

import { useEffect } from "react";

declare global {
  interface Window {
    Telegram?: {
      WebApp?: { ready: () => void; expand: () => void };
    };
  }
}

export default function Telegram() {
  useEffect(() => {
    window.Telegram?.WebApp?.ready();
    window.Telegram?.WebApp?.expand();
  }, []);
  return null;
}
