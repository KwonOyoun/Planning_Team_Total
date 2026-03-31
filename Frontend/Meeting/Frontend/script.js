document.addEventListener('DOMContentLoaded', function () {

    console.log("🔥 script.js LOADED v2026-01-20-fixed");

    /* =========================
       로그인
    ========================= */
    document.getElementById('login-form').addEventListener('submit', async function (e) {
        e.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        showLoading("회의 목록을 불러오는 중입니다.");

        try {
            const res = await fetch('/Meeting/api/login', {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });

            if (!res.ok) throw new Error("로그인 요청 실패");

            const data = await res.json();
            if (!data.success) {
                alert("로그인 실패");
                return;
            }

            window.currentUsername = username;

            document.getElementById('login-section').classList.add('hidden');
            document.getElementById('meeting-list-section').classList.remove('hidden');

            await loadMeetingListFromServer(username);

        } catch (err) {
            console.error(err);
            alert("회의 목록을 불러오는 중 오류가 발생했습니다.");
        } finally {
            // ✅ 어떤 경우든 로딩 종료
            hideLoading();
        }
    });

    /* =========================
       뒤로가기 버튼
    ========================= */
    document.getElementById('back-to-list').addEventListener('click', () => {
        document.getElementById('meeting-detail-section').classList.add('hidden');
        document.getElementById('meeting-list-section').classList.remove('hidden');
    });

    document.getElementById('back-to-edit').addEventListener('click', () => {
        document.getElementById('preview-section').classList.add('hidden');
        document.getElementById('meeting-detail-section').classList.remove('hidden');
    });

    document.getElementById('add-participant').addEventListener('click', () => {
        addParticipantField();
    });

    /* =========================
       회의록 생성
    ========================= */
    document.getElementById('write-minutes-btn').addEventListener('click', async function () {
        try {
            showLoading();

            document.getElementById('meeting-list-section')?.classList.add('hidden');
            document.getElementById('meeting-detail-section')?.classList.add('hidden');
            document.getElementById('preview-section')?.classList.add('hidden');

            const projectName = document.getElementById('project-name').value;
            const meetingName = document.getElementById('meeting-name').value;
            const meetingStart = document.getElementById('meeting-start').value;
            const meetingEnd = document.getElementById('meeting-end').value;
            const meetingLocation = document.getElementById('meeting-location').value;
            const summaryText = document.getElementById('meeting-summary').value;

            const participants = [];
            document.querySelectorAll('.participant-card').forEach(card => {
                participants.push({
                    department: card.querySelector('[id^="department-"]').value,
                    name: card.querySelector('[id^="name-"]').value,
                    position: card.querySelector('[id^="position-"]').value,
                });
            });

            const res = await fetch('/Meeting/api/generate_minutes_body', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    projectName,
                    meetingName,
                    meetingStart,
                    meetingEnd,
                    meetingLocation,
                    participants,
                    summaryText
                })
            });

            if (!res.ok) throw new Error("회의록 생성 실패");

            const data = await res.json();
            if (!data.success) throw new Error(data.error);

            generatePreview(data.minutesBody);
            document.getElementById('preview-section').classList.remove('hidden');

        } catch (err) {
            console.error(err);
            alert(err.message || '회의록 생성 오류');
        } finally {
            hideLoading();
        }
    });

    /* =========================
       HWPX 다운로드
    ========================= */
    document.getElementById('download-hwpx')?.addEventListener('click', async function () {
        try {
            console.log("📥 HWPX 다운로드 버튼 클릭");

            const projectName = document.getElementById('project-name').value;
            const meetingName = document.getElementById('meeting-name').value;
            const meetingStart = document.getElementById('meeting-start').value;
            const meetingEnd = document.getElementById('meeting-end').value;
            const meetingLocation = document.getElementById('meeting-location').value;

            const minutesBody =
                document.querySelector('#preview-content .whitespace-pre-line')?.innerText || "";

            const participants = [];
            document.querySelectorAll('.participant-card').forEach(card => {
                participants.push({
                    department: card.querySelector('[id^="department-"]').value,
                    name: card.querySelector('[id^="name-"]').value,
                    position: card.querySelector('[id^="position-"]').value,
                });
            });

            const res = await fetch('/Meeting/api/generate_hwpx', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    projectName,
                    meetingName,
                    meetingStart,
                    meetingEnd,
                    meetingLocation,
                    participants,
                    minutesBody,
                    author: window.currentAuthor || ""
                })
            });

            if (!res.ok) {
                const t = await res.text();
                throw new Error(`HWPX 생성 실패: ${res.status} ${t}`);
            }

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);

            const safeMeetingName =
                meetingName.replace(/[\\/:*?"<>|]/g, '').trim() || 'meeting';

            const date =
                meetingStart
                    ? meetingStart.replace(/[^0-9]/g, '').slice(2, 8)
                    : '000000';

            const filename = `${date}_${safeMeetingName}.hwpx`;

            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            URL.revokeObjectURL(url);

            alert('HWPX 파일이 다운로드되었습니다.');

        } catch (err) {
            console.error(err);
            alert("HWPX 다운로드 중 오류 발생");
        }
    });

});

/* =========================
   회의 목록 로드
========================= */
async function loadMeetingListFromServer(username) {
    const meetingCards = document.getElementById('meeting-cards');
    meetingCards.innerHTML = "";

    try {
        const res = await fetch(`/Meeting/api/meetings?username=${username}`, {
            method: "GET"
        });

        if (!res.ok) throw new Error("회의 목록 조회 실패");

        const data = await res.json();
        const meetings = data.meetings || [];

        if (meetings.length === 0) {
            meetingCards.innerHTML = "<p class='text-gray-500'>회의 기안이 없습니다.</p>";
            return;
        }

        meetings.forEach(meeting => {
            const card = document.createElement('div');
            card.className = 'meeting-card bg-white p-4 border rounded-lg cursor-pointer hover:bg-gray-50';

            card.innerHTML = `
                <h3 class="text-lg font-semibold text-gray-800">${meeting.title}</h3>
                <div class="flex items-center text-sm text-gray-500 mt-2 space-x-4">
                    <span>${meeting.author || '-'}</span>
                    <span>${meeting.date || '-'}</span>
                </div>
            `;

            card.addEventListener('click', async () => {
                try {
                    showLoading("회의 정보를 불러오는 중입니다.");

                    window.currentAuthor = meeting.author || "";

                    const res = await fetch(
                        `/Meeting/api/meetings/${meeting.dom_index}`,
                        {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ author: window.currentAuthor })
                        }
                    );

                    if (!res.ok) throw new Error("회의 조회 실패");

                    const data = await res.json();
                    if (!data.parsed) throw new Error("회의 파싱 결과 없음");

                    const parsed = parseMeetingSummary(data.parsed);

                    document.getElementById('project-name').value = parsed.fullProjectName || "";
                    document.getElementById('meeting-name').value = parsed.meetingName || "";

                    const { start, end } = parseKoreanDateRange(parsed.meetingDate);

                    document.getElementById('meeting-start').value = start;
                    document.getElementById('meeting-end').value = end;

                    document.getElementById('meeting-location').value =
                        parsed.meetingLocation || "";
                    document.getElementById('meeting-summary').value = data.parsed;

                    const container = document.getElementById('participants-container');
                    container.innerHTML = "";
                    parsed.participants.forEach(p =>
                        addParticipantField(p.department, p.name, "")
                    );

                    document.getElementById('meeting-list-section').classList.add('hidden');
                    document.getElementById('meeting-detail-section').classList.remove('hidden');

                } catch (err) {
                    console.error(err);
                    alert("회의 내용을 불러오지 못했습니다.");
                } finally {
                    hideLoading();   // ✅ 무조건 실행
                }
            });

            meetingCards.appendChild(card);
        });

        feather.replace();

    } catch (err) {
        console.error(err);
        alert("회의 목록을 불러오지 못했습니다. err(2)");
    }
}

function addParticipantField(department = '', name = '', position = '') {
    const participantId = Date.now();
    const participantsContainer = document.getElementById('participants-container');
    
    const participantDiv = document.createElement('div');
    participantDiv.className = 'participant-card bg-gray-50 p-4 rounded-lg border border-gray-200';
    participantDiv.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
                <label for="department-${participantId}" class="block text-sm font-medium text-gray-700">소속</label>
                <input type="text" id="department-${participantId}" value="${department}" 
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
            </div>
            <div>
                <label for="name-${participantId}" class="block text-sm font-medium text-gray-700">성함</label>
                <input type="text" id="name-${participantId}" value="${name}" 
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
            </div>
            <div class="flex items-end">
                <div class="flex-grow">
                    <label for="position-${participantId}" class="block text-sm font-medium text-gray-700">직책</label>
                    <input type="text" id="position-${participantId}" value="${position}" 
                        class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <button type="button" class="ml-2 text-red-500 hover:text-red-700 p-2">
                    <i data-feather="trash-2" class="w-4 h-4"></i>
                </button>
            </div>
        </div>
    `;
    
    // Add delete functionality
    const deleteBtn = participantDiv.querySelector('button');
    deleteBtn.addEventListener('click', function() {
        participantsContainer.removeChild(participantDiv);
    });
    
    participantsContainer.appendChild(participantDiv);
    feather.replace();
}

function generatePreview(minutesBody) {
    const previewContent = document.getElementById('preview-content');

    const projectName = document.getElementById('project-name').value;
    const meetingName = document.getElementById('meeting-name').value;
    const meetingLocation = document.getElementById('meeting-location').value;
    const startValue = document.getElementById('meeting-start')?.value;
    const endValue = document.getElementById('meeting-end')?.value;

    let formattedDate = '-';

    if (startValue && endValue) {
        const start = new Date(startValue);
        const end = new Date(endValue);

        if (!isNaN(start) && !isNaN(end)) {
            const datePart = start.toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            const startTime = start.toLocaleTimeString('ko-KR', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });

            const endTime = end.toLocaleTimeString('ko-KR', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });

            formattedDate = `${datePart} ${startTime} ~ ${endTime}`;
        }
    }


    previewContent.innerHTML = `
        <h1 class="text-2xl font-bold text-center mb-6">
            ${meetingName} 회의록
        </h1>

        <table class="w-full mb-6 border">
            <tr><th>사업명</th><td>${projectName}</td></tr>
            <tr><th>회의명</th><td>${meetingName}</td></tr>
            <tr><th>회의일시</th><td>${formattedDate}</td></tr>
            <tr><th>회의장소</th><td>${meetingLocation}</td></tr>
        </table>

        <h3 class="font-semibold mb-2">회의 내용</h3>
        <div class="whitespace-pre-line border p-4 rounded">
            ${minutesBody}
        </div>
    `;
}


function generatePreviewWithMinutesBody(minutesBody) {
    const previewContent = document.getElementById('preview-content');

    const projectName = document.getElementById('project-name').value;
    const meetingName = document.getElementById('meeting-name').value;
    const meetingDateValue = document.getElementById('meeting-date').value; // datetime-local
    const meetingLocation = document.getElementById('meeting-location').value;

    // datetime-local → 사람이 읽는 형태로 표시
    let formattedDate = '-';
    if (meetingDateValue) {
        const d = new Date(meetingDateValue);
        if (!isNaN(d)) {
            formattedDate = d.toLocaleString('ko-KR', {
                year: 'numeric', month: 'long', day: 'numeric',
                hour: '2-digit', minute: '2-digit', weekday: 'long'
            });
        }
    }

    const participants = [];
    document.querySelectorAll('.participant-card').forEach(card => {
        const department = card.querySelector('input[id^="department-"]')?.value || "";
        const name = card.querySelector('input[id^="name-"]')?.value || "";
        const position = card.querySelector('input[id^="position-"]')?.value || "";
        if (department || name || position) participants.push({ department, name, position });
    });

    const participantRows = participants.map(p => `
        <tr>
            <td class="border px-2 py-1">${escapeHtml(p.department)}</td>
            <td class="border px-2 py-1">${escapeHtml(p.name)}</td>
            <td class="border px-2 py-1">${escapeHtml(p.position || "")}</td>
        </tr>
    `).join("");

    previewContent.innerHTML = `
        <h1 class="text-2xl font-bold text-center mb-6">${escapeHtml(meetingName)} 회의록</h1>

        <div class="mb-8">
            <h3 class="text-lg font-semibold mb-2">기본 정보</h3>
            <table class="w-full border">
                <tr><th class="border px-2 py-1 w-1/4 bg-gray-50">사업명</th><td class="border px-2 py-1">${escapeHtml(projectName)}</td></tr>
                <tr><th class="border px-2 py-1 bg-gray-50">회의명</th><td class="border px-2 py-1">${escapeHtml(meetingName)}</td></tr>
                <tr><th class="border px-2 py-1 bg-gray-50">회의일시</th><td class="border px-2 py-1">${escapeHtml(formattedDate)}</td></tr>
                <tr><th class="border px-2 py-1 bg-gray-50">회의장소</th><td class="border px-2 py-1">${escapeHtml(meetingLocation)}</td></tr>
            </table>
        </div>

        <div class="mb-8">
            <h3 class="text-lg font-semibold mb-2">참석자 목록</h3>
            <table class="w-full border">
                <thead>
                    <tr>
                        <th class="border px-2 py-1 bg-gray-50">소속</th>
                        <th class="border px-2 py-1 bg-gray-50">성함</th>
                        <th class="border px-2 py-1 bg-gray-50">직책</th>
                    </tr>
                </thead>
                <tbody>
                    ${participantRows || `<tr><td class="border px-2 py-2" colspan="3">-</td></tr>`}
                </tbody>
            </table>
        </div>

        <div>
            <h3 class="text-lg font-semibold mb-2">회의 내용</h3>
            <div class="text-gray-700 whitespace-pre-line border rounded p-4">
                ${escapeHtml(minutesBody)}
            </div>
        </div>
    `;
}

// XSS 방지용 간단 escape
function escapeHtml(str) {
    return String(str ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function loadMeetingDetailsFromServer(meetingId) {
    try {
        const res = await fetch(
            `/Meeting/api/meetings/${meetingId}`
        );

        if (!res.ok) {
            throw new Error("회의 상세 조회 실패");
        }

        const data = await res.json();
        console.log("회의 상세 데이터:", data);

        // 🔹 1️⃣ 폼 채우기
        fillMeetingForm(data);

        // 🔹 2️⃣ 화면 전환
        document.getElementById('meeting-list-section').classList.add('hidden');
        document.getElementById('meeting-detail-section').classList.remove('hidden');

    } catch (err) {
        console.error(err);
        alert("회의 상세를 불러오지 못했습니다. err(3)");
    }
}

function fillMeetingForm(data) {
    // 기본 정보
    document.getElementById('project-name').value = data.projectName;
    document.getElementById('meeting-name').value = data.meetingName;
    document.getElementById('meeting-date').value = data.date;
    document.getElementById('meeting-location').value = data.location;

    // 참석자 초기화
    const participantsContainer = document.getElementById('participants-container');
    participantsContainer.innerHTML = '';

    // 참석자 추가
    data.participants.forEach(p => {
        addParticipantField(p.department, p.name, p.position);
    });
}

// full_text 파싱 함수
function parseMeetingSummary(summaryText) {
    const result = {
        fullProjectName: "",
        meetingName: "",
        meetingDate: "",
        meetingLocation: "",
        participants: []
    };

    // 전체사업명
    const fullProjectMatch = summaryText.match(/- 전체사업명\s*:\s*(.+)/);
    if (fullProjectMatch) {
        result.fullProjectName = normalizeValue(fullProjectMatch[1]);
    }

    // 회의명
    const meetingNameMatch = summaryText.match(/- 회의명\s*:\s*(.+)/);
    if (meetingNameMatch) {
        result.meetingName = normalizeValue(meetingNameMatch[1]);
    }

    // 회의일시
    const meetingDateMatch = summaryText.match(/회의일시\s*:\s*(.+)/);
    if (meetingDateMatch) {
        result.meetingDate = normalizeValue(meetingDateMatch[1]);
    }

    // 회의장소
    const meetingLocationMatch = summaryText.match(/- 회의장소\s*:\s*(.+)/);
    if (meetingLocationMatch) {
        result.meetingLocation = normalizeValue(meetingLocationMatch[1]);
    }

    // 참석자
    const participantRegex = /\(\d+\)\s*([^\/\n]+)\/([^\n]+)/g;
    let match;
    while ((match = participantRegex.exec(summaryText)) !== null) {
        result.participants.push({
            department: normalizeValue(match[1]),
            name: normalizeValue(match[2])
        });
    }

    return result;
}

// 시간 변환
function parseKoreanDateRange(dateText) {
    if (!dateText) return { start: "", end: "" };

    // ✅ 요일 포함 버전
    const regex =
        /(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일(?:\([^)]+\))?\s*(\d{1,2}):(\d{2})\s*~\s*(\d{1,2}):(\d{2})/;

    const match = dateText.match(regex);
    if (!match) return { start: "", end: "" };

    const [_, y, m, d, sh, sm, eh, em] = match;

    const year = y;
    const month = m.padStart(2, "0");
    const day = d.padStart(2, "0");

    return {
        start: `${year}-${month}-${day}T${sh.padStart(2, "0")}:${sm}`,
        end: `${year}-${month}-${day}T${eh.padStart(2, "0")}:${em}`,
    };
}

function normalizeValue(v) {
    if (!v) return "";
    if (v.trim().toLowerCase() === "none") return "";
    return v.trim();
}

function showLoading(message = "회의록을 작성중입니다.") {
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) return;

    const textEl = overlay.querySelector('#loading-text');
    if (textEl) {
        textEl.innerText = message;
    }

    overlay.classList.remove('hidden');
}

function hideLoading() {
  document.getElementById('loading-overlay')?.classList.add('hidden');
}