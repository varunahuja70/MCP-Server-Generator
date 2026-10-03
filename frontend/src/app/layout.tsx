import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "MCP Forge",
  description: "Turn OpenAPI specs into ready-to-run MCP servers.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[var(--background)] text-[var(--text)] antialiased">
        {children}
      </body>
    </html>
  );
}
