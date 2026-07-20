// index.html "사용 방법" 패널 하단 — docs/api/md 74개 API 전체를 업무구분 폴더
// 구조 그대로 계층적 접기/펼치기 트리로 보여주고, 클릭하면 "명령 실행" 입력창에
// 실행 가능한 "/코드-API명 {"파라미터명":"설명"} ..." 형태로 채워넣는다.
//
// api.html의 apidoc.js(renderDir/countFiles)와 같은 /api/spec/tree, /api/spec/detail
// 엔드포인트를 그대로 재사용한다 — 새 백엔드 엔드포인트는 만들지 않는다.
// 실제 실행은 src/utils/direct_api_command.py가 담당하며, 여기서는 그 커맨드가
// 기대하는 문자열(토큰 + 위치 파라미터 안내)을 그대로 조립해 입력창에 넣기만 한다.

const directTreeDetails = document.getElementById("direct-cmd-guide");
const directTreeBox = document.getElementById("direct-cmd-tree");
const cmdInputEl = document.getElementById("cmd-input");

// 매수/매도/정정/취소 등 주문 계열 코드 접두어 — apidoc.js의 ORDER_CODE_RE와 동일 규칙.
const DIRECT_ORDER_CODE_RE = /^(SSAM|SKAM)/;

let directTreeLoaded = false;

// TR코드가 있는 파일만 전용 커맨드로 실행 가능하다(build_token_index가 code 없는
// 항목을 제외 — OAuth 토큰 발급/폐기 2건은 /login·로그아웃이 담당하므로 제외).
// 트리에도 실행 가능한 것만 노출해 "74개" 라벨과 화면을 일치시킨다.
function countDirectFiles(node) {
  const own = node.files.filter((f) => f.code).length;
  return own + node.dirs.reduce((acc, d) => acc + countDirectFiles(d), 0);
}

function renderDirectDir(node, depth) {
  // 실행 가능한 파일이 하나도 없는 디렉터리(예: OAuth)는 렌더링하지 않는다.
  if (countDirectFiles(node) === 0) return null;

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

function renderDirectFile(file) {
  const item = document.createElement("div");
  item.className = "tree-file";
  item.textContent = file.label + (file.code && DIRECT_ORDER_CODE_RE.test(file.code) ? " ⚠️" : "");
  item.title = file.code && DIRECT_ORDER_CODE_RE.test(file.code)
    ? "주문 계열 API — 클릭 후 값을 채워 실행하면 실제 거래가 발생합니다"
    : "";
  item.addEventListener("click", () => fillDirectCommand(file));
  return item;
}

async function fillDirectCommand(file) {
  try {
    const detail = await apiGet("/api/spec/detail?path=" + encodeURIComponent(file.path));
    if (detail.error) throw new Error(detail.error);

    const token = file.label.replace(/ /g, "_");
    // 백엔드 positional_fields()와 동일하게 모든 입력 필드를 순서대로 placeholder로 채운다.
    // (KB 명세가 종목코드 등 핵심 파라미터도 필수여부 N으로 표기하는 경우가 많아 필수로 거르지 않음)
    const paramText = (detail.fields || [])
      .map((f) => {
        const desc = f.choices && f.choices.length > 0
          ? f.choices.map((c) => `${c.code}:${c.label}`).join(", ")
          : (f.description || "");
        return `{"${f.name_kr}":"${desc}"}`;
      })
      .join(" ");

    cmdInputEl.value = paramText ? `/${token} ${paramText}` : `/${token}`;
    cmdInputEl.focus();
  } catch (e) {
    alert("명세를 불러오지 못했습니다: " + e);
  }
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

if (directTreeDetails) {
  directTreeDetails.addEventListener("toggle", () => {
    if (directTreeDetails.open) loadDirectTree();
  });
}
