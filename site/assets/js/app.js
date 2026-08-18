// Planroot — fluxo de tela única do Iniciador de Projeto (PIF).
// Estados: hero -> wizard (perguntas adaptativas) -> review -> paywall (Pix) -> done.

const API = "/api";

// copy.js define window.COPY e carrega antes deste arquivo. O fallback cobre
// o caso em que ele nao chega (cache, bloqueador, rede): sem isso, cada
// leitura de window.COPY.<chave> lancaria TypeError e mataria o fluxo.
window.COPY = window.COPY || {};

const state = {
  sessionId: null,
  questionsById: {},
  phase1Ids: [],
  sequence: [],      // ordem efetiva de perguntas (fase 1 + fase 2 adaptativa)
  index: 0,
  answers: {},
  gate: 90,
  lastRoute: null,
  pollTimer: null,
};

// --------------------------------------------------------------------------- //
// Bootstrap: injeta copy (placeholders) e carrega o banco de perguntas
// --------------------------------------------------------------------------- //
// Todo o texto da interface entra por aqui: no HTML os elementos nascem
// vazios. Se copy.js nao tiver carregado (cache, bloqueador, falha de rede),
// window.COPY vem undefined -- e sem a guarda abaixo o TypeError derrubava o
// init inteiro, deixando a pagina so com o fundo. Uma pagina sem copy ainda
// e recuperavel; uma pagina sem JS nenhum, nao.
function applyCopy() {
  const copy = window.COPY;
  if (!copy) {
    console.error("copy.js nao carregou: a interface fica sem textos.");
    return;
  }
  document.querySelectorAll("[data-copy]").forEach((el) => {
    const key = el.getAttribute("data-copy");
    if (copy[key] !== undefined) el.textContent = copy[key];
  });
  document.querySelectorAll("[data-copy-attr]").forEach((el) => {
    const [attr, key] = el.getAttribute("data-copy-attr").split(":");
    if (copy[key] !== undefined) el.setAttribute(attr, copy[key]);
  });
}

async function loadQuestions() {
  const res = await fetch(`${API}/questions`);
  const data = await res.json();
  data.questions.forEach((q) => (state.questionsById[q.id] = q));
  state.phase1Ids = data.phase1_question_ids;
  state.gate = data.gate;
}

function show(viewId) {
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  document.getElementById(viewId).classList.add("active");
}

function setError(elId, msg) {
  const el = document.getElementById(elId);
  if (!msg) {
    el.classList.remove("show");
    el.textContent = "";
  } else {
    el.classList.add("show");
    el.textContent = msg;
  }
}

// --------------------------------------------------------------------------- //
// Hero -> inicia sessão
// --------------------------------------------------------------------------- //
async function startInterview() {
  setError("heroError", "");
  const brief = document.getElementById("briefInput").value.trim();
  try {
    const res = await fetch(`${API}/session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ brief }),
    });
    const data = await res.json();
    state.sessionId = data.session_id;
    state.sequence = [...state.phase1Ids];
    state.index = 0;
    state.answers = {};
    document.getElementById("progressWrap").hidden = false;
    show("view-wizard");
    renderQuestion();
  } catch (e) {
    setError("heroError", "Não foi possível iniciar. Tente novamente.");
  }
}

// --------------------------------------------------------------------------- //
// Wizard
// --------------------------------------------------------------------------- //
// Resposta canonica: a opcao decide a rota, os detalhes dao conteudo concreto
// ao blueprint. O backend aceita os dois formatos (ver app/pif_answers.py).
function answerFor(qid) {
  if (!state.answers[qid]) {
    state.answers[qid] = { option: null, details: {}, source: "explicit" };
  }
  return state.answers[qid];
}

function detailFields(q) {
  const schema = q.detail_schema || {};
  const fields = Array.isArray(schema.fields) ? schema.fields : [];
  return fields.length ? fields : [{ key: "nota", type: "text", label: null }];
}

// Campos de detalhe: onde entram o nome real, a data real, o sistema real.
// Sempre opcionais — nunca bloqueiam o avanco.
function renderDetails(q) {
  const answer = answerFor(q.id);
  const wrap = document.getElementById("qDetails");
  wrap.innerHTML = "";

  detailFields(q).forEach((field) => {
    const row = document.createElement("label");
    row.className = "detail-row";

    if (field.label) {
      const caption = document.createElement("span");
      caption.className = "detail-label";
      caption.textContent = field.label;
      row.appendChild(caption);
    }

    const input = document.createElement("input");
    input.className = "detail-input";
    input.type = field.type === "date" ? "date" : "text";
    input.value = answer.details[field.key] || "";
    if (input.type === "text") {
      input.placeholder = field.label ? "" : q.detail_hint || "";
    }
    input.oninput = () => {
      const value = input.value.trim();
      if (value) answer.details[field.key] = value;
      else delete answer.details[field.key];
    };

    row.appendChild(input);
    wrap.appendChild(row);
  });
}

function renderQuestion() {
  const qid = state.sequence[state.index];
  const q = state.questionsById[qid];
  document.getElementById("qMeta").textContent = `${q.phase} · ${state.index + 1}/${state.sequence.length}`;
  document.getElementById("qTitle").textContent = q.prompt;
  document.getElementById("qHint").textContent = window.COPY.wizard_choose_hint || "";
  document.getElementById("progressLabel").textContent = q.title;

  const box = document.getElementById("qOptions");
  box.innerHTML = "";
  const current = state.answers[qid];
  let selectedBtn = null;
  q.options.forEach((opt) => {
    const btn = document.createElement("button");
    const isSelected = current && current.option === opt.id;
    btn.className = "option" + (isSelected ? " selected" : "");
    if (isSelected) selectedBtn = btn;
    btn.textContent = opt.label;
    btn.onclick = () => {
      answerFor(qid).option = opt.id;
      box.querySelectorAll(".option").forEach((o) => o.classList.remove("selected"));
      btn.classList.add("selected");
      btn.scrollIntoView({ block: "nearest" });
      document.getElementById("nextBtn").disabled = false;
    };
    box.appendChild(btn);
  });
  box.scrollTop = 0;
  // Ao voltar para uma pergunta ja respondida, a escolha nao pode ficar
  // escondida (ou cortada) dentro da lista rolavel.
  if (selectedBtn) selectedBtn.scrollIntoView({ block: "nearest" });

  renderDetails(q);

  document.getElementById("nextBtn").disabled = !(current && current.option);
  document.getElementById("backBtn").style.visibility = state.index === 0 ? "hidden" : "visible";
}

async function postRoute() {
  const res = await fetch(`${API}/route`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers: state.answers }),
  });
  return res.json();
}

function updateMeter(ambiguity) {
  document.getElementById("ambiguityValue").textContent = `${Math.round(ambiguity)}%`;
  document.getElementById("progressFill").style.width = `${Math.min(100, ambiguity)}%`;
}

async function nextQuestion() {
  const currentId = state.sequence[state.index];
  const route = await postRoute();
  state.lastRoute = route;
  updateMeter(route.ambiguity_reduction || 0);

  // A sequência é o plano do resolver, não uma montagem da UI. Perguntas que
  // as condições da rota tornaram desnecessárias somem daqui.
  if (Array.isArray(route.active_question_ids) && route.active_question_ids.length) {
    state.sequence = route.active_question_ids;
  }

  // Reancorar pelo id: a resequência pode ter removido perguntas antes do
  // cursor, e um índice cru faria o wizard pular ou repetir telas.
  const anchor = state.sequence.indexOf(currentId);
  state.index = anchor >= 0 ? anchor + 1 : state.index + 1;

  // Pula o que já foi respondido antes (ao voltar e mudar uma resposta).
  while (
    state.index < state.sequence.length &&
    state.answers[state.sequence[state.index]] &&
    state.answers[state.sequence[state.index]].option
  ) {
    state.index += 1;
  }

  if (state.index >= state.sequence.length) {
    goReview();
  } else {
    renderQuestion();
  }
}

function prevQuestion() {
  if (state.index > 0) {
    state.index -= 1;
    renderQuestion();
    if (state.lastRoute) updateMeter(state.lastRoute.ambiguity_reduction || 0);
  }
}

// --------------------------------------------------------------------------- //
// Review
// --------------------------------------------------------------------------- //
function summaryRows(target, rows) {
  const el = document.getElementById(target);
  el.innerHTML = "";
  rows.forEach(([k, v]) => {
    const dk = document.createElement("div");
    dk.className = "k";
    dk.textContent = k;
    const dv = document.createElement("div");
    dv.className = "v";
    dv.textContent = v;
    el.appendChild(dk);
    el.appendChild(dv);
  });
}

function goReview() {
  const r = state.lastRoute || {};
  summaryRows("reviewSummary", [
    ["Preset principal", r.primary_preset || "—"],
    ["Profundidade", r.depth_profile || "—"],
    ["Overlays ativos", (r.active_overlays || []).join(", ") || "nenhum"],
    [window.COPY.ambiguity_label || "Clareza", `${Math.round(r.ambiguity_reduction || 0)}%`],
  ]);
  show("view-review");
}

async function generateBlueprint() {
  setError("reviewError", "");
  try {
    const res = await fetch(`${API}/blueprint`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, answers: state.answers }),
    });
    if (res.status === 409) {
      const d = await res.json();
      const amb = Math.round((d.detail && d.detail.ambiguity_reduction) || 0);
      setError("reviewError", `Ambiguidade ainda em ${amb}%. Responda mais perguntas (meta ${state.gate}%).`);
      return;
    }
    if (!res.ok) throw new Error("blueprint");
    const data = await res.json();
    goPaywall(data);
  } catch (e) {
    setError("reviewError", "Falha ao gerar o blueprint. Tente novamente.");
  }
}

// --------------------------------------------------------------------------- //
// Paywall (Asaas Pix)
// --------------------------------------------------------------------------- //
async function goPaywall(blueprintData) {
  document.getElementById("priceAmt").textContent = (blueprintData.price || 20).toFixed(2).replace(".", ",");
  show("view-paywall");
  setError("payError", "");

  try {
    const res = await fetch(`${API}/checkout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId }),
    });
    if (!res.ok) throw new Error("checkout");
    const data = await res.json();

    document.getElementById("pixQr").src = `data:image/png;base64,${data.qr_base64}`;
    document.getElementById("copiaCola").textContent = data.copia_cola || "";
    document.getElementById("mockPill").hidden = !data.mock;

    if (data.mock) injectSimulateButton();
    startPolling();
  } catch (e) {
    setError("payError", "Não foi possível gerar a cobrança Pix.");
  }
}

function injectSimulateButton() {
  if (document.getElementById("simBtn")) return;
  const btn = document.createElement("button");
  btn.id = "simBtn";
  btn.className = "btn btn-ghost";
  btn.style.marginTop = "10px";
  btn.textContent = "Simular pagamento (sandbox)";
  btn.onclick = async () => {
    await fetch(`${API}/dev/simulate-payment/${state.sessionId}`, { method: "POST" });
  };
  document.querySelector("#view-paywall .pix-side").appendChild(btn);
}

function startPolling() {
  clearInterval(state.pollTimer);
  state.pollTimer = setInterval(async () => {
    try {
      const res = await fetch(`${API}/payment/${state.sessionId}`);
      const data = await res.json();
      if (data.paid) {
        clearInterval(state.pollTimer);
        goDone();
      }
    } catch (e) {
      /* mantém tentando */
    }
  }, 3000);
}

// --------------------------------------------------------------------------- //
// Done — libera downloads
// --------------------------------------------------------------------------- //
function goDone() {
  const r = state.lastRoute || {};
  summaryRows("doneSummary", [
    ["Preset principal", r.primary_preset || "—"],
    ["Profundidade", r.depth_profile || "—"],
    ["Overlays ativos", (r.active_overlays || []).join(", ") || "nenhum"],
  ]);
  document.getElementById("dlPrompt").href = `${API}/download/${state.sessionId}.prompt.md`;
  document.getElementById("dlMd").href = `${API}/download/${state.sessionId}.md`;
  document.getElementById("dlJson").href = `${API}/download/${state.sessionId}.json`;
  show("view-done");
}

// Copia o "Prompt para IA" direto para a area de transferencia (uso tipico: colar no Claude/Codex).
async function copyPrompt() {
  try {
    const res = await fetch(`${API}/download/${state.sessionId}.prompt.md`);
    if (!res.ok) return;
    const text = await res.text();
    if (navigator.clipboard && text) {
      await navigator.clipboard.writeText(text);
      const btn = document.getElementById("copyPromptBtn");
      const prev = btn.textContent;
      btn.textContent = window.COPY.copy_prompt_done || "Copiado!";
      setTimeout(() => (btn.textContent = prev), 1800);
    }
  } catch (e) {
    /* silencioso: o usuario ainda pode baixar o arquivo */
  }
}

// --------------------------------------------------------------------------- //
// Wiring
// --------------------------------------------------------------------------- //
function copyPix() {
  const text = document.getElementById("copiaCola").textContent;
  if (navigator.clipboard && text) navigator.clipboard.writeText(text);
}

// Chips de exemplo do hero: preenchem o brief para quem trava na folha em
// branco. O texto de cada um vem do data-fill, no HTML.
function bindExampleChips() {
  const input = document.getElementById("briefInput");
  document.querySelectorAll(".examples .chip").forEach((chip) => {
    chip.onclick = () => {
      input.value = chip.getAttribute("data-fill") || "";
      input.focus();
    };
  });
}

function bind() {
  document.getElementById("startBtn").onclick = startInterview;
  document.getElementById("nextBtn").onclick = nextQuestion;
  document.getElementById("backBtn").onclick = prevQuestion;
  document.getElementById("generateBtn").onclick = generateBlueprint;
  document.getElementById("copyBtn").onclick = copyPix;
  document.getElementById("copyPromptBtn").onclick = copyPrompt;
  bindExampleChips();
}

(async function init() {
  applyCopy();
  bind();
  await loadQuestions();
})();
