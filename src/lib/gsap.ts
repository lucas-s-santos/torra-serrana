import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(ScrollTrigger, useGSAP);

export { gsap, ScrollTrigger, useGSAP };

/** SplitText fora do bundle inicial: só é baixado quando o primeiro <Revela> se aproxima da tela. */
let splitText: Promise<typeof import("gsap/SplitText").SplitText> | undefined;
export function loadSplitText() {
  splitText ??= import("gsap/SplitText").then(({ SplitText }) => {
    gsap.registerPlugin(SplitText);
    return SplitText;
  });
  return splitText;
}
