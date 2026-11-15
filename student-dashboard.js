/* =========================================================
   AI SMARTTIME - STUDENT DASHBOARD JAVASCRIPT
========================================================= */

document.addEventListener("DOMContentLoaded", function () {


    /* =====================================================
       ELEMENTS
    ====================================================== */

    const menuItems =
        document.querySelectorAll(
            ".menu-item[data-section]"
        );

    const pageSections =
        document.querySelectorAll(
            ".page-section"
        );

    const pageTitle =
        document.getElementById(
            "pageTitle"
        );

    const pageSubtitle =
        document.getElementById(
            "pageSubtitle"
        );

    const dateBox =
        document.getElementById(
            "currentDate"
        );

    const STUDENT_API = `${window.SMARTTIME_API_BASE || "http://127.0.0.1:8000/api"}/auth/student-profile/`;



    /* =====================================================
       SECTION INFORMATION
    ====================================================== */

    const sectionInfo = {

        dashboard: {
            title: "Student Dashboard",
            subtitle:
                "Manage your academic timetable and notifications"
        },

        timetable: {
            title: "My Timetable",
            subtitle:
                "View your complete academic timetable"
        },

        notifications: {
            title: "Notifications",
            subtitle:
                "View timetable and class updates"
        },

        profile: {
            title: "My Profile",
            subtitle:
                "View and edit your student profile"
        }

    };



    /* =====================================================
       CURRENT DATE
    ====================================================== */

    function showCurrentDate() {

        if (!dateBox) {
            return;
        }

        const today =
            new Date();

        const options = {
            day: "2-digit",
            month: "short",
            year: "numeric"
        };

        dateBox.textContent =
            today.toLocaleDateString(
                "en-GB",
                options
            );
    }


    showCurrentDate();



    /* =====================================================
       OPEN SECTION
    ====================================================== */

    function openSection(sectionName) {

        /* Hide all sections */

        pageSections.forEach(
            function (section) {

                section.classList.remove(
                    "active-section"
                );

            }
        );


        /* Remove active menu */

        menuItems.forEach(
            function (item) {

                item.classList.remove(
                    "active"
                );

            }
        );


        /* Find selected section */

        const selectedSection =
            document.getElementById(
                sectionName
            );


        if (!selectedSection) {

            console.error(
                "Section not found:",
                sectionName
            );

            return;

        }


        /* Show section */

        selectedSection.classList.add(
            "active-section"
        );


        /* Find selected menu */

        const selectedMenu =
            document.querySelector(
                '.menu-item[data-section="' +
                sectionName +
                '"]'
            );


        if (selectedMenu) {

            selectedMenu.classList.add(
                "active"
            );

        }


        /* Update header */

        if (
            sectionInfo[sectionName] &&
            pageTitle &&
            pageSubtitle
        ) {

            pageTitle.textContent =
                sectionInfo[
                    sectionName
                ].title;

            pageSubtitle.textContent =
                sectionInfo[
                    sectionName
                ].subtitle;

        }


        /* Update URL */

        history.replaceState(
            null,
            "",
            "#" + sectionName
        );


        /* Scroll top */

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });

    }



    /* =====================================================
       SIDEBAR BUTTONS
    ====================================================== */

    menuItems.forEach(
        function (item) {

            item.addEventListener(
                "click",
                function () {

                    const section =
                        item.getAttribute(
                            "data-section"
                        );

                    openSection(
                        section
                    );

                }
            );

        }
    );



    /* =====================================================
       DASHBOARD BUTTONS
       View All / Full Timetable
    ====================================================== */

    const sectionButtons =
        document.querySelectorAll(
            "[data-section-button]"
        );


    sectionButtons.forEach(
        function (button) {

            button.addEventListener(
                "click",
                function () {

                    const section =
                        button.getAttribute(
                            "data-section-button"
                        );

                    openSection(
                        section
                    );

                }
            );

        }
    );



    /* =====================================================
       OPEN SECTION FROM URL HASH
    ====================================================== */

    function openHashSection() {

        const hash =
            window.location.hash
                .replace("#", "")
                .trim();


        const validSections = [
            "dashboard",
            "timetable",
            "notifications",
            "profile"
        ];


        if (
            validSections.includes(
                hash
            )
        ) {

            openSection(
                hash
            );

        } else {

            openSection(
                "dashboard"
            );

        }

    }


    openHashSection();



    /* =====================================================
       PROFILE STORAGE
    ====================================================== */

    const PROFILE_KEY =
        "smartTimeStudentProfile";


    const defaultProfile = {

        name: "",
        regNo: "",
        branch: "",
        batch: "",
        section: "",
        group: "",
        year: "",
        email: "",
        phone: "",
        photo: ""

    };



    /* =====================================================
       GET SAVED PROFILE
    ====================================================== */

    function getProfile() {

        const savedProfile =
            localStorage.getItem(
                PROFILE_KEY
            );


        if (!savedProfile) {

            return {
                ...defaultProfile
            };

        }


        try {

            const profile =
                JSON.parse(
                    savedProfile
                );


            return {
                ...defaultProfile,
                ...profile
            };

        } catch (error) {

            console.error(
                "Profile data error:",
                error
            );

            return {
                ...defaultProfile
            };

        }

    }



    /* =====================================================
       SAVE PROFILE TO LOCAL STORAGE
    ====================================================== */

    function saveProfileData(
        profile
    ) {

        localStorage.setItem(
            PROFILE_KEY,
            JSON.stringify(
                profile
            )
        );

    }



    /* =====================================================
       LOAD PROFILE
    ====================================================== */

    function loadProfile() {

        const profile =
            getProfile();


        const profileName =
            document.getElementById(
                "profileName"
            );

        const profileRegNo =
            document.getElementById(
                "profileRegNo"
            );

        const profileBranch =
            document.getElementById(
                "profileBranch"
            );

        const profileSection =
            document.getElementById(
                "profileSection"
            );

        const profileYear =
            document.getElementById(
                "profileYear"
            );

        const profileEmail =
            document.getElementById(
                "profileEmail"
            );

        const profilePhone =
            document.getElementById(
                "profilePhone"
            );
        const profileBatch = document.getElementById("profileBatch");
        const profileGroup = document.getElementById("profileGroup");


        if (profileName) {

            profileName.value =
                profile.name || "";

        }


        if (profileRegNo) {

            profileRegNo.value =
                profile.regNo || "";

        }


        if (profileBranch) {

            profileBranch.value =
                profile.branch || "";

        }


        if (profileSection) {

            profileSection.value =
                profile.section || "";

        }


        if (profileYear) {

            profileYear.value =
                profile.year ||
                "";

        }


        if (profileEmail) {

            profileEmail.value =
                profile.email || "";

        }


        if (profilePhone) {

            profilePhone.value =
                profile.phone || "";

        }
        if (profileBatch) profileBatch.value = profile.batch || "";
        if (profileGroup) profileGroup.value = profile.group || "";


        updateSidebarProfile(
            profile
        );

    }



    /* =====================================================
       UPDATE SIDEBAR
    ====================================================== */

    function updateSidebarProfile(
        profile
    ) {

        const sidebarName =
            document.getElementById(
                "sidebarName"
            );

        const sidebarRegNo =
            document.getElementById(
                "sidebarRegNo"
            );

        const sidebarBranch =
            document.getElementById(
                "sidebarBranch"
            );

        const sidebarSection =
            document.getElementById(
                "sidebarSection"
            );

        const sidebarYear =
            document.getElementById(
                "sidebarYear"
            );

        const welcomeName =
            document.getElementById(
                "welcomeName"
            );


        if (sidebarName) {

            sidebarName.textContent =
                profile.name ||
                "Student";

        }


        if (sidebarRegNo) {

            sidebarRegNo.textContent =
                profile.regNo ||
                "";

        }


        if (sidebarBranch) {

            sidebarBranch.textContent =
                profile.branch ||
                "";

        }


        if (sidebarSection) {

            sidebarSection.textContent =
                profile.section ||
                "";

        }


        if (sidebarYear) {

            sidebarYear.textContent =
                profile.year ||
                "";

        }


        if (welcomeName) {

            welcomeName.textContent =
                profile.name ||
                "Student";

        }


        const academicValues = {
            dashboardRegNo: profile.regNo,
            dashboardBatch: profile.batch,
            dashboardSectionGroup: [profile.section, profile.group].filter(Boolean).join(" / "),
            dashboardCourse: profile.branch,
            dashboardYear: profile.year,
        };
        Object.entries(academicValues).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value || "Not assigned";
        });

        updateProfileImages(
            profile.photo
        );

    }



    /* =====================================================
       UPDATE PROFILE IMAGES
    ====================================================== */

    function updateProfileImages(
        photo
    ) {

        const sidebarImage =
            document.getElementById(
                "sidebarProfileImage"
            );

        const defaultProfile =
            document.getElementById(
                "defaultProfile"
            );

        const profileImage =
            document.getElementById(
                "profileImage"
            );

        const largeDefaultProfile =
            document.getElementById(
                "largeDefaultProfile"
            );


        if (photo) {

            /* SIDEBAR */

            if (sidebarImage) {

                sidebarImage.src =
                    photo;

                sidebarImage.style.display =
                    "block";

            }


            if (defaultProfile) {

                defaultProfile.style.display =
                    "none";

            }


            /* PROFILE PAGE */

            if (profileImage) {

                profileImage.src =
                    photo;

                profileImage.style.display =
                    "block";

            }


            if (largeDefaultProfile) {

                largeDefaultProfile.style.display =
                    "none";

            }

        } else {

            /* SIDEBAR */

            if (sidebarImage) {

                sidebarImage.removeAttribute(
                    "src"
                );

                sidebarImage.style.display =
                    "none";

            }


            if (defaultProfile) {

                defaultProfile.style.display =
                    "flex";

            }


            /* PROFILE PAGE */

            if (profileImage) {

                profileImage.removeAttribute(
                    "src"
                );

                profileImage.style.display =
                    "none";

            }


            if (largeDefaultProfile) {

                largeDefaultProfile.style.display =
                    "flex";

            }

        }

    }



    /* =====================================================
       LOAD PROFILE ON START
    ====================================================== */

    loadProfile();

    async function loadStudentProfileFromServer() {
        const token = localStorage.getItem("smartTimeToken");
        if (!token) return;
        try {
            const response = await fetch(STUDENT_API, { headers: { Authorization: `Token ${token}` } });
            if (!response.ok) throw new Error("Could not load student account details.");
            const data = await response.json();
            const profile = {
                ...getProfile(), name: data.name || "", email: data.email || "",
                regNo: data.registration_number || "", phone: data.phone || "",
                batch: data.batch || "", section: data.section || "", group: data.group || "",
                branch: data.course || "", year: data.year || "",
            };
            saveProfileData(profile);
            loadProfile();
        } catch (error) {
            console.error("Student account details could not be loaded:", error);
        }
    }
    loadStudentProfileFromServer();

    async function loadStudentTimetable() {
        try {
            const data = await studentApi("timetable/");
            const entries = Array.isArray(data) ? data : (data.results || []);
            const generated = await studentApi("ai-timetable/published/");
            entries.push(...(Array.isArray(generated) ? generated : (generated.results || [])));
            const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
            const slots = [["09:00", "09:55"], ["10:00", "10:55"], ["11:05", "12:00"], ["12:05", "13:00"], ["13:00", "14:30"], ["14:30", "15:20"], ["15:20", "16:10"], ["16:10", "17:00"]];
            const minutes = (time) => { const [h, m] = String(time || "").slice(0, 5).split(":").map(Number); return h * 60 + m; };
            const today = new Intl.DateTimeFormat("en", { weekday: "long" }).format(new Date());
            const todayBody = document.querySelector(".today-table tbody");
            const safe = escapeNotification;
            if (todayBody) {
                const todays = entries.filter((item) => String(item.day).toLowerCase() === today.toLowerCase());
                todayBody.innerHTML = todays.length ? todays.map((item) => `<tr><td>${safe(item.start_time)} - ${safe(item.end_time)}</td><td class="subject-name">${safe(item.subject_name || item.session_title)}</td><td>${safe(item.teacher_name)}</td><td>${safe(item.room_number)}</td><td><span class="status-badge scheduled">Scheduled</span></td></tr>`).join("") : `<tr><td colspan="5">No classes scheduled for ${safe(today)}.</td></tr>`;
            }
            const weeklyBody = document.querySelector(".academic-timetable tbody");
            if (weeklyBody) weeklyBody.innerHTML = days.map((day) => {
                const dayEntries = entries.filter((item) => String(item.day).toLowerCase() === day.toLowerCase());
                const cells = slots.map(([from, to], index) => {
                    if (index === 4) return '<td class="lunch">LUNCH BREAK</td>';
                    const item = dayEntries.find((entry) => minutes(entry.start_time) < minutes(to) && minutes(entry.end_time) > minutes(from));
                    const label = item ? `<strong>${safe(item.subject_name || item.session_title)}</strong><br><small>${safe(item.teacher_name)} · ${safe(item.room_number)}</small>` : "—";
                    return `<td>${label}</td>`;
                }).join("");
                return `<tr><th>${day.slice(0, 3).toUpperCase()}</th>${cells}</tr>`;
            }).join("");
        } catch (error) {
            console.error("Student timetable could not be loaded:", error);
        }
    }

    loadStudentTimetable();
    window.setInterval(loadStudentTimetable, 30000);


    /* =====================================================
       PROFILE FORM SAVE
    ====================================================== */

    const profileForm =
        document.getElementById(
            "profileForm"
        );


    if (profileForm) {

        profileForm.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();


                const oldProfile =
                    getProfile();


                const updatedProfile = {

                    name:
                        document.getElementById(
                            "profileName"
                        ).value.trim(),

                    regNo:
                        document.getElementById(
                            "profileRegNo"
                        ).value.trim(),

                    branch:
                        document.getElementById(
                            "profileBranch"
                        ).value.trim(),

                    batch:
                        document.getElementById("profileBatch").value.trim(),

                    group:
                        document.getElementById("profileGroup").value.trim(),

                    section:
                        document.getElementById(
                            "profileSection"
                        ).value,

                    year:
                        document.getElementById(
                            "profileYear"
                        ).value,

                    email:
                        document.getElementById(
                            "profileEmail"
                        ).value.trim(),

                    phone:
                        document.getElementById(
                            "profilePhone"
                        ).value.trim(),

                    photo:
                        oldProfile.photo || ""

                };

                const token = localStorage.getItem("smartTimeToken");
                if (token) {
                    try {
                        const response = await fetch(STUDENT_API, {
                            method: "PATCH",
                            headers: { "Content-Type": "application/json", Authorization: `Token ${token}` },
                            body: JSON.stringify({
                                name: updatedProfile.name, registration_number: updatedProfile.regNo,
                                phone: updatedProfile.phone, batch: updatedProfile.batch,
                                section: updatedProfile.section, group: updatedProfile.group,
                                course: updatedProfile.branch, year: updatedProfile.year,
                            }),
                        });
                        const data = await response.json();
                        if (!response.ok) throw new Error(data.error || "Profile save failed.");
                    } catch (error) {
                        const message = document.getElementById("saveMessage");
                        if (message) message.textContent = error.message;
                        return;
                    }
                }

                saveProfileData(
                    updatedProfile
                );


                updateSidebarProfile(
                    updatedProfile
                );


                const saveMessage =
                    document.getElementById(
                        "saveMessage"
                    );


                if (saveMessage) {

                    saveMessage.textContent =
                        localStorage.getItem("smartTimeToken") ? "Profile saved to your account ✓" : "Profile saved on this device ✓";


                    setTimeout(
                        function () {

                            saveMessage.textContent =
                                "";

                        },
                        3000
                    );

                }

            }
        );

    }



    /* =====================================================
       PHOTO INPUT
    ====================================================== */

    const photoInput =
        document.getElementById(
            "photoInput"
        );


    if (photoInput) {

        photoInput.addEventListener(
            "change",
            function (event) {

                const file =
                    event.target.files[0];


                if (!file) {

                    return;

                }


                /* CHECK FILE TYPE */

                if (
                    !file.type.startsWith(
                        "image/"
                    )
                ) {

                    alert(
                        "Please select a valid image file."
                    );

                    photoInput.value =
                        "";

                    return;

                }


                /* CHECK SIZE */

                if (
                    file.size >
                    5 * 1024 * 1024
                ) {

                    alert(
                        "Please select an image smaller than 5 MB."
                    );

                    photoInput.value =
                        "";

                    return;

                }


                /* READ IMAGE */

                const reader =
                    new FileReader();


                reader.onload =
                    function (e) {

                        const imageData =
                            e.target.result;


                        const profile =
                            getProfile();


                        profile.photo =
                            imageData;


                        saveProfileData(
                            profile
                        );


                        updateProfileImages(
                            imageData
                        );


                        const saveMessage =
                            document.getElementById(
                                "saveMessage"
                            );


                        if (saveMessage) {

                            saveMessage.textContent =
                                "Photo updated successfully ✓";


                            setTimeout(
                                function () {

                                    saveMessage.textContent =
                                        "";

                                },
                                3000
                            );

                        }


                        photoInput.value =
                            "";

                    };


                reader.readAsDataURL(
                    file
                );

            }
        );

    }



    /* =====================================================
       REMOVE PHOTO
    ====================================================== */

    const removePhotoBtn =
        document.getElementById(
            "removePhotoBtn"
        );


    if (removePhotoBtn) {

        removePhotoBtn.addEventListener(
            "click",
            function () {

                const profile =
                    getProfile();


                profile.photo =
                    "";


                saveProfileData(
                    profile
                );


                updateProfileImages(
                    ""
                );


                const saveMessage =
                    document.getElementById(
                        "saveMessage"
                    );


                if (saveMessage) {

                    saveMessage.textContent =
                        "Profile photo removed.";


                    setTimeout(
                        function () {

                            saveMessage.textContent =
                                "";

                        },
                        2500
                    );

                }

            }
        );

    }



    /* =====================================================
       NOTIFICATIONS
       
       IMPORTANT:
       NO ICONS ARE USED HERE.
    ====================================================== */

    let notifications = [];

    const escapeNotification = (value) => String(value ?? "").replace(/[&<>\"']/g, (character) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
    }[character]));

    async function studentApi(path, options = {}) {
        const token = localStorage.getItem("smartTimeToken");
        if (!token) return [];
        const response = await fetch(`${window.SMARTTIME_API_BASE || "http://127.0.0.1:8000/api"}/${path}`, {
            ...options,
            headers: { Authorization: `Token ${token}`, ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers }
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.error || data.detail || "Could not load dashboard data.");
        return data;
    }

    /* =====================================================
       CREATE NOTIFICATION HTML
       
       NO ICON DIV
    ====================================================== */

    function createNotificationHTML(
        notification
    ) {

        return `

            <div class="notification-item ${notification.read ? "read" : "unread"}" data-notification-id="${notification.id}">

                <div class="notification-content">

                    <h3>
                    ${escapeNotification(notification.title)}
                    </h3>

                    <p>
                    ${escapeNotification(notification.text)}
                    </p>

                    <span class="notification-time">
                    ${escapeNotification(notification.time)}
                    </span>

                </div>

            </div>

        `;

    }



    /* =====================================================
       LOAD NOTIFICATIONS
    ====================================================== */

    async function loadNotifications() {

        try {
            const data = await studentApi("notifications/");
            const rows = Array.isArray(data) ? data : (data.results || []);
            notifications = rows.map((item) => ({
                id: item.id, title: item.title, text: item.message,
                time: new Date(item.created_at).toLocaleString(), read: item.is_read
            }));
        } catch (error) {
            console.error("Student notifications could not be loaded:", error);
        }

        const dashboardContainer =
            document.getElementById(
                "dashboardNotifications"
            );

        const allContainer =
            document.getElementById(
                "allNotifications"
            );


        if (dashboardContainer) {

            dashboardContainer.innerHTML =
                notifications
                    .slice(0, 2)
                    .map(
                        createNotificationHTML
                    )
                    .join("");

        }


        if (allContainer) {

            allContainer.innerHTML =
                notifications
                    .map(
                        createNotificationHTML
                    )
                    .join("");

        }

        document.querySelectorAll(".notification-item[data-notification-id]").forEach((element) => {
            element.addEventListener("click", async () => {
                if (element.classList.contains("read")) return;
                try {
                    await studentApi(`notifications/${element.dataset.notificationId}/mark_read/`, { method: "POST" });
                    await loadNotifications();
                } catch (error) { console.error("Notification could not be marked read:", error); }
            });
        });

    }

    loadNotifications();
    window.setInterval(loadNotifications, 30000);



    /* =====================================================
       LOGOUT
    ====================================================== */

    const logoutBtn =
        document.getElementById(
            "logoutBtn"
        );


    if (logoutBtn) {

        logoutBtn.addEventListener(
            "click",
            async function () {

                const confirmLogout =
                    confirm(
                        "Are you sure you want to logout?"
                    );


                if (!confirmLogout) {

                    return;

                }


                /* Revoke backend token and clear login session */
                const token = localStorage.getItem("smartTimeToken");
                try {
                    if (token) await fetch(`${window.SMARTTIME_API_BASE || "http://127.0.0.1:8000/api"}/auth/logout/`, {
                        method: "POST", headers: { Authorization: `Token ${token}` }
                    });
                } catch (error) { console.warn("Could not revoke login token:", error); }
                finally {
                    ["smartTimeToken", "smartTimeUser", "smartTimeUserId", "loggedIn", "userRole", "userEmail", "userName"].forEach((key) => localStorage.removeItem(key));
                }

                /* Keep student profile */

                window.location.href =
                    "login.html";

            }
        );

    }



    /* =====================================================
       HASH CHANGE
       Allows browser back/forward
    ====================================================== */

    window.addEventListener(
        "hashchange",
        function () {

            openHashSection();

        }
    );


});

