import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { ClientLayout } from "@/components/layout/ClientLayout";

export const metadata: Metadata = {
  title: "FraudLens — AI Fraud-Ring Intelligence for Razorpay",
  description: "See the fraud behind the transaction. AI fraud-ring intelligence and command center.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090A0F] text-slate-200 min-h-screen flex antialiased font-sans overflow-hidden">
        <Sidebar />
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}
