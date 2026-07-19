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

// 헤더의 로그인 상태 배지를 갱신 (index.html/settings.html 공용).
// 헤더에 #session-actions(토큰재발급/화면초기화/로그아웃 — 실행 화면 전용)가 있으면
// 로그인 상태일 때만 보이도록 함께 토글한다.
async function refreshStatusBadge() {
  const badge = document.getElementById("status-badge");
  const actions = document.getElementById("session-actions");
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
    if (actions) actions.classList.toggle("hidden", !s.logged_in);
    return s;
  } catch (e) {
    badge.textContent = "서버 연결 실패";
    badge.className = "off";
    if (actions) actions.classList.add("hidden");
    return null;
  }
}

// ── 헤더 세션 버튼 (토큰재발급/로그아웃) — 3개 페이지 공통 바인딩 ──────
// 페이지별 후처리는 window 훅으로 위임한다: 실행 화면(app.js)은 출력창에 결과를
// 남기고 로그아웃 시 화면/히스토리를 함께 비우며, 훅이 없는 페이지는 alert로 알린다.
(function bindSessionActions() {
  const refreshBtn = document.getElementById("btn-token-refresh");
  const logoutBtn = document.getElementById("btn-logout");

  if (refreshBtn) {
    refreshBtn.addEventListener("click", async () => {
      refreshBtn.disabled = true;
      try {
        const r = await apiPost("/api/token/refresh", {});
        const msg = r.message || (r.success ? "토큰을 재발급했습니다." : "토큰 재발급 실패");
        if (window.onTokenRefreshed) window.onTokenRefreshed(r);
        else alert(msg);
      } catch (e) {
        if (window.onTokenRefreshed) window.onTokenRefreshed({ success: false, message: "서버 통신 오류: " + e });
        else alert("서버 통신 오류: " + e);
      } finally {
        refreshBtn.disabled = false;
        refreshStatusBadge();
      }
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      if (!window.confirm("로그아웃할까요? 발급받은 KB 토큰이 폐기됩니다.")) return;
      logoutBtn.disabled = true;
      try {
        const r = await apiPost("/api/logout", {});
        if (window.onSessionLogout) window.onSessionLogout(r);
        else alert(r.message || (r.success ? "로그아웃되었습니다." : "로그아웃 실패"));
      } catch (e) {
        alert("서버 통신 오류: " + e);
      } finally {
        logoutBtn.disabled = false;
        refreshStatusBadge();
      }
    });
  }
})();
