function feedbackController(simuladorName, intervalo = 5) {

    // lê contador
    let count = Number(localStorage.getItem("feedback_count_" + simuladorName) || 0);

    count++;
    localStorage.setItem("feedback_count_" + simuladorName, count);

    // se atingiu o limite, mostra modal
    if (count >= intervalo) {
        showFeedback(simuladorName);
        localStorage.setItem("feedback_count_" + simuladorName, 0);
    }
}
