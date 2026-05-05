(function () {
    const body = document.body;
    const themeToggleBtn = document.getElementById("themeToggle");
    const bookingModal = document.getElementById("bookingModal");
    const quizModal = document.getElementById("quizModal");
    const tourNameDisplay = document.getElementById("tourNameDisplay");
    const quizError = document.getElementById("quizError");
    const submitQuizButton = document.getElementById("submitQuizButton");
    const downloadFilesButton = document.getElementById("downloadFilesButton");
    const bookingForm = document.getElementById("bookingForm");
    const downloadSection = document.getElementById("downloadSection");
    const currentTheme = localStorage.getItem("theme");
    const currentUserName = body.dataset.username || "";
    const isAuthenticated = body.dataset.authenticated === "true";
    const loginUrl = body.dataset.loginUrl || "/login/";
    const typingText = document.querySelector(".typing-effect");
    let currentTourName = "";
    let totalBookings = 0;
    const tourStats = {};

    initSolarSystemScene();

    if (currentTheme === "light") {
        document.body.classList.add("light-theme");
        if (themeToggleBtn) {
            themeToggleBtn.innerText = "🌙";
        }
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            document.body.classList.toggle("light-theme");
            const theme = document.body.classList.contains("light-theme") ? "light" : "dark";
            themeToggleBtn.innerText = theme === "light" ? "🌙" : "☀";
            localStorage.setItem("theme", theme);
        });
    }

    initCustomSelects();
    initAsyncTourBooking();
    initAsyncPackageBooking();

    document.querySelectorAll("[data-destination-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            const card = button.closest(".tour-card");
            if (!card) {
                return;
            }

            const isExpanded = card.classList.toggle("is-expanded");
            button.setAttribute("aria-expanded", String(isExpanded));
            button.textContent = isExpanded ? "Скрыть" : "Подробнее";
        });
    });

    if (typingText) {
        const text = typingText.innerText;
        typingText.innerText = "";
        let i = 0;

        function typeWriter() {
            if (i < text.length) {
                typingText.innerHTML += text.charAt(i);
                i += 1;
                setTimeout(typeWriter, 70);
            }
        }

        setTimeout(typeWriter, 350);
    }

    window.addEventListener("scroll", () => {
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const bar = document.getElementById("myBar");
        if (!bar || height <= 0) {
            return;
        }

        const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
        bar.style.width = `${(winScroll / height) * 100}%`;
    });

    document.querySelectorAll("[data-tilt]").forEach((card) => {
        card.addEventListener("mousemove", (event) => {
            const rect = card.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((y - centerY) / centerY) * -10;
            const rotateY = ((x - centerX) / centerX) * 10;
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });

        card.addEventListener("mouseleave", () => {
            card.style.transform = "perspective(1000px) rotateX(0) rotateY(0)";
        });
    });

    document.querySelectorAll("[data-tour-name]").forEach((button) => {
        button.addEventListener("click", () => {
            if (!isAuthenticated) {
                window.location.href = `${loginUrl}?next=/destinations/`;
                return;
            }

            currentTourName = button.dataset.tourName;
            if (tourNameDisplay) {
                tourNameDisplay.innerText = `Выбранный маршрут: ${currentTourName}`;
            }

            const hasPassed = localStorage.getItem(`${currentUserName}_psychTestPassed`);
            if (hasPassed === "true") {
                resetBookingForm();
                if (bookingModal) {
                    bookingModal.style.display = "flex";
                }
            } else if (quizModal) {
                document.getElementById("quizForm")?.reset();
                if (quizError) {
                    quizError.style.display = "none";
                }
                quizModal.style.display = "flex";
            }
        });
    });

    document.querySelector("[data-close-quiz]")?.addEventListener("click", () => {
        if (quizModal) {
            quizModal.style.display = "none";
        }
    });

    document.querySelector("[data-close-booking]")?.addEventListener("click", () => {
        if (bookingModal) {
            bookingModal.style.display = "none";
        }
    });

    window.addEventListener("click", (event) => {
        if (event.target === quizModal) {
            quizModal.style.display = "none";
        }
        if (event.target === bookingModal) {
            bookingModal.style.display = "none";
        }
    });

    if (submitQuizButton) {
        submitQuizButton.addEventListener("click", () => {
            let score = 0;
            let answeredAll = true;

            for (let index = 0; index < 7; index += 1) {
                const answer = document.querySelector(`input[name="q${index}"]:checked`);
                if (!answer) {
                    answeredAll = false;
                    break;
                }
                score += Number(answer.value);
            }

            if (!answeredAll) {
                if (quizError) {
                    quizError.style.display = "block";
                }
                return;
            }

            if (quizError) {
                quizError.style.display = "none";
            }

            if (score >= 5) {
                alert(`Тест пройден успешно. Ваш результат: ${score}/7.`);
                localStorage.setItem(`${currentUserName}_psychTestPassed`, "true");
                quizModal.style.display = "none";
                resetBookingForm();
                bookingModal.style.display = "flex";
            } else {
                alert(`Недостаточно баллов: ${score}/7. Попробуйте еще раз.`);
            }
        });
    }

    if (bookingForm) {
        bookingForm.addEventListener("submit", (event) => {
            event.preventDefault();
            const phone = document.getElementById("phoneNumber")?.value || "";
            if (phone.trim().length < 5) {
                return;
            }

            bookingForm.style.display = "none";
            if (downloadSection) {
                downloadSection.style.display = "block";
            }

            totalBookings += 1;
            tourStats[currentTourName] = (tourStats[currentTourName] || 0) + 1;
            updatePopularityBadges();
        });
    }

    if (downloadFilesButton) {
        downloadFilesButton.addEventListener("click", downloadTourFiles);
    }

    function initCustomSelects() {
        document.querySelectorAll("select[data-custom-select]").forEach((select) => {
            if (select.dataset.customReady === "true") {
                return;
            }

            const enabledOptions = Array.from(select.options).filter((option) => !option.disabled);
            if (select.selectedOptions[0]?.disabled && enabledOptions.length > 0) {
                select.value = enabledOptions[0].value;
            }

            const wrapper = document.createElement("div");
            const button = document.createElement("button");
            const list = document.createElement("ul");

            wrapper.className = "custom-select";
            button.className = "custom-select__button";
            button.type = "button";
            button.disabled = select.disabled;
            button.setAttribute("aria-haspopup", "listbox");
            button.setAttribute("aria-expanded", "false");
            list.className = "custom-select__list";
            list.setAttribute("role", "listbox");

            select.classList.add("is-enhanced");
            select.dataset.customReady = "true";
            select.insertAdjacentElement("afterend", wrapper);
            wrapper.append(button, list);

            function renderOptions() {
                const selectedOption = select.selectedOptions[0] || select.options[0];
                button.textContent = selectedOption ? selectedOption.textContent.trim() : "Выберите";
                button.disabled = select.disabled;
                list.innerHTML = "";

                Array.from(select.options).forEach((option) => {
                    const item = document.createElement("li");
                    item.className = "custom-select__option";
                    item.textContent = option.textContent.trim();
                    item.dataset.value = option.value;
                    item.setAttribute("role", "option");
                    item.setAttribute("aria-selected", String(option.selected));

                    if (option.disabled) {
                        item.classList.add("is-disabled");
                        item.setAttribute("aria-disabled", "true");
                    }
                    if (option.selected) {
                        item.classList.add("is-selected");
                    }

                    item.addEventListener("click", () => {
                        if (option.disabled) {
                            return;
                        }

                        select.value = option.value;
                        select.dispatchEvent(new Event("change", { bubbles: true }));
                        renderOptions();
                        closeSelect();
                    });

                    list.appendChild(item);
                });
            }

            function openSelect() {
                document.querySelectorAll(".custom-select.is-open").forEach((openWrapper) => {
                    if (openWrapper !== wrapper) {
                        openWrapper.classList.remove("is-open");
                        openWrapper.querySelector(".custom-select__button")?.setAttribute("aria-expanded", "false");
                    }
                });
                wrapper.classList.add("is-open");
                button.setAttribute("aria-expanded", "true");
            }

            function closeSelect() {
                wrapper.classList.remove("is-open");
                button.setAttribute("aria-expanded", "false");
            }

            button.addEventListener("click", () => {
                if (button.disabled) {
                    return;
                }
                if (wrapper.classList.contains("is-open")) {
                    closeSelect();
                } else {
                    openSelect();
                }
            });

            button.addEventListener("keydown", (event) => {
                if (event.key === "Escape") {
                    closeSelect();
                }
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    button.click();
                }
            });

            select.addEventListener("change", renderOptions);
            renderOptions();
        });

        document.addEventListener("click", (event) => {
            if (event.target.closest(".custom-select")) {
                return;
            }
            document.querySelectorAll(".custom-select.is-open").forEach((wrapper) => {
                wrapper.classList.remove("is-open");
                wrapper.querySelector(".custom-select__button")?.setAttribute("aria-expanded", "false");
            });
        });
    }

    function initAsyncTourBooking() {
        document.querySelectorAll(".package-booking-form[data-book-url]").forEach((form) => {
            form.addEventListener("submit", async (event) => {
                event.preventDefault();

                const submitButton = form.querySelector('button[type="submit"]');
                const defaultButtonText = submitButton?.textContent || "";
                const formData = new FormData(form);

                if (submitButton) {
                    submitButton.disabled = true;
                    submitButton.textContent = "Бронируем...";
                }

                try {
                    const response = await fetch(form.dataset.bookUrl, {
                        method: "POST",
                        body: formData,
                        credentials: "same-origin",
                        headers: {
                            "X-CSRFToken": getCsrfToken(form),
                            "X-Requested-With": "XMLHttpRequest",
                        },
                    });
                    const data = await response.json();

                    if (!response.ok || data.status !== "success") {
                        throw new Error(data.message || "Не удалось забронировать тур.");
                    }

                    alert(data.message || "Тур успешно забронирован! Билет добавлен в личный кабинет");
                } catch (error) {
                    alert(error.message || "Ошибка бронирования. Попробуйте еще раз.");
                } finally {
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.textContent = defaultButtonText;
                    }
                }
            });
        });
    }

    function initAsyncPackageBooking() {
        document.querySelectorAll(".btn-buy").forEach((button) => {
            button.addEventListener("click", async () => {
                const form = button.closest("form.package-booking-form");
                if (!form) {
                    return;
                }

                const scheduleSelect = form.querySelector("select[name=\"schedule_id\"]");
                const scheduleId = scheduleSelect?.value || "";
                const packageId = button.dataset.packageId || "";
                if (!scheduleId || !packageId) {
                    alert("Выберите рейс для бронирования.");
                    return;
                }

                const defaultText = button.textContent;
                button.disabled = true;
                button.textContent = "Бронируем...";

                try {
                    const response = await fetch(form.dataset.bookUrl, {
                        method: "POST",
                        credentials: "same-origin",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": getCsrfToken(form),
                            "X-Requested-With": "XMLHttpRequest",
                        },
                        body: JSON.stringify({
                            package_id: packageId,
                            schedule_id: scheduleId,
                        }),
                    });
                    const data = await response.json();

                    if (!response.ok || data.status !== "success") {
                        throw new Error(data.message || "Не удалось забронировать тур.");
                    }

                    alert("Билет успешно оформлен! Проверьте личный кабинет");
                    button.textContent = "Оформлено";
                } catch (error) {
                    alert(error.message || "Ошибка бронирования. Попробуйте еще раз.");
                    button.disabled = false;
                    button.textContent = defaultText;
                }
            });
        });
    }

    function getCsrfToken(form) {
        const inputToken = form.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
        if (inputToken) {
            return inputToken;
        }

        const csrfCookie = document.cookie
            .split("; ")
            .find((row) => row.startsWith("csrftoken="));

        return csrfCookie ? decodeURIComponent(csrfCookie.split("=")[1]) : "";
    }

    function resetBookingForm() {
        if (bookingForm) {
            bookingForm.style.display = "block";
            bookingForm.reset();
        }
        if (downloadSection) {
            downloadSection.style.display = "none";
        }
    }

    function downloadTourFiles() {
        const fileUrls = {
            plan: "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
            guide: "https://iphras.ru/uplfile/root/biblio/ps/ps9/7.pdf",
            map: "https://images.unsplash.com/photo-1541185933-ef5d8ed016c2?w=1920&q=80",
        };

        const selectedFiles = document.querySelectorAll('input[name="dl_file"]:checked');
        if (selectedFiles.length === 0) {
            alert("Выберите хотя бы один файл для скачивания.");
            return;
        }

        selectedFiles.forEach((checkbox) => {
            const rawUrl = fileUrls[checkbox.value];
            const proxyUrl = `https://corsproxy.io/?${encodeURIComponent(rawUrl)}`;
            const extension = checkbox.value === "map" ? ".jpg" : ".pdf";
            const safeTourName = (currentTourName || "Tour").replace(/\s+/g, "_");
            const fileName = `${safeTourName}_${checkbox.value}${extension}`;

            fetch(proxyUrl)
                .then((response) => {
                    if (!response.ok) {
                        throw new Error("Ошибка прокси");
                    }
                    return response.blob();
                })
                .then((blob) => {
                    const link = document.createElement("a");
                    const objectUrl = URL.createObjectURL(blob);
                    link.href = objectUrl;
                    link.download = fileName;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    URL.revokeObjectURL(objectUrl);
                })
                .catch(() => {
                    window.open(rawUrl, "_blank");
                });
        });
    }

    function updatePopularityBadges() {
        document.querySelectorAll(".tour-card").forEach((card) => {
            const content = card.querySelector(".card-content");
            const title = content.querySelector("h2").innerText;
            const button = content.querySelector(".book-btn");
            const count = tourStats[title] || 0;
            const percent = totalBookings > 0 ? Math.round((count / totalBookings) * 100) : 0;

            content.querySelector(".popularity-badge")?.remove();

            const badge = document.createElement("div");
            badge.className = "popularity-badge";
            badge.innerText = `🔥 Популярность: ${percent}%`;
            content.insertBefore(badge, button);
        });
    }

    function initSolarSystemScene() {
        const container = document.getElementById("canvas-container");
        if (!container || !window.THREE) {
            return;
        }

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        const raycaster = new THREE.Raycaster();
        const pointer = new THREE.Vector2();
        const clickablePlanets = [];
        const clock = new THREE.Clock();

        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.setClearColor(0x000000, 0);
        container.appendChild(renderer.domElement);

        camera.position.set(0, 13, 42);

        // OrbitControls позволяет пользователю мягко осмотреть систему мышкой или жестом.
        const controls = window.THREE.OrbitControls
            ? new THREE.OrbitControls(camera, renderer.domElement)
            : null;
        if (controls) {
            controls.enableDamping = true;
            controls.dampingFactor = 0.06;
            controls.enablePan = false;
            controls.minDistance = 22;
            controls.maxDistance = 68;
            controls.autoRotate = true;
            controls.autoRotateSpeed = 0.28;
            controls.target.set(0, 0, 0);
        }

        // PointLight в центре сцены имитирует Солнце, подсвечивая планеты изнутри орбит.
        const sunLight = new THREE.PointLight(0xfff2b0, 2.8, 180);
        sunLight.position.set(0, 0, 0);
        scene.add(sunLight);
        scene.add(new THREE.AmbientLight(0x3f5878, 0.35));

        const sun = new THREE.Mesh(
            new THREE.SphereGeometry(3.4, 48, 48),
            new THREE.MeshBasicMaterial({ color: 0xffcc55 })
        );
        scene.add(sun);

        const sunGlow = new THREE.Mesh(
            new THREE.SphereGeometry(4.4, 48, 48),
            new THREE.MeshBasicMaterial({
                color: 0xff9f1c,
                transparent: true,
                opacity: 0.16,
            })
        );
        scene.add(sunGlow);

        // Чтобы добавить новую планету, скопируйте объект ниже и поменяйте параметры.
        // textureUrl можно заменить на путь к текстуре, если позже подключите TextureLoader.
        const planetConfigs = [
            {
                name: "earth",
                label: "Земля",
                color: 0x3f8cff,
                radius: 1.12,
                orbitRadius: 10,
                orbitSpeed: 0.55,
                initialAngle: 0.4,
                tourUrl: "/destinations/?system=earth",
            },
            {
                name: "mars",
                label: "Марс",
                color: 0xd85f3c,
                radius: 0.92,
                orbitRadius: 15,
                orbitSpeed: 0.18,
                initialAngle: 0.32,
                tourUrl: "/destinations/?system=mars",
            },
            {
                name: "saturn",
                label: "Сатурн",
                color: 0xd6b16f,
                radius: 1.35,
                orbitRadius: 21,
                orbitSpeed: 0.22,
                initialAngle: 4.8,
                tourUrl: "/destinations/?system=saturn",
            },
        ];

        const orbitMaterial = new THREE.LineBasicMaterial({
            color: 0x6bdff0,
            transparent: true,
            opacity: 0.22,
        });

        planetConfigs.forEach((config) => {
            const orbit = makeOrbitLine(config.orbitRadius, orbitMaterial);
            scene.add(orbit);

            const planet = new THREE.Mesh(
                new THREE.SphereGeometry(config.radius, 32, 32),
                new THREE.MeshStandardMaterial({
                    color: config.color,
                    roughness: 0.58,
                    metalness: 0.05,
                })
            );
            planet.userData = {
                tourUrl: config.tourUrl,
                name: config.name,
                label: config.label,
                orbitRadius: config.orbitRadius,
                orbitSpeed: config.orbitSpeed,
                angle: config.initialAngle,
            };

            if (config.name === "saturn") {
                const ring = new THREE.Mesh(
                    new THREE.RingGeometry(config.radius * 1.45, config.radius * 2.2, 48),
                    new THREE.MeshBasicMaterial({
                        color: 0xe8d198,
                        side: THREE.DoubleSide,
                        transparent: true,
                        opacity: 0.46,
                    })
                );
                ring.rotation.x = Math.PI / 2.55;
                planet.add(ring);
            }

            clickablePlanets.push(planet);
            scene.add(planet);
        });

        // Небольшое звездное поле делает сцену читаемой без внешних картинок и текстур.
        scene.add(makeStarField(520));

        function resizeScene() {
            const rect = container.getBoundingClientRect();
            const width = Math.max(rect.width, 1);
            const height = Math.max(rect.height, 1);
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height, false);
        }

        function animate() {
            const delta = clock.getDelta();
            sun.rotation.y += delta * 0.22;
            sunGlow.rotation.y -= delta * 0.12;

            clickablePlanets.forEach((planet) => {
                planet.userData.angle += delta * planet.userData.orbitSpeed;
                planet.position.set(
                    Math.cos(planet.userData.angle) * planet.userData.orbitRadius,
                    0,
                    Math.sin(planet.userData.angle) * planet.userData.orbitRadius
                );
                planet.rotation.y += delta * 0.9;
            });

            if (controls) {
                controls.update();
            }
            renderer.render(scene, camera);
            requestAnimationFrame(animate);
        }

        function openPlanetTour(event) {
            const rect = renderer.domElement.getBoundingClientRect();
            pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

            raycaster.setFromCamera(pointer, camera);
            const intersects = raycaster.intersectObjects(clickablePlanets, true);
            const planet = intersects
                .map((item) => findClickablePlanet(item.object))
                .find(Boolean);

            if (planet?.userData?.tourUrl) {
                window.location.href = planet.userData.tourUrl;
            }
        }

        function findClickablePlanet(object) {
            let current = object;
            while (current) {
                if (clickablePlanets.includes(current)) {
                    return current;
                }
                current = current.parent;
            }
            return null;
        }

        function makeOrbitLine(radius, material) {
            const points = [];
            for (let index = 0; index <= 128; index += 1) {
                const angle = (index / 128) * Math.PI * 2;
                points.push(new THREE.Vector3(Math.cos(angle) * radius, 0, Math.sin(angle) * radius));
            }
            return new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(points), material);
        }

        function makeStarField(count) {
            const positions = new Float32Array(count * 3);
            for (let index = 0; index < count; index += 1) {
                positions[index * 3] = (Math.random() - 0.5) * 120;
                positions[index * 3 + 1] = (Math.random() - 0.5) * 72;
                positions[index * 3 + 2] = (Math.random() - 0.5) * 120;
            }

            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
            return new THREE.Points(
                geometry,
                new THREE.PointsMaterial({
                    color: 0xffffff,
                    size: 0.12,
                    transparent: true,
                    opacity: 0.72,
                })
            );
        }

        window.travelXSolarSystem = {
            getPlanetScreenPosition(name) {
                const planet = clickablePlanets.find((item) => item.userData.name === name);
                if (!planet) {
                    return null;
                }

                const rect = renderer.domElement.getBoundingClientRect();
                const projected = planet.position.clone().project(camera);
                return {
                    x: rect.left + ((projected.x + 1) / 2) * rect.width,
                    y: rect.top + ((-projected.y + 1) / 2) * rect.height,
                    tourUrl: planet.userData.tourUrl,
                };
            },
        };

        resizeScene();
        animate();
        container.dataset.solarSystemReady = "true";
        renderer.domElement.addEventListener("click", openPlanetTour);
        window.addEventListener("resize", resizeScene);
    }
})();
