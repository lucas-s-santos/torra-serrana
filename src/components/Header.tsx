import { Grao } from "@/components/Logo";

/** Fixo, com mix-blend-difference: creme sobre café, quase preto sobre creme, sem trocar cor por seção. */
export function Header() {
  return (
    <header className="pointer-events-none fixed inset-x-0 top-0 z-50 text-creme mix-blend-difference">
      <div className="shell flex items-center justify-between py-5 md:py-7">
        <a href="#topo" className="pointer-events-auto flex items-center gap-2.5 font-serif text-xl tracking-[-0.01em] md:gap-3 md:text-2xl">
          <Grao id="grao-header" anima className="size-[1.45em] -translate-y-[0.04em]" />
          Torra Serrana
        </a>
        <nav className="pointer-events-auto flex items-center gap-8 font-mono text-[11px] uppercase tracking-[0.18em]">
          <span className="hidden opacity-60 md:inline">Sul de Minas — MG</span>
          <a href="#prove" className="group inline-flex items-center gap-2">
            Prove
            <span aria-hidden className="transition-transform duration-300 ease-out-expo group-hover:translate-x-1">
              →
            </span>
          </a>
        </nav>
      </div>
    </header>
  );
}
