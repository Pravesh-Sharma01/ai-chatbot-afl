import type { Metadata } from "next";
import Header from "@/components/header/header";
import "./globals.css";

export const metadata: Metadata = {
  title: "Altudo AI Chatbot",
  description: "Chat with Altudo AI Chatbot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`antialiased flex flex-col min-h-screen`}>
        <Header />
        {children}
      </body>
    </html>
  );
}
