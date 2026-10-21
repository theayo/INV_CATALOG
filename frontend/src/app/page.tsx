import { getProducts, type Product } from "@/lib/catalog";
import Refresh from "./refresh";

export const dynamic = "force-dynamic";

export default async function Home() {
  let products: Product[] | null;
  try {
    products = await getProducts();
  } catch {
    products = null;
  }

  return (
    <main>
      <header className="catalog-header">
        <div>
          <p className="eyebrow">INVIX</p>
          <h1>Каталог</h1>
        </div>
        <Refresh />
      </header>

      {products === null ? (
        <section className="notice" role="alert">
          <h2>Не удалось загрузить каталог</h2>
          <p>Попробуйте обновить страницу чуть позже.</p>
        </section>
      ) : products.length === 0 ? (
        <section className="notice">
          <h2>Пока нет товаров</h2>
          <p>Добавленные через бота товары появятся здесь.</p>
        </section>
      ) : (
        <ul className="products" aria-label="Товары">
          {products.map((product) => (
            <li key={product.id} className="product">
              <img
                src={`/images/${product.id}`}
                alt={product.title}
                width={640}
                height={480}
                loading="lazy"
              />
              <h2>{product.title}</h2>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
