import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import type { ReactNode } from "react";

import { Toaster } from "@/components/ui/sonner";
import "./styles.css";

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"]
});

const geistMono = Geist_Mono({
  variable: "--font-mono",
  subsets: ["latin"]
});

export const metadata: Metadata = {
  title: "RELAI Onboarding",
  description: "Guided RELAI CLI walkthrough for a Python SDK airline support agent"
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        {children}
        <Toaster position="bottom-right" />
      </body>
    </html>
  );
}
