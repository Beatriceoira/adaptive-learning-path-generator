import type { Metadata } from "next";
import { AuthProvider } from "@/lib/auth-context";
import { NavBar } from "@/components/NavBar";
import { APP_NAME } from "@/lib/constants";
import "./globals.css";

export const metadata: Metadata = {
  title: `${APP_NAME} — personalized learning paths`,
  description: "An AI tutor that assesses your level and adapts your learning path as you go.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-paper font-body text-ink antialiased">
        <AuthProvider>
          <NavBar />
          <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
