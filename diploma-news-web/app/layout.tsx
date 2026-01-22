import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "Diploma News",
  description: "Веб-стрічка новин для дипломного проєкту"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uk">
      <body>
        <Header />
        <main className="container-page py-6">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
