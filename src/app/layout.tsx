import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";
import localFont from "next/font/local";
import "lenis/dist/lenis.css";
import "./globals.css";
import { SmoothScroll } from "@/components/SmoothScroll";
import { FilmGrain } from "@/components/FilmGrain";
import { Gota } from "@/components/Gota";

// Fraunces instanciado (peso 400, SOFT 50, só opsz variável): 70 KB em vez de 264 KB. Ver scripts/fraunces.py
const fraunces = localFont({
  src: [
    { path: "./fonts/fraunces.woff2", style: "normal", weight: "400" },
    { path: "./fonts/fraunces-italic.woff2", style: "italic", weight: "400" },
  ],
  variable: "--font-fraunces",
  display: "swap",
  adjustFontFallback: "Times New Roman",
});
// sem preload: o primeiro quadro só usa Fraunces e Geist Mono; o corpo aparece abaixo da dobra
const geist = Geist({ subsets: ["latin"], variable: "--font-geist", display: "swap", preload: false });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono", display: "swap" });

export const metadata: Metadata = {
  title: "Torra Serrana — Do pé à xícara",
  description: "Torrefação de cafés especiais do Sul de Minas. Colheita manual, torra em pequenos lotes.",
};

export const viewport: Viewport = { themeColor: "#1a110b" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    // suppressHydrationWarning: o script abaixo marca data-gota no <html> antes da hidratação
    <html lang="pt-BR" className={`${fraunces.variable} ${geist.variable} ${geistMono.variable}`} suppressHydrationWarning>
      <body>
        {/* a gota só cai na 1ª visita da sessão: marcado antes do primeiro paint, sem piscar */}
        <script dangerouslySetInnerHTML={{ __html: `try{sessionStorage.getItem("gota")&&document.documentElement.setAttribute("data-gota","vista")}catch(e){}` }} />
        <Gota />
        <SmoothScroll />
        {children}
        <FilmGrain />
      </body>
    </html>
  );
}
