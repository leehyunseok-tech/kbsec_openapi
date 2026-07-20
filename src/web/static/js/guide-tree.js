// index.html "사용 방법" 패널 — docs/api/md 74개 API 전체를 업무구분 폴더 계층 트리로
// 보여주고(최상단), 항목 클릭 시 그 아래 "명령 실행" 폼(#api-form-body)에 항목별
// 입력칸을 만든다: 선택지 있는 필드는 콤보박스, 날짜 필드는 달력, 그 외는 입력칸.
// 값을 채우고 [실행]을 누르면 {"항목한글명":"값"} JSON 형식 명령을 조립해
// window.runCommandText()로 실행한다(원시 명령을 입력창에 남기지 않음).
//
// api.html의 apidoc.js와 같은 /api/spec/tree, /api/spec/detail 엔드포인트를 재사용한다.
// 실제 실행은 src/utils/direct_api_command.py(JSON 방식 파서)가 담당한다.

const directTreeDetails = document.getElementById("direct-cmd-guide");
const directTreeBox = document.getElementById("direct-cmd-tree");
const apiFormBody = document.getElementById("api-form-body");
const apiFormSub = document.getElementById("api-form-sub");
const apiFormOverlay = document.getElementById("api-form-overlay");
const apiFormClose = document.getElementById("api-form-close");

function openOverlay() {
  if (apiFormOverlay) apiFormOverlay.classList.remove("hidden");
}
function closeOverlay() {
  if (apiFormOverlay) apiFormOverlay.classList.add("hidden");
}

// 매수/매도/정정/취소 등 주문 계열 코드 접두어 — apidoc.js의 ORDER_CODE_RE와 동일 규칙.
const DIRECT_ORDER_CODE_RE = /^(SSAM|SKAM)/;

let directTreeLoaded = false;

// ── 트리 렌더링 (실행 가능한 TR코드 있는 파일만) ────────────────────────
function countDirectFiles(node) {
  const own = node.files.filter((f) => f.code).length;
  return own + node.dirs.reduce((acc, d) => acc + countDirectFiles(d), 0);
}

function renderDirectDir(node, depth) {
  if (countDirectFiles(node) === 0) return null; // OAuth 등 실행 불가 폴더는 제외

  const details = document.createElement("details");
  details.className = "tree-dir depth-" + depth;

  const summary = document.createElement("summary");
  summary.textContent = node.name;
  const badge = document.createElement("span");
  badge.className = "tree-count";
  badge.textContent = countDirectFiles(node);
  summary.appendChild(badge);
  details.appendChild(summary);

  node.dirs.forEach((d) => {
    const child = renderDirectDir(d, depth + 1);
    if (child) details.appendChild(child);
  });
  node.files.filter((f) => f.code).forEach((f) => details.appendChild(renderDirectFile(f)));
  return details;
}

let activeTreeFileEl = null;

function renderDirectFile(file) {
  const item = document.createElement("div");
  item.className = "tree-file";
  const isOrder = file.code && DIRECT_ORDER_CODE_RE.test(file.code);
  item.textContent = file.label + (isOrder ? " ⚠️" : "");
  item.title = isOrder ? "주문 계열 API — 값을 채워 실행하면 실제 거래가 발생합니다" : "";
  item.addEventListener("click", () => {
    if (activeTreeFileEl) activeTreeFileEl.classList.remove("active");
    activeTreeFileEl = item;
    item.classList.add("active");
    openApiForm(file);
  });
  return item;
}

async function loadDirectTree() {
  if (directTreeLoaded) return;
  directTreeLoaded = true;
  try {
    const r = await apiGet("/api/spec/tree");
    directTreeBox.innerHTML = "";
    r.tree.forEach((cat) => {
      const el = renderDirectDir(cat, 0);
      if (el) directTreeBox.appendChild(el);
    });
  } catch (e) {
    directTreeBox.textContent = "목록을 불러오지 못했습니다.";
  }
}

// ── 명령 실행 폼 ────────────────────────────────────────────────────────
// 날짜 필드 판별: 이름이 일자/일/dt/dy/ymd 계열이고 길이가 8(YYYYMMDD)인 경우.
function isDateField(f) {
  const en = (f.name_en || "").toLowerCase();
  const kr = f.name_kr || "";
  const byName = /(^|_)(dt|dy|ymd|date)$/.test(en) || kr.includes("일자") || /일$/.test(kr);
  return byName && f.length === 8;
}

async function openApiForm(file) {
  apiFormSub.textContent = file.label;
  apiFormBody.innerHTML = '<p class="hint">명세를 불러오는 중...</p>';
  openOverlay(); // 로딩 상태부터 레이어로 표시
  let detail;
  try {
    detail = await apiGet("/api/spec/detail?path=" + encodeURIComponent(file.path));
    if (detail.error) throw new Error(detail.error);
  } catch (e) {
    apiFormBody.innerHTML = '<p class="hint">명세를 불러오지 못했습니다: ' + e + "</p>";
    return;
  }
  renderApiForm(file, detail);
}

function renderApiForm(file, detail) {
  const token = file.label.replace(/ /g, "_");
  const isOrder = detail.code && DIRECT_ORDER_CODE_RE.test(detail.code);
  apiFormSub.textContent = detail.label || file.label;

  apiFormBody.innerHTML = "";

  // 커맨드 토큰 표시
  const tokenLine = document.createElement("div");
  tokenLine.className = "api-form-token";
  tokenLine.textContent = "/" + token;
  apiFormBody.appendChild(tokenLine);

  if (isOrder) {
    const warn = document.createElement("div");
    warn.className = "api-form-warn";
    warn.textContent = "⚠️ 주문 계열 API — 실행 시 실제 주문이 접수됩니다.";
    apiFormBody.appendChild(warn);
  }

  const fields = detail.fields || [];
  const widgets = []; // { field, read: () => value }

  if (fields.length === 0) {
    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = "입력 파라미터가 없습니다 — 바로 실행하세요.";
    apiFormBody.appendChild(p);
  } else {
    const form = document.createElement("div");
    form.className = "spec-fields";
    fields.forEach((f) => widgets.push(renderFieldRow(form, f)));
    apiFormBody.appendChild(form);
  }

  // 조립될 명령 미리보기
  const preview = document.createElement("code");
  preview.className = "api-form-preview";

  function buildCommand() {
    const parts = [];
    widgets.forEach(({ field, read }) => {
      const v = read();
      if (v === "" || v == null) return; // 빈 값은 생략(서버가 공백 자동 채움)
      parts.push('{"' + field.name_kr + '":"' + v + '"}');
    });
    return "/" + token + (parts.length ? " " + parts.join(" ") : "");
  }

  function refreshPreview() {
    preview.textContent = buildCommand();
  }
  widgets.forEach(({ el }) => {
    el.addEventListener("input", refreshPreview);
    el.addEventListener("change", refreshPreview);
  });
  refreshPreview();

  const actions = document.createElement("div");
  actions.className = "api-form-actions";
  const runBtn = document.createElement("button");
  runBtn.className = "api-form-run";
  runBtn.textContent = "실행";
  runBtn.addEventListener("click", () => {
    const cmd = buildCommand();
    if (isOrder && !confirm("주문 계열 API입니다. 운영환경(실거래)으로 실제 주문이 전송됩니다.\n계속할까요?")) {
      return;
    }
    if (window.runCommandText) window.runCommandText(cmd);
    closeOverlay(); // 실행 시 레이어 자동 닫기 (결과는 가운데 출력창에 표시)
  });
  actions.appendChild(runBtn);

  const previewWrap = document.createElement("div");
  previewWrap.className = "api-form-preview-wrap";
  const previewLabel = document.createElement("span");
  previewLabel.className = "api-form-preview-label";
  previewLabel.textContent = "실행될 명령";
  previewWrap.appendChild(previewLabel);
  previewWrap.appendChild(preview);

  apiFormBody.appendChild(actions);
  apiFormBody.appendChild(previewWrap);
}

// 필드 1개 → 라벨(항목한글명) + 위젯(콤보박스/날짜/입력칸). { field, el, read } 반환.
function renderFieldRow(form, f) {
  const row = document.createElement("div");
  row.className = "spec-field-row";

  const label = document.createElement("label");
  label.textContent = f.name_kr + " ";
  const en = document.createElement("span");
  en.className = "en";
  en.textContent = f.name_en;
  label.appendChild(en);
  row.appendChild(label);

  let el;
  let read;

  if (f.choices && f.choices.length > 0) {
    // 콤보박스 — 첫 항목은 빈 값(선택 안 함), 이어서 코드:라벨
    el = document.createElement("select");
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "— 선택 —";
    el.appendChild(blank);
    f.choices.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c.code;
      opt.textContent = c.code + " : " + c.label;
      el.appendChild(opt);
    });
    read = () => el.value;
  } else if (isDateField(f)) {
    // 날짜 달력 — input[type=date]의 YYYY-MM-DD를 YYYYMMDD로 변환
    el = document.createElement("input");
    el.type = "date";
    read = () => (el.value ? el.value.replace(/-/g, "") : "");
  } else {
    // 텍스트 입력 — 항목한글명을 가이드(placeholder)로
    el = document.createElement("input");
    el.type = "text";
    el.placeholder = f.description ? f.name_kr + " (" + f.description + ")" : f.name_kr;
    read = () => el.value.trim();
  }
  row.appendChild(el);

  // 설명(선택지 목록 등)을 라벨 아래 안내로 표시
  const descText = f.choices && f.choices.length > 0
    ? f.choices.map((c) => c.code + ":" + c.label).join(", ")
    : f.description;
  if (descText) {
    const desc = document.createElement("div");
    desc.className = "desc";
    desc.textContent = descText;
    row.appendChild(desc);
  }

  form.appendChild(row);
  return { field: f, el, read };
}

// ── 레이어 닫기: 닫기 버튼 / 배경(딤) 클릭 / Esc ────────────────────────
if (apiFormClose) apiFormClose.addEventListener("click", closeOverlay);
if (apiFormOverlay) {
  apiFormOverlay.addEventListener("click", (e) => {
    if (e.target === apiFormOverlay) closeOverlay(); // 모달 바깥(딤 영역) 클릭 시 닫기
  });
}
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && apiFormOverlay && !apiFormOverlay.classList.contains("hidden")) {
    closeOverlay();
  }
});

// ── 초기화 — 트리는 기본 펼침이라 로드 시 바로 채운다 ───────────────────
if (directTreeDetails) {
  directTreeDetails.addEventListener("toggle", () => {
    if (directTreeDetails.open) loadDirectTree();
  });
  if (directTreeDetails.open) loadDirectTree();
}
