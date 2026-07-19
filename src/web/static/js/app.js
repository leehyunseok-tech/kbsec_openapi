// 실행 화면(index.html) — 명령 입력/출력 + 확인·선택 세션 버튼 + 알림 폴링.
//
// 확인/선택 세션 구조는 터미널(화살표 프롬프트)/텔레그램(인라인 버튼)과 동일하다:
// 백엔드 세션 로직은 "y"/"n" 또는 1-based 번호 텍스트만 이해하므로(command_pipeline.py),
// 여기서는 버튼 클릭을 그 텍스트로 바꿔 /api/answer 로 보내기만 하면 된다.

const output = document.getElementById("output");
const input = document.getElementById("cmd-input");
const sendBtn = document.getElementById("cmd-send");
const pendingBox = document.getElementById("pending");
const pendingTitle = pendingBox.querySelector(".pending-title");
const pendingButtons = pendingBox.querySelector(".pending-buttons");

// ── 출력창 상태 유지 (sessionStorage) ──────────────────────────────────
// "API 명세"/"설정"으로 이동했다가 돌아오거나 새로고침해도 출력 이력이 남도록
// 항목을 sessionStorage(같은 탭 한정, 탭 닫으면 소멸)에 저장하고 로드 시 복원한다.
// 서버 세션(로그인/토큰)은 HttpOnly 쿠키로 이미 유지되므로 화면만 복원하면 된다.
const OUTPUT_STORE_KEY = "kbsec_run_output";
const HISTORY_STORE_KEY = "kbsec_run_history";
const OUTPUT_STORE_MAX = 300;

function loadStore(key) {
  try {
    const v = JSON.parse(sessionStorage.getItem(key) || "[]");
    return Array.isArray(v) ? v : [];
  } catch (e) {
    return [];
  }
}

function saveStore(key, arr) {
  try {
    sessionStorage.setItem(key, JSON.stringify(arr));
  } catch (e) {
    // 저장 공간 초과 등 — 화면 동작에는 영향 없으니 무시
  }
}

let outputStore = loadStore(OUTPUT_STORE_KEY);

const WELCOME_TEXT = "명령을 입력하면 결과가 여기에 표시됩니다. /help 로 전체 명령어를 볼 수 있습니다.";

function renderEntry(text, cls) {
  const span = document.createElement("span");
  span.className = "entry" + (cls ? " " + cls : "");
  span.textContent = text;
  output.appendChild(span);
  output.scrollTop = output.scrollHeight;
}

function appendOutput(text, cls) {
  renderEntry(text, cls);
  outputStore.push({ t: text, c: cls || "" });
  if (outputStore.length > OUTPUT_STORE_MAX) outputStore = outputStore.slice(-OUTPUT_STORE_MAX);
  saveStore(OUTPUT_STORE_KEY, outputStore);
}

function clearScreen() {
  outputStore = [];
  saveStore(OUTPUT_STORE_KEY, outputStore);
  output.innerHTML = "";
  renderDetect(null);
  renderEntry(WELCOME_TEXT, "notice");
}

// 저장된 이력이 있으면 초기 안내문 대신 이력을 복원한다
if (outputStore.length > 0) {
  output.innerHTML = "";
  outputStore.forEach((e) => renderEntry(e.t, e.c));
}

function setBusy(busy) {
  input.disabled = busy;
  sendBtn.disabled = busy;
  // AI 변환/KB API 응답을 기다리는 동안 출력창에 스피너를 띄워
  // 화면이 멈춘 게 아니라 뒤에서 처리 중임을 보여준다.
  if (busy) {
    if (!document.getElementById("busy-indicator")) {
      const el = document.createElement("span");
      el.id = "busy-indicator";
      el.className = "entry busy-entry";
      el.innerHTML = '<span class="spinner"></span> 처리 중입니다...';
      output.appendChild(el);
      output.scrollTop = output.scrollHeight;
    }
  } else {
    const el = document.getElementById("busy-indicator");
    if (el) el.remove();
  }
}

// ── 확인/선택 세션 렌더링 ──────────────────────────────────────────────
function renderPending(pending) {
  if (!pending) {
    pendingBox.classList.add("hidden");
    pendingTitle.textContent = "";
    pendingButtons.innerHTML = "";
    input.focus();
    return;
  }

  pendingButtons.innerHTML = "";

  if (pending.kind === "confirm") {
    pendingBox.classList.add("confirm");
    // 첫 줄("다음 명령어를 실행할까요?") 바로 오른쪽에 [Enter] 힌트를 붙이고,
    // 명령 본문은 그 아래 줄에 표시한다.
    pendingTitle.textContent = "";
    const newlineIdx = pending.message.indexOf("\n");
    const headText = newlineIdx === -1 ? pending.message : pending.message.slice(0, newlineIdx);
    const restText = newlineIdx === -1 ? "" : pending.message.slice(newlineIdx).trim();

    const headLine = document.createElement("div");
    headLine.className = "pending-head";
    headLine.textContent = headText;
    const hint = document.createElement("span");
    hint.className = "enter-hint";
    hint.textContent = "[Enter] 입력 시 실행 · [Esc] 취소";
    headLine.appendChild(hint);
    pendingTitle.appendChild(headLine);

    if (restText) {
      const rest = document.createElement("div");
      rest.className = "pending-rest";
      rest.textContent = restText;
      pendingTitle.appendChild(rest);
    }
    addPendingButton("실행", "y", "");
    addPendingButton("취소", "n", "ghost");
  } else {
    // select — 종목/API명/API필드 선택 (1-based 번호)
    pendingBox.classList.remove("confirm");
    pendingTitle.textContent = pending.title;
    pending.options.forEach((label, i) => {
      addPendingButton((i + 1) + ". " + label, String(i + 1), "secondary");
    });
    addPendingButton("취소", "취소", "ghost");
  }
  pendingBox.classList.remove("hidden");
}

function addPendingButton(label, value, cls) {
  const btn = document.createElement("button");
  btn.textContent = label;
  if (cls) btn.className = cls;
  btn.addEventListener("click", () => sendAnswer(value));
  pendingButtons.appendChild(btn);
}

async function sendAnswer(value) {
  setBusy(true);
  renderPending(null);
  try {
    const r = await apiPost("/api/answer", { value: value });
    if (r.response) appendOutput(r.response);
    renderPending(r.pending);
  } catch (e) {
    appendOutput("❌ 서버 통신 오류: " + e, "notice");
  } finally {
    setBusy(false);
    refreshStatusBadge();
    if (typeof pollApiLog === "function") pollApiLog(); // 실행 직후 로그 즉시 갱신
  }
}

// ── 명령 전송 + 입력 히스토리(↑/↓) ────────────────────────────────────
// 터미널처럼 ↑/↓ 로 이전에 입력한 명령을 다시 불러온다. draft는 히스토리 탐색을
// 시작하기 직전에 치고 있던 내용 — ↓ 로 끝까지 내려오면 복원된다.
// 히스토리도 출력 이력과 같이 sessionStorage에 저장해 페이지 이동 후에도 유지한다.
let cmdHistory = loadStore(HISTORY_STORE_KEY);
let historyIndex = -1; // -1 = 히스토리 탐색 중 아님
let historyDraft = "";

async function sendCommand() {
  const text = input.value.trim();
  if (!text) return;
  if (cmdHistory[cmdHistory.length - 1] !== text) {
    cmdHistory.push(text);
    if (cmdHistory.length > 100) cmdHistory = cmdHistory.slice(-100);
    saveStore(HISTORY_STORE_KEY, cmdHistory);
  }
  historyIndex = -1;
  historyDraft = "";
  input.value = "";
  renderDetect(null);
  appendOutput(">>> " + text, "cmd-echo");
  setBusy(true);
  try {
    const r = await apiPost("/api/command", { text: text });
    if (r.response) appendOutput(r.response);
    renderPending(r.pending);
  } catch (e) {
    appendOutput("❌ 서버 통신 오류: " + e, "notice");
  } finally {
    setBusy(false);
    refreshStatusBadge();
    input.focus();
    if (typeof pollApiLog === "function") pollApiLog(); // 실행 직후 로그 즉시 갱신
  }
}

function confirmPendingVisible() {
  return !pendingBox.classList.contains("hidden") && pendingBox.classList.contains("confirm");
}

sendBtn.addEventListener("click", sendCommand);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    // 확인 프롬프트가 떠 있고 입력창이 비어 있으면 Enter = 실행 (버튼을 누를 필요 없음)
    if (confirmPendingVisible() && input.value.trim() === "") {
      sendAnswer("y");
      return;
    }
    sendCommand();
    return;
  }
  if (e.key === "Escape" && confirmPendingVisible()) {
    sendAnswer("n");
    return;
  }
  if (e.key === "ArrowUp") {
    if (cmdHistory.length === 0) return;
    e.preventDefault();
    if (historyIndex === -1) historyDraft = input.value;
    if (historyIndex < cmdHistory.length - 1) historyIndex += 1;
    input.value = cmdHistory[cmdHistory.length - 1 - historyIndex];
    return;
  }
  if (e.key === "ArrowDown") {
    if (historyIndex === -1) return;
    e.preventDefault();
    historyIndex -= 1;
    input.value = historyIndex === -1 ? historyDraft : cmdHistory[cmdHistory.length - 1 - historyIndex];
  }
});

// 사용법 카드의 예시 명령 클릭 → 입력창에 채우기
document.querySelectorAll(".guide-card code").forEach((el) => {
  el.addEventListener("click", () => {
    input.value = el.textContent;
    input.focus();
  });
});

// ── 종목 검색창 (증분 검색, 두 글자 이상, 디바운스) ────────────────────
// 마스터는 서버 시작 시 메모리에 이미 로드되어 있어(/api/stock/search) 응답이 빠르다.
// 키보드: ↑/↓ 로 결과 목록을 이동(하이라이트), Enter는
//   - 하이라이트된 항목이 있으면 → 그 종목만 남기고 나머지 제거
//   - 없으면 → 입력값 정확일치(exact=1) 검색으로 재조회 ("삼성전자"+Enter → 삼성전자만)
const stockSearchInput = document.getElementById("stock-search");
const stockResults = document.getElementById("stock-results");
let searchTimer = null;
let searchSeq = 0; // 응답 역전 방지 — 마지막 요청의 결과만 렌더링
let resultItems = []; // 현재 렌더링된 행 [{el, item}] — 키보드 내비게이션용
let activeIndex = -1;

function debounceSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => runStockSearch(false), 200);
}

async function runStockSearch(exact) {
  const q = stockSearchInput.value.trim();
  if (q.length < 2) {
    clearStockResults();
    return;
  }
  const seq = ++searchSeq;
  try {
    const url = "/api/stock/search?q=" + encodeURIComponent(q) + (exact ? "&exact=1" : "");
    const r = await apiGet(url);
    if (seq !== searchSeq) return; // 더 최신 입력의 응답이 이미 도착함
    renderStockResults(r);
  } catch (e) {
    // 검색 실패는 조용히 무시 (다음 타이핑에서 재시도)
  }
}

function clearStockResults() {
  stockResults.classList.add("hidden");
  stockResults.innerHTML = "";
  resultItems = [];
  activeIndex = -1;
}

function stockItemMeta(s) {
  return s.kind === "domestic"
    ? [s.market, s.stock_type, s.managed, s.halted]
    : [s.exchange_name, s.currency, s.stock_type, s.trade_restriction];
}

function renderStockResults(r) {
  stockResults.innerHTML = "";
  resultItems = [];
  activeIndex = -1;
  const total = r.domestic.length + r.overseas.length;
  if (total === 0) {
    const div = document.createElement("div");
    div.className = "empty";
    div.textContent = "검색 결과가 없습니다.";
    stockResults.appendChild(div);
    stockResults.classList.remove("hidden");
    return;
  }

  if (r.domestic.length > 0) {
    addGroupLabel("국내 (" + r.domestic.length + "건)");
    r.domestic.forEach((s) => addStockRow(s));
  }
  if (r.overseas.length > 0) {
    addGroupLabel("해외 (" + r.overseas.length + "건)");
    r.overseas.forEach((s) => addStockRow(s));
  }
  stockResults.classList.remove("hidden");
}

function addGroupLabel(text) {
  const div = document.createElement("div");
  div.className = "group-label";
  div.textContent = text;
  stockResults.appendChild(div);
}

function addStockRow(item) {
  const row = document.createElement("div");
  row.className = "stock-row";
  row.title = "클릭하면 명령 입력창에 종목코드가 들어갑니다";

  const nm = document.createElement("span");
  nm.className = "nm";
  nm.textContent = item.name;
  const cd = document.createElement("span");
  cd.className = "cd";
  cd.textContent = item.code;
  const meta = document.createElement("span");
  meta.className = "meta";
  meta.textContent = stockItemMeta(item).filter(Boolean).join(" · ");

  row.appendChild(nm);
  row.appendChild(cd);
  row.appendChild(meta);
  row.addEventListener("click", () => {
    // 클릭 = 명령 입력창에 코드 삽입 + 그 종목만 목록에 남기기 (Enter 선택과 동일)
    input.value = input.value.trim() ? input.value.trim() + " " + item.code : item.code;
    collapseToItem(item);
    input.focus();
  });
  stockResults.appendChild(row);
  resultItems.push({ el: row, item: item });
}

function setActiveIndex(idx) {
  if (activeIndex >= 0 && resultItems[activeIndex]) {
    resultItems[activeIndex].el.classList.remove("active");
  }
  activeIndex = idx;
  if (activeIndex >= 0 && resultItems[activeIndex]) {
    const el = resultItems[activeIndex].el;
    el.classList.add("active");
    el.scrollIntoView({ block: "nearest" });
  }
}

function collapseToItem(chosen) {
  // 선택된 종목만 남기고 나머지 결과를 전부 제거 (Enter 선택/클릭 공용)
  stockResults.innerHTML = "";
  resultItems = [];
  activeIndex = -1;
  addGroupLabel(chosen.kind === "domestic" ? "국내 (1건)" : "해외 (1건)");
  addStockRow(chosen);
  setActiveIndex(0);
}

stockSearchInput.addEventListener("input", debounceSearch);
stockSearchInput.addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown") {
    if (resultItems.length === 0) return;
    e.preventDefault();
    setActiveIndex(activeIndex < resultItems.length - 1 ? activeIndex + 1 : 0);
    return;
  }
  if (e.key === "ArrowUp") {
    if (resultItems.length === 0) return;
    e.preventDefault();
    setActiveIndex(activeIndex > 0 ? activeIndex - 1 : resultItems.length - 1);
    return;
  }
  if (e.key === "Enter") {
    e.preventDefault();
    clearTimeout(searchTimer);
    if (activeIndex >= 0 && resultItems[activeIndex]) {
      collapseToItem(resultItems[activeIndex].item);
    } else {
      runStockSearch(true); // 정확일치 검색
    }
    return;
  }
  if (e.key === "Escape") {
    clearStockResults();
  }
});

// ── 자연어 명령의 종목 인식 표시 ───────────────────────────────────────
// "/"로 시작하지 않는 입력(자연어 → AI 변환 대상)을 타이핑하는 동안, 문장 속
// 종목명/티커/6자리 코드를 로컬 마스터로 인식해 입력창 아래에 칩으로 보여준다.
// 예: "삼성전자 10주 사줘" → [삼성전자 005930 · KOSPI]
const detectBox = document.getElementById("stock-detect");
let detectTimer = null;
let detectSeq = 0;

function renderDetect(stocks) {
  if (!stocks || stocks.length === 0) {
    detectBox.classList.add("hidden");
    detectBox.innerHTML = "";
    return;
  }
  detectBox.innerHTML = "";
  const label = document.createElement("span");
  label.textContent = "📌 인식된 종목:";
  detectBox.appendChild(label);
  stocks.forEach((s) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    const marketLabel = s.kind === "domestic" ? s.market : s.exchange_name;
    chip.innerHTML = "";
    chip.textContent = s.name + " ";
    const codeSpan = document.createElement("span");
    codeSpan.className = "code";
    codeSpan.textContent = s.code + " · " + marketLabel;
    chip.appendChild(codeSpan);
    detectBox.appendChild(chip);
  });
  detectBox.classList.remove("hidden");
}

input.addEventListener("input", () => {
  clearTimeout(detectTimer);
  const text = input.value.trim();
  if (!text || text.startsWith("/") || text.length < 2) {
    renderDetect(null);
    return;
  }
  detectTimer = setTimeout(async () => {
    const seq = ++detectSeq;
    try {
      const r = await apiGet("/api/stock/detect?text=" + encodeURIComponent(text));
      if (seq !== detectSeq) return;
      renderDetect(r.stocks);
    } catch (e) {
      // 인식 실패는 조용히 무시
    }
  }, 250);
});

// ── 자동매매 모니터 알림 폴링 (5초) ────────────────────────────────────
async function pollNotifications() {
  try {
    const r = await apiGet("/api/notifications");
    (r.notifications || []).forEach((msg) => appendOutput("🔔 [알림] " + msg, "notice"));
  } catch (e) {
    // 서버가 잠시 죽어도 폴링은 계속한다
  }
}
setInterval(pollNotifications, 5000);

// ── API 로그 패널 — 터미널과 동일한 KB API RQ/RP 로그 (증분 폴링) ──────
const apiLogBox = document.getElementById("api-log");
let apiLogSeq = 0;

function appendLogEntry(entry) {
  const empty = apiLogBox.querySelector(".log-empty");
  if (empty) empty.remove();

  const div = document.createElement("div");
  div.className = "log-entry";

  const head = document.createElement("div");
  const ts = document.createElement("span");
  ts.className = "log-ts";
  ts.textContent = entry.ts + "  ";
  head.appendChild(ts);

  const title = document.createElement("span");
  if (entry.type === "request") {
    title.className = "log-head-req";
    title.textContent = "[API 요청] " + entry.api_name + (entry.api_id ? " (" + entry.api_id + ")" : "");
    head.appendChild(title);
    div.appendChild(head);
    const url = document.createElement("div");
    url.className = "log-url";
    url.textContent = "POST " + entry.url;
    div.appendChild(url);
    div.appendChild(jsonBlock(entry.data));
  } else if (entry.type === "response") {
    title.className = "log-head-res";
    title.textContent = "[API 응답] status_code=" + entry.status_code;
    head.appendChild(title);
    div.appendChild(head);
    div.appendChild(jsonBlock(entry.body));
  } else {
    title.className = "log-head-err";
    title.textContent = "[API 오류] " + (entry.error_type || "") + ": " + (entry.message || "");
    head.appendChild(title);
    div.appendChild(head);
  }

  apiLogBox.appendChild(div);
  // 새 로그가 들어올 때마다 항상 맨 아래로 자동 스크롤 — 실행 흐름을 놓치지 않도록
  apiLogBox.scrollTop = apiLogBox.scrollHeight;
}

function jsonBlock(obj) {
  const pre = document.createElement("div");
  pre.textContent = JSON.stringify(obj, null, 2);
  return pre;
}

async function pollApiLog() {
  try {
    const r = await apiGet("/api/apilog?since=" + apiLogSeq);
    (r.logs || []).forEach(appendLogEntry);
    apiLogSeq = r.last_seq;
  } catch (e) {
    // 폴링 실패는 조용히 무시
  }
}
setInterval(pollApiLog, 2500);

// ── 좌/우 사이드 패널 가로(옆으로) 접기 — 상태는 localStorage에 기억 ───
function setSideCollapsed(panelId, collapsed) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  if (collapsed) {
    // 드래그 리사이즈가 남긴 인라인 width/height가 .collapsed의 46px보다 우선하므로 제거
    panel.style.width = "";
    panel.style.height = "";
  }
  panel.classList.toggle("collapsed", collapsed);
  localStorage.setItem("kbsec_side_" + panelId, collapsed ? "1" : "0");
}

// 명령 실행 패널의 세로 접기 (details 미사용 — 헤더 클릭 토글)
document.querySelectorAll("[data-vtoggle]").forEach((head) => {
  head.addEventListener("click", () => {
    const panel = document.getElementById(head.dataset.vtoggle);
    if (!panel) return;
    if (!panel.classList.contains("v-collapsed")) {
      // 접기 직전 — 드래그가 남긴 인라인 크기를 제거해 제목 줄만 깔끔하게 남게 한다
      panel.style.height = "";
      panel.style.width = "";
    }
    panel.classList.toggle("v-collapsed");
  });
});

document.querySelectorAll(".collapse-h-btn").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    setSideCollapsed(btn.dataset.panel, true);
  });
});
document.querySelectorAll(".side-rail").forEach((rail) => {
  rail.addEventListener("click", () => setSideCollapsed(rail.dataset.panel, false));
});
["guide-panel", "log-panel"].forEach((id) => {
  if (localStorage.getItem("kbsec_side_" + id) === "1") setSideCollapsed(id, true);
});

// ── 화면초기화 버튼 + 세션 버튼(토큰재발급/로그아웃) 실행 화면 훅 ──────
// 토큰재발급/로그아웃 버튼 자체는 api.js가 3개 페이지 공통으로 바인딩한다.
// 실행 화면은 결과를 alert 대신 출력창/API 로그에 반영하도록 훅만 정의한다.
const clearScreenBtn = document.getElementById("btn-clear-screen");
if (clearScreenBtn) {
  clearScreenBtn.addEventListener("click", (e) => {
    // 버튼이 패널 제목줄(h2.v-head, 클릭=접기 토글) 안에 있으므로 전파를 막는다
    e.stopPropagation();
    // 화면(출력창)만 초기화 — 로그인/토큰/명령 히스토리는 그대로 유지
    clearScreen();
    input.focus();
  });
}

window.onTokenRefreshed = (r) => {
  appendOutput((r.success ? "" : "❌ ") + (r.message || "토큰 재발급"), "notice");
  pollApiLog(); // 재발급 RQ/RP를 로그 패널에 즉시 반영
};

window.onSessionLogout = (r) => {
  // 화면·히스토리·대기 세션까지 전부 초기화 (서버도 확인/선택 세션을 닫는다)
  cmdHistory = [];
  saveStore(HISTORY_STORE_KEY, cmdHistory);
  historyIndex = -1;
  renderPending(null);
  clearScreen();
  renderEntry((r.success ? "👋 " : "❌ ") + (r.message || "로그아웃"), "notice");
  pollApiLog(); // 토큰 폐기 RQ/RP를 로그 패널에 즉시 반영
};

// ── 초기화 ─────────────────────────────────────────────────────────────
// 미로그인 안내는 renderEntry(비저장)로만 표시 — appendOutput으로 저장하면
// 페이지를 오갈 때마다 이력에 같은 안내문이 쌓인다.
refreshStatusBadge().then((s) => {
  if (s && !s.logged_in) {
    renderEntry("ℹ️ 아직 로그인되지 않았습니다. 상단 '설정'에서 KB증권 앱키/시크릿을 입력하면 자동으로 로그인됩니다.", "notice");
  }
});

// 페이지 이동/새로고침 전에 열려 있던 확인/선택 세션이 서버에 남아 있으면 복원
apiGet("/api/pending").then((r) => {
  if (r && r.pending) renderPending(r.pending);
}).catch(() => {});
