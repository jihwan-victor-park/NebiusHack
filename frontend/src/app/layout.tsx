import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ShopAgent — AI Shopping Assistant",
  description: "Find the best deal across big retailers and indie shops",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-[#0f0f0f] text-white antialiased">{children}</body>
    </html>
  );
}
