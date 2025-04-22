document.addEventListener("DOMContentLoaded", function () {
    // Temel elementleri seç
    const searchInput = document.getElementById("searchInput");
    const resultsContainer = document.getElementById("results");
    const favoritesContainer = document.getElementById("favorites");
    const favoritesList = document.getElementById("favoritesList");
    const emailForm = document.querySelector(".email-form");
    const emailInput = document.getElementById("emailInput");
    const userNotes = document.getElementById("userNotes");
    const sendEmailButton = document.getElementById("sendEmailButton");
    const mobileFavoritesButton = document.getElementById("mobileFavoritesButton");
    const desktopFavoritesButton = document.getElementById("desktopFavoritesButton");
    const favoriteToggle = document.getElementById("favoriteToggle");
    const footer = document.querySelector('footer');

    emailForm.addEventListener("submit", function (event) {
        event.preventDefault(); // Formun sayfayı yenilemesini engelle
    
        const emailValue = emailInput.value.trim();
        const userNotesValue = userNotes.value.trim();
        const favoriteQuestions = JSON.parse(localStorage.getItem("favorites")) || [];
    
        const emailRegex = /^(([^<>()[\]\.,;:\s@\"]+(\.[^<>()[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$/i;
        
        if (!emailValue || !emailValue.match(emailRegex)) {
            alert("Lütfen geçerli bir e-posta adresi girin.");
            return;
        }

        if (favoriteQuestions.length == 0) {
            alert("Lütfen favori sorularınızı seciniz.");
        }
    
        const emailContent = {
            email: emailValue,
            favorites: favoriteQuestions,
            notes: userNotesValue
        };
    
        fetch('/send-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(emailContent),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Favori sorularınız ve notlarınız başarıyla gönderildi!");
                emailForm.reset(); // formu temizle
            } else {
                alert("E-posta gönderilirken bir hata oluştu.");
            }
        })
        .catch(error => {
            console.error("Hata:", error);
            alert("E-posta gönderilirken bir hata oluştu.");
        });
    });    

    
    let favoriteQuestions = JSON.parse(localStorage.getItem("favorites")) || [];

    // Favori butonlarına tıklama olayı
    [favoriteToggle, desktopFavoritesButton, mobileFavoritesButton].forEach(button => {
        if (button) {
            button.addEventListener("click", handleFavoriteButtonClick);
        }
    });

    
    function handleFavoriteButtonClick(event) {
        event.stopPropagation();
        favoritesContainer.classList.toggle("visible");
        
        // Mobil görünümde favori butonunun metnini güncelle
        if (window.innerWidth <= 767 && mobileFavoritesButton) {
            mobileFavoritesButton.textContent = favoritesContainer.classList.contains("visible") ? 
                "Favorileri Kapat" : "Favorileri Aç";
        }

        // Masaüstü favori butonunun metnini güncelle
        if (favoriteToggle) {
            favoriteToggle.textContent = favoritesContainer.classList.contains("visible") ? 
                "Favorileri Kapat" : "Favorileri Aç";
        }

        updateFavoritesList();
    }

    // Favori listesini güncelle
    function updateFavoritesList() {
        favoritesList.innerHTML = "";
        favoriteQuestions.forEach((question, index) => {
            const item = document.createElement("div");
            item.className = "favorite-item";
            item.innerHTML = `
                <span>${question}</span>
                <button class="remove-fav" data-index="${index}">❌</button>
            `;
            favoritesList.appendChild(item);
        });

        // Favori silme butonlarına olay dinleyicisi ekle
        document.querySelectorAll(".remove-fav").forEach(button => {
            button.addEventListener("click", function(event) {
                event.stopPropagation();
                const index = parseInt(this.dataset.index);
                removeFavorite(index);
            });
        });
    }

    
    function addFavorite(question) {
        if (!favoriteQuestions.includes(question)) {
            favoriteQuestions.push(question);
            localStorage.setItem("favorites", JSON.stringify(favoriteQuestions));
            updateFavoritesList();
            updateFavoriteIcons();
        }
    }

  
    function removeFavorite(index) {
        favoriteQuestions.splice(index, 1);
        localStorage.setItem("favorites", JSON.stringify(favoriteQuestions));
        updateFavoritesList();
        updateFavoriteIcons();
    }

    // Favori ikonlarını güncelle
    function updateFavoriteIcons() {
        document.querySelectorAll(".fav-button").forEach(button => {
            const question = button.previousElementSibling.textContent;
            button.textContent = favoriteQuestions.includes(question) ? "❤️" : "🤍";
        });
    }

    searchInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault(); 
        }
    });
    // Arama işlemi
    searchInput.addEventListener("input", function () {
        let query = searchInput.value.trim();

        if (query.length > 1) {
            fetch(`/search?query=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    resultsContainer.innerHTML = "";
                    resultsContainer.classList.add("visible");

                    if (data.sorular.length > 0) {
                        let etiketDiv = document.createElement("div");
                        etiketDiv.className = "etiket-bilgi";
                        etiketDiv.innerHTML = `<span class="etiket-sembol">🏷️</span> En Yakın Etiket ➔ ${data.etiket}`;
                        resultsContainer.appendChild(etiketDiv);

                        let scrollableContainer = document.createElement("div");
                        scrollableContainer.className = "scrollable-container";

                        data.sorular.forEach((item, index) => {
                            let div = document.createElement("div");
                            div.className = "result-item hidden slide-in-left";
                            div.setAttribute("data-soru-id", item.id);
                        
                            let innerDiv = document.createElement("div");
                            innerDiv.style.display = "flex";
                            innerDiv.style.alignItems = "center";
                            innerDiv.style.justifyContent = "space-between";
                            innerDiv.style.width = "100%";
                        
                            let textDiv = document.createElement("span");
                            textDiv.textContent = item.soru;
                        
                            let favButton = document.createElement("span");
                            favButton.className = "fav-button";
                            favButton.textContent = favoriteQuestions.includes(item.soru) ? "❤️" : "🤍";
                        
                            favButton.addEventListener("click", function (event) {
                                event.stopPropagation();
                                if (this.textContent === "❤️") {
                                    removeFavorite(favoriteQuestions.indexOf(item.soru));
                                    this.textContent = "🤍";
                                } else {
                                    addFavorite(item.soru);
                                    this.textContent = "❤️";
                                }
                            });
                        
                            innerDiv.appendChild(textDiv);
                            innerDiv.appendChild(favButton);
                        
                            div.appendChild(innerDiv);
                        
                            setTimeout(() => {
                                div.classList.remove("hidden");
                                div.classList.add("slide-in-left");
                            }, index * 150);
                        
                            scrollableContainer.appendChild(div);
                        
                            if (index < data.sorular.length - 1) {
                                let separator = document.createElement("hr");
                                separator.className = "separator";
                                scrollableContainer.appendChild(separator);
                            }
                        });
                        resultsContainer.appendChild(scrollableContainer);

                        document.querySelectorAll(".result-item").forEach(item => {
                            item.addEventListener("click", function () {
                                let soru_id = this.getAttribute("data-soru-id");
                                toggleInfoBox(soru_id, this);
                            });
                        });
                    } else {
                        resultsContainer.innerHTML = `<p class="error-message">⚠️ Eşleşen soru bulunamadı.</p>`;
                    }
                })
                .catch(error => {
                    console.error("Veri çekme hatası:", error);
                    resultsContainer.innerHTML = `<p class="error-message">⚠️ Sonuçlar yüklenirken bir hata oluştu.</p>`;
                });
        } else {
            resultsContainer.innerHTML = "";
            resultsContainer.classList.remove("visible");
        }
    });

    // Bilgi kutusu aç/kapat
    function toggleInfoBox(soru_id, soruElement) {
        const existingInfoBox = soruElement.querySelector(".info-box");
    
        if (existingInfoBox) {
            existingInfoBox.remove();
            return;
        }
    
        fetch(`/get_info?soru_id=${encodeURIComponent(soru_id)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error("API'den veri alınamadı: " + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                const infoBox = document.createElement("div");
                infoBox.className = "info-box";
                infoBox.innerHTML = `<p>${data.bilgi_mesaji.replace(/\\n|\/n|\n/g, "<br>")}</p>`;
    
                soruElement.appendChild(infoBox);
    
                const closeInfoBox = (event) => {
                    if (!infoBox.contains(event.target)) {
                        infoBox.remove();
                        document.removeEventListener("click", closeInfoBox);
                    }
                };
    
                document.addEventListener("click", closeInfoBox);
    
                infoBox.addEventListener("click", (event) => {
                    event.stopPropagation();
                });
            })
            .catch(error => {
                console.error("Bilgi çekme hatası:", error);
                const errorBox = document.createElement("div");
                errorBox.className = "info-box error";
                errorBox.innerHTML = `<p>⚠️ Bilgi yüklenirken bir hata oluştu.</p>`;
                soruElement.appendChild(errorBox);
    
                setTimeout(() => {
                    scrollableContainer.scrollTop = 0;
                }, 100);
                
            });
    }

    
    updateFavoritesList();
}); 