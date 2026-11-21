// Conteúdo da Torra Serrana (marca fictícia). Tudo que é dado de negócio fica aqui.

// WhatsApp do Lucas (55 + DDD 35 + número), passado por ele em 20/11
export const WHATSAPP = "5535988862172";
export const WHATSAPP_MSG = "Oi! Quero um lugar no balcão.";
export const whatsappUrl = `https://wa.me/${WHATSAPP}?text=${encodeURIComponent(WHATSAPP_MSG)}`;

export const ENDERECO = ["Estrada da Serra, km 4", "Carmo de Minas · MG"];
export const HORARIO = [
  ["Ter a sáb", "8h — 18h"],
  ["Domingo", "8h — 13h"],
];

export const ORIGEM = [
  { label: "Altitude", valor: "1.100 m" },
  { label: "Variedade", valor: "Bourbon Amarelo" },
  { label: "Colheita", valor: "Manual, cereja por cereja" },
];

export const EXTRACAO = [
  { label: "Dose", de: 0, ate: 18, casas: 1, unidade: "g", janela: [0, 0.18] },
  { label: "Bebida", de: 0, ate: 36, casas: 1, unidade: "g", janela: [0.12, 0.95] },
  { label: "Tempo", de: 0, ate: 28, casas: 1, unidade: "s", janela: [0, 1] },
  { label: "Pressão", de: 0, ate: 9, casas: 1, unidade: "bar", janela: [0.04, 0.22] },
  { label: "Água", de: 88, ate: 93, casas: 1, unidade: "°C", janela: [0, 0.3] },
] as const;

export const LOTES = [
  {
    nome: "Serra Alta",
    img: "/img/graos/card-1.webp",
    notasImg: "/img/graos/notas-1.webp",
    variedade: "Bourbon Amarelo",
    processo: "Lavado",
    altitude: "1.250 m",
    notas: "Jasmim · Fruta amarela",
    torra: "Clara",
    pontos: 87,
  },
  {
    nome: "Pé de Morro",
    img: "/img/graos/card-2.webp",
    notasImg: "/img/graos/notas-2.webp",
    variedade: "Mundo Novo",
    processo: "Natural",
    altitude: "1.050 m",
    notas: "Cacau · Caramelo",
    torra: "Média",
    pontos: 85,
  },
  {
    nome: "Cereja Doce",
    img: "/img/graos/card-3.webp",
    notasImg: "/img/graos/notas-3.webp",
    variedade: "Catuaí Vermelho",
    processo: "Honey",
    altitude: "1.100 m",
    notas: "Frutas vermelhas · Mel",
    torra: "Média",
    pontos: 86,
  },
];
