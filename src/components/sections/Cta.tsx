import { LoopVideo } from "@/components/LoopVideo";
import { ENDERECO, HORARIO, whatsappUrl } from "@/lib/site";
import { Revela } from "@/components/Revela";
import { Grao } from "@/components/Logo";

export function Cta() {
  return (
    <section id="prove" aria-label="Prove" className="relative bg-cafe">
      <div className="shell grid items-center gap-14 py-28 md:grid-cols-12 md:gap-10 md:py-40">
        <div className="md:col-span-6">
          {/* xícara vista de cima; a madeira em volta some no café da página (máscara radial, sem borda dura) */}
          <div className="relative mx-auto aspect-square w-full max-w-[620px] overflow-hidden [mask-image:radial-gradient(closest-side,#000_62%,transparent)]">
            <LoopVideo src="/video/xicara-final.mp4" srcPequeno="/video/xicara-final-sm.mp4" className="absolute inset-0 size-full object-cover" />
          </div>
        </div>

        <div className="md:col-span-5 md:col-start-8">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/60">08 — Prove</p>
          <Revela className="mt-8 font-serif text-title">
            Prove na <em className="italic text-cereja">serra.</em>
          </Revela>
          <Revela as="p" delay={0.15} className="mt-8 max-w-[34ch] text-lead text-creme/70">
            Moemos na hora e tiramos na sua frente. Chama a gente e separamos um lugar no balcão.
          </Revela>

          <a
            href={whatsappUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="group mt-10 inline-flex items-center gap-4 rounded-full bg-creme px-8 py-4 font-medium text-cafe transition-colors duration-300 ease-out-expo hover:bg-caramelo focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-caramelo"
          >
            Chamar no WhatsApp
            <span aria-hidden className="transition-transform duration-300 ease-out-expo group-hover:translate-x-1">
              →
            </span>
          </a>

          <dl className="mt-14 grid grid-cols-2 gap-8 border-t border-creme/12 pt-8">
            <div>
              <dt className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/60">Onde</dt>
              <dd className="mt-3 leading-relaxed text-creme/80">
                {ENDERECO.map((l) => (
                  <span key={l} className="block">
                    {l}
                  </span>
                ))}
              </dd>
            </div>
            <div>
              <dt className="font-mono text-[11px] uppercase tracking-[0.18em] text-creme/60">Quando</dt>
              <dd className="mt-3 space-y-1 font-mono text-sm tabular-nums text-creme/80">
                {HORARIO.map(([dia, hora]) => (
                  <span key={dia} className="flex justify-between gap-4">
                    <span>{dia}</span>
                    <span>{hora}</span>
                  </span>
                ))}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <footer className="border-t border-creme/10">
        <div className="shell flex flex-col gap-3 py-8 font-mono text-[11px] uppercase tracking-[0.18em] text-creme/55 md:flex-row md:items-center md:justify-between">
          <span className="flex items-center gap-2.5 font-serif text-base normal-case tracking-normal text-creme/70">
            <Grao id="grao-rodape" className="size-6 text-caramelo" />
            Torra Serrana
          </span>
          <span>Marca fictícia · projeto de portfólio</span>
          <a href="https://instagram.com/dev.lucassilva.ss" target="_blank" rel="noopener noreferrer" className="hover:text-creme">
            Site por @dev.lucassilva.ss
          </a>
        </div>
      </footer>
    </section>
  );
}
