// API 명세 페이지 (api.html) — docs/api/md 트리 탐색 + 명세 보기 + 테스트 호출.
//
// 흐름: /api/spec/tree 로 카테고리 트리 로드 → 파일 클릭 시 /api/spec/detail 로
// md 원문 + 필드 목록(기본값 포함)을 받아 편집 폼 구성 → "전송" 시
// /api/spec/execute 로 실제 KB API 호출 → 원본 JSON 응답 표시.

const treeBox = document.getElementById("spec-tree");
const emptyBox = document.getElementById("spec-empty");
const detailBox = document.getElementById("spec-detail");
const titleEl = document.getElementById("spec-title");
const endpointEl = document.getElementById("spec-endpoint");
const fieldsBox = document.getElementById("spec-fields");
const jsonPreview = document.getElementById("spec-json-preview");
const warningEl = document.getElementById("spec-warning");
const sendBtn = document.getElementById("spec-send");
const resetBtn = document.getElementById("spec-reset");
const requestPanel = document.getElementById("spec-request-panel");
const responsePanel = document.getElementById("spec-response-panel");
const responseEl = document.getElementById("spec-response");
const mdBox = document.getElementById("spec-md");

let currentDetail = null; // /api/spec/detail 응답
let activeFileEl = null;
let fileIndex = []; // 트리의 모든 파일 [{file, el, ancestors: [details...]}] — 상태 복원용

// 다른 페이지(실행/설정)에 갔다 와도 직전에 보던 명세가 그대로 열리도록 저장하는 키
const LAST_SPEC_KEY = "kbsec_spec_last_path";

// 주문/정정/취소 계열 코드 접두어 — 실거래 경고 표시용 (조회 계열 SSQM/GSS 등과 구분)
const ORDER_CODE_RE = /^(SSAM|SKAM)/;

// ── 트리 렌더링 ────────────────────────────────────────────────────────
async function loadTree() {
  try {
    const r = await apiGet("/api/spec/tree");
    treeBox.innerHTML = "";
    fileIndex = [];
    r.tree.forEach((cat) => treeBox.appendChild(renderDir(cat, 0, [])));
    restoreLastOrSelectFirst();
  } catch (e) {
    treeBox.textContent = "목록을 불러오지 못했습니다.";
  }
}

function renderDir(node, depth, ancestors) {
  const details = document.createElement("details");
  details.className = "tree-dir depth-" + depth;
  if (depth === 0) details.open = false;

  const summary = document.createElement("summary");
  summary.textContent = node.name;
  const count = countFiles(node);
  const badge = document.createElement("span");
  badge.className = "tree-count";
  badge.textContent = count;
  summary.appendChild(badge);
  details.appendChild(summary);

  const chain = ancestors.concat([details]);
  node.dirs.forEach((d) => details.appendChild(renderDir(d, depth + 1, chain)));
  node.files.forEach((f) => {
    const item = document.createElement("div");
    item.className = "tree-file";
    item.textContent = f.label;
    item.addEventListener("click", () => selectFile(f, item));
    details.appendChild(item);
    fileIndex.push({ file: f, el: item, ancestors: chain });
  });
  return details;
}

function restoreLastOrSelectFirst() {
  // 직전에 보던 명세가 있으면 그대로, 없으면(최초 방문) 목록의 첫 번째 API를 펼쳐 보여준다.
  const lastPath = localStorage.getItem(LAST_SPEC_KEY);
  let entry = lastPath ? fileIndex.find((e) => e.file.path === lastPath) : null;
  if (!entry) entry = fileIndex[0];
  if (!entry) return;
  entry.ancestors.forEach((d) => (d.open = true)); // 트리를 해당 위치까지 펼침
  selectFile(entry.file, entry.el);
  entry.el.scrollIntoView({ block: "nearest" });
}

function countFiles(node) {
  return node.files.length + node.dirs.reduce((acc, d) => acc + countFiles(d), 0);
}

// ── 파일 선택 → 상세 로드 ──────────────────────────────────────────────
async function selectFile(file, el) {
  if (activeFileEl) activeFileEl.classList.remove("active");
  activeFileEl = el;
  el.classList.add("active");

  try {
    const d = await apiGet("/api/spec/detail?path=" + encodeURIComponent(file.path));
    if (d.error) throw new Error(d.error);
    currentDetail = d;
    localStorage.setItem(LAST_SPEC_KEY, file.path); // 다음 방문 때 이 명세를 그대로 복원
    renderDetail(d);
  } catch (e) {
    alert("명세를 불러오지 못했습니다: " + e);
  }
}

function renderDetail(d) {
  emptyBox.classList.add("hidden");
  detailBox.classList.remove("hidden");
  detailBox.classList.remove("fade-in");
  void detailBox.offsetWidth; // 리플로우로 애니메이션 재시작
  detailBox.classList.add("fade-in");

  titleEl.textContent = d.label;
  endpointEl.textContent = d.endpoint ? "POST " + d.endpoint : "(실행 엔드포인트 없음 — 명세 열람 전용)";
  warningEl.classList.toggle("hidden", !(d.code && ORDER_CODE_RE.test(d.code)));

  // 요청 폼 — 실행 가능한 API만
  requestPanel.classList.toggle("hidden", !d.executable);
  responsePanel.classList.add("hidden");
  responseEl.textContent = "";

  if (d.executable) {
    renderFields(d.fields);
    updateJsonPreview();
  }

  mdBox.innerHTML = renderMarkdown(d.markdown);
  // 명세 문서를 접힌 상태로 두지 않고 항상 펼쳐서 보여준다 (사용자 요청 — 선택 즉시 전체 명세 확인)
  const mdDetails = mdBox.closest("details");
  if (mdDetails) mdDetails.open = true;
}

// ── 요청 필드 폼 ───────────────────────────────────────────────────────
function renderFields(fields) {
  fieldsBox.innerHTML = "";
  if (fields.length === 0) {
    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = "INPUT 파라미터가 없습니다 — 그대로 전송하면 됩니다.";
    fieldsBox.appendChild(p);
    return;
  }
  fields.forEach((f) => {
    const row = document.createElement("div");
    row.className = "spec-field-row";

    const label = document.createElement("label");
    label.innerHTML = "";
    label.textContent = f.name_kr + " ";
    const en = document.createElement("span");
    en.className = "en";
    // KB 명세의 필수여부(Y/N)는 부정확해 '*' 표시를 하지 않는다.
    en.textContent = f.name_en;
    label.appendChild(en);
    row.appendChild(label);

    let inputEl;
    if (f.choices.length > 0) {
      inputEl = document.createElement("select");
      f.choices.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.code;
        opt.textContent = c.code + " : " + c.label;
        inputEl.appendChild(opt);
      });
      // 기본값이 선택지에 없으면(공백 등) 직접입력 옵션 추가
      if (!f.choices.some((c) => c.code === f.default)) {
        const opt = document.createElement("option");
        opt.value = f.default;
        opt.textContent = "(기본값)";
        inputEl.appendChild(opt);
      }
      inputEl.value = f.default;
    } else {
      inputEl = document.createElement("input");
      inputEl.type = "text";
      inputEl.value = f.default;
      inputEl.placeholder = f.description || "";
    }
    inputEl.dataset.field = f.name_en;
    inputEl.addEventListener("input", updateJsonPreview);
    inputEl.addEventListener("change", updateJsonPreview);
    row.appendChild(inputEl);

    if (f.description) {
      const desc = document.createElement("div");
      desc.className = "desc";
      desc.textContent = f.description;
      row.appendChild(desc);
    }
    fieldsBox.appendChild(row);
  });
}

function collectBody() {
  const body = {};
  fieldsBox.querySelectorAll("[data-field]").forEach((el) => {
    body[el.dataset.field] = el.value;
  });
  return body;
}

function updateJsonPreview() {
  const payload = {
    dataBody: collectBody(),
    dataHeader: { ipAddr: "(서버 자동)", macAddr: "(서버 자동)" },
  };
  jsonPreview.textContent = JSON.stringify(payload, null, 4);
}

resetBtn.addEventListener("click", () => {
  if (currentDetail) {
    renderFields(currentDetail.fields);
    updateJsonPreview();
  }
});

// ── 전송 ───────────────────────────────────────────────────────────────
sendBtn.addEventListener("click", async () => {
  if (!currentDetail || !currentDetail.executable) return;
  if (currentDetail.code && ORDER_CODE_RE.test(currentDetail.code)) {
    if (!confirm("주문 계열 API입니다. 운영환경(실거래)으로 실제 주문이 전송됩니다.\n계속할까요?")) return;
  }
  sendBtn.disabled = true;
  sendBtn.textContent = "전송 중...";
  try {
    const r = await apiPost("/api/spec/execute", {
      code: currentDetail.code,
      data_body: collectBody(),
    });
    responsePanel.classList.remove("hidden");
    responseEl.textContent = JSON.stringify(r.body !== undefined ? r.body : r, null, 4);
    responseEl.classList.toggle("err", r.success === false);
    responsePanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (e) {
    responsePanel.classList.remove("hidden");
    responseEl.textContent = "서버 통신 오류: " + e;
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "전송";
    refreshStatusBadge();
  }
});

// ── 초소형 마크다운 렌더러 (명세 md 전용: 제목/표/구분선/코드) ──────────
function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderMarkdown(md) {
  const lines = md.split("\n");
  const out = [];
  let tableRows = [];

  function flushTable() {
    if (tableRows.length === 0) return;
    const rows = tableRows.filter((cells) => !cells.every((c) => /^-+$/.test(c.replace(/\s/g, "").replace(/:/g, ""))));
    let html = "<table><thead><tr>";
    rows[0].forEach((c) => (html += "<th>" + inline(c) + "</th>"));
    html += "</tr></thead><tbody>";
    rows.slice(1).forEach((cells) => {
      html += "<tr>";
      cells.forEach((c) => (html += "<td>" + inline(c) + "</td>"));
      html += "</tr>";
    });
    html += "</tbody></table>";
    out.push(html);
    tableRows = [];
  }

  function inline(text) {
    return escapeHtml(text)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
  }

  lines.forEach((line) => {
    const t = line.trim();
    if (t.startsWith("|")) {
      tableRows.push(t.replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim()));
      return;
    }
    flushTable();
    if (t === "---") {
      out.push("<hr>");
    } else if (t.startsWith("### ")) {
      out.push("<h4>" + inline(t.slice(4)) + "</h4>");
    } else if (t.startsWith("## ")) {
      out.push("<h3>" + inline(t.slice(3)) + "</h3>");
    } else if (t.startsWith("# ")) {
      out.push("<h2>" + inline(t.slice(2)) + "</h2>");
    } else if (t.startsWith("- ")) {
      out.push("<div class='md-li'>• " + inline(t.slice(2)) + "</div>");
    } else if (t === "") {
      out.push("");
    } else {
      out.push("<p>" + inline(t) + "</p>");
    }
  });
  flushTable();
  return out.join("\n");
}

// ── 초기화 ─────────────────────────────────────────────────────────────
refreshStatusBadge();
loadTree();
