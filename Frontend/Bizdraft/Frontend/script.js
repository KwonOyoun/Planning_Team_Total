document.addEventListener('DOMContentLoaded', function () {

    /* ===============================
       DOM ELEMENTS
    =============================== */
    const keywordsForm = document.getElementById('keywordsForm');
    const titlesSection = document.getElementById('titlesSection');
    const proposalSection = document.getElementById('proposalSection');
    const titlesList = document.getElementById('titlesList');
    const proposalContent = document.getElementById('proposalContent');

    const hwpxdownloadBtn = document.getElementById('hwpxdownloadBtn');
    const pptxDownloadBtn = document.getElementById('pptxDownloadBtn');
    const rewriteBtn = document.getElementById('rewriteBtn');

    /* ===============================
       GLOBAL STATE
    =============================== */
    let currentSelectedTitle = null;
    let currentSelectedKeywords = [];

    // 🔥 서버에서 받아온 + 사용자가 수정한 프롬프트
    // prompt-sidebar.js 에서 수정되면 이 객체를 갱신하도록 설계
    window.currentPrompts = {};

    /* ===============================
       INITIAL PROMPT LOAD
    =============================== */
    fetch('/Bizdraft/prompts/default')
        .then(res => res.json())
        .then(data => {
            window.currentPrompts = data;
            console.log('초기 프롬프트 로드 완료', data);
        });

    /* ===============================
       KEYWORD INPUT HANDLING
    =============================== */
    window.addKeywordField = function () {
        const keywordInputs = document.getElementById('keywordInputs');
        const inputCount = keywordInputs.children.length;

        if (inputCount >= 5) {
            alert('최대 5개의 키워드까지 입력 가능합니다');
            return;
        }

        const newInput = document.createElement('div');
        newInput.className = 'flex items-center space-x-2';
        newInput.innerHTML = `
            <input type="text"
                    name="keywords"
                    placeholder="키워드 입력"
                    class="flex-1 px-4 py-2 border border-gray-300 rounded-lg">
            <button type="button"
                    onclick="this.parentNode.remove()"
                    class="p-2 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200">
                <i data-feather="x"></i>
            </button>
        `;
        keywordInputs.appendChild(newInput);
        feather.replace();
    };

    /* ===============================
       KEYWORD FORM SUBMIT
    =============================== */
    keywordsForm.addEventListener('submit', function (e) {
        e.preventDefault();

        titlesList.innerHTML = `
            <div class="text-center py-6 text-primary-600 font-medium">
                AI가 제목을 생성 중입니다...
            </div>
        `;
        titlesSection.classList.remove('hidden');

        const formData = new FormData(keywordsForm);
        const keywords = Array.from(formData.values())
            .map(v => v.trim())
            .filter(v => v !== '');

        fetch('/Bizdraft/api/keywords', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                keywords: keywords,                 // ✅ 배열 그대로
                prompts: window.currentPrompts      // ✅ 수정된 프롬프트
            })
        })
            .then(res => res.json())
            .then(data => {
                titlesList.innerHTML = '';

                (data.titles || []).forEach((title, index) => {
                    const el = document.createElement('div');
                    el.className = 'p-4 border rounded-lg hover:bg-primary-50 cursor-pointer';
                    el.innerHTML = `<h3 class="font-medium">${title}</h3>`;
                    el.addEventListener('click', () => generateProposal(title, keywords, index));
                    titlesList.appendChild(el);
                });
            })
            .catch(() => {
                titlesList.innerHTML = `<p class="text-red-500">제목 생성 실패</p>`;
            });
    });

    /* ===============================
       GENERATE PROPOSAL
    =============================== */
    function generateProposal(title, keywords, index) {
        currentSelectedTitle = title;
        currentSelectedKeywords = keywords;

        proposalContent.innerHTML = `
            <div class="text-center py-10 text-primary-600 font-medium">
                AI가 제안서를 작성 중입니다...
            </div>
        `;
        proposalSection.classList.remove('hidden');
        proposalSection.scrollIntoView({ behavior: 'smooth' });

        fetch('/Bizdraft/api/proposal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                keywords: keywords.join(', '),
                prompts: window.currentPrompts     // 🔥 핵심
            })
        })
            .then(res => res.json())
            .then(data => {
                if (data.ok) {
                    proposalContent.innerHTML = data.proposal_html;  // ✅ HTML 렌더링
                } else {
                    proposalContent.innerHTML = `<p class="text-red-500">제안서 생성 실패</p>`;
                }
            })
            .catch(() => {
                proposalContent.innerHTML = `<p class="text-red-500">서버 오류</p>`;
            });
    }

    /* ===============================
       DOWNLOAD BUTTONS
    =============================== */
    hwpxdownloadBtn.addEventListener('click', () => {
        if (!currentSelectedTitle) {
            alert('먼저 제안서를 작성해주세요.');
            return;
        }

        const encodedTitle = encodeURIComponent(currentSelectedTitle);
        window.location.href = `/Bizdraft/download-hwpx?title=${encodedTitle}`;
    });

    pptxDownloadBtn.addEventListener('click', () => {
        if (!currentSelectedTitle) {
            alert('먼저 제안서를 작성해주세요.');
            return;
        }

        const encodedTitle = encodeURIComponent(currentSelectedTitle);
        window.location.href = `/Bizdraft/download-pptx?title=${encodedTitle}`;
    });


    /* ===============================
       REWRITE BUTTON
    =============================== */
    rewriteBtn.addEventListener('click', () => {
        if (!currentSelectedTitle || currentSelectedKeywords.length === 0) {
            alert('먼저 제안서를 생성하세요.');
            return;
        }
        generateProposal(currentSelectedTitle, currentSelectedKeywords, 0);
    });

});

document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.querySelector('custom-prompt-sidebar');
    const toggleBtn = document.getElementById('promptToggleBtn');

    if (!sidebar || !toggleBtn) return;

    toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });
});