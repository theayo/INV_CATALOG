import type { Metadata } from "next";
import Script from "next/script";
import Telegram from "./telegram";
import "./globals.css";

export const metadata: Metadata = {
  title: "INVIX — Каталог",
  description: "Каталог товаров INVIX",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ru">
      <body>
        <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
        <Telegram />
        {children}
      </body>
    </html>
  );
}
