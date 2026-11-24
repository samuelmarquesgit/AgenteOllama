// Chat do Tork — ToolExpert AI. Módulo ES sem build.
// Segurança: todo texto vindo da API entra na página só por textContent/createTextNode (nunca como HTML).

const API = { chat: "/chat", health: "/health", conversas: "/conversas", avaliacoes: "/avaliacoes" };

const AVATAR = "/static/brand/tork-avatar.svg";
const AVATAR_ALERTA = "/static/brand/tork-avatar-alerta.svg";

// origem da resposta -> [classe do selo, texto do selo]
const SELOS = {
  banco: ["banco", "📚 Base de conhecimento"],
  catalogo: ["catalogo", "🛒 Catálogo (dados fictícios)"],
  loja: ["loja", "🏬 Dados da loja"],
  agente: ["agente", "🤖 Tork IA · resposta gerada, ainda não revisada"],
  sugestao: ["sugestao", "🤖 Resposta aprendida · aguardando revisão"],
  fallback: ["outro", "⚠️ Sem resposta segura"],
  fora_do_escopo: ["outro", "⚠️ Fora do assunto"],
  saudacao: ["outro", "👋 Tork"],
  bloqueado: ["bloqueado", "🛡️ Bloqueado por guardrail"],
};
const ORIGENS_ALERTA = new Set(["bloqueado", "fallback", "fora_do_escopo"]);
const ORIGENS_AVALIAVEIS = new Set(["banco", "catalogo", "loja", "agente", "sugestao"]);

// Menu inicial (docs/0008-Desenho-Conversacional.md)
const MENU = [
  { icone: "🔎", rotulo: "Encontrar um produto", submenu: true },
  { icone: "🛠️", rotulo: "Ajuda para escolher", texto: "Não sei qual ferramenta comprar" },
  { icone: "📦", rotulo: "Pedido ou entrega", texto: "Como acompanho meu pedido?" },
  { icone: "💳", rotulo: "Pagamento e parcelamento", texto: "Quais as formas de pagamento?" },
  { icone: "🔁", rotulo: "Trocas e garantia", texto: "Posso trocar ou devolver um produto?" },
  { icone: "👤", rotulo: "Falar com um atendente", texto: "Quero falar com um atendente" },
];
const CATEGORIAS = [
  ["Furadeiras", "Quais furadeiras vocês têm?"],
  ["Furadeiras de impacto", "Quanto custa uma furadeira de impacto?"],
  ["Parafusadeiras", "Tem parafusadeira a bateria?"],
  ["Esmerilhadeiras", "Quais esmerilhadeiras vocês têm?"],
  ["Serras", "Quanto custa uma serra circular?"],
  ["Brocas", "Quais brocas vocês têm?"],
  ["Multímetros", "Quanto custa um multímetro?"],
  ["EPI", "Tem óculos de proteção?"],
  ["Compressores", "Quanto custa um compressor de ar?"],
  ["Lavadoras", "Quanto custa uma lavadora de alta pressão?"],
];
const SUGESTOES = [
  "Quanto custa uma furadeira de impacto?",
  "Tem parafusadeira a bateria até R$ 600?",
  "Qual broca usar em concreto?",
  "Posso colocar disco maior na esmerilhadeira?",
  "Que horas a loja abre?",
  "Onde fica a loja?",
];
const ALIMENTACAO = { "127V": "127 V", "220V": "220 V", bivolt: "Bivolt", bateria: "A bateria", nao_eletrico: "" };

const $ = (seletor) => document.querySelector(seletor);
const conversa = $("#conversa");
const form = $("#form");
const campo = $("#mensagem");
const botaoEnviar = $("#enviar");
const indicadorStatus = $("#status");

let conversationId = novoId();
let enviando = false;

// ---------------------------------------------------------------- utilidades
function novoId() {
  if (window.crypto?.randomUUID) return crypto.randomUUID();
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);  // gerador criptográfico
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

function el(tag, classe, texto) {
  const e = document.createElement(tag);
  if (classe) e.className = classe;
  if (texto !== undefined) e.textContent = texto;
  return e;
}

function rolarParaFim() {
  window.scrollTo({ top: document.body.scrollHeight, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
}

function avatar(alerta = false) {
  const img = el("img", "avatar");
  img.src = alerta ? AVATAR_ALERTA : AVATAR;
  img.alt = alerta ? "Tork em alerta" : "Tork";
  img.width = 34;
  img.height = 34;
  return img;
}

// ---------------------------------------------------------------- mensagens
function adicionarCliente(texto) {
  const linha = el("div", "msg cliente");
  linha.appendChild(el("div", "balao", texto));
  conversa.appendChild(linha);
  rolarParaFim();
}

function adicionarTork(texto, { origem, meta, alerta } = {}) {
  const linha = el("div", "msg tork");
  linha.appendChild(avatar(alerta ?? ORIGENS_ALERTA.has(origem)));
  const balao = el("div", "balao");
  if (origem && SELOS[origem]) {
    const [classe, rotulo] = SELOS[origem];
    balao.appendChild(el("span", "selo " + classe, rotulo));
    balao.appendChild(document.createElement("br"));
  }
  balao.appendChild(document.createTextNode(texto));
  if (meta) balao.appendChild(el("div", "meta", meta));
  linha.appendChild(balao);
  conversa.appendChild(linha);
  rolarParaFim();
  return balao;
}

function mostrarPensando() {
  const linha = el("div", "msg tork pensando");
  linha.setAttribute("aria-label", "Tork está pensando");
  linha.appendChild(avatar());
  const balao = el("div", "balao");
  for (let i = 0; i < 3; i++) balao.appendChild(el("span", "ponto"));
  balao.appendChild(el("span", "sr-only", "Respondendo..."));
  linha.appendChild(balao);
  conversa.appendChild(linha);
  rolarParaFim();
  return linha;
}

function montarMeta(dados) {
  const partes = [];
  if (dados.perguntaInterpretada) partes.push(`Entendi como: "${dados.perguntaInterpretada}"`);
  if (dados.origem === "banco") partes.push(`${dados.matchedFaqId} · confiança ${Math.round(dados.confidence * 100)}%`);
  if (dados.origem === "banco" && dados.statusConteudo !== "validado") partes.push("conteúdo ainda não revisado por especialista");
  if (dados.statusConteudo === "dados_demonstracao") partes.push("dados fictícios de demonstração");
  if (dados.origem === "agente" && dados.matchedFaqId) partes.push(`Gravada como ${dados.matchedFaqId} para revisão humana`);
  if (dados.origem === "sugestao") partes.push(`${dados.matchedFaqId} · ainda não revisada por um especialista`);
  if (dados.guardrails?.length) partes.push(`🛡️ ${dados.guardrails.join(", ")}`);
  return partes.join(" · ");
}

function montarCards(produtos) {
  const grade = el("div", "cards");
  for (const p of produtos) {
    const card = el("article", "card");
    const img = el("img");
    img.src = p.imagem || "/static/produtos/placeholder.svg";
    img.alt = "Imagem ilustrativa: " + p.nome;
    img.loading = "lazy";
    card.appendChild(img);
    card.appendChild(el("div", "nome", p.nome));
    card.appendChild(el("div", "preco", p.preco_formatado));
    card.appendChild(el("div", "info", [p.marca, ALIMENTACAO[p.alimentacao], p.sku].filter(Boolean).join(" · ")));
    card.appendChild(el("div", "estoque " + (p.em_estoque ? "sim" : "nao"), p.em_estoque ? "● Em estoque" : "○ Sem estoque no momento"));
    if (p.especificacoes?.length) {
      const ul = el("ul");
      for (const e of p.especificacoes) ul.appendChild(el("li", "", `${e.nome}: ${e.valor}${e.unidade ? " " + e.unidade : ""}`));
      card.appendChild(ul);
    }
    grade.appendChild(card);
  }
  return grade;
}

function montarAvaliacao() {
  const caixa = el("div", "avaliar");
  caixa.appendChild(el("span", "", "Isso ajudou?"));
  for (const [util, rotulo, emoji] of [[true, "Sim, ajudou", "👍"], [false, "Não ajudou", "👎"]]) {
    const b = el("button", "", emoji);
    b.type = "button";
    b.setAttribute("aria-label", rotulo);
    b.setAttribute("aria-pressed", "false");
    b.addEventListener("click", async () => {
      for (const outro of caixa.querySelectorAll("button")) outro.disabled = true;
      b.setAttribute("aria-pressed", "true");
      try {
        await fetch(API.avaliacoes, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ conversationId, util }),
        });
        caixa.lastChild.after(el("span", "", "Obrigado pelo retorno!"));
      } catch {
        caixa.lastChild.after(el("span", "", "Não foi possível registrar agora."));
      }
    });
    caixa.appendChild(b);
  }
  return caixa;
}

// ---------------------------------------------------------------- envio
async function enviar(texto) {
  texto = texto.trim();
  if (!texto || enviando) return;
  if (texto.toLowerCase() === "menu") {
    campo.value = "";
    adicionarCliente(texto);
    mostrarBoasVindas(false);
    return;
  }
  enviando = true;
  botaoEnviar.disabled = true;
  campo.value = "";
  adicionarCliente(texto);
  const pensando = mostrarPensando();
  try {
    const r = await fetch(API.chat, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: texto, conversationId }),
    });
    if (!r.ok) throw new Error(String(r.status));
    const dados = await r.json();
    pensando.remove();
    const balao = adicionarTork(dados.answer, { origem: dados.origem, meta: montarMeta(dados) });
    if (dados.produtos?.length) balao.appendChild(montarCards(dados.produtos));
    if (ORIGENS_AVALIAVEIS.has(dados.origem)) balao.appendChild(montarAvaliacao());
    void atualizarStatus();
  } catch {
    pensando.remove();
    adicionarTork("Não consegui responder agora. Verifique a conexão e tente de novo em instantes.", { alerta: true });
  } finally {
    enviando = false;
    botaoEnviar.disabled = false;
    campo.focus();
    rolarParaFim();
  }
}

// ---------------------------------------------------------------- boas-vindas e menu
function mostrarBoasVindas(completa = true) {
  const caixa = el("section", "boas-vindas");
  caixa.setAttribute("aria-label", "Menu do Tork");
  if (completa) {
    const cabeca = el("div", "boas-vindas-cabeca");
    const img = el("img");
    img.src = AVATAR;
    img.alt = "Tork, assistente virtual da ToolExpert";
    img.width = 64;
    img.height = 64;
    cabeca.appendChild(img);
    const textos = el("div");
    textos.appendChild(el("h1", "", "Olá! 👋 Eu sou o Tork"));
    textos.appendChild(el("p", "", "Assistente da ToolExpert. Posso ajudar você a encontrar ferramentas, escolher a certa para o seu trabalho e tirar dúvidas sobre pedidos, pagamento e trocas."));
    cabeca.appendChild(textos);
    caixa.appendChild(cabeca);
  } else {
    caixa.appendChild(el("p", "", "Como posso ajudar?"));
  }
  const menu = el("div", "menu");
  for (const item of MENU) {
    const b = el("button");
    b.type = "button";
    b.appendChild(el("span", "icone", item.icone));
    b.appendChild(el("span", "", item.rotulo));
    b.addEventListener("click", () => (item.submenu ? mostrarCategorias(caixa) : void enviar(item.texto)));
    menu.appendChild(b);
  }
  caixa.appendChild(menu);
  caixa.appendChild(el("p", "dica", "Digite sua dúvida a qualquer momento, ou \"menu\" para voltar aqui."));
  conversa.appendChild(caixa);
  rolarParaFim();
}

function mostrarCategorias(caixa) {
  caixa.querySelector(".submenu")?.remove();
  const sub = el("div", "submenu");
  sub.setAttribute("aria-label", "Categorias de produtos");
  for (const [rotulo, texto] of CATEGORIAS) {
    const b = el("button", "chip", rotulo);
    b.type = "button";
    b.addEventListener("click", () => void enviar(texto));
    sub.appendChild(b);
  }
  caixa.querySelector(".menu").after(sub);
  sub.querySelector("button").focus();
}

function iniciarConversa() {
  fetch(`${API.conversas}/${conversationId}`, { method: "DELETE" }).catch(() => {});
  conversationId = novoId();
  conversa.replaceChildren();
  mostrarBoasVindas();
  campo.focus();
}

// ---------------------------------------------------------------- status e tema
async function atualizarStatus() {
  try {
    const r = await fetch(API.health);
    const d = await r.json();
    indicadorStatus.textContent = `Tork online · ${d.faqs - d.aprendidas} respostas revisadas`;
    indicadorStatus.classList.remove("offline");
  } catch {
    indicadorStatus.textContent = "Tork offline";
    indicadorStatus.classList.add("offline");
  }
}

function lerTema() {
  try { return localStorage.getItem("tema"); } catch { return null; }
}

function aplicarTema(tema) {
  if (tema) document.documentElement.dataset.theme = tema;
  else delete document.documentElement.dataset.theme;
  const escuro = tema ? tema === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  const botao = $("#tema");
  botao.textContent = escuro ? "☀️" : "🌙";
  botao.setAttribute("aria-label", escuro ? "Usar tema claro" : "Usar tema escuro");
}

function alternarTema() {
  const atual = document.documentElement.dataset.theme
    || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const novo = atual === "dark" ? "light" : "dark";
  try { localStorage.setItem("tema", novo); } catch { /* armazenamento indisponível: só nesta sessão */ }
  aplicarTema(novo);
}

// ---------------------------------------------------------------- início
function montarSugestoes() {
  const caixa = $("#sugestoes");
  for (const s of SUGESTOES) {
    const b = el("button", "chip", s);
    b.type = "button";
    b.addEventListener("click", () => void enviar(s));
    caixa.appendChild(b);
  }
}

form.addEventListener("submit", (e) => { e.preventDefault(); void enviar(campo.value); });
$("#nova").addEventListener("click", iniciarConversa);
$("#tema").addEventListener("click", alternarTema);

// Links diretos para a apresentação: /?q=pergunta abre o chat já perguntando; ?tema=claro|escuro força o tema.
const parametros = new URLSearchParams(location.search);
const TEMAS_URL = { claro: "light", escuro: "dark" };

aplicarTema(TEMAS_URL[parametros.get("tema")] || lerTema());
montarSugestoes();
mostrarBoasVindas();
await atualizarStatus();
const perguntaInicial = parametros.get("q");
if (perguntaInicial) await enviar(perguntaInicial.slice(0, 500));
