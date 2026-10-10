import type { Metadata } from "next";
import { Playfair_Display, Inter } from "next/font/google";
import "./globals.css";

const serifFont = Playfair_Display({
  variable: "--font-serif",
  subsets: ["latin"],
  display: "swap",
});

const sansFont = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "VYOM+ | Intelligent Voucher Classification Using Open-Source AI",
  description: "Transform structured transaction records into intelligent accounting voucher classifications using Gemma 4 on the Gemini API.",
  icons: {
    icon: "/favicon.ico",
  },
};

import { WorkspaceProvider } from "@/context/WorkspaceContext";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${serifFont.variable} ${sansFont.variable} dark`}
    >
      <body className="min-h-screen bg-[#050505] text-[#F4EBDD] font-sans antialiased selection:bg-[#F0AE2C]/30 selection:text-[#F4EBDD]">
        <WorkspaceProvider>
          {children}
        </WorkspaceProvider>
      </body>
    </html>
  );
}
