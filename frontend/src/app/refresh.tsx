"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

export default function Refresh() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  return (
    <button className="refresh" disabled={pending} onClick={() => startTransition(() => router.refresh())}>
      {pending ? "Обновляем…" : "Обновить"}
    </button>
  );
}
