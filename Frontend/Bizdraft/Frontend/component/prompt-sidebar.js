class CustomPromptSidebar extends HTMLElement {
    async connectedCallback() {
        this.attachShadow({ mode: 'open' });

        this.shadowRoot.innerHTML = `
        <style>
            :host {
                display: block;
                position: fixed;
                right: 0;
                top: 90px;
                width: 400px;
                height: calc(100vh - 80px);
                overflow-y: auto;
                z-index: 40;
                font-family: system-ui, -apple-system, BlinkMacSystemFont;
            }
            .sidebar-container {
                background: white;
                box-shadow: -2px 0 8px rgba(0,0,0,0.1);
                height: 100%;
                display: flex;
                flex-direction: column;
            }
            .toast {
                position: sticky;
                top: 0;
                z-index: 50;
                background: #2563eb;
                color: white;
                padding: 0.75rem 1rem;
                font-size: 0.85rem;
                text-align: center;
            }
            .toast.hidden {
                display: none;
            }
            .prompt-category {
                padding: 1rem;
                border-bottom: 1px solid #e2e8f0;
                cursor: pointer;
            }
            .prompt-category.active {
                background: #f0f9ff;
            }
            .category-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .category-title {
                font-weight: 600;
                color: #1e40af;
            }
            .prompt-editor {
                max-height: 0;
                opacity: 0;
                overflow: hidden;
                transform: translateY(-6px);
                transition:
                    max-height 0.35s ease,
                    opacity 0.25s ease,
                    transform 0.25s ease;
            }
            .prompt-category.active .prompt-editor {
                max-height: 1000px;
                opacity: 1;
                transform: translateY(0);
            }
            textarea {
                width: 100%;
                min-height: 300px;
                padding: 0.5rem;
                border: 1px solid #cbd5f5;
                border-radius: 0.25rem;
                font-family: monospace;
                font-size: 0.85rem;
                resize: vertical;
            }
            .editor-actions {
                display: flex;
                justify-content: flex-end;
                gap: 0.5rem;
                margin-top: 0.5rem;
            }
            button {
                padding: 0.25rem 0.5rem;
                border-radius: 0.25rem;
                font-size: 0.75rem;
                cursor: pointer;
                border: none;
            }
            .save-btn {
                background: #2563eb;
                color: white;
            }
            .reset-btn {
                background: #e5e7eb;
            }
                :host {
                transition: transform 0.3s ease;
            }

            /* 접힌 상태 */
            :host(.collapsed) {
                transform: translateX(100%);
            }

            /* 모바일 대응 */
            @media (max-width: 1024px) {
                :host {
                    width: 100%;
                    max-width: 360px;
                    top: 0;
                    height: 100vh;
                    z-index: 50;
                }
            }
        </style>

        <div class="sidebar-container">
            <div id="toast" class="toast hidden"></div>

            ${this.buildCategory("title", "제목 생성")}
            ${this.buildCategory("overview", "사업 개요")}
            ${this.buildCategory("need", "사업 필요성")}
            ${this.buildCategory("suggestion", "건의문")}
            ${this.buildCategory("ref1", "[참고] 1. 사업 개요")}
            ${this.buildCategory("ref2", "[참고] 2. 추진 배경 및 필요성")}
            ${this.buildCategory("ref3", "[참고] 3. 사업 내용")}
            ${this.buildCategory("ref4", "[참고] 4. 기대 효과")}
        </div>
        `;

        await this.initializeSidebar();
        feather.replace();
    }

    buildCategory(key, label) {
        return `
        <div class="prompt-category" data-key="${key}">
            <div class="category-header">
                <span class="category-title">${label}</span>
                <i data-feather="chevron-down"></i>
            </div>
            <div class="prompt-editor">
                <textarea></textarea>
                <div class="editor-actions">
                    <button class="reset-btn">초기화</button>
                    <button class="save-btn">저장</button>
                </div>
            </div>
        </div>
        `;
    }

    showToast(message) {
        const toast = this.shadowRoot.getElementById("toast");
        toast.textContent = message;
        toast.classList.remove("hidden");

        clearTimeout(this.toastTimer);
        this.toastTimer = setTimeout(() => {
            toast.classList.add("hidden");
        }, 1500);
    }

    async initializeSidebar() {
        const res = await fetch("/Bizdraft/prompts/default");
        const serverPrompts = await res.json();

        // 🔥 기본 프롬프트 저장 (초기화용)
        this.defaultPrompts = { ...serverPrompts };

        // 🔥 전역 프롬프트 상태
        window.currentPrompts = { ...serverPrompts };

        const categories = this.shadowRoot.querySelectorAll(".prompt-category");

        categories.forEach(category => {
            const key = category.dataset.key;
            const textarea = category.querySelector("textarea");
            const header = category.querySelector(".category-header");
            const icon = header.querySelector("i");
            const saveBtn = category.querySelector(".save-btn");
            const resetBtn = category.querySelector(".reset-btn");

            // 초기값 세팅
            textarea.value = serverPrompts[key] || "";

            // 입력 시 즉시 반영
            textarea.addEventListener("input", () => {
                window.currentPrompts[key] = textarea.value;
            });

            // 🔥 저장 버튼
            saveBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                window.currentPrompts[key] = textarea.value;
                this.showToast("프롬프트가 저장되었습니다.");
            });

            // 🔥 초기화 버튼
            resetBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                textarea.value = this.defaultPrompts[key] || "";
                window.currentPrompts[key] = this.defaultPrompts[key] || "";
                this.showToast("프롬프트가 초기화되었습니다.");
            });

            // 카테고리 열고 닫기
            header.addEventListener("click", () => {
                const alreadyOpen = category.classList.contains("active");

                categories.forEach(c => {
                    c.classList.remove("active");
                    c.querySelector("i")
                        .setAttribute("data-feather", "chevron-down");
                });

                if (alreadyOpen) {
                    feather.replace();
                    return;
                }

                category.classList.add("active");
                icon.setAttribute("data-feather", "chevron-up");
                feather.replace();
            });
        });
    }
}

customElements.define("custom-prompt-sidebar", CustomPromptSidebar);
