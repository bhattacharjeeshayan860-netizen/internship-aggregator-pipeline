import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Internship Radar — DS / ML / SWE",
  description:
    "Live internship aggregator scraping Greenhouse, Lever, and Ashby for paid DS/ML/SWE opportunities.",
  icons: { icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎯</text></svg>" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
