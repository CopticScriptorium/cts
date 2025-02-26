(function () {

    const KEYBOARDS = [

        { id: 'cop', name: 'Keyboard_coptic_greek', label: 'Coptic' },
        { id: 'cop-copt', name: 'Keyboard_coptic_qwerty', label: 'Coptic Qwerty' },
        // Add more keyboards here in the same format
    ];

    var virtualKeyboardEnabled = localStorage.getItem('virtualKeyboardEnabled') === 'true';
    console.log('virtualKeyboardEnabled', virtualKeyboardEnabled);
    var storedKeyboard = localStorage.getItem('preferredKeyboard') || KEYBOARDS[0].id;
    localStorage.setItem('preferredKeyboard', storedKeyboard);

    console.log('storedKeyboard', storedKeyboard);
    // Create a named handler function that we can reference for both adding and removing
    function showOSKHandler(event) {
        console.log('Focus event triggered');
        if (!keyman.osk.isVisible()) {
            console.log('OSK not visible, showing it');
            keyman.osk.show(true);  // Force show
        }
    }

    function attachKeyboardToInput(input) {
        console.log('Attaching keyboard to input');
        if (!input._keymanAttached) {  // Prevent double attachment
            keyman.attachToControl(input);
            keyman.enableControl(input);
            input.addEventListener('focus', showOSKHandler);
            input._keymanAttached = true;
        }
    }

    function detachKeyboardFromInput(input) {
        console.log('Detaching keyboard from input');
        if (input._keymanAttached) {
            input.removeEventListener('focus', showOSKHandler);
            keyman.detachFromControl(input);
            keyman.disableControl(input);
            input._keymanAttached = false;
        }
    }

    function getKeyboardById(keyboardId) {
        return KEYBOARDS.find(k => k.id === keyboardId);
    }
    // Function to set active keyboard and update UI
    function setActiveKeyboard(keyboardId) {
        const keyboard = getKeyboardById(keyboardId);
        keyman.setActiveKeyboard(keyboard.name, keyboard.id);
        document.getElementById('current-language').textContent = keyboard.label;
    }

    // Update keyboard toggle handler
    function toggleLanguage() {
        console.log('Toggling language');
        const currentLang = document.getElementById('current-language').textContent;
        const currentIndex = KEYBOARDS.findIndex(k => k.label === currentLang);
        const nextIndex = (currentIndex + 1) % KEYBOARDS.length;
        setActiveKeyboard(KEYBOARDS[nextIndex].id);
        localStorage.setItem('preferredKeyboard', KEYBOARDS[nextIndex].id);
    }

    // Update save preferences function
    function savePreferences() {
        const virtualKeyboardEnabled = document.getElementById('virtual-keyboard-toggle').checked;
        const exactSearch = document.getElementById('exact-search-toggle').checked;
        console.log('Saving preferences virtualKeyboardEnabled, exactSearch:', virtualKeyboardEnabled, exactSearch);
        localStorage.setItem('virtualKeyboardEnabled', virtualKeyboardEnabled);
        localStorage.setItem('exactSearch', exactSearch);
        applyPreferences();
    }

    async function initKeyman(virtualKeyboardEnabled) {
        let init;

        if (virtualKeyboardEnabled && !keyman.initialized) {
            console.log('Keyman Not Initialized. Initializing...');
            init = keyman.init({
                keyboardBaseUri: 'https://s.keyman.com/keyboard/',
                initialKeyboard: storedKeyboard,
                setActiveOnRegister: true,
                attachType: 'manual',
                useAlerts: false,
                osk: true,  // Ensure OSK is enabled
            }).then(function () {
                const keyboardIds = KEYBOARDS.map(keyboard => "@" + keyboard.id);
                console.log('Adding keyboards:', keyboardIds);
                return keyman.addKeyboards(keyboardIds);
            }).then(function () {
                console.log('Keyman initialized and keyboards added');
                document.getElementById('current-language').textContent = getKeyboardById(storedKeyboard).label;
                // Ensure OSK is ready
                keyman.osk.ready = true;
            }).catch(function (error) {
                console.error('Error initializing Keyman:', error);
            });
        } else {
            init = Promise.resolve(true);
        }
        return init;
    }

    async function applyPreferences() {
        console.log('Reading preferences virtualKeyboardEnabled, exactSearch:', localStorage.getItem('virtualKeyboardEnabled'), localStorage.getItem('exactSearch'));
        const virtualKeyboardEnabled = localStorage.getItem('virtualKeyboardEnabled') === 'true';
        const exactSearch = localStorage.getItem('exactSearch') === 'true';
        const searchInputs = document.querySelectorAll('input[type="text"][name="text"]');

        applyExactSearch(exactSearch, searchInputs);
        await initKeyman(virtualKeyboardEnabled);

        const languageSelector = document.getElementById('language-selector');

        // Apply preferences
        if (virtualKeyboardEnabled) {
            languageSelector.style.display = 'flex';
            searchInputs.forEach(input => {
                attachKeyboardToInput(input);
            });
            if (!keyman.osk.isVisible()) {
                keyman.osk.show();
            }
        } else {
            console.log('Hiding OSK');
            if (keyman.initialized) {
                if (keyman.osk.isVisible()) {
                    keyman.osk.hide();
                }
                languageSelector.style.display = 'none';
                searchInputs.forEach(input =>
                    detachKeyboardFromInput(input)
                );
            }
        }
    }

    function applyExactSearch(exactSearch, searchInputs) {
        if (exactSearch) {
            console.log('Setting exactSearch is true');
            searchInputs.forEach(input => {
                // Remove any existing quotes first
                const withoutQuotes = input.value.replace(/"/g, '');
                const withQuotes = `"${withoutQuotes}"`;
                if (input.value !== withQuotes) {
                    input.value = withQuotes;
                }
            });
        } else {
            console.log('Setting exactSearch is false');
            searchInputs.forEach(input => {
                const withoutQuotes = input.value.replace(/"/g, '');
                if (input.value !== withoutQuotes) {
                    input.value = withoutQuotes;
                }
            });
        }
    }
        // Initialize after document is loaded
    document.addEventListener('DOMContentLoaded', function () {
            // Set default value for exactSearch if not present
            if (localStorage.getItem('exactSearch') == null) {
                console.log('No prefrences found initializeing exactSearch to true');
                localStorage.setItem('exactSearch', 'true');
                document.getElementById('exact-search-toggle').checked = true;
            } else {
                exactSearch = localStorage.getItem('exactSearch') === 'true';
                console.log('exactSearch', exactSearch);
                document.getElementById('exact-search-toggle').checked = exactSearch;
            }
            storedKeyboard = localStorage.getItem('preferredKeyboard') || KEYBOARDS[0].id;
            console.log('storedKeyboard', storedKeyboard);
            document.getElementById('language-toggle').addEventListener('click', toggleLanguage);
            document.getElementById('virtual-keyboard-toggle').addEventListener('change', savePreferences);
            document.getElementById('exact-search-toggle').addEventListener('change', savePreferences);
            const searchForm = document.querySelector('.search-bar');
            searchForm.addEventListener('submit', function (e) {
                console.log("form submitted. Applying Exact searcch before submission")
                e.preventDefault();
                applyExactSearch(document.getElementById('exact-search-toggle').checked == true, searchForm.querySelectorAll('input[type="text"][name="text"]'));
                this.submit();
            });
        });
        console.log('Event listeners attached');
        applyPreferences();
    }
)();
