// fetch 공통 래퍼 — 모든 화면이 이 함수로만 백엔드(/api/*)와 통신한다.
// 세션 식별은 HttpOnly 쿠키(kbsec_web_sid)가 자동으로 처리하므로 JS에서 다룰 것이 없다.

async function apiGet(path) {
  const res = await fetch(path, { headers: { "Accept": "application/json" } });
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

// 헤더의 로그인 상태 배지를 갱신 (index.html/settings.html 공용)
async function refreshStatusBadge() {
  const badge = document.getElementById("status-badge");
  if (!badge) return null;
  try {
    const s = await apiGet("/api/settings");
    if (s.logged_in) {
      badge.textContent = s.env_name + " 로그인됨";
      badge.className = "on";
    } else {
      badge.textContent = "미로그인 — 설정에서 앱키 입력";
      badge.className = "off";
    }
    return s;
  } catch (e) {
    badge.textContent = "서버 연결 실패";
    badge.className = "off";
    return null;
  }
}
