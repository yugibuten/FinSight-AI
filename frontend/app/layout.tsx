import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinSight — Financial intelligence",
  description: "Understand markets through grounded, natural-language research.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
