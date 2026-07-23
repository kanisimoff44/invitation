// Появление секций при скролле + отправка формы RSVP.
(function () {
    "use strict";

    // --- Reveal-анимация секций ---
    var revealEls = document.querySelectorAll(".reveal");
    if ("IntersectionObserver" in window && revealEls.length) {
        var io = new IntersectionObserver(
            function (entries, obs) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        obs.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.12 }
        );
        revealEls.forEach(function (el) { io.observe(el); });
    } else {
        revealEls.forEach(function (el) { el.classList.add("is-visible"); });
    }

    // --- Форма RSVP ---
    var form = document.getElementById("rsvp-form");
    if (!form) return;

    var submitBtn = document.getElementById("rsvp-submit");
    var errorEl = document.getElementById("rsvp-error");
    var thanksBox = document.getElementById("rsvp-thanks");
    var thanksText = document.getElementById("rsvp-thanks-text");

    function showError(msg) {
        errorEl.textContent = msg;
        errorEl.hidden = false;
    }

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        errorEl.hidden = true;

        var nameEl = document.getElementById("full_name");
        var name = (nameEl.value || "").trim();
        if (name.length < 2) {
            showError("Пожалуйста, укажите имя и фамилию.");
            nameEl.focus();
            return;
        }

        var attendingEl = form.querySelector('input[name="attending"]:checked');
        if (!attendingEl) {
            showError("Пожалуйста, выберите, придёте ли вы.");
            return;
        }
        var attending = attendingEl.value === "yes";

        // Поле guests может отсутствовать (фича отключена флагом на сервере).
        var guestsEl = document.getElementById("guests_count");
        var guestsCount = guestsEl ? parseInt(guestsEl.value, 10) || 0 : 0;

        var hpEl = form.querySelector('input[name="website"]');
        var website = hpEl ? hpEl.value : "";

        // Убираем форму (вместе с кнопкой) сразу и показываем статус отправки —
        // это же место затем займёт итоговая фраза.
        submitBtn.disabled = true;
        form.hidden = true;
        thanksText.textContent = "Отправляем…";
        thanksBox.hidden = false;

        fetch("/api/rsvp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                full_name: name,
                attending: attending,
                guests_count: guestsCount,
                website: website
            })
        })
            .then(function (res) {
                if (!res.ok) throw new Error("bad status " + res.status);
                return res.json();
            })
            .then(function (data) {
                try {
                    localStorage.setItem("rsvp_submitted", "1");
                } catch (_) { /* игнор */ }
                thanksText.textContent =
                    (data && data.message) || "Спасибо! Ваш ответ получен.";
            })
            .catch(function () {
                // Ошибка — возвращаем форму, чтобы можно было повторить.
                thanksBox.hidden = true;
                form.hidden = false;
                submitBtn.disabled = false;
                showError(
                    "Не удалось отправить. Проверьте соединение и попробуйте ещё раз."
                );
            });
    });
})();
