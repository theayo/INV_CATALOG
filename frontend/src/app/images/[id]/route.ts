import { apiUrl } from "@/lib/catalog";

export async function GET(_request: Request, context: RouteContext<"/images/[id]">) {
  const { id } = await context.params;
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) {
    return new Response(null, { status: 404 });
  }
  try {
    const response = await fetch(apiUrl(`/api/products/${id}/image`), {
      cache: "no-store",
      signal: AbortSignal.timeout(15000),
    });
    if (!response.ok) return new Response(null, { status: response.status });
    return new Response(response.body, {
      headers: {
        "Content-Type": response.headers.get("Content-Type") ?? "image/jpeg",
        "Cache-Control": "public, max-age=3600",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch {
    return new Response(null, { status: 503 });
  }
}
