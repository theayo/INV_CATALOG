export type Product = {
  id: string;
  title: string;
  image_url: string;
  created_at: string;
};

export function apiUrl(path: string): string {
  const origin = process.env.API_BASE_URL ?? "http://localhost:8000";
  return `${origin.replace(/\/$/, "")}${path}`;
}

export async function getProducts(): Promise<Product[]> {
  const response = await fetch(apiUrl("/api/products"), {
    cache: "no-store",
    signal: AbortSignal.timeout(8000),
  });
  if (!response.ok) throw new Error("Catalog request failed");
  const products: Product[] = await response.json();
  if (!Array.isArray(products)) throw new Error("Invalid catalog response");
  return products;
}
