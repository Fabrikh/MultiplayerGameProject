function validateForm() {
  var password = document.getElementById("password").value;
  var confirmPassword = document.getElementById("confirm_password").value;

  if (password !== confirmPassword) {
    document.getElementById("passwordMismatch").style.display = "block";
    return false;
  } else {
    document.getElementById("passwordMismatch").style.display = "none";
    return true;
  }
}
