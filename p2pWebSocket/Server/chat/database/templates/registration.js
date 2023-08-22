document.addEventListener("DOMContentLoaded", function () {
  var registrationForm = document.getElementById("registrationForm");
  var passwordInput = document.getElementById("password");
  var confirmPasswordInput = document.getElementById("confirm_password");
  var avatarInput = document.getElementById("avatar");

  registrationForm.addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent the default form submission

    var username = document.getElementById("username").value;
    var password = passwordInput.value;
    var confirmPassword = confirmPasswordInput.value;

    if (password !== confirmPassword) {
      document.getElementById("passwordMismatch").style.display = "block";
      return false;
    }

    var selectedFile = avatarInput.files[0];
    if (selectedFile) {
      var reader = new FileReader();

      reader.onload = function (e) {
        var base64Image = e.target.result;
        console.log("Base64 encoded image:", base64Image);

        // Add base64-encoded image to the form data
        var hiddenInput = document.createElement("input");
        hiddenInput.type = "hidden";
        hiddenInput.name = "base64Image";
        hiddenInput.id = "base64Image";
        hiddenInput.value = base64Image;
        registrationForm.appendChild(hiddenInput);

        // Submit the form
        registrationForm.submit();
      };

      reader.readAsDataURL(selectedFile);
    }
  });
});
