document.addEventListener("DOMContentLoaded", function () {
   
    document.getElementById('user_agent').value = navigator.userAgent;
    console.log("user info present");

    const fileInput = document.getElementById('file-upload');
    const fileUploadText = document.getElementById('file-upload-text');

    fileInput.addEventListener('change', function() {
        const files = fileInput.files;
        if (files.length > 0) {
            fileUploadText.textContent = `${files.length} image(s) selected`;
        } else {
            fileUploadText.textContent = 'No images selected';
        }
    });
});
