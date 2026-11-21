import { Header } from "@/components/Header";
import { Hero } from "@/components/sections/Hero";
import { Origem } from "@/components/sections/Origem";
import { Serra } from "@/components/sections/Serra";
import { Crema } from "@/components/sections/Crema";
import { Extracao } from "@/components/sections/Extracao";
import { Graos } from "@/components/sections/Graos";
import { Leite } from "@/components/sections/Leite";
import { Citacao } from "@/components/sections/Citacao";
import { Casa } from "@/components/sections/Casa";
import { Cta } from "@/components/sections/Cta";

export default function Home() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <Origem />
        <Serra />
        <Crema />
        <Extracao />
        <Graos />
        <Leite />
        <Citacao />
        <Casa />
        <Cta />
      </main>
    </>
  );
}
