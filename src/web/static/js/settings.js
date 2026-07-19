// 설정 화면(settings.html) — 필수(client_key/client_secret) + 선택(Claude/텔레그램) 입력.
// "저장하고 로그인" = POST /api/settings 한 번으로 설정 반영 + KB 토큰 발급까지 처리된다.
// 서버는 시크릿 원문을 절대 돌려주지 않으므로(마스킹된 상태만), 입력칸을 저장값으로
// 되채우는 동작은 없다 — 상태 표는 "설정됨/미설정"만 보여준다.

const form = document.getElementById("settings-form");
const saveBtn = document.getElementById("save-btn");
const formMsg = document.getElementById("form-msg");

function showMsg(ok, text) {
  formMsg.textContent = text;
  formMsg.className = "form-msg " + (ok ? "ok" : "err");
}

function fmtRemaining(seconds) {
  if (seconds == null) return "만료/없음";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return (h > 0 ? h + "시간 " : "") + m + "분";
}

async function refreshStatusTable() {
  const s = await refreshStatusBadge();
  if (!s) return;
  document.getElementById("st-login").textContent = s.logged_in ? "✅ 로그인됨" : "❌ 미로그인";
  document.getElementById("st-env").textContent = s.logged_in ? s.env_name : "-";
  document.getElementById("st-token").textContent = s.logged_in ? fmtRemaining(s.token_remaining_seconds) : "-";
  document.getElementById("st-claude").textContent = s.claude_configured
    ? "✅ 설정됨" + (s.claude_model ? " (" + s.claude_model + ")" : "")
    : "미설정 (자연어 명령 사용 불가)";
  document.getElementById("st-telegram").textContent = s.telegram_configured ? "✅ 설정됨" : "미설정 (파일은 경로만 표시)";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const body = {
    env: document.getElementById("env").value,
    client_key: document.getElementById("client_key").value.trim(),
    client_secret: document.getElementById("client_secret").value.trim(),
    claude_api_key: document.getElementById("claude_api_key").value.trim(),
    claude_model: document.getElementById("claude_model").value.trim(),
    telegram_token: document.getElementById("telegram_token").value.trim(),
    telegram_chat_id: document.getElementById("telegram_chat_id").value.trim(),
  };

  if (!body.client_key || !body.client_secret) {
    showMsg(false, "앱키(client_key)와 앱시크릿(client_secret)은 필수입니다.");
    return;
  }

  saveBtn.disabled = true;
  saveBtn.textContent = "로그인 중...";
  try {
    const r = await apiPost("/api/settings", body);
    showMsg(r.success, r.message || (r.success ? "저장/로그인 완료" : "실패"));
    if (r.success) {
      // 성공하면 시크릿 입력칸은 비워둔다(브라우저 화면에 남겨두지 않음)
      document.getElementById("client_key").value = "";
      document.getElementById("client_secret").value = "";
      document.getElementById("claude_api_key").value = "";
      document.getElementById("telegram_token").value = "";
    }
  } catch (err) {
    showMsg(false, "서버 통신 오류: " + err);
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = "저장하고 로그인";
    refreshStatusTable();
  }
});

refreshStatusTable();
