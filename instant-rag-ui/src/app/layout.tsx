import type { Metadata } from "next";
import ClientLayout from "./layout.client";

export const metadata: Metadata = {
  title: "Instant-RAG",
  description: "AI-powered multi-project RAG system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <ClientLayout>{children}</ClientLayout>;
}
