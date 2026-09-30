// =========================================================
// FORMAT AI ANSWERS (Markdown bold -> real bold)
// =========================================================

function formatAnswer(text) {

    // Escape HTML first, so model output can never inject markup
    const escaped =
        text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

    // The model sometimes writes "**Word****:" (four asterisks).
    // Collapse any run of 3+ asterisks into exactly two, otherwise
    // the bold pairs get shifted onto the wrong words.
    const normalized =
        escaped.replace(/\*{3,}/g, "**");

    // **bold** -> <strong>bold</strong>
    const bolded =
        normalized.replace(
            /\*\*(.+?)\*\*/g,
            "<strong>$1</strong>"
        );

    // Remove any stray asterisks left over (e.g. "****:")
    return bolded.replace(/\*/g, "");
}


const chat =
    document.getElementById("chat");

const questionInput =
    document.getElementById("question");

const askButton =
    document.getElementById("askButton");

const pdfInput =
    document.getElementById("pdfInput");

const pdfButton =
    document.getElementById("pdf-button");

const documentsContainer =
    document.getElementById(
        "documentsContainer"
    );

const documentsList =
    document.getElementById(
        "documentsList"
    );

const pdfLoading =
    document.getElementById(
        "pdfLoading"
    );


// =========================================================
// EVENTS
// =========================================================

askButton.addEventListener(
    "click",
    sendQuestion
);


questionInput.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key === "Enter"
        ) {

            event.preventDefault();

            sendQuestion();
        }
    }
);


// =========================================================
// QUESTIONS
// =========================================================

async function sendQuestion() {

    const question =
        questionInput.value.trim();

    if (
        question === ""
    ) {
        return;
    }

    addMessage(
        question,
        "user"
    );

    questionInput.value = "";

    const loadingMessage =
        addMessage(
            "● Searching...",
            "loading"
        );

    try {

        const response =
            await fetch(
                "/ask",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        question:
                            question
                    })
                }
            );

        const data =
            await response.json();

        loadingMessage.remove();

        if (
            !response.ok
        ) {

            addMessage(
                data.answer ||
                "An error occurred.",
                "error"
            );

            return;
        }

        addMessage(
            data.answer,
            "ai",
            data.sources || []
        );

    } catch (error) {

        console.error(
            "Question error:",
            error
        );

        loadingMessage.remove();

        addMessage(
            "⚠ An error occurred while "
            + "processing the question.",
            "error"
        );
    }
}


// =========================================================
// ADD CHAT MESSAGE
// =========================================================

function addMessage(
    text,
    sender,
    sources = []
) {

    const message =
        document.createElement(
            "div"
        );

    message.className =
        `message ${sender}`;

    const bubble =
        document.createElement(
            "div"
        );

    bubble.className =
        "bubble";

    // AI answers are formatted (bold etc.); everything else
    // (user questions, errors, loading text) stays plain text.
    if (sender === "ai") {

        bubble.innerHTML =
            formatAnswer(text);

    } else {

        bubble.textContent =
            text;
    }

    message.appendChild(
        bubble
    );


    // -----------------------------------------------------
    // Sources
    // -----------------------------------------------------

    if (
        sender === "ai"
        && sources.length > 0
    ) {

        const sourceBox =
            document.createElement(
                "div"
            );

        sourceBox.className =
            "sources";


        const sourceTitle =
            document.createElement(
                "div"
            );

        sourceTitle.className =
            "sources-title";

        sourceTitle.textContent =
            "Sources";

        sourceBox.appendChild(
            sourceTitle
        );


        const uniqueSources =
            [];

        const seenSources =
            new Set();


        sources.forEach(
            function (source) {

                const documentName =
                    source.document_name
                    ||
                    "Unknown document";

                const pageNumber =
                    source.page_number
                    ||
                    "?";

                const sourceKey =
                    `${documentName}|${pageNumber}`;


                if (
                    seenSources.has(
                        sourceKey
                    )
                ) {

                    return;
                }


                seenSources.add(
                    sourceKey
                );


                uniqueSources.push({
                    documentName,
                    pageNumber
                });

            }
        );


        uniqueSources.forEach(
            function (source) {

                const sourceItem =
                    document.createElement(
                        "div"
                    );

                sourceItem.className =
                    "source-item";

                sourceItem.textContent =
                    `📄 ${source.documentName}`
                    + ` — Page ${source.pageNumber}`;

                sourceBox.appendChild(
                    sourceItem
                );
            }
        );


        message.appendChild(
            sourceBox
        );
    }


    chat.appendChild(
        message
    );

    chat.scrollTop =
        chat.scrollHeight;

    return message;
}


// =========================================================
// LOAD DOCUMENTS
// =========================================================

async function loadDocuments() {

    try {

        const response =
            await fetch(
                "/documents"
            );

        const data =
            await response.json();

        if (
            response.ok
        ) {

            renderDocuments(
                data.documents || []
            );
        }

    } catch (error) {

        console.error(
            "Document loading error:",
            error
        );
    }
}


// =========================================================
// RENDER DOCUMENTS
// =========================================================

function renderDocuments(
    documents
) {

    documentsList.innerHTML = "";


    if (
        documents.length === 0
    ) {

        documentsContainer.style
            .display = "none";

        return;
    }


    documentsContainer.style
        .display = "block";


    documents.forEach(
        function (documentName) {

            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "document-item";


            const name =
                document.createElement(
                    "span"
                );

            name.className =
                "document-name";

            name.textContent =
                `📄 ${documentName}`;


            const removeButton =
                document.createElement(
                    "button"
                );

            removeButton.className =
                "remove-document";

            removeButton.type =
                "button";

            removeButton.textContent =
                "×";


            removeButton.title =
                "Remove PDF";


            removeButton.addEventListener(
                "click",
                function () {

                    removeDocument(
                        documentName
                    );
                }
            );


            item.appendChild(
                name
            );

            item.appendChild(
                removeButton
            );

            documentsList.appendChild(
                item
            );

        }
    );
}


// =========================================================
// UPLOAD PDF
// =========================================================

pdfInput.addEventListener(
    "change",
    async function () {

        const file =
            pdfInput.files[0];


        if (!file) {
            return;
        }


        if (
            file.type !==
            "application/pdf"
        ) {

            addMessage(
                "⚠ Please select a valid PDF file.",
                "error"
            );

            pdfInput.value = "";

            return;
        }


        const formData =
            new FormData();


        formData.append(
            "file",
            file
        );


        pdfButton.style.display =
            "none";

        pdfLoading.style.display =
            "block";


        try {

            const response =
                await fetch(
                    "/upload",
                    {
                        method: "POST",
                        body: formData
                    }
                );


            const data =
                await response.json();


            if (
                !response.ok
            ) {

                addMessage(
                    "⚠ "
                    + (
                        data.message
                        ||
                        "PDF upload failed."
                    ),
                    "error"
                );

                return;
            }


            renderDocuments(
                data.documents || []
            );


            addMessage(
                `✓ ${file.name} uploaded successfully.`,
                "ai"
            );


        } catch (error) {

            console.error(
                "Upload error:",
                error
            );


            addMessage(
                "⚠ An error occurred while "
                + "uploading the PDF.",
                "error"
            );

        } finally {

            pdfButton.style.display =
                "inline-flex";

            pdfLoading.style.display =
                "none";

            pdfInput.value = "";
        }
    }
);


// =========================================================
// REMOVE ONE PDF
// =========================================================

async function removeDocument(
    documentName
) {

    const confirmed =
        window.confirm(
            `Remove "${documentName}"?`
        );


    if (!confirmed) {
        return;
    }


    try {

        const encodedName =
            encodeURIComponent(
                documentName
            );


        const response =
            await fetch(
                `/delete/${encodedName}`,
                {
                    method: "DELETE"
                }
            );


        const data =
            await response.json();


        if (
            !response.ok
        ) {

            addMessage(
                "⚠ "
                + (
                    data.message
                    ||
                    "PDF could not be removed."
                ),
                "error"
            );

            return;
        }


        renderDocuments(
            data.documents || []
        );


    } catch (error) {

        console.error(
            "Delete error:",
            error
        );


        addMessage(
            "⚠ An error occurred while "
            + "removing the PDF.",
            "error"
        );
    }
}


// =========================================================
// INITIAL LOAD
// =========================================================

// IMPORTANT:
// Do NOT call /delete here.
// Existing PDFs must survive page refresh.

loadDocuments();